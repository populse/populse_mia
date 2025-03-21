"""The first module used at the mia runtime.

Basically, this module is dedicated to the initialisation of the basic
parameters and the various checks necessary for a successful launch of the
mia's GUI.

:Contains:
    :Function:
        - add_to_sys_path
        - check_package
        - main
        - qt_message_handler

"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

import argparse
import importlib
import logging
import os
import sys
import tempfile
from pathlib import Path

# PyQt5 imports
from PyQt5.QtCore import QCoreApplication, Qt, qInstallMessageHandler
from PyQt5.QtWidgets import QApplication, QMessageBox

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def add_to_sys_path(path, name, index=0):
    """
    Adds the specified path to the system path if it's a valid directory.

    :param path (pathlib.Path): The directory path to be added to the
                                system path.
    :param name (str): The name of the package being added.
    :param index (int, optional): The index at which to insert the path
                                  into sys.path. Defaults to 0.
    :return (bool): True if the path is a valid directory and was added
                    to sys.path, False otherwise.
    """

    if path.is_dir():
        sys.path.insert(index, str(path))
        logger.info(f"  . Using {name} package from {path}")
        return True

    else:
        logger.warning(f"{name} package not found!")
        return False


def check_package(name):
    """
    Attempts to import a package by its name, logs the location of the
    package if successful, and logs an error if the package is missing.

    :param name (str): The name of the package to be imported.

    :return (bool): True if the package is imported successfully;
                    False if the package is missing.
    """

    try:
        mod = importlib.import_module(name)
        mod_dir = Path(mod.__file__).resolve().parent[1]
        logger.info(f"  . Using {name} package from {mod_dir}")
        return True

    except ImportError:
        logger.error(f"Failed to import {name} package!")
        return None

    except AttributeError:
        logger.warning(f"{name} package has no __file__ attribute!")
        return True


def main(args):
    """Make basic configuration check, then actual launch of Mia.

    Checks if Mia is called from the site/dist packages (`user mode`) or from a
    cloned git repository (`developer mode`).

    ~/.populse_mia/configuration_path.yml is mandatory, if it doesn't exist
    or is corrupted, try to create one with a valid properties path.

    - If launched from a cloned git repository (`developer mode`):
        - the properties_path is the "properties_dev_path" parameter in
          ~/.populse_mia/configuration_path.yml
    - If launched from the site/dist packages (`user mode`):
        - the properties_path is the "properties_user_path" parameter in
          ~/.populse_mia/configuration_path.yml

    Launches the verify_processes() function, then the launch_mia() function
    (Mia's real launch).
    """

    pypath = []
    package_not_found = []
    # Disables any etelemetry check.
    os.environ.setdefault("NO_ET", "1")
    os.environ.setdefault("NIPYPE_NO_ET", "1")
    # Trying to fix High DPI Display issue
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # General QApplication class instantiation
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    QApplication.setOverrideCursor(Qt.WaitCursor)

    # Adding the populse projects path to sys.path, if in developer mode
    if Path(__file__).resolve().parents[1] not in sys.path:
        # "developer" mode
        DEV_MODE = True
        os.environ["MIA_DEV_MODE"] = "1"
        # Determine the root development directory
        root_dev_dir = Path(__file__).resolve().parents[2]
        branch = ""
        populse_bdir = ""
        capsul_bdir = ""
        soma_bdir = ""

        if not (root_dev_dir / "populse_mia").is_dir():
            # Different sources layout - try casa_distro mode
            # TODO: At the moment, my casa_distro isn't working, and I don't
            #       understand this part. I'll check later when I've got
            #       casa_distro back.
            # TODO start
            root_dev_dir = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                )
            )

            if os.path.basename(root_dev_dir) == "populse":
                root_dev_dir = os.path.dirname(root_dev_dir)
                populse_bdir = "populse"
                soma_bdir = "soma"

            logger.info(f"root_dev_dir: {root_dev_dir}")
            branch = os.path.basename(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            logger.info(f"branch: {branch}")
            # TODO stop

        # populse packages
        packages = [
            {
                "populse_mia": (
                    root_dev_dir / populse_bdir / "populse_mia" / branch
                )
            },
            {"capsul": (root_dev_dir / capsul_bdir / "capsul" / branch)},
            {
                "soma": (
                    root_dev_dir / soma_bdir / "soma-base" / branch / "python"
                )
            },
            {
                "soma_workflow": (
                    root_dev_dir
                    / soma_bdir
                    / "soma-workflow"
                    / branch
                    / "python"
                )
            },
            {
                "populse_db": (
                    root_dev_dir
                    / populse_bdir
                    / "populse_db"
                    / branch
                    / "python"
                )
            },
            {
                "mia_processes": (
                    root_dev_dir / populse_bdir / "mia_processes" / branch
                )
            },
        ]
        # Adding populse packages in sys.path
        logger.info("- Mia in 'developer' mode")
        i = 0

        for package in packages:

            for name, dev_path in package.items():

                if add_to_sys_path(dev_path, name, i):
                    pypath.append(dev_path)
                    i += 1

                elif not check_package(name):
                    package_not_found.append(name)

                try:
                    importlib.import_module(name)
                    logger.info(
                        f"    {name} version: "
                        f"{sys.modules[name].__version__}"
                    )

                except (ModuleNotFoundError, AttributeError):
                    # version is not found
                    pass

        if package_not_found:
            error_msg = "\n".join(f"- {pkg}" for pkg in package_not_found)
            QMessageBox.warning(
                None,
                "populse_mia - ImportError",
                f"Missing packages:\n{error_msg}\nPlease reinstall them.",
            )
            sys.exit(1)

    # TODO: Same as the first todo above, I don't understand the lines below,
    #       so I'll comment on them for now.
    # elif "CASA_DISTRO" in os.environ:
    #     # If the casa distro development environment is detected,
    #     # developer mode is activated.
    #     os.environ["MIA_DEV_MODE"] = "1"
    #     DEV_MODE = True

    else:  # "user" mode
        os.environ["MIA_DEV_MODE"] = "0"
        DEV_MODE = False
        logger.info("- Mia in 'user' mode")
        modules = (
            "populse_mia",
            "capsul",
            "soma",
            "soma_workflow",
            "populse_db",
            "mia_processes",
        )

        for module in modules:

            if module in sys.modules:
                mod = sys.modules[module]

            else:
                mod = importlib.import_module(module)

            logger.info(
                f"  . Using {mod.__name__} package "
                f"from {mod.__path__[0]} ..."
            )

            try:
                logger.info(
                    f"    {mod.__name__} version: "
                    f"{sys.modules[module].__version__}"
                )

            except (ModuleNotFoundError, AttributeError):
                # version is not found
                pass

    # Check if nipype is available on the station.
    # If not available ask the user to install it.
    try:
        importlib.import_module("nipype")

    except (ImportError, AttributeError) as e:
        logger.error(f"MIA warning {e.__class__}: {e}")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("populse_mia -  warning: ImportError!")
        msg.setText(
            "An issue has been detected with "
            "the nipype package. Please (re)install this "
            "package and/or fix the issues displayed in the standard "
            "output. Then, start again Mia ..."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(msg.close)
        msg.exec()
        sys.exit(1)

    # Now that populse projects paths have been set in sys.path, if necessary,
    # we can import from these projects:
    # Populse_mia imports
    from populse_mia.utils import (  # noqa E402
        check_python_version,
        launch_mia,
        verify_processes,
        verify_setup,
    )

    verify_setup(dev_mode=DEV_MODE, pypath=list(map(str, pypath)))
    verify_processes(
        sys.modules["nipype"].__version__,
        sys.modules["mia_processes"].__version__,
        sys.modules["capsul"].__version__,
    )
    check_python_version()
    cwd = os.getcwd()

    with tempfile.TemporaryDirectory() as temp_work_dir:
        os.chdir(temp_work_dir)
        launch_mia(app, args)
        os.chdir(cwd)


def qt_message_handler(message):
    """
    Custom Qt message handler to filter out specific unwanted messages and
    output the remaining ones.

    :param message (str): The message to be handled, potentially filtered and
                          then output.
    """

    for unwanted_message in unwanted_messages:

        if message.strip() == unwanted_message:
            return

        elif unwanted_message in message:
            # Remove the unwanted message but keep the rest of the line
            message = message.replace(unwanted_message, "").strip()

    # Output the remaining message (if any)
    if message:
        sys.stderr.write(message + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populse Mia Application Entry Point."
    )
    parser.add_argument(
        "--multi_instance",
        type=bool,
        default=False,
        help="Set the value of multi_instance.",
    )
    args = parser.parse_args()
    # Print the multi_instance argument value
    logger.info(f"--multi_instance is set to: {args.multi_instance}")
    # This will only be executed when this module is run directly
    # list of unwanted messages to filter out in stdout
    unwanted_messages = [
        "QPixmap::scaleHeight: Pixmap is a null pixmap",
    ]
    # Install the custom Qt message handler
    qInstallMessageHandler(qt_message_handler)
    main(args)
