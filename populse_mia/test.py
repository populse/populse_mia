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
from datetime import datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from time import sleep
from unittest.mock import MagicMock, Mock

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
from PyQt5 import QtGui
from PyQt5.QtCore import (
    QT_VERSION_STR,
    QCoreApplication,
    QEvent,
    QModelIndex,
    QPoint,
    Qt,
    QThread,
    QTimer,
    qInstallMessageHandler,
)
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QTableWidgetItem,
)
from traits.api import TraitListObject, Undefined

# The following statement is currently commented because it has no effect and
# can be replaced by a function call to have an effect, e.g. sys.settrace()
# sys.settrace

uts_dir = os.path.isdir(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
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

if (
    not os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    in sys.path
):
    # "developer" mode
    os.environ["MIA_DEV_MODE"] = "1"
    root_dev_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    )

    # Adding populse_mia
    print('\n- Unit testing in "developer" mode\n')

    if os.path.isdir(os.path.join(root_dev_dir, "populse-mia")):
        mia_dev_dir = os.path.join(root_dev_dir, "populse-mia")

    else:
        mia_dev_dir = os.path.join(root_dev_dir, "populse_mia")

    print("- Using populse_mia package from {} " "...".format(mia_dev_dir))
    sys.path.insert(0, mia_dev_dir)
    del mia_dev_dir

    # Adding mia_processes:
    if os.path.isdir(os.path.join(root_dev_dir, "mia_processes")):
        mia_processes_dev_dir = os.path.join(root_dev_dir, "mia_processes")
        print(
            "- Using mia_processes package from {} "
            "...".format(mia_processes_dev_dir)
        )
        sys.path.insert(1, mia_processes_dev_dir)
        del mia_processes_dev_dir

    # Adding populse_db:
    if os.path.isdir(os.path.join(root_dev_dir, "populse_db")):
        populse_db_dev_dir = os.path.join(root_dev_dir, "populse_db", "python")
        print(
            "- Using populse_db package from {} "
            "...".format(populse_db_dev_dir)
        )
        sys.path.insert(1, populse_db_dev_dir)
        del populse_db_dev_dir

    # Adding capsul:
    if os.path.isdir(os.path.join(root_dev_dir, "capsul")):
        capsul_dev_dir = os.path.join(root_dev_dir, "capsul")
        print(f"- Using capsul package from {capsul_dev_dir} ...")
        sys.path.insert(1, capsul_dev_dir)
        del capsul_dev_dir

    # Adding soma-base:
    if os.path.isdir(os.path.join(root_dev_dir, "soma-base")):
        soma_base_dev_dir = os.path.join(root_dev_dir, "soma-base", "python")
        print(
            "- Using soma-base package from {} "
            "...".format(soma_base_dev_dir)
        )
        sys.path.insert(1, soma_base_dev_dir)
        del soma_base_dev_dir

    # Adding soma-workflow:
    if os.path.isdir(os.path.join(root_dev_dir, "soma-workflow")):
        soma_workflow_dev_dir = os.path.join(
            root_dev_dir, "soma-workflow", "python"
        )
        print(
            "- Using soma-workflow package from {} "
            "...".format(soma_workflow_dev_dir)
        )
        sys.path.insert(1, soma_workflow_dev_dir)
        del soma_workflow_dev_dir

else:
    os.environ["MIA_DEV_MODE"] = "0"

# Imports after defining the location of populse packages in the case of a
# developer configuration:

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
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    COLLECTION_HISTORY,
    COLLECTION_INITIAL,
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
    TAG_BRICKS,
    TAG_CHECKSUM,
    TAG_EXP_TYPE,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_ORIGIN_USER,
    TAG_TYPE,
    TYPE_NII,
)

# Populse_mia import
from populse_mia.data_manager.data_loader import (  # noqa: E402
    ImportProgress,
    ImportWorker,
)
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
    PopUpSelectTag,
    PopUpSelectTagCountTable,
)
from populse_mia.utils import (  # noqa: E402
    check_value_type,
    table_to_database,
    verify_processes,
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
            - edit_databrowser_list: change value for a tag in DataBrowser
            - execute_QDialogAccept: accept (close) a QDialog instance
            - execute_QDialogClose: closes a QDialog instance
            - execute_QMessageBox_clickClose: press the Close button of
              a QMessageBox instance
            - execute_QMessageBox_clickOk: press the Ok button of a
              QMessageBox instance
            - execute_QMessageBox_clickYes: press the Yes button of a
              QMessageBox instance
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

        w = QApplication.activeWindow()

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
        """Creates a mocked java (.jar) executable.

        :param path: the full path of the executable, ending by '.jar'

        :return: 0 if success or 1 if failure
        """

        (folder, name) = os.path.split(path)

        CONTENT = (
            "public class MockApp {\n"
            + "    public static void main(String[] args){\n"
            + '        System.out.println("Executed mock java app.");\n'
            + "    }\n"
            + "}"
        )

        # Creates the .java source code
        with open(os.path.join(folder, "MockApp.java"), "w") as file:
            file.write(CONTENT)

        # Creates the MANIFEST file
        with open(os.path.join(folder, "MANIFEST.MF"), "w") as file:
            file.write("Main-Class:  MockApp\n")
        # The build only works with the '\n' at the end of the manifest

        # Check if the OpenJDK Runtime (java) is installed
        try:
            subprocess.run(["java", "-version"])

        except FileNotFoundError:
            print("OpenJDK Runtime is not installed")
            return 1

        # Compile and pack
        subprocess.run(["javac", "-d", ".", "MockApp.java"], cwd=folder)
        subprocess.run(
            ["jar", "cvmf", "MANIFEST.MF", name, "MockApp.class"], cwd=folder
        )

        if not os.path.exists(path):
            print("The java executable was not created")
            return 1

        return 0

    def edit_databrowser_list(self, value):
        """Change value for a tag in DataBrowser.

        :param value: the new value
        """

        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            item = w.table.item(0, 0)
            item.setText(value)
            w.update_table_values(True)

    def execute_QDialogAccept(self):
        """Accept (close) a QDialog window."""

        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            w.accept()

    # def execute_QDialogClose(self):
    #     """Close a QDialog window.
    #
    #     Currently, this method is not used.
    #     """
    #
    #     w = QApplication.activeWindow()
    #
    #     if isinstance(w, QDialog):
    #         w.close()

    # def execute_QMessageBox_clickClose(self):
    #     """Press the Close button of a QMessageBox instance.
    #
    #     Currently, this method is not used.
    #     """
    #
    #     w = QApplication.activeWindow()
    #
    #     if isinstance(w, QMessageBox):
    #         close_button = w.button(QMessageBox.Close)
    #         QTest.mouseClick(close_button, Qt.LeftButton)

    def execute_QMessageBox_clickOk(self):
        """Press the Ok button of a QMessageBox instance."""

        w = QApplication.activeWindow()

        if isinstance(w, QMessageBox):
            close_button = w.button(QMessageBox.Ok)
            QTest.mouseClick(close_button, Qt.LeftButton)

    # def execute_QMessageBox_clickYes(self):
    #     """Press the Yes button of a QMessageBox instance.
    #
    #     Currently, this method is not used.
    #     """
    #
    #     w = QApplication.activeWindow()
    #
    #     if isinstance(w, QMessageBox):
    #         close_button = w.button(QMessageBox.Yes)
    #         QTest.mouseClick(close_button, Qt.LeftButton)

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
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
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
                3
            ].itemAt(1).widget().clicked.emit()

        elif init_state == "nipype":
            pkg_lib_window.line_edit.setText("nipype.interfaces")
            # Clicks on remove package
            pkg_lib_window.layout().children()[0].layout().children()[
                3
            ].itemAt(1).widget().clicked.emit()

        elif init_state == "nipype.interfaces":
            pkg_lib_window.line_edit.setText("nipype.interfaces.DataGrabber")
            # Clicks on remove package
            pkg_lib_window.layout().children()[0].layout().children()[
                3
            ].itemAt(1).widget().clicked.emit()

        else:
            pkg_lib_window.line_edit.setText("nipype.interfaces.DataGrabber")
            # Clicks on add package
            pkg_lib_window.layout().children()[0].layout().children()[
                3
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
            QApplication.processEvents()

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

        # Removing the opened projects (in CI, the tests are run twice)
        config = Config(properties_path=self.properties_path)
        config.set_opened_projects([])
        config.saveConfig()
        QApplication.processEvents()
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


class TestMIADataBrowser(TestMIACase):
    """Tests for the data browser tab (DataBrowser).

    :Contains:
        :Method:
            - test_add_path: tests the popup to add a path
            - test_add_tag: tests the pop up adding a tag
            - test_advanced_search: tests the advanced search widget
            - test_brick_history: tests the brick history popup
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
            - test_update_data_history: updates the history of data that
              have been re-written
            - test_update_default_value: updates the values when a list
              of default values is created
            - test_utils: test the utils functions
            - test_visualized_tags: tests the popup modifying the
              visualized tags
    """

    def test_add_path(self):
        """Tries import a document to the project.

        - Tests: DataBrowser.add_path and PopUpAddPath

        - Mocks: the execution of QFileDialog and QMessageBox
        """

        # Sets shortcuts for often used objects
        ppl_manager = self.main_window.pipeline_manager
        session = ppl_manager.project.session
        table_data = self.main_window.data_browser.table_data

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

        # Mocks the execution of a message box
        QMessageBox.show = Mock()

        # Opens the 'add_path' pop-up
        self.main_window.data_browser.table_data.add_path()
        add_path = self.main_window.data_browser.table_data.pop_up_add_path

        # Tries to add a document without filling the pop-up fields
        QTest.mouseClick(add_path.ok_button, Qt.LeftButton)
        self.assertEqual(add_path.msg.text(), "Invalid arguments")

        # Tries to add invalid document path
        add_path.file_line_edit.setText(str([DOCUMENT_1 + "_"]))
        add_path.type_line_edit.setText(str([TYPE_NII]))
        QTest.mouseClick(add_path.ok_button, Qt.LeftButton)
        self.assertEqual(add_path.msg.text(), "Invalid arguments")

        # Adds a valid document path
        add_path.file_line_edit.setText(str([DOCUMENT_1]))
        add_path.type_line_edit.setText(str([TYPE_NII]))
        QTest.mouseClick(add_path.ok_button, Qt.LeftButton)

        # Asserts that the document was added into the data browser
        # A regular '.split('/')' will not work in Windows OS
        filename = os.path.split(
            session.get_documents_names(COLLECTION_CURRENT)[0]
        )[-1]
        self.assertTrue(filename in DOCUMENT_1)

        self.assertEqual(table_data.rowCount(), 1)

        # Mocks the execution of file dialog box and finds the file type
        for ext in ["nii", "mat", "txt"]:
            QFileDialog.getOpenFileNames = Mock(
                return_value=(["file." + ext], "All Files (*)")
            )
            add_path.file_to_choose()

        # Adds a document into the database and tries to save the same
        # one once again
        self.project.session.add_document(COLLECTION_CURRENT, DOCUMENT_1)
        add_path.file_line_edit.setText(str([DOCUMENT_1]))
        add_path.save_path()

    def test_add_tag(self):
        """Tests the pop-up adding a tag."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Mocks the execution of a dialog box and clicking close
        QMessageBox.exec = lambda self_, *args: self_.close()

        # Testing without tag name
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        # QTimer.singleShot(1000, self.execute_QMessageBox_clickClose)
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(add_tag.msg.text(), "The tag name cannot be empty")

        QApplication.processEvents()

        # Testing with tag name already existing
        add_tag.text_edit_tag_name.setText("Type")
        # QTimer.singleShot(1000, self.execute_QMessageBox_clickClose)
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(add_tag.msg.text(), "This tag name already exists")

        QApplication.processEvents()

        # Testing with wrong type
        add_tag.text_edit_tag_name.setText("Test")
        add_tag.combo_box_type.setCurrentText(FIELD_TYPE_INTEGER)
        add_tag.type = FIELD_TYPE_INTEGER
        add_tag.text_edit_default_value.setText("Should be integer")
        # QTimer.singleShot(1000, self.execute_QMessageBox_clickClose)
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(add_tag.msg.text(), "Invalid default value")

        QApplication.processEvents()

        # Testing when everything is ok
        add_tag.text_edit_tag_name.setText("Test")
        add_tag.text_edit_default_value.setText("def_value")
        add_tag.type = FIELD_TYPE_STRING

        QTest.qWait(500)

        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        for document in self.main_window.project.session.get_documents_names(
            COLLECTION_CURRENT
        ):
            self.assertEqual(
                self.main_window.project.session.get_value(
                    COLLECTION_CURRENT, document, "Test"
                ),
                "def_value",
            )

        for document in self.main_window.project.session.get_documents_names(
            COLLECTION_INITIAL
        ):
            self.assertEqual(
                self.main_window.project.session.get_value(
                    COLLECTION_INITIAL, document, "Test"
                ),
                "def_value",
            )

        test_column = self.main_window.data_browser.table_data.get_tag_column(
            "Test"
        )

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(
                row, test_column
            )
            self.assertEqual(item.text(), "def_value")

        QApplication.processEvents()

        # Testing with list type
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        add_tag.text_edit_tag_name.setText("Test_list")

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

        add_tag.combo_box_type.setCurrentText("Integer List")
        QTest.mouseClick(add_tag.text_edit_default_value, Qt.LeftButton)
        QTest.mouseClick(
            add_tag.text_edit_default_value.list_creation.add_element_label,
            Qt.LeftButton,
        )
        table = add_tag.text_edit_default_value.list_creation.table
        item = QTableWidgetItem()
        item.setText(str(1))
        table.setItem(0, 0, item)
        item = QTableWidgetItem()
        item.setText(str(2))
        table.setItem(0, 1, item)
        item = QTableWidgetItem()
        item.setText(str(3))
        table.setItem(0, 2, item)

        QTest.qWait(500)

        QTest.mouseClick(
            add_tag.text_edit_default_value.list_creation.ok_button,
            Qt.LeftButton,
        )
        self.assertEqual(add_tag.text_edit_default_value.text(), "[1, 2, 3]")
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)

        test_list_column = (
            self.main_window.data_browser.table_data.get_tag_column(
                "Test_list"
            )
        )

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(
                row, test_list_column
            )
            self.assertEqual(item.text(), "[1, 2, 3]")

        QApplication.processEvents()

    def test_advanced_search(self):
        """Tests the advanced search widget."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )

        QTest.mouseClick(
            self.main_window.data_browser.advanced_search_button, Qt.LeftButton
        )

        # Testing - and + buttons
        self.assertEqual(
            1, len(self.main_window.data_browser.advanced_search.rows)
        )
        first_row = self.main_window.data_browser.advanced_search.rows[0]
        QTest.mouseClick(first_row[6], Qt.LeftButton)
        self.assertEqual(
            2, len(self.main_window.data_browser.advanced_search.rows)
        )
        second_row = self.main_window.data_browser.advanced_search.rows[1]
        QTest.mouseClick(second_row[5], Qt.LeftButton)
        self.assertEqual(
            1, len(self.main_window.data_browser.advanced_search.rows)
        )
        first_row = self.main_window.data_browser.advanced_search.rows[0]
        QTest.mouseClick(first_row[5], Qt.LeftButton)
        self.assertEqual(
            1, len(self.main_window.data_browser.advanced_search.rows)
        )

        field = self.main_window.data_browser.advanced_search.rows[0][2]
        condition = self.main_window.data_browser.advanced_search.rows[0][3]
        value = self.main_window.data_browser.advanced_search.rows[0][4]
        field_filename_index = field.findText(TAG_FILENAME)
        field.setCurrentIndex(field_filename_index)
        condition_contains_index = condition.findText("CONTAINS")
        condition.setCurrentIndex(condition_contains_index)
        value.setText("G1")
        QTest.mouseClick(
            self.main_window.data_browser.advanced_search.search, Qt.LeftButton
        )

        # Testing that only G1 scans are displayed with the filter applied
        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 2)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )

        # Testing that every scan is back when clicking again on
        # advanced search
        QTest.mouseClick(
            self.main_window.data_browser.advanced_search_button, Qt.LeftButton
        )
        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )

    def test_brick_history(self):
        """Tests the brick history popup."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        bricks_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("History")
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
        self.assertEqual(brick_table.horizontalHeaderItem(0).text(), "Name")
        self.assertEqual(brick_table.horizontalHeaderItem(1).text(), "Init")
        self.assertEqual(
            brick_table.horizontalHeaderItem(2).text(), "Init Time"
        )
        self.assertEqual(brick_table.horizontalHeaderItem(3).text(), "Exec")
        self.assertEqual(
            brick_table.horizontalHeaderItem(4).text(), "Exec Time"
        )
        self.assertEqual(
            brick_table.horizontalHeaderItem(5).text(), "data_type"
        )
        self.assertEqual(brick_table.horizontalHeaderItem(6).text(), "fwhm")
        self.assertEqual(
            brick_table.horizontalHeaderItem(7).text(), "implicit_masking"
        )
        self.assertEqual(
            brick_table.horizontalHeaderItem(8).text(), "in_files"
        )
        self.assertEqual(
            brick_table.horizontalHeaderItem(9).text(), "matlab_cmd"
        )
        self.assertEqual(brick_table.horizontalHeaderItem(10).text(), "mfile")
        # self.assertEqual(brick_table.item(0, 0).text(), "smooth_1")
        self.assertEqual(
            brick_table.cellWidget(0, 0).children()[1].text(), "smooth_1"
        )
        # self.assertEqual(brick_table.item(0, 1).text(), "Done")
        self.assertEqual(
            brick_table.cellWidget(0, 1).children()[1].text(), "Done"
        )
        self.assertEqual(
            brick_table.cellWidget(0, 2).children()[1].text(),
            "2022-04-05 14:22:30.298043",
        )
        self.assertEqual(
            brick_table.cellWidget(0, 3).children()[1].text(), "Done"
        )
        self.assertEqual(
            brick_table.cellWidget(0, 4).children()[1].text(),
            "2022-04-05 14:22:30.298043",
        )
        self.assertEqual(
            brick_table.cellWidget(0, 5).children()[1].text(), "0"
        )
        self.assertEqual(
            brick_table.cellWidget(0, 6).children()[1].text(),
            "[6.0, 6.0, 6.0]",
        )
        self.assertEqual(
            brick_table.cellWidget(0, 7).children()[1].text(), "False"
        )
        self.assertEqual(
            brick_table.cellWidget(0, 8).children()[2].text(),
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii",
        )
        self.assertEqual(
            brick_table.cellWidget(0, 9).children()[1].text(),
            "/usr/local/SPM/spm12_standalone/run_spm12.sh "
            "/usr/local/MATLAB/MATLAB_Runtime/v95 script",
        )
        self.assertEqual(
            brick_table.cellWidget(0, 10).children()[1].text(), "True"
        )

    def test_clear_cell(self):
        """Tests the method clearing cells."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Selecting a cell
        bw_column = self.main_window.data_browser.table_data.get_tag_column(
            "BandWidth"
        )
        bw_item = self.main_window.data_browser.table_data.item(0, bw_column)
        bw_item.setSelected(True)
        self.assertEqual(float(bw_item.text()[1:-1]), 50000.0)
        self.assertEqual(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT,
                "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                "pvm-000220_000.nii",
                "BandWidth",
            ),
            [50000.0],
        )

        # Clearing the cell
        bw_item = self.main_window.data_browser.table_data.item(0, bw_column)
        bw_item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.clear_cell()
        self.main_window.data_browser.table_data.itemChanged.connect(
            self.main_window.data_browser.table_data.change_cell_color
        )

        # Checking that it's empty
        bw_item = self.main_window.data_browser.table_data.item(0, bw_column)
        self.assertEqual(bw_item.text(), "*Not Defined*")
        self.assertIsNone(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT,
                "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                "pvm-000220_000.nii",
                "BandWidth",
            )
        )

    def test_clone_tag(self):
        """Tests the pop up cloning a tag."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Testing without new tag name
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(clone_tag.msg.text(), "The tag name can't be empty")

        # Testing without any tag selected to clone
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        clone_tag.line_edit_new_tag_name.setText("Test")
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(
            clone_tag.msg.text(), "The tag to clone must be selected"
        )

        # Testing with tag name already existing
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        clone_tag.line_edit_new_tag_name.setText("Type")
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(clone_tag.msg.text(), "This tag name already exists")

        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag
        clone_tag.line_edit_new_tag_name.setText("Test")
        clone_tag.search_bar.setText("BandWidth")
        clone_tag.list_widget_tags.setCurrentRow(0)  # BandWidth tag selected
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )
        test_row = self.main_window.project.session.get_field(
            COLLECTION_CURRENT, "Test"
        )
        bandwidth_row = self.main_window.project.session.get_field(
            COLLECTION_CURRENT, "BandWidth"
        )
        self.assertEqual(test_row.description, bandwidth_row.description)
        self.assertEqual(test_row.unit, bandwidth_row.unit)
        self.assertEqual(test_row.default_value, bandwidth_row.default_value)
        self.assertEqual(test_row.field_type, bandwidth_row.field_type)
        self.assertEqual(test_row.origin, TAG_ORIGIN_USER)
        self.assertEqual(test_row.visibility, True)
        test_row = self.main_window.project.session.get_field(
            COLLECTION_INITIAL, "Test"
        )
        bandwidth_row = self.main_window.project.session.get_field(
            COLLECTION_INITIAL, "BandWidth"
        )
        self.assertEqual(test_row.description, bandwidth_row.description)
        self.assertEqual(test_row.unit, bandwidth_row.unit)
        self.assertEqual(test_row.default_value, bandwidth_row.default_value)
        self.assertEqual(test_row.field_type, bandwidth_row.field_type)
        self.assertEqual(test_row.origin, TAG_ORIGIN_USER)
        self.assertEqual(test_row.visibility, True)

        for document in self.main_window.project.session.get_documents_names(
            COLLECTION_CURRENT
        ):
            self.assertEqual(
                self.main_window.project.session.get_value(
                    COLLECTION_CURRENT, document, "Test"
                ),
                self.main_window.project.session.get_value(
                    COLLECTION_CURRENT, document, "BandWidth"
                ),
            )

        for document in self.main_window.project.session.get_documents_names(
            COLLECTION_INITIAL
        ):
            self.assertEqual(
                self.main_window.project.session.get_value(
                    COLLECTION_INITIAL, document, "Test"
                ),
                self.main_window.project.session.get_value(
                    COLLECTION_INITIAL, document, "BandWidth"
                ),
            )

        test_column = self.main_window.data_browser.table_data.get_tag_column(
            "Test"
        )
        bw_column = self.main_window.data_browser.table_data.get_tag_column(
            "BandWidth"
        )

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item_bw = self.main_window.data_browser.table_data.item(
                row, bw_column
            )
            item_test = self.main_window.data_browser.table_data.item(
                row, test_column
            )
            self.assertEqual(item_bw.text(), item_test.text())

    def test_count_table(self):
        """Tests the count table popup."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        QTest.mouseClick(
            self.main_window.data_browser.count_table_button, Qt.LeftButton
        )
        count_table = self.main_window.data_browser.count_table_pop_up
        self.assertEqual(len(count_table.push_buttons), 2)

        count_table.push_buttons[0].setText("BandWidth")
        count_table.fill_values(0)
        count_table.push_buttons[1].setText("EchoTime")
        count_table.fill_values(1)
        QTest.mouseClick(count_table.push_button_count, Qt.LeftButton)

        # Trying to add and remove tag buttons
        QTest.mouseClick(count_table.add_tag_label, Qt.LeftButton)
        self.assertEqual(len(count_table.push_buttons), 3)
        QTest.mouseClick(count_table.remove_tag_label, Qt.LeftButton)
        self.assertEqual(len(count_table.push_buttons), 2)

        self.assertEqual(count_table.push_buttons[0].text(), "BandWidth")
        self.assertEqual(count_table.push_buttons[1].text(), "EchoTime")

        QApplication.processEvents()

        self.assertEqual(
            count_table.table.horizontalHeaderItem(0).text(), "BandWidth"
        )
        self.assertEqual(
            count_table.table.horizontalHeaderItem(1).text()[1:-1], "75.0"
        )
        self.assertAlmostEqual(
            float(count_table.table.horizontalHeaderItem(2).text()[1:-1]),
            5.8239923,
        )
        self.assertEqual(
            count_table.table.horizontalHeaderItem(3).text()[1:-1], "5.0"
        )
        self.assertEqual(
            count_table.table.verticalHeaderItem(3).text(), "Total"
        )
        self.assertEqual(count_table.table.item(0, 0).text()[1:-1], "50000.0")
        self.assertEqual(count_table.table.item(1, 0).text()[1:-1], "25000.0")
        self.assertAlmostEqual(
            float(count_table.table.item(2, 0).text()[1:-1]), 65789.48
        )
        self.assertEqual(count_table.table.item(3, 0).text(), "3")
        self.assertEqual(count_table.table.item(0, 1).text(), "2")
        self.assertEqual(count_table.table.item(1, 1).text(), "")
        self.assertEqual(count_table.table.item(2, 1).text(), "")
        self.assertEqual(count_table.table.item(3, 1).text(), "2")
        self.assertEqual(count_table.table.item(0, 2).text(), "")
        self.assertEqual(count_table.table.item(1, 2).text(), "2")
        self.assertEqual(count_table.table.item(2, 2).text(), "")
        self.assertEqual(count_table.table.item(3, 2).text(), "2")
        self.assertEqual(count_table.table.item(0, 3).text(), "")
        self.assertEqual(count_table.table.item(1, 3).text(), "")
        self.assertEqual(count_table.table.item(2, 3).text(), "5")
        self.assertEqual(count_table.table.item(3, 3).text(), "5")

    def test_mia_preferences(self):
        """Tests the MIA preferences popup."""

        config = Config(properties_path=self.properties_path)
        old_auto_save = config.isAutoSave()
        self.assertEqual(old_auto_save, False)

        # Auto save activated
        self.main_window.action_software_preferences.trigger()
        properties = self.main_window.pop_up_preferences
        properties.projects_save_path_line_edit.setText(
            tempfile.mkdtemp(prefix="projects_tests")
        )
        properties.tab_widget.setCurrentIndex(1)
        properties.save_checkbox.setChecked(True)
        QTest.mouseClick(properties.push_button_ok, Qt.LeftButton)
        QTest.qWait(500)
        self.execute_QMessageBox_clickOk()

        config = Config(properties_path=self.properties_path)
        new_auto_save = config.isAutoSave()
        self.assertEqual(new_auto_save, True)

        # Auto save disabled again
        self.main_window.action_software_preferences.trigger()
        properties = self.main_window.pop_up_preferences
        properties.tab_widget.setCurrentIndex(1)
        properties.save_checkbox.setChecked(False)
        QTest.mouseClick(properties.push_button_ok, Qt.LeftButton)
        QTest.qWait(500)
        self.execute_QMessageBox_clickOk()
        config = Config(properties_path=self.properties_path)
        reput_auto_save = config.isAutoSave()
        self.assertEqual(reput_auto_save, False)

        # Checking that the changes are not effective if cancel is clicked
        self.main_window.action_software_preferences.trigger()
        properties = self.main_window.pop_up_preferences
        properties.tab_widget.setCurrentIndex(1)
        properties.save_checkbox.setChecked(True)
        QTest.mouseClick(properties.push_button_cancel, Qt.LeftButton)
        QTest.qWait(500)
        self.execute_QMessageBox_clickOk()
        config = Config(properties_path=self.properties_path)
        # clear config -> user_mode become True !
        config.config = {}
        auto_save = config.isAutoSave()
        self.assertEqual(auto_save, False)

        # Checking that the values for the "Projects preferences" are well set
        self.assertEqual(config.get_max_projects(), 5)
        config.set_max_projects(7)
        self.assertEqual(config.get_max_projects(), 7)
        config.set_max_projects(5)

        config_path = os.path.join(
            config.get_properties_path(), "properties", "config.yml"
        )
        self.assertEqual(os.path.exists(config_path), True)

        self.assertEqual(config.get_user_mode(), True)
        config.set_user_mode(False)
        self.assertEqual(config.get_user_mode(), False)

        self.assertEqual(config.get_mri_conv_path(), "")

        self.assertEqual(config.get_matlab_command(), None)
        self.assertEqual(config.get_matlab_path(), None)
        self.assertEqual(config.get_matlab_standalone_path(), "")
        self.assertEqual(config.get_spm_path(), "")
        self.assertEqual(config.get_spm_standalone_path(), "")
        self.assertEqual(config.get_use_matlab(), False)
        self.assertEqual(config.get_use_spm(), False)
        self.assertEqual(config.get_use_spm_standalone(), False)
        self.assertEqual(config.getBackgroundColor(), "")
        self.assertEqual(config.getChainCursors(), False)
        self.assertEqual(config.getNbAllSlicesMax(), 10)
        self.assertEqual(config.getShowAllSlices(), False)
        self.assertEqual(config.getTextColor(), "")
        self.assertEqual(config.getThumbnailTag(), "SequenceName")

        self.assertEqual(
            False, version.parse(yaml.__version__) > version.parse("9.1")
        )
        self.assertEqual(
            True, version.parse(yaml.__version__) < version.parse("9.1")
        )

        self.assertEqual(config.get_projects_save_path(), "")

    def test_mini_viewer(self):
        """Selects scans and display them in the mini viewer.

        - Tests MiniViewer.
        - The mini viewer displays information of the selected scan in a
          box under the scans list, in the data browser tab.
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser
        viewer = self.main_window.data_browser.viewer

        # Selects the first scan
        data_browser.table_data.item(0, 0).setSelected(True)

        # Gets the 3D slider range
        slider_3D_range = viewer.slider_3D[0].maximum()

        # Moves the 3D slide to the middle of the range
        viewer.slider_3D[0].setValue(int(slider_3D_range / 2))

        # Shows all slices
        viewer.check_box_slices.setCheckState(Qt.Checked)

        # Unchecks show all slices
        viewer.check_box_slices.setCheckState(Qt.Checked)

        # Checks the chain cursors
        viewer.check_box_cursors.setCheckState(Qt.Checked)

        # Selects the second scan
        data_browser.table_data.item(1, 0).setSelected(True)

        # Moves the 3D slides to the lower limit
        viewer.slider_3D[0].setValue(0)

        # Moves the 3D slides to the middle of the range
        viewer.slider_3D[0].setValue(int(slider_3D_range / 2))

        # Moves the 3D slides to the middle of the range
        viewer.slider_3D[0].setValue(slider_3D_range)

        # Unchecks the chain cursors
        viewer.check_box_cursors.setCheckState(Qt.Unchecked)

        viewer.update_nb_slices()

    def test_modify_table(self):
        """Test the modify_table module."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")
        scans_displayed = []
        item = self.main_window.data_browser.table_data.item(0, 0)
        scan_name = item.text()

        # Test values of a list of floats
        value = [5.0, 3.0]
        tag_name = ["FOV"]
        if not self.main_window.data_browser.table_data.isRowHidden(0):
            scans_displayed.append(scan_name)

        # Test that the value will not change if the tag's type is incorrect
        old_value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scans_displayed[0], "FOV"
        )

        mod = ModifyTable(
            self.main_window.project,
            value,
            [str],
            scans_displayed,
            tag_name,
        )
        mod.update_table_values(True)
        mod.deleteLater()
        del mod
        new_value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scans_displayed[0], "FOV"
        )
        self.assertEqual(old_value, new_value)

        # Test that the value will change when all parameters are correct
        tag_object = self.main_window.project.session.get_field(
            COLLECTION_CURRENT, "FOV"
        )
        mod = ModifyTable(
            self.main_window.project,
            value,
            [tag_object.field_type],
            scans_displayed,
            tag_name,
        )
        mod.update_table_values(True)
        new_value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scans_displayed[0], "FOV"
        )
        self.assertEqual(mod.table.columnCount(), 2)
        mod.deleteLater()
        del mod
        self.assertEqual(value, new_value)

    def test_multiple_sort(self):
        """Tests the multiple sort popup."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.multiple_sort_pop_up()
        self.main_window.data_browser.table_data.itemChanged.connect(
            self.main_window.data_browser.table_data.change_cell_color
        )
        multiple_sort = self.main_window.data_browser.table_data.pop_up

        multiple_sort.push_buttons[0].setText("BandWidth")
        multiple_sort.fill_values(0)
        multiple_sort.push_buttons[1].setText("Exp Type")
        multiple_sort.fill_values(1)
        QTest.mouseClick(multiple_sort.push_button_sort, Qt.LeftButton)

        scan = self.main_window.data_browser.table_data.item(0, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014"
            "-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm-000940"
            "_800.nii",
        )
        scan = self.main_window.data_browser.table_data.item(1, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014"
            "-02-14102317-04-G3_Guerbet_MDEFT-MDEFTpvm-000940"
            "_800.nii",
        )
        scan = self.main_window.data_browser.table_data.item(2, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
            "-000220_000.nii",
        )
        scan = self.main_window.data_browser.table_data.item(3, 0).text()
        self.assertEqual(
            scan,
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
            "-000220_000.nii",
        )
        scan = self.main_window.data_browser.table_data.item(4, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
            "-000142_400.nii",
        )
        scan = self.main_window.data_browser.table_data.item(5, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RAREpvm"
            "-000142_400.nii",
        )
        scan = self.main_window.data_browser.table_data.item(6, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RAREpvm"
            "-000142_400.nii",
        )
        scan = self.main_window.data_browser.table_data.item(7, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RAREpvm"
            "-000142_400.nii",
        )
        scan = self.main_window.data_browser.table_data.item(8, 0).text()
        self.assertEqual(
            scan,
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RAREpvm"
            "-000142_400.nii",
        )

    def test_multiple_sort_appendix(self):
        """Adds and removes tags in the data browser.

        - Tests: PopUpMultipleSort

        - Mocks: PopUpSelectTagCountTable.exec_
        """

        table_data = self.main_window.data_browser.table_data

        table_data.multiple_sort_pop_up()
        self.assertTrue(hasattr(table_data, "pop_up"))

        # Adds a 3rd tag to the pop-up
        table_data.pop_up.add_tag_label.clicked.emit()
        self.assertEqual(len(table_data.pop_up.push_buttons), 3)

        # Removes the tag
        table_data.pop_up.remove_tag_label.clicked.emit()
        self.assertEqual(len(table_data.pop_up.push_buttons), 2)

        # Mocks the execution of 'PopUpSelectTagCountTable'
        def mock_select_tags(self):
            """blabla"""
            self.selected_tag = "Exp Type"
            return True

        PopUpSelectTagCountTable.exec_ = mock_select_tags

        table_data.pop_up.select_tag(0)

        # Adds a tag in place of 'Tag n1'
        table_data.pop_up.select_tag(0)

        # Closes the pop-up
        table_data.pop_up.close()

    def test_openTagsPopUp(self):
        """Opens a document in data viewer and opens a pop-up to select the
        legend of the thumbnails.

        - Tests MiniViewer.openTagsPopUp.
        - Indirectly tests PopUpSelectTag.
        - Mocks: PopUpSelectTag.exec_
        """

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser
        viewer = data_browser.viewer

        # Gets a document filepath
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

        # Adds the document to the data browser
        addPath = PopUpAddPath(data_browser.project, data_browser)
        addPath.file_line_edit.setText(str([DOCUMENT_1]))
        addPath.save_path()

        # Selects the document in the data browser
        data_browser.table_data.item(0, 0).setSelected(True)

        # Mocks the execution of the dialog window
        PopUpSelectTag.exec_ = Mock(return_value=True)

        # Opens the tags pop-up and cancel it
        viewer.openTagsPopUp()
        viewer.popUp.cancel_clicked()

        # Opens the tags pop-up
        viewer.openTagsPopUp()

        # Searches for an empty string
        viewer.popUp.search_str("")

        # Asserts that both the first and second tags are not hidden
        self.assertFalse(viewer.popUp.list_widget_tags.item(0).isHidden())
        self.assertFalse(viewer.popUp.list_widget_tags.item(1).isHidden())

        # Searches for the tag 'Exp Type'
        data_browser.viewer.popUp.search_str("Exp Type")

        # Asserts that the second tag is hidden, the first is not
        self.assertFalse(viewer.popUp.list_widget_tags.item(0).isHidden())
        self.assertTrue(viewer.popUp.list_widget_tags.item(1).isHidden())

        # Selects one tab
        item_0 = viewer.popUp.list_widget_tags.item(0)
        viewer.popUp.list_widget_tags.itemClicked.emit(item_0)

        viewer.popUp.list_widget_tags.item(0).setCheckState(Qt.Checked)
        viewer.popUp.ok_clicked()

    def test_open_project(self):
        """Tests project opening."""

        project_8_path = self.get_new_test_project(name="project_8")
        self.main_window.switch_project(project_8_path, "project_8")

        self.assertEqual(self.main_window.project.getName(), "project_8")
        self.assertEqual(
            self.main_window.windowTitle(),
            "MIA - Multiparametric Image Analysis (Admin mode) - project_8",
        )

        documents = self.main_window.project.session.get_documents_names(
            COLLECTION_CURRENT
        )

        self.assertEqual(len(documents), 9)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in documents
        )
        documents = self.main_window.project.session.get_documents_names(
            COLLECTION_INITIAL
        )
        self.assertEqual(len(documents), 9)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in documents
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in documents
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in documents
        )

    def test_project_filter(self):
        """Creates a project, saves a filter and opens it.

        - Tests:
            - DataBrowser.open_popup
            - Project.save_current_filter

        - Mocks:
           - QMessageBox.exec
           - QInputDialog.getText
        """

        test_project_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_project_path, "test_project")

        # Mocks the execution of a dialog box
        QMessageBox.exec = lambda *arg: None

        # Saves the current filter as 'filter_1'
        QInputDialog.getText = lambda *argv: ("filter_1", True)
        self.main_window.data_browser.save_filter_action.trigger()

        # Tries to save it again by the same name
        self.main_window.data_browser.save_filter_action.trigger()

        # Opens the saved filters pop-up
        self.main_window.data_browser.open_filter_action.trigger()
        open_popup = self.main_window.data_browser.popUp

        # Closes the pop-up and re-opens it
        open_popup.cancel_clicked()
        self.main_window.data_browser.open_filter_action.trigger()

        # Tries to search for an empty string
        open_popup.search_str("")
        self.assertFalse(open_popup.list_widget_filters.item(0).isHidden())

        # Tries to search for a non-existent filter
        open_popup.search_str("filter_2")
        self.assertTrue(open_popup.list_widget_filters.item(0).isHidden())

        # Tries to search for an existing filter
        open_popup.search_str("filter_1")
        self.assertFalse(open_popup.list_widget_filters.item(0).isHidden())

        open_popup.list_widget_filters.item(0).setSelected(True)
        # QTest.mouseClick(open_popup.push_button_ok, Qt.LeftButton)
        open_popup.push_button_ok.clicked.emit()

        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 3)

    def test_project_properties(self):
        """Tests saved projects addition and removal."""

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

        SavedProjects.loadSavedProjects = lambda a: True
        saved_projects = SavedProjects()
        self.assertEqual(saved_projects.pathsList, [])

    def test_proj_remov_from_cur_proj(self):
        """Tests that the projects are removed from the list of current
        projects.
        """

        config = Config(properties_path=self.properties_path)
        projects = config.get_opened_projects()
        self.assertEqual(len(projects), 1)
        self.assertTrue(self.main_window.project.folder in projects)

    def test_rapid_search(self):
        """Tests the rapid search bar."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Checking that the 9 scans are shown in the DataBrowser
        self.assertEqual(
            self.main_window.data_browser.table_data.rowCount(), 9
        )
        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )

        # Testing G1 rapid search
        self.main_window.data_browser.search_bar.setText("G1")
        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 2)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans_displayed
        )

        # Testing that all the scans are back when clicking on the cross
        QTest.mouseClick(
            self.main_window.data_browser.button_cross, Qt.LeftButton
        )
        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
            "-000220_000.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm"
            "-000940_800.nii" in scans_displayed
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
            "-000142_400.nii" in scans_displayed
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
            "-000220_000.nii" in scans_displayed
        )

        # Testing not defined values
        QTest.mouseClick(
            self.main_window.data_browser.button_cross, Qt.LeftButton
        )
        self.main_window.data_browser.search_bar.setText("*Not Defined*")
        scans_displayed = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(
            scans_displayed,
            [
                "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                "pvm-000142_400.nii"
            ],
        )

    def test_remove_scan(self):
        """Creates a new project, adds scans to the session and remove them.

        - Tests:
            - PipelineManagerTab.remove_scan
            - PopUpRemoveScan

        - Mocks:
            - PopUpRemoveScan.exec
        """

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        data_browser = self.main_window.data_browser
        tb_data = data_browser.table_data
        session = self.main_window.project.session

        # Creates a new project folder
        project_8_path = self.get_new_test_project()
        ppl_manager.project.folder = project_8_path
        folder = os.path.join(project_8_path, "data", "raw_data")

        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )
        NII_FILE_2 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-05-G4_"
            "Guerbet_T1SE_800-RAREpvm-000142_400.nii"
        )
        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        DOCUMENT_2 = os.path.abspath(os.path.join(folder, NII_FILE_2))

        # Adds 2 scans to the current session
        session.add_document(COLLECTION_CURRENT, DOCUMENT_1)
        session.add_document(COLLECTION_INITIAL, DOCUMENT_1)
        session.add_document(COLLECTION_CURRENT, DOCUMENT_2)
        session.add_document(COLLECTION_INITIAL, DOCUMENT_2)
        ppl_manager.scan_list.append(DOCUMENT_1)
        ppl_manager.scan_list.append(DOCUMENT_2)
        data_browser.data_sent = True

        # Refreshes the data browser tab
        self.main_window.update_project(project_8_path)

        # Selects all scans
        tb_data.selectColumn(0)

        # Cancels removing both scans
        PopUpRemoveScan.exec = lambda x: tb_data.pop.cancel_clicked()
        data_browser.table_data.remove_scan()

        # Rejects removing both scans
        PopUpRemoveScan.exec = lambda x: tb_data.pop.no_all_clicked()
        data_browser.table_data.remove_scan()

        # Asserts that the data browser kept both scans
        self.assertEqual(len(tb_data.scans), 2)

        # Effectively removes both scans
        PopUpRemoveScan.exec = lambda x: tb_data.pop.yes_all_clicked()
        data_browser.table_data.remove_scan()

        # Asserts that the scans were deleted
        self.assertEqual(len(tb_data.scans), 0)

        # Adds one scan to the current session
        session.add_document(COLLECTION_CURRENT, DOCUMENT_1)
        session.add_document(COLLECTION_INITIAL, DOCUMENT_1)
        self.main_window.update_project(project_8_path)
        ppl_manager.scan_list.append(DOCUMENT_1)

        # Selects the scan
        data_browser.table_data.selectColumn(0)

        # Removes the scan
        PopUpRemoveScan.exec = lambda x: tb_data.pop.yes_clicked()
        data_browser.table_data.remove_scan()

        # Asserts that the scans were deleted
        self.assertEqual(len(tb_data.scans), 0)

        # project_8_path = self.get_new_test_project()
        # self.main_window.switch_project(project_8_path, "project_8")

    #

    # scans_displayed = []
    #
    # for row in range(0,
    #                 self.main_window.data_browser.table_data.rowCount()):
    #    item = self.main_window.data_browser.table_data.item(row, 0)
    #    scan_name = item.text()
    #
    #    if not self.main_window.data_browser.table_data.isRowHidden(row):
    #        scans_displayed.append(scan_name)
    #
    # self.assertEqual(len(scans_displayed), 9)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
    #                "-000220_000.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFTpvm"
    #                "-000940_800.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm"
    #                "-000940_800.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
    #                "-000220_000.nii" in scans_displayed)
    #
    # Trying to remove a scan
    # self.main_window.data_browser.table_data.selectRow(0)
    # self.main_window.data_browser.table_data.remove_scan()
    # scans_displayed = []
    #
    # for row in range(0,
    #                 self.main_window.data_browser.table_data.rowCount()):
    #    item = self.main_window.data_browser.table_data.item(row, 0)
    #    scan_name = item.text()
    #
    #    if not self.main_window.data_browser.table_data.isRowHidden(row):
    #        scans_displayed.append(scan_name)
    #
    # self.assertEqual(len(scans_displayed), 8)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFTpvm"
    #                "-000940_800.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm"
    #                "-000940_800.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
    #                "-000142_400.nii" in scans_displayed)
    # self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
    #                "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
    #                "-000220_000.nii" in scans_displayed)

    def test_remove_tag(self):
        """Tests the popup removing user tags."""

        # Adding a tag "Test"
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        add_tag.text_edit_tag_name.setText("Test")
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        old_tags_current = self.main_window.project.session.get_fields_names(
            COLLECTION_CURRENT
        )
        old_tags_initial = self.main_window.project.session.get_fields_names(
            COLLECTION_INITIAL
        )

        # Open the "Remove a tag" pop-up but do nothing
        self.main_window.data_browser.remove_tag_action.trigger()
        remove_tag = self.main_window.data_browser.pop_up_remove_tag
        QTest.mouseClick(remove_tag.push_button_ok, Qt.LeftButton)
        new_tags_current = self.main_window.project.session.get_fields_names(
            COLLECTION_CURRENT
        )
        new_tags_initial = self.main_window.project.session.get_fields_names(
            COLLECTION_INITIAL
        )

        # Check that the list of tags has not changed
        self.assertTrue(old_tags_current == new_tags_current)
        self.assertTrue(old_tags_initial == new_tags_initial)

        old_tags_current = self.main_window.project.session.get_fields_names(
            COLLECTION_CURRENT
        )
        old_tags_initial = self.main_window.project.session.get_fields_names(
            COLLECTION_INITIAL
        )
        # Check that "Test" tag is in the list of tags
        self.assertTrue("Test" in old_tags_current)
        self.assertTrue("Test" in old_tags_initial)

        # Open the "Remove a tag" pop-up and remove "Test" tag
        self.main_window.data_browser.remove_tag_action.trigger()
        remove_tag = self.main_window.data_browser.pop_up_remove_tag
        remove_tag.list_widget_tags.setCurrentRow(0)  # Test tag selected
        QTest.mouseClick(remove_tag.push_button_ok, Qt.LeftButton)
        new_tags_current = self.main_window.project.session.get_fields_names(
            COLLECTION_CURRENT
        )
        new_tags_initial = self.main_window.project.session.get_fields_names(
            COLLECTION_INITIAL
        )
        # Check that "Test" tag is no longer in the list of tags
        self.assertTrue("Test" not in new_tags_current)
        self.assertTrue("Test" not in new_tags_initial)

    def test_reset_cell(self):
        """Tests the method resetting the selected cells."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # scan name
        item = self.main_window.data_browser.table_data.item(0, 0)
        scan_name = item.text()

        # Test for a list:
        # Values in the db
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name, "BandWidth"
            )[0]
        )

        # Value in the DataBrowser
        bandwidth_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("BandWidth")
        item = self.main_window.data_browser.table_data.item(
            0, bandwidth_column
        )
        databrowser = float(item.text()[1:-1])

        # Check equality between DataBrowser and db
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # Change the value
        item.setSelected(True)
        # threading.Timer(
        #     2, partial(self.edit_databrowser_list, "25000")
        # ).start()
        QTimer.singleShot(2000, partial(self.edit_databrowser_list, "25000"))
        self.main_window.data_browser.table_data.edit_table_data_values()

        # Check again the equality between DataBrowser and db
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name, "BandWidth"
            )[0]
        )
        item = self.main_window.data_browser.table_data.item(
            0, bandwidth_column
        )
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, float(50000))

        # Reset the current value to the initial value
        item = self.main_window.data_browser.table_data.item(
            0, bandwidth_column
        )
        item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_cell()
        self.main_window.data_browser.table_data.itemChanged.connect(
            self.main_window.data_browser.table_data.change_cell_color
        )
        item.setSelected(False)

        # Check whether the data has been reset
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name, "BandWidth"
            )[0]
        )
        item = self.main_window.data_browser.table_data.item(
            0, bandwidth_column
        )
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # Test for a string:
        # Values in the db
        value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scan_name, "Type"
        )
        value_initial = self.main_window.project.session.get_value(
            COLLECTION_INITIAL, scan_name, "Type"
        )

        # Value in the DataBrowser
        type_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("Type")
        item = self.main_window.data_browser.table_data.item(0, type_column)
        databrowser = item.text()

        # Check equality between DataBrowser and db
        self.assertEqual(value, "Scan")
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # Change the value
        item.setSelected(True)
        item.setText("Test")
        item.setSelected(False)

        # Check again the equality between DataBrowser and db
        value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scan_name, "Type"
        )
        value_initial = self.main_window.project.session.get_value(
            COLLECTION_INITIAL, scan_name, "Type"
        )
        item = self.main_window.data_browser.table_data.item(0, type_column)

        databrowser = item.text()

        self.assertEqual(value, "Test")
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, "Scan")

        # Reset the current value to the initial value
        item = self.main_window.data_browser.table_data.item(0, type_column)
        item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_cell()
        self.main_window.data_browser.table_data.itemChanged.connect(
            self.main_window.data_browser.table_data.change_cell_color
        )
        item.setSelected(False)

        # Check whether the data has been reset
        value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scan_name, "Type"
        )
        value_initial = self.main_window.project.session.get_value(
            COLLECTION_INITIAL, scan_name, "Type"
        )
        item = self.main_window.data_browser.table_data.item(0, type_column)
        databrowser = item.text()
        self.assertEqual(value, "Scan")
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

    def test_reset_column(self):
        """Tests the method resetting the columns selected."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Second document; scan name
        item = self.main_window.data_browser.table_data.item(1, 0)
        scan_name2 = item.text()

        # Second document; values in the db
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name2, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name2, "BandWidth"
            )[0]
        )

        # Second document; value in the DataBrowser
        bandwidth_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("BandWidth")
        item2 = self.main_window.data_browser.table_data.item(
            1, bandwidth_column
        )
        databrowser = float(item2.text()[1:-1])

        # Check equality between DataBrowser and db for second document
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)
        item2.setSelected(True)

        # Third document; scan name
        item = self.main_window.data_browser.table_data.item(2, 0)
        scan_name3 = item.text()

        # Third document; values in the db
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name3, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name3, "BandWidth"
            )[0]
        )

        # Third document; value in the DataBrowser
        item3 = self.main_window.data_browser.table_data.item(
            2, bandwidth_column
        )

        # Check equality between DataBrowser and db for third document
        databrowser = float(item3.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)
        item3.setSelected(True)

        # Change the value to [70000] for the third and second documents
        # threading.Timer(
        #     2, partial(self.edit_databrowser_list, "70000")
        # ).start()
        QTimer.singleShot(2000, partial(self.edit_databrowser_list, "70000"))
        self.main_window.data_browser.table_data.edit_table_data_values()

        # Second document; values in the db
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name2, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name2, "BandWidth"
            )[0]
        )
        # Second document; value in the DataBrowser
        item2 = self.main_window.data_browser.table_data.item(
            1, bandwidth_column
        )
        databrowser = float(item2.text()[1:-1])

        # Check equality between DataBrowser and db for second document
        self.assertEqual(value, float(70000))
        self.assertEqual(value, databrowser)
        self.assertEqual(float(50000), value_initial)
        item2.setSelected(True)

        # Third document; values in the db
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name3, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name3, "BandWidth"
            )[0]
        )

        # Third document; value in the DataBrowser
        item3 = self.main_window.data_browser.table_data.item(
            2, bandwidth_column
        )
        databrowser = float(item3.text()[1:-1])

        # Check value in database for the third document
        self.assertEqual(value, float(70000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, float(25000))
        item3.setSelected(True)

        # Reset the current value to the initial value
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_column()
        self.main_window.data_browser.table_data.itemChanged.connect(
            self.main_window.data_browser.table_data.change_cell_color
        )

        # Check the value in the db and DataBrowser for the second document
        # has been reset
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name2, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name2, "BandWidth"
            )[0]
        )
        item2 = self.main_window.data_browser.table_data.item(
            1, bandwidth_column
        )
        databrowser = float(item2.text()[1:-1])
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # Check the value in the db and DataBrowser for the third document
        # has been reset
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name3, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name3, "BandWidth"
            )[0]
        )
        item3 = self.main_window.data_browser.table_data.item(
            2, bandwidth_column
        )
        databrowser = float(item3.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

    def test_reset_row(self):
        """Tests row reset."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Value in DataBrowser for the second document
        type_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("Type")
        type_item = self.main_window.data_browser.table_data.item(
            1, type_column
        )
        old_type = type_item.text()

        # Check value in DataBrowser for the second document
        self.assertEqual(old_type, "Scan")

        # Change the value
        type_item.setSelected(True)
        type_item.setText("Test")

        # Check if value in DataBrowser as been changed
        set_item = self.main_window.data_browser.table_data.item(
            1, type_column
        )
        set_type = set_item.text()
        self.assertEqual(set_type, "Test")

        # Reset row for second document
        self.main_window.data_browser.table_data.clearSelection()
        item = self.main_window.data_browser.table_data.item(1, 0)
        item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_row()
        self.main_window.data_browser.table_data.itemChanged.connect(
            self.main_window.data_browser.table_data.change_cell_color
        )

        # Check if value in DataBrowser as been reset
        type_item = self.main_window.data_browser.table_data.item(
            1, type_column
        )
        new_type = type_item.text()
        self.assertEqual(new_type, "Scan")

    def test_save_project(self):
        """Test opening & saving of a project."""

        config = Config(properties_path=self.properties_path)
        projects_dir = os.path.realpath(
            tempfile.mkdtemp(prefix="projects_tests")
        )

        # Instead of executing the pop-up, only shows it
        # This prevents thread deadlocking
        QMessageBox.exec = lambda self_: self_.show()

        # Tries to open the project pop-up without the projects save dir
        config.set_projects_save_path(None)
        self.main_window.create_project_pop_up()
        self.main_window.msg.accept()

        # Tries to save the project 'something' without setting the
        # projects save directory
        self.main_window.saveChoice()
        self.main_window.msg.accept()

        # Sets the project save directory
        config.set_projects_save_path(projects_dir)
        something_path = os.path.join(projects_dir, "something")
        project_8_path = self.get_new_test_project(name="project_8")

        # Saves the project 'something'
        self.main_window.saveChoice()
        self.assertEqual(self.main_window.project.getName(), "something")
        self.assertEqual(os.path.exists(something_path), True)

        # Switches to project 'project_8'
        self.main_window.switch_project(project_8_path, "project_8")
        self.assertEqual(self.main_window.project.getName(), "project_8")
        self.main_window.saveChoice()  # Updates the project 'project_8'

        # Removes the project 'something' file tree
        shutil.rmtree(something_path)

        PopUpNewProject.exec = lambda x: True
        PopUpNewProject.selectedFiles = lambda x: True
        PopUpNewProject.get_filename = lambda x, y: True
        PopUpNewProject.relative_path = something_path

        PopUpOpenProject.exec = lambda x: True
        PopUpOpenProject.selectedFiles = lambda x: True
        PopUpOpenProject.get_filename = lambda x, y: True
        PopUpOpenProject.relative_path = something_path
        PopUpOpenProject.path, PopUpOpenProject.name = os.path.split(
            something_path
        )
        # Creates and saves the project 'something'
        self.main_window.create_project_pop_up()
        self.assertEqual(self.main_window.project.getName(), "something")
        self.assertEqual(os.path.exists(something_path), True)

        # Switches to another project and verifies that project
        # 'something' is shown in the projects pop-up
        self.main_window.switch_project(project_8_path, "project_8")
        self.main_window.open_project_pop_up()
        self.assertEqual(self.main_window.project.getName(), "something")

        # Removes the project 'something' tree
        self.main_window.switch_project(project_8_path, "project_8")
        shutil.rmtree(something_path)

    def test_send_doc_to_pipeline_manager(self):
        """Tests the popup sending the documents to the pipeline manager."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Checking that the pipeline manager has an empty list at the beginning
        self.assertEqual(self.main_window.pipeline_manager.scan_list, [])

        # Sending the selection (all scans), but closing the popup
        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(500)

        send_popup.close()

        # Checking that the list is still empty
        self.assertEqual(self.main_window.pipeline_manager.scan_list, [])

        # Sending the selection (all scans), but hit the "OK" button
        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(500)

        send_popup.ok_clicked()

        # Checking that all scans have been sent to the pipeline manager
        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 9)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
            "pvm-000142_400.nii" in scans
        )
        self.assertTrue(
            "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
            "pvm-000220_000.nii" in scans
        )

        # Selecting the first 2 scans
        item1 = self.main_window.data_browser.table_data.item(0, 0)
        item1.setSelected(True)
        scan1 = item1.text()
        item2 = self.main_window.data_browser.table_data.item(1, 0)
        item2.setSelected(True)
        scan2 = item2.text()

        # Sending the selection (first 2 scans)
        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(500)

        send_popup.ok_clicked()

        # Checking that the first 2 scans have been sent to the
        # pipeline manager
        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 2)
        self.assertTrue(scan1 in scans)
        self.assertTrue(scan2 in scans)

        # Checking with the rapid search
        self.main_window.data_browser.table_data.clearSelection()
        self.main_window.data_browser.search_bar.setText("G3")

        # Sending the selection (G3 scans)
        QTest.mouseClick(
            self.main_window.data_browser.send_documents_to_pipeline_button,
            Qt.LeftButton,
        )
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(500)

        send_popup.ok_clicked()

        # Checking that G3 scans have been sent to the pipeline manager
        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 2)
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans
        )
        self.assertTrue(
            "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
            "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
            "pvm-000940_800.nii" in scans
        )

    def test_set_value(self):
        """Tests the values modifications.

        This test is redundant with the first part of test_reset_cell.
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Scan name for the second document
        item = self.main_window.data_browser.table_data.item(1, 0)
        scan_name = item.text()

        # Test for a list:
        # Values in the db
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name, "BandWidth"
            )[0]
        )

        # Value in the DataBrowser
        bandwidth_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("BandWidth")
        item = self.main_window.data_browser.table_data.item(
            1, bandwidth_column
        )
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # Change the value
        item.setSelected(True)
        # threading.Timer(
        #     2, partial(self.edit_databrowser_list, "25000")
        # ).start()
        QTimer.singleShot(2000, partial(self.edit_databrowser_list, "25000"))
        self.main_window.data_browser.table_data.edit_table_data_values()

        # Check if value was changed in db and DataBrowser
        value = float(
            self.main_window.project.session.get_value(
                COLLECTION_CURRENT, scan_name, "BandWidth"
            )[0]
        )
        value_initial = float(
            self.main_window.project.session.get_value(
                COLLECTION_INITIAL, scan_name, "BandWidth"
            )[0]
        )
        item = self.main_window.data_browser.table_data.item(
            1, bandwidth_column
        )
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, float(50000))
        item.setSelected(False)

        # Test for a string:
        # Values in the db
        value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scan_name, "Type"
        )
        value_initial = self.main_window.project.session.get_value(
            COLLECTION_INITIAL, scan_name, "Type"
        )

        # Value in the DataBrowser
        type_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("Type")
        item = self.main_window.data_browser.table_data.item(1, type_column)
        databrowser = item.text()

        # Check equality between DataBrowser and db
        self.assertEqual(value, "Scan")
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # Change the value
        item.setSelected(True)
        item.setText("Test")
        item.setSelected(False)

        # Check if value in DataBrowser and db as been changed
        value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scan_name, "Type"
        )
        value_initial = self.main_window.project.session.get_value(
            COLLECTION_INITIAL, scan_name, "Type"
        )
        item = self.main_window.data_browser.table_data.item(1, type_column)
        databrowser = item.text()
        self.assertEqual(value, "Test")
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, "Scan")

    def test_show_brick_history(self):
        """Opens the history pop-up for scans with history related to
        standard bricks and bricks contained by a sub-pipeline.

        - Tests
            - TableDataBrowser.show_brick_history
            - PopUpShowHistory
        """

        # Creates a new project folder and switches to it
        new_project_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_project_path, "light_test_project")

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser
        session = self.main_window.project.session

        # Gets the input file path of the input scan
        INPUT_SCAN = session.get_documents(COLLECTION_CURRENT)[0]["FileName"]

        # Opens the history pop-up for the scan related to 'smooth_1'
        hist_index = data_browser.table_data.get_tag_column("History")
        hist_button = data_browser.table_data.cellWidget(
            0, hist_index
        ).children()[-1]
        hist_button.clicked.emit()  # Opens the history window

        # Asserts that a history pop-up was created
        self.assertTrue(
            hasattr(data_browser.table_data, "brick_history_popup")
        )

        # Clicks on the input button displayed on the history pop-up.
        # This shows the corresponding scan in the data browser
        input_button = (
            data_browser.table_data.brick_history_popup.table.cellWidget(
                0, 8
            ).children()[2]
        )

        input_button.clicked.emit()  # Clicks on the input button

        # Asserts that 'INPUT_SCAN' history pop-up was created
        self.assertNotEqual(data_browser.table_data.selectedItems(), 0)
        self.assertEqual(
            data_browser.table_data.selectedItems()[0].text(), INPUT_SCAN
        )

        # Opens the history pop-up for the scan related to 'quad_smooth_1'
        hist_button = data_browser.table_data.cellWidget(
            1, hist_index
        ).children()[-1]

        hist_button.clicked.emit()  # Opens the history window
        hist_button.close()

    def test_sort(self):
        """Tests the sorting in the DataBrowser."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        mixed_bandwidths = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            bandwidth_column = (
                self.main_window.data_browser.table_data.get_tag_column
            )("BandWidth")
            item = self.main_window.data_browser.table_data.item(
                row, bandwidth_column
            )
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                mixed_bandwidths.append(scan_name)

        (
            self.main_window.data_browser.table_data.horizontalHeader
        )().setSortIndicator(bandwidth_column, 0)
        up_bandwidths = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            bandwidth_column = (
                self.main_window.data_browser.table_data.get_tag_column
            )("BandWidth")
            item = self.main_window.data_browser.table_data.item(
                row, bandwidth_column
            )
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                up_bandwidths.append(scan_name)

        self.assertNotEqual(mixed_bandwidths, up_bandwidths)
        self.assertEqual(sorted(mixed_bandwidths), up_bandwidths)

        (
            self.main_window.data_browser.table_data.horizontalHeader
        )().setSortIndicator(bandwidth_column, 1)
        down_bandwidths = []

        for row in range(
            0, self.main_window.data_browser.table_data.rowCount()
        ):
            bandwidth_column = (
                self.main_window.data_browser.table_data.get_tag_column
            )("BandWidth")
            item = self.main_window.data_browser.table_data.item(
                row, bandwidth_column
            )
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                down_bandwidths.append(scan_name)

        self.assertNotEqual(mixed_bandwidths, down_bandwidths)
        self.assertEqual(
            sorted(mixed_bandwidths, reverse=True), down_bandwidths
        )

    def test_table_data_add_columns(self):
        """Adds tag columns to the table data window.

        - Tests TableDataBrowser.add_columns.
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for often used objects
        table_data = self.main_window.data_browser.table_data

        # Adds a tag, of the types float, datetime, date and time, to
        # the project session
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
        for tag, tag_type in zip(tags, types):
            table_data.project.session.add_field(
                COLLECTION_CURRENT, tag, tag_type, "", True, "", "", ""
            )

        table_data.add_columns()  # Adds the tags to table view

        # Asserts that the tags were added to the table view
        for tag in tags:
            self.assertIsNotNone(table_data.get_tag_column(tag))

    def test_table_data_appendix(self):
        """Opens a project and tests miscellaneous methods of the table
        data view, in the data browser.

        -Tests
            - TableDataBrowser.change_cell_color
            - TableDataBrowser.section_moved
            - TableDataBrowser.selectColumn
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Set often used shortcuts
        table_data = self.main_window.data_browser.table_data

        # TESTS CHANGE_CELL_COLOR
        # Adds a new document to the collection
        NEW_DOC = {"FileName": "mock_file_name"}
        self.main_window.project.session.add_document(
            COLLECTION_CURRENT, NEW_DOC
        )
        self.main_window.project.session.add_document(
            COLLECTION_INITIAL, NEW_DOC
        )

        # Selects the 'Filename' of the first scan and changes its value
        # to this document filename
        table_data.item(0, 0).setSelected(True)
        table_data.item(0, 0).setText(NEW_DOC["FileName"])
        table_data.item(0, 0).setSelected(False)

        # Selects 'FOV' and changes its value
        table_data.item(0, 3).setSelected(True)
        table_data.item(0, 3).setText("[4.0, 4.0]")
        table_data.item(0, 3).setSelected(False)

        # Creates a tag of type float and selects it
        self.main_window.data_browser.add_tag_infos(
            "mock_tag", 0.0, FIELD_TYPE_FLOAT, "", ""
        )
        table_data.item(0, 6).setSelected(True)

        # Mocks the execution of a dialog box
        QMessageBox.exec = lambda *args: None

        # Tries setting an invalid string value to the tag
        table_data.item(0, 6).setText("invalid_string")
        table_data.item(0, 6).setSelected(False)

        # Creates another tag of type float and selects it
        self.main_window.data_browser.add_tag_infos(
            "mock_tag_1", 0.0, FIELD_TYPE_FLOAT, "", ""
        )
        table_data.item(0, 7).setSelected(True)

        # Sets a valid float value to the tag
        table_data.item(0, 7).setText("0.0")

        # Changing the same tag does not trigger the 'valueChanged' and
        # thus not the 'change_cell_color' method
        table_data.item(0, 7).setSelected(False)

        # Selects the 'Exp Type' and 'FOV' of the first scan, which have
        # distinct data types
        table_data.item(0, 2).setSelected(True)
        table_data.item(0, 3).setSelected(True)

        # Tries changing the value of 'Exp Type'
        table_data.item(0, 2).setText("RARE_B")

        # Asserts that only 'Exp Type' changed
        self.assertEqual(table_data.item(0, 2).text(), "RARE_B")
        self.assertNotEqual(table_data.item(0, 3).text(), "RARE_B")

        # TESTS SELECTION_MOVED

        # Switch columns of the 2 first tags
        table_data.horizontalHeader().sectionMoved.emit(0, 0, 1)

        # SELECT_COLUMN
        # Selects the whole filename column
        table_data.selectColumn(0)

        # Asserts that it was selected
        selected_items = table_data.selectedItems()
        self.assertEqual(len(selected_items), len(table_data.scans))
        self.assertEqual(selected_items[0].text(), table_data.scans[0][0])

    def test_table_data_context_menu(self):
        """Right-click on a scan to display the context menu table, and choose
        an option.

        - Tests: TableDataBrowser.context_menu_table

        - Mocks:
            - QMenu.exec_
            - QMessageBox.exec
        """

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for often used objects
        table_data = self.main_window.data_browser.table_data

        # Mocks the execution of a dialog box
        QMessageBox.exec = lambda *args: None

        # Opens the context menu one time before cycling through the
        # actions
        QMenu.exec_ = lambda *args: None
        table_data.context_menu_table(QPoint(10, 10))

        # Cycles through the actions by opening the context menu and
        # clicking in each one of them
        act_names = [
            "action_reset_cell",
            "action_reset_column",
            "action_reset_row",
            "action_clear_cell",
            "action_add_scan",
            "action_remove_scan",
            "action_visualized_tags",
            "action_select_column",
            "action_multiple_sort",
            "action_send_documents_to_pipeline",
            "action_display_file",
        ]
        # Including 'action_sort_column' will crash the build

        for act_name in act_names:
            QMenu.exec_ = lambda *args: getattr(table_data, act_name)
            table_data.context_menu_table(QPoint(10, 10))

    def test_undo_redo_databrowser(self):
        """Tests the DataBrowser undo/redo."""

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # 1. Tag value (list)
        # Check undos and redos are empty
        self.assertEqual(self.main_window.project.undos, [])
        self.assertEqual(self.main_window.project.redos, [])

        # DataBrowser value for second document
        bw_column = (self.main_window.data_browser.table_data.get_tag_column)(
            "BandWidth"
        )
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_old = bw_item.text()

        # Check the value is really 50000
        self.assertEqual(float(bw_old[1:-1]), 50000)

        # Change the value
        bw_item.setSelected(True)
        # threading.Timer(2,
        #                 partial(self.edit_databrowser_list, "0.0")).start()
        QTimer.singleShot(2000, partial(self.edit_databrowser_list, "0.0"))
        self.main_window.data_browser.table_data.edit_table_data_values()

        # Check undos and redos have the right values.
        self.assertEqual(
            self.main_window.project.undos,
            [
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
            ],
        )
        self.assertEqual(self.main_window.project.redos, [])

        # Check the value has really been changed to 0.0.
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_set = bw_item.text()
        self.assertEqual(float(bw_set[1:-1]), 0)

        # Undo
        self.main_window.action_undo.trigger()

        # Check the value has really been reset to 50000
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_undo = bw_item.text()
        self.assertEqual(float(bw_undo[1:-1]), 50000)

        # Check undos / redos have the right values
        self.assertEqual(
            self.main_window.project.redos,
            [
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
            ],
        )
        self.assertEqual(self.main_window.project.undos, [])

        # Redo
        self.main_window.action_redo.trigger()

        # Check the value has really been reset to 0.0
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_redo = bw_item.text()
        self.assertEqual(float(bw_redo[1:-1]), 0)

        # we test undos / redos have the right values
        self.assertEqual(
            self.main_window.project.undos,
            [
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
            ],
        )
        self.assertEqual(self.main_window.project.redos, [])

        # 2. Remove a scan (document)
        # Check there are 9 documents in db (current and initial)
        self.assertEqual(
            9,
            len(
                self.main_window.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )
            ),
        )
        self.assertEqual(
            9,
            len(
                self.main_window.project.session.get_documents_names(
                    COLLECTION_INITIAL
                )
            ),
        )

        # Remove the eighth document
        self.main_window.data_browser.table_data.selectRow(8)
        self.main_window.data_browser.table_data.remove_scan()

        # Check if there are now 8 documents in db (current and initial)
        self.assertEqual(
            8,
            len(
                self.main_window.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )
            ),
        )
        self.assertEqual(
            8,
            len(
                self.main_window.project.session.get_documents_names(
                    COLLECTION_INITIAL
                )
            ),
        )

        # Undo
        self.main_window.action_undo.trigger()

        # Check there are still only 8 documents in the database
        # (current and initial). In fact the document has been permanently
        # deleted and we cannot recover it in this case
        self.assertEqual(
            8,
            len(
                self.main_window.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )
            ),
        )
        self.assertEqual(
            8,
            len(
                self.main_window.project.session.get_documents_names(
                    COLLECTION_INITIAL
                )
            ),
        )

        # 3. Add a tag
        # Check we don't have 'Test' tag in the db
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # Add the Test tag
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        add_tag.text_edit_tag_name.setText("Test")
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)

        # Check the 'Test' tag is in the db
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # Undo
        self.main_window.action_undo.trigger()

        # Check 'Test' tag is not in the db
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # Redo
        self.main_window.action_redo.trigger()

        # Check the 'Test' tag is in the db
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # 4. Remove tag
        # Remove the 'Test' tag
        self.main_window.data_browser.remove_tag_action.trigger()
        remove_tag = self.main_window.data_browser.pop_up_remove_tag
        remove_tag.list_widget_tags.setCurrentRow(0)  # 'Test' tag selected
        QTest.mouseClick(remove_tag.push_button_ok, Qt.LeftButton)

        # Check 'Test' tag is not in the db
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # Undo
        self.main_window.action_undo.trigger()

        # Check 'Test' tag is in the db
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # Redo
        self.main_window.action_redo.trigger()

        # Check 'Test' tag is not in the db
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # 4. clone tag
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag

        for fov_column in range(clone_tag.list_widget_tags.count()):
            if clone_tag.list_widget_tags.item(fov_column).text() == "FOV":
                break

        # 'FOV' tag selected
        clone_tag.list_widget_tags.setCurrentRow(fov_column)
        clone_tag.line_edit_new_tag_name.setText("Test")
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)

        # Check 'Test' tag is in the db
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertTrue(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )

        # Value in the db
        item = self.main_window.data_browser.table_data.item(1, 0)
        scan_name = item.text()
        value = self.main_window.project.session.get_value(
            COLLECTION_CURRENT, scan_name, "Test"
        )
        value_initial = self.main_window.project.session.get_value(
            COLLECTION_INITIAL, scan_name, "Test"
        )

        # Value in the DataBrowser
        test_column = (
            self.main_window.data_browser.table_data.get_tag_column
        )("Test")
        item = self.main_window.data_browser.table_data.item(1, test_column)
        databrowser = item.text()

        # Check equality between DataBrowser and db
        self.assertEqual(value, [3.0, 3.0])
        self.assertEqual(value, ast.literal_eval(databrowser))
        self.assertEqual(value, value_initial)

        # Undo
        self.main_window.action_undo.trigger()

        # Check 'Test' tag is not in the db and not in the DataBrowser
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_CURRENT
            )
        )
        self.assertFalse(
            "Test"
            in self.main_window.project.session.get_fields_names(
                COLLECTION_INITIAL
            )
        )
        self.assertIsNone(
            (self.main_window.data_browser.table_data.get_tag_column)("Test")
        )

    def test_unnamed_proj_soft_open(self):
        """Tests unnamed project creation at software opening."""

        self.assertIsInstance(self.project, Project)
        self.assertEqual(self.main_window.project.getName(), "Unnamed project")
        tags = self.main_window.project.session.get_fields_names(
            COLLECTION_CURRENT
        )
        self.assertEqual(len(tags), 6)
        self.assertTrue(TAG_CHECKSUM in tags)
        self.assertTrue(TAG_FILENAME in tags)
        self.assertTrue(TAG_TYPE in tags)
        self.assertTrue(TAG_EXP_TYPE in tags)
        self.assertTrue(TAG_BRICKS in tags)
        self.assertTrue(TAG_HISTORY in tags)
        self.assertEqual(
            self.main_window.project.session.get_documents_names(
                COLLECTION_CURRENT
            ),
            [],
        )
        self.assertEqual(
            self.main_window.project.session.get_documents_names(
                COLLECTION_INITIAL
            ),
            [],
        )
        collections = self.main_window.project.session.get_collections_names()
        self.assertEqual(len(collections), 5)
        self.assertTrue(COLLECTION_INITIAL in collections)
        self.assertTrue(COLLECTION_CURRENT in collections)
        self.assertTrue(COLLECTION_BRICK in collections)
        self.assertTrue(COLLECTION_HISTORY in collections)
        self.assertEqual(
            self.main_window.windowTitle(),
            "MIA - Multiparametric Image Analysis "
            "(Admin mode) - Unnamed project",
        )

    def test_update_data_history(self):
        """Updates the history of data that have been re-written.

        - Tests: Project.update_data_history
        """

        # Creates a test project
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_proj_path, "test_project")

        # Gets a scan that contains a smooth brick in its history
        NII_FILE_3 = (
            "sGuerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_"
            "Guerbet_Anat-RAREpvm-000220_000.nii"
        )
        DOCUMENT_3 = os.path.join("data", "derived_data", NII_FILE_3)

        # Cleanup earlier history and check that no obsolete bricks is detected
        obsolete_bricks = self.main_window.project.update_data_history(
            [DOCUMENT_3]
        )
        self.assertEqual(obsolete_bricks, set())

    def test_update_default_value(self):
        """Updates the values when a list of default values is created.

        Tests: DefaultValueListCreation.update_default_value
        """

        # Set shortcuts for objects that are often used
        data_browser = self.main_window.data_browser

        # The objects are successively created in the following order:
        # PopUpAddTag > DefaultValueQLineEdit > DefaultValueListCreation
        pop_up = PopUpAddTag(data_browser, data_browser.project)
        text_edt = pop_up.text_edit_default_value

        # Assures the instantiation of 'DefaultValueListCreation'
        text_edt.parent.type = "list_"

        # Mocks the execution of a dialog window
        DefaultValueListCreation.show = Mock()

        # 'DefaultValueListCreation' can be instantiated with an empty
        # string, non-empty string or list
        # Only a list leads to the table values being filled
        # Empty string
        text_edt.setText("")
        text_edt.mousePressEvent(None)

        # Non-empty string
        text_edt.setText("non_empty")
        text_edt.mousePressEvent(None)
        self.assertEqual(text_edt.list_creation.table.itemAt(0, 0).text(), "")

        # List of length = 2
        text_edt.setText("[1, 2]")
        text_edt.mousePressEvent(None)

        self.assertEqual(text_edt.list_creation.table.item(0, 0).text(), "1")
        self.assertEqual(text_edt.list_creation.table.item(0, 1).text(), "2")
        self.assertEqual(text_edt.list_creation.table.columnCount(), 2)
        # ''[1]'' will become '[1]' after being passed through s
        # 'ast.literal_eval()'

        # Adds one element to the table
        text_edt.list_creation.add_element()
        self.assertEqual(text_edt.list_creation.table.columnCount(), 3)

        # Removes one element to the table
        text_edt.list_creation.remove_element()
        self.assertEqual(text_edt.list_creation.table.columnCount(), 2)

        # Resize the table
        text_edt.list_creation.resize_table()

        # Resize the table while mocking a column width of 900 elements
        text_edt.list_creation.table.setColumnWidth(0, 900)
        text_edt.list_creation.resize_table()

        # The default value can be updated with several types of data
        types = [
            FIELD_TYPE_LIST_INTEGER,
            FIELD_TYPE_LIST_FLOAT,
            FIELD_TYPE_LIST_BOOLEAN,
            FIELD_TYPE_LIST_BOOLEAN,
            FIELD_TYPE_LIST_STRING,
            FIELD_TYPE_LIST_DATE,
            FIELD_TYPE_LIST_DATETIME,
            FIELD_TYPE_LIST_TIME,
        ]
        values = [
            "[1]",
            "[1.1]",
            "[True]",
            "[False]",
            '["str"]',
            '["11/11/1111"]',
            '["11/11/1111 11:11:11.11"]',
            '["11:11:11.11"]',
        ]

        for type_, value in zip(types, values):
            text_edt.setText(value)
            text_edt.mousePressEvent(None)
            text_edt.list_creation.type = type_
            text_edt.list_creation.update_default_value()

        # Induces a 'ValueError', mocks the execution of a dialog box
        QMessageBox.exec = Mock()
        text_edt.setText('["not_boolean"]')
        text_edt.mousePressEvent(None)
        text_edt.list_creation.type = FIELD_TYPE_LIST_BOOLEAN
        text_edt.list_creation.update_default_value()

    def test_utils(self):
        """Test the utils functions."""

        self.assertEqual(table_to_database(True, FIELD_TYPE_BOOLEAN), True)
        self.assertEqual(table_to_database("False", FIELD_TYPE_BOOLEAN), False)

        format_ = "%d/%m/%Y"
        value = datetime.strptime("01/01/2019", format_).date()
        self.assertEqual(check_value_type("01/01/2019", FIELD_TYPE_DATE), True)
        self.assertEqual(
            table_to_database("01/01/2019", FIELD_TYPE_DATE), value
        )

        format_ = "%d/%m/%Y %H:%M:%S.%f"
        value = datetime.strptime("15/7/2019 16:16:55.789643", format_)
        self.assertEqual(
            check_value_type("15/7/2019 16:16:55.789643", FIELD_TYPE_DATETIME),
            True,
        )
        self.assertEqual(
            table_to_database(
                "15/7/2019 16:16:55.789643", FIELD_TYPE_DATETIME
            ),
            value,
        )

        format_ = "%H:%M:%S.%f"
        value = datetime.strptime("16:16:55.789643", format_).time()
        self.assertEqual(
            check_value_type("16:16:55.789643", FIELD_TYPE_TIME), True
        )
        self.assertEqual(
            table_to_database("16:16:55.789643", FIELD_TYPE_TIME), value
        )

    def test_visualized_tags(self):
        """Tests the popup modifying the visualized tags."""

        # Testing default tags visibility
        visible = self.main_window.project.session.get_shown_tags()
        self.assertEqual(len(visible), 4)
        self.assertTrue(TAG_FILENAME in visible)
        self.assertTrue(TAG_BRICKS in visible)
        self.assertTrue(TAG_TYPE in visible)
        self.assertTrue(TAG_EXP_TYPE in visible)

        # Testing columns displayed in the DataBrowser
        self.assertEqual(
            4, self.main_window.data_browser.table_data.columnCount()
        )
        columns_displayed = []

        for column in range(
            0, self.main_window.data_browser.table_data.columnCount()
        ):
            tag_displayed = (
                self.main_window.data_browser.table_data.horizontalHeaderItem
            )(column).text()

            if not self.main_window.data_browser.table_data.isColumnHidden(
                column
            ):
                columns_displayed.append(tag_displayed)

        self.assertEqual(sorted(visible), sorted(columns_displayed))

        # Testing that FileName tag is the first column
        self.assertEqual(
            TAG_FILENAME,
            self.main_window.data_browser.table_data.horizontalHeaderItem(
                0
            ).text(),
        )

        # Trying to set the visible tags
        QTest.mouseClick(
            self.main_window.data_browser.visualized_tags_button, Qt.LeftButton
        )
        settings = self.main_window.data_browser.table_data.pop_up

        # Testing that checksum tag isn't displayed
        settings.tab_tags.search_bar.setText(TAG_CHECKSUM)
        self.assertEqual(settings.tab_tags.list_widget_tags.count(), 0)

        # Testing that history uuid tag isn't displayed
        settings.tab_tags.search_bar.setText(TAG_HISTORY)
        self.assertEqual(settings.tab_tags.list_widget_tags.count(), 0)

        # Testing that FileName is not displayed in the list of visible tags
        settings.tab_tags.search_bar.setText("")
        visible_tags = []

        for row in range(
            0, settings.tab_tags.list_widget_selected_tags.count()
        ):
            item = settings.tab_tags.list_widget_selected_tags.item(row).text()
            visible_tags.append(item)

        self.assertEqual(len(visible_tags), 3)
        self.assertTrue(TAG_BRICKS in visible_tags)
        self.assertTrue(TAG_EXP_TYPE in visible_tags)
        self.assertTrue(TAG_TYPE in visible_tags)

        # Testing when hiding a tag
        # Bricks tag selected
        settings.tab_tags.list_widget_selected_tags.item(2).setSelected(True)
        QTest.mouseClick(
            settings.tab_tags.push_button_unselect_tag, Qt.LeftButton
        )
        visible_tags = []

        for row in range(
            0, settings.tab_tags.list_widget_selected_tags.count()
        ):
            item = settings.tab_tags.list_widget_selected_tags.item(row).text()
            visible_tags.append(item)

        self.assertEqual(len(visible_tags), 2)
        self.assertTrue(TAG_TYPE in visible_tags)
        self.assertTrue(TAG_EXP_TYPE in visible_tags)
        QTest.mouseClick(settings.push_button_ok, Qt.LeftButton)

        new_visibles = self.main_window.project.session.get_shown_tags()
        self.assertEqual(len(new_visibles), 3)
        self.assertTrue(TAG_FILENAME in new_visibles)
        self.assertTrue(TAG_EXP_TYPE in new_visibles)
        self.assertTrue(TAG_TYPE in new_visibles)

        columns_displayed = []

        for column in range(
            0, self.main_window.data_browser.table_data.columnCount()
        ):
            item = (
                self.main_window.data_browser.table_data.horizontalHeaderItem
            )(column)

            if not self.main_window.data_browser.table_data.isColumnHidden(
                column
            ):
                columns_displayed.append(item.text())

        self.assertEqual(len(columns_displayed), 3)
        self.assertTrue(TAG_FILENAME in columns_displayed)
        self.assertTrue(TAG_EXP_TYPE in columns_displayed)
        self.assertTrue(TAG_TYPE in columns_displayed)

        # Testing when showing a new tag
        QTest.mouseClick(
            self.main_window.data_browser.visualized_tags_button, Qt.LeftButton
        )
        settings = self.main_window.data_browser.table_data.pop_up
        settings.tab_tags.search_bar.setText(TAG_BRICKS)
        settings.tab_tags.list_widget_tags.item(0).setSelected(True)
        QTest.mouseClick(
            settings.tab_tags.push_button_select_tag, Qt.LeftButton
        )
        QTest.mouseClick(settings.push_button_ok, Qt.LeftButton)

        new_visibles = self.main_window.project.session.get_shown_tags()
        self.assertEqual(len(new_visibles), 4)
        self.assertTrue(TAG_FILENAME in new_visibles)
        self.assertTrue(TAG_EXP_TYPE in new_visibles)
        self.assertTrue(TAG_TYPE in new_visibles)
        self.assertTrue(TAG_BRICKS in new_visibles)

        columns_displayed = []

        for column in range(
            0, self.main_window.data_browser.table_data.columnCount()
        ):
            item = (
                self.main_window.data_browser.table_data.horizontalHeaderItem
            )(column)

            if not self.main_window.data_browser.table_data.isColumnHidden(
                column
            ):
                columns_displayed.append(item.text())

        self.assertEqual(len(columns_displayed), 4)
        self.assertTrue(TAG_FILENAME in columns_displayed)
        self.assertTrue(TAG_EXP_TYPE in columns_displayed)
        self.assertTrue(TAG_TYPE in columns_displayed)
        self.assertTrue(TAG_BRICKS in columns_displayed)


class TestMIAMainWindow(TestMIACase):
    """Tests for the main window class (MainWindow).

    :Contains:
        :Method:
            - test_check_database: checks if the database has changed
              since the scans were first imported
            - test_closeEvent: opens a project and closes the main window
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
        """Checks if the database has changed since the scans were first
        imported.

        - Tests: MainWindow.test_check_database

        - Mocks QMessageBox.exec
        """

        # Creates a new project and switches to it
        test_proj_path = self.get_new_test_project()
        self.main_window.switch_project(test_proj_path, "test_project")

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager

        # Mocks the execution of a dialog box by accepting it
        QMessageBox.exec = lambda self_, *arg: self_.accept()

        # Gets the file path
        ppl_manager.project.folder = test_proj_path
        folder = os.path.join(test_proj_path, "data", "raw_data")
        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_"
            "Guerbet_MDEFT-MDEFTpvm-000940_800.nii"
        )
        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Removes one document from the database
        os.remove(DOCUMENT_1)

        # Check if the files of the database have been modified
        # Since QMessageBox.exec is mocked, the QMessageBox's text is not
        # observed
        self.main_window.action_check_database.triggered.emit()

    def test_closeEvent(self):
        """Opens a project and closes the main window.

        - Tests: MainWindow.closeEvent
        """

        # FIXME: Does this test really bring anything new compared to other
        #        tests already performed?
        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(new_proj_path, "test_light_project")

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager

        # Gets the UID of the first brick in the brick collection, which is
        # composed of the bricks appearing in the scan history.
        bricks_coll = ppl_manager.project.session.get_documents(
            COLLECTION_BRICK
        )
        brick = bricks_coll[0]

        # Appends it to the 'brick_list'
        ppl_manager.brick_list.append(brick.ID)

        # Mocks having initialized the pipeline
        ppl_manager.init_clicked = True

        # 'self.main_window.close()' is already called by 'tearDown'
        # after each test

        # No assertion is possible since the 'self.main_window.project'
        # was deleted

        print()

    def test_create_project_pop_up(self):
        """Tries to create a new project with an already open project, with and
        without setting the projects folder path.

        - Tests:
            - MainWindow.create_project_pop_up
            - PopUpNewProject

        - Mocks:
            - PopUpQuit.exec
            - QMessageBox.exec
            - PopUpNewProject.exec
        """

        # Sets shortcuts for often used objects
        session = self.main_window.project.session

        # Creates a new project folder and switches to it
        new_proj_path = self.get_new_test_project(light=True)
        folder = os.path.join(new_proj_path, "data", "downloaded_data")
        NII_FILE_1 = (
            "Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_"
            "Guerbet_Anat-RAREpvm-000220_000.nii"
        )
        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Adds a document to the collection
        session.add_document(COLLECTION_CURRENT, DOCUMENT_1)

        # Mocks the execution of the pop-up quit
        PopUpQuit.exec = lambda self_, *args: self_.show()

        # Tries to create a project with unsaved modifications
        self.main_window.create_project_pop_up()

        # Closes the error dialog
        self.assertTrue(hasattr(self.main_window, "pop_up_close"))
        self.main_window.pop_up_close.accept()

        session.remove_document(COLLECTION_CURRENT, DOCUMENT_1)

        # Mocks the execution of a pop-up
        QMessageBox.exec = lambda self_, *args: self_.show()

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
        PopUpNewProject.exec = lambda self_, *args: None

        # Opens the "create project" pop-up
        self.main_window.create_project_pop_up()

        # Mocks the execution of a pop-up
        QMessageBox.exec = lambda *args: None

        # Tries to create a new project in the same directory of an
        # existing one
        self.main_window.exPopup.get_filename(
            (os.path.join(folder, NII_FILE_1),)
        )

        # Creates a new project
        self.main_window.exPopup.get_filename(
            (os.path.join(folder, "new_project"),)
        )

    def test_files_in_project(self):
        """Tests whether a given file is part of the project.

        - Tests: MainWindow.files_in_project
        """

        # Creates a now test project
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.project.folder = test_proj_path

        # Checks for a bool type as a file
        res = self.main_window.project.files_in_project([{"mock_key": False}])
        self.assertFalse(res)

        # Checks for a str type path located out of the project
        res = self.main_window.project.files_in_project("/out_of_project")
        self.assertFalse(res)

        # Checks for a str type path within the project
        res = self.main_window.project.files_in_project(
            os.path.join(test_proj_path, "mock_file")
        )
        self.assertTrue(res)  # Asserts it is not empty

    def test_import_data(self):
        """Opens a project and simulates importing a file from the mri_conv
        java executable.

        - Tests:
            - read_log (data_loader.py)
            - ImportProgress

        - Mocks:
            - ImportWorker.start
            - ImportProgress.exec
        """

        # Opens a test project and switches to it
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_proj_path, "test_project")

        # Creates a mocked java executable
        mock_mriconv_path = os.path.join(
            test_proj_path, "mock_mriconv", "mockapp.jar"
        )
        os.mkdir(os.path.split(mock_mriconv_path)[0])
        res = self.create_mock_jar(mock_mriconv_path)
        self.assertEqual(res, 0)

        # Sets the 'MRIManager.jar' path to a mocked java executable
        config = Config()
        config.set_mri_conv_path(os.path.normpath(mock_mriconv_path))

        # Gets information regarding the fist scan, located in the
        # 'derived_data' of the project
        DOCUMENT_1 = (self.main_window.project.session.get_documents_names)(
            "current"
        )[0]
        DOCUMENT_1_NAME = os.path.split(DOCUMENT_1)[-1].split(".")[0]

        # Gets the 'raw_data' folder path, where the scan will be import
        RAW_DATA_FLDR = os.path.join(test_proj_path, "data", "raw_data")

        # Copies a scan to the raw data folder
        shutil.copy(
            os.path.join(test_proj_path, DOCUMENT_1),
            os.path.join(RAW_DATA_FLDR, os.path.split(DOCUMENT_1)[-1]),
        )

        # Creates the .json with the tag values, in the raw data folder
        JSON_TAG_DUMP = {
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
                "units": "MHz",
                "type": "float",
                "value": [[50000.0]],
            },
        }
        JSON_TAG = os.path.join(RAW_DATA_FLDR, DOCUMENT_1_NAME + ".json")

        with open(JSON_TAG, "w") as file:
            json.dump(JSON_TAG_DUMP, file)

        # Creates the 'logExport*.json' file, in the raw data folder
        JSON_EXPORT_DUMP = [
            {
                "StatusExport": "Export ok",
                "NameFile": DOCUMENT_1_NAME,
                "Bvec_bval": "no",
            }
        ]
        JSON_EXPORT = os.path.join(
            test_proj_path, "data", "raw_data", "logExportMock.json"
        )

        with open(JSON_EXPORT, "w") as file:
            json.dump(JSON_EXPORT_DUMP, file)

        # Mocks the thread start to avoid thread deadlocking
        ImportWorker.start = lambda self_, *args: None
        ImportProgress.exec = lambda self_, *args: self_.worker.run()

        # Reads the scans added to the project
        # FIXME: Try uncommenting the following line
        # scans_added = read_log(self.main_window.project, self.main_window)

        # Mocks importing a scan, runs a mocked java executable instead
        # of the 'MRIManager.jar'
        self.main_window.import_data()

        new_scan = os.path.normpath(
            DOCUMENT_1.replace("derived_data", "raw_data")
        )
        table_data_scans = (
            self.main_window.data_browser.table_data.scans_to_visualize
        )
        table_data_scans = [
            os.path.normpath(path) for path in table_data_scans
        ]

        # Asserts that the first scan was added to the 'raw_data' folder
        self.assertIn(new_scan, table_data_scans)

    def test_open_project_pop_up(self):
        """Creates a test project and opens a project, including unsaved
        modifications.

        - Tests: MainWindow.open_project_pop_up

        - Mocks:
            - QMessageBox.exec
            - PopUpOpenProject.exec
            - PopUpQuit.exec
        """

        # Creates a test project
        test_proj_path = self.get_new_test_project(light=True)
        self.main_window.switch_project(test_proj_path, "test_project")

        # Sets shortcuts for objects that are often used
        data_browser = self.main_window.data_browser

        QMessageBox.exec = lambda self_, *arg: self_.show()

        # Resets the projects save directory
        Config().set_projects_save_path(None)

        # Tries to open a project without setting the projects save dir
        self.main_window.open_project_pop_up()
        self.main_window.msg.accept()

        # Sets the projects save dir
        config = Config(properties_path=self.properties_path)
        config.set_projects_save_path(os.path.split(test_proj_path)[0])

        PopUpOpenProject.exec = lambda self_, *arg: self_.show()

        # Opens a project
        self.main_window.open_project_pop_up()

        self.main_window.exPopup.get_filename((test_proj_path,))

        # Deletes a scan from data browser
        data_browser.table_data.selectRow(0)
        self.main_window.data_browser.table_data.remove_scan()

        # Asserts that there are unsaved modification
        self.assertTrue(self.main_window.check_unsaved_modifications())

        PopUpQuit.exec = lambda self_: self_.show()

        # Tries to open a project with unsaved modifications
        self.main_window.open_project_pop_up()
        self.main_window.pop_up_close.accept()

    def test_open_recent_project(self):
        """Creates 2 test projects and opens one by the recent projects action.

        - Tests: MainWindow.open_recent_project
        """

        # Creates 2 test projects
        proj_test_1_path = self.get_new_test_project(
            name="test_project_1", light=True
        )
        proj_test_2_path = self.get_new_test_project(
            name="test_project_2", light=True
        )

        # Switches to the first one
        self.main_window.switch_project(proj_test_1_path, "test_project_1")
        config = Config(properties_path=self.properties_path)
        config.set_projects_save_path(os.path.split(proj_test_1_path)[0])
        self.main_window.saved_projects_list.append(proj_test_1_path)

        # Saves project 1
        self.main_window.saveChoice()

        # Switches to project 2
        self.main_window.switch_project(proj_test_2_path, "test_project_2")

        # Asserts that test project 1 is shown in recent projects
        self.assertTrue(self.main_window.saved_projects_actions[0].isVisible())

        # Clicks on it
        self.main_window.saved_projects_actions[0].triggered.emit()

        # Asserts that it is now the current project
        config = Config(properties_path=self.properties_path)
        self.assertEqual(
            os.path.abspath(config.get_opened_projects()[0]), proj_test_1_path
        )

        # Deletes a scan from data browser
        self.main_window.data_browser.table_data.selectRow(0)
        # FIXME: following line raise exception, only on macos build:
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
        # While waiting to investiget and find a fix the line is commented:
        # self.main_window.data_browser.table_data.remove_scan()

        # Asserts that there are unsaved modification
        # FIXME: By commenting the previous line we have to also comment the
        # following line:
        # self.assertTrue(self.main_window.check_unsaved_modifications())

        PopUpQuit.exec = lambda self_: self_.show()

        # Tries to open a project with unsaved modifications
        self.main_window.saved_projects_actions[0].triggered.emit()

        print()

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
        pkg_lib_window.layout().children()[0].layout().children()[3].itemAt(
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
        pkg_lib_window.layout().children()[0].layout().children()[3].itemAt(
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
        pkg_lib_window.layout().children()[0].layout().children()[3].itemAt(
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
                3
            ].itemAt(0).widget().clicked.emit()
            f.close()
            sys.stdout = stdout_fileno
            pkg_lib_window.ok_clicked()

        # Opens the package library pop-up
        self.main_window.package_library_pop_up()
        pkg_lib_window = self.main_window.pop_up_package_library

        # Tries to delete PKG
        pkg_lib_window.line_edit.setText(PKG)
        pkg_lib_window.layout().children()[0].layout().children()[3].itemAt(
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
        pkg_lib_window.layout().children()[0].layout().children()[3].itemAt(
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
        pkg_lib_window.layout().children()[0].layout().children()[3].itemAt(
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
        pkg_lib_window.layout().children()[0].layout().children()[3].itemAt(
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
                3
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
        self.assertIsNone(res)

        # Clicks on the remove package button without selecting package
        rmv_pkg_button = (
            pkg_lib_window.layout()
            .children()[0]
            .layout()
            .children()[3]
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
        pkg_lib_window.remove_package_with_text(_2rem=PKG, tree_remove=False)

        # Resets the process library to its original state for nipype
        cur_state = self.proclibview_nipype_state(proc_lib_view)

        if cur_state != init_state:
            self.proclibview_nipype_reset_state(
                self.main_window, ppl_manager, init_state
            )

        # Saves the config to 'process_config.yml'
        ppl_manager.processLibrary.save_config()

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
        QMessageBox.question = Mock(return_value=QMessageBox.YesToAll)
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
        main_wnd.pop_up_preferences.use_current_mainwindow_size(main_wnd)

        # Mocks the click of the OK button on 'QMessageBox.exec'
        QMessageBox.exec = lambda x: QMessageBox.Yes

        # Programs the controller version to change to V1
        main_wnd.pop_up_preferences.control_checkbox_toggled(main_wnd)
        main_wnd.pop_up_preferences.control_checkbox_changed = True
        self.assertTrue(main_wnd.get_controller_version())

        # Cancels the above change
        main_wnd.pop_up_preferences.control_checkbox_toggled(main_wnd)
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

            # Asserts that MATLAB was enabled and MATLAB standalone
            # remains disabled
            config = Config(properties_path=self.properties_path)
            self.assertTrue(config.get_use_matlab())
            self.assertFalse(config.get_use_matlab_standalone())

            main_wnd.software_preferences_pop_up()  # Reopens the window

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

        DOCUMENT_1 = (self.main_window.project.session.get_documents_names)(
            "current"
        )[0]

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

        DOCUMENT_1 = (self.main_window.project.session.get_documents_names)(
            "current"
        )[0]
        DOCUMENT_2 = (self.main_window.project.session.get_documents_names)(
            "current"
        )[1]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_ctrler = self.main_window.pipeline_manager.nodeController

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
        input_filter.update_tags()
        self.add_visualized_tag("AcquisitionDate")
        # FIXME: The following statement is always True (not the correct test)
        self.assertTrue(
            type(input_filter.table_data.get_tag_column("AcquisitionDate"))
            == int
        )

        # Updates the tag to filter with
        input_filter.update_tag_to_filter()

        input_filter.push_button_tag_filter.setText("FileName")
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

        DOCUMENT_1 = (self.main_window.project.session.get_documents_names)(
            "current"
        )[0]

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
        DOCUMENT_1 = (self.main_window.project.session.get_documents_names)(
            "current"
        )[0]
        DOCUMENT_2 = (self.main_window.project.session.get_documents_names)(
            "current"
        )[1]

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
        plug_filter.push_button_tag_filter.setText("FileName")
        # TODO: select tag to filter with

        # Closes the filter for the plug "in_files"
        plug_filter.ok_clicked()

        # Assert the modified value
        self.assertIn(
            str(Path(DOCUMENT_2)),
            str(Path(node.get_plug_value("in_files")[0])),
        )

        # Opens a filter for the plug "in_files", now with a "scans_list"
        node_controller.scan_list = (
            self.main_window.project.session.get_documents_names
        )("current")
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

        DOCUMENT_1 = self.main_window.project.session.get_documents_names(
            "current"
        )[0]
        DOCUMENT_2 = self.main_window.project.session.get_documents_names(
            "current"
        )[1]

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

        pipeline_manager.project.session.add_document(
            COLLECTION_BRICK, brick_id
        )

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
        pipeline_manager.project.session.get_document(
            COLLECTION_CURRENT, DOCUMENT_1
        )
        pipeline_manager.project.session.get_document(
            COLLECTION_CURRENT, DOCUMENT_2
        )
        has_document = pipeline_manager.project.session.has_document
        self.assertTrue(has_document(COLLECTION_CURRENT, DOCUMENT_1))
        self.assertTrue(has_document(COLLECTION_CURRENT, DOCUMENT_2))

    def test_add_plug_value_to_database_non_list_type(self):
        """Opens a project, adds a 'Rename' process, exports a non list type
        input plug and adds it to the database.

        - Tests: PipelineManagerTab(QWidget).add_plug_value_to_database()
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        DOCUMENT_1 = self.main_window.project.session.get_documents_names(
            "current"
        )[0]

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

        pipeline_manager.project.session.add_document(
            COLLECTION_BRICK, brick_id
        )

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

        has_document = pipeline_manager.project.session.has_document

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
        pipeline_manager.project.session.get_document(
            COLLECTION_CURRENT, DOCUMENT_1
        )
        self.assertTrue(has_document(COLLECTION_CURRENT, DOCUMENT_1))
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
                        "field_type": "string",
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
                        "field_type": "string",
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

            if session.has_document(COLLECTION_CURRENT, P_VALUE):
                session.remove_document(COLLECTION_CURRENT, P_VALUE)
            if session.has_document(COLLECTION_CURRENT, DOCUMENT_1):
                session.remove_document(COLLECTION_CURRENT, DOCUMENT_1)
            if session.has_document(COLLECTION_INITIAL, P_VALUE):
                session.remove_document(COLLECTION_INITIAL, P_VALUE)
            if session.has_document(COLLECTION_INITIAL, DOCUMENT_1):
                session.remove_document(COLLECTION_INITIAL, DOCUMENT_1)

        # Sets shortcuts for often used objects
        ppl_manager = self.main_window.pipeline_manager
        session = ppl_manager.project.session
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

        session.add_document(COLLECTION_CURRENT, DOCUMENT_1)

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

        ppl_manager.project.session.add_document(COLLECTION_BRICK, brick_id)

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
        SCAN_1 = session.get_document(COLLECTION_CURRENT, DOCUMENT_1)
        session.get_document = mock_get_document

        # Mocks the value setter on the session
        session.set_values = Mock()

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
        attributes = {"Checksum": "Checksum_value"}
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

        DOCUMENT_1 = self.main_window.project.session.get_documents_names(
            "current"
        )[0]

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

        pipeline_manager.project.session.add_document(
            COLLECTION_BRICK, brick_id
        )

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
        print("\n\n** an exception message is expected below\n")
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
        process.study_config.project = Mock()
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

        # Mocks the allocation of the pipeline into another thread
        # This function seem to require a different number of arguments
        # depending on the platform, therefore a 'Mock' is used
        QThread.start = Mock()

        # Pipeline fails while running, due to capsul import error
        ppl_manager.runPipeline()

        # Directly runs the 'QThread' object, as the only solution found
        # to run the pipeline during the test routine
        ppl_manager.progress.worker.run()

        # Sends the signal to finish the pipeline
        ppl_manager.progress.worker.finished.emit()

        self.assertEqual(ppl_manager.last_run_pipeline, ppl)
        QThread.start.assert_called_once()

        # Pipeline is stopped by the user, the pipeline fails before running
        ppl_manager.runPipeline()
        ppl_manager.stop_execution()
        ppl_manager.progress.worker.run()
        ppl_manager.progress.worker.finished.emit()

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


class Test_Z_MIAOthers(TestMIACase):
    """Tests for other parts of the MIA software that do not relate much
    with the other classes.

    :Contains:
        :Method:
            - test_iteration_table: plays with the iteration table
            - test_process_library: install the brick_test and then remove it
            - test_check_setup: check that Mia's configuration control is
                                working correctly
            - test_verify_processes: check that Mia's processes control is
                                     working correctly
    """

    def test_iteration_table(self):
        """Opens a new project, initializes the pipeline iteration and changes
        its parameters.

        - Tests: IterationTable

        - Mocks: the execution of a PopUpSelectTagCountTable and a QDialog
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Sets shortcuts for objects that are often used
        iter_table = self.main_window.pipeline_manager.iterationTable
        session = iter_table.project.session
        ppl_manager = self.main_window.pipeline_manager
        ppl_editor = ppl_manager.pipelineEditorTabs.get_current_editor()

        # Mocks the execution of a dialog box to avoid asynchronous shot
        QDialog.exec_ = Mock(return_value=QDialog.Accepted)

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
        self.assertEqual(iter_table.values_list[-1][0], [50000.0])

        # Removes a tag and asserts that a tag button was removed
        iter_table.remove_tag()
        self.assertEqual(len(iter_table.push_buttons), 2)

        # Mocks the execution of 'PopUpSelectTagCountTable' to avoid
        # asynchronous shot
        PopUpSelectTagCountTable.exec_ = Mock(return_value=True)

        # Selects a tag to iterate over, tests 'select_iteration_tag' while
        # mocking a 'PopUpSelectTagCountTable'.
        # Due to the above mock, 'iterated_tag' is set as None
        ppl_editor.iterated_tag = "BandWidth"
        iter_table.select_iteration_tag()
        # iter_table.combo_box.clear()
        # iter_table.combo_box.addItems(['[50000.0]'])
        self.assertIsNone(ppl_editor.iterated_tag)

        # Filters the scans matching the selected  'iterated_tag'
        # Since the execution is mocked, 'tag_values_list' becomes empty
        iter_table.filter_values()
        self.assertTrue(isinstance(ppl_editor.tag_values_list, list))
        self.assertTrue(len(ppl_editor.tag_values_list) == 0)

        # Updates the button with the selected tag
        iter_table.update_selected_tag("Bandwidth")

        # Selects the visualized tag
        iter_table.select_visualized_tag(0)

        # Sends the data browser scans to the pipeline manager and updates the
        # iterated tags
        SCANS_LIST = iter_table.project.session.get_documents_names("current")
        ppl_manager.scan_list = SCANS_LIST
        iter_table.update_iterated_tag()

        # Updates the iteration table, tests 'update_table' while
        # mocking the execution of 'filter_documents'

        DOC_1_NAME = SCANS_LIST[0]
        DOC_1 = iter_table.project.session.get_document("current", DOC_1_NAME)

        session.filter_documents = Mock(return_value=[DOC_1])
        ppl_editor.iterated_tag = "BandWidth"

        iter_table.update_table()

        # Asserts that the iteration table has one item
        self.assertIsNotNone(iter_table.iteration_table.item(0, 0))
        self.assertIsNone(iter_table.iteration_table.item(1, 0))

    def test_process_library(self):
        """Inserts a row, mimes and changes the data and deletes it.

        - Tests: ProcessLibrary

        -Mocks:
            - QMessageBox.exec
            - QMessageBox.question

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
        ppl_manager.processLibrary.save_config()
        proc_lib = ppl_manager.processLibrary.process_library

        # Switches to pipeline manager
        self.main_window.tabs.setCurrentIndex(2)

        # Gets the child count
        child_count = proc_lib._model.getNode(QModelIndex()).childCount()
        row_data = "untitled" + str(child_count)

        # Adds a row to the process library
        proc_lib._model.insertRow(0)

        # Gets its index and selects it
        row_index = self.find_item_by_data(proc_lib, row_data)
        self.assertIsNotNone(row_index)
        proc_lib.selectionModel().select(
            row_index, QItemSelectionModel.SelectCurrent
        )

        # Mimes the data of the row widget
        mime_data = proc_lib._model.mimeData([row_index])
        self.assertEqual(
            mime_data.data("component/name").data(),
            bytes(row_data, encoding="utf-8"),
        )

        # Changes the data of the row
        proc_lib._model.setData(row_index, "untitled101")
        self.assertEqual(row_index.data(), "untitled101")

        # Mocks the execution of a dialog box
        QMessageBox.exec = lambda *args: None
        QMessageBox.question = lambda *args: QMessageBox.Yes

        # Deletes the row by pressing the del key
        event = Mock()
        event.key = lambda *args: Qt.Key_Delete
        proc_lib.keyPressEvent(event)

        # Mocks a mouse press event of the first item of the process lib
        mouse_event = QtGui.QMouseEvent
        mouse_event.pos = lambda *args: QPoint(0, 0)
        mouse_event.button = lambda *args: Qt.RightButton

        # Mocks the return value of 'mousePressEvent'
        QTreeView.mousePressEvent = lambda *args: True

        # Adds a row to the process library
        proc_lib._model.insertRow(0)

        # Mocks selecting 'Delete package'
        QMenu.exec_ = lambda *args: proc_lib.remove

        res = proc_lib.mousePressEvent(mouse_event)
        self.assertTrue(res)

        # Adds a row to the process library
        proc_lib._model.insertRow(0)

        # Mocks selecting 'Delete package'
        QMenu.exec_ = lambda *args: proc_lib.action_delete

        proc_lib.mousePressEvent(mouse_event)

    def test_check_setup(self):
        """Check that Mia's configuration control is working correctly.

        - Tests: utils.verify_setup()
        """
        dot_mia_config = os.path.join(
            os.path.dirname(self.properties_path), "configuration_path.yml"
        )

        QTimer.singleShot(1000, self.execute_QDialogAccept)
        verify_setup(dev_mode=True, dot_mia_config=dot_mia_config)

    def test_verify_processes(self):
        """Check that Mia's processes control is working correctly

        - Tests: utils.verify_processes()
        """

        verify_processes("toto", "titi", "tata")


if __name__ == "__main__":
    # Install the custom Qt message handler
    qInstallMessageHandler(qt_message_handler)
    unittest.main()
