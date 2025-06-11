"""This module is dedicated to populse_mia unit tests.

:Contains:
    :Class:
        - TestMIACase
        - TestMIADataBrowser
        - TestMIAMainWindow
        - TestMIANodeController
        - TestMIAPipelineEditor
        - TestMIAPipelineManagerTab
        - Test_Z_MIAOthers

"""

# flake8: noqa
##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# General imports:

# Other import
import ast
import copy
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

# import threading
import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from time import sleep
from unittest.mock import MagicMock, Mock, patch

import psutil
import yaml

# Nipype import
from nipype.interfaces import Rename, Select
from nipype.interfaces.base.traits_extension import (
    File,
    InputMultiObject,
    OutputMultiPath,
)
from nipype.interfaces.spm import Smooth, Threshold
from packaging import version

# PyQt5 import
from PyQt5 import QtGui, sip
from PyQt5.QtCore import (
    QT_VERSION_STR,
    QCoreApplication,
    QEvent,
    QModelIndex,
    QPoint,
    Qt,
    qInstallMessageHandler,
)
from PyQt5.QtTest import QSignalSpy, QTest
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QFileDialog,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
)
from traits.api import TraitListObject, Undefined

uts_dir = os.path.isdir(
    os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        ),
        "mia_ut_data",
    )
)

if not uts_dir:
    print(
        "\nTo work properly, unit tests need data in the populse_mia(or "
        "populse-mia)/mia_ut_data directory. Please use:\n"
        "git clone https://gricad-gitlab.univ-grenoble-alpes.fr/mia/"
        "mia_ut_data.git\n"
        "in populse_mia directory to download it...\n"
    )
    sys.exit()

populse_mia_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)
# UTs are always in developer mode
os.environ["MIA_DEV_MODE"] = "1"
root_dev_dir = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    )
)

if populse_mia_dir not in sys.path:

    # Adding populse_mia
    if os.path.isdir(os.path.join(root_dev_dir, "populse-mia")):
        mia_dev_dir = os.path.join(root_dev_dir, "populse-mia")

    else:
        mia_dev_dir = os.path.join(root_dev_dir, "populse_mia")

    print("- Using populse_mia package from {} " "...".format(mia_dev_dir))
    sys.path.insert(0, mia_dev_dir)
    del mia_dev_dir

mia_processes_dir = os.path.join(root_dev_dir, "mia_processes")

if mia_processes_dir not in sys.path:

    if os.path.isdir(mia_processes_dir):
        # Adding mia_processes
        print(
            "- Using mia_processes package from {} "
            "...".format(mia_processes_dir)
        )
        sys.path.insert(1, mia_processes_dir)
        del mia_processes_dir

populse_db_dir = os.path.join(root_dev_dir, "populse_db", "python")

if populse_db_dir not in sys.path:

    if os.path.isdir(populse_db_dir):
        # Adding populse_db
        print(
            "- Using populse_db package from {} " "...".format(populse_db_dir)
        )
        sys.path.insert(1, populse_db_dir)
        del populse_db_dir

capsul_dir = os.path.join(root_dev_dir, "capsul")

if capsul_dir not in sys.path:

    if os.path.isdir(capsul_dir):
        # Adding capsul
        print(f"- Using capsul package from {capsul_dir} ...")
        sys.path.insert(1, capsul_dir)
        del capsul_dir

soma_base_dir = os.path.join(root_dev_dir, "soma-base", "python")

if soma_base_dir not in sys.path:

    if os.path.isdir(soma_base_dir):
        # Adding soma-base
        print("- Using soma-base package from {} " "...".format(soma_base_dir))
        sys.path.insert(1, soma_base_dir)
        del soma_base_dir

soma_workflow_dir = os.path.join(root_dev_dir, "soma-workflow", "python")

if soma_workflow_dir not in sys.path:

    if os.path.isdir(soma_workflow_dir):
        # Adding soma-workflow:
        print(
            "- Using soma-workflow package from {} "
            "...".format(soma_workflow_dir)
        )
        sys.path.insert(1, soma_workflow_dir)
        del soma_workflow_dir

# Imports after defining the location of populse packages:

# Capsul import
from capsul.api import (  # noqa: E402
    PipelineNode,
    ProcessNode,
    Switch,
    get_process_instance,
)
from capsul.attributes.completion_engine import (  # noqa: E402
    ProcessCompletionEngine,
)
from capsul.engine import CapsulEngine, WorkflowExecutionError  # noqa: E402
from capsul.pipeline.pipeline import Pipeline  # noqa: E402
from capsul.pipeline.pipeline_workflow import (  # noqa: E402
    workflow_from_pipeline,
)
from capsul.pipeline.process_iteration import ProcessIteration  # noqa: E402
from capsul.process.process import NipypeProcess  # noqa: E402
from capsul.qt_gui.widgets.settings_editor import SettingsEditor  # noqa: E402

# Mia_processes import
from mia_processes.bricks.tools import Input_Filter  # noqa: E402

# soma import
from soma.qt_gui.qt_backend.Qt import (  # noqa: E402
    QItemSelectionModel,
    QTreeView,
)
from soma.qt_gui.qt_backend.QtWidgets import QMenu  # noqa: E402

from populse_mia.data_manager import (  # noqa: E402
    BRICK_EXEC,
    BRICK_EXEC_TIME,
    BRICK_ID,
    BRICK_INIT,
    BRICK_INIT_TIME,
    BRICK_NAME,
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    COLLECTION_HISTORY,
    COLLECTION_INITIAL,
    FIELD_ATTRIBUTES_COLLECTION,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_INTEGER,
    FIELD_TYPE_LIST_BOOLEAN,
    FIELD_TYPE_LIST_DATE,
    FIELD_TYPE_LIST_DATETIME,
    FIELD_TYPE_LIST_FLOAT,
    FIELD_TYPE_LIST_INTEGER,
    FIELD_TYPE_LIST_STRING,
    FIELD_TYPE_LIST_TIME,
    FIELD_TYPE_STRING,
    FIELD_TYPE_TIME,
    NOT_DEFINED_VALUE,
    TAG_BRICKS,
    TAG_CHECKSUM,
    TAG_EXP_TYPE,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_ORIGIN_USER,
    TAG_TYPE,
    TAG_UNIT_MHZ,
    TYPE_NII,
)

# Populse_mia import
from populse_mia.data_manager.data_loader import read_log  # noqa: E402
from populse_mia.data_manager.project import Project  # noqa: E402
from populse_mia.data_manager.project_properties import (  # noqa: E402
    SavedProjects,
)
from populse_mia.software_properties import Config  # noqa: E402
from populse_mia.user_interface.data_browser.modify_table import (  # noqa: E402, E501
    ModifyTable,
)
from populse_mia.user_interface.main_window import MainWindow  # noqa: E402
from populse_mia.user_interface.pipeline_manager.pipeline_editor import (  # noqa: E402, E501
    PipelineEditor,
    save_pipeline,
)
from populse_mia.user_interface.pipeline_manager.pipeline_manager_tab import (  # noqa: E402, E501
    RunProgress,
)
from populse_mia.user_interface.pipeline_manager.process_library import (  # noqa: E402, E501
    PackageLibraryDialog,
)
from populse_mia.user_interface.pop_ups import (  # noqa: E402
    DefaultValueListCreation,
    PopUpAddPath,
    PopUpAddTag,
    PopUpClosePipeline,
    PopUpDeletedProject,
    PopUpDeleteProject,
    PopUpInheritanceDict,
    PopUpNewProject,
    PopUpOpenProject,
    PopUpQuit,
    PopUpRemoveScan,
    PopUpSeeAllProjects,
    PopUpSelectTagCountTable,
)
from populse_mia.utils import (  # noqa: E402; verify_processes,
    check_value_type,
    table_to_database,
    verify_setup,
)

# Working from the scripts directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Disables any etelemetry check.
if "NO_ET" not in os.environ:
    os.environ["NO_ET"] = "1"

if "NIPYPE_NO_ET" not in os.environ:
    os.environ["NIPYPE_NO_ET"] = "1"

# List of unwanted messages to filter out in stdout
unwanted_messages = [
    "QPixmap::scaleHeight: Pixmap is a null pixmap",
]


def qt_message_handler(mode, context, message):
    """Custom Qt message handler to filter out specific messages"""

    for unwanted_message in unwanted_messages:

        if message.strip() == unwanted_message:
            return

        elif unwanted_message in message:
            # Remove the unwanted message but keep the rest of the line
            message = message.replace(unwanted_message, "").strip()

    # Output the remaining message (if any)
    if message:
        sys.stderr.write(message + "\n")


class TestMIACase(unittest.TestCase):
    """Parent class for the test classes of mia.

    :Contains:
        :Method:
            - add_visualized_tag: selects a tag to display with the
              "Visualized tags" pop-up
            - clean_uts_packages: deleting the package added during the UTs or
              old one still existing
            - create_mock_jar: creates a mocked java (.jar) executable
            - execute_QDialogAccept: accept (close) a QDialog instance
            - find_item_by_data: looks for a QModelIndex whose contents
              correspond to the argument data
            - get_new_test_project: create a temporary project that can
              be safely modified
            - proclibview_nipype_state: give the state of nipype in the process
            - proclibview_nipype_reset_state: reset nipype to its initial state
              (before the start of the current test) in the process library
              view
            - restart_MIA: restarts MIA within a unit test
            - setUp: called automatically before each test method
            - setUpClass: called before tests in the individual class
            - tearDown: cleans up after each test method
            - tearDownClass: called after tests in the individual class
    """

    def add_visualized_tag(self, tag):
        """With the "Visualized tags" pop-up open, selects a tag to display.

        - Should be called, with a delay, before opening the "Visualized tags"
          pop-up, i.e.:
              QTimer.singleShot(1000, lambda:self.add_visualized_tag(
              'AcquisitionDate'))
          It's currently not the case
          (see TestMIANodeController.test_filter_widget()).

        :param tag: the tag to be displayed (str)
        """

        w = self._app.activeWindow()

        if isinstance(w, QDialog):
            visualized_tags = w.layout().itemAt(0).widget()
            tags_list = visualized_tags.list_widget_tags

            if version.parse(QT_VERSION_STR) == version.parse("5.9.2"):
                found_item = tags_list.findItems(tag, Qt.MatchExactly)

            else:
                found_item = tags_list.findItems(
                    tag, Qt.MatchFlag.MatchExactly
                )

            tags_list.setCurrentItem(found_item[0])
            visualized_tags.click_select_tag()
            w.accept()

    def clean_uts_packages(self, proc_lib_view):
        """Deleting the packages added during the UTs."""

        pck2remove = [
            k
            for (k, v) in proc_lib_view.to_dict().items()
            if "UTs_processes" in k
        ]
        user_proc = proc_lib_view.to_dict().get("User_processes", None)

        if user_proc is not None and "Unit_test_pipeline" in user_proc:
            pck2remove.append("Unit_test_pipeline")

        # Mocks the MessageBox().question() for populse_mia.user_interface.
        # pipeline_manager.process_library.PackageLibraryDialog.delete_package()
        QMessageBox.question = Mock(return_value=QMessageBox.Yes)

        # Mocks the event.key
        event = Mock()
        event.key = lambda: Qt.Key_Delete

        # Remove
        for k in pck2remove:
            pkg_index = self.find_item_by_data(proc_lib_view, k)
            (
                proc_lib_view.selectionModel().select(
                    pkg_index, QItemSelectionModel.SelectCurrent
                )
            )
            proc_lib_view.keyPressEvent(event)

    def create_mock_jar(self, path):
        """
        Create a mock Java executable (.jar) for testing.

        :param path (str): Full path to the output .jar file.
        :returns (int): 0 if creation succeeded, 1 otherwise.
        """

        (folder, name) = os.path.split(path)

        java_source = (
            "public class MockApp {\n"
            + "    public static void main(String[] args){\n"
            + '        System.out.println("Executed mock java app.");\n'
            + "    }\n"
            + "}"
        )

        # Write Java source file
        with open(os.path.join(folder, "MockApp.java"), "w") as f:
            f.write(java_source)

        # Write MANIFEST file (note the trailing newline is required)
        with open(os.path.join(folder, "MANIFEST.MF"), "w") as f:
            f.write("Main-Class:  MockApp\n")

        # Check for Java runtime availability
        try:
            subprocess.run(
                ["java", "-version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        except (FileNotFoundError, subprocess.CalledProcessError):
            print("OpenJDK Runtime is not installed or not found.")
            return 1

        # Compile Java source and package jar
        try:
            subprocess.run(
                ["javac", "-d", ".", "MockApp.java"], cwd=folder, check=True
            )
            subprocess.run(
                ["jar", "cvmf", "MANIFEST.MF", name, "MockApp.class"],
                cwd=folder,
                check=True,
            )
        except subprocess.CalledProcessError:
            print("Failed to compile or package the Java mock executable.")
            return 1

        if not os.path.exists(path):
            print("The java executable was not created")
            return 1

        return 0

    def execute_QDialogAccept(self):
        """Accept (close) a QDialog window."""

        w = self._app.activeWindow()

        if isinstance(w, QDialog):
            w.accept()

    def find_item_by_data(
        self, q_tree_view: QTreeView, data: str
    ) -> QModelIndex:
        """Looks for a QModelIndex, in a QTreeView instance."""

        assert isinstance(
            q_tree_view, QTreeView
        ), "first argument is not a QTreeView instance!"
        q_tree_view.expandAll()
        index = q_tree_view.indexAt(QPoint(0, 0))

        while index.data() and index.data() != data:
            index = q_tree_view.indexBelow(index)

        return index

    def get_new_test_project(self, name="test_project", light=False):
        """Copies a test project where it can be safely modified.

        - The new project is created in the /tmp (/Temp) folder.

        :param name: name of the directory containing the project (str)
        :param light: True to copy a project with few documents (bool)
        """

        new_test_proj = os.path.join(self.project_path, name)

        if os.path.exists(new_test_proj):
            shutil.rmtree(new_test_proj)

        test_proj = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            ),
            "mia_ut_data",
            "resources",
            "mia",
            "light_test_project" if light else "project_8",
        )
        shutil.copytree(test_proj, new_test_proj)
        return new_test_proj

    def proclibview_nipype_state(self, proc_lib_view):
        """Give the state of nipype proc_lib_view.

        :param proc_lib_view: the process library view object

        :return: the state of nipype proc_lib_view:
                 - None: proc_lib_view is empty or nipype is not loaded.
                 - 'nipype': 'nipype' is loaded but 'interfaces' not.
                 - 'nipype.interface': 'nipype.interface' is loaded but
                                       'DataGrabber' not.
                 - 'process_enabled': 'nipype.interface.DataGrabber' is
                                      loaded.
        """

        if proc_lib_view.to_dict():
            if proc_lib_view.to_dict().get("nipype"):
                if proc_lib_view.to_dict().get("nipype").get("interfaces"):
                    if (
                        proc_lib_view.to_dict()
                        .get("nipype")
                        .get("interfaces")
                        .get("DataGrabber")
                    ):
                        state = (
                            proc_lib_view.to_dict()
                            .get("nipype")
                            .get("interfaces")
                            .get("DataGrabber")
                        )

                    else:
                        state = "nipype.interfaces"

                else:
                    state = "nipype"

            else:
                state = None

        else:
            state = None

        return state

    def proclibview_nipype_reset_state(
        self, main_window, ppl_manager, init_state
    ):
        """Reset the process library view to its initial state.

        :param main_window: the main window object
        :param ppl_manager: the pipeline manager object
        :param init_state: the initial state of nipype proc_lib_view:
                           - None: proc_lib_view is empty or nipype is not
                                   loaded.
                           - 'nipype': 'nipype' is loaded but 'interfaces' not.
                           - 'nipype.interface': 'nipype.interface' is loaded
                                                 but 'DataGrabber' not.
                           - 'process_enabled': 'nipype.interface.DataGrabber'
                                                is loaded.
        """
        main_window.package_library_pop_up()
        pkg_lib_window = main_window.pop_up_package_library
        ppl_manager.processLibrary.process_library.pkg_library.is_path = False

        if init_state is None:
            pkg_lib_window.line_edit.setText("nipype")
            # Clicks on remove package
            pkg_lib_window.layout().children()[0].layout().children()[
                1
            ].itemAt(1).widget().clicked.emit()

        elif init_state == "nipype":
            pkg_lib_window.line_edit.setText("nipype.interfaces")
            # Clicks on remove package
            pkg_lib_window.layout().children()[0].layout().children()[
                1
            ].itemAt(1).widget().clicked.emit()

        elif init_state == "nipype.interfaces":
            pkg_lib_window.line_edit.setText("nipype.interfaces.DataGrabber")
            # Clicks on remove package
            pkg_lib_window.layout().children()[0].layout().children()[
                1
            ].itemAt(1).widget().clicked.emit()

        else:
            pkg_lib_window.line_edit.setText("nipype.interfaces.DataGrabber")
            # Clicks on add package
            pkg_lib_window.layout().children()[0].layout().children()[
                1
            ].itemAt(0).widget().clicked.emit()

        pkg_lib_window.ok_clicked()

    def restart_MIA(self):
        """Restarts MIA within a unit test.

        - Can be used to restart MIA after changing the controller version in
          Mia preferences.
        """

        # Close current window
        if self.main_window:
            self.main_window.close()
            self.main_window.deleteLater()
            self._app.processEvents()

        # Reset config/state
        config = Config(properties_path=self.properties_path)
        config.set_opened_projects([])
        config.set_user_mode(False)
        config.saveConfig()
        # Reset internal app state (without recreating QApplication)
        self.project = Project(None, True)
        self.main_window = MainWindow(self.project, test=True)

    def setUp(self):
        """Called before each test"""

        # Make _app available at instance level
        self._app = self.__class__._app
        # All the tests are run in admin mode
        config = Config(properties_path=self.properties_path)
        config.set_user_mode(False)

        self.project = Project(None, True)
        self.main_window = MainWindow(self.project, test=True)

    @classmethod
    def setUpClass(cls):
        """Called once at the beginning of the class"""

        cls.properties_path = os.path.join(
            tempfile.mkdtemp(prefix="mia_tests"), "dev"
        )
        cls.project_path = os.path.join(
            tempfile.mkdtemp(prefix="mia_project"), "project"
        )
        # hack the Config class to get properties path, because some Config
        # instances are created out of our control in the code
        Config.properties_path = cls.properties_path

        # properties folder management / initialisation:
        properties_dir = os.path.join(cls.properties_path, "properties")

        if not os.path.exists(properties_dir):
            os.makedirs(properties_dir, exist_ok=True)

        if not os.path.exists(
            os.path.join(properties_dir, "saved_projects.yml")
        ):
            with open(
                os.path.join(properties_dir, "saved_projects.yml"),
                "w",
                encoding="utf8",
            ) as configfile:
                yaml.dump(
                    {"paths": []},
                    configfile,
                    default_flow_style=False,
                    allow_unicode=True,
                )

        if not os.path.exists(os.path.join(properties_dir, "config.yml")):
            with open(
                os.path.join(properties_dir, "config.yml"),
                "w",
                encoding="utf8",
            ) as configfile:
                yaml.dump(
                    "gAAAAABd79UO5tVZSRNqnM5zzbl0KDd7Y98KCSKCNizp9aDq"
                    "ADs9dAQHJFbmOEX2QL_jJUHOTBfFFqa3OdfwpNLbvWNU_rR0"
                    "VuT1ZdlmTYv4wwRjhlyPiir7afubLrLK4Jfk84OoOeVtR0a5"
                    "a0k0WqPlZl-y8_Wu4osHeQCfeWFKW5EWYF776rWgJZsjn3fx"
                    "Z-V2g5aHo-Q5aqYi2V1Kc-kQ9ZwjFBFbXNa1g9nHKZeyd3ve"
                    "6p3RUSELfUmEhS0eOWn8i-7GW1UGa4zEKCsoY6T19vrimiuR"
                    "Vy-DTmmgzbbjGkgmNxB5MvEzs0BF2bAcina_lKR-yeICuIqp"
                    "TSOBfgkTDcB0LVPBoQmogUVVTeCrjYH9_llFTJQ3ZtKZLdeS"
                    "tFR5Y2I2ZkQETi6m-0wmUDKf-KRzmk6sLRK_oz6GmuTAN8A5"
                    "1au2v1M=",
                    configfile,
                    default_flow_style=False,
                    allow_unicode=True,
                )

            # processes/User_processes folder management / initialisation:
            user_processes_dir = os.path.join(
                cls.properties_path, "processes", "User_processes"
            )

            if not os.path.exists(user_processes_dir):
                os.makedirs(user_processes_dir, exist_ok=True)

            if not os.path.exists(
                os.path.join(user_processes_dir, "__init__.py")
            ):
                Path(
                    os.path.join(
                        user_processes_dir,
                        "__init__.py",
                    )
                ).touch()

        cls._app = QApplication.instance() or QApplication(sys.argv)

    def tearDown(self):
        """Called after each test"""

        if self.main_window:
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None

        # Removing the opened projects (in CI, the tests are run twice)
        config = Config(properties_path=self.properties_path)
        config.set_opened_projects([])
        config.saveConfig()

        for widget in self._app.topLevelWidgets():

            try:

                if not sip.isdeleted(widget):
                    widget.close()
                    widget.deleteLater()

            except Exception as e:
                print(f"Error closing widget: {e}")

        self._app.processEvents()
        self.project = None
        self.main_window = None

    @classmethod
    def tearDownClass(cls):
        """Called once at the end of the class"""

        if os.path.exists(cls.properties_path):
            shutil.rmtree(cls.properties_path)

        if os.path.exists(cls.project_path):
            shutil.rmtree(cls.project_path)

        cls._app.quit()
        del cls._app


# class Test_Z_MIAOthers(TestMIACase):
class Test1AMIAOthers(TestMIACase):
    """Tests for other parts of the MIA software that do not relate much
    with the other classes.

    :Contains:
        :Method:
            - _mock_mouse_event: mock QMouseEvent for a right-click at
                                 position (0, 0)
            - test_check_setup: check that Mia's configuration control is
                                working correctly
            - test_iteration_table: plays with the iteration table
            - test_process_library: install the brick_test and then remove it

            - test_verify_processes: check that Mia's processes control is
                                     working correctly (currently commented)
    """

    def _mock_mouse_event(self):
        """
        Returns a mock QMouseEvent for a right-click at position (0, 0).
        """
        event = Mock()
        event.pos.return_value = QPoint(0, 0)
        event.button.return_value = Qt.RightButton
        return event

    @patch("PyQt5.QtWidgets.QDialog.exec", return_value=QDialog.Accepted)
    def test_check_setup(self, mock_exec):
        """Check that Mia's configuration control is working correctly.

        - Tests: utils.verify_setup()
        """
        dot_mia_config = os.path.join(
            os.path.dirname(self.properties_path), "configuration_path.yml"
        )
        verify_setup(dev_mode=True, dot_mia_config=dot_mia_config)
        mock_exec.assert_called_once()

    @patch(
        "populse_mia.user_interface.pipeline_manager.iteration_table."
        "PopUpSelectTagCountTable.exec_",
        return_value=True,
    )
    @patch("PyQt5.QtWidgets.QDialog.exec_", return_value=QDialog.Accepted)
    def test_iteration_table(self, mock_exec, mock_pop_up):
        """Opens a new project, initializes the pipeline iteration and changes
        its parameters.

        - Tests: IterationTable behavior without asynchronous dialogs.

        - Mocks: the execution of a PopUpSelectTagCountTable and a QDialog
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Sets shortcuts for objects that are often used
        iter_table = self.main_window.pipeline_manager.iterationTable
        ppl_manager = self.main_window.pipeline_manager
        ppl_editor = ppl_manager.pipelineEditorTabs.get_current_editor()

        # Allows for the iteration of the pipeline
        iter_table.check_box_iterate.setChecked(True)

        # Adds a tag and asserts that a tag button was added
        iter_table.add_tag()
        self.assertEqual(len(iter_table.push_buttons), 3)
        self.assertEqual(iter_table.push_buttons[-1].text(), "Tag n°3")

        # Fill the 'values_list' with the tag values in the documents
        iter_table.push_buttons[2].setText("BandWidth")
        iter_table.fill_values(2)
        self.assertTrue(len(iter_table.values_list[-1]) == 3)
        self.assertTrue(isinstance(iter_table.values_list[-1][0], list))
        self.assertEqual(iter_table.values_list[-1][0], [65789.48])

        # Removes a tag and asserts that a tag button was removed
        iter_table.remove_tag()
        self.assertEqual(len(iter_table.push_buttons), 2)

        # Selects a tag to iterate over, tests 'select_iteration_tag' while
        # mocking a 'PopUpSelectTagCountTable'.
        # Due to the PopUpSelectTagCountTable.exec_ mock,
        # 'iterated_tag' is set as None
        ppl_editor.iterated_tag = "BandWidth"
        iter_table.select_iteration_tag()
        self.assertIsNone(ppl_editor.iterated_tag)

        # Filters the scans matching the selected  'iterated_tag'
        # Since the execution is mocked, 'tag_values_list' becomes empty
        iter_table.filter_values()
        self.assertEqual(ppl_editor.tag_values_list, [])

        # Updates the button with the selected tag
        iter_table.update_selected_tag("Bandwidth")

        # Selects the visualized tag
        iter_table.select_visualized_tag(0)

        # Sends the data browser scans to the pipeline manager and updates the
        # iterated tags
        with iter_table.project.database.data() as database_data:
            SCANS_LIST = database_data.get_document_names(COLLECTION_CURRENT)

        ppl_manager.scan_list = SCANS_LIST
        iter_table.update_iterated_tag()

        # Updates the iteration table, tests 'update_table' while
        # mocking the execution of 'filter_documents'
        DOC_1_NAME = SCANS_LIST[0]

        with iter_table.project.database.data() as database_data:
            DOC_1 = database_data.get_document(COLLECTION_CURRENT, DOC_1_NAME)

        # Patch the method directly on the real class
        # (no mocking of `data()` or context managers)
        with patch.object(
            database_data.__class__, "filter_documents", return_value=DOC_1
        ):
            ppl_editor.iterated_tag = "BandWidth"
            iter_table.update_table()

        # Asserts that the iteration table has one item
        self.assertIsNotNone(iter_table.iteration_table.item(0, 0))
        self.assertIsNone(iter_table.iteration_table.item(1, 0))

        # Asserts that QDialog.exec_ and PopUpSelectTagCountTable.exec_
        # has been called twice
        self.assertEqual(mock_exec.call_count, 2)
        self.assertEqual(mock_pop_up.call_count, 2)

    @patch("PyQt5.QtWidgets.QMenu.exec_")
    @patch(
        "PyQt5.QtWidgets.QMessageBox.question", return_value=QMessageBox.Yes
    )
    @patch("PyQt5.QtWidgets.QMessageBox.exec", return_value=None)
    def test_process_library(
        self, mock_msgbox_exec, mock_msgbox_question, mock_menu_exec
    ):
        """
        Tests row insert, rename, delete in ProcessLibrary with
        mocking dialogs.

        The process library is located at the left corner of the pipeline
        manager tab, where the list of available bricks is shown.
        """
        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_manager.processLibrary.process_config = {}
        ppl_manager.processLibrary.packages = {
            "User_processes": {"Tests": "process_enabled"}
        }
        ppl_manager.processLibrary.paths = []
        ppl_manager.processLibrary.pkg_library.save()
        proc_lib = ppl_manager.processLibrary.process_library

        # Switches to pipeline manager
        self.main_window.tabs.setCurrentIndex(2)

        # Gets the child count
        child_count = proc_lib._model.getNode(QModelIndex()).childCount()
        row_data = "untitled" + str(child_count)

        # Insert new row to the process library
        success = proc_lib._model.insertRow(0)
        self.assertTrue(success)

        # Gets its index and selects it
        row_index = self.find_item_by_data(proc_lib, row_data)
        self.assertIsNotNone(row_index)
        proc_lib.selectionModel().select(
            row_index, QItemSelectionModel.SelectCurrent
        )

        # Test mime data of the row widget
        mime_data = proc_lib._model.mimeData([row_index])
        self.assertEqual(
            mime_data.data("component/name").data(),
            bytes(row_data, encoding="utf-8"),
        )

        # Rename the row
        set_result = proc_lib._model.setData(row_index, "untitled101")
        self.assertTrue(set_result)
        self.assertEqual(row_index.data(), "untitled101")

        # Simulate delete key press
        event = Mock()
        event.key = lambda *args: Qt.Key_Delete
        proc_lib.keyPressEvent(event)

        # Create dummy QAction objects
        dummy_action_remove = QAction("Remove package")
        dummy_action_delete = QAction("Delete package")

        # Monkey-patch QTreeView.mousePressEvent to avoid calling base
        # implementation
        with patch.object(QTreeView, "mousePressEvent", return_value=True):
            # Simulate right-click and select "Remove package"
            proc_lib._model.insertRow(0)
            row_index_remove = self.find_item_by_data(
                proc_lib, "untitled" + str(child_count + 1)
            )
            self.assertIsNotNone(row_index_remove)
            mock_menu_exec.return_value = dummy_action_remove
            res = proc_lib.mousePressEvent(self._mock_mouse_event())
            self.assertTrue(res)
            self.assertEqual(mock_menu_exec.call_count, 1)

            # Simulate right-click and select "Delete package"
            proc_lib._model.insertRow(0)
            row_index_delete = self.find_item_by_data(
                proc_lib, "untitled" + str(child_count + 2)
            )
            self.assertIsNotNone(row_index_delete)
            mock_menu_exec.return_value = dummy_action_delete
            proc_lib.mousePressEvent(self._mock_mouse_event())
            self.assertEqual(mock_menu_exec.call_count, 2)
            proc_lib.mousePressEvent(self._mock_mouse_event())
            # MessageBox.question should have been called (for
            # delete confirmation)
            self.assertGreaterEqual(mock_msgbox_question.call_count, 1)

    @unittest.skip("skip this test until it has been repaired.")
    def test_verify_processes(self):
        """Check that Mia's processes control is working correctly

        - Tests: utils.verify_processes()
        """
        config = Config()
        proc_config = os.path.join(
            config.get_properties_path(), "properties", "process_config.yml"
        )

        with open(proc_config) as stream:
            proc_content = yaml.load(stream, Loader=yaml.FullLoader)

        self.assertEqual(proc_content, {"Packages": {}, "Paths": []})
        verify_processes("nipype_ver", "mia_proc_ver", "capsul_ver")

        with open(proc_config) as stream:
            proc_content = yaml.load(stream, Loader=yaml.FullLoader)

        self.assertTrue("capsul" in proc_content["Packages"])
        self.assertTrue("mia_processes" in proc_content["Packages"])
        self.assertTrue("nipype" in proc_content["Packages"])
        self.assertEqual(proc_content["Paths"], [])
        self.assertEqual(
            proc_content["Versions"],
            {
                "capsul": "capsul_ver",
                "mia_processes": "mia_proc_ver",
                "nipype": "nipype_ver",
            },
        )


class TestMIADataBrowser(TestMIACase):
    """Tests for the data browser tab (DataBrowser).

    :Contains:
        :Method:
            - assert_scans_present: Asserts that all expected scan names are
                                    present in the given list.
            - get_cell_text: Returns the text of the QLabel inside a cell
                             widget.
            - get_db_and_databrowser_value: Returns current, initial DB values
                                            and UI value for a given tag.
            - get_visible_scans: Returns the list of scan names currently
                                 visible in the table.
            - suppress_item_changed_signal: Temporarily disconnects and
                                            reconnects the itemChanged signal.
            - test_add_path: Tests the popup to add a path.
            - test_add_tag: Tests the pop up adding a tag.
            - test_advanced_search: Tests the advanced search widget.
            - test_brick_history: Tests the brick history popup.
            - test_clear_cell: tests the method clearing cells
            - test_clone_tag: tests the pop up cloning a tag
            - test_count_table: tests the count table popup
            - test_mia_preferences: tests the Mia preferences popup
            - test_mini_viewer: selects scans and display them in the mini
              viewer
            - test_modify_table: tests the modify table module
            - test_multiple_sort: tests the multiple sort popup
            - test_multiple_sort_appendix: adds and removes tags in the data
              browser
            - test_openTagsPopUp: opens a pop-up to select the legend of the
              thumbnails
            - test_open_project: tests project opening
            - test_project_filter: tests project filter opening
            - test_project_properties: tests saved projects addition and
              removal
            - test_proj_remov_from_cur_proj: tests that the projects are
              removed from the list of current projects
            - test_rapid_search: tests the rapid search bar
            - test_remove_scan: tests scans removal in the DataBrowser
            - test_remove_tag: tests the popup removing user tags
            - test_reset_cell: tests the method resetting the selected
              cells
            - test_reset_column: tests the method resetting the columns
              selected
            - test_reset_row: test row reset
            - test_save_project: test opening & saving of a project
            - test_send_doc_to_pipeline_manager: tests the popup sending
              documents to the pipeline manager
            - test_set_value: tests the values modifications
            - test_show_brick_history: opens the history pop-up for
              scans with history related to a brick
            - test_sort: tests the sorting in the DataBrowser
            - test_table_data_add_columns: adds tag columns to the table data
              window
            - test_table_data_appendix: opens a project and tests miscellaneous
              methods of the table data view, in the data browser
            - test_table_data_context_menu: right clicks a scan to show the
              context menu table, and choses one option
            - test_undo_redo_databrowser: tests data browser undo/redo
            - test_unnamed_proj_soft_open: tests unnamed project
              creation at software opening
            - test_update_default_value: updates the values when a list
              of default values is created
            - test_utils: test the utils functions
            - test_visualized_tags: tests the popup modifying the
              visualized tags
    """

    def assert_scans_present(self, scans, expected_subset):
        """
        Asserts that all expected scan names are present in the given list.
        """

        for expected in expected_subset:
            self.assertIn(expected, scans)

    def get_cell_text(self, table, row, column, label_index=0):
        """
        Utility method to retrieve the text of the QLabel inside a cell
        widget.

        :param table (QTableWidget): The table containing the cell.
        :param row (int): The row index.
        :param column (int): The column index.
        :param label_index (int): If multiple labels are present, which
                                    one to return. Default is 0 (first QLabel
                                    found).
        :returns (str): The text of the QLabel, or fails the test if not
                        found.
        """
        widget = table.cellWidget(row, column)
        self.assertIsNotNone(widget, f"No widget at cell ({row}, {column})")
        labels = widget.findChildren(QLabel)
        self.assertGreater(
            len(labels),
            label_index,
            f"Not enough QLabel widgets in cell ({row}, {column})",
        )

        return labels[label_index].text()

    def get_db_and_databrowser_value(self, main_window, row_nb, tag):
        """
        Fetches the current and initial values of a given tag from the
        database, along with the corresponding value and item from the data
        browser UI.

        :param main_window (QMainWindow): The main application window
                                          containing the project and data
                                          browser.
        :param row_nb (int): The row index in the data browser table.
        :param tag (str): The name of the tag (column) to retrieve.

        :returns (tuple): A 4-tuple containing:
            - value (Any): The current value from the database
                           (COLLECTION_CURRENT).
            - value_initial (Any): The initial value from the database
                                   (COLLECTION_INITIAL).
            - value_ui (str | None): The value displayed in the data browser
                                     UI, or None if not available.
            - item (QTableWidgetItem | None): The table item corresponding to
                                              the tag, or None if not found.
        """
        table = main_window.data_browser.table_data
        col = table.get_tag_column(tag)
        scan_name = table.item(row_nb, 0).text()
        item = table.item(row_nb, col)
        value_ui = item.text() if item is not None else None

        with main_window.project.database.data() as db:
            value = db.get_value(COLLECTION_CURRENT, scan_name, tag)
            value_initial = db.get_value(COLLECTION_INITIAL, scan_name, tag)

        return value, value_initial, value_ui, item

    def get_visible_scans(self):
        """
        Returns the list of scan names currently visible in the table.
        """
        self._app.processEvents()
        visible_scans = []

        for row in range(self.main_window.data_browser.table_data.rowCount()):

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                item = self.main_window.data_browser.table_data.item(row, 0)
                visible_scans.append(item.text())

        return visible_scans

    @contextmanager
    def suppress_item_changed_signal(self, table_data):
        """
        Temporarily disables the itemChanged signal to prevent unwanted slot
        execution during programmatic updates to the table data.

        :param table_data (QTableWidget): The data browser's table widget
                                          whose itemChanged signal is to be
                                          suppressed.

        :yields: None. The context block is executed with the signal
                       disconnected, and it is reconnected automatically
                       afterward.
        """
        table_data.itemChanged.disconnect()

        try:
            yield

        finally:
            table_data.itemChanged.connect(table_data.change_cell_color)

    def test_add_path(self):
        """
        Tests importing a document into the project via the DataBrowser UI.

        - Verifies behavior of `DataBrowser.add_path()` and `PopUpAddPath`.
        - Mocks `QFileDialog.getOpenFileNames` and `QMessageBox.show`.
        - Checks:
            - Handling of empty or invalid fields.
            - Successful addition of a valid document.
            - Duplicate document addition behavior.
        """
        # Sets shortcuts for often used objects
        ppl_manager = self.main_window.pipeline_manager
        table_data = self.main_window.data_browser.table_data
        # Creates a new project folder and adds one document to the
        # project, sets the plug value that is added to the database
        project_8_path = self.get_new_test_project()
        ppl_manager.project.folder = project_8_path
        raw_data_folder = os.path.join(project_8_path, "data", "raw_data")
        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )
        DOCUMENT_1 = os.path.abspath(os.path.join(raw_data_folder, NII_FILE_1))

        with patch("PyQt5.QtWidgets.QMessageBox.show"):
            # Opens the 'add_path' pop-up
            self.main_window.data_browser.table_data.add_path()
            add_path = self.main_window.data_browser.table_data.pop_up_add_path
            # Case 1: Try adding without filling any fields
            QTest.mouseClick(add_path.ok_button, Qt.LeftButton)
            self.assertEqual(add_path.msg.text(), "Invalid arguments")
            # Case 2: Invalid document path
            add_path.file_line_edit.setText(str([DOCUMENT_1 + "_"]))
            add_path.type_line_edit.setText(str([TYPE_NII]))
            QTest.mouseClick(add_path.ok_button, Qt.LeftButton)
            self.assertEqual(add_path.msg.text(), "Invalid arguments")
            # Case 3: Valid document addition
            add_path.file_line_edit.setText(str([DOCUMENT_1]))
            add_path.type_line_edit.setText(str([TYPE_NII]))
            QTest.mouseClick(add_path.ok_button, Qt.LeftButton)

            # Asserts that the document was added into the data browser
            # A regular '.split('/')' will not work in Windows OS
            with ppl_manager.project.database.data() as database_data:
                filename = os.path.split(
                    database_data.get_document_names(COLLECTION_CURRENT)[0]
                )[-1]
                self.assertTrue(filename in DOCUMENT_1)
                self.assertEqual(table_data.rowCount(), 1)

            # Case 4: QFileDialog file selection by mocked extensions
            for ext in ["nii", "mat", "txt"]:

                with patch(
                    "PyQt5.QtWidgets.QFileDialog.getOpenFileNames",
                    return_value=([f"file.{ext}"], "All Files (*)"),
                ):
                    add_path.file_to_choose()

            # Case 5: Try saving the same document again
            with self.project.database.data(write=True) as database_data:
                database_data.add_document(COLLECTION_CURRENT, DOCUMENT_1)

            add_path.file_line_edit.setText(str([DOCUMENT_1]))
            add_path.save_path()

    def test_add_tag(self):
        """
        Test the add tag functionality in the data browser.

        This test verifies that:
        - Empty tag names are properly rejected
        - Duplicate tag names are properly rejected
        - Invalid default values for the selected type are rejected
        - Valid string tags are successfully added to the database and UI
        - List-type tags (Integer List) are properly created and displayed

        """
        # Sets shortcuts for often used objects
        data_browser = self.main_window.data_browser
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Use patch context manager instead of direct modification
        with patch("PyQt5.QtWidgets.QMessageBox.exec", return_value=None):
            # === Test: Empty tag name ===
            data_browser.add_tag_action.trigger()
            add_tag = data_browser.pop_up_add_tag
            QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
            self.assertEqual(
                add_tag.msg.text(), "The tag name cannot be empty"
            )
            # === Test: Duplicate tag name ===
            add_tag.text_edit_tag_name.setText(TAG_TYPE)
            QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
            self.assertEqual(
                add_tag.msg.text(), "This tag name already exists"
            )
            # === Test: Invalid default value for Integer ===
            add_tag.text_edit_tag_name.setText("Test")
            add_tag.combo_box_type.setCurrentText("Integer")
            add_tag.type = FIELD_TYPE_INTEGER
            add_tag.text_edit_default_value.setText("Should be integer")
            QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
            self.assertEqual(add_tag.msg.text(), "Invalid default value")
            # === Test: Valid String tag creation ===
            add_tag.text_edit_tag_name.setText("Test")
            add_tag.combo_box_type.setCurrentText("String")
            add_tag.type = FIELD_TYPE_STRING
            add_tag.text_edit_default_value.setText("def_value")
            QTest.qWait(200)
            QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)

            # Verify tag was added to database
            with self.main_window.project.database.data() as database_data:

                # Check if tag exists in both collections
                for collection in [COLLECTION_CURRENT, COLLECTION_INITIAL]:
                    self.assertIn(
                        "Test", database_data.get_field_names(collection)
                    )

                    # Check default value for each document
                    for doc in database_data.get_document_names(collection):
                        self.assertEqual(
                            database_data.get_value(collection, doc, "Test"),
                            "def_value",
                        )

            # Verify tag appears in UI with correct value
            test_column = data_browser.table_data.get_tag_column("Test")

            for row in range(data_browser.table_data.rowCount()):
                item = data_browser.table_data.item(row, test_column)
                self.assertEqual(item.text(), "def_value")

        # === Test: Valid Integer List tag creation ===
        with patch("PyQt5.QtWidgets.QMessageBox.exec", return_value=None):
            data_browser.add_tag_action.trigger()
            add_tag = data_browser.pop_up_add_tag
            add_tag.text_edit_tag_name.setText("Test_list")
            # Test all combo box types properly load
            combo_box_types = [
                "String",
                "Integer",
                "Float",
                "Boolean",
                "Date",
                "Datetime",
                "Time",
                "String List",
                "Integer List",
                "Float List",
                "Boolean List",
                "Date List",
                "Datetime List",
                "Time List",
            ]

            for data_type in combo_box_types:
                add_tag.combo_box_type.setCurrentText(data_type)

            # Set to Integer List for our test
            add_tag.combo_box_type.setCurrentText("Integer List")
            # Simulate list value creation
            QTest.mouseClick(add_tag.text_edit_default_value, Qt.LeftButton)
            QTest.mouseClick(
                (
                    add_tag.text_edit_default_value.list_creation.add_element_label
                ),
                Qt.LeftButton,
            )
            # Add items to table
            table = add_tag.text_edit_default_value.list_creation.table

            for col, value in enumerate([1, 2, 3]):
                item = QTableWidgetItem(str(value))
                table.setItem(0, col, item)

            # Close the list dialog
            QTest.mouseClick(
                add_tag.text_edit_default_value.list_creation.ok_button,
                Qt.LeftButton,
            )
            self.assertEqual(
                add_tag.text_edit_default_value.text(), "[1, 2, 3]"
            )
            # Confirm tag creation
            QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
            # Verify the list tag appears in the UI
            test_list_column = data_browser.table_data.get_tag_column(
                "Test_list"
            )

            for row in range(data_browser.table_data.rowCount()):
                item = data_browser.table_data.item(row, test_list_column)
                self.assertEqual(item.text(), "[1, 2, 3]")

        self._app.processEvents()

    def test_advanced_search(self):
        """Tests the advanced search widget."""
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")
        self._app.processEvents()

        initial_expected = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01"
            "-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04"
            "-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-05"
            "-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-06"
            "-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-08"
            "-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-09"
            "-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-10"
            "-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-11"
            "-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27-2014-02-"
            "14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
        ]

        scans = self.get_visible_scans()
        self.assertEqual(len(scans), 9)
        self.assert_scans_present(scans, initial_expected)

        # Open advanced search
        QTest.mouseClick(
            self.main_window.data_browser.advanced_search_button, Qt.LeftButton
        )
        self._app.processEvents()

        adv_search = self.main_window.data_browser.advanced_search
        self.assertEqual(len(adv_search.rows), 1)

        first_row = adv_search.rows[0]
        QTest.mouseClick(first_row[6], Qt.LeftButton)  # + button
        self._app.processEvents()
        self.assertEqual(len(adv_search.rows), 2)

        second_row = adv_search.rows[1]
        QTest.mouseClick(second_row[5], Qt.LeftButton)  # - button
        self._app.processEvents()
        self.assertEqual(len(adv_search.rows), 1)

        first_row = adv_search.rows[0]
        QTest.mouseClick(first_row[5], Qt.LeftButton)  # - button again
        self._app.processEvents()
        self.assertEqual(len(adv_search.rows), 1)

        # Apply filter
        field, condition, value = first_row[2], first_row[3], first_row[4]
        field.setCurrentIndex(field.findText(TAG_FILENAME))
        condition.setCurrentIndex(condition.findText("CONTAINS"))
        value.setText("G1")
        self._app.processEvents()
        QTest.mouseClick(adv_search.search, Qt.LeftButton)
        self._app.processEvents()

        filtered_expected = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01"
            "-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27-2014-02-"
            "14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
        ]

        scans = self.get_visible_scans()
        self.assertEqual(len(scans), 2)
        self.assert_scans_present(scans, filtered_expected)

        # Reset filter
        QTest.mouseClick(
            self.main_window.data_browser.advanced_search_button, Qt.LeftButton
        )
        self._app.processEvents()

        scans = self.get_visible_scans()
        self.assertEqual(len(scans), 9)
        self.assert_scans_present(scans, initial_expected)

    def test_brick_history(self):
        """Tests the brick history popup."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        bricks_column = (
            self.main_window.data_browser.table_data.get_tag_column(TAG_BRICKS)
        )
        bricks_widget = self.main_window.data_browser.table_data.cellWidget(
            0, bricks_column
        )
        smooth_button = bricks_widget.layout().itemAt(0).widget()
        self.assertEqual(smooth_button.text(), "smooth_1")
        QTest.mouseClick(smooth_button, Qt.LeftButton)

        brick_history = (
            self.main_window.data_browser.table_data.brick_history_popup
        )
        brick_table = brick_history.table

        expected_headers = [
            BRICK_NAME,
            BRICK_INIT,
            BRICK_INIT_TIME,
            BRICK_EXEC,
            BRICK_EXEC_TIME,
            "data_type",
            "fwhm",
            "implicit_masking",
            "in_files",
            "matlab_cmd",
            "mfile",
        ]

        for i, expected in enumerate(expected_headers):
            self.assertEqual(
                brick_table.horizontalHeaderItem(i).text(), expected
            )

        self.assertEqual(self.get_cell_text(brick_table, 0, 0), "smooth_1")
        self.assertEqual(self.get_cell_text(brick_table, 0, 1), "Done")

        # Assert datetime format for BRICK_INIT_TIME and BRICK_EXEC_TIME
        date_regex = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        init_time = self.get_cell_text(brick_table, 0, 2)
        exec_time = self.get_cell_text(brick_table, 0, 4)
        # We only verifying the format of date, not its exact value.
        self.assertRegex(init_time, date_regex)
        self.assertRegex(exec_time, date_regex)

        self.assertEqual(self.get_cell_text(brick_table, 0, 3), "Done")
        self.assertEqual(self.get_cell_text(brick_table, 0, 5), "0")
        self.assertEqual(
            self.get_cell_text(brick_table, 0, 6), "[6.0, 6.0, 6.0]"
        )
        self.assertEqual(self.get_cell_text(brick_table, 0, 7), "False")

        # in_files might have multiple widgets; adjust label_index if needed
        in_files_widget = brick_table.cellWidget(0, 8)
        self.assertIsNotNone(in_files_widget)
        in_files_labels = in_files_widget.findChildren(QLabel)
        self.assertGreaterEqual(len(in_files_labels), 3)
        in_files_button = in_files_widget.findChild(QPushButton)
        self.assertIsNotNone(
            in_files_button, "Could not find QPushButton in in_files cell"
        )
        self.assertIn(
            "data/raw_data/Guerbet-C6-2014",
            in_files_button.text(),
            f"Unexpected button text: {in_files_button.text()}",
        )
        self.assertEqual(
            self.get_cell_text(brick_table, 0, 9),
            "/data/softs/MATLAB/R2024a/bin/matlab",
        )
        self.assertEqual(self.get_cell_text(brick_table, 0, 10), "True")

    def test_clear_cell(self):
        """
        Tests clearing a cell and ensuring value is removed from database.
        """
        project_path = self.get_new_test_project()
        self.main_window.switch_project(project_path, "project_8")

        # Sets shortcuts for often used objects
        data_browser = self.main_window.data_browser
        table = data_browser.table_data

        # Locate the BandWidth column and the first item
        bw_column = table.get_tag_column("BandWidth")
        bw_item = table.item(0, bw_column)

        # Confirm initial value in table
        self.assertEqual(float(bw_item.text()[1:-1]), 50000.0)

        # Confirm initial value in database
        file_path = (
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii"
        )

        with self.main_window.project.database.data() as db:
            self.assertEqual(
                db.get_value(COLLECTION_CURRENT, file_path, "BandWidth"),
                [50000.0],
            )

        # Clear the cell
        bw_item.setSelected(True)
        table.itemChanged.disconnect()
        table.clear_cell()
        table.itemChanged.connect(table.change_cell_color)

        # Confirm the cell text is now marked as not defined
        bw_item = table.item(0, bw_column)
        self.assertEqual(bw_item.text(), NOT_DEFINED_VALUE)

        # Confirm the database no longer has a value for BandWidth
        with self.main_window.project.database.data() as db:
            self.assertIsNone(
                db.get_value(COLLECTION_CURRENT, file_path, "BandWidth")
            )

    def test_clone_tag(self):
        """
        Tests the pop-up for cloning a tag.
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # -- Test 1: No new tag name provided --
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(clone_tag.msg.text(), "The tag name can't be empty")

        # -- Test 2: No tag selected to clone --
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        clone_tag.line_edit_new_tag_name.setText("Test")
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(
            clone_tag.msg.text(), "The tag to clone must be selected"
        )

        # -- Test 3: New tag name already exists --
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        clone_tag.line_edit_new_tag_name.setText(TAG_TYPE)
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(clone_tag.msg.text(), "This tag name already exists")

        # -- Test 4: Successful cloning of "BandWidth" tag to "Test" --
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        clone_tag.line_edit_new_tag_name.setText("Test")
        clone_tag.search_bar.setText("BandWidth")
        clone_tag.list_widget_tags.setCurrentRow(0)  # BandWidth tag selected
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)

        # Helper to assert metadata equivalence
        def assert_metadata_equal(tag1, tag2, collection):
            """
            Asserts that the metadata of two tags are equal in the given
            collection.
            """

            with self.main_window.project.database.data() as db:
                self.assertTrue(tag1 in db.get_field_names(collection))
                meta1 = db.get_field_attributes(collection, tag1)
                meta2 = db.get_field_attributes(collection, tag2)
                self.assertEqual(meta1["description"], meta2["description"])
                self.assertEqual(meta1["unit"], meta2["unit"])
                self.assertEqual(
                    meta1["default_value"], meta2["default_value"]
                )
                self.assertEqual(meta1["field_type"], meta2["field_type"])
                self.assertEqual(meta1["origin"], TAG_ORIGIN_USER)
                self.assertTrue(meta1["visibility"])

        # -- Check metadata in both collections --
        assert_metadata_equal("Test", "BandWidth", COLLECTION_CURRENT)
        assert_metadata_equal("Test", "BandWidth", COLLECTION_INITIAL)

        # -- Check data values in all documents --
        with self.main_window.project.database.data() as db:

            for collection in [COLLECTION_CURRENT, COLLECTION_INITIAL]:

                for doc in db.get_document_names(collection):
                    self.assertEqual(
                        db.get_value(collection, doc, "Test"),
                        db.get_value(collection, doc, "BandWidth"),
                    )

        # -- Check values in the table view --
        table = self.main_window.data_browser.table_data
        test_col = table.get_tag_column("Test")
        bw_col = table.get_tag_column("BandWidth")

        for row in range(table.rowCount()):
            item_test = table.item(row, test_col)
            item_bw = table.item(row, bw_col)
            self.assertEqual(item_test.text(), item_bw.text())

    def test_count_table(self):
        """
        Tests the count table popup.
        """
        # Constants
        BANDWIDTH = "BandWidth"
        ECHOTIME = "EchoTime"

        # Helper to get text from a table header without brackets
        def get_header_text(table, col):
            """
            Returns the header text of a given column without brackets.
            """

            return table.horizontalHeaderItem(col).text().strip("[]")

        # Helper to get text from a table cell without brackets
        def get_cell_text(table, row, col):
            """
            Returns the text of a cell in the count table without brackets.
            """

            return table.item(row, col).text().strip("[]")

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Open count table popup
        QTest.mouseClick(
            self.main_window.data_browser.count_table_button, Qt.LeftButton
        )
        count_table = self.main_window.data_browser.count_table_pop_up

        self.assertEqual(len(count_table.push_buttons), 2)

        # Set tags to count
        count_table.push_buttons[0].setText(BANDWIDTH)
        count_table.fill_values(0)
        count_table.push_buttons[1].setText(ECHOTIME)
        count_table.fill_values(1)

        # Perform count
        QTest.mouseClick(count_table.push_button_count, Qt.LeftButton)

        # Add and remove a tag
        QTest.mouseClick(count_table.add_tag_label, Qt.LeftButton)
        self.assertEqual(len(count_table.push_buttons), 3)
        QTest.mouseClick(count_table.remove_tag_label, Qt.LeftButton)
        self.assertEqual(len(count_table.push_buttons), 2)

        # Check tag names
        self.assertEqual(count_table.push_buttons[0].text(), BANDWIDTH)
        self.assertEqual(count_table.push_buttons[1].text(), ECHOTIME)

        self._app.processEvents()

        # Check headers
        self.assertEqual(get_header_text(count_table.table, 0), BANDWIDTH)
        self.assertEqual(get_header_text(count_table.table, 1), "5.0")
        self.assertEqual(float(get_header_text(count_table.table, 2)), 75.0)
        self.assertEqual(get_header_text(count_table.table, 3), "5.8239923")
        self.assertEqual(
            count_table.table.verticalHeaderItem(3).text(), "Total"
        )

        # Expected values for table cells
        expected_cells = {
            (0, 0): "65789.48",
            (1, 0): "50000.0",
            (2, 0): "25000.0",
            (3, 0): "3",
            (0, 1): "5",
            (1, 1): "",
            (2, 1): "",
            (3, 1): "5",
            (0, 2): "",
            (1, 2): "2",
            (2, 2): "",
            (3, 2): "2",
            (0, 3): "",
            (1, 3): "",
            (2, 3): "2",
            (3, 3): "2",
        }

        for (row, col), expected in expected_cells.items():
            self.assertEqual(
                get_cell_text(count_table.table, row, col), expected
            )

    @patch("PyQt5.QtWidgets.QMessageBox.exec_", return_value=QMessageBox.Ok)
    def test_mia_preferences(self, mock_qmsgbox):
        """Tests the MIA preferences popup with QMessageBox mocked."""

        def reload_config():
            """
            Reloads the configuration from the properties path.
            """

            return Config(properties_path=self.properties_path)

        def open_preferences():
            """
            Opens the preferences dialog and returns the properties widget.
            """
            self.main_window.action_software_preferences.trigger()
            return self.main_window.pop_up_preferences

        config = reload_config()
        self.assertFalse(config.isAutoSave())

        # Enable Auto Save
        properties = open_preferences()
        properties.projects_save_path_line_edit.setText(
            tempfile.mkdtemp(prefix="projects_tests")
        )
        properties.tab_widget.setCurrentIndex(1)
        properties.save_checkbox.setChecked(True)
        QTest.mouseClick(properties.push_button_ok, Qt.LeftButton)
        QTest.qWait(100)
        config = reload_config()
        self.assertTrue(config.isAutoSave())

        # Disable Auto Save again
        properties = open_preferences()
        properties.tab_widget.setCurrentIndex(1)
        properties.save_checkbox.setChecked(False)
        QTest.mouseClick(properties.push_button_ok, Qt.LeftButton)
        QTest.qWait(100)
        config = reload_config()
        self.assertFalse(config.isAutoSave())

        # Cancel — config should remain unchanged
        properties = open_preferences()
        properties.tab_widget.setCurrentIndex(1)
        properties.save_checkbox.setChecked(True)
        QTest.mouseClick(properties.push_button_cancel, Qt.LeftButton)
        QTest.qWait(100)
        config = reload_config()
        config.config = {}
        self.assertFalse(config.isAutoSave())

        # --- Check project preferences ---
        self.assertEqual(config.get_max_projects(), 5)
        config.set_max_projects(7)
        self.assertEqual(config.get_max_projects(), 7)
        config.set_max_projects(5)

        config_path = os.path.join(
            config.get_properties_path(), "properties", "config.yml"
        )
        self.assertTrue(os.path.exists(config_path))

        self.assertTrue(config.get_user_mode())
        config.set_user_mode(False)
        self.assertFalse(config.get_user_mode())

        self.assertEqual(config.get_projects_save_path(), "")

        # --- Check external tools (Matlab/SPM) ---
        self.assertIsNone(config.get_matlab_command())
        self.assertIsNone(config.get_matlab_path())
        self.assertEqual(config.get_matlab_standalone_path(), "")
        self.assertEqual(config.get_spm_path(), "")
        self.assertEqual(config.get_spm_standalone_path(), "")
        self.assertFalse(config.get_use_matlab())
        self.assertFalse(config.get_use_spm())
        self.assertFalse(config.get_use_spm_standalone())

        # --- Check display and behavior settings ---
        self.assertEqual(config.getBackgroundColor(), "")
        self.assertEqual(config.getTextColor(), "")
        self.assertFalse(config.getShowAllSlices())
        self.assertFalse(config.getChainCursors())
        self.assertEqual(config.getNbAllSlicesMax(), 10)
        self.assertEqual(config.getThumbnailTag(), "SequenceName")

        # --- Check MRI conversion path ---
        self.assertEqual(config.get_mri_conv_path(), "")

    def test_mini_viewer(self):
        """
        Tests MiniViewer functionality.

        - Displays scan information in the mini viewer box.
        - Verifies slider behavior and checkbox states.
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser
        viewer = self.main_window.data_browser.viewer

        # Helper: select scan by row index
        def select_scan(index: int):
            """
            Selects a scan in the data browser table by index.

            :param index: The row index of the scan to select.
            """
            item = data_browser.table_data.item(index, 0)
            self.assertIsNotNone(item)
            item.setSelected(True)

        # Helper: set slider to percentage position
        def set_slider_percent(slider, percent: float):
            """
            Sets the slider value to a percentage of its maximum.

            :param slider: The slider to set.
            :param percent: A float between 0.0 and 1.0.
            """
            max_val = slider.maximum()
            slider.setValue(int(max_val * percent))

        # Helper: toggle a checkbox to a state
        def set_checkbox(checkbox, state: bool):
            """
            Sets the checkbox state to checked or unchecked.

            :param checkbox: The checkbox to set.
            :param state: True for checked, False for unchecked.
            """
            checkbox.setCheckState(Qt.Checked if state else Qt.Unchecked)

        # Select first scan and adjust slider
        select_scan(0)
        set_slider_percent(viewer.slider_3D[0], 0.5)

        # Show all slices
        set_checkbox(viewer.check_box_slices, True)

        # Reset to show one slice
        set_checkbox(viewer.check_box_slices, False)

        # Enable chain cursors
        set_checkbox(viewer.check_box_cursors, True)

        # Select second scan
        select_scan(1)

        # Move slider to various positions
        set_slider_percent(viewer.slider_3D[0], 0.0)
        set_slider_percent(viewer.slider_3D[0], 0.5)
        set_slider_percent(viewer.slider_3D[0], 1.0)

        # Disable chain cursors
        set_checkbox(viewer.check_box_cursors, False)

        # Update number of displayed slices
        viewer.update_nb_slices()

    def test_modify_table(self):
        """
        Test ModifyTable behavior with valid and invalid field types.
        """

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser
        table = data_browser.table_data

        # Step 1: Set up a new test project
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Step 2: Select a visible scan
        scan_item = table.item(0, 0)
        self.assertIsNotNone(scan_item)
        scan_name = scan_item.text()
        self.assertFalse(table.isRowHidden(0))

        scans_displayed = [scan_name]
        tag_name = ["FOV"]
        value = [5.0, 3.0]

        # Step 3: Ensure value doesn't change with incorrect field type
        with self.main_window.project.database.data() as db:
            old_value = db.get_value(COLLECTION_CURRENT, scan_name, "FOV")

        mod = ModifyTable(
            self.main_window.project,
            value,
            [FIELD_TYPE_LIST_BOOLEAN],  # Incorrect type
            scans_displayed,
            tag_name,
        )
        mod.update_table_values(True)
        mod.deleteLater()

        with self.main_window.project.database.data() as db:
            unchanged_value = db.get_value(
                COLLECTION_CURRENT, scan_name, "FOV"
            )

        self.assertEqual(old_value, unchanged_value)

        # Step 4: Get correct field type and apply update
        with self.main_window.project.database.data() as db:
            tag_object = db.get_field_attributes(COLLECTION_CURRENT, "FOV")
            correct_type = tag_object["field_type"]

        mod = ModifyTable(
            self.main_window.project,
            value,
            [correct_type],  # Correct type
            scans_displayed,
            tag_name,
        )
        mod.update_table_values(True)

        with self.main_window.project.database.data() as db:
            updated_value = db.get_value(COLLECTION_CURRENT, scan_name, "FOV")

        self.assertEqual(mod.table.columnCount(), 2)
        self.assertEqual(value, updated_value)

        mod.deleteLater()

    def test_multiple_sort(self):
        """
        Test the multiple sort popup functionality and resulting order.
        """

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser
        table = data_browser.table_data

        # Step 1: Set up project
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Step 2: Temporarily disconnect signal to prevent unwanted side
        #         effects
        table.itemChanged.disconnect()

        # Step 3: Open multiple sort popup and configure sorting
        table.multiple_sort_pop_up()
        table.itemChanged.connect(table.change_cell_color)
        multiple_sort = table.pop_up

        # Step 4: Apply multi-sort using two criteria
        multiple_sort.push_buttons[0].setText("BandWidth")
        multiple_sort.fill_values(0)

        multiple_sort.push_buttons[1].setText(TAG_EXP_TYPE)
        multiple_sort.fill_values(1)

        QTest.mouseClick(multiple_sort.push_button_sort, Qt.LeftButton)

        # Step 5: Expected scan order after sorting
        expected_scans = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014"
            "-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014"
            "-02-14102317-04-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
        ]

        # Step 6: Compare actual scan order with expected order
        for row_index, expected_scan in enumerate(expected_scans):
            actual_scan = table.item(row_index, 0).text()
            self.assertEqual(
                actual_scan,
                expected_scan,
                msg=f"Mismatch at row {row_index}: "
                f"expected {expected_scan}, got {actual_scan}",
            )

    def test_multiple_sort_appendix(self):
        """
        Test adding and removing tags in the multiple sort popup.

        - Target class: PopUpMultipleSort
        - Mocks: PopUpSelectTagCountTable.exec_
        """
        # Sets shortcuts for objects that are often used
        table_data = self.main_window.data_browser.table_data

        table_data.multiple_sort_pop_up()
        self.assertTrue(
            hasattr(table_data, "pop_up"), "Popup should be created"
        )

        pop_up = table_data.pop_up

        # Add a third tag
        pop_up.add_tag_label.clicked.emit()
        self.assertEqual(
            len(pop_up.push_buttons), 3, "Should have 3 tag selection buttons"
        )

        # Remove the added tag
        pop_up.remove_tag_label.clicked.emit()
        self.assertEqual(
            len(pop_up.push_buttons),
            2,
            "Should be back to 2 tag selection buttons",
        )

        # Properly scoped mock
        def fake_exec(self):
            """
            Mocked method to simulate the execution of a QDialog.

            Sets the selected_tag attribute to a predefined tag and simulates
            the dialog returning an accepted state (i.e., the user
            clicked "OK").

            :param self (PopUpSelectTagCountTable): The dialog instance being
                                                    mocked.

            :returns (bool): Always returns True to indicate the dialog was
                             accepted.
            """
            self.selected_tag = TAG_EXP_TYPE
            return True

        with patch.object(PopUpSelectTagCountTable, "exec_", fake_exec):
            table_data.pop_up.select_tag(0)

        table_data.pop_up.close()

    def test_openTagsPopUp(self):
        """
        Tests opening the tags selection popup in the MiniViewer.

        - Verifies integration between MiniViewer.openTagsPopUp and
          PopUpSelectTag.
        - Confirms filtering behavior in the tag selection list.
        - Ensures correct handling of tag selection and dialog interaction.

        - Tests: MiniViewer.openTagsPopUp
        - Indirectly tests: PopUpSelectTag
        - Mocks: PopUpSelectTag.exec_ using unittest.mock.patch
        """
        data_browser = self.main_window.data_browser
        viewer = data_browser.viewer

        # Get absolute path to a NIfTI file in the test project
        folder = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "mia_ut_data",
            "resources",
            "mia",
            "project_8",
            "data",
            "raw_data",
        )
        folder = os.path.abspath(folder)

        document_path = os.path.join(
            folder,
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
        )

        # Add the document to the project
        add_path_dialog = PopUpAddPath(data_browser.project, data_browser)
        add_path_dialog.file_line_edit.setText(str([document_path]))
        add_path_dialog.save_path()

        # Select the added document in the table
        data_browser.table_data.item(0, 0).setSelected(True)

        # Mock dialog execution using a context manager
        with patch(
            "populse_mia.user_interface.pop_ups.PopUpSelectTag.exec_",
            return_value=True,
        ):
            # Open the tag selection popup, then cancel it
            viewer.openTagsPopUp()
            viewer.popUp.cancel_clicked()

            # Open it again and run interaction tests
            viewer.openTagsPopUp()
            pop_up = viewer.popUp

            # Search with empty string: all tags should be visible
            pop_up.search_str("")
            self.assertFalse(pop_up.list_widget_tags.item(0).isHidden())
            self.assertFalse(pop_up.list_widget_tags.item(1).isHidden())

            # Filter with specific tag: expect one item to be hidden
            pop_up.search_str(TAG_EXP_TYPE)
            self.assertFalse(pop_up.list_widget_tags.item(0).isHidden())
            self.assertTrue(pop_up.list_widget_tags.item(1).isHidden())

            # Simulate clicking and selecting the first item
            item_0 = pop_up.list_widget_tags.item(0)
            pop_up.list_widget_tags.itemClicked.emit(item_0)
            item_0.setCheckState(Qt.Checked)

            # Confirm selection with OK
            pop_up.ok_clicked()

    def test_open_project(self):
        """
        Tests that the project opens correctly, including expected UI title
        and document presence in the current and initial collections.
        """
        # Open the test project
        project_8_path = self.get_new_test_project(name="project_8")
        self.main_window.switch_project(project_8_path, "project_8")

        # Check project name and window title
        self.assertEqual(self.main_window.project.getName(), "project_8")
        self.assertEqual(
            self.main_window.windowTitle(),
            "MIA - Multiparametric Image Analysis (Admin mode) - project_8",
        )

        # Expected document list in both current and initial collections
        expected_docs = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "04-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "05-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "06-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "08-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "09-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "10-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "11-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27-2014-02-"
            "14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
        ]

        # Check that documents are loaded in both collections
        with self.main_window.project.database.data() as db_data:

            for collection in [COLLECTION_CURRENT, COLLECTION_INITIAL]:
                documents = db_data.get_document_names(collection)
                self.assertEqual(len(documents), 9)

                for expected in expected_docs:
                    self.assertIn(
                        expected,
                        documents,
                        f"{expected} not found in {collection}",
                    )

    def test_project_filter(self):
        """
        Tests saving and applying a project filter.

        - Verifies:
            - DataBrowser.open_popup behavior
            - Project.save_current_filter functionality

        - Uses scoped mocks:
            - QMessageBox.exec (to bypass dialogs)
            - QInputDialog.getText (to simulate user input)
        """

        test_project_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_project_path, "test_project")

        with (
            patch("PyQt5.QtWidgets.QMessageBox.exec", return_value=None),
            patch(
                "PyQt5.QtWidgets.QInputDialog.getText",
                return_value=("filter_1", True),
            ),
        ):

            # Save the current filter with the name 'filter_1'
            self.main_window.data_browser.save_filter_action.trigger()

            # Try to save it again (will reuse the same mocked name)
            self.main_window.data_browser.save_filter_action.trigger()

        # Open the saved filters popup
        self.main_window.data_browser.open_filter_action.trigger()
        popup = self.main_window.data_browser.popUp

        # Cancel and reopen the popup
        popup.cancel_clicked()
        self.main_window.data_browser.open_filter_action.trigger()
        popup = self.main_window.data_browser.popUp

        def filter_visible_at(index: int) -> bool:
            """
            Checks if the filter item at the given index in the filter list
            is visible.

            :param index (int): The index of the filter item in the list
                                widget.

            :returns (bool): True if the filter item is visible, False if
                             it is hidden.
            """
            return not popup.list_widget_filters.item(index).isHidden()

        # Search with empty string (should show the filter)
        popup.search_str("")
        self.assertTrue(filter_visible_at(0))

        # Search for non-existent filter
        popup.search_str("filter_2")
        self.assertFalse(filter_visible_at(0))

        # Search for existing filter
        popup.search_str("filter_1")
        self.assertTrue(filter_visible_at(0))

        # Select and apply the filter
        popup.list_widget_filters.item(0).setSelected(True)
        popup.push_button_ok.clicked.emit()

        # Get displayed scans
        displayed_scans = [
            self.main_window.data_browser.table_data.item(row, 0).text()
            for row in range(
                self.main_window.data_browser.table_data.rowCount()
            )
            if not self.main_window.data_browser.table_data.isRowHidden(row)
        ]

        self.assertEqual(len(displayed_scans), 3)

    def test_project_properties(self):
        """
        Tests saved projects addition and removal.

        - Ensures that saved project paths are tracked properly.
        - Mocks SavedProjects.loadSavedProjects only within scope.
        """

        saved_projects = self.main_window.saved_projects
        self.assertEqual(saved_projects.pathsList, [])

        config = Config(properties_path=self.properties_path)
        project_8_path = self.get_new_test_project()

        os.remove(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "saved_projects.yml",
            )
        )

        saved_projects = SavedProjects()
        self.assertEqual(saved_projects.pathsList, [])

        saved_projects.addSavedProject(project_8_path)
        self.assertEqual(saved_projects.pathsList, [project_8_path])

        saved_projects.addSavedProject("/home")
        self.assertEqual(saved_projects.pathsList, ["/home", project_8_path])

        saved_projects.addSavedProject(project_8_path)
        self.assertEqual(saved_projects.pathsList, [project_8_path, "/home"])

        saved_projects.removeSavedProject(project_8_path)
        saved_projects.removeSavedProject("/home")
        self.assertEqual(saved_projects.pathsList, [])

        with patch(
            "populse_mia.data_manager.project_properties.SavedProjects."
            "loadSavedProjects",
            return_value=True,
        ):
            saved_projects = SavedProjects()

            self.assertEqual(saved_projects.pathsList, [])

    def test_proj_remov_from_cur_proj(self):
        """
        Tests that the current project is correctly removed from the list of
        opened projects after closing or switching.

        - Verifies that the current project path is listed in the opened
          projects.
        """

        config = Config(properties_path=self.properties_path)
        opened_projects = config.get_opened_projects()

        # There should be exactly one opened project (the one just loaded)
        self.assertEqual(len(opened_projects), 1)

        # The current project's folder should be in the list
        current_project_path = self.main_window.project.folder
        self.assertIn(current_project_path, opened_projects)

    def test_rapid_search(self):
        """
        Tests the rapid search bar behavior in the DataBrowser.

        Steps:
        - Load a project with 9 scans.
        - Verify all scans are initially visible.
        - Filter scans using the search bar (e.g., "G1").
        - Verify the filtered results.
        - Clear the filter using the cross button.
        - Verify all scans are shown again.
        - Test filtering using NOT_DEFINED_VALUE.
        """

        def get_visible_scan_names():
            """
            Retrieves the list of scan names currently visible in the data
            browser table.

            This function iterates over all rows in the data browser's scan
            table and collects the scan names from the first column (index 0)
            of rows that are not hidden.

            :returns (List[str]): A list of scan names (as strings) for all
                                  visible rows in the table.
            """

            return [
                self.main_window.data_browser.table_data.item(row, 0).text()
                for row in range(
                    self.main_window.data_browser.table_data.rowCount()
                )
                if not self.main_window.data_browser.table_data.isRowHidden(
                    row
                )
            ]

        # Setup
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Initial state: all 9 scans should be visible
        self.assertEqual(
            self.main_window.data_browser.table_data.rowCount(), 9
        )

        expected_initial_scans = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "04-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "05-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "06-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "08-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "09-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "10-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "11-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27-2014-02-"
            "14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
        ]

        scans_displayed = get_visible_scan_names()
        self.assertEqual(len(scans_displayed), 9)

        for scan in expected_initial_scans:
            self.assertIn(scan, scans_displayed)

        # Apply rapid search for "G1"
        self.main_window.data_browser.search_bar.setText("G1")
        scans_displayed = get_visible_scan_names()

        expected_g1_scans = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27-2014-02-"
            "14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
        ]

        self.assertEqual(len(scans_displayed), 2)

        for scan in expected_g1_scans:
            self.assertIn(scan, scans_displayed)

        # Clear search using cross button
        QTest.mouseClick(
            self.main_window.data_browser.button_cross, Qt.LeftButton
        )
        scans_displayed = get_visible_scan_names()

        self.assertEqual(len(scans_displayed), 9)

        for scan in expected_initial_scans:
            self.assertIn(scan, scans_displayed)

        # Test filtering using NOT_DEFINED_VALUE
        QTest.mouseClick(
            self.main_window.data_browser.button_cross, Qt.LeftButton
        )
        self.main_window.data_browser.search_bar.setText(NOT_DEFINED_VALUE)
        scans_displayed = get_visible_scan_names()

        self.assertEqual(
            scans_displayed,
            [
                "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-"
                "14102317-11-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii"
            ],
        )

    def test_remove_scan(self):
        """
        Tests the removal of scans from the database via the
        PipelineManagerTab.

        - Covered:
            - PipelineManagerTab.remove_scan
            - PopUpRemoveScan

        - Mocks:
            - PopUpRemoveScan.exec
        """

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        data_browser = self.main_window.data_browser
        tb_data = data_browser.table_data

        # Create a new project and setup file paths
        project_path = self.get_new_test_project()
        ppl_manager.project.folder = project_path
        raw_data_path = os.path.join(project_path, "data", "raw_data")

        nii_file_1 = os.path.abspath(
            os.path.join(
                raw_data_path,
                "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
                "Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            )
        )
        nii_file_2 = os.path.abspath(
            os.path.join(
                raw_data_path,
                "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-05-G4_"
                "Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            )
        )

        # Adds 2 scans to the current database
        with self.main_window.project.database.data(write=True) as db:
            db.add_document(COLLECTION_CURRENT, nii_file_1)
            db.add_document(COLLECTION_INITIAL, nii_file_1)
            db.add_document(COLLECTION_CURRENT, nii_file_2)
            db.add_document(COLLECTION_INITIAL, nii_file_2)

        ppl_manager.scan_list.extend([nii_file_1, nii_file_2])
        data_browser.data_sent = True

        # Refreshes the data browser tab
        self.main_window.update_project(project_path)

        # Selects all scans
        tb_data.selectColumn(0)

        # --- Act & Assert: Cancel Removal ---
        with patch.object(
            PopUpRemoveScan, "exec", lambda x: tb_data.pop.cancel_clicked()
        ):
            tb_data.remove_scan()

        with patch.object(
            PopUpRemoveScan, "exec", lambda x: tb_data.pop.no_all_clicked()
        ):
            tb_data.remove_scan()

        # Asserts that the data browser kept both scans
        self.assertEqual(
            len(tb_data.scans),
            2,
            "Scans should not be removed when cancelled.",
        )

        # --- Act & Assert: Confirm Removal of Both ---
        with patch.object(
            PopUpRemoveScan, "exec", lambda x: tb_data.pop.yes_all_clicked()
        ):
            tb_data.remove_scan()

        # Asserts that the scans were deleted
        self.assertEqual(
            len(tb_data.scans),
            0,
            "Scans should be removed after confirmation.",
        )

        # --- Arrange Again: Add one scan ---
        with self.main_window.project.database.data(write=True) as db:
            # Adds one scan to the current database
            db.add_document(COLLECTION_CURRENT, nii_file_1)
            db.add_document(COLLECTION_INITIAL, nii_file_1)

        self.main_window.update_project(project_path)
        ppl_manager.scan_list.append(nii_file_1)

        # Selects the scan
        tb_data.selectColumn(0)

        # --- Act & Assert: Confirm Single Removal ---
        with patch.object(
            PopUpRemoveScan, "exec", lambda x: tb_data.pop.yes_clicked()
        ):
            tb_data.remove_scan()

        self.assertEqual(
            len(tb_data.scans),
            0,
            "Single scan should be removed after confirmation.",
        )

    def test_remove_tag(self):
        """
        Tests the tag removal popup in the data browser.

        - Verifies:
            - Tag is added correctly.
            - Tag list remains unchanged when removal popup is confirmed
              without selection.
            - Tag is removed when explicitly selected and confirmed.
        """

        data_browser = self.main_window.data_browser

        # --- Arrange: Add a tag "Test" ---
        data_browser.add_tag_action.trigger()
        add_tag_popup = data_browser.pop_up_add_tag
        add_tag_popup.text_edit_tag_name.setText("Test")
        QTest.mouseClick(add_tag_popup.push_button_ok, Qt.LeftButton)

        with self.main_window.project.database.data() as db:
            tags_current_before = db.get_field_names(COLLECTION_CURRENT)
            tags_initial_before = db.get_field_names(COLLECTION_INITIAL)

        self.assertIn(
            "Test",
            tags_current_before,
            "'Test' tag not found in current collection.",
        )
        self.assertIn(
            "Test",
            tags_initial_before,
            "'Test' tag not found in initial collection.",
        )

        # --- Act: Trigger remove tag popup, click OK without selection ---
        data_browser.remove_tag_action.trigger()
        remove_tag_popup = data_browser.pop_up_remove_tag
        QTest.mouseClick(remove_tag_popup.push_button_ok, Qt.LeftButton)

        with self.main_window.project.database.data() as db:
            tags_current_after_cancel = db.get_field_names(COLLECTION_CURRENT)
            tags_initial_after_cancel = db.get_field_names(COLLECTION_INITIAL)

        # --- Assert: No tag should be removed ---
        self.assertEqual(
            tags_current_before,
            tags_current_after_cancel,
            "Tags in current collection changed unexpectedly.",
        )
        self.assertEqual(
            tags_initial_before,
            tags_initial_after_cancel,
            "Tags in initial collection changed unexpectedly.",
        )

        # --- Act: Trigger remove tag popup again,
        #          select and confirm removal ---
        data_browser.remove_tag_action.trigger()
        remove_tag_popup = data_browser.pop_up_remove_tag
        remove_tag_popup.list_widget_tags.setCurrentRow(0)  # Select "Test"
        QTest.mouseClick(remove_tag_popup.push_button_ok, Qt.LeftButton)

        with self.main_window.project.database.data() as db:
            tags_current_final = db.get_field_names(COLLECTION_CURRENT)
            tags_initial_final = db.get_field_names(COLLECTION_INITIAL)

        # --- Assert: "Test" tag should be removed from both collections ---
        self.assertNotIn(
            "Test",
            tags_current_final,
            "'Test' tag was not removed from current collection.",
        )
        self.assertNotIn(
            "Test",
            tags_initial_final,
            "'Test' tag was not removed from initial collection.",
        )

    def test_reset_cell(self):
        """Tests the method resetting the selected cells."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")
        table = self.main_window.data_browser.table_data

        # Helper to get fresh item
        def get_item(tag):
            """
            Retrieve the table widget item for the specified tag in the first
            row.

            :param tag (str): The tag (column identifier) whose cell item is
                              to be fetched.

            :returns (QTableWidgetItem): The item at row 0 of the column
                                         corresponding to `tag`.
            """
            col = table.get_tag_column(tag)

            return table.item(0, col)

        # Sanity-check initial BandWidth
        val, val_init, val_ui, item = self.get_db_and_databrowser_value(
            self.main_window, 0, "BandWidth"
        )
        self.assertEqual(
            float(val[0]), 50000.0, f"Expected DB value 50000.0, got {val}"
        )
        self.assertEqual(
            float(val[0]),
            float(val_ui.strip("[]")),
            "Mismatch in UI and DB value",
        )
        self.assertEqual(
            float(val[0]),
            float(val_init[0]),
            "Mismatch between current and initial DB values",
        )

        # 1) Define exec_ that “does the OK click”:
        def exec_as_update(self, *args, **kwargs):
            """
            Patched exec_ method that injects a test value into the dialog
            table and runs the real update logic without showing the dialog.

            :param self (ModifyTable): The dialog instance being tested.
            :param args: Positional arguments forwarded to exec_, unused here.
            :param kwargs: Keyword arguments forwarded to exec_, unused here.

            :returns (bool): Always returns True to simulate the user
                             clicking "Ok".
            """
            # inject the new text into the dialog’s table
            self.table.setItem(0, 0, QTableWidgetItem("25000"))
            # call the real update logic (with test=True so no QMessageBox)
            ModifyTable.update_table_values(self, test=True)

            return True

        # 2) Patch only exec_ on the ModifyTable class that DataBrowser uses:
        patch_target = (
            "populse_mia.user_interface.data_browser.data_browser."
            "ModifyTable.exec_"
        )

        with patch(patch_target, new=exec_as_update):
            # select, run the edit routine, and deselect
            item.setSelected(True)
            table.edit_table_data_values()
            item = get_item("BandWidth")
            item.setSelected(False)

        # Re-check values
        val, val_init, val_ui, _ = self.get_db_and_databrowser_value(
            self.main_window, 0, "BandWidth"
        )
        self.assertEqual(
            float(val[0]),
            25000.0,
            f"Expected updated value 25000.0, got {val}",
        )
        self.assertEqual(
            float(val[0]),
            float(val_ui.strip("[]")),
            "UI and DB mismatch after edit",
        )
        self.assertEqual(
            float(val_init[0]),
            50000.0,
            "Initial value should remain unchanged",
        )

        # Reset cell
        item.setSelected(True)

        with self.suppress_item_changed_signal(table):
            table.reset_cell()

        item.setSelected(False)

        # Validate reset
        val, val_init, val_ui, _ = self.get_db_and_databrowser_value(
            self.main_window, 0, "BandWidth"
        )
        self.assertEqual(
            float(val[0]), 50000.0, "Reset value does not match initial"
        )
        self.assertEqual(
            float(val[0]),
            float(val_ui.strip("[]")),
            "UI and DB mismatch after reset",
        )
        self.assertEqual(
            float(val[0]),
            float(val_init[0]),
            "Reset failed to restore initial DB value",
        )

        # Test for a string: TAG_TYPE
        val, val_init, val_ui, item = self.get_db_and_databrowser_value(
            self.main_window, 0, TAG_TYPE
        )
        self.assertEqual(val, TYPE_NII, "Initial DB value mismatch")
        self.assertEqual(val, val_ui, "Initial UI value mismatch")
        self.assertEqual(
            val, val_init, "Current and initial DB value mismatch"
        )

        # Change the value
        item.setSelected(True)
        item.setText("Test")
        item.setSelected(False)

        val, val_init, val_ui, item = self.get_db_and_databrowser_value(
            self.main_window, 0, TAG_TYPE
        )
        self.assertEqual(val, "Test", "Expected updated string value 'Test'")
        self.assertEqual(val, val_ui, "UI and DB mismatch after text change")
        self.assertEqual(
            val_init, TYPE_NII, "Initial string value should remain unchanged"
        )

        # Reset cell
        item.setSelected(True)

        with self.suppress_item_changed_signal(table):
            table.reset_cell()

        item.setSelected(False)

        # Validate reset
        val, val_init, val_ui, _ = self.get_db_and_databrowser_value(
            self.main_window, 0, TAG_TYPE
        )
        self.assertEqual(
            val, TYPE_NII, "Reset string value does not match initial"
        )
        self.assertEqual(val, val_ui, "UI and DB string mismatch after reset")
        self.assertEqual(
            val, val_init, "Reset failed to restore initial string value"
        )

    def test_reset_column(self):
        """
        Test that edit_table_data_values() properly updates column values,
        and reset_column() reverts them to their initial state.
        """
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        table = self.main_window.data_browser.table_data
        bandwidth_col = table.get_tag_column("BandWidth")

        # Initial checks before modification
        curr2, init2, gui2, _ = self.get_db_and_databrowser_value(
            self.main_window, 1, "BandWidth"
        )
        self.assertEqual(
            (float(curr2[0]), float(gui2.strip("[]")), float(init2[0])),
            (50000, 50000, 50000),
        )

        curr3, init3, gui3, _ = self.get_db_and_databrowser_value(
            self.main_window, 2, "BandWidth"
        )
        self.assertEqual(
            (float(curr3[0]), float(gui3.strip("[]")), float(init3[0])),
            (25000, 25000, 25000),
        )

        # 1) Define patched exec_ to simulate user editing both selected rows
        def exec_as_update(self, *args, **kwargs):
            """
            Simulated exec_() for ModifyTable: injects value and calls update
            logic.
            """
            self.table.setItem(0, 0, QTableWidgetItem("70000"))
            self.update_table_values(test=True)

            return True  # Simulate "OK" button

        # 2) Patch exec_ only on ModifyTable
        patch_target = (
            "populse_mia.user_interface.data_browser.data_browser."
            "ModifyTable.exec_"
        )

        with patch(patch_target, new=exec_as_update):
            # Select both rows
            table.item(1, bandwidth_col).setSelected(True)
            table.item(2, bandwidth_col).setSelected(True)
            table.edit_table_data_values()

        # Check new values
        curr2, init2, gui2, _ = self.get_db_and_databrowser_value(
            self.main_window, 1, "BandWidth"
        )
        self.assertEqual(
            (float(curr2[0]), float(gui2.strip("[]")), float(init2[0])),
            (70000, 70000, 50000),
        )

        curr3, init3, gui3, _ = self.get_db_and_databrowser_value(
            self.main_window, 2, "BandWidth"
        )
        self.assertEqual(
            (float(curr3[0]), float(gui3.strip("[]")), float(init3[0])),
            (70000, 70000, 25000),
        )

        # 3) Reset the column
        with self.suppress_item_changed_signal(table):
            table.reset_column()

        table.item(1, bandwidth_col).setSelected(False)
        table.item(2, bandwidth_col).setSelected(False)

        # Verify values are restored
        curr2, init2, gui2, _ = self.get_db_and_databrowser_value(
            self.main_window, 1, "BandWidth"
        )
        self.assertEqual(
            (float(curr2[0]), float(gui2.strip("[]")), float(init2[0])),
            (50000, 50000, 50000),
        )

        curr3, init3, gui3, _ = self.get_db_and_databrowser_value(
            self.main_window, 2, "BandWidth"
        )
        self.assertEqual(
            (float(curr3[0]), float(gui3.strip("[]")), float(init3[0])),
            (25000, 25000, 25000),
        )

    def test_reset_row(self):
        """Tests row reset."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")
        table = self.main_window.data_browser.table_data

        # Value in DataBrowser and DataBase for the second document
        curr, init, gui, type_item = self.get_db_and_databrowser_value(
            self.main_window, 1, TAG_TYPE
        )
        # Check value for the second document
        self.assertEqual((curr, init, gui), (TYPE_NII, TYPE_NII, TYPE_NII))

        # Change the value
        type_item.setSelected(True)
        type_item.setText("Test")

        # Check if value in DataBrowser and DataBase as been changed
        curr, init, gui, _ = self.get_db_and_databrowser_value(
            self.main_window, 1, TAG_TYPE
        )
        self.assertEqual((curr, init, gui), ("Test", TYPE_NII, "Test"))

        # Reset row for second document
        table.clearSelection()
        scan_item = table.item(1, 0)
        scan_item.setSelected(True)

        with self.suppress_item_changed_signal(table):
            table.reset_row()

        # Check if value in DataBrowser as been reset
        curr, init, gui, type_item = self.get_db_and_databrowser_value(
            self.main_window, 1, TAG_TYPE
        )
        self.assertEqual((curr, init, gui), (TYPE_NII, TYPE_NII, TYPE_NII))

    def test_save_project(self):
        """
        Test creating, saving, switching, and reopening a project,
        while mocking dialogs and preventing UI blocking.
        """
        config = Config(properties_path=self.properties_path)
        projects_dir = os.path.realpath(
            tempfile.mkdtemp(prefix="projects_tests")
        )
        something_path = os.path.join(projects_dir, "something")

        # -- Patch QMessageBox.exec to prevent modal dialog
        with patch.object(QMessageBox, "exec", lambda self_: self_.show()):
            # -- No save path configured initially
            config.set_projects_save_path(None)
            self.main_window.create_project_pop_up()
            self.main_window.msg.accept()

            # -- Attempt save without path
            self.main_window.saveChoice()
            self.main_window.msg.accept()

            # -- Configure a proper project save path
            config.set_projects_save_path(projects_dir)
            project_8_path = self.get_new_test_project(name="project_8")

            # -- Save new project 'something'
            self.main_window.saveChoice()
            self.assertEqual(self.main_window.project.getName(), "something")
            self.assertTrue(os.path.exists(something_path))

            # -- Switch to project_8 and save it
            self.main_window.switch_project(project_8_path, "project_8")
            self.assertEqual(self.main_window.project.getName(), "project_8")
            self.main_window.saveChoice()

            # -- Remove 'something' to simulate a fresh open
            shutil.rmtree(something_path)

            # --- Mock project pop-ups ---

            # Common mock configuration
            def mock_popup(relative_path):
                """
                Create a MagicMock instance simulating a PopUpNewProject
                dialog.

                :param relative_path (str): The relative path to set as the
                                            selected file and filename in the
                                            popup.

                :returns (MagicMock): A mocked PopUpNewProject instance with
                                      predefined behaviors:
                    - `relative_path` attribute set to the given path.
                    - `selectedFiles()` returns a list containing the relative
                      path.
                    - `get_filename()` returns the relative path.
                    - `exec_()` returns True, simulating a successful dialog
                      execution.
                """
                popup = MagicMock(spec=PopUpNewProject)
                popup.relative_path = relative_path
                popup.selectedFiles.return_value = [relative_path]
                popup.get_filename.return_value = relative_path
                popup.exec_.return_value = True
                return popup

            new_project_popup = mock_popup(something_path)
            open_project_popup = mock_popup(something_path)
            open_project_popup.path, open_project_popup.name = os.path.split(
                something_path
            )

            with (
                patch(
                    "populse_mia.user_interface.main_window.PopUpNewProject",
                    return_value=new_project_popup,
                ),
                patch(
                    "populse_mia.user_interface.main_window.PopUpOpenProject",
                    return_value=open_project_popup,
                ),
            ):
                # -- Recreate 'something' project
                self.main_window.create_project_pop_up()
                self.assertEqual(
                    self.main_window.project.getName(), "something"
                )
                self.assertTrue(os.path.exists(something_path))

                # -- Switch to another project and open the 'something'
                #    project
                self.main_window.switch_project(project_8_path, "project_8")
                self.main_window.open_project_pop_up()
                self.assertEqual(
                    self.main_window.project.getName(), "something"
                )

                # -- Switch back and clean up
                self.main_window.switch_project(project_8_path, "project_8")
                shutil.rmtree(something_path)

    def test_send_doc_to_pipeline_manager(self):
        """
        Test that documents (scans) can be sent from the data browser to the
        pipeline manager.

        This includes:
            - Sending all scans (cancel and confirm cases)
            - Sending a manual selection of scans
            - Sending filtered scans using the search bar

        All popup interactions are mocked to avoid GUI side effects.
        """

        def simulate_send_popup(confirm: bool = True):
            """
            Simulate user interaction with the send_documents_to_pipeline
            popup dialog.

            This function waits briefly for the popup to be fully initialized,
            then either confirms the selection by triggering the OK action or
            cancels by closing the popup, depending on the `confirm` parameter.

            :param confirm (bool): If True, simulate clicking the OK button to
                                   confirm the selection. If False, simulate
                                   closing/cancelling the popup. Defaults to
                                   True.
            """
            popup = self.main_window.data_browser.show_selection
            QTest.qWait(100)

            if confirm:
                popup.ok_clicked()

            else:
                popup.close()

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Start with empty pipeline manager
        self.assertEqual(self.main_window.pipeline_manager.scan_list, [])

        # --- Case 1: Cancel popup, expect no scans sent ---
        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )

        simulate_send_popup(confirm=False)
        self.assertEqual(self.main_window.pipeline_manager.scan_list, [])

        # --- Case 2: Confirm popup with full selection ---
        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )
        simulate_send_popup()

        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 9)

        expected_scans = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "04-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "05-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "06-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "08-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "09-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "10-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "11-G4_Guerbet_T1SE_800-RAREpvm-000142_400.nii",
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27-2014-02-"
            "14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
        ]

        for expected in expected_scans:
            self.assertIn(expected, scans)

        # --- Case 3: Select first two scans manually ---
        table = self.main_window.data_browser.table_data
        item1 = table.item(0, 0)
        item2 = table.item(1, 0)
        item1.setSelected(True)
        item2.setSelected(True)
        scan1 = item1.text()
        scan2 = item2.text()

        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )
        simulate_send_popup()

        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 2)
        self.assertIn(scan1, scans)
        self.assertIn(scan2, scans)

        # --- Case 4: Use search bar to filter 'G3' scans ---
        self.main_window.data_browser.table_data.clearSelection()
        self.main_window.data_browser.search_bar.setText("G3")

        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )
        simulate_send_popup()

        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 2)

        expected_g3_scans = [
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "04-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "10-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii",
        ]
        for expected in expected_g3_scans:
            self.assertIn(expected, scans)

    def test_set_value(self):
        """
        Test modification of cell values in the data browser table.

        This test verifies that both list values (BandWidth) and string values
        (Type) can be properly modified through the UI and that changes
        persist correctly in both the database and table display.

        This test is redundant with the first part of test_reset_cell.
        """
        # Setup test environment
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Get scan name from the second document
        scan_item = self.main_window.data_browser.table_data.item(1, 0)
        scan_name = scan_item.text()

        # Test constants
        ORIGINAL_BANDWIDTH = 50000.0
        NEW_BANDWIDTH = 25000.0
        NEW_TYPE_VALUE = "Test"

        from collections import namedtuple

        # Helper to get database values
        DatabaseValues = namedtuple("DatabaseValues", ["current", "initial"])

        def get_db_values(tag_name, convert_to_float=False):
            """Get current and initial values from database for a tag."""

            with self.main_window.project.database.data() as database_data:
                current = database_data.get_value(
                    COLLECTION_CURRENT, scan_name, tag_name
                )
                initial = database_data.get_value(
                    COLLECTION_INITIAL, scan_name, tag_name
                )

                if convert_to_float:
                    current = float(current[0])
                    initial = float(initial[0])

                return DatabaseValues(current=current, initial=initial)

        # Test BandWidth (list value) modification
        # Values in database
        bandwidth_db = get_db_values("BandWidth", convert_to_float=True)

        # Value in DataBrowser
        bandwidth_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("BandWidth")
        bandwidth_item = self.main_window.data_browser.table_data.item(
            1, bandwidth_column
        )
        bandwidth_table = float(bandwidth_item.text().strip("[]"))

        # Verify initial state
        self.assertEqual(bandwidth_db.current, float(50000))
        self.assertEqual(bandwidth_db.current, bandwidth_table)
        self.assertEqual(bandwidth_db.current, bandwidth_db.initial)

        # Modify bandwidth value through UI
        bandwidth_item.setSelected(True)

        def exec_and_update(self):
            """Mock dialog execution to update table values."""
            self.update_table_values()
            return True

        with patch.object(ModifyTable, "exec_", new=exec_and_update):
            bandwidth_item.setText(f"[{NEW_BANDWIDTH:.1f}]")
            self.main_window.data_browser.table_data.edit_table_data_values()

        bandwidth_item = self.main_window.data_browser.table_data.item(
            1, bandwidth_column
        )
        bandwidth_item.setSelected(False)

        # Verify bandwidth changes persisted correctly
        updated_bandwidth_db = get_db_values(
            "BandWidth", convert_to_float=True
        )
        updated_bandwidth_table = float(bandwidth_item.text().strip("[]"))

        self.assertEqual(updated_bandwidth_db.current, NEW_BANDWIDTH)
        self.assertEqual(updated_bandwidth_db.current, updated_bandwidth_table)
        self.assertEqual(updated_bandwidth_db.initial, ORIGINAL_BANDWIDTH)

        # Test Type (string value) modification
        # Get initial type values from database and table
        type_db = get_db_values(TAG_TYPE)

        type_column = self.main_window.data_browser.table_data.get_tag_column(
            TAG_TYPE
        )
        type_item = self.main_window.data_browser.table_data.item(
            1, type_column
        )
        type_table = type_item.text()

        # Verify initial state
        self.assertEqual(type_db.current, TYPE_NII)
        self.assertEqual(type_db.current, type_table)
        self.assertEqual(type_db.current, type_db.initial)

        # Modify type value through UI
        type_item.setSelected(True)
        type_item.setText(NEW_TYPE_VALUE)
        type_item.setSelected(False)

        # Verify type changes persisted correctly
        updated_type_db = get_db_values(TAG_TYPE)
        updated_type_table = type_item.text()

        self.assertEqual(updated_type_db.current, NEW_TYPE_VALUE)
        self.assertEqual(updated_type_db.current, updated_type_table)
        self.assertEqual(updated_type_db.initial, TYPE_NII)

    def test_show_brick_history(self):
        """
        Tests that the brick history pop-up opens correctly and allows
        navigation between scans through its interface.

        Covers:
            - TableDataBrowser.show_brick_history()
            - PopUpShowHistory

        Verifies:
            - Brick history pop-up is created on click.
            - Input scan button in the pop-up correctly selects the scan.
        """

        # Create and switch to a new test project
        project_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(project_path, "light_test_project")

        data_browser = self.main_window.data_browser
        table_data = data_browser.table_data

        # Retrieve expected input scan filename from the database
        with self.main_window.project.database.data() as db:
            input_scan_name = db.get_document(COLLECTION_CURRENT)[0][
                TAG_FILENAME
            ]

        # Locate and click the brick history button for the first scan
        brick_col_index = table_data.get_tag_column(TAG_BRICKS)
        hist_button = table_data.cellWidget(0, brick_col_index).findChild(
            QPushButton
        )
        hist_button.clicked.emit()

        # Assert that the history pop-up was created
        self.assertTrue(
            hasattr(table_data, "brick_history_popup"),
            msg="History pop-up was not created",
        )

        popup = table_data.brick_history_popup

        # Click on the 'input file' button in the history popup to reselect
        # scan
        input_button = popup.table.cellWidget(0, 8).findChild(QPushButton)
        input_button.clicked.emit()

        # Assert the correct scan is selected after clicking the input file
        # button
        selected_items = table_data.selectedItems()
        self.assertTrue(
            selected_items, msg="No item selected after input button click"
        )
        self.assertEqual(
            selected_items[0].text(),
            input_scan_name,
            msg="Incorrect scan selected from history pop-up",
        )

        # Re-open the history pop-up for the second scan (double-smoothed)
        hist_button = table_data.cellWidget(1, brick_col_index).findChild(
            QPushButton
        )
        hist_button.clicked.emit()

        # Optional cleanup (good practice, though not strictly required here)
        hist_button.close()

    def test_sort(self):
        """
        Test sorting functionality in the DataBrowser table.

        This test verifies that the DataBrowser table can be properly sorted
        by the BandWidth column in both ascending and descending order.
        """
        # Setup test environment
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        table = self.main_window.data_browser.table_data

        # Constants for Qt sort orders
        QT_ASCENDING = 0  # Qt.AscendingOrder
        QT_DESCENDING = 1  # Qt.DescendingOrder

        def get_visible_bandwidth_values():
            """Extract BandWidth values from all visible table rows.

            Return (list): BandWidth values from visible rows in current table
                           order.
            """
            bandwidth_column = table.get_tag_column("BandWidth")
            bandwidth_values = []

            for row in range(table.rowCount()):
                if not table.isRowHidden(row):
                    item = table.item(row, bandwidth_column)
                    bandwidth_values.append(item.text())

            return bandwidth_values

        def set_sort_order(sort_order):
            """Set the table sort order for the BandWidth column.

            Args:
                sort_order: Qt sort order (0 for ascending, 1 for descending)
            """
            bandwidth_column = table.get_tag_column("BandWidth")
            header = table.horizontalHeader()
            header.setSortIndicator(bandwidth_column, sort_order)

        # Get initial (unsorted) bandwidth values
        initial_bandwidths = get_visible_bandwidth_values()

        # Test ascending sort
        set_sort_order(QT_ASCENDING)
        ascending_bandwidths = get_visible_bandwidth_values()

        # Verify ascending sort worked correctly
        self.assertNotEqual(
            initial_bandwidths,
            ascending_bandwidths,
            "Ascending sort should change the order from initial state",
        )
        self.assertEqual(
            sorted(initial_bandwidths),
            ascending_bandwidths,
            "Ascending sort should match Python's sorted() result",
        )

        # Test descending sort
        set_sort_order(QT_DESCENDING)
        descending_bandwidths = get_visible_bandwidth_values()

        # Verify descending sort worked correctly
        self.assertNotEqual(
            initial_bandwidths,
            descending_bandwidths,
            "Descending sort should change the order from initial state",
        )
        self.assertEqual(
            sorted(initial_bandwidths, reverse=True),
            descending_bandwidths,
            "Descending sort should match Python's reverse sorted() result",
        )

    def test_table_data_add_columns(self):
        """
        Adds tag columns to the table data window.

        - Tests TableDataBrowser.add_columns.
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for often used objects
        table_data = self.main_window.data_browser.table_data

        # Adds a tag, of the types float, datetime, date and time, to
        # the database
        tags = [
            "mock_tag_float",
            "mock_tag_datetime",
            "mock_tag_date",
            "mock_tag_time",
        ]
        types = [
            FIELD_TYPE_FLOAT,
            FIELD_TYPE_DATETIME,
            FIELD_TYPE_DATE,
            FIELD_TYPE_TIME,
        ]

        with table_data.project.database.schema() as database_schema:

            for tag, tag_type in zip(tags, types):
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_CURRENT,
                        "field_name": tag,
                        "field_type": tag_type,
                        "description": "",
                        "visibility": True,
                        "origin": "",
                        "unit": "",
                        "default_value": "",
                    }
                )

        table_data.add_columns()  # Adds the tags to table view

        # Asserts that the tags were added to the table view
        for tag in tags:
            tag_column_ind = table_data.get_tag_column(tag)
            self.assertIsNotNone(tag_column_ind)
            self.assertFalse(table_data.isColumnHidden(tag_column_ind))

    def test_table_data_appendix(self):
        """
        Test various behaviors of the table data view in the data browser.

        This includes verifying correct interaction with:
            - TableDataBrowser.change_cell_color
            - TableDataBrowser.section_moved
            - TableDataBrowser.selectColumn

        The test:
            - Opens a test project
            - Adds a scan via the add_path dialog
            - Mocks user interactions (dialogs)
            - Checks that editing cells updates or preserves values correctly
            - Tests column selection and header section movement
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Set often used shortcuts
        table_data = self.main_window.data_browser.table_data

        # Adds a new document to the collection
        NEW_DOC = "mock_file_name.nii"
        src = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "mia_ut_data",
            "resources",
            "mia",
            "light_test_project",
            "data",
            "downloaded_data",
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-"
            "01-G1_Guerbet_Anat-RAREpvm-000220_000.nii",
        )
        src = os.path.realpath(os.path.normpath(src))
        dst = os.path.join(os.path.dirname(new_proj_path), NEW_DOC)
        shutil.copy2(src, dst)

        with patch("PyQt5.QtWidgets.QMessageBox.show"):
            # Opens the 'add_path' pop-up
            table_data.add_path()
            add_path = self.main_window.data_browser.table_data.pop_up_add_path
            add_path.file_line_edit.setText(str([dst]))
            add_path.type_line_edit.setText(str([TYPE_NII]))
            QTest.mouseClick(add_path.ok_button, Qt.LeftButton)

        # Test initial state
        scan_cur, scan_init, scan_ui, _ = self.get_db_and_databrowser_value(
            self.main_window, 3, TAG_FILENAME
        )
        expected_path = os.path.join("data", "downloaded_data", NEW_DOC)
        self.assertEqual(scan_cur, expected_path, "Current DB value mismatch")
        self.assertEqual(scan_cur, scan_ui, "UI value mismatch")
        self.assertEqual(
            scan_cur, scan_init, "Current and initial DB value mismatch"
        )
        fov_cur, fov_init, fov_ui, _ = self.get_db_and_databrowser_value(
            self.main_window, 3, "FOV"
        )
        self.assertIsNone(fov_cur, "Current DB value mismatch")
        self.assertEqual(fov_ui, "*Not Defined*", "UI value mismatch")
        self.assertIsNone(fov_init, "Current and initial DB value mismatch")

        # Selects 'FOV' and changes its value to a new one with good type
        table_data.item(3, 3).setSelected(True)

        def exec_and_update(self):
            """Mock dialog execution to update table values."""
            self.update_table_values()
            return True

        with patch.object(ModifyTable, "exec_", new=exec_and_update):
            table_data.item(3, 3).setText("[4.0, 4.0]")
            self.main_window.data_browser.table_data.edit_table_data_values()
            table_data.item(3, 3).setSelected(False)

        # Asserts that the 'FOV' value was changed
        fov_cur, fov_init, fov_ui, _ = self.get_db_and_databrowser_value(
            self.main_window, 3, "FOV"
        )
        self.assertEqual(fov_cur, [4.0, 4.0], "Current DB value mismatch")
        self.assertEqual(fov_ui, "[4.0, 4.0]", "UI value mismatch")
        self.assertIsNone(fov_init, "Current and initial DB value mismatch")
        # Creates a tag of type float and selects it
        self.main_window.data_browser.add_tag_infos(
            "mock_tag", 0.0, FIELD_TYPE_FLOAT, "", ""
        )
        table_data.item(3, 7).setSelected(True)

        # Mocks the execution of a dialog box
        with patch.object(QMessageBox, "exec", return_value=None):
            # Tries setting an invalid string value to the tag
            table_data.item(3, 7).setText("invalid_string")
            table_data.item(3, 7).setSelected(False)

            # Asserts that the tag value was not changed
            tag_cur, tag_init, tag_ui, _ = self.get_db_and_databrowser_value(
                self.main_window, 3, "mock_tag"
            )
            self.assertEqual(tag_cur, 0.0, "Initial DB value mismatch")
            self.assertEqual(tag_ui, "0", "UI value mismatch")
            self.assertEqual(
                tag_init, tag_cur, "Current and initial DB value mismatch"
            )

            # Creates another tag of type float and selects it
            self.main_window.data_browser.add_tag_infos(
                "mock_tag_1", 0.0, FIELD_TYPE_FLOAT, "", ""
            )
            table_data.item(3, 8).setSelected(True)

            # Sets a valid float value to the tag
            table_data.item(3, 8).setText("1.0")

            # Changing the same tag does not trigger the 'valueChanged' and
            # thus not the 'change_cell_color' method
            table_data.item(3, 8).setSelected(False)

            # Asserts that the tag value was changed
            tag_cur, tag_init, tag_ui, _ = self.get_db_and_databrowser_value(
                self.main_window, 3, "mock_tag_1"
            )
            self.assertEqual(tag_cur, 1.0, "Current DB value mismatch")
            self.assertEqual(tag_ui, "1", "UI value mismatch")
            self.assertEqual(
                tag_init, 0.0, "Current and initial DB value mismatch"
            )

            # Selects the 'Exp Type' and 'FOV' of the mock scan, which have
            # distinct data types
            table_data.item(3, 2).setSelected(True)
            table_data.item(3, 3).setSelected(True)

            # Tries changing the value of 'Exp Type'
            table_data.item(3, 2).setText("mock_val")

            # Asserts that nothing was changed
            exp_cur, exp_init, exp_ui, _ = self.get_db_and_databrowser_value(
                self.main_window, 3, "Exp Type"
            )
            self.assertIsNone(exp_cur, "Current DB value mismatch")
            self.assertEqual(exp_ui, "*Not Defined*", "UI value mismatch")
            self.assertIsNone(exp_init, "Initial DB value mismatch")

            # Selects only the 'Exp Type'
            table_data.item(3, 3).setSelected(False)

            # Tries changing the value of 'Exp Type'
            table_data.item(3, 2).setText("mock_val")

            # Asserts the value was changed
            exp_cur, exp_init, exp_ui, _ = self.get_db_and_databrowser_value(
                self.main_window, 3, "Exp Type"
            )
            self.assertEqual(exp_cur, "mock_val", "Current DB value mismatch")
            self.assertEqual(exp_ui, "mock_val", "UI value mismatch")
            self.assertIsNone(exp_init, "Initial DB value mismatch")

            table_data.item(3, 2).setSelected(False)

        # TESTS SELECTION_MOVED
        # Switch columns of the 2 first tags (including the TAG_FILENAME)
        table_data.horizontalHeader().sectionMoved.emit(0, 0, 1)

        # Selects the whole filename column
        table_data.selectColumn(0)

        # Asserts that TAG_FILENAMEwas not moved
        selected_items = table_data.selectedItems()
        self.assertEqual(len(selected_items), len(table_data.scans))
        self.assertEqual(selected_items[0].text(), table_data.scans[0][0])
        self.assertEqual(
            table_data.horizontalHeaderItem(0).text(), TAG_FILENAME
        )

    def test_table_data_context_menu(self):
        """
        Simulates a right-click on a scan to display the context menu in the
        data table and triggers each available action to ensure correct
        behavior.

        This test verifies that the `TableDataBrowser.context_menu_table`
        method handles various context menu actions without error.

        Mocks:
            - QMenu.exec_: Simulates user selection of context menu actions.
            - QMessageBox.exec: Suppresses message box dialogs during the
                                test.
        """
        # Create a new lightweight test project and switch to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Get a reference to the data table
        table_data = self.main_window.data_browser.table_data

        with (
            patch.object(QMessageBox, "exec", return_value=None),
            patch.object(QMenu, "exec_", return_value=None),
        ):
            # Trigger the context menu once before simulating individual
            # actions
            table_data.context_menu_table(QPoint(10, 10))

            # List of action names to simulate from the context menu
            action_names = [
                "action_reset_cell",
                "action_reset_column",
                "action_reset_row",
                "action_clear_cell",
                "action_add_scan",
                "action_remove_scan",
                "action_sort_column",
                "action_sort_column_descending",
                "action_visualized_tags",
                "action_select_column",
                "action_multiple_sort",
                "action_send_documents_to_pipeline",
                "action_display_file",
                # Note: 'action_sort_column' may cause instability
            ]

            # Simulate selecting each action via the context menu
            for action_name in action_names:

                with patch.object(
                    QMenu,
                    "exec_",
                    return_value=getattr(table_data, action_name),
                ):
                    table_data.context_menu_table(QPoint(10, 10))

    def test_undo_redo_databrowser(self):
        """
        Test undo and redo functionality in the DataBrowser across
        several operations.

        This test verifies that user actions such as modifying a tag value,
        removing scans, adding/removing/cloning tags are correctly recorded
        in the project's undo/redo stacks, and that the database and GUI
        reflect the expected changes after each undo/redo operation.

        Tested operations include:
            1. Modifying a tag value ("BandWidth") of a scan and
               undoing/redoing the change.
            2. Attempting to undo the deletion of a scan (should have
               no effect).
            3. Adding a new tag ("Test") and verifying undo/redo toggles
               it properly.
            4. Removing an existing tag and checking undo/redo consistency.
            5. Cloning an existing tag ("FOV") to create a new one ("Test"),
            verifying values in both the database and DataBrowser.

        Ensures:
            - Undo/redo stacks (`project.undos` and `project.redos`) are
              updated appropriately.
            - DataBrowser UI and internal database states remain synchronized.
            - Non-reversible operations (e.g., scan deletion) behave as
              expected.
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Get a reference to the data table
        table = self.main_window.data_browser.table_data

        # 1. Tag value (list)
        # Initial undo/redo stacks must be empty
        self.assertListEqual(self.main_window.project.undos, [])
        self.assertListEqual(self.main_window.project.redos, [])

        # DataBrowser value for the second document
        bw_col = table.get_tag_column("BandWidth")
        bw_item = table.item(1, bw_col)
        old_value = float(bw_item.text().strip("[]"))

        # Check the value is the good one (50000)
        self.assertEqual(old_value, 50000.0)

        # Change the value from 50000 to 0.0
        bw_item.setSelected(True)

        def exec_and_update(self):
            """Mock dialog execution to update table values."""
            self.update_table_values()
            return True

        with patch.object(ModifyTable, "exec_", new=exec_and_update):
            bw_item.setText("[0.0]")
            table.edit_table_data_values()
            bw_item = table.item(1, bw_col)
            bw_item.setSelected(False)

        # Check project.undos and project.redos have the right values.
        expected_mod = [
            [
                "modified_values",
                [
                    [
                        "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii",
                        "BandWidth",
                        [50000.0],
                        [0.0],
                    ]
                ],
            ]
        ]
        self.assertListEqual(self.main_window.project.undos, expected_mod)
        self.assertEqual(self.main_window.project.redos, [])

        # Check the value has really been changed to 0.0.
        self.assertEqual(float(bw_item.text().strip("[]")), 0.0)

        scan_name = table.item(1, 0).text()

        with self.main_window.project.database.data() as db:
            self.assertEqual(
                db.get_value(COLLECTION_CURRENT, scan_name, "BandWidth"), [0]
            )
            self.assertEqual(
                db.get_value(COLLECTION_INITIAL, scan_name, "BandWidth"),
                [50000],
            )

        # Undo
        self.main_window.action_undo.trigger()

        # Check the value has really been reset to 50000
        self.assertEqual(float(bw_item.text().strip("[]")), 50000.0)

        # Check undos / redos have the right values
        self.assertListEqual(self.main_window.project.redos, expected_mod)
        self.assertListEqual(self.main_window.project.undos, [])

        # Redo
        self.main_window.action_redo.trigger()

        # Check the value has really been reset to 0.0
        self.assertEqual(float(bw_item.text().strip("[]")), 0.0)

        # we test undos / redos have the right values
        self.assertListEqual(self.main_window.project.undos, expected_mod)
        self.assertEqual(self.main_window.project.redos, [])

        # 2. Remove a scan (document)
        # Check there are 9 documents in db (current and initial)
        with self.main_window.project.database.data() as db:
            self.assertEqual(
                9,
                len(db.get_document_names(COLLECTION_CURRENT)),
            )
            self.assertEqual(
                9,
                len(db.get_document_names(COLLECTION_INITIAL)),
            )

        # Remove the eighth document
        table.selectRow(8)
        table.remove_scan()

        # Check if there are now 8 documents in db (current and initial)
        with self.main_window.project.database.data() as db:
            self.assertEqual(
                8,
                len(db.get_document_names(COLLECTION_CURRENT)),
            )
            self.assertEqual(
                8,
                len(db.get_document_names(COLLECTION_INITIAL)),
            )

        # Undo
        self.main_window.action_undo.trigger()

        # Check there are still only 8 documents in the database
        # (current and initial). In fact the document has been permanently
        # deleted and we cannot recover it in this case. It is not possible to
        # undo the deletion of a document. Here, the undo will apply to the
        # last modification of the BandWidth value.
        with self.main_window.project.database.data() as db:
            self.assertEqual(
                8,
                len(db.get_document_names(COLLECTION_CURRENT)),
            )
            self.assertEqual(
                8,
                len(db.get_document_names(COLLECTION_INITIAL)),
            )

            # Check the value has really been reset to 50000
            self.assertEqual(float(bw_item.text().strip("[]")), 50000.0)

            # Check undos / redos have the right values
            self.assertListEqual(self.main_window.project.redos, expected_mod)
            self.assertEqual(self.main_window.project.undos, [])
            self.assertEqual(
                db.get_value(COLLECTION_CURRENT, scan_name, "BandWidth"),
                [50000],
            )
            self.assertEqual(
                db.get_value(COLLECTION_INITIAL, scan_name, "BandWidth"),
                [50000],
            )

        # 3. Add a tag
        # Check we don't have 'Test' tag in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertNotIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertNotIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsNone(table.get_tag_column("Test"))

        # Add the Test tag
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        add_tag.text_edit_tag_name.setText("Test")
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)

        # Check the 'Test' tag is in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsInstance(table.get_tag_column("Test"), int)

        # Undo
        self.main_window.action_undo.trigger()

        # Check 'Test' tag is not in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertNotIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertNotIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsNone(table.get_tag_column("Test"))

        # Redo
        self.main_window.action_redo.trigger()

        # Check the 'Test' tag is in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsInstance(table.get_tag_column("Test"), int)

        # 4. Remove tag
        # Remove the 'Test' tag
        self.main_window.data_browser.remove_tag_action.trigger()
        remove_tag = self.main_window.data_browser.pop_up_remove_tag
        remove_tag.list_widget_tags.setCurrentRow(1)  # 'Test' tag selected
        QTest.mouseClick(remove_tag.push_button_ok, Qt.LeftButton)

        # Check 'Test' tag is not in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertNotIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertNotIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsNone(table.get_tag_column("Test"))

        # Undo
        self.main_window.action_undo.trigger()

        # Check 'Test' tag is in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsInstance(table.get_tag_column("Test"), int)

        # Redo
        self.main_window.action_redo.trigger()

        # Check 'Test' tag is not in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertNotIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertNotIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsNone(table.get_tag_column("Test"))

        # 4. Clone tag 'FOV' to 'Test'
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag

        for i in range(clone_tag.list_widget_tags.count()):

            if clone_tag.list_widget_tags.item(i).text() == "FOV":
                clone_tag.list_widget_tags.setCurrentRow(i)
                break

        # 'FOV' tag selected
        clone_tag.line_edit_new_tag_name.setText("Test")
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)

        # Check 'Test' tag is in the db and in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertIn("Test", db.get_field_names(COLLECTION_CURRENT))
            self.assertIn("Test", db.get_field_names(COLLECTION_INITIAL))
            self.assertIsInstance(table.get_tag_column("Test"), int)

        # Value in the db
        item = table.item(1, 0)
        scan_name = item.text()

        with self.main_window.project.database.data() as db:
            value_cur = db.get_value(COLLECTION_CURRENT, scan_name, "Test")
            value_init = db.get_value(COLLECTION_INITIAL, scan_name, "Test")

        # Value in the DataBrowser
        test_column = table.get_tag_column("Test")
        item = table.item(1, test_column)
        databrowser_val = item.text()

        # Check equality between DataBrowser and db
        self.assertEqual(value_cur, [3.0, 3.0])
        self.assertEqual(value_cur, ast.literal_eval(databrowser_val))
        self.assertEqual(value_cur, value_init)

        # Undo
        self.main_window.action_undo.trigger()

        # Check 'Test' tag is not in the db and not in the DataBrowser
        with self.main_window.project.database.data() as db:
            self.assertFalse("Test" in db.get_field_names(COLLECTION_CURRENT))
            self.assertFalse("Test" in db.get_field_names(COLLECTION_INITIAL))

        self.assertIsNone(table.get_tag_column("Test"))

    def test_unnamed_proj_soft_open(self):
        """
        Test that an unnamed project is correctly initialized at software
        startup.

        Verifies that:
            - The project instance is created and named "Unnamed project".
            - The default tags in the 'current' collection are correctly set.
            - No documents exist in 'current' and 'initial' collections.
            - All expected collections are present.
            - The main window title reflects the unnamed project.
        """

        self.assertIsInstance(self.project, Project)
        self.assertEqual(self.main_window.project.getName(), "Unnamed project")

        with self.main_window.project.database.data() as db:
            tags = db.get_field_names(COLLECTION_CURRENT)
            expected_tags = {
                TAG_CHECKSUM,
                TAG_FILENAME,
                TAG_TYPE,
                TAG_EXP_TYPE,
                TAG_BRICKS,
                TAG_HISTORY,
            }
            self.assertEqual(set(tags), expected_tags)
            self.assertListEqual(db.get_document_names(COLLECTION_CURRENT), [])
            self.assertListEqual(db.get_document_names(COLLECTION_INITIAL), [])

            collections = db.get_collection_names()

            expected_collections = {
                FIELD_ATTRIBUTES_COLLECTION,
                COLLECTION_INITIAL,
                COLLECTION_CURRENT,
                COLLECTION_BRICK,
                COLLECTION_HISTORY,
            }
            self.assertEqual(set(collections), expected_collections)

            self.assertEqual(
                self.main_window.windowTitle(),
                "MIA - Multiparametric Image Analysis "
                "(Admin mode) - Unnamed project",
            )

    def test_update_default_value(self):
        """
        Test the update of default tag values for various input types via the
        DefaultValueListCreation mechanism.

        This test verifies:
            - Table behavior for different input formats (empty string,
              non-empty string, valid list).
            - Addition, removal, and resizing of list elements.
            - Update behavior across multiple field types.
            - Error handling for invalid input types.
        """
        # Set shortcuts for objects that are often used
        data_browser = self.main_window.data_browser

        # The objects are successively created in the following order:
        # PopUpAddTag > DefaultValueQLineEdit > DefaultValueListCreation
        pop_up = PopUpAddTag(data_browser, data_browser.project)
        text_edit = pop_up.text_edit_default_value

        # Assures the instantiation of 'DefaultValueListCreation'
        # text_edt.parent.type = "list_"
        text_edit.parent.type = FIELD_TYPE_LIST_STRING

        # Mocks the execution of a dialog window
        with patch.object(DefaultValueListCreation, "show"):
            # 'DefaultValueListCreation' can be instantiated with an empty
            # string, non-empty string or list
            # Only a list leads to the table values being filled
            # - Case: empty string
            text_edit.setText("")
            text_edit.mousePressEvent(None)
            self.assertEqual(
                text_edit.list_creation.table.item(0, 0).text(), ""
            )

            # - Case: non-empty string
            text_edit.setText("non_empty")
            text_edit.mousePressEvent(None)
            self.assertEqual(
                text_edit.list_creation.table.item(0, 0).text(), ""
            )

            # - Case: valid list (length == 2)
            text_edit.setText("[1, 2]")
            text_edit.mousePressEvent(None)
            table = text_edit.list_creation.table
            self.assertEqual(table.item(0, 0).text(), "1")
            self.assertEqual(table.item(0, 1).text(), "2")
            self.assertEqual(table.columnCount(), 2)

            # Test add and remove element
            text_edit.list_creation.add_element()
            self.assertEqual(table.columnCount(), 3)

            text_edit.list_creation.remove_element()
            self.assertEqual(table.columnCount(), 2)

            # Resize table
            text_edit.list_creation.resize_table()
            table.setColumnWidth(0, 900)
            text_edit.list_creation.resize_table()

            # Test various data types
            test_cases = [
                (FIELD_TYPE_LIST_INTEGER, "[1]"),
                (FIELD_TYPE_LIST_FLOAT, "[1.1]"),
                (FIELD_TYPE_LIST_BOOLEAN, "[True]"),
                (FIELD_TYPE_LIST_BOOLEAN, "[False]"),
                (FIELD_TYPE_LIST_STRING, '["str"]'),
                (FIELD_TYPE_LIST_DATE, '["11/11/1111"]'),
                (FIELD_TYPE_LIST_DATETIME, '["11/11/1111 11:11:11.11"]'),
                (FIELD_TYPE_LIST_TIME, '["11:11:11.11"]'),
            ]

            for field_type, value in test_cases:
                text_edit.setText(value)
                text_edit.mousePressEvent(None)
                text_edit.list_creation.type = field_type
                text_edit.list_creation.update_default_value()

            # Test ValueError handling with invalid boolean string, mocks the
            # execution of a dialog box
            with patch.object(QMessageBox, "exec"):
                text_edit.setText('["not_boolean"]')
                text_edit.mousePressEvent(None)
                text_edit.list_creation.type = FIELD_TYPE_LIST_BOOLEAN
                text_edit.list_creation.update_default_value()

    def test_utils(self):
        """
        Test utility functions for type checking and conversion from UI table
        strings to correctly typed Python values for various field types.

        Functions tested:
            - check_value_type: validates if a string value matches a given
                                field type.
            - table_to_database: converts a string value from the UI into a
                                 typed value suitable for storage in the
                                 database.
        """
        # Boolean tests
        boolean_cases = [
            (True, True),
            ("False", False),
        ]

        for input_value, expected in boolean_cases:
            with self.subTest(field_type="boolean", input=input_value):
                self.assertEqual(
                    table_to_database(input_value, FIELD_TYPE_BOOLEAN),
                    expected,
                )

        # Date test
        date_str = "01/01/2019"
        date_format = "%d/%m/%Y"
        expected_date = datetime.strptime(date_str, date_format).date()
        self.assertTrue(check_value_type(date_str, FIELD_TYPE_DATE))
        self.assertEqual(
            table_to_database(date_str, FIELD_TYPE_DATE), expected_date
        )

        # Datetime test
        datetime_str = "15/7/2019 16:16:55.789643"
        datetime_format = "%d/%m/%Y %H:%M:%S.%f"
        expected_datetime = datetime.strptime(datetime_str, datetime_format)
        self.assertTrue(check_value_type(datetime_str, FIELD_TYPE_DATETIME))
        self.assertEqual(
            table_to_database(datetime_str, FIELD_TYPE_DATETIME),
            expected_datetime,
        )

        # Time test
        time_str = "16:16:55.789643"
        time_format = "%H:%M:%S.%f"
        expected_time = datetime.strptime(time_str, time_format).time()
        self.assertTrue(check_value_type(time_str, FIELD_TYPE_TIME))
        self.assertEqual(
            table_to_database(time_str, FIELD_TYPE_TIME), expected_time
        )

    def test_visualized_tags(self):
        """
        Validate the tag visibility management system and its impact on the
        DataBrowser UI.

        This test simulates user interaction with the tag visibility popup
        and verifies:
            - Default visible tags are correctly initialized.
            - UI column headers match backend tag visibility.
            - System tags (e.g., checksum, history) remain hidden.
            - Filename tag is always visible and in the first column.
            - Tags can be hidden and re-shown via the interface.
        """
        data_browser = self.main_window.data_browser
        table = data_browser.table_data

        # Verify initial default tag visibility state
        with self.main_window.project.database.data() as database_data:
            visible_tags = database_data.get_shown_tags()

        expected_tags = {TAG_FILENAME, TAG_BRICKS, TAG_TYPE, TAG_EXP_TYPE}
        self.assertSetEqual(set(visible_tags), expected_tags)

        # Verify UI column display matches backend state
        self.assertEqual(table.columnCount(), 4)

        displayed_columns = [
            table.horizontalHeaderItem(i).text()
            for i in range(table.columnCount())
            if not table.isColumnHidden(i)
        ]

        self.assertSetEqual(set(displayed_columns), set(visible_tags))

        # Ensure filename tag is always the first column
        first_column_tag = table.horizontalHeaderItem(0).text()
        self.assertEqual(first_column_tag, TAG_FILENAME)

        # Open tag management popup
        QTest.mouseClick(data_browser.visualized_tags_button, Qt.LeftButton)
        settings = table.pop_up

        # Ensure system tags are not visible in tag manager
        for system_tag in [TAG_CHECKSUM, TAG_HISTORY]:
            settings.tab_tags.search_bar.setText(system_tag)
            tag_count = settings.tab_tags.list_widget_tags.count()
            self.assertEqual(tag_count, 0)

        # Check manageable (non-system) tags
        settings.tab_tags.search_bar.setText("")
        selected_tags_widget = settings.tab_tags.list_widget_selected_tags

        manageable_tags = [
            selected_tags_widget.item(i).text()
            for i in range(selected_tags_widget.count())
        ]
        expected_manageable = {TAG_BRICKS, TAG_EXP_TYPE, TAG_TYPE}
        self.assertSetEqual(set(manageable_tags), expected_manageable)
        self.assertNotIn(TAG_FILENAME, manageable_tags)

        # Simulate hiding the BRICKS tag
        selected_tags_widget.item(2).setSelected(True)
        QTest.mouseClick(
            settings.tab_tags.push_button_unselect_tag, Qt.LeftButton
        )

        visible_tags = [
            selected_tags_widget.item(i).text()
            for i in range(selected_tags_widget.count())
        ]

        self.assertSetEqual(set(visible_tags), {TAG_TYPE, TAG_EXP_TYPE})
        QTest.mouseClick(settings.push_button_ok, Qt.LeftButton)

        with self.main_window.project.database.data() as database_data:
            new_visible_tags = database_data.get_shown_tags()

        self.assertSetEqual(
            set(new_visible_tags), {TAG_FILENAME, TAG_TYPE, TAG_EXP_TYPE}
        )

        displayed_columns = [
            table.horizontalHeaderItem(i).text()
            for i in range(table.columnCount())
            if not table.isColumnHidden(i)
        ]

        self.assertSetEqual(
            set(displayed_columns), {TAG_FILENAME, TAG_TYPE, TAG_EXP_TYPE}
        )

        # Simulate showing the BRICKS tag again
        QTest.mouseClick(data_browser.visualized_tags_button, Qt.LeftButton)
        settings = table.pop_up
        settings.tab_tags.search_bar.setText(TAG_BRICKS)
        settings.tab_tags.list_widget_tags.item(0).setSelected(True)
        QTest.mouseClick(
            settings.tab_tags.push_button_select_tag, Qt.LeftButton
        )
        QTest.mouseClick(settings.push_button_ok, Qt.LeftButton)

        with self.main_window.project.database.data() as database_data:
            new_visible_tags = database_data.get_shown_tags()

        self.assertSetEqual(
            set(new_visible_tags),
            {TAG_FILENAME, TAG_TYPE, TAG_EXP_TYPE, TAG_BRICKS},
        )

        displayed_columns = [
            table.horizontalHeaderItem(i).text()
            for i in range(table.columnCount())
            if not table.isColumnHidden(i)
        ]
        self.assertSetEqual(
            set(displayed_columns),
            {TAG_FILENAME, TAG_TYPE, TAG_EXP_TYPE, TAG_BRICKS},
        )


class TestMIAMainWindow(TestMIACase):
    """Tests for the main window class (MainWindow).

    :Contains:
        :Method:
            - test_check_database: checks if the database has changed
              since the scans were first imported
            - test_create_project_pop_up: tries to create a new project
              with a project already open.
            - test_files_in_project: tests whether or not a given file
              is part of the project.
            - test_import_data: opens a project and simulates importing
              a file from the MriConv java executable
            - test_open_project_pop_up: creates a test project and opens
              a project, including unsaved modifications.
            - test_open_recent_project: creates 2 test projects and
              opens one by the recent projects action.
            - test_open_shell: opens Qt console and kill it afterwards.
            - test_package_library_dialog_add_pkg: creates a new project
              folder, opens the processes library and adds a package.
            - test_package_library_dialog_del_pkg: creates a new project
              folder, opens the processes library and deletes a package.
            - test_package_library_dialog_rmv_pkg: creates a new project
              folder, opens the processes library and removes a package.
            - test_package_library_others: Creates a new project folder, opens
              the processes library and adds a package.
            - test_popUpDeletedProject: adds a deleted projects to the
              projects list and launches mia.
            - test_popUpDeleteProject: creates a new project and deletes
              it.
            - test_see_all_projects: creates 2 projects and tries to
              open them through the all projects pop-up.
            - test_software_preferences_pop_up: opens the preferences
              pop up and changes parameters.
            - test_software_preferences_pop_up_config_file: opens the
              preferences pop up and changes parameters.
            - test_software_preferences_pop_up_modules_config: changes
              the configuration of AFNI, ANTS, FSL, SPM, mrtrix and MATLAB.
            - test_software_preferences_pop_up_validate: opens the
              preferences pop up for AFNI, ANTS, FSL, SPM, mrtrix and MATLAB.
            - test_switch_project: create project and switches to it.
            - test_tab_changed: switches between data browser, data
              viewer and pipeline manager.
    """

    def test_check_database(self):
        """
        Test detection of changes in the project's database after file removal.

        This test verifies that the application correctly identifies changes
        to the database, such as a missing file after import.
        """
        # Create and switch to a new test project
        test_proj_path = self.get_new_test_project()
        self.main_window.switch_project(test_proj_path, "test_project")

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager

        # Construct path to a file and remove it
        ppl_manager.project.folder = test_proj_path
        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )
        file_path = os.path.abspath(
            os.path.join(test_proj_path, "data", "raw_data", NII_FILE_1)
        )
        os.remove(file_path)

        # Check if the files of the database have been modified
        with patch.object(
            QMessageBox, "exec", return_value=QMessageBox.Accepted
        ) as mock_exec:
            self.main_window.action_check_database.triggered.emit()
            self.assertTrue(mock_exec.called)

    def test_create_project_pop_up(self):
        """Test project creation popup behavior under various conditions.

        Verifies the MainWindow.create_project_pop_up method handles:
            - Project creation with unsaved modifications (triggers quit popup)
            - Project creation without configured projects folder (shows error)
            - Normal project creation flow with proper configuration

        Components tested:
            MainWindow.create_project_pop_up, PopUpNewProject

        Mocked components:
            PopUpQuit.exec, QMessageBox.exec, PopUpNewProject.exec
        """
        # Creates a new project folder
        new_proj_path = self.get_new_test_project(light=True)

        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_"
            "Guerbet_Anat-RAREpvm-000220_000.nii"
        )
        DOCUMENT_1 = os.path.join("data", "downloaded_data", NII_FILE_1)

        # Adds a document to the collection
        with self.main_window.project.database.data(
            write=True
        ) as database_data:
            database_data.add_document(COLLECTION_CURRENT, DOCUMENT_1)

        # Mocks the execution of the pop-up quit
        with patch.object(PopUpQuit, "exec", new=lambda self: self.show()):
            # Tries to create a project with unsaved modifications
            self.main_window.create_project_pop_up()

        # Closes the error dialog
        self.assertTrue(hasattr(self.main_window, "pop_up_close"))
        self.main_window.pop_up_close.accept()

        # Remove the document from the DB
        with self.main_window.project.database.data(
            write=True
        ) as database_data:
            database_data.remove_document(COLLECTION_CURRENT, DOCUMENT_1)

        # Mocks the execution of a pop-up
        with patch.object(QMessageBox, "exec", lambda self_: self_.show()):
            # Resets the projects folder
            config = Config(properties_path=self.properties_path)
            config.set_projects_save_path(None)

            # Tries to create a new project without setting the projects folder
            self.main_window.create_project_pop_up()

        self.assertTrue(hasattr(self.main_window, "msg"))
        self.main_window.msg.accept()

        # Sets the projects folder path
        proj_folder = os.path.split(new_proj_path)[0]
        config = Config(properties_path=self.properties_path)
        config.set_projects_save_path(proj_folder)

        # Mocks the execution of 'PopUpNewProject
        with patch.object(PopUpNewProject, "exec", lambda self_, *args: None):
            # Opens the "create project" pop-up
            self.main_window.create_project_pop_up()

        # Tries to create a new project in the same directory of an
        # existing one
        self.main_window.exPopup.get_filename([DOCUMENT_1])

        # Creates a new project
        self.main_window.exPopup.get_filename(
            [os.path.join("data", "downloaded_data", "new_project")]
        )

    def test_files_in_project(self):
        """
        Test MainWindow.project.files_in_project method.

        Verifies that the method correctly identifies which files belong to
        the project, handling invalid inputs and files both inside and outside
        the project directory.
        """

        # Creates a now test project
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.project.folder = test_proj_path

        # Invalid input (non-string) returns empty set
        res = self.main_window.project.files_in_project([{"mock_key": False}])
        self.assertEqual(res, set())

        # File outside project returns empty set
        res = self.main_window.project.files_in_project("/out_of_project")
        self.assertEqual(res, set())

        # File within project returns filename
        res = self.main_window.project.files_in_project(
            os.path.join(test_proj_path, "mock_file")
        )
        self.assertEqual(res, {"mock_file"})

    def test_import_data(self):
        """
        Test importing data via the mocked MRI conversion process.

        This test simulates opening a project, setting up a mock Java
        executable for MRI conversion, and importing a scan file into the
        project.

        It verifies:
            - The integration with `read_log` (from `data_loader.py`)
            - Proper behavior of `ImportProgress`

        Mocks within this test:
            - `ImportWorker.start` to prevent actual threading
            - `ImportProgress.exec` to run the worker directly
        """

        # Prepare test project and switch context
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_proj_path, "test_project")

        # Create a mock conversion Java executable
        mock_mriconv_path = os.path.join(
            test_proj_path, "mock_mriconv", "mockapp.jar"
        )
        os.makedirs(os.path.dirname(mock_mriconv_path), exist_ok=True)
        self.assertEqual(self.create_mock_jar(mock_mriconv_path), 0)

        # Configure path to the mocked executable
        config = Config()
        config.set_mri_conv_path(os.path.normpath(mock_mriconv_path))

        # Retrieve first document from current collection
        with self.main_window.project.database.data() as db_data:
            document_1 = db_data.get_document_names(COLLECTION_CURRENT)[0]

        document_1_name = os.path.splitext(os.path.basename(document_1))[0]

        # Gets the 'raw_data' folder path, where the scan will be import
        raw_data_folder = os.path.join(test_proj_path, "data", "raw_data")

        # Copies a scan to the raw data folder
        shutil.copy(
            os.path.join(test_proj_path, document_1),
            os.path.join(raw_data_folder, os.path.basename(document_1)),
        )

        # Create JSON tag file with metadata for the scan,
        # in the raw data folder.
        json_tag_data = {
            "AcquisitionTime": {
                "format": "HH:mm:ss.SSS",
                "description": "The time the acquisition of data.",
                "units": "mock_unit",
                "type": "time",
                "value": ["00:09:40.800"],
            },
            "BandWidth": {
                "format": None,
                "description": "",
                "units": TAG_UNIT_MHZ,
                "type": "float",
                "value": [[50000.0]],
            },
        }
        json_tag_path = os.path.join(
            raw_data_folder, f"{document_1_name}.json"
        )

        with open(json_tag_path, "w") as file:
            json.dump(json_tag_data, file)

        # Create a mock logExport JSON file, in the raw data folder
        json_export_data = [
            {
                "StatusExport": "Export ok",
                "NameFile": document_1_name,
                "Bvec_bval": "no",
            }
        ]
        json_export_path = os.path.join(raw_data_folder, "logExportMock.json")

        with open(json_export_path, "w") as f:
            json.dump(json_export_data, f)

        # Mock ImportWorker.start and ImportProgress.exec only during
        # import_data call
        with (
            patch(
                "populse_mia.data_manager.data_loader.ImportWorker.start",
                lambda self_, *args: None,
            ),
            patch(
                "populse_mia.data_manager.data_loader.ImportProgress.exec",
                lambda self_, *args: self_.worker.run(),
            ),
        ):
            scan_added = read_log(self.main_window.project, self.main_window)

            # Mocks importing a scan, runs a mocked java executable instead
            # of the 'MRIManager.jar'
            self.main_window.import_data()

        # Verify the scan was imported into the 'raw_data' folder
        expected_scan_path = os.path.normpath(
            document_1.replace("downloaded_data", "raw_data")
        )
        scans = [
            os.path.normpath(p)
            for p in self.main_window.data_browser.table_data.scans_to_visualize
        ]
        # Asserts that the first scan was added to the 'raw_data' folder
        self.assertIn(expected_scan_path, scans)
        self.assertIn(expected_scan_path, scan_added)

    def test_open_project_pop_up(self):
        """
        Test the behavior of MainWindow.open_project_pop_up under different
        project state conditions, including:

        - No project save directory set
        - Project opened successfully
        - Project with unsaved modifications

        Mocks the following components:
            - QMessageBox.exec
            - PopUpOpenProject.exec
            - PopUpQuit.exec
        """

        # Create a lightweight test project and switch to it
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_proj_path, "test_project")

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser

        with patch(
            "PyQt5.QtWidgets.QMessageBox.exec",
            lambda self_, *args: self_.show(),
        ):
            # Reset the projects save directory
            Config().set_projects_save_path(None)

            # Attempt to open a project without a set save directory
            self.main_window.open_project_pop_up()
            self.main_window.msg.accept()

            # Set the project save directory
            config = Config(properties_path=self.properties_path)
            config.set_projects_save_path(os.path.dirname(test_proj_path))

        with patch(
            "populse_mia.user_interface.pop_ups.PopUpOpenProject.exec",
            lambda self_, *args: self_.show(),
        ):
            # Open a project successfully
            self.main_window.open_project_pop_up()

            self.main_window.exPopup.get_filename((test_proj_path,))

            # Delete the first scan from the data browser
            data_browser.table_data.selectRow(0)
            data_browser.table_data.remove_scan()

            # Ensure unsaved modifications are detected
            self.assertTrue(self.main_window.check_unsaved_modifications())

        with patch(
            "populse_mia.user_interface.pop_ups.PopUpQuit.exec",
            lambda self_: self_.show(),
        ):
            # Attempt to open another project with unsaved modifications
            self.main_window.open_project_pop_up()
            self.main_window.pop_up_close.accept()

    def test_open_recent_project(self):
        """
        Test opening a recent project via the 'recent projects' action.

        This includes switching between two projects, saving one, verifying
        its presence in the recent projects list, and reopening it.

        - Tests: MainWindow.open_recent_project
        """

        # Create two test projects
        proj_test_1_path = self.get_new_test_project(
            name="test_project_1", light=True
        )
        proj_test_2_path = self.get_new_test_project(
            name="test_project_2", light=True
        )

        # Switches to the first one
        self.main_window.switch_project(proj_test_1_path, "test_project_1")
        config = Config(properties_path=self.properties_path)
        config.set_projects_save_path(os.path.dirname(proj_test_1_path))
        self.main_window.saved_projects_list.append(proj_test_1_path)

        # Saves project 1
        self.main_window.saveChoice()

        # Switches to project 2
        self.main_window.switch_project(proj_test_2_path, "test_project_2")

        # Verify project 1 is listed as a recent project
        self.assertTrue(self.main_window.saved_projects_actions[0].isVisible())

        # Trigger opening of project 1 from recent projects
        self.main_window.saved_projects_actions[0].triggered.emit()

        # Verify project 1 is now the opened project
        config = Config(properties_path=self.properties_path)
        self.assertEqual(
            os.path.abspath(config.get_opened_projects()[0]), proj_test_1_path
        )

        # Try to simulate unsaved modifications
        # known macOS issue
        self.main_window.data_browser.table_data.selectRow(0)

        # FIXME: following line causes sqlite3.OperationalError,
        #        due to "attempt to write a readonly database",
        #        only on macos build:
        # Traceback (most recent call last):
        # File "/Users/appveyor/projects/populse-mia/populse_mia/
        # test.py",
        # line 3797, in test_open_recent_project
        # self.main_window.data_browser.table_data.remove_scan()
        # File "/Users/appveyor/projects/populse-mia/populse_mia/
        # user_interface/data_browser/data_browser.py", line 2055, in
        # remove_scan
        # scan_path)
        # File "/Users/appveyor/projects/populse_db/python/populse_db/
        # database.py", line 724, in remove_document
        # self.engine.remove_document(collection, document_id)
        # File "/Users/appveyor/projects/populse_db/python/populse_db/
        # engine/sqlite.py", line 628, in remove_document
        # self.remove_value(collection, document_id, field.field_name)
        # File "/Users/appveyor/projects/populse_db/python/populse_db/
        # engine/sqlite.py", line 612, in remove_value
        # self.cursor.execute(sql, [document_id])
        # sqlite3.OperationalError: attempt to write a readonly database

        self.main_window.data_browser.table_data.remove_scan()

        # Asserts that there are unsaved modification
        # FIXME: By commenting the previous line we have to also comment the
        #       following line:

        self.assertTrue(self.main_window.check_unsaved_modifications())

        # PopUpQuit.exec = lambda self_: self_.show()

        with patch(
            "populse_mia.user_interface.pop_ups.PopUpQuit.exec",
            lambda self_: self_.show(),
        ):
            # Tries to open a project with unsaved modifications
            self.main_window.saved_projects_actions[0].triggered.emit()

    @unittest.skip("Not currently available on all the platforms")
    # @unittest.skipUnless(sys.platform.startswith("linux"), "requires linux")
    def test_open_shell(self):
        """Opens a Qt console and kill it afterward.

        -Tests: MainWindow.open_shell

        Currently, this test is only done on linux.
        """

        # Opens the Qt console
        self.main_window.action_open_shell.triggered.emit()

        qt_console_process = None
        time_elapsed = 0

        while time_elapsed < 5:
            # Gets the current process
            current_process = psutil.Process()
            children = current_process.children(recursive=True)

            # If qt_console_process is not none, the qt console process
            # was found
            if qt_console_process:
                break

            if children:
                # Gets the process pid (process id)
                for child in children:
                    if child.name() == "jupyter-qtconso":
                        qt_console_process = child.pid

            sleep(1)
            time_elapsed += 1

        if qt_console_process:
            # Kills the Qt console
            os.kill(qt_console_process, 9)

        else:
            print("the Qt console process was not found")

    def test_package_library_dialog_add_pkg(self):
        """Creates a new project folder, opens the processes library and
        adds a package.

        - Tests: PackageLibraryDialog

        - Mocks:
            - QMessageBox.exec
            - QMessageBox.exec_
            - QFileDialog.exec_
        """

        PKG = "nipype.interfaces.DataGrabber"

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Set shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl_edt_tab = ppl_edt_tabs.get_current_editor()
        ppl = ppl_edt_tabs.get_current_pipeline()
        proc_lib_view = ppl_manager.processLibrary.process_library

        # Opens the package library pop-up
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library

        # Clicks on the add package button without selecting anything
        QMessageBox.exec = lambda x: None
        QMessageBox.exec_ = lambda x: None
        pkg_lib_window.layout().children()[0].layout().children()[1].itemAt(
            0
        ).widget().clicked.emit()

        # Open a browser to select a package
        QFileDialog.exec_ = lambda x: True
        # proc_lib_view.pkg_library.browse_package()

        # Fill in the line edit to "PKG" then click on the add package button
        pkg_lib_window.line_edit.setText(PKG)
        proc_lib_view.pkg_library.is_path = False
        os.environ["FSLOUTPUTTYPE"] = "NIFTI"
        stdout_fileno = sys.stdout
        f = open(os.devnull, "w")
        sys.stdout = f
        pkg_lib_window.layout().children()[0].layout().children()[1].itemAt(
            0
        ).widget().clicked.emit()
        f.close()
        sys.stdout = stdout_fileno
        # Resets the previous action
        pkg_lib_window.add_list.selectAll()
        pkg_lib_window.layout().children()[0].layout().itemAt(
            8
        ).widget().layout().itemAt(1).widget().clicked.emit()

        # Apply changes, close the package library pop-up
        pkg_lib_window.ok_clicked()

        # Opens again the package library pop-up
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library

        # Writes the name of a non-existent package on the line edit
        pkg_lib_window.line_edit.setText("non-existent")

        # Clicks on the add package button
        pkg_lib_window.layout().children()[0].layout().children()[1].itemAt(
            0
        ).widget().clicked.emit()

        # Apply changes, close the package library pop-up
        pkg_lib_window.ok_clicked()

        # Makes a mocked process folder "Mock_process" in the temporary
        # project path
        mock_proc_fldr = os.path.join(
            new_proj_path, "processes", "UTs_processes"
        )
        os.makedirs(mock_proc_fldr, exist_ok=True)

        # Make a '__init__.py' in the mock_proc_fldr that raise
        # an 'ImportError'
        init_file = open(os.path.join(mock_proc_fldr, "__init__.py"), "w")
        init_file.write("raise ImportError('mock_import_error')")
        init_file.close()

        # Make a 'test_unit_test_1.py' in the mock_proc_fldr with a
        # real process
        unit_test = open(os.path.join(mock_proc_fldr, "unit_test_1.py"), "w")
        unit_test.writelines(
            [
                "from capsul.api import Pipeline\n",
                "import traits.api as traits\n",
                "class Unit_test_1(Pipeline):\n",
                "    def pipeline_definition(self):\n",
                "        self.add_process('smooth_1', "
                "'mia_processes.bricks.preprocess.spm.spatial_preprocessing."
                "Smooth')\n",
                "        self.export_parameter('smooth_1', 'in_files', "
                "is_optional=False)\n",
                "        self.export_parameter('smooth_1', 'fwhm', "
                "is_optional=True)\n",
                "        self.export_parameter('smooth_1', 'data_type', "
                "is_optional=True)\n",
                "        self.export_parameter('smooth_1', 'implicit_masking',"
                " is_optional=True)\n",
                "        self.export_parameter('smooth_1', 'out_prefix', "
                "is_optional=True)\n",
                "        self.export_parameter('smooth_1', 'smoothed_files', "
                "is_optional=False)\n",
                "        self.reorder_traits(('in_files', 'fwhm', 'data_type',"
                " 'implicit_masking', 'out_prefix', 'smoothed_files'))\n",
                "        self.node_position = {\n",
                "            'smooth_1': (-119.0, -73.0),\n",
                "            'inputs': (-373.26518439966446, -73.0),\n",
                "            'outputs': (227.03404291855725, -73.0),\n",
                "        }\n",
                "        self.node_dimension = {\n",
                "            'smooth_1': (221.046875, 215.0),\n",
                "            'inputs': (137.3125, 161.0),\n",
                "            'outputs': (111.25867003946317, 61.0),\n",
                "        }\n",
                "        self.do_autoexport_nodes_parameters = False\n",
            ]
        )
        unit_test.close()

        # Makes a file "mock_file_path" in the temporary projects path
        mock_file_path = os.path.join(new_proj_path, "mock_file")
        mock_file = open(mock_file_path, "w")
        mock_file.close()

        # Opens again the package library pop-up
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library

        # Opens the "installation processes" (from folder) pop up
        folder_btn = (
            pkg_lib_window.layout()
            .children()[0]
            .layout()
            .itemAt(1)
            .itemAt(3)
            .widget()
        )
        folder_btn.clicked.emit()

        # Sets the folder to a non-existent file path
        (
            pkg_lib_window.pop_up_install_processes.path_edit.setText(
                mock_file_path + "_"
            )
        )

        # Clicks on "install package" button of "installation processes" pup-up
        instl_pkg_btn = (
            pkg_lib_window.pop_up_install_processes.layout()
            .children()[1]
            .itemAt(0)
            .widget()
        )
        instl_pkg_btn.clicked.emit()  # Displays an error dialog box

        # Sets the folder to an existing file path
        (
            pkg_lib_window.pop_up_install_processes.path_edit.setText(
                mock_file_path
            )
        )

        # Clicks on "install package" button of "installation processes" pup-up
        instl_pkg_btn.clicked.emit()  # Displays an error dialog box

        # Sets the folder to be a valid package
        (
            pkg_lib_window.pop_up_install_processes.path_edit.setText(
                mock_proc_fldr
            )
        )

        # Clicks on "install package" button of "installation processes" pup-up
        # Displays an error dialog box since __init__.py raise ImportError
        instl_pkg_btn.clicked.emit()

        # Make a proper '__init__.py
        init_file = open(os.path.join(mock_proc_fldr, "__init__.py"), "w")
        init_file.write("from .unit_test_1 import Unit_test_1")
        init_file.close()

        # Clicks again on "install package" button
        instl_pkg_btn.clicked.emit()

        # Closes the "installation processes" (from folder) pop up
        pkg_lib_window.pop_up_install_processes.close()

        # Apply changes, close the package library pop-up
        pkg_lib_window.ok_clicked()

        # Switches to the pipeline manager tab
        self.main_window.tabs.setCurrentIndex(2)

        # Adds the processes Rename, creates the "rename_1" node
        ppl_edt_tab.click_pos = QPoint(450, 500)
        ppl_edt_tab.add_named_process(Rename)

        # Exports the mandatory input and output plugs for "rename_1"
        ppl_edt_tab.current_node_name = "rename_1"
        ppl_edt_tab.export_unconnected_mandatory_inputs()
        ppl_edt_tab.export_all_unconnected_outputs()

        # Saves the pipeline as the package 'Unit_test_pipeline' in
        # User_processes
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "unit_test_pipeline.py",
        )

        save_pipeline(ppl, filename)
        self.main_window.pipeline_manager.updateProcessLibrary(filename)

        # Cleaning the process library in pipeline manager tab (deleting the
        # package added in this test, or old one still existing)
        self.clean_uts_packages(proc_lib_view)

    def test_package_library_dialog_del_pkg(self):
        """Creates a new project folder, opens the processes library and
        deletes a package.

        - Tests: PackageLibraryDialog

        - Mocks:
            - QMessageBox.exec
            - QMessageBox.question
        """
        PKG = "nipype.interfaces.DataGrabber"

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl_edt_tab = ppl_edt_tabs.get_current_editor()
        ppl = ppl_edt_tabs.get_current_pipeline()
        proc_lib_view = ppl_manager.processLibrary.process_library

        # Takes the initial state of nipype proc_lib_view and makes sure that
        # PKG is already installed

        init_state = self.proclibview_nipype_state(proc_lib_view)

        if init_state != "process_enabled":
            self.main_window.package_library_pop_up()
            pkg_lib_window = self.main_window.pop_up_package_library
            pkg_lib_window.line_edit.setText(PKG)
            (
                ppl_manager.processLibrary.process_library.pkg_library.is_path
            ) = False
            # Clicks on add package
            os.environ["FSLOUTPUTTYPE"] = "NIFTI"
            stdout_fileno = sys.stdout
            f = open(os.devnull, "w")
            sys.stdout = f
            pkg_lib_window.layout().children()[0].layout().children()[
                1
            ].itemAt(0).widget().clicked.emit()
            f.close()
            sys.stdout = stdout_fileno
            pkg_lib_window.ok_clicked()

        # Opens the package library pop-up
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library

        # Tries to delete PKG
        pkg_lib_window.line_edit.setText(PKG)
        pkg_lib_window.layout().children()[0].layout().children()[1].itemAt(
            2
        ).widget().clicked.emit()  # Clicks on delete package

        # Resets the previous action
        pkg_lib_window.del_list.selectAll()
        stdout_fileno = sys.stdout
        f = open(os.devnull, "w")
        sys.stdout = f
        (
            pkg_lib_window.layout()
            .children()[0]
            .layout()
            .itemAt(12)
            .widget()
            .layout()
            .itemAt(1)
            .widget()
            .clicked.emit()
        )  # clicks on Reset
        f.close()
        sys.stdout = stdout_fileno

        # Tries to delete again PKG
        pkg_lib_window.layout().children()[0].layout().children()[1].itemAt(
            2
        ).widget().clicked.emit()  # Clicks on delete package

        # Close the package library pop-up
        QMessageBox.question = Mock(return_value=QMessageBox.No)
        stdout_fileno = sys.stdout
        f = open(os.devnull, "w")
        sys.stdout = f
        pkg_lib_window.ok_clicked()  # Do not apply the modification
        f.close()
        sys.stdout = stdout_fileno

        # Opens again the package library pop-up
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library

        # Tries to delete PKG
        pkg_lib_window.line_edit.setText(PKG)
        pkg_lib_window.layout().children()[0].layout().children()[1].itemAt(
            2
        ).widget().clicked.emit()  # Clicks on delete package

        # Close the package library pop-up, apply changes for a package which
        # is part of nipype, the package is only removed.
        QMessageBox.question = Mock(return_value=QMessageBox.Yes)
        pkg_lib_window.ok_clicked()
        pkg_lib_window.msg.close()  # Closes the warning message

        # Add again PKG
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library
        pkg_lib_window.line_edit.setText(PKG)
        stdout_fileno = sys.stdout
        f = open(os.devnull, "w")
        sys.stdout = f
        pkg_lib_window.layout().children()[0].layout().children()[1].itemAt(
            0
        ).widget().clicked.emit()  # Clicks on add package
        f.close()
        sys.stdout = stdout_fileno
        pkg_lib_window.ok_clicked()

        # Switches to the pipeline manager tab
        self.main_window.tabs.setCurrentIndex(2)

        # Selects the 'DataGrabber' package in Pipeline Manager tab
        pkg_index = self.find_item_by_data(proc_lib_view, "DataGrabber")
        (
            proc_lib_view.selectionModel().select(
                pkg_index, QItemSelectionModel.SelectCurrent
            )
        )

        # Tries to delete a package that cannot be deleted (is part of nipype),
        # selecting it and pressing the del key
        event = Mock()
        event.key = lambda: Qt.Key_Delete
        proc_lib_view.keyPressEvent(event)
        proc_lib_view.pkg_library.msg.close()

        # Tries to delete a package that cannot be deleted, calling the
        # function
        pkg_lib_window.delete_package()
        pkg_lib_window.msg.close()  # Closes the warning message

        # Tries to delete a package corresponding to an empty string
        pkg_lib_window.line_edit.setText("")
        pkg_lib_window.delete_package()
        pkg_lib_window.msg.close()  # Closes the warning message

        # Adds the processes Rename, creates the "rename_1" node
        ppl_edt_tab.click_pos = QPoint(450, 500)
        ppl_edt_tab.add_named_process(Rename)

        # Exports the mandatory input and output plugs for "rename_1"
        ppl_edt_tab.current_node_name = "rename_1"
        ppl_edt_tab.export_unconnected_mandatory_inputs()
        ppl_edt_tab.export_all_unconnected_outputs()

        # Saves the pipeline as the package 'Unit_test_pipeline' in
        # User_processes
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "unit_test_pipeline.py",
        )
        save_pipeline(ppl, filename)
        self.main_window.pipeline_manager.updateProcessLibrary(filename)

        # Makes a mocked process folder "Mock_process" in the temporary
        # project path
        mock_proc_fldr = os.path.join(
            new_proj_path, "processes", "UTs_processes"
        )
        os.makedirs(mock_proc_fldr, exist_ok=True)

        if os.path.exists(
            os.path.join(
                config.get_properties_path(),
                "processes",
                "User_processes",
                "unit_test_pipeline.py",
            )
        ):
            shutil.copy(
                os.path.join(
                    config.get_properties_path(),
                    "processes",
                    "User_processes",
                    "unit_test_pipeline.py",
                ),
                os.path.join(mock_proc_fldr, "unit_test_2.py"),
            )

            with open(os.path.join(mock_proc_fldr, "unit_test_2.py")) as file:
                filedata = file.read()
                filedata = filedata.replace(
                    "Unit_test_pipeline", "Unit_test_2"
                )

            with open(
                os.path.join(mock_proc_fldr, "unit_test_2.py"), "w"
            ) as file:
                file.write(filedata)

            init_file = open(os.path.join(mock_proc_fldr, "__init__.py"), "w")
            init_file.write("from .unit_test_2 import Unit_test_2")
            init_file.close()

        # Imports the UTs_processes processes folder as a package
        pkg_lib_window.install_processes_pop_up()
        pkg_lib_window.pop_up_install_processes.path_edit.setText(
            mock_proc_fldr
        )
        QMessageBox.exec = lambda x: QMessageBox.Ok
        (
            pkg_lib_window.pop_up_install_processes.layout()
            .children()[-1]
            .itemAt(0)
            .widget()
            .clicked.emit()
        )
        pkg_lib_window.pop_up_install_processes.close()
        pkg_lib_window.ok_clicked()

        # Gets the 'Unit_test_2' index and selects it
        test_ppl_index = self.find_item_by_data(proc_lib_view, "Unit_test_2")
        (
            proc_lib_view.selectionModel().select(
                test_ppl_index, QItemSelectionModel.SelectCurrent
            )
        )

        # Tries to delete the package 'Unit_test_2', rejects the
        # dialog box
        QMessageBox.question = Mock(return_value=QMessageBox.No)
        proc_lib_view.keyPressEvent(event)

        # Effectively deletes the package 'Unit_test_2', accepting the
        # dialog box
        QMessageBox.question = Mock(return_value=QMessageBox.Yes)
        proc_lib_view.keyPressEvent(event)

        # Resets the process library to its original state for nipype
        cur_state = self.proclibview_nipype_state(proc_lib_view)

        if cur_state != init_state:
            self.proclibview_nipype_reset_state(
                self.main_window, ppl_manager, init_state
            )

        # Cleaning the process library in pipeline manager tab (deleting the
        # package added in this test, or old one still existing)
        self.clean_uts_packages(proc_lib_view)

    def test_package_library_dialog_rmv_pkg(self):
        """Creates a new project folder, opens the processes library and
        removes a package. Also saves the current configuration.

        - Tests: PackageLibraryDialog

        - Mocks:
            - QMessageBox.exec
            - QMessageBox.exec_
        """

        PKG = "nipype.interfaces.DataGrabber"

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        proc_lib_view = ppl_manager.processLibrary.process_library

        # Takes the initial state of nipype proc_lib_view and makes sure that
        # PKG is already installed
        init_state = self.proclibview_nipype_state(proc_lib_view)

        if init_state != "process_enabled":
            self.main_window.package_library_pop_up()
            pkg_lib_window = self.main_window.pop_up_package_library
            pkg_lib_window.line_edit.setText(PKG)
            (
                ppl_manager.processLibrary.process_library.pkg_library.is_path
            ) = False
            # Clicks on add package
            pkg_lib_window.layout().children()[0].layout().children()[
                1
            ].itemAt(0).widget().clicked.emit()
            pkg_lib_window.ok_clicked()

        # Opens the package library pop-up
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library

        # Mocks the execution of a dialog box
        QMessageBox.exec = lambda x: None
        QMessageBox.exec_ = lambda x: None

        # Mocks deleting a package that is not specified
        res = pkg_lib_window.remove_package("")
        self.assertFalse(res)

        # Tries removing a non-existent package
        res = pkg_lib_window.remove_package("non_existent_package")
        self.assertFalse(res)

        # Clicks on the remove package button without selecting package
        rmv_pkg_button = (
            pkg_lib_window.layout()
            .children()[0]
            .layout()
            .children()[1]
            .itemAt(1)
            .widget()
        )
        rmv_pkg_button.clicked.emit()

        # Writes the name of an existing package on the line edit and clicks on
        # the remove package button
        pkg_lib_window.line_edit.setText(PKG)
        rmv_pkg_button.clicked.emit()

        # Resets the previous action
        pkg_lib_window.remove_list.selectAll()
        (
            pkg_lib_window.layout()
            .children()[0]
            .layout()
            .itemAt(10)
            .widget()
            .layout()
            .itemAt(1)
            .widget()
            .clicked.emit()
        )

        # Click again on the remove package button
        rmv_pkg_button.clicked.emit()

        # Apply changes
        pkg_lib_window.ok_clicked()

        # Mocks removing a package with text and from the tree
        pkg_lib_window.remove_dic[PKG] = 1
        pkg_lib_window.add_dic[PKG] = 1
        pkg_lib_window.delete_dic[PKG] = 1
        pkg_lib_window.remove_package_with_text(
            package_name=PKG, tree_remove=False
        )

        # Resets the process library to its original state for nipype
        cur_state = self.proclibview_nipype_state(proc_lib_view)

        if cur_state != init_state:
            self.proclibview_nipype_reset_state(
                self.main_window, ppl_manager, init_state
            )

        # Saves the config to 'process_config.yml'
        ppl_manager.processLibrary.pkg_library.save()

    def test_package_library_others(self):
        """Creates a new project folder, opens the processes library and
        adds a package.

        The package library object opens up as a pop-up when
        File > Package library manager is clicked.

        - Tests: PackageLibraryDialog
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Opens the package library pop-up
        self.main_window.package_library_pop_up()

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        pkg_lib = ppl_manager.processLibrary.pkg_library.package_library
        pkg_lib_window = self.main_window.pop_up_package_library

        # Mocks the package tree
        mock_pkg_tree = [
            {"Double_rename": "process_enabled"},
            [{"Double_rename": "process_enabled"}],
            ({"Double_rename": "process_enabled"}),
        ]

        # Mocks filling an item with the above item
        pkg_lib.fill_item(pkg_lib.invisibleRootItem(), mock_pkg_tree)

        # Closes the package library pop-up
        pkg_lib_window.close()

    def test_popUpDeletedProject(self):
        """Adds a deleted projects to the projects list and launches mia.

        - Tests: PopUpDeletedProject.
        """

        # Sets a projects save directory
        # config = Config()
        config = Config(properties_path=self.properties_path)
        projects_save_path = os.path.join(self.properties_path, "projects")
        config.set_projects_save_path(projects_save_path)

        # Mocks a project filepath that does not exist in the filesystem
        # Adds this filepath to 'saved_projects.yml'
        savedProjects = SavedProjects()
        del_prjct = os.path.join(projects_save_path, "missing_project")
        savedProjects.addSavedProject(del_prjct)

        # Asserts that 'saved_projects.yml' contains the filepath
        # FIXME: The following line does not seem to be supported by the
        #        appveyor version, while it works fine on my station...
        #        For now I comment ...
        # self.assertIn(del_prjct, savedProjects.loadSavedProjects()['paths'])

        # Mocks the execution of a dialog box
        PopUpDeletedProject.exec = Mock()

        # Adds code from the 'main.py', gets deleted projects
        saved_projects_object = SavedProjects()
        saved_projects_list = copy.deepcopy(saved_projects_object.pathsList)
        deleted_projects = []
        for saved_project in saved_projects_list:
            if not os.path.isdir(saved_project):
                deleted_projects.append(os.path.abspath(saved_project))
                saved_projects_object.removeSavedProject(saved_project)

        if deleted_projects is not None and deleted_projects:
            self.msg = PopUpDeletedProject(deleted_projects)

        # Asserts that 'saved_projects.yml' no longer contains it
        # FIXME: Since the previous FIXME, and comment, the following line is
        #        also commented
        # self.assertNotIn(del_prjct,
        #                  savedProjects.loadSavedProjects()['paths'])

    def test_popUpDeleteProject(self):
        """Creates a new project and deletes it.

        Not to be confused with test_PopUpDeletedProject!

        - Tests:
            - MainWindow.delete_project
            - PopUpDeleteProject.
        """

        # Gets a new project
        test_proj_path = self.get_new_test_project()
        self.main_window.switch_project(test_proj_path, "test_project")

        # Instead of executing the pop-up, only shows it
        # This avoids thread deadlocking
        QMessageBox.exec = lambda self_: self_.show()

        # Resets the projects folder
        Config(properties_path=self.properties_path).set_projects_save_path("")

        # Tries to delete a project without setting the projects folder
        self.main_window.delete_project()
        self.main_window.msg.accept()

        # Sets a projects save directory
        config = Config(properties_path=self.properties_path)
        proj_save_path = os.path.split(test_proj_path)[0]
        config.set_projects_save_path(proj_save_path)

        # Append 'test_proj_path' to 'saved_projects.pathsList' and
        # 'opened_projects', to increase coverage
        self.main_window.saved_projects.pathsList.append(
            os.path.relpath(test_proj_path)
        )
        config.set_opened_projects([os.path.relpath(test_proj_path)])

        # PopUpDeleteProject.exec = lambda self_: self_.show()
        PopUpDeleteProject.exec = lambda self_: None

        # Deletes a project with the projects folder set
        self.main_window.delete_project()

        exPopup = self.main_window.exPopup

        # Checks the first project to be deleted
        exPopup.check_boxes[0].setChecked(True)

        # Mocks the dialog box to directly return 'YesToAll'
        QMessageBox.warning = Mock(return_value=QMessageBox.YesToAll)
        exPopup.ok_clicked()

    def test_see_all_projects(self):
        """
        Creates 2 projects and tries to open them through the
        all projects pop-up.

        - Tests:
            - MainWindow.see_all_projects
            - PopUpSeeAllProjects

        - Mocks:
            - PopUpSeeAllProjects.exec
            - QMessageBox.exec
        """

        # Sets shortcuts for objects that are often used
        main_wnd = self.main_window

        # Creates 2 new project folders
        project_8_path = self.get_new_test_project(name="project_8")
        project_9_path = self.get_new_test_project(name="project_9")

        # Sets the projects save path
        config = Config(properties_path=self.properties_path)
        config.set_projects_save_path(self.properties_path)

        # Adds the projects to the 'pathsList'
        main_wnd.saved_projects.pathsList.append(project_8_path)
        main_wnd.saved_projects.pathsList.append(project_9_path)

        # Mocks the execution of 'PopUpSeeAllProjects' and 'QMessageBox'
        PopUpSeeAllProjects.exec = lambda x: None
        QMessageBox.exec = lambda x: None

        # Deletes the folder containing the project 9
        shutil.rmtree(project_9_path)

        # Show the projects pop-up
        main_wnd.see_all_projects()

        item_0 = self.main_window.exPopup.treeWidget.itemAt(0, 0)
        self.assertEqual(item_0.text(0), "project_8")
        self.assertEqual(
            main_wnd.exPopup.treeWidget.itemBelow(item_0).text(0), "project_9"
        )

        # Asserts that project 8 is not opened:
        config = Config(properties_path=self.properties_path)
        self.assertNotEqual(
            os.path.abspath(config.get_opened_projects()[0]), project_8_path
        )

        # Tries to open a project with no projects selected
        main_wnd.exPopup.open_project()

        # Selects project 8, which was not deleted
        item_0.setSelected(True)

        # Opens project 8
        main_wnd.exPopup.open_project()

        # Asserts that project 8 is now opened
        config = Config(properties_path=self.properties_path)
        self.assertEqual(
            os.path.abspath(config.get_opened_projects()[0]), project_8_path
        )

    def test_software_preferences_pop_up(self):
        """Opens the preferences pop up and changes parameters.

        - Tests:
            - MainWindow.software_preferences_pop_up
            - PopUpPreferences

        - Mocks
            - QFileDialog.getOpenFileName
            - QFileDialog.getExistingDirectory
            - QLineEdit.text
            - QDialog.exec
            - QMessageBox.exec
            - QPlainTextEdit.toPlainText
        """

        # Sets shortcuts for objects that are often used
        main_wnd = self.main_window
        ppl_manager = main_wnd.pipeline_manager

        # Creates a new project folder and adds one document to the project
        project_8_path = self.get_new_test_project()
        ppl_manager.project.folder = project_8_path

        # Modification of some configuration parameters
        config = Config(properties_path=self.properties_path)
        config.setControlV1(True)
        config.setAutoSave(True)
        config.set_clinical_mode(True)
        config.set_use_fsl(True)
        config.set_use_afni(True)
        config.set_use_ants(True)
        config.set_use_mrtrix(True)
        config.set_mainwindow_size([100, 100, 100])

        # Open and close the software preferences window
        main_wnd.software_preferences_pop_up()
        main_wnd.pop_up_preferences.close()

        # Activate the V1 controller GUI and the user mode
        config.setControlV1(False)
        config.set_user_mode(True)

        # Enables Matlab MCR
        config.set_use_matlab_standalone(True)

        # Check that matlab MCR is selected
        main_wnd.software_preferences_pop_up()
        # fmt: off
        self.assertTrue(
            main_wnd.pop_up_preferences.use_matlab_standalone_checkbox.
            isChecked()
        )
        # fmt: on
        main_wnd.pop_up_preferences.close()

        # Enables Matlab
        config.set_use_matlab(True)

        # Check that matlab is selected and matlab MCR not
        main_wnd.software_preferences_pop_up()
        self.assertTrue(
            main_wnd.pop_up_preferences.use_matlab_checkbox.isChecked()
        )
        # fmt: off
        self.assertFalse(
            main_wnd.pop_up_preferences.use_matlab_standalone_checkbox.
            isChecked()
        )
        # fmt: on
        main_wnd.pop_up_preferences.close()

        # Enables SPM
        config.set_use_spm(True)

        # Check that SPM and matlab are selected
        main_wnd.software_preferences_pop_up()
        self.assertTrue(
            main_wnd.pop_up_preferences.use_matlab_checkbox.isChecked()
        )
        self.assertTrue(
            main_wnd.pop_up_preferences.use_spm_checkbox.isChecked()
        )
        main_wnd.pop_up_preferences.close()

        # Enables SPM standalone
        config.set_use_spm_standalone(True)

        # Check that SPM standalone and matlab MCR are selected,
        # SPM and matlab not
        main_wnd.software_preferences_pop_up()
        if "Windows" not in platform.architecture()[1]:
            # fmt: off
            self.assertTrue(
                main_wnd.pop_up_preferences.use_matlab_standalone_checkbox.
                isChecked()
            )
            self.assertTrue(
                main_wnd.pop_up_preferences.use_spm_standalone_checkbox.
                isChecked()
            )
            # fmt: on
            self.assertFalse(
                main_wnd.pop_up_preferences.use_matlab_checkbox.isChecked()
            )
            self.assertFalse(
                main_wnd.pop_up_preferences.use_spm_checkbox.isChecked()
            )
        main_wnd.pop_up_preferences.close()

        # Mocks 'QFileDialog.getOpenFileName' (returns an existing file)
        # This method returns a tuple (filename, file_types), where file_types
        # is the allowed file type (eg. 'All Files (*)')
        mock_path = os.path.split(project_8_path)[0]
        QFileDialog.getOpenFileName = lambda x, y, z: (mock_path,)

        # Mocks 'QFileDialog.getExistingDirectory'
        QFileDialog.getExistingDirectory = lambda x, y, z: mock_path

        # Open the software preferences window
        main_wnd.software_preferences_pop_up()

        # Browses the FSL path
        main_wnd.pop_up_preferences.browse_fsl()
        self.assertEqual(
            main_wnd.pop_up_preferences.fsl_choice.text(), mock_path
        )

        # Browses the AFNI path
        main_wnd.pop_up_preferences.browse_afni()
        self.assertEqual(
            main_wnd.pop_up_preferences.afni_choice.text(), mock_path
        )

        # Browses the ANTS path
        main_wnd.pop_up_preferences.browse_ants()
        self.assertEqual(
            main_wnd.pop_up_preferences.ants_choice.text(), mock_path
        )

        # Browses the mrtrix path
        main_wnd.pop_up_preferences.browse_mrtrix()
        self.assertEqual(
            main_wnd.pop_up_preferences.mrtrix_choice.text(), mock_path
        )

        # Browses the MATLAB path
        main_wnd.pop_up_preferences.browse_matlab()
        self.assertEqual(
            main_wnd.pop_up_preferences.matlab_choice.text(), mock_path
        )

        # Browses the MATLAB MCR path
        main_wnd.pop_up_preferences.browse_matlab_standalone()
        self.assertEqual(
            main_wnd.pop_up_preferences.matlab_standalone_choice.text(),
            mock_path,
        )

        # Browses the SPM path
        main_wnd.pop_up_preferences.browse_spm()
        self.assertEqual(
            main_wnd.pop_up_preferences.spm_choice.text(), mock_path
        )

        # Browses the SPM Standalone path
        main_wnd.pop_up_preferences.browse_spm_standalone()
        self.assertEqual(
            main_wnd.pop_up_preferences.spm_standalone_choice.text(), mock_path
        )

        # Browses the MriConv path
        main_wnd.pop_up_preferences.browse_mri_conv_path()
        self.assertEqual(
            main_wnd.pop_up_preferences.mri_conv_path_line_edit.text(),
            mock_path,
        )

        # Browser the projects save path
        main_wnd.pop_up_preferences.browse_projects_save_path()
        self.assertEqual(
            main_wnd.pop_up_preferences.projects_save_path_line_edit.text(),
            mock_path,
        )

        # Sets the admin password to be 'mock_admin_password'
        admin_password = "mock_admin_password"
        old_psswd = main_wnd.pop_up_preferences.salt + admin_password
        hash_psswd = sha256(old_psswd.encode()).hexdigest()
        config.set_admin_hash(hash_psswd)

        # Calls 'admin_mode_switch' without checking the box
        main_wnd.pop_up_preferences.admin_mode_switch()

        # Calls 'admin_mode_switch', mocking the execution of 'QInputDialog'
        main_wnd.pop_up_preferences.admin_mode_checkbox.setChecked(True)
        QInputDialog.getText = lambda w, x, y, z: (None, False)
        main_wnd.pop_up_preferences.admin_mode_switch()

        # Tries to activate admin mode with the wrong password
        main_wnd.pop_up_preferences.admin_mode_checkbox.setChecked(True)
        QInputDialog.getText = lambda w, x, y, z: (
            "mock_wrong_password",
            True,
        )
        main_wnd.pop_up_preferences.admin_mode_switch()
        self.assertFalse(main_wnd.pop_up_preferences.change_psswd.isVisible())

        # Activates admin mode with the correct password
        QInputDialog.getText = lambda w, x, y, z: (admin_password, True)
        main_wnd.pop_up_preferences.admin_mode_checkbox.setChecked(True)
        main_wnd.pop_up_preferences.admin_mode_switch()
        self.assertTrue(main_wnd.pop_up_preferences.change_psswd.isVisible())

        # Mocks the old passwd text field to be 'mock_admin_password'
        # (and the other textfields too!)
        # QLineEdit.text = lambda x: admin_password

        # Changes the admin password
        QDialog.exec = lambda x: False
        main_wnd.pop_up_preferences.change_admin_psswd("")
        # QDialog.exec = lambda x: True
        # main_wnd.pop_up_preferences.change_admin_psswd('')

        # Shows a wrong path pop-up message
        main_wnd.pop_up_preferences.wrong_path(
            "/mock_path", "mock_tool", extra_mess="mock_msg"
        )
        self.assertTrue(hasattr(main_wnd.pop_up_preferences, "msg"))
        self.assertEqual(
            main_wnd.pop_up_preferences.msg.icon(), QMessageBox.Critical
        )
        main_wnd.pop_up_preferences.msg.close()

        # Sets the main window size
        main_wnd.pop_up_preferences.use_current_mainwindow_size()

        # Mocks the click of the OK button on 'QMessageBox.exec'
        QMessageBox.exec = lambda x: QMessageBox.Yes

        # Programs the controller version to change to V1
        main_wnd.pop_up_preferences.control_checkbox_toggled()
        main_wnd.pop_up_preferences.control_checkbox_changed = True
        self.assertTrue(main_wnd.get_controller_version())

        # Cancels the above change
        main_wnd.pop_up_preferences.control_checkbox_toggled()
        self.assertFalse(main_wnd.get_controller_version())

        # Edits the Capsul config file
        # QDialog.exec = lambda x: False
        # capsul_engine.load = lambda x: True
        # main_wnd.pop_up_preferences.edit_capsul_config()

        # Mocks an exception in the QDialog execution
        # exc_1 = lambda x: (_ for _ in ()).throw(Exception('mock exception'))
        # QDialog.exec = exc_1
        # main_wnd.pop_up_preferences.edit_capsul_config()

        # Mocks an exception in the 'set_capsul_config' call
        # QDialog.exec = lambda x: True
        # exc_2 = lambda x, y: (_ for _ in ()).throw(Exception(
        #                                            'mock exception'))
        # Config.set_capsul_config = exc_2
        # main_wnd.pop_up_preferences.edit_capsul_config()
        # FIXME: failing in MacOS build

        # Close the software preferences window
        main_wnd.pop_up_preferences.close()

        # Return certain parameters to their default configuration values
        config.set_use_spm_standalone(True)
        config.set_use_spm(False)
        config.set_use_matlab(False)
        config.set_use_matlab_standalone(False)
        config.set_use_fsl(False)
        config.set_use_afni(False)
        config.set_use_ants(False)
        config.set_use_mrtrix(False)

    def test_software_preferences_pop_up_config_file(self):
        """Opens the preferences pop up and changes parameters to edit the
        config file and capsul config file.

        -Tests:
            - PopUpPreferences.edit_config_file
            - PopUpPreferences.findChar
            - PopUpPreferences.edit_capsul_config

        - Mocks
            - Config.set_capsul_config
            - QDialog.exec
            - SettingsEditor.update_gui
        """

        # Sets shortcuts for objects that are often used
        main_wnd = self.main_window

        # Mocks the execution of 'PopUpPreferences' to speed up the test
        # PopUpPreferences.show = lambda x: None

        main_wnd.software_preferences_pop_up()

        # Tries to edit the config file, mocks failure in 'QDialog.exec'
        QDialog.exec = lambda x: False
        main_wnd.pop_up_preferences.edit_config_file()
        self.assertTrue(hasattr(main_wnd.pop_up_preferences, "editConf"))

        # Mocks the execution to change 'user_mode' from 'false' to 'true'
        def mock_exec(x):
            """blabla"""
            config_file = (
                main_wnd.pop_up_preferences.editConf.txt.toPlainText()
            )
            config_file = config_file.replace(
                "user_mode: false", "user_mode: true"
            )
            main_wnd.pop_up_preferences.editConf.txt.setPlainText(config_file)
            return True

        QDialog.exec = mock_exec

        # Asserts that the 'Config' object was updated
        main_wnd.pop_up_preferences.edit_config_file()
        config = Config(properties_path=self.properties_path)
        self.assertTrue(config.get_user_mode())

        # Tries to find an empty string of characters in the config file
        main_wnd.pop_up_preferences.findChar()

        # Highlights the string 'user_mode' in the config file
        main_wnd.pop_up_preferences.findChar_line_edit.setText("user_mode")
        main_wnd.pop_up_preferences.findChar()

        # Mocks the execution of a 'capsul' method
        SettingsEditor.update_gui = lambda x: None
        # This fixes the Mac OS build

        # Mocks the execution of a 'QDialog'
        QDialog.exec = lambda x: True
        main_wnd.pop_up_preferences.edit_capsul_config()

        Config.set_capsul_config = lambda x, y: (_ for _ in ()).throw(
            Exception("mock_except")
        )
        main_wnd.pop_up_preferences.edit_capsul_config()

        QDialog.exec = lambda x: (_ for _ in ()).throw(
            Exception("mock_except")
        )
        main_wnd.pop_up_preferences.edit_capsul_config()

        QDialog.exec = lambda x: False
        main_wnd.pop_up_preferences.edit_capsul_config()

        main_wnd.pop_up_preferences.close()

    def test_software_preferences_pop_up_modules_config(self):
        """Opens the preferences pop up and sets the configuration of modules.

        For AFNI, ANTS, FSL, SPM, mrtrix and MATLAB.

        -Tests: PopUpPreferences.validate_and_save

        - Mocks:
            - PopUpPreferences.show
            - QMessageBox.show
            - QLineEdit.text
            - QDialog.exec
            - QMessageBox.exec
            - QPlainTextEdit.toPlainText
        """

        # Sets shortcuts for objects that are often used
        main_wnd = self.main_window

        # Mocks the execution of 'PopUpPreferences' to speed up the test
        # PopUpPreferences.show = lambda x: None

        # Mocks 'QMessageBox.show'
        QMessageBox.show = lambda x: None

        tmp_path = self.properties_path

        # Temporary solution that allows test only on Linux and MacOS
        if platform.system() == "Windows":
            return

        # Mocks executables to be used as the afni, ants, mrtrix, fslm, matlab
        # and spm cmds
        def mock_executable(
            exc_dir,
            exc_name,
            failing=False,
            output="mock executable",
            err_msg="mock_error",
        ):
            """Creates a working or failing mocked executable, optionally
            setting the output and error messages,
            """

            system = platform.system()

            if system == "Linux":
                exc_content = f'#!/bin/bash\necho "{output}"'
                if failing:
                    exc_content += f'\necho "{err_msg}" 1>&2\nexit 1'
                exc_path = os.path.join(exc_dir, exc_name)
                exc = open(exc_path, "w")
                exc.write(exc_content)
                exc.close()
                subprocess.run(["chmod", "+x", exc_path])

            elif system == "Darwin":
                exc_content = '#!/usr/bin/env bash\necho "mock executable"'
                if failing:
                    exc_content += f'\necho "{err_msg}" 1>&2\nexit 1'
                exc_path = os.path.join(exc_dir, exc_name)
                exc = open(exc_path, "w")
                exc.write(exc_content)
                exc.close()
                subprocess.run(["chmod", "+x", exc_path])

            elif system == "Windows":
                pass
                # TODO: build mocked executable for Windows

        # Segment module testing into functions to improve readability
        # of the code

        def test_afni_config():
            """Tests the AFNI configuration."""

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Enables AFNI
            main_wnd.pop_up_preferences.use_afni_checkbox.setChecked(True)

            # Sets a directory that does not exist
            (
                main_wnd.pop_up_preferences.afni_choice.setText(
                    os.path.join(tmp_path + "mock")
                )
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Sets a directory that does not contain the AFNI cmd
            main_wnd.pop_up_preferences.afni_choice.setText(tmp_path)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Asserts that AFNI is disabled in the 'config' object
            config = Config(properties_path=self.properties_path)
            self.assertFalse(config.get_use_afni())

            # Sets the path to the AFNI to 'tmp_path'
            main_wnd.pop_up_preferences.afni_choice.setText(tmp_path)

            mock_executable(tmp_path, "afni", failing=True)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            mock_executable(tmp_path, "afni")
            # main_wnd.pop_up_preferences.ok_clicked()  # Closes the window
            main_wnd.pop_up_preferences.close()  # Closes the window

            # Disables AFNI
            config = Config(properties_path=self.properties_path)
            config.set_use_afni(False)
            config.set_afni_path("")

        def test_ants_config():
            """Tests the ANTS configuration."""

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Enables ANTS
            main_wnd.pop_up_preferences.use_ants_checkbox.setChecked(True)

            # Sets a directory that does not exist
            (
                main_wnd.pop_up_preferences.ants_choice.setText(
                    os.path.join(tmp_path + "mock")
                )
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Sets a directory that does not contain the ANTS cmd
            main_wnd.pop_up_preferences.ants_choice.setText(tmp_path)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Asserts that ANTS is disabled in the 'config' object
            config = Config(properties_path=self.properties_path)
            self.assertFalse(config.get_use_ants())

            # Sets the path to the AFNI to 'tmp_path'
            main_wnd.pop_up_preferences.afni_choice.setText(tmp_path)

            mock_executable(tmp_path, "SmoothImage", failing=True)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            mock_executable(tmp_path, "SmoothImage")
            # main_wnd.pop_up_preferences.ok_clicked()  # Closes the window
            main_wnd.pop_up_preferences.close()  # Closes the window

            # Disables ANTS
            config = Config(properties_path=self.properties_path)
            config.set_use_ants(False)
            config.set_ants_path("")

        def test_fsl_config():
            """Tests the FSL configuration."""

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Enables FSL
            main_wnd.pop_up_preferences.use_fsl_checkbox.setChecked(True)

            # Does not set a directory for FSL
            main_wnd.pop_up_preferences.ok_clicked()

            # Sets paths to the bin and parent directory folders
            main_wnd.pop_up_preferences.fsl_choice.setText(
                os.path.join(tmp_path, "etc", "fslconf", "bin")
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            main_wnd.pop_up_preferences.fsl_choice.setText(
                os.path.join(tmp_path, "etc", "fslconf")
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Sets a directory that does not contain the FSL cmd
            main_wnd.pop_up_preferences.fsl_choice.setText(tmp_path)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Asserts that FSL is disabled in the 'config' object
            config = Config(properties_path=self.properties_path)
            self.assertFalse(config.get_use_fsl())

            # Sets the path to the FSL to 'tmp_path'
            fsl_path = os.path.join(tmp_path, "bin")
            os.mkdir(fsl_path)
            main_wnd.pop_up_preferences.fsl_choice.setText(fsl_path)

            mock_executable(fsl_path, "flirt", failing=True)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            mock_executable(fsl_path, "flirt")
            # main_wnd.pop_up_preferences.ok_clicked()  # Closes the window
            main_wnd.pop_up_preferences.close()  # Closes the window

            # Disables FSL
            config = Config(properties_path=self.properties_path)
            config.set_use_fsl(False)
            config.set_fsl_config("")

        def test_mrtrix_config():
            """Tests the mrtrix configuration."""

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Enables mrtrix
            main_wnd.pop_up_preferences.use_mrtrix_checkbox.setChecked(True)

            # Sets a directory that does not exist
            (
                main_wnd.pop_up_preferences.mrtrix_choice.setText(
                    os.path.join(tmp_path + "mock")
                )
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Sets a directory that does not contain the mrtrix cmd
            main_wnd.pop_up_preferences.mrtrix_choice.setText(tmp_path)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Asserts that mrtrix is disabled in the 'config' object
            config = Config(properties_path=self.properties_path)
            self.assertFalse(config.get_use_mrtrix())

            # Sets the path to the mrtrix to 'tmp_path'
            main_wnd.pop_up_preferences.mrtrix_choice.setText(tmp_path)

            mock_executable(tmp_path, "mrinfo", failing=True)
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            mock_executable(tmp_path, "mrinfo")
            # main_wnd.pop_up_preferences.ok_clicked()  # Closes the window
            main_wnd.pop_up_preferences.close()  # Closes the window

            # Disables mrtrix
            config = Config(properties_path=self.properties_path)
            config.set_use_mrtrix(False)
            config.set_mrtrix_path("")

        def test_spm_matlab_config():
            """Tests the SPM and MATLAB (licence) configuration."""

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Enables SPM
            main_wnd.pop_up_preferences.use_spm_checkbox.setChecked(True)

            # Sets a MATLAB executable path that does not exists
            main_wnd.pop_up_preferences.matlab_choice.setText(
                os.path.join(tmp_path, "matlab")
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Creates a failing MATLAB executable
            mock_executable(tmp_path, "matlab", failing=True)

            # Sets the same MATLAB directory in the preferences window and
            # in the config object
            config = Config(properties_path=self.properties_path)
            config.set_matlab_path(os.path.join(tmp_path, "matlab"))
            # main_wnd.pop_up_preferences.ok_clicked() # Opens error dialog

            # Also sets the same SPM directory in the preferences window and
            # in the config object, and a 'tmp_path' as the MATLAB directory
            config = Config(properties_path=self.properties_path)
            config.set_spm_path(tmp_path)
            main_wnd.pop_up_preferences.spm_choice.setText(tmp_path)
            main_wnd.pop_up_preferences.ok_clicked()  # Closes the window

            config = Config(properties_path=self.properties_path)
            self.assertTrue(config.get_use_spm())
            self.assertTrue(config.get_use_matlab())
            self.assertFalse(config.get_use_matlab_standalone())
            # Case where both MATLAB and SPM applications are used

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Resets the MATLAB executable path
            Config(properties_path=self.properties_path).set_matlab_path("")
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Creates a working MATLAB executable
            mock_executable(tmp_path, "matlab")
            main_wnd.pop_up_preferences.ok_clicked()  # Closes the window

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Restricts the permission on the MATLAB executable to induce
            # an exception on 'subprocess.Popen'
            subprocess.run(["chmod", "-x", os.path.join(tmp_path, "matlab")])

            # Resets the MATLAB executable path (which was set by the last
            # call on 'ok_clicked')
            Config(properties_path=self.properties_path).set_matlab_path("")

            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Case where SPM directory is not valid
            (
                main_wnd.pop_up_preferences.spm_choice.setText(
                    os.path.join(tmp_path, "not_existing")
                )
            )
            # main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog
            main_wnd.pop_up_preferences.close()  # Closes the window

            # Disables MATLAB and SPM
            config = Config(properties_path=self.properties_path)
            config.set_use_matlab(False)
            config.set_use_spm(False)
            config.set_spm_path("")
            config.set_matlab_path("")

        def test_matlab_config():
            """Tests the MATLAB (license) configuration."""

            main_wnd.software_preferences_pop_up()  # Reopens the window

            # Sets the projects folder for the preferences window to close
            # when pressing on 'OK'
            # fmt: off
            (
                main_wnd.pop_up_preferences.projects_save_path_line_edit.
                setText(tmp_path)
            )
            # fmt: on

            # Enables MATLAB
            main_wnd.pop_up_preferences.use_matlab_checkbox.setChecked(True)

            # Sets the same MATLAB directory on both the preferences
            # window and 'config' object
            main_wnd.pop_up_preferences.matlab_choice.setText(tmp_path)
            Config(properties_path=self.properties_path).set_matlab_path(
                tmp_path
            )

            main_wnd.pop_up_preferences.ok_clicked()  # Closes the window

            # Asserts that MATLAB and MATLAB standalone
            # remains disabled
            config = Config(properties_path=self.properties_path)
            self.assertFalse(config.get_use_matlab())
            self.assertFalse(config.get_use_matlab_standalone())

            # main_wnd.software_preferences_pop_up()  # Reopens the window

            # Resets the 'config' object
            config.set_use_matlab(False)

            # Resets the MATLAB directory
            main_wnd.pop_up_preferences.matlab_choice.setText("")
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Creates a failing MATLAB executable
            mock_executable(tmp_path, "matlab", failing=True)

            # Sets the MATLAB directory to this executable
            (
                main_wnd.pop_up_preferences.matlab_choice.setText(
                    os.path.join(tmp_path, "matlab")
                )
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Restricts the permission required to run the MATLAB
            # executable to induce an exception on 'subprocess.Popen'
            subprocess.run(["chmod", "-x", os.path.join(tmp_path, "matlab")])
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Asserts that MATLAB was still not enabled
            config = Config(properties_path=self.properties_path)
            self.assertFalse(config.get_use_matlab())

            # Creates a working MATLAB executable
            mock_executable(tmp_path, "matlab")
            main_wnd.pop_up_preferences.ok_clicked()  # Closes window
            # main_wnd.pop_up_preferences.close()  # Closes the window

            # Asserts that MATLAB was enabled and MATLAB standalone
            # remains disabled
            config = Config(properties_path=self.properties_path)
            self.assertTrue(config.get_use_matlab())
            self.assertFalse(config.get_use_matlab_standalone())

            # Disables MATLAB and SPM
            config = Config(properties_path=self.properties_path)
            config.set_use_matlab(False)
            config.set_matlab_path("")

        def test_matlab_mcr_spm_standalone():
            """Tests the Matlab MCR and SPM standalone configuration"""

            main_wnd.software_preferences_pop_up()  # Opens the window

            # Sets the projects folder for the preferences window to close
            # when pressing on 'OK'
            # fmt: off
            (
                main_wnd.pop_up_preferences.projects_save_path_line_edit.
                setText(tmp_path)
            )
            # fmt: on

            # Enables SPM standalone
            # fmt: off
            (
                main_wnd.pop_up_preferences.use_spm_standalone_checkbox.
                setChecked(True)
            )
            # fmt: on

            # Failing configurations for SPM standalone + MATLAB MCR

            # Sets a non-existing directory for MATLAB MCR
            (
                main_wnd.pop_up_preferences.matlab_standalone_choice.setText(
                    os.path.join(tmp_path, "non_existing")
                )
            )

            main_wnd.pop_up_preferences.ok_clicked()  # Opens error message

            # Sets an existing directory for MATLAB MCR, non-existing
            # directory for SPM standalone
            (
                main_wnd.pop_up_preferences.matlab_standalone_choice.setText(
                    tmp_path
                )
            )
            (
                main_wnd.pop_up_preferences.spm_standalone_choice.setText(
                    os.path.join(tmp_path, "non_existing")
                )
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Sets existing directories for both MATLAB MCR and SPM
            # standalone
            (
                main_wnd.pop_up_preferences.spm_standalone_choice.setText(
                    tmp_path
                )
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Does not find a SPM standalone executable
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Creates a failing SPM standalone executable
            mock_executable(tmp_path, "run_spm.sh", failing=True)

            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            mock_executable(
                tmp_path,
                "run_spm.sh",
                failing=True,
                err_msg="shared libraries",
            )

            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            # Restricts the permission required to run the MATLAB
            # executable to induce an exception on 'subprocess.Popen'
            subprocess.run(
                ["chmod", "-x", os.path.join(tmp_path, "run_spm.sh")]
            )
            main_wnd.pop_up_preferences.ok_clicked()  # Opens error dialog

            config = Config(properties_path=self.properties_path)
            self.assertFalse(config.get_use_spm_standalone())
            self.assertFalse(config.get_use_matlab_standalone())

            # Passing configurations for SPM standalone + MATLAB MCR

            # Creates an SPM standalone executable that throws a non-critical
            # error
            mock_executable(
                tmp_path,
                "run_spm.sh",
                failing=True,
                output="_ _ version (standalone)",
            )

            main_wnd.pop_up_preferences.ok_clicked()  # Closes window

            config = Config(properties_path=self.properties_path)
            # FIXME: the following lines makes, only with macos build:
            #        'AssertionError: False is not true'. Commented.
            # self.assertTrue(config.get_use_spm_standalone())
            # self.assertTrue(config.get_use_matlab_standalone())

            # Resets the 'config' object
            config.set_spm_standalone_path("")
            config.set_use_spm_standalone(False)
            config.set_use_matlab_standalone(False)

            main_wnd.software_preferences_pop_up()  # Opens the window
            # fmt: off
            (
                main_wnd.pop_up_preferences.use_spm_standalone_checkbox.
                setChecked(True)
            )
            # fmt: on
            main_wnd.pop_up_preferences.spm_standalone_choice.setText(tmp_path)

            mock_executable(tmp_path, "run_spm.sh")

            main_wnd.pop_up_preferences.ok_clicked()  # Closes the window

            config = Config(properties_path=self.properties_path)
            # FIXME: the following lines makes, only with macos build:
            #        'AssertionError: False is not true'. Commented.
            # self.assertTrue(config.get_use_spm_standalone())
            # self.assertTrue(config.get_use_matlab_standalone())

            # Resets the 'config' object
            config.set_use_spm_standalone(False)
            config.set_use_matlab_standalone(False)

            main_wnd.software_preferences_pop_up()  # Opens the window
            # fmt: off
            (
                main_wnd.pop_up_preferences.use_spm_standalone_checkbox.
                setChecked(True)
            )
            # fmt: on

            # The same MATLAB directory is already the same on both the
            # preferences window and 'config' object, same for SPM
            # standalone
            main_wnd.pop_up_preferences.ok_clicked()  # Closes the window

            config = Config(properties_path=self.properties_path)
            # FIXME: the following lines makes, only with macos build:
            #        'AssertionError: False is not true'. Commented.
            # self.assertTrue(config.get_use_spm_standalone())
            # self.assertTrue(config.get_use_matlab_standalone())

        Config(properties_path=self.properties_path).set_projects_save_path(
            tmp_path
        )

        # Test the configuration modules AFNI, ANTS, FSL, mrtrix,
        # SPM and MATLAB
        test_afni_config()
        test_ants_config()
        test_mrtrix_config()
        test_fsl_config()
        test_spm_matlab_config()
        test_matlab_config()
        test_matlab_mcr_spm_standalone()

    def test_software_preferences_pop_up_validate(self):
        """Opens the preferences pop up, sets the configuration.

        For modules AFNI, ANTS, FSL, SPM, mrtrix and MATLAB without pressing
        the OK button and switches the auto-save, controller version and
        radio view options.

        - Tests: PopUpPreferences.validate_and_save

        - Mocks:
            - PopUpPreferences.show
            - QMessageBox.show
        """

        # Validates the Pipeline tab without pressing the 'OK' button:

        # Set shortcuts for objects that are often used
        main_wnd = self.main_window

        # Mocks the execution of 'PopUpPreferences' to speed up the test
        # PopUpPreferences.show = lambda x: None

        tmp_path = self.properties_path
        main_wnd.software_preferences_pop_up()

        # Selects standalone modules
        for module in ["matlab_standalone", "spm_standalone"]:
            getattr(
                main_wnd.pop_up_preferences, "use_" + module + "_checkbox"
            ).setChecked(True)

        # Validates the Pipeline tab without pressing the 'OK' button
        main_wnd.pop_up_preferences.validate_and_save()

        config = Config(properties_path=self.properties_path)
        for module in ["matlab_standalone", "spm_standalone"]:
            self.assertTrue(getattr(config, "get_use_" + module)())

        # Selects non standalone modules
        for module in ["afni", "ants", "fsl", "matlab", "mrtrix", "spm"]:
            getattr(
                main_wnd.pop_up_preferences, "use_" + module + "_checkbox"
            ).setChecked(True)

        # Validates the Pipeline tab without pressing the 'OK' button
        main_wnd.pop_up_preferences.validate_and_save()

        config = Config(properties_path=self.properties_path)
        for module in ["afni", "ants", "fsl", "matlab", "mrtrix", "spm"]:
            self.assertTrue(getattr(config, "get_use_" + module)())

        # Validates the Pipeline tab by pressing the 'OK' button:

        # Sets the projects folder for the preferences window to close
        # when pressing on 'OK'
        (
            main_wnd.pop_up_preferences.projects_save_path_line_edit.setText(
                tmp_path
            )
        )

        # Mocks the execution of 'wrong_path' and 'QMessageBox.show'
        main_wnd.pop_up_preferences.wrong_path = lambda x, y: None
        QMessageBox.show = lambda x: None

        # Deselects non standalone modules
        for module in ["afni", "ants", "fsl", "matlab", "mrtrix", "spm"]:
            getattr(
                main_wnd.pop_up_preferences, "use_" + module + "_checkbox"
            ).setChecked(False)

        # Deselects the 'radioView', 'adminMode' and 'clinicalMode' option
        for opt in ["save", "radioView", "admin_mode", "clinical_mode"]:
            (
                getattr(
                    main_wnd.pop_up_preferences, opt + "_checkbox"
                ).setChecked(False)
            )
        # The options autoSave, radioView and controlV1 are not selected

        # Sets the projects save path
        Config(properties_path=self.properties_path).set_projects_save_path(
            tmp_path
        )

        # Validates the all tab after pressing the 'OK' button
        main_wnd.pop_up_preferences.ok_clicked()

        config = Config(properties_path=self.properties_path)

        for opt in [
            "isAutoSave",
            "isRadioView",
            "isControlV1",
            "get_use_clinical",
        ]:
            self.assertFalse(getattr(config, opt)())

        self.assertTrue(config.get_user_mode())
        self.assertEqual(config.get_projects_save_path(), tmp_path)

        # Deselects MATLAB and SPM modules from the config file
        config = Config(properties_path=self.properties_path)

        for module in ["matlab", "spm"]:
            getattr(config, "set_use_" + module)(False)

        main_wnd.software_preferences_pop_up()  # Reopens the window

        # Selects the autoSave, radioView and controlV1 options
        for opt in [
            "save_checkbox",
            "radioView_checkbox",
            "control_checkbox",
            "admin_mode_checkbox",
            "clinical_mode_checkbox",
        ]:
            getattr(main_wnd.pop_up_preferences, opt).setChecked(True)

        # Alternates to minimized mode
        main_wnd.pop_up_preferences.fullscreen_cbox.setChecked(True)

        # Sets a non-existent projects save path
        Config(properties_path=self.properties_path).set_projects_save_path(
            os.path.join(tmp_path, "non_existent")
        )

        # Validates the all tab after pressing the 'OK' button
        main_wnd.pop_up_preferences.ok_clicked()

        # Asserts that the 'config' objects was not updated with the
        # non-existent projects folder
        config = Config(properties_path=self.properties_path)
        self.assertEqual(config.get_projects_save_path(), tmp_path)

    def test_switch_project(self):
        """Creates a project and switches to it.

        - Tests: MainWindow.switch_project

        - Mocks: QMessageBox.exec
        """

        # Mocks the execution of a dialog window
        QMessageBox.exec = lambda self_: None

        # Creates a new project
        test_proj_path = self.get_new_test_project()

        # Switches to an existing mia project
        res = self.main_window.switch_project(test_proj_path, "test_project")
        self.assertTrue(res)
        self.assertEqual(self.main_window.project.folder, test_proj_path)

        self.main_window.project.folder = ""  # Resets the project folder

        # Tries to switch to a non-existent project
        res = self.main_window.switch_project(
            test_proj_path + "_", "test_project"
        )
        self.assertFalse(res)
        self.assertEqual(self.main_window.project.folder, "")

        # Tries to switch to a project that is already opened in another
        # instance of the software
        res = self.main_window.switch_project(test_proj_path, "test_project")
        self.assertFalse(res)
        self.assertEqual(self.main_window.project.folder, "")

        # Resets the opened projects list
        config = Config(properties_path=self.properties_path)
        config.set_opened_projects([])

        # Deletes the 'COLLECTION_CURRENT' equivalent in 'mia.db'
        # con = sqlite3.connect(os.path.join(test_proj_path,
        #                                    'database','mia.db'))
        # cursor = con.cursor()
        # query = "DELETE FROM '_collection' WHERE collection_name = 'current'"
        # cursor.execute(query)
        # con.commit()
        # con.close()

        # Tries to switch to a project that cannot be read by mia
        # res = self.main_window.switch_project(test_proj_path, 'test_project')
        # self.assertFalse(res)

        # Deletes the 'filters' folder of the project
        subprocess.run(["rm", "-rf", os.path.join(test_proj_path, "filters")])

        # Tries to switch to non mia project
        res = self.main_window.switch_project(test_proj_path, "test_project")
        self.assertFalse(res)

    def test_tab_changed(self):
        """Switches between tabs.

        Data browser, data viewer and pipeline manager.

        Tests: MainWindow.tab_changed.

        Mocks: QMessageBox.exec.
        """

        # Creates a test project
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_proj_path, "test_project")

        # Set shortcuts for objects that are often used
        data_browser = self.main_window.data_browser

        # Switches to data viewer
        self.main_window.tabs.setCurrentIndex(1)  # Calls tab_changed()
        self.assertEqual(self.main_window.tabs.currentIndex(), 1)

        # Deletes a scan from data browser
        data_browser.table_data.selectRow(0)
        data_browser.table_data.remove_scan()

        # Mocks the execution of a dialog box by accepting it
        QMessageBox.exec = lambda self_, *arg: self_.accept()

        # Switch to pipeline manager with unsaved modifications
        self.main_window.tabs.setCurrentIndex(2)  # Calls tab_changed()
        self.assertEqual(self.main_window.tabs.currentIndex(), 2)

        # Mocks nots list
        # self.main_window.project.currentFilter.nots = ['NOT', '', '']

        # Switches to data browser
        self.main_window.tabs.setCurrentIndex(0)  # Calls tab_changed()
        self.assertEqual(self.main_window.tabs.currentIndex(), 0)


class TestMIANodeController(TestMIACase):
    """Tests for the node controller, part of the pipeline manager tab.

    - Tests: NodeController.

    :Contains:
        :Method:
            - test_attributes_filter: displays an attributes filter and
              modifies it.
            - test_capsul_node_controller: adds, changes and deletes
              processes using the capsul node controller.
            - test_display_filter: displays node parameters and a plug
              filter.
            - test_filter_widget: opens up the "FilterWidget()" to
              modify its parameters.
            - test_node_controller: adds, changes and deletes processes
              to the node controller.
            - test_plug_filter: displays a plug filter and modifies it
            - test_update_node_name: displays node parameters and
              updates its name.
    """

    def test_attributes_filter(self):
        """Displays the parameters of a node, displays an attributes filter
        and modifies it.

        - Tests: AttributesFilter in V2 controller GUI (CapsulNodeController).
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_controller = self.main_window.pipeline_manager.nodeController

        # Adds the process Smooth, creates a node called "smooth_1"
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Smooth)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the unconnected mandatory plugs
        ppl_edt_tabs.get_current_editor().current_node_name = "smooth_1"
        (
            ppl_edt_tabs.get_current_editor
        )().export_node_unconnected_mandatory_plugs()

        # Displays parameters of 'inputs' node
        input_process = pipeline.nodes[""].process
        self.main_window.pipeline_manager.displayNodeParameters(
            "inputs", input_process
        )

        # Opens the attributes filter, selects item and closes it
        node_controller.filter_attributes()
        attributes_filter = node_controller.pop_up
        attributes_filter.table_data.selectRow(0)
        attributes_filter.ok_clicked()

        # Opens the attributes filter, does not select an item and closes it
        node_controller.filter_attributes()
        attributes_filter = node_controller.pop_up
        attributes_filter.search_str("!@#")
        attributes_filter.ok_clicked()

    def test_capsul_node_controller(self):
        """
        Adds, changes and deletes processes using the capsul node controller.

        Displays the attributes filter.

        Tests: CapsulNodeController
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        with self.main_window.project.database.data() as database_data:
            DOCUMENT_1 = database_data.get_document_names(COLLECTION_CURRENT)[
                0
            ]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_ctrler = self.main_window.pipeline_manager.nodeController

        # Adds 2 processes Rename, creates 2 nodes called "rename_1" and
        # "rename_2":
        process_class = Rename
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Displays parameters of "rename_2" node
        rename_process = pipeline.nodes["rename_2"].process
        self.main_window.pipeline_manager.displayNodeParameters(
            "rename_2", rename_process
        )

        # Tries changing its name to "rename_2" and then to "rename_3"
        node_ctrler.update_node_name()
        self.assertEqual(node_ctrler.node_name, "rename_2")
        node_ctrler.update_node_name(
            new_node_name="rename_1", old_node_name="rename_2"
        )
        self.assertEqual(node_ctrler.node_name, "rename_2")
        node_ctrler.update_node_name(
            new_node_name="rename_3", old_node_name="rename_2"
        )
        self.assertEqual(node_ctrler.node_name, "rename_3")

        # Deletes node "rename_3"
        ppl_edt_tabs.get_current_editor().del_node("rename_3")

        # Display parameters of the "inputs" node
        input_process = pipeline.nodes[""].process
        node_ctrler.display_parameters(
            "inputs", get_process_instance(input_process), pipeline
        )

        # Displays parameters of "rename_1" node
        rename_process = pipeline.nodes["rename_1"].process
        self.main_window.pipeline_manager.displayNodeParameters(
            "rename_1", rename_process
        )

        # Exports plugs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "rename_1"
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        pipeline.nodes["rename_1"].set_plug_value("in_file", DOCUMENT_1)
        pipeline.nodes["rename_1"].set_plug_value(
            "format_string", "new_name.nii"
        )

        # Runs pipeline and expects an error
        # self.main_window.pipeline_manager.runPipeline()
        # FIXME: running the pipeline gives the error:
        #        ModuleNotFoundError: No module named 'capsul'

        # Displays the attributes filter
        node_ctrler.filter_attributes()
        attributes_filter = node_ctrler.pop_up
        attributes_filter.table_data.selectRow(0)
        attributes_filter.ok_clicked()

        # Releases the process
        node_ctrler.release_process()
        node_ctrler.update_parameters()

    def test_display_filter(self):
        """Displays parameters of a node and displays a plug filter."""

        config = Config(properties_path=self.properties_path)
        controlV1_ver = config.isControlV1()

        # Switch to V1 node controller GUI, if necessary
        if not controlV1_ver:
            config.setControlV1(True)
            self.restart_MIA()

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        node_controller = self.main_window.pipeline_manager.nodeController

        # Adding a process
        process_class = Threshold
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        # Creates a node called "threshold_1"
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exporting the input plugs and modifying the "synchronize" input plug
        (pipeline_editor_tabs.get_current_editor)().current_node_name = (
            "threshold_1"
        )
        (
            pipeline_editor_tabs.get_current_editor
        )().export_node_all_unconnected_inputs()

        input_process = pipeline.nodes[""].process
        node_controller.display_parameters(
            "inputs", get_process_instance(input_process), pipeline
        )

        if hasattr(node_controller, "get_index_from_plug_name"):
            index = node_controller.get_index_from_plug_name(
                "synchronize", "in"
            )
            node_controller.line_edit_input[index].setText("2")
            # This calls "update_plug_value" method
            node_controller.line_edit_input[index].returnPressed.emit()

            # Calling the display_filter method
            node_controller.display_filter(
                "inputs", "synchronize", (), input_process
            )
            node_controller.pop_up.close()
            self.assertEqual(
                2, pipeline.nodes["threshold_1"].get_plug_value("synchronize")
            )

        # Switches back to node controller V2, if necessary (return to initial
        # state)
        config = Config(properties_path=self.properties_path)

        if not controlV1_ver:
            config.setControlV1(False)

    @unittest.skip("skip this test until it has been repaired.")
    def test_filter_widget(self):
        """Places a node of the "Input_Filter" process, feeds in documents
        and opens up the "FilterWidget()" to modify its parameters.

        Tests the class FilterWidget() within the Node Controller V1
        (class NodeController()). The class FilterWidget() is
        independent on the Node
        Controller version (V1 or V2) and can be used in both of them.
        """

        config = Config(properties_path=self.properties_path)
        controlV1_ver = config.isControlV1()

        # Switch to V1 node controller GUI, if necessary
        if not controlV1_ver:
            config.setControlV1(True)
            self.restart_MIA()

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        with self.main_window.project.database.data() as database_data:
            DOCUMENT_1 = database_data.get_document_names(COLLECTION_CURRENT)[
                0
            ]
            DOCUMENT_2 = database_data.get_document_names(COLLECTION_CURRENT)[
                1
            ]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_ctrler = self.main_window.pipeline_manager.nodeController
        self.main_window.tabs.setCurrentIndex(2)

        # Adds the process "input_filter_1"
        process_class = Input_Filter
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the input plugs for "input_filter_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "input_filter_1"
        (
            ppl_edt_tabs.get_current_editor
        )().export_node_unconnected_mandatory_plugs()

        # Displays parameters of the "inputs" node
        input_process = pipeline.nodes[""].process
        node_ctrler.display_parameters(
            "inputs", get_process_instance(input_process), pipeline
        )

        # Opens a filter for the plug "input" of the "inputs" node
        parameters = (0, pipeline, type(Undefined))
        node_ctrler.display_filter(
            "inputs", "input", parameters, input_process
        )

        # Selects all records in the "input" node
        plug_filter = node_ctrler.pop_up

        plug_filter.ok_clicked()

        # Opens the filter widget for the node "input_filter_1"
        ppl_edt_tabs.open_filter("input_filter_1")
        input_filter = ppl_edt_tabs.filter_widget

        index_DOCUMENT_1 = input_filter.table_data.get_scan_row(DOCUMENT_1)
        # index_DOCUMENT_2 = input_filter.table_data.get_scan_row(DOCUMENT_2)

        # Tries to search for an empty string and asserts that none of the
        # documents are hidden
        input_filter.search_str("")

        # Test "DOCUMENT_1" is not hidden
        # FIXME: Only for the Windows version, the method isRowHidden()
        #        does not seem to give the expected result. Waiting to look at
        #        this, we comment ..
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_1))
        # Test "DOCUMENT_2" is not hidden
        # FIXME: Only for the Windows version, the method isRowHidden()
        #        does not seem to give the expected result. Waiting to look at
        #        this, we comment ..
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_2))

        # Searches for "DOCUMENT_2" and verifies that "DOCUMENT_1" is hidden
        input_filter.search_str(DOCUMENT_2)
        self.assertTrue(input_filter.table_data.isRowHidden(index_DOCUMENT_1))

        # Resets the search bar and assert that none of the documents
        # are hidden
        input_filter.reset_search_bar()

        # Test "DOCUMENT_1" is not hidden
        # FIXME: Only for the Windows version, the method isRowHidden()
        #        does not seem to give the expected result. Waiting to look at
        #        this, we comment ..
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_1))
        # Test "DOCUMENT_1" is not hidden
        # FIXME: Only for the Windows version, the method isRowHidden()
        #        does not seem to give the expected result. Waiting to look at
        #        this, we comment ..
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_2))

        # Opens the "Visualized tags" pop up and adds the "AcquisitionDate" tag
        # QTimer.singleShot(1000, lambda:self.add_visualized_tag(
        #       'AcquisitionDate'))
        input_filter.update_tags()
        self.add_visualized_tag("AcquisitionDate")
        # FIXME: The following statement is always True (not the correct test)
        self.assertTrue(
            type(input_filter.table_data.get_tag_column("AcquisitionDate"))
            == int
        )

        # Updates the tag to filter with
        # with patch.object(PopUpSelectTagCountTable, 'exec_', return_value=True):
        input_filter.update_tag_to_filter()

        input_filter.push_button_tag_filter.setText(TAG_FILENAME)
        # TODO: select tag to filter with

        # Closes the filter
        input_filter.ok_clicked()

        # Switches back to node controller V2, if necessary (return to initial
        # state)
        config = Config(properties_path=self.properties_path)

        if not controlV1_ver:
            config.setControlV1(False)

    def test_node_controller(self):
        """Adds, changes and deletes processes to the node controller,
        display the attributes filter.

        Tests the class NodeController().
        """

        config = Config(properties_path=self.properties_path)
        controlV1_ver = config.isControlV1()

        # Switch to V1 node controller GUI, if necessary
        if not controlV1_ver:
            config.setControlV1(True)
            self.restart_MIA()

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        with self.main_window.project.database.data() as database_data:
            DOCUMENT_1 = database_data.get_document_names(COLLECTION_CURRENT)[
                0
            ]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_ctrler = self.main_window.pipeline_manager.nodeController

        # Add, twice, the process Rename, creates the "rename_1" and "rename_2"
        # nodes
        process_class = Rename
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Displays parameters of "rename_2" node
        rename_process = pipeline.nodes["rename_2"].process
        self.main_window.pipeline_manager.displayNodeParameters(
            "rename_2", rename_process
        )

        # Tries to change its name to "rename_1" and then to "rename_3"
        node_ctrler.update_node_name()
        self.assertEqual(node_ctrler.node_name, "rename_2")
        node_ctrler.update_node_name(new_node_name="rename_1")
        self.assertEqual(node_ctrler.node_name, "rename_2")
        node_ctrler.update_node_name(new_node_name="rename_3")
        self.assertEqual(node_ctrler.node_name, "rename_3")

        # Deletes node "rename_2"
        ppl_edt_tabs.get_current_editor().del_node("rename_3")
        self.assertRaises(KeyError, lambda: pipeline.nodes["rename_3"])

        # Exports the input plugs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "rename_1"
        (
            ppl_edt_tabs.get_current_editor
        )().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Display parameters of the "inputs" node
        input_process = pipeline.nodes[""].process
        node_ctrler.display_parameters(
            "inputs", get_process_instance(input_process), pipeline
        )

        # Display the filter of the 'in_file' plug, "inputs" node
        node_ctrler.display_filter(
            "inputs", "in_file", (0, pipeline, type(Undefined)), input_process
        )
        node_ctrler.pop_up.close()

        # Sets the values of the mandatory plugs
        pipeline.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        pipeline.nodes[""].set_plug_value("format_string", "new_file.nii")

        # Checks the indexed of input and output plug labels
        in_plug_index = node_ctrler.get_index_from_plug_name("in_file", "in")
        self.assertEqual(in_plug_index, 1)
        out_plug_index = node_ctrler.get_index_from_plug_name(
            "_out_file", "out"
        )
        self.assertEqual(out_plug_index, 0)

        # Tries to update the plug value without a new value
        node_ctrler.update_plug_value(
            "in", "in_file", pipeline, type(Undefined)
        )
        node_ctrler.update_plug_value(
            "out", "_out_file", pipeline, type(Undefined)
        )
        node_ctrler.update_plug_value(
            None, "in_file", pipeline, type(Undefined)
        )

        # Tries to update the plug value with a new value
        node_ctrler.update_plug_value(
            "in", "in_file", pipeline, str, new_value="new_value.nii"
        )
        node_ctrler.update_plug_value(
            "out", "_out_file", pipeline, str, new_value="new_value.nii"
        )

        # Releases the process
        node_ctrler.release_process()
        node_ctrler.update_parameters()

        # Switches back to node controller V2, if necessary (return to initial
        # state)
        config = Config(properties_path=self.properties_path)

        if not controlV1_ver:
            config.setControlV1(False)

    @unittest.skip("skip this test until it has been repaired.")
    def test_plug_filter(self):
        """Displays the parameters of a node, displays a plug filter and
        modifies it.

        Tests the class PlugFilter() within the Node Controller V1
        (class NodeController()).
        """

        config = Config(properties_path=self.properties_path)
        controlV1_ver = config.isControlV1()

        # Switch to V1 node controller GUI, if necessary
        if not controlV1_ver:
            config.setControlV1(True)
            self.restart_MIA()

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Get the 2 first documents/records
        with self.main_window.project.database.data() as database_data:
            DOCUMENT_1 = database_data.get_document_names(COLLECTION_CURRENT)[
                0
            ]
            DOCUMENT_2 = database_data.get_document_names(COLLECTION_CURRENT)[
                1
            ]

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        node_controller = self.main_window.pipeline_manager.nodeController

        # Add the "Smooth" process, creates a node called "smooth_1"
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exports the mandatory plugs
        pipeline_editor_tabs.get_current_editor().current_node_name = (
            "smooth_1"
        )
        (
            pipeline_editor_tabs.get_current_editor
        )().export_node_unconnected_mandatory_plugs()

        # Display parameters of "smooth_1" node
        input_process = pipeline.nodes[""].process

        node_controller.display_parameters(
            "inputs", get_process_instance(input_process), pipeline
        )

        # Opens a filter for the plug "in_files",
        # without "node_controller.scans_list"
        parameters = (0, pipeline, type(Undefined))
        node_controller.display_filter(
            "inputs", "in_files", parameters, input_process
        )

        # Asserts its default value
        node = pipeline.nodes[""]
        self.assertEqual(Undefined, node.get_plug_value("in_files"))

        # Look for "DOCUMENT_2" in the input documents
        plug_filter = node_controller.pop_up
        plug_filter.search_str(DOCUMENT_2)
        index_DOCUMENT_1 = plug_filter.table_data.get_scan_row(DOCUMENT_1)

        # if "DOCUMENT_1" is hidden
        self.assertTrue(plug_filter.table_data.isRowHidden(index_DOCUMENT_1))

        # Resets the search bar
        plug_filter.reset_search_bar()

        # if "DOCUMENT_1" is not hidden
        self.assertFalse(plug_filter.table_data.isRowHidden(index_DOCUMENT_1))

        # Tries search for an empty string
        plug_filter.search_str("")

        # Search for "DOCUMENT_2" and changes tags
        plug_filter.search_str(DOCUMENT_2)

        index_DOCUMENT_2 = plug_filter.table_data.get_scan_row(DOCUMENT_2)
        plug_filter.table_data.selectRow(index_DOCUMENT_2)

        # FIXME: we need to find a better way to interact with the plug_filter
        #        objects. At the moment, QTimer.singleShoot does not give a
        #        good result because it is an asynchronous action and we can
        #        observe mixtures of QT signals. Since we are not
        #        instantiating exactly the right objects, this results in a
        #        mixture of signals that can crash the execution. Currently
        #        the QTimer.singleShoot is removed (this should not change
        #        much the test coverage because the objects are still used
        #        (update_tags, update_tag_to_filter)

        plug_filter.update_tags()

        self.assertTrue(
            type(plug_filter.table_data.get_tag_column("AcquisitionDate"))
            == int
        )

        plug_filter.update_tag_to_filter()
        plug_filter.push_button_tag_filter.setText(TAG_FILENAME)
        # TODO: select tag to filter with

        # Closes the filter for the plug "in_files"
        plug_filter.ok_clicked()

        # Assert the modified value
        self.assertIn(
            str(Path(DOCUMENT_2)),
            str(Path(node.get_plug_value("in_files")[0])),
        )

        # Opens a filter for the plug "in_files", now with a "scans_list"
        with self.main_window.project.database.data() as database_data:
            node_controller.scan_list = database_data.get_document_names(
                COLLECTION_CURRENT
            )

        node_controller.display_filter(
            "inputs", "in_files", parameters, input_process
        )

        # Look for something that does not give any match
        plug_filter.search_str("!@#")
        # this will empty the "plug_filter.table_data.selectedIndexes()"
        # and trigger an uncovered part of "set_plug_value(self)"

        plug_filter.ok_clicked()

        # Switches back to node controller V2, if necessary (return to initial
        # state)
        config = Config(properties_path=self.properties_path)

        if not controlV1_ver:
            config.setControlV1(False)

    def test_update_node_name(self):
        """Displays parameters of a node and updates its name."""

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_editor_tabs = pipeline_manager.pipelineEditorTabs

        # Adding a process => creates a node called "smooth_1"
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        # Displaying the smooth_1 node parameters
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        process = pipeline.nodes["smooth_1"].process
        pipeline_manager.displayNodeParameters("smooth_1", process)
        node_controller = pipeline_manager.nodeController

        # Change the node name from smooth_1 to smooth_test, test if it's ok
        node_controller.line_edit_node_name.setText("smooth_test")
        keyEvent = QtGui.QKeyEvent(
            QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier
        )
        QCoreApplication.postEvent(
            node_controller.line_edit_node_name, keyEvent
        )
        QTest.qWait(100)
        self.assertTrue("smooth_test" in pipeline.nodes.keys())

        # Add 2 another Smooth process => Creates nodes called
        # smooth_1 and smooth_2
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        # Adding link between smooth_test and smooth_1 nodes
        source = ("smooth_test", "_smoothed_files")
        dest = ("smooth_1", "in_files")
        pipeline_editor_tabs.get_current_editor().add_link(
            source, dest, True, False
        )

        # Adding link between smooth_2 and smooth_1 nodes
        source = ("smooth_1", "_smoothed_files")
        dest = ("smooth_2", "in_files")
        pipeline_editor_tabs.get_current_editor().add_link(
            source, dest, True, False
        )

        # Displaying the smooth_1 node parameters
        process = pipeline.nodes["smooth_1"].process
        pipeline_manager.displayNodeParameters("smooth_1", process)
        node_controller = pipeline_manager.nodeController

        # Change node name from smooth_1 to smooth_test.
        # This should not change the node name because there is already a
        # "smooth_test" process in the pipeline.
        # Test if smooth_1 is still in the pipeline
        node_controller.line_edit_node_name.setText("smooth_test")
        keyEvent = QtGui.QKeyEvent(
            QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier
        )
        QCoreApplication.postEvent(
            node_controller.line_edit_node_name, keyEvent
        )
        QTest.qWait(100)
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        node_controller.line_edit_node_name.setText("smooth_test_2")
        keyEvent = QtGui.QKeyEvent(
            QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier
        )
        QCoreApplication.postEvent(
            node_controller.line_edit_node_name, keyEvent
        )
        QTest.qWait(100)
        self.assertTrue("smooth_test_2" in pipeline.nodes.keys())

        # Verifying that the updated node has the same links
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_test_2"].plugs["in_files"].links_from),
        )
        self.assertEqual(
            1,
            len(
                pipeline.nodes["smooth_test_2"]
                .plugs["_smoothed_files"]
                .links_to
            ),
        )


class TestMIAPipelineEditor(TestMIACase):
    """Tests for the pipeline editor, part of the pipeline manager tab.

    Tests PipelineEditor.

    :Contains:
        :Method:
            - test_add_tab: adds tabs to the PipelineEditorTabs
            - test_close_tab: closes a tab in the PipelineEditorTabs
            - test_drop_process: adds a Nipype SPM Smooth process to the
              pipeline editor
            - test_export_plug: exports plugs and mocks dialog boxes
            - test_save_pipeline: creates a pipeline and tries to save it
            - test_update_plug_value: displays node parameters and
              updates a plug value
            - test_z_check_modif: opens a pipeline, modifies it and
              check the modifications
            - test_z_get_editor: gets the instance of an editor
            - test_z_get_filename: gets the relative path to a
              previously saved pipeline file
            - test_z_get_index: gets the index of an editor
            - test_z_get_tab_name: gets the tab name of the editor
            - test_z_load_pipeline: loads a pipeline
            - test_z_open_sub_pipeline: opens a sub_pipeline
            - test_z_set_current_editor: sets the current editor
            - test_zz_del_pack: deletes a brick created during UTs
    """

    def test_add_tab(self):
        """Adds tabs to the PipelineEditorTabs."""

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )

        # Adding two new tabs
        pipeline_editor_tabs.new_tab()
        self.assertEqual(pipeline_editor_tabs.count(), 3)
        self.assertEqual(pipeline_editor_tabs.tabText(1), "New Pipeline 1")
        pipeline_editor_tabs.new_tab()
        self.assertEqual(pipeline_editor_tabs.count(), 4)
        self.assertEqual(pipeline_editor_tabs.tabText(2), "New Pipeline 2")

    def test_close_tab(self):
        """Closes a tab in the pipeline editor tabs.

        Indirectly tests PopUpClosePipeline.

        - Tests: PipelineEditor.close_tab

        - Mocks: PopUpClosePipeline.exec
        """

        # Sets shortcuts for objects that are often used
        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs

        # Closes an unmodified tab
        ppl_edt_tabs.close_tab(0)

        # Adds a process to modify the pipeline
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)
        self.assertEqual(ppl_edt_tabs.tabText(0)[-2:], " *")

        # Mocks the execution of the 'QDialog'
        # Instead of showing it, directly chooses 'save_as_clicked'
        PopUpClosePipeline.exec = Mock(
            side_effect=lambda: ppl_edt_tabs.pop_up_close.save_as_clicked()
        )
        ppl_edt_tabs.save_pipeline = Mock()

        # Tries to close the modified tab and saves the pipeline as
        ppl_edt_tabs.close_tab(0)

        # Asserts that 'undos' and 'redos' were deleted
        editor = ppl_edt_tabs.get_editor_by_index(0)
        with self.assertRaises(KeyError):
            ppl_edt_tabs.undos[editor]
            ppl_edt_tabs.redos[editor]

        # Directly chooses 'do_not_save_clicked'
        PopUpClosePipeline.exec = Mock(
            side_effect=lambda: ppl_edt_tabs.pop_up_close.do_not_save_clicked()
        )

        # Adds a new tab and a process
        ppl_edt_tabs.new_tab()
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        # Tries to close the modified tab and cancels saving
        ppl_edt_tabs.close_tab(0)

        # Directly chooses 'cancel_clicked'
        PopUpClosePipeline.exec = Mock(
            side_effect=lambda: ppl_edt_tabs.pop_up_close.cancel_clicked()
        )

        # Adds a process
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        # Tries to close the modified tab and cancels saving
        ppl_edt_tabs.close_tab(0)

        # Directly chooses 'cancel_clicked'
        PopUpClosePipeline.exec = Mock(
            side_effect=lambda: ppl_edt_tabs.pop_up_close.cancel_clicked()
        )

        # Adds a new process
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        # Tries to close the modified tab and cancels saving
        ppl_edt_tabs.close_tab(0)

    def test_drop_process(self):
        """Adds a Nipype SPM's Smooth process to the pipeline editor."""

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        self.assertFalse(
            "smooth_1"
            in (pipeline_editor_tabs.get_current_pipeline)().nodes.keys()
        )
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().drop_process(
            "nipype.interfaces.spm.Smooth"
        )
        self.assertTrue(
            "smooth_1"
            in (pipeline_editor_tabs.get_current_pipeline)().nodes.keys()
        )

    def test_export_plug(self):
        """Adds a process and exports plugs in the pipeline editor.

        -Tests: PipelineEditor.test_export_plug

        - Mocks:
            - QMessageBox.question
            - QInputDialog.getText
        """

        # Set shortcuts for objects that are often used
        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        ppl_edt = ppl_edt_tabs.get_current_editor()

        # Mocks 'PipelineEditor' attributes
        ppl_edt._temp_plug_name = ("", "")
        ppl_edt._temp_plug = Mock()
        ppl_edt._temp_plug.optional = False

        # Mocks the execution of a plug edit dialog
        PipelineEditor._PlugEdit.exec_ = Mock()

        # Exports a plug with no parameters
        ppl_edt._export_plug(pipeline_parameter=False, temp_plug_name=None)

        PipelineEditor._PlugEdit.exec_.assert_called_once_with()

        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        # Exports a plug value
        res = ppl_edt._export_plug(
            temp_plug_name=("rename_1", "_out_file"),
            pipeline_parameter="_out_file",
        )

        self.assertIsNone(res)

        # Mocks 'QMessageBox.question' to click accept
        QMessageBox.question = Mock(return_value=QMessageBox.Yes)

        # Tries to export the same plug value, accepts overwriting it
        # With 'multi_export' then the temp_plug_value will be returned
        res = ppl_edt._export_plug(
            temp_plug_name=("rename_1", "_out_file"),
            pipeline_parameter="_out_file",
            multi_export=True,
        )

        QMessageBox.question.assert_called_once()
        self.assertEqual(res, "_out_file")

        # Mocks again 'QMessageBox.question' to click reject
        QMessageBox.question = Mock(return_value=QMessageBox.No)
        QInputDialog.getText = Mock(return_value=("new_name", True))

        # Mocks 'export_parameter' to throw a 'TraitError'
        # from traits.api import TraitError
        # ppl_edt.scene.pipeline.export_parameter = Mock(
        #    side_effect=TraitError())

        # Tries to export the same plug value, denies overwriting it
        res = ppl_edt._export_plug(
            temp_plug_name=("rename_1", "_out_file"),
            pipeline_parameter="_out_file",
            multi_export=True,
        )

        QMessageBox.question.assert_called_once()
        QInputDialog.getText.assert_called_once()
        self.assertEqual(res, "_out_file")

    def test_save_pipeline(self):
        """Creates a pipeline and tries to save it.

        - Tests:
            - PipelineEditor.save_pipeline
            - PipelineEditorTabs.save_pipeline
            - save_pipeline inside pipeline_editor.py

        - Mocks:
            - QMessageBox.exec
            - QFileDialog.getSaveFileName
        """

        # Save the state of the current process library
        config = Config(properties_path=self.properties_path)
        usr_proc_folder = os.path.join(
            config.get_properties_path(), "processes", "User_processes"
        )
        shutil.copytree(
            usr_proc_folder,
            os.path.join(
                self.properties_path,
                "4UTs_TestMIAPipelineEditor",
                "User_processes",
            ),
        )
        shutil.copy(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            ),
            os.path.join(self.properties_path, "4UTs_TestMIAPipelineEditor"),
        )

        # Sets often used shortcuts
        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs

        # Switch to pipeline manager
        self.main_window.tabs.setCurrentIndex(2)

        # Tries to save a pipeline that is empty
        res = ppl_edt_tabs.save_pipeline()
        self.assertIsNone(res)

        # Adds a process
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Smooth)

        # Exports the input and output plugs
        ppl_edt_tabs.get_current_editor().current_node_name = "smooth_1"
        # fmt: off
        (
            ppl_edt_tabs.get_current_editor().
            export_node_unconnected_mandatory_plugs()
        )
        (
            ppl_edt_tabs.get_current_editor().
            export_node_all_unconnected_outputs()
        )
        # fmt: on

        # Mocks the execution of a dialog box
        QMessageBox.exec = lambda *args: None

        # Tries to save the pipeline with the user cancelling it
        QFileDialog.getSaveFileName = lambda *args: [""]
        res = ppl_edt_tabs.save_pipeline()
        self.assertIsNone(res)

        # Mocks the execution of a QFileDialog
        QFileDialog.getSaveFileName = lambda *args: [filename]

        # Removes the config.get_properties_path()/processes/User_processes
        # folder, to increase coverage
        shutil.rmtree(usr_proc_folder)

        # Tries to save the pipeline with a filename starting by a digit
        config = Config(properties_path=self.properties_path)
        usr_proc_folder = os.path.join(
            config.get_properties_path(), "processes", "User_processes"
        )
        filename = os.path.join(usr_proc_folder, "1_test_pipeline")
        res = ppl_edt_tabs.save_pipeline()
        self.assertIsNone(res)

        # Tries to save the pipeline with a filename without extension,
        # which is automatically completed to .py
        filename = os.path.join(usr_proc_folder, "test_pipeline_1")
        QFileDialog.getSaveFileName = lambda *args: [filename]
        res = ppl_edt_tabs.save_pipeline()
        self.assertTrue(res)  # The resulting filename is not empty

        # Save the pipeline with a filename with the wrong .c extension,
        # which is automatically corrected to .py
        filename = os.path.join(usr_proc_folder, "test_pipeline_2.c")
        QFileDialog.getSaveFileName = lambda *args: [filename]
        res = ppl_edt_tabs.save_pipeline()
        self.assertTrue(res)  # The resulting filename is not empty

        # Sets user mode to true
        Config(properties_path=self.properties_path).set_user_mode(True)

        # Tries to overwrite the previously saved pipeline without
        # permissions
        res = ppl_edt_tabs.save_pipeline()
        self.assertIsNone(res)

        # Sets user mode back to false
        Config(properties_path=self.properties_path).set_user_mode(True)

        # Saves a pipeline by specifying a filename
        filename = os.path.join(usr_proc_folder, "test_pipeline_3.py")
        res = ppl_edt_tabs.save_pipeline(new_file_name=filename)
        self.assertTrue(res)  # The resulting filename is not empty

    def test_update_plug_value(self):
        """Displays parameters of a node and updates a plug value."""

        config = Config(properties_path=self.properties_path)
        controlV1_ver = config.isControlV1()

        # Switch to V1 node controller GUI, if necessary
        if not controlV1_ver:
            config.setControlV1(True)
            self.restart_MIA()

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        node_controller = self.main_window.pipeline_manager.nodeController

        # Adding a process, creates a node called "threshold_1"
        process_class = Threshold
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        # Displaying the node parameters
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        node_controller.display_parameters(
            "threshold_1", get_process_instance(process_class), pipeline
        )

        # Updating the value of the "synchronize" input plug and
        # "_activation_forced" output plugs.
        # get_index_from_plug_name() only exists on the NodeController class
        # (v1).
        if hasattr(node_controller, "get_index_from_plug_name"):
            index = node_controller.get_index_from_plug_name(
                "synchronize", "in"
            )
            node_controller.line_edit_input[index].setText("1")

            # This calls "update_plug_value" method:
            node_controller.line_edit_input[index].returnPressed.emit()
            self.assertEqual(
                1, pipeline.nodes["threshold_1"].get_plug_value("synchronize")
            )

            # Updating the value of the "_activation_forced" plug
            index = node_controller.get_index_from_plug_name(
                "_activation_forced", "out"
            )
            node_controller.line_edit_output[index].setText("True")

            # This calls "update_plug_value" method:
            node_controller.line_edit_output[index].returnPressed.emit()
            self.assertEqual(
                True,
                pipeline.nodes["threshold_1"].get_plug_value(
                    "_activation_forced"
                ),
            )

        # Exporting the input plugs and modifying the "synchronize" input plug
        (pipeline_editor_tabs.get_current_editor)().current_node_name = (
            "threshold_1"
        )
        (
            pipeline_editor_tabs.get_current_editor
        )().export_node_all_unconnected_inputs()

        input_process = pipeline.nodes[""].process
        node_controller.display_parameters(
            "inputs", get_process_instance(input_process), pipeline
        )

        # Updating the value of the "synchronize" input plug.
        # get_index_from_plug_name() only exists on the NodeController class
        # (v1).
        if hasattr(node_controller, "get_index_from_plug_name"):
            index = node_controller.get_index_from_plug_name(
                "synchronize", "in"
            )
            node_controller.line_edit_input[index].setText("2")

            # This calls "update_plug_value" method:
            node_controller.line_edit_input[index].returnPressed.emit()
            self.assertEqual(
                2, pipeline.nodes["threshold_1"].get_plug_value("synchronize")
            )

        # Switches back to node controller V2, if necessary (return to initial
        # state)
        config = Config(properties_path=self.properties_path)

        if not controlV1_ver:
            config.setControlV1(False)

    def test_z_check_modif(self):
        """Opens a pipeline, opens it as a process in another tab, modifies it
        and check the modifications.
        """

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )

        # Adding a process from a .py file, creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "test_pipeline_1.py",
        )
        pipeline_editor_tabs.load_pipeline(filename)
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        # Make a new pipeline editor tab
        pipeline_editor_tabs.new_tab()
        pipeline_editor_tabs.set_current_editor_by_tab_name("New Pipeline 1")

        # Adding a process from Packages library, creates a node called
        # "test_pipeline_1_1"
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().drop_process(
            "User_processes.Test_pipeline_1"
        )
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("test_pipeline_1_1" in pipeline.nodes.keys())

        # Adding two processes, creates nodes called "smooth_1" and "smooth_2"
        pipeline_editor_tabs.get_current_editor().drop_process(
            "nipype.interfaces.spm.Smooth"
        )
        pipeline_editor_tabs.get_current_editor().drop_process(
            "nipype.interfaces.spm.Smooth"
        )
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())

        # Adding a link between smooth_1 and test_pipeline_1_1 nodes
        pipeline_editor_tabs.get_current_editor().add_link(
            ("smooth_1", "_smoothed_files"),
            ("test_pipeline_1_1", "in_files"),
            active=True,
            weak=False,
        )
        self.assertEqual(
            1,
            len(
                pipeline.nodes["test_pipeline_1_1"]
                .plugs["in_files"]
                .links_from
            ),
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Adding a link between test_pipeline_1_1 and smooth_2 nodes
        pipeline_editor_tabs.get_current_editor().add_link(
            ("test_pipeline_1_1", "_smoothed_files"),
            ("smooth_2", "in_files"),
            active=True,
            weak=False,
        )
        self.assertEqual(
            1, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(
                pipeline.nodes["test_pipeline_1_1"]
                .plugs["_smoothed_files"]
                .links_to
            ),
        )

        # Return to the first tab
        pipeline_editor_tabs.set_current_editor_by_tab_name(
            "test_pipeline_1.py"
        )

        # Export all plugs of the smooth_1 node
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().export_node_plugs(
            "smooth_1", optional=True
        )

        # Save the pipeline
        self.main_window.pipeline_manager.savePipeline(uncheck=True)

        # Go back to the second tab
        pipeline_editor_tabs.set_current_editor_by_tab_name("New Pipeline 1")
        pipeline_editor_tabs.get_current_editor().scene.pos[
            "test_pipeline_1_1"
        ] = QPoint(450, 500)

        # Check if the nodes of the pipeline have been modified
        pipeline_editor_tabs.get_current_editor().check_modifications()
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue(
            "fwhm" in pipeline.nodes["test_pipeline_1_1"].plugs.keys()
        )

    def test_z_get_editor(self):
        """Gets the instance of an editor.

        - Tests:
            - PipelineEditorTabs.get_editor_by_index
            - PipelineEditorTabs.get_current_editor
            - PipelineEditorTabs.get_editor_by_tab_name
            - PipelineEditorTabs.get_editor_by_filename
        """

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "test_pipeline_1.py",
        )
        pipeline_editor_tabs.load_pipeline(filename)
        editor0 = pipeline_editor_tabs.get_current_editor()

        # create new tab with new editor and make it current:
        pipeline_editor_tabs.new_tab()
        editor1 = pipeline_editor_tabs.get_current_editor()

        # Perform various tests on the pipeline editor tabs
        self.assertEqual(pipeline_editor_tabs.get_editor_by_index(0), editor0)
        self.assertEqual(pipeline_editor_tabs.get_editor_by_index(1), editor1)
        self.assertEqual(pipeline_editor_tabs.get_current_editor(), editor1)
        self.assertEqual(
            editor0,
            pipeline_editor_tabs.get_editor_by_tab_name("test_pipeline_1.py"),
        )
        self.assertEqual(
            editor1,
            pipeline_editor_tabs.get_editor_by_tab_name("New Pipeline 1"),
        )
        self.assertEqual(
            None, pipeline_editor_tabs.get_editor_by_tab_name("dummy")
        )
        self.assertEqual(
            editor0, pipeline_editor_tabs.get_editor_by_file_name(filename)
        )
        self.assertEqual(
            None, pipeline_editor_tabs.get_editor_by_file_name("dummy")
        )

    def test_z_get_filename(self):
        """Gets the relative path to a previously saved pipeline file.

        - Tests:
            - PipelineEditorTabs.get_filename_by_index
            - PipelineEditorTabs.get_current_filename
        """

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "test_pipeline_1.py",
        )
        pipeline_editor_tabs.load_pipeline(filename)

        self.assertEqual(
            filename,
            os.path.abspath(pipeline_editor_tabs.get_filename_by_index(0)),
        )
        self.assertEqual(None, pipeline_editor_tabs.get_filename_by_index(1))
        self.assertEqual(
            filename,
            os.path.abspath(pipeline_editor_tabs.get_current_filename()),
        )

    def test_z_get_index(self):
        """Gets the index of an editor.

        - Tests:
            - PipelineEditorTabs.get_index_by_tab_name
            - PipelineEditorTabs.get_index_by_filename
            - PipelineEditorTabs.get_index_by_editor
        """

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "test_pipeline_1.py",
        )
        pipeline_editor_tabs.load_pipeline(filename)
        editor0 = pipeline_editor_tabs.get_current_editor()

        # Create new tab with new editor and make it current
        pipeline_editor_tabs.new_tab()
        editor1 = pipeline_editor_tabs.get_current_editor()

        self.assertEqual(
            0, pipeline_editor_tabs.get_index_by_tab_name("test_pipeline_1.py")
        )
        self.assertEqual(
            1, pipeline_editor_tabs.get_index_by_tab_name("New Pipeline 1")
        )
        self.assertEqual(
            None, pipeline_editor_tabs.get_index_by_tab_name("dummy")
        )

        self.assertEqual(
            0, pipeline_editor_tabs.get_index_by_filename(filename)
        )
        self.assertEqual(
            None, pipeline_editor_tabs.get_index_by_filename("dummy")
        )

        self.assertEqual(0, pipeline_editor_tabs.get_index_by_editor(editor0))
        self.assertEqual(1, pipeline_editor_tabs.get_index_by_editor(editor1))
        self.assertEqual(
            None, pipeline_editor_tabs.get_index_by_editor("dummy")
        )

    def test_z_get_tab_name(self):
        """Gets the tab name of the editor.

        - Tests:
            - PipelineEditorTabs.get_tab_name_by_index
            - PipelineEditorTabs.get_current_tab_name
        """

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )

        self.assertEqual(
            "New Pipeline", pipeline_editor_tabs.get_tab_name_by_index(0)
        )
        self.assertEqual(None, pipeline_editor_tabs.get_tab_name_by_index(1))
        self.assertEqual(
            "New Pipeline", pipeline_editor_tabs.get_current_tab_name()
        )

    def test_z_load_pipeline(self):
        """Loads a pipeline."""

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "test_pipeline_1.py",
        )
        pipeline_editor_tabs.load_pipeline(filename)

        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

    def test_z_open_sub_pipeline(self):
        """Opens a sub_pipeline."""

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        config = Config(properties_path=self.properties_path)

        # Adding the "config.get_properties_path()/processes" path to the
        # system path
        sys.path.append(
            os.path.join(config.get_properties_path(), "processes")
        )

        # Importing the 'User_processes' package
        package_name = "User_processes"
        __import__(package_name)
        pkg = sys.modules[package_name]

        for name, cls in sorted(list(pkg.__dict__.items())):
            if name == "Test_pipeline_1":
                process_class = cls

        # Adding the "test_pipeline_1" as a process
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        # Opening the sub-pipeline in a new editor
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        process_instance = pipeline.nodes["test_pipeline_1_1"].process
        pipeline_editor_tabs.open_sub_pipeline(process_instance)
        self.assertTrue(3, pipeline_editor_tabs.count())
        self.assertEqual(
            "test_pipeline_1.py",
            os.path.basename(pipeline_editor_tabs.get_filename_by_index(1)),
        )

    def test_z_set_current_editor(self):
        """Sets the current editor.

        - Tests:
            - PipelineEditorTabs.set_current_editor_by_tab_name
            - PipelineEditorTabs.set_current_editor_by_file_name
            - PipelineEditorTabs.set_current_editor_by_editor
        """

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )
        config = Config(properties_path=self.properties_path)
        filename = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "test_pipeline_1.py",
        )
        pipeline_editor_tabs.load_pipeline(filename)
        editor0 = pipeline_editor_tabs.get_current_editor()

        # create new tab with new editor and make it current:
        pipeline_editor_tabs.new_tab()
        editor1 = pipeline_editor_tabs.get_current_editor()

        pipeline_editor_tabs.set_current_editor_by_tab_name(
            "test_pipeline_1.py"
        )
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 0)
        pipeline_editor_tabs.set_current_editor_by_tab_name("New Pipeline 1")
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 1)

        pipeline_editor_tabs.set_current_editor_by_file_name(filename)
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 0)

        pipeline_editor_tabs.set_current_editor_by_editor(editor1)
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 1)
        pipeline_editor_tabs.set_current_editor_by_editor(editor0)
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 0)

    def test_zz_del_pack(self):
        """Remove the bricks created during the unit tests.

        Take advantage of this to cover the part of the code used to remove the
        packages.
        """

        pkg = PackageLibraryDialog(self.main_window)

        # The Test_pipeline brick was added in the package library
        self.assertTrue(
            "Test_pipeline_1"
            in pkg.package_library.package_tree["User_processes"]
        )

        pkg.delete_package(
            to_delete="User_processes.Test_pipeline_1", loop=True
        )

        # The Test_pipeline brick has been removed from the package library
        self.assertFalse(
            "Test_pipeline_1"
            in pkg.package_library.package_tree["User_processes"]
        )

        # Restore the initial process library (before test_save_pipeline test)
        config = Config(properties_path=self.properties_path)
        usr_proc_folder = os.path.join(
            config.get_properties_path(), "processes", "User_processes"
        )
        shutil.rmtree(usr_proc_folder)
        os.remove(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            )
        )
        shutil.copytree(
            os.path.join(
                self.properties_path,
                "4UTs_TestMIAPipelineEditor",
                "User_processes",
            ),
            os.path.join(usr_proc_folder),
        )
        shutil.copy(
            os.path.join(
                self.properties_path,
                "4UTs_TestMIAPipelineEditor",
                "process_config.yml",
            ),
            os.path.join(config.get_properties_path(), "properties"),
        )


class TestMIAPipelineManagerTab(TestMIACase):
    """Tests the pipeline manager tab class, part of the homonym tab.

    :Contains:
        :Method:
            - test_add_plug_value_to_database_list_type: adds a list type plug
              value to the database
            - test_add_plug_value_to_database_non_list_type: adds a non list
              type plug value to the database
            - test_add_plug_value_to_database_several_inputs: exports a non
              list type input plug and with several possible inputs
            - test_ask_iterated_pipeline_plugs: test the iteration
              dialog for each plug of a Rename process
            - test_build_iterated_pipeline: mocks methods and builds an
              iterated pipeline
            - test_check_requirements: checks the requirements for a given node
            - test_cleanup_older_init: tests the cleaning of old
              initialisations
            - test_complete_pipeline_parameters: test the pipeline
              parameters completion
            - test_delete_processes: deletes a process and makes the undo/redo
            - test_end_progress: creates a progress object and tries to end it
            - test_garbage_collect: collects the garbage of a pipeline
            - test_get_capsul_engine: gets the capsul engine of the pipeline
            - test_get_missing_mandatory_parameters: tries to initialize
              the pipeline with missing mandatory parameters
            - test_get_pipeline_or_process: gets a pipeline and a process from
              the pipeline_manager
            - test_initialize: mocks objects and initializes the workflow
            - test_register_completion_attributes: mocks methods of the
              pipeline manager and registers completion attributes
            - test_register_node_io_in_database: sets input and output
              parameters and registers them in database
            - test_remove_progress: removes the progress of the pipeline
            - test_run: creates a pipeline manager progress object and
              tries to run it
            - test_save_pipeline: saves a simple pipeline
            - test_savePipelineAs: saves a pipeline under another name
            - test_set_anim_frame: runs the 'rotatingBrainVISA.gif' animation
            - test_show_status: shows the status of pipeline execution
            - test_stop_execution: shows the status window of the pipeline
              manager
            - test_undo_redo: tests the undo/redo feature
            - test_update_auto_inheritance: updates the job's auto inheritance
              dict
            - test_update_inheritance: updates the job's inheritance dict
            - test_update_node_list: initializes a workflow and adds a
              process to the "pipline_manager.node_list"
            - test_z_init_pipeline: initializes the pipeline
            - test_z_runPipeline: adds a processruns a pipeline
            - test_zz_del_pack: deletion of the brick created during UTs
    """

    def test_add_plug_value_to_database_list_type(self):
        """Opens a project, adds a 'Select' process, exports a list type
        input plug and adds it to the database.

        - Tests: PipelineManagerTab(QWidget).add_plug_value_to_database().
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_9")

        with self.main_window.project.database.data() as database_data:
            DOCUMENT_1 = database_data.get_document_names(COLLECTION_CURRENT)[
                0
            ]
            DOCUMENT_2 = database_data.get_document_names(COLLECTION_CURRENT)[
                1
            ]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs

        # Adds the process Select, creates the "select_1" node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Select)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "select_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "select_1"
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        pipeline_manager = self.main_window.pipeline_manager

        # Initializes the workflow manually
        pipeline_manager.workflow = workflow_from_pipeline(
            pipeline, complete_parameters=True
        )

        # Gets the 'job' and mocks adding a brick to the collection
        job = pipeline_manager.workflow.jobs[0]

        brick_id = str(uuid.uuid4())
        job.uuid = brick_id
        pipeline_manager.brick_list.append(brick_id)

        with pipeline_manager.project.database.data(
            write=True
        ) as database_data:
            database_data.add_document(COLLECTION_BRICK, brick_id)

        # Sets the mandatory plug values corresponding to "inputs" node
        trait_list_inlist = TraitListObject(
            InputMultiObject(), pipeline, "inlist", [DOCUMENT_1, DOCUMENT_2]
        )

        # Mocks the creation of a completion engine
        process = job.process()
        plug_name = "inlist"
        trait = process.trait(plug_name)
        inputs = process.get_inputs()

        # Mocks the attributes dict
        attributes = {
            "not_list": "not_list_value",
            "small_list": ["list_item1"],
            "large_list": ["list_item1", "list_item2", "list_item3"],
        }

        # Adds plug value of type 'TraitListObject'
        pipeline_manager.add_plug_value_to_database(
            trait_list_inlist,
            brick_id,
            "",
            "select_1",
            plug_name,
            "select_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # Asserts that both 'DOCUMENT_1' and 'DOCUMENT_2' are stored in
        # the database
        with pipeline_manager.project.database.data() as database_data:
            self.assertTrue(
                database_data.has_document(COLLECTION_CURRENT, DOCUMENT_1)
            )
            self.assertTrue(
                database_data.has_document(COLLECTION_CURRENT, DOCUMENT_2)
            )

    def test_add_plug_value_to_database_non_list_type(self):
        """Opens a project, adds a 'Rename' process, exports a non list type
        input plug and adds it to the database.

        - Tests: PipelineManagerTab(QWidget).add_plug_value_to_database()
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        with self.main_window.project.database.data() as database_data:
            DOCUMENT_1 = database_data.get_document_names(COLLECTION_CURRENT)[
                0
            ]

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )

        # Adds the process Rename, creates the "rename_1" node
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(Rename)
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "rename_1"
        pipeline_editor_tabs.get_current_editor().current_node_name = (
            "rename_1"
        )
        (
            pipeline_editor_tabs.get_current_editor
        )().export_unconnected_mandatory_inputs()
        (
            pipeline_editor_tabs.get_current_editor
        )().export_all_unconnected_outputs()

        old_scan_name = DOCUMENT_1.split("/")[-1]
        new_scan_name = "new_name.nii"

        # Changes the "_out_file" in the "outputs" node
        pipeline.nodes[""].set_plug_value(
            "_out_file", DOCUMENT_1.replace(old_scan_name, new_scan_name)
        )

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_manager.workflow = workflow_from_pipeline(
            pipeline, complete_parameters=True
        )

        job = pipeline_manager.workflow.jobs[0]

        brick_id = str(uuid.uuid4())
        job.uuid = brick_id
        pipeline_manager.brick_list.append(brick_id)

        with pipeline_manager.project.database.data(
            write=True
        ) as database_data:
            database_data.add_document(COLLECTION_BRICK, brick_id)

        # Sets the mandatory plug values in the "inputs" node
        pipeline.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        pipeline.nodes[""].set_plug_value("format_string", new_scan_name)

        process = job.process()
        plug_name = "in_file"
        trait = process.trait(plug_name)

        inputs = process.get_inputs()

        attributes = {}
        completion = ProcessCompletionEngine.get_completion_engine(process)

        if completion:
            attributes = completion.get_attribute_values().export_to_dict()

        # Plug value is file location outside project directory
        pipeline_manager.add_plug_value_to_database(
            DOCUMENT_1,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        with pipeline_manager.project.database.data() as database_data:
            self.assertTrue(
                database_data.has_document(COLLECTION_CURRENT, DOCUMENT_1)
            )

        # Plug values outside the directory are not registered into the
        # database, therefore only plug values inside the project will be used
        # from now on.

        # Plug value is file location inside project directory
        inside_project = os.path.join(
            pipeline_manager.project.folder, DOCUMENT_1.split("/")[-1]
        )
        pipeline_manager.add_plug_value_to_database(
            inside_project,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # Plug value that is already in the database
        pipeline_manager.add_plug_value_to_database(
            inside_project,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # Plug value is tag
        tag_value = os.path.join(pipeline_manager.project.folder, "tag.gz")
        pipeline_manager.add_plug_value_to_database(
            tag_value,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # Plug value is .mat
        mat_value = os.path.join(pipeline_manager.project.folder, "file.mat")
        pipeline_manager.add_plug_value_to_database(
            mat_value,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # Plug value is .txt
        txt_value = os.path.join(pipeline_manager.project.folder, "file.txt")
        pipeline_manager.add_plug_value_to_database(
            txt_value,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # 'parent_files' are extracted from the 'inheritance_dict' and
        # 'auto_inheritance_dict' attributes of 'job'. They test cases are
        # listed below:
        # 'parent_files' inside 'auto_inheritance_dict'
        job.auto_inheritance_dict = {inside_project: "parent_files_value"}
        pipeline_manager.add_plug_value_to_database(
            inside_project,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # 'parent_files' inside 'inheritance_dict'
        job.auto_inheritance_dict = None
        job.inheritance_dict = {inside_project: "parent_files_value"}
        pipeline_manager.add_plug_value_to_database(
            inside_project,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # 'parent_files' inside 'inheritance_dict', dict type
        job.inheritance_dict = {
            inside_project: {
                "own_tags": [
                    {
                        "name": "tag_name",
                        "field_type": FIELD_TYPE_STRING,
                        "description": "description_content",
                        "visibility": "visibility_content",
                        "origin": "origin_content",
                        "unit": "unit_content",
                        "value": "value_content",
                        "default_value": "default_value_content",
                    }
                ],
                "parent": "parent_content",
            }
        }
        pipeline_manager.add_plug_value_to_database(
            inside_project,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

        # 'parent_files' inside 'inheritance_dict', output is one of the inputs
        job.inheritance_dict = {
            inside_project: {
                "own_tags": [
                    {
                        "name": "tag_name",
                        "field_type": FIELD_TYPE_STRING,
                        "description": "description_content",
                        "visibility": "visibility_content",
                        "origin": "origin_content",
                        "unit": "unit_content",
                        "value": "value_content",
                        "default_value": "default_value_content",
                    }
                ],
                "parent": "parent_content",
                "output": inside_project,
            }
        }

        pipeline_manager.add_plug_value_to_database(
            inside_project,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        )

    def test_add_plug_value_to_database_several_inputs(self):
        """Creates a new project folder, adds a 'Rename' process, exports a
        non list type input plug and with several possible inputs.

        Independently opens an inheritance dict pop-up.

        The test cases are divided into:
        - 1) 'parent_files' is a dict with 2 keys and identical values
        - 2) 'parent_files' is a dict with 2 keys and distinct values
        - 3) 'mock_key_2' is in 'ppl_manager.key' indexed by the node name
        - 4) 'mock_key_2' is in 'ppl_manager.key' indexed by the node name +
             plug value

        - Tests:
            - PipelineManagerTab.add_plug_value_to_database
            - PopUpInheritanceDict.

        - Mocks:
            - PopUpInheritanceDict.exec
        """

        def mock_get_document(collection, relfile):
            """Blabla"""

            SCAN_1_ = SCAN_1

            if relfile == "mock_val_1":
                SCAN_1_._values[3] = "Exp Type 1"
                return SCAN_1_
            elif relfile == "mock_val_2":
                SCAN_1_._values[3] = "Exp Type 2"
                return SCAN_1_

            return None

        # Those methods are called prior to adding a plug to the database
        def reset_inheritance_dicts():
            """Blabla"""

            job.inheritance_dict = {DOCUMENT_1: None}
            job.auto_inheritance_dict = {DOCUMENT_1: parent_files}

        def reset_collections():
            """Blabla"""

            with ppl_manager.project.database.data(
                write=True
            ) as database_data:

                if database_data.has_document(COLLECTION_CURRENT, P_VALUE):
                    database_data.remove_document(COLLECTION_CURRENT, P_VALUE)

                if database_data.has_document(COLLECTION_CURRENT, DOCUMENT_1):
                    database_data.remove_document(
                        COLLECTION_CURRENT, DOCUMENT_1
                    )

                if database_data.has_document(COLLECTION_INITIAL, P_VALUE):
                    database_data.remove_document(COLLECTION_INITIAL, P_VALUE)

                if database_data.has_document(COLLECTION_INITIAL, DOCUMENT_1):
                    database_data.remove_document(
                        COLLECTION_INITIAL, DOCUMENT_1
                    )

        # Sets shortcuts for often used objects
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl_edt_tab = ppl_edt_tabs.get_current_editor()

        # Creates a new project folder and adds one document to the
        # project, sets the plug value that is added to the database
        project_8_path = self.get_new_test_project()
        ppl_manager.project.folder = project_8_path
        folder = os.path.join(project_8_path, "data", "raw_data")
        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )
        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        P_VALUE = DOCUMENT_1.replace(os.path.abspath(project_8_path), "")[1:]

        with ppl_manager.project.database.data(write=True) as database_data:
            database_data.add_document(COLLECTION_CURRENT, DOCUMENT_1)

        # Adds the processes Rename, creates the "rename_1" node
        ppl_edt_tab.click_pos = QPoint(450, 500)
        ppl_edt_tab.add_named_process(Rename)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "rename_1"
        ppl_edt_tab.current_node_name = "rename_1"
        ppl_edt_tab.export_unconnected_mandatory_inputs()
        ppl_edt_tab.export_all_unconnected_outputs()

        old_scan_name = DOCUMENT_1.split("/")[-1]
        new_scan_name = "new_name.nii"

        # Changes the "_out_file" in the "outputs" node
        pipeline.nodes[""].set_plug_value(
            "_out_file", DOCUMENT_1.replace(old_scan_name, new_scan_name)
        )

        ppl_manager.workflow = workflow_from_pipeline(
            pipeline, complete_parameters=True
        )

        job = ppl_manager.workflow.jobs[0]

        brick_id = str(uuid.uuid4())
        job.uuid = brick_id
        ppl_manager.brick_list.append(brick_id)

        with ppl_manager.project.database.data(write=True) as database_data:
            database_data.add_document(COLLECTION_BRICK, brick_id)

        # Sets the mandatory plug values in the "inputs" node
        pipeline.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        pipeline.nodes[""].set_plug_value("format_string", new_scan_name)

        process = job.process()
        plug_name = "in_file"
        trait = process.trait(plug_name)

        inputs = process.get_inputs()

        attributes = {}
        completion = ProcessCompletionEngine.get_completion_engine(process)

        if completion:
            attributes = completion.get_attribute_values().export_to_dict()

        # Mocks the document getter to always return a scan
        with ppl_manager.project.database.data() as database_data:
            SCAN_1 = database_data.get_document(COLLECTION_CURRENT, DOCUMENT_1)
            database_data.get_document = mock_get_document

            # Mocks the value setter on the database
            database_data.set_values = Mock()

            # 1) 'parent_files' is a dict with 2 keys and identical values
            parent_files = {
                "mock_key_1": os.path.join(
                    ppl_manager.project.folder, "mock_val_1"
                ),
                "mock_key_2": os.path.join(
                    ppl_manager.project.folder, "mock_val_1"
                ),
            }

        reset_inheritance_dicts()
        reset_collections()

        args = [
            DOCUMENT_1,
            brick_id,
            "",
            "rename_1",
            plug_name,
            "rename_1",
            job,
            trait,
            inputs,
            attributes,
        ]

        ppl_manager.add_plug_value_to_database(*args)

        # Mocks the execution of 'PopUpInheritanceDict' to avoid
        # asynchronous shot
        PopUpInheritanceDict.exec = Mock()

        # 2) 'parent_files' is a dict with 2 keys and distinct values
        # Triggers the execution of 'PopUpInheritanceDict'
        parent_files["mock_key_2"] = os.path.join(
            ppl_manager.project.folder, "mock_val_2"
        )

        reset_inheritance_dicts()
        reset_collections()

        ppl_manager.add_plug_value_to_database(*args)

        # 3) 'mock_key_2' is in 'ppl_manager.key' indexed by the node name
        ppl_manager.key = {"rename_1": "mock_key_2"}

        reset_inheritance_dicts()
        reset_collections()

        ppl_manager.add_plug_value_to_database(*args)

        # 4) 'mock_key_2' is in 'ppl_manager.key' indexed by the node name
        # + plug value
        ppl_manager.key = {"rename_1in_file": "mock_key_2"}

        reset_inheritance_dicts()
        reset_collections()

        ppl_manager.add_plug_value_to_database(*args)

        # Independently tests 'PopUpInheritanceDict'
        pop_up = PopUpInheritanceDict(
            {"mock_key": "mock_value"},
            "mock_full_name",
            "mock_plug_name",
            True,
        )

        pop_up.ok_clicked()
        pop_up.okall_clicked()
        pop_up.ignore_clicked()
        pop_up.ignoreall_clicked()
        pop_up.ignore_node_clicked()

    def test_ask_iterated_pipeline_plugs(self):
        """Adds the process 'Rename', export mandatory input and output plug
        and opens an iteration dialog for each plug.

        - Tests: PipelineManagerTab.ask_iterated_pipeline_plugs
        """

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs

        # Adds the processes Rename, creates the "rename_1" node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        pipeline = ppl_edt_tabs.get_current_pipeline()
        pipeline_manager = self.main_window.pipeline_manager

        # Exports the mandatory input and output plugs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "rename_1"
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Mocks executing a dialog box and clicking close
        QDialog.exec_ = lambda self_, *args: self_.accept()

        pipeline_manager.ask_iterated_pipeline_plugs(pipeline)

    def test_build_iterated_pipeline(self):
        """Adds a 'Select' process, exports its mandatory inputs, mocks
        some methods of the pipeline manager and builds an iterated pipeline.

        - Tests:'PipelineManagerTab.build_iterated_pipeline'
        """

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        ppl_manager = self.main_window.pipeline_manager

        # Adds the processes Select, creates the "select_1" node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Select)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "select_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "select_1"
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Mocks 'parent_pipeline' and returns a 'Process' instead of a
        # 'Pipeline'
        pipeline = pipeline.nodes["select_1"].process
        pipeline.parent_pipeline = True

        ppl_manager.get_pipeline_or_process = MagicMock(return_value=pipeline)

        # Mocks 'ask_iterated_pipeline_plugs' and returns the tuple
        # '(iterated_plugs, database_plugs)'
        ppl_manager.ask_iterated_pipeline_plugs = MagicMock(
            return_value=(["index", "inlist", "_out"], ["inlist"])
        )

        # Mocks 'update_nodes_and_plugs_activation' with no returned values
        pipeline.update_nodes_and_plugs_activation = MagicMock()

        # Builds iterated pipeline
        print("\n\n** An exception message is expected below\n")
        ppl_manager.build_iterated_pipeline()

        # Asserts the mock methods were called as expected
        ppl_manager.get_pipeline_or_process.assert_called_once_with()
        ppl_manager.ask_iterated_pipeline_plugs.assert_called_once_with(
            pipeline
        )
        pipeline.update_nodes_and_plugs_activation.assert_called_once_with()

    def test_check_requirements(self):
        """Adds a 'Select' process, appends it to the nodes list and checks
        the requirements for the given node.

        - Tests: PipelineManagerTab.check_requirements
        """

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        pipeline_manager = self.main_window.pipeline_manager

        # Adds the processes Select, creates the "select_1" node
        process_class = Select
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Appends a 'Process' to 'pipeline_manager.node_list' and checks
        # requirements
        pipeline_manager.node_list.append(pipeline.nodes["select_1"].process)
        config = pipeline_manager.check_requirements()

        # Asserts the output
        self.assertTrue(isinstance(config, dict))
        self.assertTrue(
            list(config[next(iter(config))].keys())
            == ["capsul_engine", "capsul.engine.module.nipype"]
        )

    def test_cleanup_older_init(self):
        """Mocks a brick list, mocks some methods from the pipeline manager
        and cleans up old initialization results.

        - Tests: PipelineManagerTab.cleanup_older_init
        """

        ppl_manager = self.main_window.pipeline_manager

        # Mocks a 'pipeline_manager.brick_list'
        brick_id = str(uuid.uuid4())
        ppl_manager.brick_list.append(brick_id)

        # Mocks methods used in the test
        (ppl_manager.main_window.data_browser.table_data.delete_from_brick) = (
            MagicMock()
        )
        ppl_manager.project.cleanup_orphan_nonexisting_files = MagicMock()

        # Cleans up older init
        ppl_manager.cleanup_older_init()

        # Asserts that the mock methods were called as expected
        # fmt: off
        (
            ppl_manager.main_window.data_browser.table_data.delete_from_brick.
            assert_called_once_with(brick_id)
        )
        (
            ppl_manager.project.cleanup_orphan_nonexisting_files.
            assert_called_once_with()
        )
        # fmt: on

        # Asserts that both 'brick_list' and 'node_list' were cleaned
        self.assertTrue(len(ppl_manager.brick_list) == 0)
        self.assertTrue(len(ppl_manager.node_list) == 0)

    def test_complete_pipeline_parameters(self):
        """Mocks a method of pipeline manager and completes the pipeline
        parameters.

        - Tests: PipelineManagerTab.complete_pipeline_parameters
        """

        ppl_manager = self.main_window.pipeline_manager

        # Mocks method used in the test
        ppl_manager.get_capsul_engine = MagicMock(
            return_value=ppl_manager.get_pipeline_or_process()
        )

        # Complete pipeline parameters
        ppl_manager.complete_pipeline_parameters()

        # Asserts that the mock method was called as expected
        ppl_manager.get_capsul_engine.assert_called_once_with()

    def test_delete_processes(self):
        """Deletes a process and makes the undo/redo action."""

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )

        # Adding processes
        process_class = Smooth

        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        # Creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )
        # Creates a node called "smooth_2"
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )
        # Creates a node called "smooth_3"
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        pipeline = pipeline_editor_tabs.get_current_pipeline()

        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())

        pipeline_editor_tabs.get_current_editor().add_link(
            ("smooth_1", "_smoothed_files"),
            ("smooth_2", "in_files"),
            active=True,
            weak=False,
        )

        self.assertEqual(
            1, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        pipeline_editor_tabs.get_current_editor().add_link(
            ("smooth_2", "_smoothed_files"),
            ("smooth_3", "in_files"),
            active=True,
            weak=False,
        )

        self.assertEqual(
            1, len(pipeline.nodes["smooth_3"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_2"].plugs["_smoothed_files"].links_to),
        )

        pipeline_editor_tabs.get_current_editor().current_node_name = (
            "smooth_2"
        )
        pipeline_editor_tabs.get_current_editor().del_node()

        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())
        self.assertEqual(
            0,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )
        self.assertEqual(
            0, len(pipeline.nodes["smooth_3"].plugs["in_files"].links_from)
        )

        pipeline_manager.undo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())
        self.assertEqual(
            1, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )
        self.assertEqual(
            1, len(pipeline.nodes["smooth_3"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_2"].plugs["_smoothed_files"].links_to),
        )

        pipeline_manager.redo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())
        self.assertEqual(
            0,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )
        self.assertEqual(
            0, len(pipeline.nodes["smooth_3"].plugs["in_files"].links_from)
        )

    def test_end_progress(self):
        """Creates a pipeline manager progress object and tries to end it.

        - Tests RunProgress.end_progress
        """

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Creates a 'RunProgress' object
        ppl_manager.progress = RunProgress(ppl_manager)

        # 'ppl_manager.worker' does not have a 'exec_id'
        ppl_manager.progress.end_progress()

        # Mocks an 'exec_id' and an 'get_pipeline_or_process'
        ppl_manager.progress.worker.exec_id = str(uuid.uuid4())
        engine = ppl.get_study_config().engine
        engine.raise_for_status = Mock()

        # Ends the progress with success
        ppl_manager.progress.end_progress()

        engine.raise_for_status.assert_called_once_with(
            ppl_manager.progress.worker.status,
            ppl_manager.progress.worker.exec_id,
        )

        # Mocks a 'WorkflowExecutionError' exception
        engine.raise_for_status = Mock(
            side_effect=WorkflowExecutionError({}, {}, verbose=False)
        )

        # Raises a 'WorkflowExecutionError' while ending progress
        # ppl_manager.progress.end_progress()
        # FIXME: the above call to the function leads to a Segmentation
        #        fault when the test routine is launched in AppVeyor.

    def test_garbage_collect(self):
        """Mocks several objects of the pipeline manager and collects the
        garbage of the pipeline.

        - Tests: PipelineManagerTab.test_garbage_collect
        """

        ppl_manager = self.main_window.pipeline_manager

        # INTEGRATED TEST

        # Mocks the 'initialized' object
        ppl_manager.pipelineEditorTabs.get_current_editor().initialized = True

        # Collects the garbage
        ppl_manager.garbage_collect()

        # Asserts that the 'initialized' object changed state
        self.assertFalse(
            ppl_manager.pipelineEditorTabs.get_current_editor().initialized
        )

        # ISOLATED TEST

        # Mocks again the 'initialized' object
        ppl_manager.pipelineEditorTabs.get_current_editor().initialized = True

        # Mocks the methods used in the test
        ppl_manager.postprocess_pipeline_execution = MagicMock()
        ppl_manager.project.cleanup_orphan_nonexisting_files = MagicMock()
        ppl_manager.project.cleanup_orphan_history = MagicMock()
        (ppl_manager.main_window.data_browser.table_data.update_table) = (
            MagicMock()
        )
        ppl_manager.update_user_buttons_states = MagicMock()

        # Collects the garbage
        ppl_manager.garbage_collect()

        # Asserts that the 'initialized' object changed state
        self.assertFalse(
            ppl_manager.pipelineEditorTabs.get_current_editor().initialized
        )

        # Asserts that the mocked methods were called as expected
        ppl_manager.postprocess_pipeline_execution.assert_called_once_with()
        # fmt: off
        (
            ppl_manager.project.cleanup_orphan_nonexisting_files.
            assert_called_once_with()
        )
        # fmt: on
        ppl_manager.project.cleanup_orphan_history.assert_called_once_with()
        # fmt:off
        (
            ppl_manager.main_window.data_browser.table_data.update_table.
            assert_called_once_with()
        )
        # fmt:on
        ppl_manager.update_user_buttons_states.assert_called_once_with()

    def test_get_capsul_engine(self):
        """Mocks an object in the pipeline manager and gets the capsul engine
        of the pipeline.

        - Tests: PipelineManagerTab.get_capsul_engine
        """

        ppl_manager = self.main_window.pipeline_manager

        # INTEGRATED

        # Gets the capsul engine
        capsul_engine = ppl_manager.get_capsul_engine()

        # Asserts that the 'capsul_engine' is of class 'CapsulEngine'
        self.assertIsInstance(capsul_engine, CapsulEngine)

        # ISOLATED
        ppl_manager.pipelineEditorTabs.get_capsul_engine = MagicMock()

        # Gets the capsul engine
        _ = ppl_manager.get_capsul_engine()

        # Asserts that the mocked method was called as expected
        # fmt: off
        (
            ppl_manager.pipelineEditorTabs.get_capsul_engine.
            assert_called_once_with()
        )
        # fmt: on

    def test_get_missing_mandatory_parameters(self):
        """
        Adds a process, exports input and output plugs and tries to initialize
        the pipeline with missing mandatory parameters.

        -Tests: PipelineManagerTab.get_missing_mandatory_parameters
        """

        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory inputs and outputs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "rename_1"
        (
            ppl_edt_tabs.get_current_editor
        )().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor()._export_plug(
            temp_plug_name=("rename_1", "_out_file"),
            pipeline_parameter="_out_file",
            optional=False,
            weak_link=False,
        )

        # Initializes the pipeline
        ppl_manager.workflow = workflow_from_pipeline(
            pipeline, complete_parameters=True
        )
        ppl_manager.update_node_list()

        # Asserts that 2 mandatory parameters are missing
        ppl_manager.update_node_list()
        missing_inputs = ppl_manager.get_missing_mandatory_parameters()
        self.assertEqual(len(missing_inputs), 2)
        self.assertEqual(missing_inputs[0], "rename_1.format_string")
        self.assertEqual(missing_inputs[1], "rename_1.in_file")

        # Empties the jobs list
        ppl_manager.workflow.jobs = []

        # Asserts that 2 mandatory parameters are still missing
        missing_inputs = ppl_manager.get_missing_mandatory_parameters()
        self.assertEqual(len(missing_inputs), 2)
        self.assertEqual(missing_inputs[0], "rename_1.format_string")
        self.assertEqual(missing_inputs[1], "rename_1.in_file")

    def test_get_pipeline_or_process(self):
        """Adds a process and gets a pipeline and a process from the pipeline
        manager.

        - Tests: PipelineManagerTab.get_pipeline_or_process
        """

        # Sets shortcuts for often used objects
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        # Gets the pipeline
        pipeline = ppl_manager.get_pipeline_or_process()

        # Asserts that the object 'pipeline' is a 'Pipeline'
        self.assertIsInstance(pipeline, Pipeline)

        # Adds the processes Rename, creates the "rename_1" node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        # Gets a process
        process = ppl_manager.get_pipeline_or_process()

        # Asserts that the process 'pipeline' is indeed a 'NipypeProcess'
        self.assertIsInstance(process, NipypeProcess)

    def test_initialize(self):
        """Adds Select process, exports its plugs, mocks objects from the
        pipeline manager and initializes the workflow.

        - Tests: the PipelineManagerTab.initialize
        """

        # Gets the paths of 2 documents
        folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "mia_ut_data",
            "resources",
            "mia",
            "project_8",
            "data",
            "raw_data",
        )

        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        # Adds the process 'Rename' as the node 'rename_1'
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory inputs and outputs for 'select_1'
        ppl_edt_tabs.get_current_editor().current_node_name = "rename_1"
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Sets mandatory parameters 'select_1'
        pipeline.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        pipeline.nodes[""].set_plug_value("format_string", "new_name.nii")

        # Checks that there is no workflow index
        self.assertIsNone(ppl_manager.workflow)

        # Mocks objects
        ppl_manager.init_clicked = True
        ppl_manager.ignore_node = True
        ppl_manager.key = {"item": "item_value"}
        ppl_manager.ignore = {"item": "item_value"}

        # Mocks methods
        ppl_manager.init_pipeline = Mock()
        # FIXME: if the method 'init_pipeline' is not mocked the whole
        #        test routine fails with a 'Segmentation Fault'

        # Initializes the pipeline
        ppl_manager.initialize()

        # Asserts that a workflow has been created
        # self.assertIsNotNone(ppl_manager.workflow)
        # from soma_workflow.client_types import Workflow
        # self.assertIsInstance(ppl_manager.workflow, Workflow)
        # FiXME: the above code else leads to 'Segmentation Fault'

        self.assertFalse(ppl_manager.ignore_node)
        self.assertEqual(len(ppl_manager.key), 0)
        self.assertEqual(len(ppl_manager.ignore), 0)
        ppl_manager.init_pipeline.assert_called_once_with()

        # Mocks an object to induce an exception
        ppl_manager.init_pipeline = None

        # Induces an exception in the pipeline initialization
        print("\n\n** an exception message is expected below")
        ppl_manager.initialize()

        self.assertFalse(ppl_manager.ignore_node)

    def test_register_completion_attributes(self):
        """Mocks methods of the pipeline manager and registers completion
        attributes.

        Since a method of the ProcessCompletionEngine class is mocked,
        this test may render the upcoming test routine unstable.

        - Tests: PipelineManagerTab.register_completion_attributes
        """

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Gets the path of one document
        folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "mia_ut_data",
            "resources",
            "mia",
            "project_8",
            "data",
            "raw_data",
        )

        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_"
            "Guerbet_Anat-RAREpvm-000220_000.nii"
        )
        NII_FILE_2 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        DOCUMENT_2 = os.path.abspath(os.path.join(folder, NII_FILE_2))

        # Adds a Select processes, creates the 'select_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Select)

        # Export plugs and sets their values
        print("\n\n** an exception message is expected below\n")
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()
        ppl.nodes[""].set_plug_value("inlist", [DOCUMENT_1, DOCUMENT_2])
        proj_dir = os.path.join(
            os.path.abspath(os.path.normpath(ppl_manager.project.folder)), ""
        )
        output_dir = os.path.join(proj_dir, "output_file.nii")
        ppl.nodes[""].set_plug_value("_out", output_dir)

        # Register completion without 'attributes'
        ppl_manager.register_completion_attributes(ppl)

        # Mocks 'get_capsul_engine' for the method not to throw an error
        # with the insertion of the upcoming mock
        capsul_engine = ppl_edt_tabs.get_capsul_engine()
        ppl_manager.get_capsul_engine = Mock(return_value=capsul_engine)

        # Mocks attributes values that are in the tags list
        attributes = {TAG_CHECKSUM: "Checksum_value"}
        (
            ProcessCompletionEngine.get_completion_engine(
                ppl
            ).get_attribute_values
        )().export_to_dict = Mock(return_value=attributes)

        # Register completion with mocked 'attributes'
        ppl_manager.register_completion_attributes(ppl)

    def test_register_node_io_in_database(self):
        """Adds a process, sets input and output parameters and registers them
        in database.

        - Tests: PipelineManagerTab._register_node_io_in_database
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_9")

        with self.main_window.project.database.data() as database_data:
            DOCUMENT_1 = database_data.get_document_names(COLLECTION_CURRENT)[
                0
            ]

        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )

        # Adds the processes Rename, creates the "rename_1" node
        process_class = Rename
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "rename_1"
        pipeline_editor_tabs.get_current_editor().current_node_name = (
            "rename_1"
        )
        (
            pipeline_editor_tabs.get_current_editor
        )().export_unconnected_mandatory_inputs()
        (
            pipeline_editor_tabs.get_current_editor
        )().export_all_unconnected_outputs()

        old_scan_name = DOCUMENT_1.split("/")[-1]
        new_scan_name = "new_name.nii"

        # Sets the mandatory plug values in the "inputs" node
        pipeline.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        pipeline.nodes[""].set_plug_value("format_string", new_scan_name)

        # Changes the "_out_file" in the "outputs" node
        pipeline.nodes[""].set_plug_value(
            "_out_file", DOCUMENT_1.replace(old_scan_name, new_scan_name)
        )

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_manager.workflow = workflow_from_pipeline(
            pipeline, complete_parameters=True
        )

        job = pipeline_manager.workflow.jobs[0]

        brick_id = str(uuid.uuid4())
        job.uuid = brick_id
        pipeline_manager.brick_list.append(brick_id)

        with pipeline_manager.project.database.data(
            write=True
        ) as database_data:
            database_data.add_document(COLLECTION_BRICK, brick_id)

        pipeline_manager._register_node_io_in_database(job, job.process())

        # Simulates a 'ProcessNode()' as 'process'
        process_node = ProcessNode(pipeline, "", job.process())
        pipeline_manager._register_node_io_in_database(job, process_node)

        # Simulates a 'PipelineNode()' as 'process'
        pipeline_node = PipelineNode(pipeline, "", job.process())
        pipeline_manager._register_node_io_in_database(job, pipeline_node)

        # Simulates a 'Switch()' as 'process'
        switch = Switch(pipeline, "", [""], [""])
        switch.completion_engine = None
        pipeline_manager._register_node_io_in_database(job, switch)

        # Simulates a list of outputs in 'process'
        job.process().list_outputs = []
        job.process().outputs = []
        pipeline_manager._register_node_io_in_database(job, job.process())

    def test_remove_progress(self):
        """Mocks an object of the pipeline manager and removes its progress.

        - Tests: PipelineManagerTab.remove_progress
        """

        ppl_manager = self.main_window.pipeline_manager

        # Mocks the 'progress' object
        ppl_manager.progress = RunProgress(ppl_manager)

        # Removes progress
        ppl_manager.remove_progress()

        # Asserts that the object 'progress' was deleted
        self.assertFalse(hasattr(ppl_manager, "progress"))

    def test_run(self):
        """Adds a process, creates a pipeline manager progress object and
        tries to run it while mocking methods of the pipeline manager.

        - Tests: RunWorker.run
        """
        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()
        folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "mia_ut_data",
            "resources",
            "mia",
            "project_8",
            "data",
            "raw_data",
        )
        # project_8_path = self.get_new_test_project()
        # ppl_manager.project.folder = project_8_path
        # folder = os.path.join(project_8_path, "data", "raw_data")
        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_"
            "Guerbet_Anat-RAREpvm-000220_000.nii"
        )

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Sets the mandatory parameters
        ppl.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        ppl.nodes[""].set_plug_value("format_string", "new_name.nii")

        # Creates a 'RunProgress' object
        ppl_manager.progress = RunProgress(ppl_manager)

        # Mocks a node that does not have a process and a node that has
        # a pipeline as a process
        ppl.nodes["switch"] = Switch(ppl, "", [""], [""])
        ppl.nodes["pipeline"] = ProcessNode(ppl, "pipeline", Pipeline())

        ppl_manager.progress.worker.run()

        # Mocks 'get_pipeline_or_process' to return a 'NipypeProcess' instead
        # of a 'Pipeline' and 'postprocess_pipeline_execution' to throw an
        # exception
        ppl_manager.progress = RunProgress(ppl_manager)
        # fmt: off
        (
            ppl_manager.progress.worker.pipeline_manager.
            get_pipeline_or_process
        ) = Mock(return_value=ppl.nodes["rename_1"].process)
        (
            ppl_manager.progress.worker.pipeline_manager.
            postprocess_pipeline_execution
        ) = Mock(side_effect=ValueError())
        # fmt: on
        # print("\n\n** an exception message is expected below\n")
        ppl_manager.progress.worker.run()

        # Mocks an interruption request
        ppl_manager.progress.worker.interrupt_request = True

        ppl_manager.progress.worker.run()

    def test_savePipeline(self):
        """Mocks methods of the pipeline manager and tries to save the pipeline
        over several conditions.

        -Tests: PipelineManagerTab.savePipeline
        """

        def click_yes(self_):
            """Blabla"""

            close_button = self_.button(QMessageBox.Yes)
            QTest.mouseClick(close_button, Qt.LeftButton)

        # Set shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        config = Config(properties_path=self.properties_path)
        ppl_path = os.path.join(
            config.get_properties_path(),
            "processes",
            "User_processes",
            "test_pipeline_1.py",
        )

        ppl_edt_tabs.get_current_editor()._pipeline_filename = ppl_path

        # Save pipeline as with empty filename, unchecked
        ppl_manager.savePipeline(uncheck=True)

        # Mocks 'savePipeline' from 'ppl_edt_tabs'
        ppl_edt_tabs.save_pipeline = Mock(return_value="not_empty")

        # Saves pipeline as with empty filename, checked
        ppl_manager.savePipeline(uncheck=True)

        # Sets the path to save the pipeline
        ppl_edt_tabs.get_current_editor()._pipeline_filename = ppl_path

        # Saves pipeline as with filled filename, uncheck
        ppl_manager.savePipeline(uncheck=True)

        # Mocks executing a dialog box and clicking close
        QMessageBox.exec = lambda self_, *args: self_.close()

        # Aborts pipeline saving with filled filename
        ppl_manager.savePipeline()

        # Mocks executing a dialog box and clicking yes
        QMessageBox.exec = click_yes

        # Accept pipeline saving with filled filename
        ppl_manager.savePipeline()

    def test_savePipelineAs(self):
        """Mocks a method from pipeline manager and saves a pipeline under
        another name.

        - Tests: PipelineManagerTab.savePipelineAs
        """

        # Set shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        # Saves pipeline with empty filename
        ppl_manager.savePipelineAs()

        # Mocks 'savePipeline' from 'ppl_edt_tabs'
        ppl_edt_tabs.save_pipeline = Mock(return_value="not_empty")

        # Saves pipeline with not empty filename
        ppl_manager.savePipelineAs()

    def test_set_anim_frame(self):
        """Runs the 'rotatingBrainVISA.gif' animation."""

        pipeline_manager = self.main_window.pipeline_manager

        config = Config()
        sources_images_dir = config.getSourceImageDir()
        self.assertTrue(sources_images_dir)  # if the string is not empty

        pipeline_manager._mmovie = QtGui.QMovie(
            os.path.join(sources_images_dir, "rotatingBrainVISA.gif")
        )
        pipeline_manager._set_anim_frame()

    def test_show_status(self):
        """Shows the status of the pipeline execution.

        Indirectly tests StatusWidget.__init__ and
        StatusWidget.toggle_soma_workflow.

        -Tests: PipelineManagerTab.test_show_status
        """

        # Set shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager

        # Shows the status of the pipeline's execution
        ppl_manager.show_status()

        self.assertIsNone(ppl_manager.status_widget.swf_widget)

        # Creates 'ppl_manager.status_widget.swf_widget', not visible by
        # default (the argument is irrelevant)
        ppl_manager.status_widget.toggle_soma_workflow(False)

        # Asserts that 'swf_widget' has been created and is visible
        self.assertIsNotNone(ppl_manager.status_widget.swf_widget)
        self.assertFalse(ppl_manager.status_widget.swf_widget.isVisible())

        # Toggles visibility on
        ppl_manager.status_widget.toggle_soma_workflow(False)
        self.assertFalse(ppl_manager.status_widget.swf_widget.isVisible())

        # Toggles visibility off
        ppl_manager.status_widget.toggle_soma_workflow(True)
        self.assertTrue(ppl_manager.status_widget.swf_widget.isVisible())

    def test_stop_execution(self):
        """Shows the status window of the pipeline manager.

        - Tests: PipelineManagerTab.test_show_status
        """

        # Set shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager

        # Creates a 'RunProgress' object
        ppl_manager.progress = RunProgress(ppl_manager)

        ppl_manager.stop_execution()

        self.assertTrue(ppl_manager.progress.worker.interrupt_request)

    def test_undo_redo(self):
        """Tests the undo/redo action."""

        config = Config(properties_path=self.properties_path)
        controlV1_ver = config.isControlV1()

        # Switch to V1 node controller GUI, if necessary
        if not controlV1_ver:
            config.setControlV1(True)
            self.restart_MIA()

        # Set shortcuts for objects that are often used
        pipeline_manager = self.main_window.pipeline_manager
        pipeline_editor_tabs = (
            self.main_window.pipeline_manager.pipelineEditorTabs
        )

        # Creates a new project folder and adds one document to the
        # project
        # test_proj_path = self.get_new_test_project()
        # folder = os.path.join(test_proj_path, 'data', 'raw_data')
        # NII_FILE_1 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-
        #                      '04-G3_Guerbet_MDEFT-MDEFTpvm-000940_800.nii')
        # DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Creates a project with another project already opened
        # self.main_window.data_browser.table_data.add_path()

        # pop_up_add_path = (self.main_window.data_browser.
        #                                         table_data.pop_up_add_path)

        # pop_up_add_path.file_line_edit.setText(DOCUMENT_1)
        # pop_up_add_path.save_path()

        # self.main_window.undo()

        # self.main_window.redo()

        # Mocks not saving the pipeline
        # QMessageBox.exec = lambda self_, *arg: self_.buttons(
        #                                                  )[-1].clicked.emit()

        # Switches to pipeline manager
        self.main_window.tabs.setCurrentIndex(2)

        # Add a Smooth process => creates a node called "smooth_1",
        # test if Smooth_1 is a node in the current pipeline / editor
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        # Undo (remove the node), test if the node was removed
        pipeline_manager.undo()
        self.assertFalse("smooth_1" in pipeline.nodes.keys())

        # Redo (add again the node), test if the node was added
        pipeline_manager.redo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        # Delete the node, test if the node was removed
        pipeline_editor_tabs.get_current_editor().current_node_name = (
            "smooth_1"
        )
        pipeline_editor_tabs.get_current_editor().del_node()
        self.assertFalse("smooth_1" in pipeline.nodes.keys())

        # Undo (add again the node), test if the node was added
        pipeline_manager.undo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        # Redo (delete again the node), test if the node was removed
        pipeline_manager.redo()
        self.assertFalse("smooth1" in pipeline.nodes.keys())

        # Adding a new Smooth process => creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        # Export the "out_prefix" plug as "prefix_smooth" in Input node, test
        # if the Input node have a prefix_smooth plug
        pipeline_editor_tabs.get_current_editor()._export_plug(
            temp_plug_name=("smooth_1", "out_prefix"),
            pipeline_parameter="prefix_smooth",
            optional=False,
            weak_link=False,
        )
        self.assertTrue("prefix_smooth" in pipeline.nodes[""].plugs.keys())

        # Undo (remove prefix_smooth from Input node),
        # test if the prefix_smooth plug was deleted from Input node
        pipeline_manager.undo()
        self.assertFalse("prefix_smooth" in pipeline.nodes[""].plugs.keys())

        # redo (export again the "out_prefix" plug),
        # test if the Input node have a prefix_smooth plug
        pipeline_manager.redo()
        self.assertTrue("prefix_smooth" in pipeline.nodes[""].plugs.keys())

        # Delete the "prefix_smooth" plug from the Input node,
        # test if the Input node have not a prefix_smooth plug
        pipeline_editor_tabs.get_current_editor()._remove_plug(
            _temp_plug_name=("inputs", "prefix_smooth")
        )
        self.assertFalse("prefix_smooth" in pipeline.nodes[""].plugs.keys())

        # Undo (export again the "out_prefix" plug),
        # test if the Input node have a prefix_smooth plug
        pipeline_manager.undo()
        self.assertTrue("prefix_smooth" in pipeline.nodes[""].plugs.keys())

        # redo (deleting the "prefix_smooth" plug from the Input node),
        # test if the Input node have not a prefix_smooth plug
        pipeline_manager.redo()
        self.assertFalse("prefix_smooth" in pipeline.nodes[""].plugs.keys())

        # FIXME: export_plugs (currently there is a bug if a plug is
        #        of type list)

        # Adding a new Smooth process => creates a node called "smooth_2"
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 550)
        pipeline_editor_tabs.get_current_editor().add_named_process(
            process_class
        )

        # Adding a link
        pipeline_editor_tabs.get_current_editor().add_link(
            ("smooth_1", "_smoothed_files"),
            ("smooth_2", "in_files"),
            active=True,
            weak=False,
        )

        # test if the 2 nodes have the good links
        self.assertEqual(
            1, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Undo (remove the link), test if the 2 nodes have not the links
        pipeline_manager.undo()
        self.assertEqual(
            0, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            0,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Redo (add again the link), test if the 2 nodes have the good links
        pipeline_manager.redo()
        self.assertEqual(
            1, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Removing the link, test if the 2 nodes have not the links
        link = "smooth_1._smoothed_files->smooth_2.in_files"
        pipeline_editor_tabs.get_current_editor()._del_link(link)
        self.assertEqual(
            0, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            0,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Undo (add again the link), test if the 2 nodes have the good links
        pipeline_manager.undo()
        self.assertEqual(
            1, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Redo (remove the link), test if the 2 nodes have not the links
        pipeline_manager.redo()
        self.assertEqual(
            0, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            0,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Re-adding a link
        pipeline_editor_tabs.get_current_editor().add_link(
            ("smooth_1", "_smoothed_files"),
            ("smooth_2", "in_files"),
            active=True,
            weak=False,
        )

        # Updating the node name
        process = pipeline.nodes["smooth_2"].process
        pipeline_manager.displayNodeParameters("smooth_2", process)
        node_controller = self.main_window.pipeline_manager.nodeController
        node_controller.display_parameters("smooth_2", process, pipeline)
        node_controller.line_edit_node_name.setText("my_smooth")
        keyEvent = QtGui.QKeyEvent(
            QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier
        )
        QCoreApplication.postEvent(
            node_controller.line_edit_node_name, keyEvent
        )
        QTest.qWait(100)

        # test if the smooth_2 node has been replaced by the
        # my_smooth node and test the links
        self.assertTrue("my_smooth" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertEqual(
            1, len(pipeline.nodes["my_smooth"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Undo (Updating the node name from my_smooth to smooth_2),
        # test if it's ok
        pipeline_manager.undo()
        QTest.qWait(100)
        self.assertFalse("my_smooth" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())
        self.assertEqual(
            1, len(pipeline.nodes["smooth_2"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Redo (Updating the node name from smooth_2 to my_smooth),
        # test if it's ok
        pipeline_manager.redo()
        QTest.qWait(100)
        self.assertTrue("my_smooth" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertEqual(
            1, len(pipeline.nodes["my_smooth"].plugs["in_files"].links_from)
        )
        self.assertEqual(
            1,
            len(pipeline.nodes["smooth_1"].plugs["_smoothed_files"].links_to),
        )

        # Updating a plug value
        if hasattr(node_controller, "get_index_from_plug_name"):
            index = node_controller.get_index_from_plug_name(
                "out_prefix", "in"
            )
            node_controller.line_edit_input[index].setText("PREFIX")
            node_controller.update_plug_value(
                "in", "out_prefix", pipeline, str
            )

            self.assertEqual(
                "PREFIX",
                pipeline.nodes["my_smooth"].get_plug_value("out_prefix"),
            )

            self.main_window.undo()
            self.assertEqual(
                "s", pipeline.nodes["my_smooth"].get_plug_value("out_prefix")
            )

            self.main_window.redo()
            self.assertEqual(
                "PREFIX",
                pipeline.nodes["my_smooth"].get_plug_value("out_prefix"),
            )

        # Switches back to node controller V2, if necessary (return to initial
        # state)
        config = Config(properties_path=self.properties_path)

        if not controlV1_ver:
            config.setControlV1(False)

    def test_update_auto_inheritance(self):
        """Adds a process and updates the job's auto inheritance dict.

        - Tests: PipelineManagerTab.update_auto_inheritance
        """

        project_8_path = self.get_new_test_project()
        folder = os.path.join(
            project_8_path,
            "data",
            "raw_data",
        )

        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_"
            "Guerbet_Anat-RAREpvm-000220_000.nii"
        )
        NII_FILE_2 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )

        DOCUMENT_1 = os.path.realpath(os.path.join(folder, NII_FILE_1))
        DOCUMENT_2 = os.path.realpath(os.path.join(folder, NII_FILE_2))

        # Set shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        ppl.nodes["rename_1"].set_plug_value("in_file", DOCUMENT_1)
        node = ppl.nodes["rename_1"]

        # Initializes the workflow manually
        ppl_manager.workflow = workflow_from_pipeline(
            ppl, complete_parameters=True
        )

        job = ppl_manager.workflow.jobs[0]

        # Mocks the node's parameters
        node.auto_inheritance_dict = {}
        process = node.process

        real_project = Mock()
        fake_db_data = Mock()
        fake_db_data.has_document.return_value = True

        @contextmanager
        def fake_data_cm():
            """
            Context manager that yields mock database data for testing
            purposes.

            :yields: The fake database data object used in tests.
            """
            yield fake_db_data

        real_project.database = Mock()
        real_project.database.data = fake_data_cm

        process.study_config.project = real_project
        process.study_config.project.folder = os.path.dirname(project_8_path)
        process.outputs = []
        process.list_outputs = []
        process.auto_inheritance_dict = {}

        # Mocks 'job.param_dict' to share items with both the inputs and
        # outputs list of the process
        # Note: only 'in_file' and '_out_file' are file trait types
        job.param_dict["_out_file"] = "_out_file_value"

        ppl_manager.update_auto_inheritance(node, job)

        # 'job.param_dict' as list of objects
        job.param_dict["inlist"] = [DOCUMENT_1, DOCUMENT_2]
        process.get_outputs = Mock(return_value={"_out": ["_out_value"]})
        process.add_trait(
            "_out", OutputMultiPath(File(exists=True), desc="out files")
        )
        job.param_dict["_out"] = ["_out_value"]
        ppl_manager.update_auto_inheritance(node, job)

        # 'node' does not have a 'project'
        del node.process.study_config.project
        ppl_manager.update_auto_inheritance(node, job)

        # 'node' is not a 'Process'
        node = {}
        ppl_manager.update_auto_inheritance(node, job)

    def test_update_inheritance(self):
        """Adds a process and updates the job's inheritance dict.

        - Tests: PipelineManagerTab.update_inheritance
        """

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        node = ppl.nodes["rename_1"]

        # Initializes the workflow manually
        ppl_manager.workflow = workflow_from_pipeline(
            ppl, complete_parameters=True
        )

        # Gets the 'job' and mocks adding a brick to the collection
        job = ppl_manager.workflow.jobs[0]

        # Node's name does not contains 'Pipeline'
        node.context_name = ""
        node.process.inheritance_dict = {"item": "value"}
        ppl_manager.project.node_inheritance_history = {}
        ppl_manager.update_inheritance(job, node)

        self.assertEqual(job.inheritance_dict, {"item": "value"})

        # Node's name contains 'Pipeline'
        node.context_name = "Pipeline.rename_1"
        ppl_manager.update_inheritance(job, node)

        self.assertEqual(job.inheritance_dict, {"item": "value"})

        # Node's name in 'node_inheritance_history'
        (ppl_manager.project.node_inheritance_history["rename_1"]) = [
            {0: "new_value"}
        ]
        ppl_manager.update_inheritance(job, node)

        self.assertEqual(job.inheritance_dict, {0: "new_value"})

    def test_update_node_list(self):
        """Adds a process, exports input and output plugs, initializes a
        workflow and adds the process to the "pipline_manager.node_list".

        - Tests: PipelineManagerTab.update_node_list
        """

        # Set shortcuts for often used objects
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        process_class = Rename
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory inputs and outputs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = "rename_1"
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Initializes the workflow
        ppl_manager.workflow = workflow_from_pipeline(
            pipeline, complete_parameters=True
        )

        # Asserts that the "node_list" is empty by default
        node_list = self.main_window.pipeline_manager.node_list
        self.assertEqual(len(node_list), 0)

        # Asserts that the process "Rename" was added to "node_list"
        ppl_manager.update_node_list()
        self.assertEqual(len(node_list), 1)
        self.assertEqual(node_list[0]._nipype_class, "Rename")

    def test_z_init_pipeline(self):
        """Adds a process, mocks several parameters from the pipeline
        manager and initializes the pipeline.

        - Tests: PipelineManagerTab.init_pipeline
        """

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Gets the path of one document
        folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "mia_ut_data",
            "resources",
            "mia",
            "project_8",
            "data",
            "raw_data",
        )

        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_"
            "Guerbet_Anat-RAREpvm-000220_000.nii"
        )

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Verifies that all the processes were added
        self.assertEqual(["", "rename_1"], ppl.nodes.keys())

        # Initialize the pipeline with missing mandatory parameters
        ppl_manager.workflow = workflow_from_pipeline(
            ppl, complete_parameters=True
        )

        # Mocks executing a dialog box, instead shows it
        QMessageBox.exec = lambda self_, *args: self_.show()

        ppl_manager.update_node_list()
        init_result = ppl_manager.init_pipeline()
        ppl_manager.msg.accept()
        self.assertFalse(init_result)

        # Sets the mandatory parameters
        ppl.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        ppl.nodes[""].set_plug_value("format_string", "new_name.nii")

        # Mocks an iteration pipeline
        ppl.name = "Iteration_pipeline"
        process_it = ProcessIteration(ppl.nodes["rename_1"].process, "")
        ppl.list_process_in_pipeline.append(process_it)

        # Initialize the pipeline with mandatory parameters set
        # QTimer.singleShot(1000, self.execute_QDialogAccept)
        # init_result = ppl_manager.init_pipeline(pipeline=ppl)
        # ppl_manager.msg.accept()

        # Mocks requirements to {} and initializes the pipeline
        ppl_manager.check_requirements = Mock(return_value={})
        init_result = ppl_manager.init_pipeline()
        ppl_manager.msg.accept()
        self.assertFalse(init_result)
        # ppl_manager.check_requirements.assert_called_once_with(
        #    "global", message_list=[]
        # )
        ppl_manager.check_requirements.assert_called_once()
        # Mocks external packages as requirements and initializes the pipeline
        pkgs = ["fsl", "afni", "ants", "matlab", "mrtrix", "spm"]
        req = {"capsul_engine": {"uses": Mock()}}

        for pkg in pkgs:
            req[f"capsul.engine.module.{pkg}"] = {"directory": False}

        req["capsul_engine"]["uses"].get = Mock(return_value=1)
        proc = Mock()
        proc.context_name = "moke_process"
        req = {proc: req}
        ppl_manager.check_requirements = Mock(return_value=req)

        # QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        ppl_manager.msg.accept()
        self.assertFalse(init_result)

        # Extra steps for SPM
        req[proc]["capsul.engine.module.spm"]["directory"] = True
        req[proc]["capsul.engine.module.spm"]["standalone"] = True
        Config().set_matlab_standalone_path(None)

        # QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        ppl_manager.msg.accept()
        self.assertFalse(init_result)

        req[proc]["capsul.engine.module.spm"]["standalone"] = False

        # QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        ppl_manager.msg.accept()
        self.assertFalse(init_result)

        # Deletes an attribute of each package requirement
        for pkg in pkgs:
            del req[proc][f"capsul.engine.module.{pkg}"]

        # QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        ppl_manager.msg.accept()
        self.assertFalse(init_result)

        # Mocks a 'ValueError' in 'workflow_from_pipeline'
        ppl.find_empty_parameters = Mock(side_effect=ValueError)

        # QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        ppl_manager.msg.accept()
        self.assertFalse(init_result)

    def test_z_runPipeline(self):
        """Adds a process, export plugs and runs a pipeline.

        - Tests:
            - PipelineManagerTab.runPipeline
            - PipelineManagerTab.finish_execution
            - RunProgress
            - RunWorker
        """
        # Set shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Creates a new project folder and adds one document to the
        # project, sets the plug value that is added to the database
        project_8_path = self.get_new_test_project()
        ppl_manager.project.folder = project_8_path
        folder = os.path.join(project_8_path, "data", "raw_data")
        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )
        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Switches to pipeline manager tab
        self.main_window.tabs.setCurrentIndex(2)

        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Sets the mandatory parameters
        ppl.nodes[""].set_plug_value("in_file", DOCUMENT_1)
        ppl.nodes[""].set_plug_value("format_string", "new_name.nii")

        # Test successful pipeline run with patched thread start
        with (
            patch.object(QDialog, "exec_", return_value=QDialog.Accepted),
            patch(
                "populse_mia.user_interface.pipeline_manager."
                "pipeline_manager_tab.RunWorker.start"
            ) as mock_start,
        ):
            ppl_manager.runPipeline()

            self.assertEqual(ppl_manager.last_run_pipeline, ppl)
            mock_start.assert_called_once()

            # Wait for the worker's finished signal
            worker = ppl_manager.progress.worker

            if worker:  # Ensure worker was actually created
                spy = QSignalSpy(worker.finished)
                worker.finished.emit()  # simulate finish if needed
                spy.wait(1000)
                self.assertGreaterEqual(
                    len(spy), 1, "Worker did not emit 'finished'"
                )

            if hasattr(ppl_manager, "progress") and ppl_manager.progress:
                self.assertIsNone(
                    ppl_manager.progress.worker,
                    "Worker was not cleared after execution",
                )

        # Test pipeline run with manual interruption
        # (simulate failure before execution)
        with (
            patch.object(QDialog, "exec_", return_value=QDialog.Accepted),
            patch(
                "populse_mia.user_interface.pipeline_manager."
                "pipeline_manager_tab.RunWorker.start"
            ) as mock_start,
        ):
            ppl_manager.runPipeline()
            ppl_manager.stop_execution()

            # Simulate the worker finishing
            worker = ppl_manager.progress.worker

            if worker:
                spy = QSignalSpy(worker.finished)
                worker.finished.emit()
                spy.wait(1000)
                self.assertGreaterEqual(
                    len(spy), 1, "Worker did not emit 'finished'"
                )

            if hasattr(ppl_manager, "progress") and ppl_manager.progress:
                self.assertIsNone(
                    ppl_manager.progress.worker,
                    "Worker was not cleared after execution",
                )

    def test_zz_del_pack(self):
        """We remove the brick created during the unit tests, and we take
        advantage of this to cover the part of the code used to remove the
        packages"""

        pkg = PackageLibraryDialog(self.main_window)

        # The Test_pipeline brick was added in the package library
        self.assertTrue(
            "Test_pipeline_1"
            in pkg.package_library.package_tree["User_processes"]
        )

        pkg.delete_package(
            to_delete="User_processes.Test_pipeline_1", loop=True
        )

        # The Test_pipeline brick has been removed from the package library
        self.assertFalse(
            "Test_pipeline_1"
            in pkg.package_library.package_tree["User_processes"]
        )


if __name__ == "__main__":
    # Install the custom Qt message handler
    qInstallMessageHandler(qt_message_handler)
    unittest.main()
