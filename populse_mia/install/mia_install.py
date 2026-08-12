"""
Initialize the Populse Mia installation environment.

This module provides the first stage of the Mia installation process.
It verifies that the Python packages required by the installer are available,
installs any missing dependencies, and then launches the graphical installer.

In fact, this module exists for historical reasons. Originally, the
installation of Mia was handled separately from populse_mia, so we needed to
make sure that PyQt5 and other required dependencies were properly installed
and available on the system. Today, this module is part of populse_mia, and
since PyQt5 and the other required packages are dependencies of populse_mia,
they should normally be installed automatically when populse_mia is installed
via pip. We are keeping the module because it only adds a few additional
checks, with little to no significant impact on execution time. It can also
still be useful for detecting and fixing certain configuration or installation
issues.

The module is intended to run only in user mode.
"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

import importlib
import logging
import os
import subprocess
import sys

# We use this module only in user mode.
os.environ["MIA_DEV_MODE"] = "0"

__all__ = ["install_and_import", "run_installer"]

logger = logging.getLogger(__name__)


def install_and_import(module_name):
    """
    Ensure that a Python module is available.

    The function first attempts to import the requested module. If it is not
    installed, it installs the corresponding package using ``pip`` and retries
    the import.

    When executed inside a virtual environment, the package is installed into
    that environment. Otherwise, the installation is performed with the
    ``--user`` option.

    :param module_name: Name of the package to install.
    :type module_name: str

    :raises subprocess.CalledProcessError: If the package installation fails.
    :raises ImportError: If the module cannot be imported after installation.

    Note:
        Some package names differ from their import names. For example,
        ``pyyaml`` is installed from PyPI but imported as ``yaml``.
    """
    import_name = "yaml" if module_name == "pyyaml" else module_name

    try:
        # Try to import the module
        importlib.import_module(import_name)
        return

    except ImportError:
        # Module not found, install it
        logger.warning(f"{module_name} not found. Installing...")
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
        ]

        # Check if running in a virtual environment
        if sys.prefix == sys.base_prefix:
            command.append("--user")

        command.append(module_name)
        subprocess.check_call(command)

        # Try to import the module again after installation
        try:
            importlib.import_module(import_name)

        except ImportError as exc:
            raise ImportError(
                f"Unable to import '{import_name}' after installing "
                f"'{module_name}'."
            ) from exc


def run_installer():
    """
    Launch the Populse Mia installation wizard.

    This function verifies that all Python packages required by the installer
    are available. Missing packages are installed automatically whenever
    possible. Once the installation environment has been validated, the
    graphical installation wizard is created and displayed.

    If a required dependency cannot be imported after installation, the
    process terminates with an error message describing how to retry the
    installation.
    """
    msg = "Please wait, Install & Repair mode in progress..."
    print("\n" + msg + "\n")
    logger.info(msg)
    # List of required packages
    packages = ("PyQt5", "pyyaml", "packaging", "cryptography")

    # We start by checking whether the packages needed for the installation are
    # available; if they aren't, we try to install them...
    for package in packages:

        try:
            install_and_import(package)

        except subprocess.CalledProcessError:
            logger.warning(
                f"Failed to install {package}. Please check the pip "
                f"installation."
            )

        except ImportError:
            logger.warning(
                f"Could not import {package} after installation. Please "
                f"check compatibility or try reinstalling manually."
            )

    # Clear specific packages from sys.modules to avoid conflicts
    modules_to_clear = {
        "yaml",
        "packaging",
        "cryptography",
    }

    for name in tuple(sys.modules):

        if name.startswith("PyQt5") or name in modules_to_clear:
            sys.modules.pop(name, None)

    try:
        # FIXME: Do we really need to import the following three modules here?
        import cryptography  # noqa: F401
        import packaging  # noqa: F401
        import yaml  # noqa: F401
        from PyQt5 import QtWidgets

        # Import MIAInstallWidget after confirming dependencies
        from .mia_install_widget import MIAInstallWidget

    except ImportError as e:
        sys.exit(
            f"\n{e}...\n\nPython package environment was not correctly "
            "updated!\n\nPlease retry by running:\n"
            "    python3 -m populse_mia -i\n\n"
            "If the issue persists, try installing the module manually "
            "(python3 -m pip install module).\n"
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
    msg = "End of the installation process...\n"
    print(msg)
    logger.info(msg)
