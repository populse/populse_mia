"""The first module used during mia's installation.

This module is responsible for initializing core parameters and conducting
essential checks to ensure a successful installation of Mia. It sets up
configurations, verifies system compatibility, and manages dependencies
to establish a stable environment for the application.

:Contains:
    :Function:
        - install_and_import
"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

import importlib
import os
import subprocess
import sys

# We use this module only in user mode.
os.environ["MIA_DEV_MODE"] = "0"


def install_and_import(module_name):
    """Tries to import the specified module.

    If the module is not found, it installs the module using pip and then
    imports it.
    If running inside a virtual environment, it installs the module there;
    otherwise, it adds the '--user' flag for a user-level installation.

    Args:
        module_name (str): The name of the module to import or install.

    Raises:
        subprocess.CalledProcessError: If the pip installation fails.
        ImportError: If the module cannot be imported even after installation.

    Example:
        install_and_import('pyyaml')
        install_and_import('requests')

    Note:
        Some module names differ between PyPi and Python import names,
        such as "pyyaml" (PyPi) vs. "yaml" (Python).
    """
    import_name = "yaml" if module_name == "pyyaml" else module_name

    try:
        # Try to import the module
        importlib.import_module(import_name)

    except ImportError:
        # Module not found, install it
        print(f"{module_name} not found. Installing...")

        # Check if running in a virtual environment
        is_venv = sys.prefix != sys.base_prefix
        pip_install_command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            module_name,
        ]

        # Add '--user' flag only if not in a virtual environment
        if not is_venv:
            pip_install_command.insert(4, "--user")

        subprocess.check_call(pip_install_command)

        # Try to import the module again after installation
        try:
            importlib.import_module(import_name)

        except ImportError:
            raise ImportError(
                f"Failed to import {module_name} after " f"installation."
            )


def run_installer():
    """
    Docstring to write ...
    """
    print("Please wait, installation in progress! ...\n")
    # List of required packages
    packages = ["PyQt5", "pyyaml", "packaging", "cryptography"]

    for package in packages:

        try:
            install_and_import(package)

        except subprocess.CalledProcessError:
            print(
                f"Failed to install {package}. Please check your "
                f"pip installation."
            )

        except ImportError:
            print(
                f"Could not import {package} after installation. "
                "Please check compatibility or try reinstalling manually."
            )

    # Clear specific packages from sys.modules to avoid conflicts
    for key in list(sys.modules):

        if key.startswith("PyQt5") or key in {
            "yaml",
            "packaging",
            "cryptography",
        }:
            del sys.modules[key]

    try:
        import crypt  # noqa: F401

        import packaging  # noqa: F401
        import yaml  # noqa: F401

        # FIXME: Replace 'crypt' with updated libraries like legacycrypt,
        #        bcrypt, argon2-cffi, hashlib, and passlib when upgrading
        #        to Python 3.13
        # Import MIAInstallWidget after confirming dependencies
        from mia_install_widget import MIAInstallWidget
        from PyQt5 import QtWidgets

    except ImportError as e:
        sys.exit(
            f"\n{e}...\n\nPython package environment was not correctly "
            "updated!\n\nPlease retry by running:\n    python3 install_mia.py"
            "\n\nIf the issue persists, try manually installing the "
            "problematic module.\n"
        )

    # Initialize and display Mia installation widget
    app = QtWidgets.QApplication(sys.argv)
    mia_install_widget = MIAInstallWidget()

    # Center widget on screen
    frame_gm = mia_install_widget.frameGeometry()
    screen = QtWidgets.QApplication.desktop().screenNumber(
        QtWidgets.QApplication.desktop().cursor().pos()
    )
    center_point = (
        QtWidgets.QApplication.desktop().screenGeometry(screen).center()
    )
    frame_gm.moveCenter(center_point)
    mia_install_widget.move(frame_gm.topLeft())

    mia_install_widget.show()
    app.exec()
