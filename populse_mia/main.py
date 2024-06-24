# -*- coding: utf-8 -*-
"""The first module used at the mia runtime.

Basically, this module is dedicated to the initialisation of the basic
parameters and the various checks necessary for a successful launch of the
mia's GUI.

:Contains:
    :Function:
        - main

"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

import os
import sys
import tempfile

# PyQt5 imports
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

# main_window = None


def main():
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
    if "NO_ET" not in os.environ:
        os.environ["NO_ET"] = "1"

    if "NIPYPE_NO_ET" not in os.environ:
        os.environ["NIPYPE_NO_ET"] = "1"

    # Trying to fix High DPI Display issue
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # General QApplication class instantiation
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    QApplication.setOverrideCursor(Qt.WaitCursor)

    # Adding the populse projects path to sys.path, if in developer mode
    if (
        not os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        in sys.path
    ):  # "developer" mode
        DEV_MODE = True
        os.environ["MIA_DEV_MODE"] = "1"
        root_dev_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        )
        branch = ""
        populse_bdir = ""
        capsul_bdir = ""
        soma_bdir = ""

        if not os.path.isdir(os.path.join(root_dev_dir, "populse_mia")):
            # Different sources layout - try casa_distro mode
            root_dev_dir = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                )
            )

            if os.path.basename(root_dev_dir) == "populse":
                root_dev_dir = os.path.dirname(root_dev_dir)
                populse_bdir = "populse"
                soma_bdir = "soma"

            print("root_dev_dir:", root_dev_dir)
            branch = os.path.basename(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            print("branch:", branch)

        i = 0
        # Adding populse_mia
        print('\n- Mia in "developer" mode')
        mia_dev_dir = os.path.join(
            root_dev_dir, populse_bdir, "populse_mia", branch
        )
        print("  . Using populse_mia package from {} ...".format(mia_dev_dir))
        sys.path.insert(i, mia_dev_dir)
        pypath.append(mia_dev_dir)
        del mia_dev_dir
        from populse_mia import info

        print(f"    populse_mia version: {info.__version__}")

        # Adding capsul
        if os.path.isdir(os.path.join(root_dev_dir, capsul_bdir, "capsul")):
            i += 1
            capsul_dev_dir = os.path.join(
                root_dev_dir, capsul_bdir, "capsul", branch
            )
            print(
                "  . Using capsul package from {} ...".format(capsul_dev_dir)
            )
            sys.path.insert(i, capsul_dev_dir)
            pypath.append(capsul_dev_dir)
            del capsul_dev_dir

        else:

            try:
                import capsul

            except Exception:
                print("  . capsul package was not found!...")
                package_not_found.append("capsul")

            else:
                capsul_dir = os.path.dirname(os.path.dirname(capsul.__file__))
                print(
                    "  . Using capsul package from {} ...".format(capsul_dir)
                )
                del capsul_dir
                del capsul

        # Adding soma_base:
        if os.path.isdir(os.path.join(root_dev_dir, soma_bdir, "soma-base")):
            i += 1
            soma_b_dev_dir = os.path.join(
                root_dev_dir, soma_bdir, "soma-base", branch, "python"
            )
            print("  . Using soma package from {} ...".format(soma_b_dev_dir))
            sys.path.insert(i, soma_b_dev_dir)
            pypath.append(soma_b_dev_dir)
            del soma_b_dev_dir

        else:

            try:
                import soma

            except Exception:
                print("  . soma package was not found!...")
                package_not_found.append("soma")

            else:
                soma_b_dir = os.path.dirname(os.path.dirname(soma.__file__))
                print("  . Using soma package from {} ...".format(soma_b_dir))
                del soma_b_dir
                del soma

        # Adding soma_workflow:
        if os.path.isdir(
            os.path.join(root_dev_dir, soma_bdir, "soma-workflow")
        ):
            i += 1
            soma_w_dev_dir = os.path.join(
                root_dev_dir, soma_bdir, "soma-workflow", branch, "python"
            )
            print(
                "  . Using soma_workflow package from {} "
                "...".format(soma_w_dev_dir)
            )
            sys.path.insert(i, soma_w_dev_dir)
            pypath.append(soma_w_dev_dir)
            del soma_w_dev_dir

        else:

            try:
                import soma_workflow

            except Exception:
                print("  . soma_workflow package was not found!...")
                package_not_found.append("soma_workflow")

            else:
                soma_w_dir = os.path.dirname(
                    os.path.dirname(soma_workflow.__file__)
                )
                print(
                    "  . Using soma_worflow package from {} ...".format(
                        soma_w_dir
                    )
                )
                del soma_w_dir
                del soma_workflow

        # Adding populse_db:
        if os.path.isdir(
            os.path.join(root_dev_dir, populse_bdir, "populse_db")
        ):
            i += 1
            populse_db_dev_dir = os.path.join(
                root_dev_dir, populse_bdir, "populse_db", branch, "python"
            )
            print(
                "  . Using populse_db package from {} "
                "...".format(populse_db_dev_dir)
            )
            sys.path.insert(i, populse_db_dev_dir)
            pypath.append(populse_db_dev_dir)
            del populse_db_dev_dir

        else:

            try:
                import populse_db

            except Exception:
                print("  . populse_db package was not found!...")
                package_not_found.append("populse_db")

            else:
                populse_db_dir = os.path.dirname(
                    os.path.dirname(populse_db.__file__)
                )
                print(
                    "  . Using populse_db package from {} ...".format(
                        populse_db_dir
                    )
                )
                del populse_db_dir
                del populse_db

        # Adding mia_processes:
        if os.path.isdir(
            os.path.join(root_dev_dir, populse_bdir, "mia_processes")
        ):
            i += 1
            mia_processes_dev_dir = os.path.join(
                root_dev_dir, populse_bdir, "mia_processes", branch
            )
            print(
                "  . Using mia_processes package from {} "
                "...".format(mia_processes_dev_dir)
            )
            sys.path.insert(i, mia_processes_dev_dir)
            pypath.append(mia_processes_dev_dir)
            del mia_processes_dev_dir
            from mia_processes import info

            print(f"    mia_processes version: {info.__version__}")

        else:

            try:
                import mia_processes

            except Exception:
                print("  . mia_processes package was not found!...")
                package_not_found.append("mia_processes")

            else:
                mia_processes_dir = os.path.dirname(
                    os.path.dirname(mia_processes.__file__)
                )
                print(
                    "  . Using mia_processes package from {} "
                    "...".format(mia_processes_dir)
                )
                del mia_processes_dir
                del mia_processes

        del root_dev_dir

        if package_not_found:
            print(
                "\nMia cannot be started because the following packages "
                "were not found:\n"
                + "\n".join(f"- {package}" for package in package_not_found)
            )
            sys.exit(1)

    # elif "CASA_DISTRO" in os.environ:
    #     # If the casa distro development environment is detected,
    #     # developer mode is activated.
    #     os.environ["MIA_DEV_MODE"] = "1"
    #     DEV_MODE = True

    else:  # "user" mode
        os.environ["MIA_DEV_MODE"] = "0"
        DEV_MODE = False
        print('\n- Mia in "user" mode')
        # Where do we import the modules from?
        modules = (
            "populse_mia",
            "capsul",
            "soma",
            "soma_workflow",
            "populse_db",
            "mia_processes",
        )

        for i in modules:
            if i in sys.modules:
                mod = sys.modules[i]

            else:
                mod = __import__(i)
                del sys.modules[i]

            print(
                "  . Using {0} package from {1} ...".format(
                    mod.__name__, mod.__path__[0]
                )
            )

    # Check if nipype, mia_processes and capsul are available on the station.
    # If not available ask the user to install them
    pkg_error = []
    # pkg_error: a list containing nipype and/or mia_processes and/or capsul,
    #            if not currently installed
    capsulVer = None  # capsul version currently installed
    miaProcVer = None  # mia_processes version currently installed
    nipypeVer = None  # nipype version currently installed

    try:
        from capsul import info as capsul_info

        capsulVer = capsul_info.__version__

    except (ImportError, AttributeError) as e:
        pkg_error.append("capsul")
        print("\n" + "*" * 37)
        print("MIA warning {0}: {1}".format(e.__class__, e))
        print("*" * 37 + "\n")

    try:
        __import__("nipype")
        nipypeVer = sys.modules["nipype"].__version__

    except (ImportError, AttributeError) as e:
        pkg_error.append("nipype")
        print("\n" + "*" * 37)
        print("MIA warning {0}: {1}".format(e.__class__, e))
        print("*" * 37 + "\n")

    try:
        __import__("mia_processes")
        miaProcVer = sys.modules["mia_processes"].__version__

    except (ImportError, AttributeError) as e:
        pkg_error.append("mia_processes")
        print("\n" + "*" * 37)
        print("MIA warning {0}: {1}".format(e.__class__, e))
        print("*" * 37 + "\n")

    if pkg_error:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("populse_mia -  warning: ImportError!")

        if len(pkg_error) == 1:
            msg.setText(
                "An issue has been detected with the {0} package. "
                "Please (re)install this package and/or fix the "
                "problems displayed in the standard output. "
                "Then, start again Mia ...".format(pkg_error[0])
            )

        elif len(pkg_error) == 2:
            msg.setText(
                "An issue has been detected with the {0} and {1} packages. "
                "Please (re)install these package and/or fix the "
                "problems displayed in the standard output. "
                "Then, start again Mia ...".format(pkg_error[0], pkg_error[1])
            )

        else:
            msg.setText(
                "An issue has been detected with the {0}, {1} and {2} "
                "packages. Please (re)install these package and/or fix the "
                "problems displayed in the standard output. "
                "Then, start again Mia ...".format(
                    pkg_error[0], pkg_error[1], pkg_error[2]
                )
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

    verify_setup(dev_mode=DEV_MODE, pypath=pypath)
    verify_processes(nipypeVer, miaProcVer, capsulVer)
    check_python_version()
    cwd = os.getcwd()

    with tempfile.TemporaryDirectory() as temp_work_dir:
        os.chdir(temp_work_dir)
        launch_mia(app)
        os.chdir(cwd)


if __name__ == "__main__":
    # this will only be executed when this module is run directly
    main()
