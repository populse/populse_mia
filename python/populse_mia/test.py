"""Unitary tests.

:Contains:
    :Class:
        - TestMIADataBrowser
        - TestMIAPipelineManager
        - TestMIAPipelineManagerTab

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

### General imports:

#  PyQt5 import

from PyQt5 import QtGui
from PyQt5.QtCore import (QCoreApplication, QEvent, QPoint, Qt, QTimer,
                          QT_VERSION_STR)
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (QApplication, QDialog, QMessageBox,
                             QTableWidgetItem)

# Nipype import
from nipype.interfaces import Rename, Select
from nipype.interfaces.base.traits_extension import InputMultiObject
from nipype.interfaces.spm import Smooth, Threshold

# other import
import ast
import os
import shutil
import sys
import tempfile
import threading
import unittest
import uuid
import yaml
from datetime import datetime
from functools import partial
from packaging import version
from pathlib import Path
from traits.api import Undefined, TraitListObject
from unittest.mock import Mock, MagicMock

if not os.path.dirname(os.path.dirname(os.path.realpath(__file__))) in sys.path:
    # "developer" mode
    root_dev_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))))

    # Adding populse_mia
    print('\n- Mia in "developer" mode\n')

    if os.path.isdir(os.path.join(root_dev_dir, 'populse-mia')):
        mia_dev_dir = os.path.join(root_dev_dir, 'populse-mia', 'python')

    else:
        mia_dev_dir = os.path.join(root_dev_dir, 'populse_mia', 'python')

    sys.path.insert(0, mia_dev_dir)
    del mia_dev_dir

    # Adding mia_processes:
    if os.path.isdir(os.path.join(root_dev_dir, 'mia_processes')):
        mia_processes_dev_dir = os.path.join(root_dev_dir, 'mia_processes',
                                             'python')
        print('- Using mia_processes package from {} '
              '...'.format(mia_processes_dev_dir))
        sys.path.insert(1, mia_processes_dev_dir)
        del mia_processes_dev_dir

    # Adding populse_db:
    if os.path.isdir(os.path.join(root_dev_dir, 'populse_db')):
        populse_db_dev_dir = os.path.join(root_dev_dir, 'populse_db', 'python')
        print('- Using populse_db package from {} '
              '...'.format(populse_db_dev_dir))
        sys.path.insert(1, populse_db_dev_dir)
        del populse_db_dev_dir

    # Adding capsul:
    if os.path.isdir(os.path.join(root_dev_dir, 'capsul')):
        capsul_dev_dir = os.path.join(root_dev_dir, 'capsul')
        print('- Using capsul package from {} '
              '...'.format(capsul_dev_dir))
        sys.path.insert(1, capsul_dev_dir)
        del capsul_dev_dir

    # Adding soma-base:
    if os.path.isdir(os.path.join(root_dev_dir, 'soma-base')):
        soma_base_dev_dir = os.path.join(root_dev_dir, 'soma-base', 'python')
        print('- Using soma-base package from {} '
              '...'.format(soma_base_dev_dir))
        sys.path.insert(1, soma_base_dev_dir)
        del soma_base_dev_dir

    # Adding soma-workflow:
    if os.path.isdir(os.path.join(root_dev_dir, 'soma-workflow')):
        soma_workflow_dev_dir = os.path.join(root_dev_dir, 'soma-workflow',
                                             'python')
        print('- Using soma-workflow package from {} '
              '...'.format(soma_workflow_dev_dir))
        sys.path.insert(1, soma_workflow_dev_dir)
        del soma_workflow_dev_dir

### Imports after defining the location of populse packages in the case of a
# developer configuration:

# capsul import
from capsul.api import (get_process_instance, Process, ProcessNode,
                        PipelineNode, Switch)
from capsul.attributes.completion_engine import ProcessCompletionEngine
from capsul.engine import CapsulEngine
from capsul.pipeline.pipeline import Pipeline
from capsul.pipeline.pipeline_workflow import workflow_from_pipeline
from capsul.pipeline.process_iteration import ProcessIteration
from capsul.process.process import NipypeProcess

# mia_processes import
from mia_processes.bricks.tools import Input_Filter

# populse_mia import
from populse_mia.data_manager.project import (COLLECTION_BRICK,
                                              COLLECTION_CURRENT,
                                              COLLECTION_HISTORY,
                                              COLLECTION_INITIAL, Project,
                                              TAG_BRICKS, TAG_CHECKSUM,
                                              TAG_EXP_TYPE, TAG_FILENAME,
                                              TAG_HISTORY, TAG_ORIGIN_USER,
                                              TAG_TYPE)
from populse_mia.data_manager.project_properties import SavedProjects
from populse_mia.software_properties import Config, verCmp
from populse_mia.user_interface.data_browser.modify_table import ModifyTable
from populse_mia.user_interface.main_window import MainWindow
from populse_mia.user_interface.pipeline_manager.pipeline_editor import (
                                                                  save_pipeline)
from populse_mia.user_interface.pipeline_manager.pipeline_manager_tab import (
                                                                    RunProgress)
from populse_mia.user_interface.pipeline_manager.process_library import (
                                                           InstallProcesses,
                                                           PackageLibraryDialog)
from populse_mia.user_interface.pop_ups import (PopUpNewProject,
                                                PopUpOpenProject)
from populse_mia.utils.utils import check_value_type, table_to_database

# populse_db import
from populse_db.database import (FIELD_TYPE_BOOLEAN, FIELD_TYPE_DATE,
                                 FIELD_TYPE_DATETIME, FIELD_TYPE_INTEGER,
                                 FIELD_TYPE_STRING, FIELD_TYPE_TIME)

# soma_workflow import
from soma_workflow import constants as swconstants


# Working from the scripts directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Disables any etelemetry check.
if 'NO_ET' not in os.environ:
    os.environ['NO_ET'] = "1"


class TestMIADataBrowser(unittest.TestCase):
    """Tests for the data browser tab

    :Contains:
        :Method:
            - edit_databrowser_list: change value to [25000] for a tag in
              DataBrowser
            - execute_QMessageBox_clickClose: press the Close button of a
              QMessageBox instance
            - execute_QMessageBox_clickOk: press the Ok button of a QMessageBox
              instance
            - get_new_test_project: create a temporary project that can be
              safely modified
            - setUp: called automatically before each test method
            - tearDown: cleans up after each test method
            - setUpClass: called before tests in the individual class
            - tearDownClass: called after tests in the individual class
            - test_add_path: tests the popup to add a path
            - test_add_tag: tests the pop up adding a tag
            - test_advanced_search: tests the advanced search widget
            - test_brick_history: tests the brick history popup
            - test_clear_cell: tests the method clearing cells
            - test_clone_tag: tests the pop up cloning a tag
            - test_count_table: tests the count table popup
            - test_mia_preferences: tests the Mia preferences popup
            - test_modify_table: tests the modify table module
            - test_multiple_sort: tests the multiple sort popup
            - test_open_project: tests project opening
            - test_open_project_filter: tests project filter opening
            - test_project_properties: tests saved projects addition and removal
            - test_proj_remov_from_cur_proj: tests that the projects are
              removed from the list of current projects
            - test_rapid_search: tests the rapid search bar
            - test_remove_scan: tests scans removal in the DataBrowser
            - test_remove_tag: tests the popup removing user tags
            - test_reset_cell: tests the method resetting the selected cells
            - test_reset_column: tests the method resetting the columns
              selected
            - test_reset_row: test row reset
            - test_save_project: test opening & saving of a project
            - test_send_doc_to_pip: tests the popup sending the documents
              to the pipeline manager
            - test_set_value: tests the values modifications
            - test_sort: tests the sorting in the DataBrowser
            - test_tab_change: tests the tab change from data browser to
              pipeline manager
            - test_undo_redo_databrowser: tests the DataBrowser undo/redo
            - test_unnamed_proj_soft_open: tests unnamed project creation at
              software opening
            - test_utils: test the utils functions
            - test_visualized_tags: tests the popup modifying the visualized
              tags
    """

    def edit_databrowser_list(self, value):
        """Change value for a tag in DataBrowser

        :param value: the new value
        """

        w = QApplication.activeWindow()
        item = w.table.item(0, 0)
        item.setText(value)
        w.update_table_values(True)

    def execute_QMessageBox_clickClose(self):
        """
        Press the Close button of a QMessageBox instance
        """

        w = QApplication.activeWindow()

        if isinstance(w, QMessageBox):
            close_button = w.button(QMessageBox.Close)
            QTest.mouseClick(close_button, Qt.LeftButton)

    def execute_QMessageBox_clickOk(self):
        """
        Press the Ok button of a QMessageBox instance
        """

        w = QApplication.activeWindow()

        if isinstance(w, QMessageBox):
            close_button = w.button(QMessageBox.Ok)
            QTest.mouseClick(close_button, Qt.LeftButton)

    def get_new_test_project(self):
        """
        Copy the test project in a location we can modify safely
        """

        project_path = os.path.join(self.config_path, 'project_8')

        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        config = Config(config_path=self.config_path)
        mia_path = config.get_mia_path()
        project_8_path = os.path.join(mia_path, 'resources', 'mia',
                                      'project_8')
        shutil.copytree(project_8_path, project_path)
        return project_path

    def setUp(self):
        """
        Called before each test
        """

        # All the tests are run in admin mode
        config = Config(config_path=self.config_path)
        config.set_user_mode(False)
        self.app = QApplication.instance()

        if self.app is None:
            self.app = QApplication(sys.argv)

        self.project = Project(None, True)
        self.main_window = MainWindow(self.project, test=True)

    def tearDown(self):
        """
        Called after each test
        """

        self.main_window.close()
        # Removing the opened projects (in CI, the tests are run twice)
        config = Config(config_path=self.config_path)
        config.set_opened_projects([])
        config.saveConfig()
        self.app.exit()

    @classmethod
    def setUpClass(cls):
        """
        Called once at the beginning of the class
        """

        cls.config_path = tempfile.mkdtemp(prefix='mia_tests')
        # hack the Config class to get config_path, because some Config
        # instances are created out of our control in the code
        Config.config_path = cls.config_path

    @classmethod
    def tearDownClass(cls):
        """
        Called once at the end of the class
        """

        if os.path.exists(cls.config_path):
            shutil.rmtree(cls.config_path)

    def test_add_path(self):
        """
        Tests the popup to add a path
        """

        QTest.mouseClick(self.main_window.data_browser.addRowLabel,
                         Qt.LeftButton)
        add_path = self.main_window.data_browser.table_data.pop_up_add_path

        QTest.mouseClick(add_path.ok_button, Qt.LeftButton)
        self.assertEqual(add_path.msg.text(), "Invalid arguments")

        add_path.file_line_edit.setText(os.path.join(".",
                                                     "test_not_existing.py"))
        add_path.type_line_edit.setText("Python")
        QTest.mouseClick(add_path.ok_button, Qt.LeftButton)
        self.assertEqual(add_path.msg.text(), "Invalid arguments")

        add_path.file_line_edit.setText(os.path.join(".", "test.py"))
        add_path.type_line_edit.setText("Python")
        QTest.mouseClick(add_path.ok_button, Qt.LeftButton)

        self.assertEqual(self.main_window.project.session.get_documents_names(
                                                            COLLECTION_CURRENT),
                         [os.path.join('data', 'downloaded_data', 'test.py')])
        self.assertEqual(self.main_window.project.session.get_documents_names(
                                                            COLLECTION_INITIAL),
                         [os.path.join('data', 'downloaded_data', 'test.py')])
        self.assertEqual(self.main_window.data_browser.table_data.rowCount(),
                         1)
        self.assertEqual(self.main_window.data_browser.table_data.item(0, 0
                                                                       ).text(),
                         os.path.join('data', 'downloaded_data', 'test.py'))

    def test_add_tag(self):
        """
        Tests the pop-up adding a tag
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Testing without tag name
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        QTimer.singleShot(1000, self.execute_QMessageBox_clickClose)
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(add_tag.msg.text(), "The tag name cannot be empty")

        QApplication.processEvents()

        # Testing with tag name already existing
        add_tag.text_edit_tag_name.setText("Type")
        QTimer.singleShot(1000, self.execute_QMessageBox_clickClose)
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(add_tag.msg.text(), "This tag name already exists")

        QApplication.processEvents()

        # Testing with wrong type
        add_tag.text_edit_tag_name.setText("Test")
        add_tag.combo_box_type.setCurrentText(FIELD_TYPE_INTEGER)
        add_tag.type = FIELD_TYPE_INTEGER
        add_tag.text_edit_default_value.setText("Should be integer")
        QTimer.singleShot(1000, self.execute_QMessageBox_clickClose)
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertEqual(add_tag.msg.text(), "Invalid default value")

        QApplication.processEvents()

        # Testing when everything is ok
        add_tag.text_edit_tag_name.setText("Test")
        add_tag.text_edit_default_value.setText("def_value")
        add_tag.type = FIELD_TYPE_STRING

        QTest.qWait(100)

        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        for document in self.main_window.project.session.get_documents_names(
                                                            COLLECTION_CURRENT):
            self.assertEqual(self.main_window.project.session.get_value(
                                          COLLECTION_CURRENT, document, "Test"),
                             "def_value")

        for document in self.main_window.project.session.get_documents_names(
                                                            COLLECTION_INITIAL):
            self.assertEqual(self.main_window.project.session.get_value(
                                          COLLECTION_INITIAL, document, "Test"),
                             "def_value")

        test_column = self.main_window.data_browser.table_data.get_tag_column(
                                                                         "Test")

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row,
                                                                 test_column)
            self.assertEqual(item.text(), "def_value")

        QApplication.processEvents()

        # Testing with list type
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        add_tag.text_edit_tag_name.setText("Test_list")

        combo_box_types = ["String", "Integer", "Float", "Boolean", "Date",
                           "Datetime", "Time", "String List", "Integer List",
                           "Float List", "Boolean List", "Date List",
                           "Datetime List", "Time List"]

        for data_type in combo_box_types:
            add_tag.combo_box_type.setCurrentText(data_type)

        add_tag.combo_box_type.setCurrentText("Integer List")
        QTest.mouseClick(add_tag.text_edit_default_value, Qt.LeftButton)
        QTest.mouseClick(
                add_tag.text_edit_default_value.list_creation.add_element_label,
                Qt.LeftButton)
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

        QTest.qWait(100)

        QTest.mouseClick(
                        add_tag.text_edit_default_value.list_creation.ok_button,
                        Qt.LeftButton)
        self.assertEqual(add_tag.text_edit_default_value.text(), "[1, 2, 3]")
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)

        test_list_column = (self.main_window.data_browser.table_data.
                            get_tag_column("Test_list"))

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(
                                                               row,
                                                               test_list_column)
            self.assertEqual(item.text(), "[1, 2, 3]")

        QApplication.processEvents()

    def test_advanced_search(self):
        """
        Tests the advanced search widget
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)

        QTest.mouseClick(self.main_window.data_browser.advanced_search_button,
                         Qt.LeftButton)

        # Testing - and + buttons
        self.assertEqual(1,
                         len(
                            self.main_window.data_browser.advanced_search.rows))
        first_row = self.main_window.data_browser.advanced_search.rows[0]
        QTest.mouseClick(first_row[6], Qt.LeftButton)
        self.assertEqual(2,
                         len(
                            self.main_window.data_browser.advanced_search.rows))
        second_row = self.main_window.data_browser.advanced_search.rows[1]
        QTest.mouseClick(second_row[5], Qt.LeftButton)
        self.assertEqual(1,
                         len(
                            self.main_window.data_browser.advanced_search.rows))
        first_row = self.main_window.data_browser.advanced_search.rows[0]
        QTest.mouseClick(first_row[5], Qt.LeftButton)
        self.assertEqual(1,
                         len(
                            self.main_window.data_browser.advanced_search.rows))

        field = self.main_window.data_browser.advanced_search.rows[0][2]
        condition = self.main_window.data_browser.advanced_search.rows[0][3]
        value = self.main_window.data_browser.advanced_search.rows[0][4]
        field_filename_index = field.findText(TAG_FILENAME)
        field.setCurrentIndex(field_filename_index)
        condition_contains_index = condition.findText("CONTAINS")
        condition.setCurrentIndex(condition_contains_index)
        value.setText("G1")
        QTest.mouseClick(self.main_window.data_browser.advanced_search.search,
                         Qt.LeftButton)

        # Testing that only G1 scans are displayed with the filter applied
        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 2)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)

        # Testing that every scan is back when clicking again on advanced search
        QTest.mouseClick(self.main_window.data_browser.advanced_search_button,
                         Qt.LeftButton)
        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)

    def test_brick_history(self):
        """
        Tests the brick history popup
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        bricks_column = (self.main_window.data_browser.table_data.
                         get_tag_column)("History")
        bricks_widget = self.main_window.data_browser.table_data.cellWidget(
                                                                  0,
                                                                  bricks_column)
        smooth_button = bricks_widget.layout().itemAt(0).widget()
        self.assertEqual(smooth_button.text(), "smooth_1")
        QTest.mouseClick(smooth_button, Qt.LeftButton)
        brick_history = (self.main_window.data_browser.table_data.
                         brick_history_popup)
        brick_table = brick_history.table
        self.assertEqual(brick_table.horizontalHeaderItem(0).text(), "Name")
        self.assertEqual(brick_table.horizontalHeaderItem(1).text(), "Init")
        self.assertEqual(brick_table.horizontalHeaderItem(2).text(),
                         "Init Time")
        self.assertEqual(brick_table.horizontalHeaderItem(3).text(), "Exec")
        self.assertEqual(brick_table.horizontalHeaderItem(4).text(),
                         "Exec Time")
        self.assertEqual(brick_table.horizontalHeaderItem(5).text(),
                         "data_type")
        self.assertEqual(brick_table.horizontalHeaderItem(6).text(), "fwhm")
        self.assertEqual(brick_table.horizontalHeaderItem(7).text(),
                         "implicit_masking")
        self.assertEqual(brick_table.horizontalHeaderItem(8).text(),
                         "in_files")
        self.assertEqual(brick_table.horizontalHeaderItem(9).text(),
                         "matlab_cmd")
        self.assertEqual(brick_table.horizontalHeaderItem(10).text(), "mfile")
        self.assertEqual(brick_table.item(0, 0).text(), "smooth_1")
        self.assertEqual(brick_table.item(0, 1).text(), "Done")
        self.assertEqual(brick_table.item(0, 2).text(),
                         "2022-04-05 14:22:30.298043")
        self.assertEqual(brick_table.item(0, 3).text(), "Done")
        self.assertEqual(brick_table.item(0, 4).text(),
                         "2022-04-05 14:22:30.298043")
        self.assertEqual(brick_table.item(0, 5).text(), "0")
        self.assertEqual(brick_table.item(0, 6).text(), "[6.0, 6.0, 6.0]")
        self.assertEqual(brick_table.item(0, 7).text(), "False")
        self.assertEqual(brick_table.cellWidget(0, 8).children()[1].text(),
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                         "pvm-000220_000.nii")
        self.assertEqual(brick_table.item(0, 9).text(),
                         "/usr/local/SPM/spm12_standalone/run_spm12.sh "
                         "/usr/local/MATLAB/MATLAB_Runtime/v95 script")
        self.assertEqual(brick_table.item(0, 10).text(), "True")

    def test_clear_cell(self):
        """
        Tests the method clearing cells
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Selecting a cell
        bw_column = self.main_window.data_browser.table_data.get_tag_column(
                                                                    "BandWidth")
        bw_item = self.main_window.data_browser.table_data.item(0, bw_column)
        bw_item.setSelected(True)
        self.assertEqual(float(bw_item.text()[1:-1]), 50000.0)
        self.assertEqual(self.main_window.project.session.get_value(
                             COLLECTION_CURRENT,
                             "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                             "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                             "pvm-000220_000.nii",
                             "BandWidth"),
                         [50000.0])

        # Clearing the cell
        bw_item = self.main_window.data_browser.table_data.item(0, bw_column)
        bw_item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.clear_cell()
        self.main_window.data_browser.table_data.itemChanged.connect(
                     self.main_window.data_browser.table_data.change_cell_color)

        # Checking that it's empty
        bw_item = self.main_window.data_browser.table_data.item(0, bw_column)
        self.assertEqual(bw_item.text(), "*Not Defined*")
        self.assertIsNone(self.main_window.project.session.get_value(
                             COLLECTION_CURRENT,
                             "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                             "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                             "pvm-000220_000.nii",
                             "BandWidth"))

    def test_clone_tag(self):
        """
        Tests the pop up cloning a tag
        """

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
        self.assertEqual(clone_tag.msg.text(),
                         "The tag to clone must be selected")

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
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))
        test_row = self.main_window.project.session.get_field(
                                                             COLLECTION_CURRENT,
                                                             "Test")
        bandwidth_row = self.main_window.project.session.get_field(
                                                             COLLECTION_CURRENT,
                                                             "BandWidth")
        self.assertEqual(test_row.description, bandwidth_row.description)
        self.assertEqual(test_row.unit, bandwidth_row.unit)
        self.assertEqual(test_row.default_value, bandwidth_row.default_value)
        self.assertEqual(test_row.field_type, bandwidth_row.field_type)
        self.assertEqual(test_row.origin, TAG_ORIGIN_USER)
        self.assertEqual(test_row.visibility, True)
        test_row = self.main_window.project.session.get_field(
                                                             COLLECTION_INITIAL,
                                                             "Test")
        bandwidth_row = self.main_window.project.session.get_field(
                                                             COLLECTION_INITIAL,
                                                             "BandWidth")
        self.assertEqual(test_row.description, bandwidth_row.description)
        self.assertEqual(test_row.unit, bandwidth_row.unit)
        self.assertEqual(test_row.default_value, bandwidth_row.default_value)
        self.assertEqual(test_row.field_type, bandwidth_row.field_type)
        self.assertEqual(test_row.origin, TAG_ORIGIN_USER)
        self.assertEqual(test_row.visibility, True)

        for document in self.main_window.project.session.get_documents_names(
                                                            COLLECTION_CURRENT):
            self.assertEqual(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             document,
                                                             "Test"),
                             self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             document,
                                                             "BandWidth"))

        for document in self.main_window.project.session.get_documents_names(
                                                            COLLECTION_INITIAL):
            self.assertEqual(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             document,
                                                             "Test"),
                             self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             document,
                                                             "BandWidth"))

        test_column = self.main_window.data_browser.table_data.get_tag_column(
                                                                         "Test")
        bw_column = self.main_window.data_browser.table_data.get_tag_column(
                                                                    "BandWidth")

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item_bw = self.main_window.data_browser.table_data.item(row,
                                                                    bw_column)
            item_test = self.main_window.data_browser.table_data.item(
                                                                    row,
                                                                    test_column)
            self.assertEqual(item_bw.text(), item_test.text())

    def test_count_table(self):
        """
        Tests the count table popup
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        QTest.mouseClick(self.main_window.data_browser.count_table_button,
                         Qt.LeftButton)
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

        self.assertEqual(count_table.table.horizontalHeaderItem(0).text(),
                         "BandWidth")
        self.assertEqual(
                         count_table.table.horizontalHeaderItem(1).text()[1:-1],
                         "75.0")
        self.assertAlmostEqual(float(count_table.table.horizontalHeaderItem(2
                                                                ).text()[1:-1]),
                               5.8239923)
        self.assertEqual(count_table.table.horizontalHeaderItem(3).text()[1:-1],
                         "5.0")
        self.assertEqual(count_table.table.verticalHeaderItem(3).text(),
                         "Total")
        self.assertEqual(count_table.table.item(0, 0).text()[1:-1], "50000.0")
        self.assertEqual(count_table.table.item(1, 0).text()[1:-1], "25000.0")
        self.assertAlmostEqual(float(count_table.table.item(2, 0).text()[1:-1]),
                               65789.48)
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
        """
        Tests the MIA preferences popup
        """

        config = Config(config_path=self.config_path)
        old_auto_save = config.isAutoSave()
        self.assertEqual(old_auto_save, False)

        # Auto save activated
        self.main_window.action_software_preferences.trigger()
        properties = self.main_window.pop_up_preferences
        properties.projects_save_path_line_edit.setText(
                                                       tempfile.mkdtemp(
                                                       prefix='projects_tests'))
        properties.tab_widget.setCurrentIndex(1)
        properties.save_checkbox.setChecked(True)
        QTest.mouseClick(properties.push_button_ok, Qt.LeftButton)
        QTest.qWait(500)
        self.execute_QMessageBox_clickOk()

        config = Config(config_path=self.config_path)
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
        config = Config(config_path=self.config_path)
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
        config = Config(config_path=self.config_path)
        # clear config -> user_mode become True !
        config.config = {}
        auto_save = config.isAutoSave()
        self.assertEqual(auto_save, False)

        # Checking that the values for the "Projects preferences" are well set
        self.assertEqual(config.get_max_projects(), 5)
        config.set_max_projects(7)
        self.assertEqual(config.get_max_projects(), 7)
        config.set_max_projects(5)

        mia_path = os.path.join(config.get_mia_path(),
                                "properties", "config.yml")
        self.assertEqual(os.path.exists(mia_path), True)

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

        self.assertEqual(False,
                         version.parse(yaml.__version__) > version.parse(
                                                                         "9.1"))
        self.assertEqual(True,
                         version.parse(yaml.__version__) < version.parse(
                                                                         "9.1"))

        self.assertEqual(config.get_projects_save_path(), '')

    def test_modify_table(self):
        """
        Test the modify table module
        """

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
                                                             COLLECTION_CURRENT,
                                                             scans_displayed[0],
                                                             "FOV")

        mod = ModifyTable(self.main_window.project, value, [type("string")],
                          scans_displayed, tag_name)
        mod.update_table_values(True)
        new_value = self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scans_displayed[0],
                                                             "FOV")
        self.assertEqual(old_value, new_value)

        # Test that the value will change when all parameters are correct
        tag_object = self.main_window.project.session.get_field(
                                                             COLLECTION_CURRENT,
                                                             "FOV")
        mod = ModifyTable(self.main_window.project, value,
                          [tag_object.field_type], scans_displayed, tag_name)
        mod.update_table_values(True)
        new_value = self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scans_displayed[0],
                                                             "FOV")
        self.assertEqual(mod.table.columnCount(), 2)
        self.assertEqual(value, new_value)

    def test_multiple_sort(self):
        """
        Tests the multiple sort popup
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.multiple_sort_pop_up()
        self.main_window.data_browser.table_data.itemChanged.connect(
                     self.main_window.data_browser.table_data.change_cell_color)
        multiple_sort = self.main_window.data_browser.table_data.pop_up

        multiple_sort.push_buttons[0].setText("BandWidth")
        multiple_sort.fill_values(0)
        multiple_sort.push_buttons[1].setText("Exp Type")
        multiple_sort.fill_values(1)
        QTest.mouseClick(multiple_sort.push_button_sort, Qt.LeftButton)

        scan = self.main_window.data_browser.table_data.item(0, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014"
                         "-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm-000940"
                         "_800.nii")
        scan = self.main_window.data_browser.table_data.item(1, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27-2014"
                         "-02-14102317-04-G3_Guerbet_MDEFT-MDEFTpvm-000940"
                         "_800.nii")
        scan = self.main_window.data_browser.table_data.item(2, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
                         "-000220_000.nii")
        scan = self.main_window.data_browser.table_data.item(3, 0).text()
        self.assertEqual(scan,
                         "data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
                         "-000220_000.nii")
        scan = self.main_window.data_browser.table_data.item(4, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
                         "-000142_400.nii")
        scan = self.main_window.data_browser.table_data.item(5, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RAREpvm"
                         "-000142_400.nii")
        scan = self.main_window.data_browser.table_data.item(6, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RAREpvm"
                         "-000142_400.nii")
        scan = self.main_window.data_browser.table_data.item(7, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RAREpvm"
                         "-000142_400.nii")
        scan = self.main_window.data_browser.table_data.item(8, 0).text()
        self.assertEqual(scan,
                         "data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                         "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RAREpvm"
                         "-000142_400.nii")

    def test_open_project(self):
        """
        Tests project opening
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        self.assertEqual(self.main_window.project.getName(), "project_8")
        self.assertEqual(self.main_window.windowTitle(),
                         "MIA - Multiparametric Image Analysis"
                         " (Admin mode) - project_8")

        documents = self.main_window.project.session.get_documents_names(
                                                             COLLECTION_CURRENT)

        self.assertEqual(len(documents), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in documents)
        documents = self.main_window.project.session.get_documents_names(
                                                             COLLECTION_INITIAL)
        self.assertEqual(len(documents), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in documents)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in documents)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in documents)

    def test_open_project_filter(self):
        """
        Tests project filter opening
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        self.main_window.data_browser.open_filter_action.trigger()
        open_popup = self.main_window.data_browser.popUp
        open_popup.list_widget_filters.item(0).setSelected(True)
        QTest.mouseClick(open_popup.push_button_ok, Qt.LeftButton)

        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 2)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)

    def test_project_properties(self):
        """
        Tests saved projects addition and removal
        """

        saved_projects = self.main_window.saved_projects
        self.assertEqual(saved_projects.pathsList, [])

        config = Config(config_path=self.config_path)
        project_8_path = self.get_new_test_project()

        os.remove(os.path.join(config.get_config_path(), 'saved_projects.yml'))

        saved_projects = SavedProjects()
        self.assertEqual(saved_projects.pathsList, [])

        saved_projects.addSavedProject(project_8_path)
        self.assertEqual(saved_projects.pathsList, [project_8_path])

        saved_projects.addSavedProject('/home')
        self.assertEqual(saved_projects.pathsList, ['/home', project_8_path])

        saved_projects.addSavedProject(project_8_path)
        self.assertEqual(saved_projects.pathsList, [project_8_path, "/home"])

        saved_projects.removeSavedProject(project_8_path)
        saved_projects.removeSavedProject("/home")
        self.assertEqual(saved_projects.pathsList, [])

        SavedProjects.loadSavedProjects = lambda a: True
        saved_projects = SavedProjects()
        self.assertEqual(saved_projects.pathsList, [])

    def test_proj_remov_from_cur_proj(self):
        """
        Tests that the projects are removed from the list of current projects
        """

        config = Config(config_path=self.config_path)
        projects = config.get_opened_projects()
        self.assertEqual(len(projects), 1)
        self.assertTrue(self.main_window.project.folder in projects)

    def test_rapid_search(self):
        """
        Tests the rapid search bar
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Checking that the 9 scans are shown in the DataBrowser
        self.assertEqual(self.main_window.data_browser.table_data.rowCount(),
                         9)
        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)

        # Testing G1 rapid search
        self.main_window.data_browser.search_bar.setText("G1")
        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 2)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans_displayed)

        # Testing that all the scans are back when clicking on the cross
        QTest.mouseClick(self.main_window.data_browser.button_cross,
                         Qt.LeftButton)
        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
                        "-000220_000.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm"
                        "-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
                        "-000220_000.nii" in scans_displayed)

        # Testing not defined values
        QTest.mouseClick(self.main_window.data_browser.button_cross,
                         Qt.LeftButton)
        self.main_window.data_browser.search_bar.setText("*Not Defined*")
        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(scans_displayed,
                         ["data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                          "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                          "pvm-000142_400.nii"])

    def test_remove_scan(self):
        """
        Tests scans removal in the DataBrowser
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
                        "-000220_000.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFTpvm"
                        "-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm"
                        "-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
                        "-000220_000.nii" in scans_displayed)

        # Trying to remove a scan
        self.main_window.data_browser.table_data.selectRow(0)
        self.main_window.data_browser.table_data.remove_scan()
        scans_displayed = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            item = self.main_window.data_browser.table_data.item(row, 0)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                scans_displayed.append(scan_name)

        self.assertEqual(len(scans_displayed), 8)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFTpvm"
                        "-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFTpvm"
                        "-000940_800.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RAREpvm"
                        "-000142_400.nii" in scans_displayed)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm"
                        "-000220_000.nii" in scans_displayed)

    def test_remove_tag(self):
        """
        Tests the popup removing user tags
        """

        # Adding a tag
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        add_tag.text_edit_tag_name.setText("Test")
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)

        old_tags_current = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_CURRENT)
        old_tags_initial = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_INITIAL)
        self.main_window.data_browser.remove_tag_action.trigger()
        remove_tag = self.main_window.data_browser.pop_up_remove_tag
        QTest.mouseClick(remove_tag.push_button_ok, Qt.LeftButton)
        new_tags_current = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_CURRENT)
        new_tags_initial = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_INITIAL)
        self.assertTrue(old_tags_current == new_tags_current)
        self.assertTrue(old_tags_initial == new_tags_initial)

        old_tags_current = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_CURRENT)
        old_tags_initial = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_INITIAL)
        self.assertTrue("Test" in old_tags_current)
        self.assertTrue("Test" in old_tags_initial)
        self.main_window.data_browser.remove_tag_action.trigger()
        remove_tag = self.main_window.data_browser.pop_up_remove_tag
        remove_tag.list_widget_tags.setCurrentRow(0)  # Test tag selected
        QTest.mouseClick(remove_tag.push_button_ok, Qt.LeftButton)
        new_tags_current = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_CURRENT)
        new_tags_initial = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_INITIAL)
        self.assertTrue("Test" not in new_tags_current)
        self.assertTrue("Test" not in new_tags_initial)

    def test_reset_cell(self):
        """
        Tests the method resetting the selected cells
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # scan name
        item = self.main_window.data_browser.table_data.item(0, 0)
        scan_name = item.text()

        ### Test for a list:
        # values in the db
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "BandWidth")[0])

        # value in the DataBrowser
        bandwidth_column = (self.main_window.data_browser.table_data.
                                                    get_tag_column)("BandWidth")
        item = self.main_window.data_browser.table_data.item(0,
                                                             bandwidth_column)
        databrowser = float(item.text()[1:-1])

        # we test equality between DataBrowser and db
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # we change the value
        item.setSelected(True)
        threading.Timer(2,
                        partial(self.edit_databrowser_list, '25000')).start()
        self.main_window.data_browser.table_data.edit_table_data_values()

        # we test again the equality between DataBrowser and db
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "BandWidth")[0])
        item = self.main_window.data_browser.table_data.item(0,
                                                             bandwidth_column)
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, float(50000))

        # we reset the current value to the initial value
        item = self.main_window.data_browser.table_data.item(0,
                                                             bandwidth_column)
        item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_cell()
        self.main_window.data_browser.table_data.itemChanged.connect(
                     self.main_window.data_browser.table_data.change_cell_color)
        item.setSelected(False)

        # we test whether the data has been reset
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "BandWidth")[0])
        item = self.main_window.data_browser.table_data.item(0,
                                                             bandwidth_column)
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        ### Test for a string:
        # values in the db
        value = self.main_window.project.session.get_value(COLLECTION_CURRENT,
                                                           scan_name,
                                                           "Type")
        value_initial = self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "Type")

        # value in the DataBrowser
        type_column = (self.main_window.data_browser.table_data.
                                                         get_tag_column)("Type")
        item = self.main_window.data_browser.table_data.item(0, type_column)
        databrowser = item.text()

        # we test equality between DataBrowser and db
        self.assertEqual(value, "Scan")
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # we change the value
        item.setSelected(True)
        item.setText("Test")
        item.setSelected(False)

        # we test again the equality between DataBrowser and db
        value = self.main_window.project.session.get_value(COLLECTION_CURRENT,
                                                           scan_name,
                                                           "Type")
        value_initial = self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "Type")
        item = self.main_window.data_browser.table_data.item(0, type_column)

        databrowser = item.text()

        self.assertEqual(value, "Test")
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, "Scan")

        # we reset the current value to the initial value
        item = self.main_window.data_browser.table_data.item(0, type_column)
        item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_cell()
        self.main_window.data_browser.table_data.itemChanged.connect(
            self.main_window.data_browser.table_data.change_cell_color)
        item.setSelected(False)

        # we test whether the data has been reset
        value = self.main_window.project.session.get_value(COLLECTION_CURRENT,
                                                           scan_name,
                                                           "Type")
        value_initial = self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "Type")
        item = self.main_window.data_browser.table_data.item(0, type_column)
        databrowser = item.text()
        self.assertEqual(value, "Scan")
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

    def test_reset_column(self):
        """
        Tests the method resetting the columns selected
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # second document; scan name
        item = self.main_window.data_browser.table_data.item(1, 0)
        scan_name2 = item.text()

        # second document; values in the db
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name2,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name2,
                                                             "BandWidth")[0])

        # second document; value in the DataBrowser
        bandwidth_column = (self.main_window.data_browser.table_data.
                                                    get_tag_column)("BandWidth")
        item2 = self.main_window.data_browser.table_data.item(1,
                                                              bandwidth_column)
        databrowser = float(item2.text()[1:-1])

        # we test equality between DataBrowser and db for second document
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)
        item2.setSelected(True)

        # third document; scan name
        item = self.main_window.data_browser.table_data.item(2, 0)
        scan_name3 = item.text()

        # third document; values in the db
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name3,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name3,
                                                             "BandWidth")[0])

        # third document; value in the DataBrowser
        item3 = self.main_window.data_browser.table_data.item(2,
                                                              bandwidth_column)

        # we test equality between DataBrowser and db for third document
        databrowser = float(item3.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)
        item3.setSelected(True)

        # we change the value to [70000] for the third and second documents
        threading.Timer(2,
                        partial(self.edit_databrowser_list, '70000')).start()
        self.main_window.data_browser.table_data.edit_table_data_values()

        # second document; values in the db
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name2,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name2,
                                                             "BandWidth")[0])
        # second document; value in the DataBrowser
        item2 = self.main_window.data_browser.table_data.item(1,
                                                              bandwidth_column)
        databrowser = float(item2.text()[1:-1])

        # we test equality between DataBrowser and db for second document
        self.assertEqual(value, float(70000))
        self.assertEqual(value, databrowser)
        self.assertEqual(float(50000), value_initial)
        item2.setSelected(True)

        # third document; values in the db
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name3,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name3,
                                                             "BandWidth")[0])

        # third document; value in the DataBrowser
        item3 = self.main_window.data_browser.table_data.item(2,
                                                              bandwidth_column)
        databrowser = float(item3.text()[1:-1])

        # we test value in database for the third document
        self.assertEqual(value, float(70000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, float(25000))
        item3.setSelected(True)

        # we reset the current value to the initial value
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_column()
        self.main_window.data_browser.table_data.itemChanged.connect(
                     self.main_window.data_browser.table_data.change_cell_color)

        # we test the value in the db and DataBrowser for the second document
        # has been reset
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name2,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name2,
                                                             "BandWidth")[0])
        item2 = self.main_window.data_browser.table_data.item(1,
                                                              bandwidth_column)
        databrowser = float(item2.text()[1:-1])
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # we test the value in the db and DataBrowser for the third document
        # has been reset
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name3,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name3,
                                                             "BandWidth")[0])
        item3 = self.main_window.data_browser.table_data.item(2,
                                                              bandwidth_column)
        databrowser = float(item3.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

    def test_reset_row(self):
        """
        Tests row reset
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # value in DataBrowser for the second document
        type_column = (self.main_window.data_browser.table_data.
                                                         get_tag_column)("Type")
        type_item = self.main_window.data_browser.table_data.item(1,
                                                                  type_column)
        old_type = type_item.text()

        # we test value in DataBrowser for the second document
        self.assertEqual(old_type, "Scan")

        # we change the value
        type_item.setSelected(True)
        type_item.setText("Test")

        # we test if value in DataBrowser as been changed
        set_item = self.main_window.data_browser.table_data.item(1,
                                                                 type_column)
        set_type = set_item.text()
        self.assertEqual(set_type, "Test")

        # we reset row for second document
        self.main_window.data_browser.table_data.clearSelection()
        item = self.main_window.data_browser.table_data.item(1, 0)
        item.setSelected(True)
        self.main_window.data_browser.table_data.itemChanged.disconnect()
        self.main_window.data_browser.table_data.reset_row()
        self.main_window.data_browser.table_data.itemChanged.connect(
                     self.main_window.data_browser.table_data.change_cell_color)

        # we test if value in DataBrowser as been reset
        type_item = self.main_window.data_browser.table_data.item(1,
                                                                  type_column)
        new_type = type_item.text()
        self.assertEqual(new_type, "Scan")

    def test_save_project(self):
        """
        Test opening & saving of a project
        """
        config = Config(config_path=self.config_path)
        projects_dir = os.path.realpath(tempfile.mkdtemp(
                                                       prefix='projects_tests'))
        config.set_projects_save_path(projects_dir)
        something_path = os.path.join(projects_dir, 'something')
        project_8_path = self.get_new_test_project()

        self.main_window.saveChoice()  # Saves the project 'something'
        self.assertEqual(self.main_window.project.getName(), "something")
        self.assertEqual(os.path.exists(something_path), True)

        self.main_window.switch_project(project_8_path, "project_8")
        self.assertEqual(self.main_window.project.getName(), "project_8")
        self.main_window.saveChoice()  # Updates the project 'project_8'

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
                                                                 something_path)
        # Saves the project 'something'
        self.main_window.create_project_pop_up()
        self.assertEqual(self.main_window.project.getName(), "something")
        self.assertEqual(os.path.exists(something_path), True)

        self.main_window.switch_project(project_8_path, "project_8")
        self.main_window.open_project_pop_up()
        self.assertEqual(self.main_window.project.getName(), "something")

        self.main_window.switch_project(project_8_path, "project_8")
        shutil.rmtree(something_path)

    def test_send_doc_to_pip(self):
        """
        Tests the popup sending the documents to the pipeline manager
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Checking that the pipeline manager has an empty list at the beginning
        self.assertEqual(self.main_window.pipeline_manager.scan_list, [])

        # Sending the selection (all scans), but closing the popup
        QTest.mouseClick(
                self.main_window.data_browser.send_documents_to_pipeline_button,
                Qt.LeftButton)
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(100)

        send_popup.close()

        # Checking that the list is stil empty
        self.assertEqual(self.main_window.pipeline_manager.scan_list, [])

        # Sending the selection (all scans)
        QTest.mouseClick(
                self.main_window.data_browser.send_documents_to_pipeline_button,
                Qt.LeftButton)
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(100)

        send_popup.ok_clicked()

        # Checking that all scans have been sent to the pipeline manager
        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 9)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-05-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-06-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-08-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-09-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-11-G4_Guerbet_T1SE_800-RARE"
                        "pvm-000142_400.nii" in scans)
        self.assertTrue("data/derived_data/sGuerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                        "pvm-000220_000.nii" in scans)

        # Selecting the first 2 scans
        item1 = self.main_window.data_browser.table_data.item(0, 0)
        item1.setSelected(True)
        scan1 = item1.text()
        item2 = self.main_window.data_browser.table_data.item(1, 0)
        scan2 = item2.text()
        item2.setSelected(True)

        # Sending the selection (first 2 scans)
        QTest.mouseClick(
                self.main_window.data_browser.send_documents_to_pipeline_button,
                Qt.LeftButton)
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(100)

        send_popup.ok_clicked()

        # Checking that the first 2 scans have been sent to the pipeline manager
        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 2)
        self.assertTrue(scan1 in scans)
        self.assertTrue(scan2 in scans)

        # Testing with the rapid search
        self.main_window.data_browser.table_data.clearSelection()
        self.main_window.data_browser.search_bar.setText("G3")

        # Sending the selection (G3 scans)
        QTest.mouseClick(
                self.main_window.data_browser.send_documents_to_pipeline_button,
                Qt.LeftButton)
        send_popup = self.main_window.data_browser.show_selection

        QTest.qWait(100)

        send_popup.ok_clicked()

        # Checking that G3 scans have been sent to the pipeline manager
        scans = self.main_window.pipeline_manager.scan_list
        self.assertEqual(len(scans), 2)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-04-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans)
        self.assertTrue("data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                        "-2014-02-14102317-10-G3_Guerbet_MDEFT-MDEFT"
                        "pvm-000940_800.nii" in scans)

    def test_set_value(self):
        """
        Tests the values modifications

        This test is redundant with the first part of test_reset_cell.
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # scan name for the second document
        item = self.main_window.data_browser.table_data.item(1, 0)
        scan_name = item.text()

        ### Test for a list:
        # values in the db
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "BandWidth")[0])

        # value in the DataBrowser
        bandwidth_column = (self.main_window.data_browser.table_data.
                                                    get_tag_column)("BandWidth")
        item = self.main_window.data_browser.table_data.item(1,
                                                             bandwidth_column)
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(50000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # we change the value
        item.setSelected(True)
        threading.Timer(2,
                        partial(self.edit_databrowser_list, '25000')).start()
        self.main_window.data_browser.table_data.edit_table_data_values()

        # we test if value was changed in db and DataBrowser
        value = float(self.main_window.project.session.get_value(
                                                             COLLECTION_CURRENT,
                                                             scan_name,
                                                             "BandWidth")[0])
        value_initial = float(self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "BandWidth")[0])
        item = self.main_window.data_browser.table_data.item(1,
                                                             bandwidth_column)
        databrowser = float(item.text()[1:-1])
        self.assertEqual(value, float(25000))
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, float(50000))
        item.setSelected(False)

        ### Test for a string:
        # values in the db
        value = self.main_window.project.session.get_value(COLLECTION_CURRENT,
                                                           scan_name,
                                                           "Type")
        value_initial = self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "Type")

        # value in the DataBrowser
        type_column = (self.main_window.data_browser.table_data.
                                                         get_tag_column)("Type")
        item = self.main_window.data_browser.table_data.item(1, type_column)
        databrowser = item.text()

        # we test equality between DataBrowser and db
        self.assertEqual(value, "Scan")
        self.assertEqual(value, databrowser)
        self.assertEqual(value, value_initial)

        # we change the value
        item.setSelected(True)
        item.setText("Test")
        item.setSelected(False)

        # we test if value in DataBrowser and db as been changed
        value = self.main_window.project.session.get_value(COLLECTION_CURRENT,
                                                           scan_name,
                                                           "Type")
        value_initial = self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "Type")
        item = self.main_window.data_browser.table_data.item(1, type_column)
        databrowser = item.text()
        self.assertEqual(value, "Test")
        self.assertEqual(value, databrowser)
        self.assertEqual(value_initial, "Scan")

    def test_sort(self):
        """
        Tests the sorting in the databrowser
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        mixed_bandwidths = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            bandwidth_column = (self.main_window.data_browser.table_data.
                                                    get_tag_column)("BandWidth")
            item = self.main_window.data_browser.table_data.item(
                                                               row,
                                                               bandwidth_column)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                mixed_bandwidths.append(scan_name)

        (self.main_window.data_browser.table_data.
                          horizontalHeader)().setSortIndicator(bandwidth_column,
                                                               0)
        up_bandwidths = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            bandwidth_column = (self.main_window.data_browser.table_data.
                                                    get_tag_column)("BandWidth")
            item = self.main_window.data_browser.table_data.item(
                                                               row,
                                                               bandwidth_column)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                up_bandwidths.append(scan_name)

        self.assertNotEqual(mixed_bandwidths, up_bandwidths)
        self.assertEqual(sorted(mixed_bandwidths), up_bandwidths)

        (self.main_window.data_browser.table_data.
                          horizontalHeader)().setSortIndicator(bandwidth_column,
                                                               1)
        down_bandwidths = []

        for row in range(0,
                         self.main_window.data_browser.table_data.rowCount()):
            bandwidth_column = (self.main_window.data_browser.table_data.
                                                    get_tag_column)("BandWidth")
            item = self.main_window.data_browser.table_data.item(
                                                               row,
                                                               bandwidth_column)
            scan_name = item.text()

            if not self.main_window.data_browser.table_data.isRowHidden(row):
                down_bandwidths.append(scan_name)

        self.assertNotEqual(mixed_bandwidths, down_bandwidths)
        self.assertEqual(sorted(mixed_bandwidths, reverse=True),
                         down_bandwidths)

    def test_tab_change(self):
        """
        Tests the tab change from data browser to pipeline manager
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        self.main_window.tabs.setCurrentIndex(2)
        index = self.main_window.tabs.currentIndex()
        scans = self.main_window.project.session.get_documents_names(
                                                             COLLECTION_CURRENT)
        self.assertEqual(scans, self.main_window.pipeline_manager.scan_list)
        self.assertEqual("Pipeline Manager",
                         self.main_window.tabs.tabText(index))

        self.main_window.tabs.setCurrentIndex(0)
        index = self.main_window.tabs.currentIndex()
        self.assertEqual(self.main_window.tabs.tabText(index), "Data Browser")

    def test_undo_redo_databrowser(self):
        """
        Tests the databrowser undo/redo
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # 1. Tag value (list)
        # we test undos and redos are empty
        self.assertEqual(self.main_window.project.undos, [])
        self.assertEqual(self.main_window.project.redos, [])

        # DataBrowser value for second document
        bw_column = (self.main_window.data_browser.table_data.
                                                    get_tag_column)("BandWidth")
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_old = bw_item.text()

        # we test the value is really 50000
        self.assertEqual(float(bw_old[1:-1]), 50000)

        # we change the value
        bw_item.setSelected(True)
        threading.Timer(2, partial(self.edit_databrowser_list, '0.0')).start()
        self.main_window.data_browser.table_data.edit_table_data_values()

        # we test undos and redos have the right values.
        self.assertEqual(self.main_window.project.undos,
                         [["modified_values",
                           [["data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                             "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                             "pvm-000220_000.nii",
                             "BandWidth",
                             [50000.0],
                             [0.0]
                             ]]
                           ]])
        self.assertEqual(self.main_window.project.redos, [])

        # we test the value has really been changed to 0.0.
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_set = bw_item.text()
        self.assertEqual(float(bw_set[1:-1]), 0)

        # we undo
        self.main_window.action_undo.trigger()

        # we test the value has really been reset to 50000
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_undo = bw_item.text()
        self.assertEqual(float(bw_undo[1:-1]), 50000)

        # we test undos / redos have the right values
        self.assertEqual(self.main_window.project.redos,
                         [["modified_values",
                           [["data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                             "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                             "pvm-000220_000.nii",
                             "BandWidth",
                             [50000.0],
                             [0.0]
                             ]]
                           ]])
        self.assertEqual(self.main_window.project.undos, [])

        # we redo
        self.main_window.action_redo.trigger()

        # we test the value has really been reset to 0.0
        bw_item = self.main_window.data_browser.table_data.item(1, bw_column)
        bw_redo = bw_item.text()
        self.assertEqual(float(bw_redo[1:-1]), 0)

        # we test undos / redos have the right values
        self.assertEqual(self.main_window.project.undos,
                         [["modified_values",
                           [["data/raw_data/Guerbet-C6-2014-Rat-K52-Tube27"
                             "-2014-02-14102317-01-G1_Guerbet_Anat-RARE"
                             "pvm-000220_000.nii",
                             "BandWidth",
                             [50000.0],
                             [0.0]
                             ]]
                           ]])
        self.assertEqual(self.main_window.project.redos, [])

        # 2. Remove a can (document)
        # we test there are 9 documents in db (current and initial)
        self.assertEqual(
                       9,
                       len(self.main_window.project.session.get_documents_names(
                                                           COLLECTION_CURRENT)))
        self.assertEqual(
                       9,
                       len(self.main_window.project.session.get_documents_names(
                                                           COLLECTION_INITIAL)))

        # we remove the eighth document
        self.main_window.data_browser.table_data.selectRow(8)
        self.main_window.data_browser.table_data.remove_scan()

        # we test if there are now 8 documents in db (current and initial)
        self.assertEqual(
                       8,
                       len(self.main_window.project.session.get_documents_names(
                                                           COLLECTION_CURRENT)))
        self.assertEqual(
                       8,
                       len(self.main_window.project.session.get_documents_names(
                                                           COLLECTION_INITIAL)))

        # we undo
        self.main_window.action_undo.trigger()

        # we test there are still only 8 documents in the database
        # (current and initial). In fact the document has been permanently
        # deleted and we cannot recover it in this case
        self.assertEqual(
                       8,
                       len(self.main_window.project.session.get_documents_names(
                                                           COLLECTION_CURRENT)))
        self.assertEqual(
                       8,
                       len(self.main_window.project.session.get_documents_names(
                                                           COLLECTION_INITIAL)))

        # 3. Add a tag
        # we test we don't have 'Test' tag in the db
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # we add the Test tag
        self.main_window.data_browser.add_tag_action.trigger()
        add_tag = self.main_window.data_browser.pop_up_add_tag
        add_tag.text_edit_tag_name.setText("Test")
        QTest.mouseClick(add_tag.push_button_ok, Qt.LeftButton)

        # we test we have the 'Test' tag in the db
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # we undo
        self.main_window.action_undo.trigger()

        # we test we don't have 'Test' tag in the db
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # we redo
        self.main_window.action_redo.trigger()

        # we test we have the 'Test' tag in the db
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # 4. remove tag
        # we remove the 'Test' tag
        self.main_window.data_browser.remove_tag_action.trigger()
        remove_tag = self.main_window.data_browser.pop_up_remove_tag
        remove_tag.list_widget_tags.setCurrentRow(0)  # 'Test' tag selected
        QTest.mouseClick(remove_tag.push_button_ok, Qt.LeftButton)

        # we test we don't have 'Test' tag in the db
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # we undo
        self.main_window.action_undo.trigger()

        # we test we have the 'Test' tag in the db
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # we redo
        self.main_window.action_redo.trigger()

        # we test we don't have 'Test' tag in the db
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # 4. clone tag
        self.main_window.data_browser.clone_tag_action.trigger()
        clone_tag = self.main_window.data_browser.pop_up_clone_tag

        for fov_column in range(clone_tag.list_widget_tags.count()):

            if clone_tag.list_widget_tags.item(fov_column).text() == 'FOV':
                break

        # 'FOV' tag selected
        clone_tag.list_widget_tags.setCurrentRow(fov_column)
        clone_tag.line_edit_new_tag_name.setText('Test')
        QTest.mouseClick(clone_tag.push_button_ok, Qt.LeftButton)

        # we test we have the 'Test' tag in the db
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertTrue("Test" in
                        self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))

        # value in the db
        item = self.main_window.data_browser.table_data.item(1, 0)
        scan_name = item.text()
        value = self.main_window.project.session.get_value(COLLECTION_CURRENT,
                                                           scan_name,
                                                           "Test")
        value_initial = self.main_window.project.session.get_value(
                                                             COLLECTION_INITIAL,
                                                             scan_name,
                                                             "Test")

        # value in the DataBrowser
        test_column = (self.main_window.data_browser.table_data.
                                                         get_tag_column)("Test")
        item = self.main_window.data_browser.table_data.item(1, test_column)
        databrowser = item.text()

        # we test equality between DataBrowser and db
        self.assertEqual(value, [3.0, 3.0])
        self.assertEqual(value, ast.literal_eval(databrowser))
        self.assertEqual(value, value_initial)

        # we undo
        self.main_window.action_undo.trigger()

        # we test we don't have the 'Test' tag in the db and in the DataBrowser
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_CURRENT))
        self.assertFalse("Test" in
                         self.main_window.project.session.get_fields_names(
                                                            COLLECTION_INITIAL))
        self.assertIsNone((self.main_window.data_browser.table_data.
                                                        get_tag_column)("Test"))

    def test_unnamed_proj_soft_open(self):
        """
        Tests unnamed project creation at software opening
        """

        self.assertIsInstance(self.project, Project)
        self.assertEqual(self.main_window.project.getName(),
                         "Unnamed project")
        tags = self.main_window.project.session.get_fields_names(
                                                             COLLECTION_CURRENT)
        self.assertEqual(len(tags), 6)
        self.assertTrue(TAG_CHECKSUM in tags)
        self.assertTrue(TAG_FILENAME in tags)
        self.assertTrue(TAG_TYPE in tags)
        self.assertTrue(TAG_EXP_TYPE in tags)
        self.assertTrue(TAG_BRICKS in tags)
        self.assertTrue(TAG_HISTORY in tags)
        self.assertEqual(self.main_window.project.session.get_documents_names(
                                                            COLLECTION_CURRENT),
                         [])
        self.assertEqual(self.main_window.project.session.get_documents_names(
                                                            COLLECTION_INITIAL),
                         [])
        collections = self.main_window.project.session.get_collections_names()
        self.assertEqual(len(collections), 5)
        self.assertTrue(COLLECTION_INITIAL in collections)
        self.assertTrue(COLLECTION_CURRENT in collections)
        self.assertTrue(COLLECTION_BRICK in collections)
        self.assertTrue(COLLECTION_HISTORY in collections)
        self.assertEqual(self.main_window.windowTitle(),
                         "MIA - Multiparametric Image Analysis "
                         "(Admin mode) - Unnamed project")

    def test_utils(self):
        """
        Test the utils functions
        """

        self.assertEqual(table_to_database(True, FIELD_TYPE_BOOLEAN), True)
        self.assertEqual(table_to_database("False", FIELD_TYPE_BOOLEAN), False)

        format = "%d/%m/%Y"
        value = datetime.strptime("01/01/2019", format).date()
        self.assertEqual(check_value_type("01/01/2019", FIELD_TYPE_DATE), True)
        self.assertEqual(table_to_database("01/01/2019", FIELD_TYPE_DATE),
                         value)

        format = "%d/%m/%Y %H:%M:%S.%f"
        value = datetime.strptime("15/7/2019 16:16:55.789643", format)
        self.assertEqual(check_value_type("15/7/2019 16:16:55.789643",
                                          FIELD_TYPE_DATETIME),
                         True)
        self.assertEqual(table_to_database("15/7/2019 16:16:55.789643",
                                           FIELD_TYPE_DATETIME),
                         value)

        format = "%H:%M:%S.%f"
        value = datetime.strptime("16:16:55.789643", format).time()
        self.assertEqual(check_value_type("16:16:55.789643", FIELD_TYPE_TIME),
                         True)
        self.assertEqual(table_to_database("16:16:55.789643", FIELD_TYPE_TIME),
                         value)

    def test_visualized_tags(self):
        """
        Tests the popup modifying the visualized tags
        """

        # Testing default tags visibility
        visibles = self.main_window.project.session.get_shown_tags()
        self.assertEqual(len(visibles), 4)
        self.assertTrue(TAG_FILENAME in visibles)
        self.assertTrue(TAG_BRICKS in visibles)
        self.assertTrue(TAG_TYPE in visibles)
        self.assertTrue(TAG_EXP_TYPE in visibles)

        # Testing columns displayed in the databrowser
        self.assertEqual(4,
                         self.main_window.data_browser.table_data.columnCount())
        columns_displayed = []

        for column in range(
                        0,
                        self.main_window.data_browser.table_data.columnCount()):
            tag_displayed = (self.main_window.data_browser.table_data.
                                            horizontalHeaderItem)(column).text()

            if not self.main_window.data_browser.table_data.isColumnHidden(
                                                                        column):
                columns_displayed.append(tag_displayed)

        self.assertEqual(sorted(visibles), sorted(columns_displayed))

        # Testing that FileName tag is the first column
        self.assertEqual(
                  TAG_FILENAME,
                  self.main_window.data_browser.table_data.horizontalHeaderItem(
                                                                      0).text())

        # Trying to set the visibles tags
        QTest.mouseClick(self.main_window.data_browser.visualized_tags_button,
                         Qt.LeftButton)
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

        for row in range(0,
                         settings.tab_tags.list_widget_selected_tags.count()):
            item = settings.tab_tags.list_widget_selected_tags.item(row).text()
            visible_tags.append(item)

        self.assertEqual(len(visible_tags), 3)
        self.assertTrue(TAG_BRICKS in visible_tags)
        self.assertTrue(TAG_EXP_TYPE in visible_tags)
        self.assertTrue(TAG_TYPE in visible_tags)

        ### Testing when hiding a tag
        # Bricks tag selected
        settings.tab_tags.list_widget_selected_tags.item(2).setSelected(True)
        QTest.mouseClick(settings.tab_tags.push_button_unselect_tag,
                         Qt.LeftButton)
        visible_tags = []

        for row in range(0,
                         settings.tab_tags.list_widget_selected_tags.count()):
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
                        0,
                        self.main_window.data_browser.table_data.columnCount()):
            item = (self.main_window.data_browser.table_data.
                                                   horizontalHeaderItem)(column)

            if not self.main_window.data_browser.table_data.isColumnHidden(
                                                                        column):
                columns_displayed.append(item.text())

        self.assertEqual(len(columns_displayed), 3)
        self.assertTrue(TAG_FILENAME in columns_displayed)
        self.assertTrue(TAG_EXP_TYPE in columns_displayed)
        self.assertTrue(TAG_TYPE in columns_displayed)

        # Testing when showing a new tag
        QTest.mouseClick(self.main_window.data_browser.visualized_tags_button,
                         Qt.LeftButton)
        settings = self.main_window.data_browser.table_data.pop_up
        settings.tab_tags.search_bar.setText(TAG_BRICKS)
        settings.tab_tags.list_widget_tags.item(0).setSelected(True)
        QTest.mouseClick(settings.tab_tags.push_button_select_tag,
                         Qt.LeftButton)
        QTest.mouseClick(settings.push_button_ok, Qt.LeftButton)

        new_visibles = self.main_window.project.session.get_shown_tags()
        self.assertEqual(len(new_visibles), 4)
        self.assertTrue(TAG_FILENAME in new_visibles)
        self.assertTrue(TAG_EXP_TYPE in new_visibles)
        self.assertTrue(TAG_TYPE in new_visibles)
        self.assertTrue(TAG_BRICKS in new_visibles)

        columns_displayed = []

        for column in range(
                        0,
                        self.main_window.data_browser.table_data.columnCount()):
            item = (self.main_window.data_browser.table_data.
                                                   horizontalHeaderItem)(column)

            if not self.main_window.data_browser.table_data.isColumnHidden(
                                                                        column):
                columns_displayed.append(item.text())

        self.assertEqual(len(columns_displayed), 4)
        self.assertTrue(TAG_FILENAME in columns_displayed)
        self.assertTrue(TAG_EXP_TYPE in columns_displayed)
        self.assertTrue(TAG_TYPE in columns_displayed)
        self.assertTrue(TAG_BRICKS in columns_displayed)

class TestMIAPipelineManager(unittest.TestCase):
    """Tests for the pipeline manager tab.

    :Contains:
        :Method:
            - add_visualized_tag: selects a tag to display with the
              "Visualized tags" pop-up
            - execute_QDialogAccept: accept (close) a QDialog window
            - get_new_test_project: create a temporary project that can
              be safely modified
            - restart_MIA: restarts MIA within a unit test.
            - setUp: called automatically before each test method
            - setUpClass: called before tests in the individual class
            - tearDown: cleans up after each test method
            - tearDownClass: called after tests in the individual class
            - test_add_tab: adds tabs to the PipelineEditorTabs
            - test_attributes_filter: displays an attributes filter and 
              modifies it
            - test_capsul_node_controller: adds, changes and deletes 
              processes using the capsul node controller
            - test_close_tab: closes a tab in the PipelineEditorTabs
            - test_display_filter: displays node parameters and a plug 
              filter
            - test_drop_process: adds a Nipype SPM Smooth process to the
              pipeline editor
            - test_filter_widget: opens up the "FilterWidget()" to 
              modify its parameters
            - test_iteration_table: plays with the iteration table
            - test_node_controller: adds, changes and deletes processes 
              to the node controller
            - test_plug_filter: displays a plug filter and modifies it
            - test_process_library: install the brick_test and then 
              remove it
            - test_update_node_name: displays node parameters and 
              updates its name
            - test_update_plug_value: displays node parameters and 
              updates a plug value
            - test_z_get_editor: gets the instance of an editor
            - test_z_get_filename: gets the relative path to a 
              previously saved pipeline file
            - test_z_get_index: gets the index of an editor
            - test_z_get_tab_name: gets the tab name of the editor
            - test_z_load_pipeline: loads a pipeline
            - test_z_open_sub_pipeline: opens a sub_pipeline
            - test_z_set_current_editor: sets the current editor
            - test_zz_check_modif: opens a pipeline, opens it as a 
              process in another tab, modifies it and check the 
              modifications
            - test_zz_del_pack(self): deletion of the brick created during UTs
    """

    def add_visualized_tag(self, tag):
        """
        With the "Visualized tags" pop-up open, selects a tag to display.

        Parameters
        ----------
        tag: string
          The tag to be displayed

        Usage
        -----
        Should be called, with a delay, before opening the "Visualized tags"
        pop-up:
        QTimer.singleShot(1000,
                          lambda:self.add_visualized_tag('AcquisitionDate'))
        """

        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            visualized_tags = w.layout().itemAt(0).widget()
            tags_list = visualized_tags.list_widget_tags

            if version.parse(QT_VERSION_STR) == version.parse('5.9.2'):
                found_item = tags_list.findItems(tag, Qt.MatchExactly)

            else:
                found_item = tags_list.findItems(tag,
                                                 Qt.MatchFlag.MatchExactly)

            tags_list.setCurrentItem(found_item[0])
            visualized_tags.click_select_tag()

    def execute_QDialogAccept(self):
        """
        Accept (close) a QDialog window
        """

        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            w.accept()

    def execute_QMessageBox_clickYes(self):
        """
        Is supposed to allow to press the Yes button if a pipeline is 
        overwritten in the test_zz_check_modifications method
        """
        w = QApplication.activeWindow()

        if isinstance(w, QMessageBox):
            close_button = w.button(QMessageBox.Yes)
            QTest.mouseClick(close_button, Qt.LeftButton)

    def execute_QDialogClose(self):
        """
        Is supposed to abort( close) a QDialog window
        """
        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            w.close()
    
    def get_new_test_project(self):
        """
        Copy the test project in a location we can modify safely
        """

        project_path = os.path.join(self.config_path, 'project_8')

        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        config = Config(config_path=self.config_path)
        mia_path = config.get_mia_path()
        project_8_path = os.path.join(mia_path, 'resources', 'mia',
                                      'project_8')
        shutil.copytree(project_8_path, project_path)
        return project_path

    def restart_MIA(self):
        """
        Restarts MIA within a unit test.

        Notes
        -----
        Can be used to restart MIA after changing the controller version in MIA
        preferences.
        """

        self.main_window.close()

        # Removing the opened projects (in CI, the tests are run twice)
        config = Config(config_path=self.config_path)
        config.set_opened_projects([])
        config.saveConfig()
        self.app.exit()

        config = Config(config_path=self.config_path)
        config.set_user_mode(False)
        self.app = QApplication.instance()

        if self.app is None:
            self.app = QApplication(sys.argv)

        self.project = Project(None, True)
        self.main_window = MainWindow(self.project, test=True)

    def setUp(self):
        """
        Called before each test
        """

        # All the tests are run in admin mode
        config = Config(config_path=self.config_path)
        config.set_user_mode(False)

        self.app = QApplication.instance()

        if self.app is None:
            self.app = QApplication(sys.argv)

        self.project = Project(None, True)
        self.main_window = MainWindow(self.project, test=True)

    @classmethod
    def setUpClass(cls):
        """
        Called once at the beginning of the class
        """

        cls.config_path = tempfile.mkdtemp(prefix='mia_tests')
        # hack the Config class to get config_path, because some Config
        # instances are created out of our control in the code
        Config.config_path = cls.config_path

    def tearDown(self):
        """
        Called after each test
        """

        self.main_window.close()

        # Removing the opened projects (in CI, the tests are run twice)
        config = Config(config_path=self.config_path)
        config.set_opened_projects([])
        config.saveConfig()

        self.app.exit()

    @classmethod
    def tearDownClass(cls):
        """
        Called once at the end of the class
        """

        if os.path.exists(cls.config_path):
            shutil.rmtree(cls.config_path)

    def test_add_tab(self):
        """
        Adds tabs to the PipelineEditorTabs
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)

        # Adding two new tabs
        pipeline_editor_tabs.new_tab()
        self.assertEqual(pipeline_editor_tabs.count(), 3)
        self.assertEqual(pipeline_editor_tabs.tabText(1), "New Pipeline 1")
        pipeline_editor_tabs.new_tab()
        self.assertEqual(pipeline_editor_tabs.count(), 4)
        self.assertEqual(pipeline_editor_tabs.tabText(2), "New Pipeline 2")

    def test_attributes_filter(self):
        '''
        Displays the parameters of a node, displays an attributes filter
        and modifies it.

        Notes:
        -----
        Tests AttributesFilter within the Node Controller V2
        (CapsulNodeController()).
        '''

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_controller = self.main_window.pipeline_manager.nodeController

        # Adds the process Smooth, creates a node called "smooth_1"
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Smooth)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the input plugs
        ppl_edt_tabs.get_current_editor().current_node_name = 'smooth_1'
        (ppl_edt_tabs.
                 get_current_editor)().export_node_unconnected_mandatory_plugs()

        # Displays parameters of 'inputs' node
        input_process = pipeline.nodes[''].process
        self.main_window.pipeline_manager.displayNodeParameters('inputs',
                                                                input_process)

        # Opens the attributes filter, selects item and closes it
        node_controller.filter_attributes()
        attributes_filter = node_controller.pop_up
        attributes_filter.table_data.selectRow(0)
        attributes_filter.ok_clicked()

        # Opens the attributes filter, does not select an item and closes it
        node_controller.filter_attributes()
        attributes_filter = node_controller.pop_up
        attributes_filter.search_str('!@#')
        attributes_filter.ok_clicked()

    def test_capsul_node_controller(self):
        """
        Adds, changes and deletes processes using the capsul node
        controller, displays the attributes filter.

        Notes:
        ------
        Tests the class CapsulNodeController().
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        DOCUMENT_1 = (self.main_window.project.session.
                                              get_documents_names)("current")[0]

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
        rename_process = pipeline.nodes['rename_2'].process
        self.main_window.pipeline_manager.displayNodeParameters('rename_2',
                                                                rename_process)

        # Tries changing its name to "rename_2" and then to "rename_3"
        node_ctrler.update_node_name()
        self.assertEqual(node_ctrler.node_name, 'rename_2')
        node_ctrler.update_node_name(new_node_name='rename_1',
                                     old_node_name='rename_2')
        self.assertEqual(node_ctrler.node_name, 'rename_2')
        node_ctrler.update_node_name(new_node_name='rename_3',
                                     old_node_name='rename_2')
        self.assertEqual(node_ctrler.node_name, 'rename_3')

        # Deletes node "rename_3"
        ppl_edt_tabs.get_current_editor().del_node("rename_3")

        # Display parameters of the "inputs" node
        input_process = pipeline.nodes[''].process
        node_ctrler.display_parameters('inputs',
                                       get_process_instance(input_process),
                                       pipeline)

        # Displays parameters of "rename_1" node
        rename_process = pipeline.nodes['rename_1'].process
        self.main_window.pipeline_manager.displayNodeParameters('rename_1',
                                                                rename_process)

        # Exports the input plugs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = 'rename_1'
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        pipeline.nodes['rename_1'].set_plug_value('in_file', DOCUMENT_1)
        pipeline.nodes['rename_1'].set_plug_value('format_string',
                                                  'new_name.nii')

        # Runs pipeline and expects an error
        # self.main_window.pipeline_manager.runPipeline()
        # FIXME: running the pipeline gives the error "wrapped C/C++ object of
        #        type PipelineEditorTabs has been deleted".

        # Displays attributes filter
        node_ctrler.filter_attributes()
        attributes_filter = node_ctrler.pop_up
        attributes_filter.table_data.selectRow(0)
        attributes_filter.ok_clicked()

        # Releases the process
        node_ctrler.release_process()
        node_ctrler.update_parameters()

    def test_close_tab(self):
        """
        Closes a tab in the PipelineEditorTabs
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)

        # Adding a new tab and closing the first one
        pipeline_editor_tabs.new_tab()
        pipeline_editor_tabs.close_tab(0)
        self.assertEqual(pipeline_editor_tabs.count(), 2)
        self.assertEqual(pipeline_editor_tabs.tabText(0), "New Pipeline 1")

        # When the last editor is closed, one is automatically opened
        pipeline_editor_tabs.close_tab(0)
        self.assertEqual(pipeline_editor_tabs.tabText(0), "New Pipeline")

        # Modifying the pipeline editor
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        self.assertEqual(pipeline_editor_tabs.tabText(0)[-2:], " *")

        # # Still some bug with the pop-up execution
        #
        #
        # # Closing the modified pipeline editor and clicking on "Cancel"
        # pipeline_editor_tabs.close_tab(0)
        # pop_up_close = pipeline_editor_tabs.pop_up_close
        # # QTest.mouseClick(pop_up_close.push_button_cancel, Qt.LeftButton)
        # # QTimer.singleShot(0, pop_up_close.push_button_cancel.clicked)
        # pop_up_close.cancel_clicked()
        # self.assertEqual(pipeline_editor_tabs.count(), 2)
        #
        # # Closing the modified pipeline editor and clicking on "Do not save"
        # pipeline_editor_tabs.close_tab(0)
        # pop_up_close = pipeline_editor_tabs.pop_up_close
        # # QTest.mouseClick(pop_up_close.push_button_do_not_save, Qt.LeftButton)
        # # QTimer.singleShot(0, pop_up_close.push_button_cancel.clicked)
        # pop_up_close.do_not_save_clicked()
        # self.assertEqual(pipeline_editor_tabs.count(), 1)

        # TODO: HOW TO TEST "SAVE AS" ACTION ?

    def test_display_filter(self):
        """
        Displays parameters of a node and displays a plug filter
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        node_controller = self.main_window.pipeline_manager.nodeController

        # Adding a process
        process_class = Threshold
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        # Creates a node called "threshold_1"
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exporting the input plugs and modifying the "synchronize" input plug
        (pipeline_editor_tabs.
                         get_current_editor)().current_node_name = "threshold_1"
        (pipeline_editor_tabs.
                      get_current_editor)().export_node_all_unconnected_inputs()

        input_process = pipeline.nodes[""].process
        node_controller.display_parameters("inputs",
                                           get_process_instance(input_process),
                                           pipeline)

        if hasattr(node_controller, 'get_index_from_plug_name'):
            index = node_controller.get_index_from_plug_name("synchronize",
                                                             "in")
            node_controller.line_edit_input[index].setText("2")
            # This calls "update_plug_value" method
            node_controller.line_edit_input[index].returnPressed.emit()

            # Calling the display_filter method
            node_controller.display_filter("inputs", "synchronize", (),
                                           input_process)
            node_controller.pop_up.close()
            self.assertEqual(2,
                             pipeline.nodes["threshold_1"].get_plug_value(
                                                                 "synchronize"))
        # TODO 1: currently we do not enter in the last if statement (controller
        #         v2). Implement the switch to V1 controller to enable the
        #         last if
        # TODO 2: open a project and modify the filter pop-up

    def test_drop_process(self):
        """
        Adds a Nipype SPM's Smooth process to the pipeline editor
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().drop_process(
                                                 'nipype.interfaces.spm.Smooth')
        self.assertTrue('smooth_1' in
                        (pipeline_editor_tabs.
                                           get_current_pipeline)().nodes.keys())

    def test_filter_widget(self):
        """
        Places a node of the "Input_Filter" process, feeds in documents
        and opens up the "FilterWidget()" to modify its parameters.

        Notes:
        -----
        Tests the class FilterWidget() within the Node Controller V1
        (class NodeController()). The class FilterWidget() is
        independent on the Node
        Controller version (V1 or V2) and can be used in both of them.
        """

        # Switches to node controller V1
        config = Config(config_path=self.config_path)
        config.setControlV1(True)

        self.restart_MIA()

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        DOCUMENT_2 = (self.main_window.project.session.
                                              get_documents_names)("current")[1]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_ctrler = self.main_window.pipeline_manager.nodeController

        # Adds the process Smooth, creates the node "input_filter_1"
        process_class = Input_Filter
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the input plugs for "input_filter_1"
        ppl_edt_tabs.get_current_editor().current_node_name = 'input_filter_1'
        (ppl_edt_tabs.
                 get_current_editor)().export_node_unconnected_mandatory_plugs()

        # Displays parameters of the "inputs" node
        input_process = pipeline.nodes[''].process
        node_ctrler.display_parameters('inputs',
                                       get_process_instance(input_process),
                                       pipeline)

        # Opens a filter for the plug "input" of the "inputs" node
        parameters = (0, pipeline, type(Undefined))
        node_ctrler.display_filter('inputs', 'input', parameters,
                                   input_process)

        # Selects all records in the "input" node
        plug_filter = node_ctrler.pop_up
        plug_filter.ok_clicked()

        # Opens the filter widget for the node "input_filter_1"
        ppl_edt_tabs.open_filter('input_filter_1')
        input_filter = ppl_edt_tabs.filter_widget

        #index_DOCUMENT_1 = input_filter.table_data.get_scan_row(DOCUMENT_1)
        #index_DOCUMENT_2 = input_filter.table_data.get_scan_row(DOCUMENT_2)

        # Tries to search for an empty string and asserts that none of the
        # documents are not hidden
        input_filter.search_str('')
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_1)) # if "DOCUMENT_1" is not hidden
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_2)) # if "DOCUMENT_1" is not hidden

        # Searches for "DOCUMENT_2" and verifies that "DOCUMENT_1" is hidden
        input_filter.search_str(DOCUMENT_2)
        # self.assertTrue(input_filter.table_data.isRowHidden(index_DOCUMENT_1))

        # Resets the search bar and assert that none of the documents are not hidden
        input_filter.reset_search_bar()
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_1)) # if "DOCUMENT_1" is not hidden
        # self.assertFalse(input_filter.table_data.isRowHidden(index_DOCUMENT_2)) # if "DOCUMENT_1" is not hidden
        # FIXME: input_filter.table_data.isRowHidden() does not work as expected

        # Opens the "Visualized tags" pop up and adds the "AcquisitionDate" tag
        input_filter.update_tags()
        self.add_visualized_tag('AcquisitionDate')
        self.assertTrue(type(input_filter.table_data.
                                      get_tag_column('AcquisitionDate')) == int)

        # Updates the tag to filter with
        input_filter.update_tag_to_filter()
        input_filter.push_button_tag_filter.setText('FileName')
        # TODO: select tag to filter with

        # Closes the filter
        input_filter.ok_clicked()

        # Switches back to node controller V2
        config = Config(config_path=self.config_path)
        config.setControlV1(False)

    # def test_init_MIA_processes(self):
    #     """
    #     Adds all the tools processes, initializes and runs the pipeline
    #     """
    #
    #     # Forcing the exit
    #     self.main_window.force_exit = True
    #
    #     # Adding the processes path to the system path
    #     import sys
    #     sys.path.append(os.path.join('..', '..', 'processes'))
    #
    #     pipeline_editor_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
    #
    #     pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
    #
    #     # Importing the package
    #     package_name = 'MIA_processes.IRMaGe.Tools'
    #     __import__(package_name)
    #     pkg = sys.modules[package_name]
    #     process_class = None
    #     for name, cls in sorted(list(pkg.__dict__.items())):
    #         if name != "Input_Filter":
    #             try:
    #                 proc_instance = get_process_instance(cls)
    #             except:
    #                 pass
    #             else:
    #                 print("class", cls)
    #                 process_class = cls
    #                 pipeline_editor_tabs.get_current_editor().add_process(process_class)
    #
    #     pipeline = pipeline_editor_tabs.get_current_pipeline()
    #
    #     # Verifying that all the processes are here
    #     self.assertTrue('duplicate_file1' in pipeline.nodes.keys())
    #     self.assertTrue('find_in_list1' in pipeline.nodes.keys())
    #     self.assertTrue('files_to_list1' in pipeline.nodes.keys())
    #     self.assertTrue('list_to_file1' in pipeline.nodes.keys())
    #     self.assertTrue('list_duplicate1' in pipeline.nodes.keys())
    #     self.assertTrue('roi_list_generator1' in pipeline.nodes.keys())
    #
    #     # Setting values to verify that the initialization works well
    #     pipeline.nodes['duplicate_file1'].set_plug_value('file1', 'test_file.txt')
    #     pipeline.nodes['find_in_list1'].set_plug_value('in_list', ['test1.txt', 'test2.txt'])
    #     pipeline.nodes['find_in_list1'].set_plug_value('pattern', '1')
    #     pipeline.nodes['files_to_list1'].set_plug_value('file1', 'test1.txt')
    #     pipeline.nodes['files_to_list1'].set_plug_value('file2', 'test2.txt')
    #     pipeline.nodes['list_to_file1'].set_plug_value('file_list', ['test1.txt', 'test2.txt'])
    #     pipeline.nodes['list_duplicate1'].set_plug_value('file_name', 'test_file.txt')
    #     pipeline.nodes['roi_list_generator1'].set_plug_value('pos', ['TEST1', 'TEST2'])
    #
    #     # Initialization/run of the pipeline
    #     self.main_window.pipeline_manager.init_pipeline()
    #     self.main_window.pipeline_manager.runPipeline()
    #
    #     # Verifying the results
    #     self.assertEqual(pipeline.nodes['duplicate_file1'].get_plug_value('out_file1'), 'test_file.txt')
    #     self.assertEqual(pipeline.nodes['duplicate_file1'].get_plug_value('out_file2'), 'test_file.txt')
    #     self.assertEqual(pipeline.nodes['find_in_list1'].get_plug_value('out_file'), 'test1.txt')
    #     self.assertEqual(pipeline.nodes['files_to_list1'].get_plug_value('file_list'), ['test1.txt', 'test2.txt'])
    #     self.assertEqual(pipeline.nodes['list_to_file1'].get_plug_value('file'), 'test1.txt')
    #     self.assertEqual(pipeline.nodes['list_duplicate1'].get_plug_value('out_list'), ['test_file.txt'])
    #     self.assertEqual(pipeline.nodes['list_duplicate1'].get_plug_value('out_file'), 'test_file.txt')
    #     self.assertEqual(pipeline.nodes['roi_list_generator1'].get_plug_value('roi_list'), [['TEST1', '_L'],
    #                                                                                         ['TEST1', '_R'],
    #                                                                                         ['TEST2', '_L'],
    #                                                                                         ['TEST2', '_R']])
    #
    # def test_init_SPM_pre_processes(self):
    #     """
    #     Adds all SPM pre-processes and initializes the pipeline
    #     """
    #
    #     # Forcing the exit
    #     self.main_window.force_exit = True
    #
    #     # Adding the processes path to the system path
    #     import sys
    #     sys.path.append(os.path.join('..', '..', 'processes'))
    #
    #     pipeline_editor_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
    #
    #     pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
    #
    #     # Importing the package
    #     package_name = 'MIA_processes.SPM'
    #     __import__(package_name)
    #     pkg = sys.modules[package_name]
    #     process_class = None
    #     preproc_list = ['Smooth', 'NewSegment', 'Normalize', 'Realign', 'Coregister']
    #     for name, cls in sorted(list(pkg.__dict__.items())):
    #         if name in preproc_list:
    #             try:
    #                 proc_instance = get_process_instance(cls)
    #             except:
    #                 pass
    #             else:
    #                 process_class = cls
    #                 pipeline_editor_tabs.get_current_editor().add_process(process_class)
    #
    #     pipeline = pipeline_editor_tabs.get_current_pipeline()
    #
    #     # Verifying that all the processes are here
    #     self.assertTrue('smooth1' in pipeline.nodes.keys())
    #     self.assertTrue('newsegment1' in pipeline.nodes.keys())
    #     self.assertTrue('normalize1' in pipeline.nodes.keys())
    #     self.assertTrue('realign1' in pipeline.nodes.keys())
    #     self.assertTrue('coregister1' in pipeline.nodes.keys())
    #
    #     # Choosing a nii file from the project_8's raw_data folder
    #     folder = os.path.join('project_8', 'data', 'raw_data')
    #     nii_file = 'Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000.nii'
    #     nii_no_ext = 'Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_Guerbet_Anat-RAREpvm-000220_000'
    #     nii_path = os.path.abspath(os.path.join(folder, nii_file))
    #
    #     # Setting values to verify that the initialization works well
    #     pipeline.nodes['smooth1'].set_plug_value('in_files', nii_path)
    #     pipeline.nodes['newsegment1'].set_plug_value('channel_files', nii_path)
    #     pipeline.nodes['normalize1'].set_plug_value('apply_to_files', nii_path)
    #     if os.path.isfile(os.path.join(folder, 'y_' + nii_file)):
    #         pipeline.nodes['normalize1'].set_plug_value('deformation_file',
    #                                                     os.path.abspath(os.path.join(folder, 'y_' + nii_file)))
    #     else:
    #         # This makes no sense but for the moment, we only check the initialization
    #         # and we just need to put a file in this plug
    #         pipeline.nodes['normalize1'].set_plug_value('deformation_file',
    #                                                     os.path.abspath(os.path.join(folder, nii_file)))
    #
    #     pipeline.nodes['realign1'].set_plug_value('in_files', nii_path)
    #
    #     # This makes no sense but for the moment, we only check the initialization
    #     # and we just need to put a file in this plug
    #     pipeline.nodes['coregister1'].set_plug_value('apply_to_files', nii_path)
    #     pipeline.nodes['coregister1'].set_plug_value('target', nii_path)
    #     pipeline.nodes['coregister1'].set_plug_value('source', nii_path)
    #
    #     # Initialization/run of the pipeline
    #     self.main_window.pipeline_manager.init_pipeline()
    #
    #     # Verifying the results
    #     self.assertEqual(pipeline.nodes['smooth1'].get_plug_value('smoothed_files'),
    #                      os.path.abspath(os.path.join(folder, 's' + nii_file)))
    #     self.assertTrue(pipeline.nodes['newsegment1'].get_plug_value('native_class_images'),
    #                     os.path.abspath(os.path.join(folder, 'c1' + nii_file)))
    #     self.assertTrue(pipeline.nodes['newsegment1'].get_plug_value('native_class_images'),
    #                     os.path.abspath(os.path.join(folder, 'c2' + nii_file)))
    #     self.assertTrue(pipeline.nodes['newsegment1'].get_plug_value('native_class_images'),
    #                     os.path.abspath(os.path.join(folder, 'c3' + nii_file)))
    #     self.assertTrue(pipeline.nodes['newsegment1'].get_plug_value('native_class_images'),
    #                     os.path.abspath(os.path.join(folder, 'c4' + nii_file)))
    #     self.assertTrue(pipeline.nodes['newsegment1'].get_plug_value('native_class_images'),
    #                     os.path.abspath(os.path.join(folder, 'c5' + nii_file)))
    #     self.assertTrue(pipeline.nodes['newsegment1'].get_plug_value('native_class_images'),
    #                     os.path.abspath(os.path.join(folder, 'c6' + nii_file)))
    #     self.assertEqual(pipeline.nodes['newsegment1'].get_plug_value('bias_field_images'),
    #                      os.path.abspath(os.path.join(folder, 'BiasField_' + nii_file)))
    #     self.assertEqual(pipeline.nodes['newsegment1'].get_plug_value('forward_deformation_field'),
    #                      os.path.abspath(os.path.join(folder, 'y_' + nii_file)))
    #     self.assertEqual(pipeline.nodes['normalize1'].get_plug_value('normalized_files'),
    #                      os.path.abspath(os.path.join(folder, 'w' + nii_file)))
    #     self.assertEqual(pipeline.nodes['realign1'].get_plug_value('realigned_files'),
    #                      os.path.abspath(os.path.join(folder, 'r' + nii_file)))
    #     self.assertEqual(pipeline.nodes['realign1'].get_plug_value('mean_image'),
    #                      os.path.abspath(os.path.join(folder, 'mean' + nii_file)))
    #     self.assertEqual(pipeline.nodes['realign1'].get_plug_value('realignment_parameters'),
    #                      os.path.abspath(os.path.join(folder, 'rp_' + nii_no_ext + '.txt')))
    #     self.assertEqual(pipeline.nodes['coregister1'].get_plug_value('coregistered_files'),
    #                      os.path.abspath(os.path.join(folder, nii_file)))

    def test_iteration_table(self):
        """
        Plays with the iteration table
        """

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        iteration_table = self.main_window.pipeline_manager.iterationTable
        QTimer.singleShot(1000, self.execute_QDialogAccept)
        iteration_table.check_box_iterate.setChecked(True)
        iteration_table.update_selected_tag("BandWidth")
        iteration_table.update_iterated_tag("BandWidth")
        self.assertEqual(iteration_table.iterated_tag_label.text(),
                         "BandWidth:")
        iteration_table.add_tag()
        self.assertEqual(len(iteration_table.push_buttons), 3)
        iteration_table.remove_tag()
        self.assertEqual(len(iteration_table.push_buttons), 2)
        iteration_table.add_tag()
        iteration_table.push_buttons[2].setText("AcquisitionTime")
        iteration_table.fill_values(2)
        iteration_table.update_table()
        self.assertTrue(iteration_table.combo_box.currentText()[1:-1] in [
                                                                     "65789.48",
                                                                     "25000.0",
                                                                     "50000.0"])

    '''def test_open_filter(self):
        """
        Opens an input filter
        """

        # Adding the processes path to the system path
        import sys
        sys.path.append(os.path.join('..', '..', 'processes'))

        # Importing the package
        package_name = 'MIA_processes.IRMaGe.Tools'
        __import__(package_name)
        pkg = sys.modules[package_name]
        process_class = None
        for name, cls in sorted(list(pkg.__dict__.items())):
            if name == 'Input_Filter':
                process_class = cls

        if not process_class:
            print('No Input_Filer class found')
            return

        pipeline_editor_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_process(process_class)  # Creates a node called "input_filter1"
        pipeline_editor_tabs.open_filter("input_filter1")
        pipeline_editor_tabs.filter_widget.close()
        self.assertFalse(pipeline.nodes["input_filter1"].get_plug_value("output"))

        # TODO: open a project and modify the filter pop-up
    '''

    def test_node_controller(self):
        """
        Adds, changes and deletes processes to the node controller,
        display the attributes filter.

        Notes:
        ------
        Tests the class NodeController().
        """

        # Switches to node controller V1
        config = Config(config_path=self.config_path)
        config.setControlV1(True)

        self.restart_MIA()

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        DOCUMENT_1 = (self.main_window.project.session.
                                              get_documents_names)("current")[0]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        node_ctrler = self.main_window.pipeline_manager.nodeController

        # Adds the process Rename, creates the "rename_1" nodes
        process_class = Rename
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Displays parameters of "rename_2" node
        rename_process = pipeline.nodes['rename_2'].process
        self.main_window.pipeline_manager.displayNodeParameters('rename_2',
                                                                rename_process)

        # Tries to changes its name to "rename_2" and then to "rename_3"
        node_ctrler.update_node_name()
        self.assertEqual(node_ctrler.node_name, 'rename_2')
        node_ctrler.update_node_name(new_node_name='rename_1')
        self.assertEqual(node_ctrler.node_name, 'rename_2')
        node_ctrler.update_node_name(new_node_name='rename_3')
        self.assertEqual(node_ctrler.node_name, 'rename_3')

        # Deletes node "rename_2"
        ppl_edt_tabs.get_current_editor().del_node("rename_3")
        self.assertRaises(KeyError, lambda: pipeline.nodes['rename_3'])

        # Exports the input plugs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = 'rename_1'
        (ppl_edt_tabs.
                     get_current_editor)().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Display parameters of the "inputs" node
        input_process = pipeline.nodes[''].process
        node_ctrler.display_parameters('inputs',
                                       get_process_instance(input_process),
                                       pipeline)

        # Display the filter of the 'in_file' plug, "inputs" node
        node_ctrler.display_filter('inputs', 'in_file',
                                   (0, pipeline, type(Undefined)),
                                   input_process)
        node_ctrler.pop_up.close()

        # Sets the values of the mandatory plugs
        pipeline.nodes[''].set_plug_value('in_file', DOCUMENT_1)
        pipeline.nodes[''].set_plug_value('format_string', 'new_file.nii')

        # Checks the indexed of input and output plug labels
        in_plug_index = node_ctrler.get_index_from_plug_name('in_file','in')
        self.assertEqual(in_plug_index, 1)
        out_plug_index = node_ctrler.get_index_from_plug_name('_out_file',
                                                              'out')
        self.assertEqual(out_plug_index, 0)

        # Tries to updates the plug value without a new value
        node_ctrler.update_plug_value('in', 'in_file', pipeline,
                                      type(Undefined))
        node_ctrler.update_plug_value('out', '_out_file', pipeline,
                                      type(Undefined))
        node_ctrler.update_plug_value(None, 'in_file', pipeline,
                                      type(Undefined))

        # Tries to updates the plug value with a new value
        node_ctrler.update_plug_value('in', 'in_file', pipeline, str,
                                      new_value='new_value.nii')
        node_ctrler.update_plug_value('out', '_out_file', pipeline, str,
                                      new_value='new_value.nii')

        # Releases the process
        node_ctrler.release_process()
        node_ctrler.update_parameters()

        # Switches back to node controller V2
        config = Config(config_path=self.config_path)
        config.setControlV1(False)

    def test_plug_filter(self):
        """
        Displays the parameters of a node, displays a plug filter
        and modifies it.

        Notes:
        -----
        Tests the class PlugFilter() within the Node Controller V1
        (class NodeController()).
        """

        # Switches to node controller V1
        config = Config(config_path=self.config_path)
        config.setControlV1(True)

        self.restart_MIA()

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, "project_8")

        # Get the 2 first documents/records
        DOCUMENT_1 = (self.main_window.project.session.
                                              get_documents_names)("current")[0]
        DOCUMENT_2 = (self.main_window.project.session.
                                              get_documents_names)("current")[1]

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        node_controller = self.main_window.pipeline_manager.nodeController

        # Add the "Smooth" process
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)

        # Creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exports the mandatory plugs
        pipeline_editor_tabs.get_current_editor().current_node_name = "smooth_1"
        (pipeline_editor_tabs.
                 get_current_editor)().export_node_unconnected_mandatory_plugs()

        # Display parameters of "smooth_1" node
        input_process = pipeline.nodes[""].process

        node_controller.display_parameters("inputs",
                                           get_process_instance(input_process),
                                           pipeline)

        # Opens a filter for the plug "in_files",
        # without "node_controller.scans_list"
        parameters = (0, pipeline, type(Undefined))
        node_controller.display_filter("inputs", "in_files",
                                       parameters, input_process)

        # Asserts its default value
        node = pipeline.nodes[""]
        self.assertEqual(Undefined, node.get_plug_value("in_files"))

        # Searchs for "DOCUMENT_2" the input documents
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
        plug_filter.search_str('')

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

        self.assertTrue(type(
               plug_filter.table_data.get_tag_column('AcquisitionDate')) == int)

        plug_filter.update_tag_to_filter()
        plug_filter.push_button_tag_filter.setText('FileName')
        # TODO: select tag to filter with

        # Closes the filter for the plug "in_files"
        plug_filter.ok_clicked()

        # Assert the modified value
        self.assertIn(str(Path(DOCUMENT_2)),
                      str(Path(node.get_plug_value("in_files")[0])))

        # Opens a filter for the plug "in_files", now with a "scans_list"
        node_controller.scan_list = (self.main_window.project.session.
                                     get_documents_names)("current")
        node_controller.display_filter("inputs", "in_files",
                                       parameters, input_process)

        # Searchs for something that does not give any match
        plug_filter.search_str('!@#')
        # this will empty the "plug_filter.table_data.selectedIndexes()"
        # and trigger a uncovered part of "set_plug_value(self)"

        plug_filter.ok_clicked()

        # Switches back to node controller V2
        config = Config(config_path=self.config_path)
        config.setControlV1(False)

    def test_process_library(self):
        """
        Install the brick_test and then remove it
        """

        config = Config(config_path=self.config_path)
        QMessageBox.exec = lambda x: True

        pkg = InstallProcesses(self.main_window, folder=False)
        brick = os.path.join(config.get_mia_path(), 'resources',
                             'mia', 'brick_test.zip')
        pkg.path_edit.text = lambda: brick
        pkg.install()

        pkg = PackageLibraryDialog(self.main_window)
        pkg.save()

        with open(os.path.join(config.get_mia_path(), 'properties',
                               'process_config.yml'),
                  'r') as stream:

            if verCmp(yaml.__version__, '5.1', 'sup'):
                pro_dic = yaml.load(stream, Loader=yaml.FullLoader)

            else:
                pro_dic = yaml.load(stream)

            self.assertIn("brick_test", pro_dic["Packages"])

        pkg.remove_package("brick_test")
        pkg.save_config()

        process = os.path.join(config.get_mia_path(), 'processes',
                               'brick_test')
        shutil.rmtree(process)

        with open(os.path.join(config.get_mia_path(), 'properties',
                               'process_config.yml'),
                  'r') as stream:

            if verCmp(yaml.__version__, '5.1', 'sup'):
                pro_dic = yaml.load(stream, Loader=yaml.FullLoader)

            else:
                pro_dic = yaml.load(stream)

            self.assertNotIn("brick_test", pro_dic["Packages"])

    def test_save_pipeline(self):
        """
        Saves a simple pipeline
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        node_controller = self.main_window.pipeline_manager.nodeController
        config = Config(config_path=self.config_path)

        # Adding a process
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)

        # Creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        # Displaying the node parameters
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        node_controller.display_parameters("smooth_1",
                                           get_process_instance(process_class),
                                           pipeline)

        # Exporting the input plugs
        pipeline_editor_tabs.get_current_editor().current_node_name = "smooth_1"
        (pipeline_editor_tabs.
                 get_current_editor)().export_node_unconnected_mandatory_plugs()
        (pipeline_editor_tabs.
                     get_current_editor)().export_node_all_unconnected_outputs()

        filename = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline.py')
        save_pipeline(pipeline, filename)
        self.main_window.pipeline_manager.updateProcessLibrary(filename)
        self.assertTrue(os.path.isfile(os.path.join(config.get_mia_path(),
                                                    'processes',
                                                    'User_processes',
                                                    'test_pipeline.py')))

    def test_update_node_name(self):
        """
        Displays parameters of a node and updates its name
        """

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_editor_tabs = pipeline_manager.pipelineEditorTabs

        # Adding a process => creates a node called "smooth_1"
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        # Displaying the smooth_1 node parameters
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        process = pipeline.nodes['smooth_1'].process
        pipeline_manager.displayNodeParameters("smooth_1", process)
        node_controller = pipeline_manager.nodeController

        # Change the node name from smooth_1 to smooth_test, test if it's ok
        node_controller.line_edit_node_name.setText("smooth_test")
        keyEvent = QtGui.QKeyEvent(QEvent.KeyPress, Qt.Key_Return,
                                   Qt.NoModifier)
        QCoreApplication.postEvent(node_controller.line_edit_node_name,
                                   keyEvent)
        QTest.qWait(100)
        self.assertTrue("smooth_test" in pipeline.nodes.keys())

        # Add 2 another Smooth process => Creates nodes called
        # smooth_1 and smooth_2
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        # Adding link between smooth_test and smooth_1 nodes
        source = ('smooth_test', '_smoothed_files')
        dest = ('smooth_1', 'in_files')
        pipeline_editor_tabs.get_current_editor().add_link(source, dest, True,
                                                           False)

        # Adding link between smooth_2 and smooth_1 nodes
        source = ('smooth_1', '_smoothed_files')
        dest = ('smooth_2', 'in_files')
        pipeline_editor_tabs.get_current_editor().add_link(source, dest, True,
                                                           False)

        # Displaying the smooth_1 node parameters
        process = pipeline.nodes['smooth_1'].process
        pipeline_manager.displayNodeParameters("smooth_1", process)
        node_controller = pipeline_manager.nodeController

        # Change node name from smooth_1 to smooth_test.
        # This should not change the node name because there is already a
        # "smooth_test" process in the pipeline.
        # Test if smooth_1 is still in the pipeline
        node_controller.line_edit_node_name.setText("smooth_test")
        keyEvent = QtGui.QKeyEvent(QEvent.KeyPress, Qt.Key_Return,
                                   Qt.NoModifier)
        QCoreApplication.postEvent(node_controller.line_edit_node_name,
                                   keyEvent)
        QTest.qWait(100)
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        node_controller.line_edit_node_name.setText("smooth_test_2")
        keyEvent = QtGui.QKeyEvent(QEvent.KeyPress, Qt.Key_Return,
                                   Qt.NoModifier)
        QCoreApplication.postEvent(node_controller.line_edit_node_name,
                                   keyEvent)
        QTest.qWait(100)
        self.assertTrue("smooth_test_2" in pipeline.nodes.keys())

        # Verifying that the updated node has the same links
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_test_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_test_2"].plugs[
                                                   "_smoothed_files"].links_to))

    def test_update_plug_value(self):
        """
        Displays parameters of a node and updates a plug value
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        node_controller = self.main_window.pipeline_manager.nodeController

        # Adding a process
        process_class = Threshold
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)

        # Creates a node called "threshold_1":
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        # Displaying the node parameters
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        node_controller.display_parameters("threshold_1",
                                           get_process_instance(process_class),
                                           pipeline)

        # Updating the value of the "synchronize" plug
        if hasattr(node_controller, 'get_index_from_plug_name'):
            index = node_controller.get_index_from_plug_name("synchronize",
                                                             "in")
            node_controller.line_edit_input[index].setText("1")

            # This calls "update_plug_value" method:
            node_controller.line_edit_input[index].returnPressed.emit()
            self.assertEqual(1,
                             pipeline.nodes["threshold_1"].get_plug_value(
                                                                 "synchronize"))

            # Updating the value of the "_activation_forced" plug
            index = node_controller.get_index_from_plug_name(
                                                           "_activation_forced",
                                                           "out")
            node_controller.line_edit_output[index].setText("True")

            # This calls "update_plug_value" method:
            node_controller.line_edit_output[index].returnPressed.emit()
            self.assertEqual(True,
                             pipeline.nodes["threshold_1"].get_plug_value(
                                                          "_activation_forced"))

        # Exporting the input plugs and modifying the "synchronize" input plug
        (pipeline_editor_tabs.
                         get_current_editor)().current_node_name = "threshold_1"
        (pipeline_editor_tabs.
                      get_current_editor)().export_node_all_unconnected_inputs()

        input_process = pipeline.nodes[""].process
        node_controller.display_parameters("inputs",
                                           get_process_instance(input_process),
                                           pipeline)

        if hasattr(node_controller, 'get_index_from_plug_name'):
            index = node_controller.get_index_from_plug_name("synchronize",
                                                             "in")
            node_controller.line_edit_input[index].setText("2")

            # This calls "update_plug_value" method:
            node_controller.line_edit_input[index].returnPressed.emit()
            self.assertEqual(2,
                             pipeline.nodes["threshold_1"].get_plug_value(
                                                                 "synchronize"))

    def test_z_get_editor(self):
        """
        Gets the instance of an editor (z to run at the end)

        This tests:
         - PipelineEditorTabs.get_editor_by_index
         - PipelineEditorTabs.get_current_editor
         - PipelineEditorTabs.get_editor_by_tab_name
         - PipelineEditorTabs.get_editor_by_filename
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        config = Config(config_path=self.config_path)

        filename = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline.py')
        pipeline_editor_tabs.load_pipeline(filename)

        editor0 = pipeline_editor_tabs.get_current_editor()
        # create new tab with new editor and make it current:
        pipeline_editor_tabs.new_tab()
        editor1 = pipeline_editor_tabs.get_current_editor()

        self.assertEqual(pipeline_editor_tabs.get_editor_by_index(0), editor0)
        self.assertEqual(pipeline_editor_tabs.get_editor_by_index(1), editor1)
        self.assertEqual(pipeline_editor_tabs.get_current_editor(), editor1)
        self.assertEqual(editor0,
                         pipeline_editor_tabs.get_editor_by_tab_name(
                                                            "test_pipeline.py"))
        self.assertEqual(editor1,
                         pipeline_editor_tabs.get_editor_by_tab_name(
                                                              "New Pipeline 1"))
        self.assertEqual(None,
                         pipeline_editor_tabs.get_editor_by_tab_name("dummy"))
        self.assertEqual(editor0,
                         pipeline_editor_tabs.get_editor_by_file_name(filename))
        self.assertEqual(None,
                         pipeline_editor_tabs.get_editor_by_file_name("dummy"))

    def test_z_get_filename(self):
        """
        Gets the relative path to a previously saved pipeline file
        (z to run at the end).

        This tests:
         - PipelineEditorTabs.get_filename_by_index
         - PipelineEditorTabs.get_current_filename
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        config = Config(config_path=self.config_path)

        filename = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline.py')
        pipeline_editor_tabs.load_pipeline(filename)

        self.assertEqual(filename,
                         os.path.abspath(
                             pipeline_editor_tabs.get_filename_by_index(0)))
        self.assertEqual(None, pipeline_editor_tabs.get_filename_by_index(1))
        self.assertEqual(filename,
                         os.path.abspath(
                             pipeline_editor_tabs.get_current_filename()))

    def test_z_get_index(self):
        """
        Gets the index of an editor. (z to run at the end)

        This tests:
         - PipelineEditorTabs.get_index_by_tab_name
         - PipelineEditorTabs.get_index_by_filename
         - PipelineEditorTabs.get_index_by_editor
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        config = Config(config_path=self.config_path)
        filename = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline.py')
        pipeline_editor_tabs.load_pipeline(filename)
        editor0 = pipeline_editor_tabs.get_current_editor()

        # create new tab with new editor and make it current
        pipeline_editor_tabs.new_tab()
        editor1 = pipeline_editor_tabs.get_current_editor()

        self.assertEqual(0,
                         pipeline_editor_tabs.get_index_by_tab_name(
                                                            "test_pipeline.py"))
        self.assertEqual(1,
                         pipeline_editor_tabs.get_index_by_tab_name(
                                                              "New Pipeline 1"))
        self.assertEqual(None,
                         pipeline_editor_tabs.get_index_by_tab_name("dummy"))

        self.assertEqual(0,
                         pipeline_editor_tabs.get_index_by_filename(filename))
        self.assertEqual(None,
                         pipeline_editor_tabs.get_index_by_filename("dummy"))

        self.assertEqual(0, pipeline_editor_tabs.get_index_by_editor(editor0))
        self.assertEqual(1, pipeline_editor_tabs.get_index_by_editor(editor1))
        self.assertEqual(None,
                         pipeline_editor_tabs.get_index_by_editor("dummy"))

    def test_z_get_tab_name(self):
        """
        Gets the tab name of the editor. (z to run at the end)

        This tests:
         - PipelineEditorTabs.get_tab_name_by_index
         - PipelineEditorTabs.get_current_tab_name
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)

        self.assertEqual("New Pipeline",
                         pipeline_editor_tabs.get_tab_name_by_index(0))
        self.assertEqual(None,
                         pipeline_editor_tabs.get_tab_name_by_index(1))
        self.assertEqual("New Pipeline",
                         pipeline_editor_tabs.get_current_tab_name())

    def test_z_load_pipeline(self):
        """
        Loads a pipeline (z to run at the end)
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        config = Config(config_path=self.config_path)

        filename = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline.py')
        pipeline_editor_tabs.load_pipeline(filename)

        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

    def test_z_open_sub_pipeline(self):
        """
        Opens a sub_pipeline (z to run at the end)
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        config = Config(config_path=self.config_path)

        # Adding the processes path to the system path
        sys.path.append(os.path.join(config.get_mia_path(), 'processes'))

        # Importing the package
        package_name = 'User_processes'
        __import__(package_name)
        pkg = sys.modules[package_name]

        for name, cls in sorted(list(pkg.__dict__.items())):

            if name == 'Test_pipeline':
                process_class = cls

        # Adding the "test_pipeline" as a process
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        # Opening the sub-pipeline in a new editor
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        process_instance = pipeline.nodes["test_pipeline_1"].process
        pipeline_editor_tabs.open_sub_pipeline(process_instance)

        self.assertTrue(3, pipeline_editor_tabs.count())
        self.assertEqual("test_pipeline.py",
                         os.path.basename(
                             pipeline_editor_tabs.get_filename_by_index(1)))

    def test_z_set_current_editor(self):
        """
        Sets the current editor (z to run at the end)

        This tests:
         - PipelineEditorTabs.set_current_editor_by_tab_name
         - PipelineEditorTabs.set_current_editor_by_file_name
         - PipelineEditorTabs.set_current_editor_by_editor
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        config = Config(config_path=self.config_path)
        filename = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline.py')
        pipeline_editor_tabs.load_pipeline(filename)
        editor0 = pipeline_editor_tabs.get_current_editor()

        # create new tab with new editor and make it current:
        pipeline_editor_tabs.new_tab()
        editor1 = pipeline_editor_tabs.get_current_editor()

        pipeline_editor_tabs.set_current_editor_by_tab_name("test_pipeline.py")
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 0)
        pipeline_editor_tabs.set_current_editor_by_tab_name("New Pipeline 1")
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 1)

        pipeline_editor_tabs.set_current_editor_by_file_name(filename)
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 0)

        pipeline_editor_tabs.set_current_editor_by_editor(editor1)
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 1)
        pipeline_editor_tabs.set_current_editor_by_editor(editor0)
        self.assertEqual(pipeline_editor_tabs.currentIndex(), 0)

    def test_zz_check_modif(self):
        """
        Opens a pipeline, opens it as a process in another tab, modifies it
        and check the modifications
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        config = Config(config_path=self.config_path)

        filename = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline.py')
        pipeline_editor_tabs.load_pipeline(filename)

        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        pipeline_editor_tabs.new_tab()
        pipeline_editor_tabs.set_current_editor_by_tab_name("New Pipeline 1")
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)

        pipeline_editor_tabs.get_current_editor().drop_process(
                                                 "User_processes.Test_pipeline")
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        self.assertTrue("test_pipeline_1" in pipeline.nodes.keys())

        pipeline_editor_tabs.get_current_editor().drop_process(
                                                 "nipype.interfaces.spm.Smooth")
        pipeline_editor_tabs.get_current_editor().drop_process(
                                                 "nipype.interfaces.spm.Smooth")
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())

        pipeline_editor_tabs.get_current_editor().add_link(
                                                ("smooth_1", "_smoothed_files"),
                                                ("test_pipeline_1", "in_files"),
                                                active=True, weak=False)

        self.assertEqual(1,
                         len(pipeline.nodes["test_pipeline_1"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        pipeline_editor_tabs.get_current_editor().add_link(
                                         ("test_pipeline_1", "_smoothed_files"),
                                         ("smooth_2", "in_files"),
                                         active=True, weak=False)

        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["test_pipeline_1"].plugs[
                                                   "_smoothed_files"].links_to))

        pipeline_editor_tabs.set_current_editor_by_tab_name("test_pipeline.py")
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)

        (pipeline_editor_tabs.
                          get_current_editor)().export_node_plugs("smooth_1",
                                                                  optional=True)
        self.main_window.pipeline_manager.savePipeline(uncheck=True)

        pipeline_editor_tabs.set_current_editor_by_tab_name("New Pipeline 1")
        pipeline_editor_tabs.get_current_editor().scene.pos[
                                           "test_pipeline_1"] = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().check_modifications()

        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("fwhm" in
                                 pipeline.nodes["test_pipeline_1"].plugs.keys())

    def test_zz_del_pack(self):
        """ We remove the brick created during the unit tests, and we take
        advantage of this to cover the part of the code used to remove the
        packages """
         
        pkg = PackageLibraryDialog(self.main_window)

        # The Test_pipeline brick was added in the package library
        self.assertTrue("Test_pipeline" in
                             pkg.package_library.package_tree['User_processes'])

        pkg.delete_package(to_delete="User_processes.Test_pipeline", loop=True)

        # The Test_pipeline brick has been removed from the package library
        self.assertFalse("Test_pipeline" in
                             pkg.package_library.package_tree['User_processes'])


class TestMIAPipelineManagerTab(unittest.TestCase):
    """Tests 'pipeline_manager_tab.py'.

    :Contains:
        :Method:
            - add_visualized_tag: selects a tag to display with the
              "Visualized tags" pop-up
            - execute_QDialogAccept: accept (close) a QDialog window
            - get_new_test_project: create a temporary project that can
              be safely modified
            - restart_MIA: restarts MIA within a unit test.
            - setUp: called automatically before each test method
            - setUpClass: called before tests in the individual class
            - tearDown: cleans up after each test method
            - tearDownClass: called after tests in the individual class
            - test_add_plug_value_to_database_list_type: adds a list 
              type plug value to the database
            - test_add_plug_value_to_database_non_list_type: adds a non 
              list type plug value to the database
            - test_ask_iterated_pipeline_plugs: test the iteration dialog for
               each plug of a Rename process
            - test_build_iterated_pipeline: mocks methods and builds an 
              iterated pipeline
            - test_check_requirements: checks the requirements for a
              given node
            - test_cleanup_older_init: tests the cleaning of old initialisations
            - test_complete_pipeline_parameters: test the pipeline parameters
              completion
            - test_delete_processes: deletes a process and makes the 
              undo/redo
            - test_finish_execution: finishes the execution of the 
              pipeline
            - test_garbage_collect: collects the garbage of the pipeline
            - test_get_capsul_engine: gets the capsul engine of the
              pipeline
            - test_get_missing_mandatory_parameters: tries to initialize
              the pipeline with missing mandatory parameters
            - test_get_pipeline_or_process: gets a pipeline and a
              process from the pipeline_manager
            - test_initialize: mocks objects and initializes the 
              workflow
            - test_register_completion_attributes: registers completion 
              attributes
            - test_register_node_io_in_database: sets input and output 
              parameters and registers them in database
            - test_remove_progress: removes the progress of the pipeline
            - test_save_pipeline: saves a simple pipeline
            - test_set_anim_frame: runs the 'rotatingBrainVISA.gif' 
              animation
            - test_undo_redo: tests the undo/redo
            - test_update_node_list: initializes a workflow and adds a 
              process to the "pipline_manager.node_list"
            - test_z_init_pipeline: initializes the pipeline
            - test_z_init_pipeline_2: initialize a pipeline with several
               mock parameters
            - test_z_runPipeline: adds a processruns a pipeline
            - test_zz_del_pack(self): deletion of the brick created during UTs
    """

    def add_visualized_tag(self, tag):
        """
        With the "Visualized tags" pop-up open, selects a tag to display.

        Parameters
        ----------
        tag: string
          The tag to be displayed

        Usage
        -----
        Should be called, with a delay, before opening the "Visualized tags"
        pop-up:
        QTimer.singleShot(1000,
                          lambda:self.add_visualized_tag('AcquisitionDate'))
        """

        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            visualized_tags = w.layout().itemAt(0).widget()
            tags_list = visualized_tags.list_widget_tags

            if version.parse(QT_VERSION_STR) == version.parse('5.9.2'):
                found_item = tags_list.findItems(tag, Qt.MatchExactly)

            else:
                found_item = tags_list.findItems(tag,
                                                 Qt.MatchFlag.MatchExactly)

            tags_list.setCurrentItem(found_item[0])
            visualized_tags.click_select_tag()

    def execute_QDialogAccept(self):
        """
        Accept (close) a QDialog window
        """

        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            w.accept()

    def execute_QMessageBox_clickYes(self):
        """
        Is supposed to allow to press the Yes button if a pipeline is 
        overwritten in the test_zz_check_modifications method
        """
        w = QApplication.activeWindow()

        if isinstance(w, QMessageBox):
            close_button = w.button(QMessageBox.Yes)
            QTest.mouseClick(close_button, Qt.LeftButton)

    def execute_QDialogClose(self):
        """
        Is supposed to abort( close) a QDialog window
        """
        w = QApplication.activeWindow()

        if isinstance(w, QDialog):
            w.close()
    
    def get_new_test_project(self):
        """
        Copy the test project in a location we can modify safely
        """

        project_path = os.path.join(self.config_path, 'project_8')

        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        config = Config(config_path=self.config_path)
        mia_path = config.get_mia_path()
        project_8_path = os.path.join(mia_path, 'resources', 'mia',
                                      'project_8')
        shutil.copytree(project_8_path, project_path)
        return project_path

    def restart_MIA(self):
        """
        Restarts MIA within a unit test.

        Notes
        -----
        Can be used to restart MIA after changing the controller version in MIA
        preferences.
        """

        self.main_window.close()

        # Removing the opened projects (in CI, the tests are run twice)
        config = Config(config_path=self.config_path)
        config.set_opened_projects([])
        config.saveConfig()
        self.app.exit()

        config = Config(config_path=self.config_path)
        config.set_user_mode(False)
        self.app = QApplication.instance()

        if self.app is None:
            self.app = QApplication(sys.argv)

        self.project = Project(None, True)
        self.main_window = MainWindow(self.project, test=True)

    def setUp(self):
        """
        Called before each test
        """

        # All the tests are run in admin mode
        config = Config(config_path=self.config_path)
        config.set_user_mode(False)

        self.app = QApplication.instance()

        if self.app is None:
            self.app = QApplication(sys.argv)

        self.project = Project(None, True)
        self.main_window = MainWindow(self.project, test=True)

    @classmethod
    def setUpClass(cls):
        """
        Called once at the beginning of the class
        """

        cls.config_path = tempfile.mkdtemp(prefix='mia_tests')
        # hack the Config class to get config_path, because some Config
        # instances are created out of our control in the code
        Config.config_path = cls.config_path

    def tearDown(self):
        """
        Called after each test
        """

        self.main_window.close()

        # Removing the opened projects (in CI, the tests are run twice)
        config = Config(config_path=self.config_path)
        config.set_opened_projects([])
        config.saveConfig()

        self.app.exit()

    @classmethod
    def tearDownClass(cls):
        """
        Called once at the end of the class
        """

        if os.path.exists(cls.config_path):
            shutil.rmtree(cls.config_path)

    def test_add_plug_value_to_database_list_type(self):
        """
        Opens a project, adds a 'Select' process, exports a list type
        input plug and adds it to the database.

        Notes
        -----
        Tests the PipelineManagerTab(QWidget).add_plug_value_to_database().
        """

        # Opens project 8 and switches to it

        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, 'project_9')

        DOCUMENT_1 = self.main_window.project.session.get_documents_names(
                                                                   "current")[0]
        DOCUMENT_2 = self.main_window.project.session.get_documents_names(
                                                                   "current")[1]

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs

        # Adds the processes Select, creates the "select_1" node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Select)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "select_1"
        ppl_edt_tabs.get_current_editor().current_node_name = 'select_1'
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        pipeline_manager = self.main_window.pipeline_manager

        # Initializes the workflow manually
        pipeline_manager.workflow = workflow_from_pipeline(
                                                       pipeline,
                                                       complete_parameters=True)

        # Gets the 'job' and mocks adding a brick to the collection
        job = pipeline_manager.workflow.jobs[0]

        brick_id = str(uuid.uuid4())
        job.uuid = brick_id
        pipeline_manager.brick_list.append(brick_id)

        pipeline_manager.project.session.add_document(COLLECTION_BRICK,
                                                      brick_id)

        # Sets the mandatory plug values corresponding to "inputs" node
        trait_list_inlist = TraitListObject(InputMultiObject(), pipeline,
                                            'inlist', [DOCUMENT_1, DOCUMENT_2])

        # Mocks the creation of a completion engine
        process = job.process()
        plug_name = 'inlist'
        trait = process.trait(plug_name)
        inputs = process.get_inputs()

        # Mocks the attributes dict
        attributes = {
            'not_list': 'not_list_value',
            'small_list': ['list_item1'],
            'large_list': ['list_item1', 'list_item2', 'list_item3']
        }

        # Adds plug value of type 'TraitListObject'
        pipeline_manager.add_plug_value_to_database(trait_list_inlist, brick_id,
                                                    '', 'select_1', plug_name,
                                                    'select_1', job,
                                                    trait, inputs, attributes)

        # Asserts that both 'DOCUMENT_1' and 'DOCUMENT_2' are stored in
        # the database
        pipeline_manager.project.session.get_document(COLLECTION_CURRENT,
                                                      DOCUMENT_1)
        pipeline_manager.project.session.get_document(COLLECTION_CURRENT,
                                                      DOCUMENT_2)
        has_document = pipeline_manager.project.session.has_document
        self.assertTrue(has_document(COLLECTION_CURRENT, DOCUMENT_1))
        self.assertTrue(has_document(COLLECTION_CURRENT, DOCUMENT_2))

    def test_add_plug_value_to_database_non_list_type(self):
        """
        Opens a project, adds a 'Rename' process, exports a non list type
        input plug and adds it to the database.

        Notes
        -----
        Tests the PipelineManagerTab(QWidget).add_plug_value_to_database().
        """

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, 'project_8')

        DOCUMENT_1 = self.main_window.project.session.get_documents_names(
                                                                   "current")[0]

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)

        # Adds the processes Smooth, creates the "rename_1" node
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(Rename)
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "rename_1"
        pipeline_editor_tabs.get_current_editor().current_node_name = 'rename_1'
        (pipeline_editor_tabs.
                     get_current_editor)().export_unconnected_mandatory_inputs()
        (pipeline_editor_tabs.
                          get_current_editor)().export_all_unconnected_outputs()

        old_scan_name = DOCUMENT_1.split('/')[-1]
        new_scan_name = 'new_name.nii'

        # Changes the "_out_file" in the "outputs" node
        pipeline.nodes[''].set_plug_value('_out_file',
                                          DOCUMENT_1.replace(old_scan_name,
                                                             new_scan_name))

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_manager.workflow = workflow_from_pipeline(
                                                       pipeline,
                                                       complete_parameters=True)

        job = pipeline_manager.workflow.jobs[0]

        brick_id = str(uuid.uuid4())
        job.uuid = brick_id
        pipeline_manager.brick_list.append(brick_id)

        pipeline_manager.project.session.add_document(COLLECTION_BRICK,
                                                      brick_id)

        # Sets the mandatory plug values in the "inputs" node
        pipeline.nodes[''].set_plug_value('in_file', DOCUMENT_1)
        pipeline.nodes[''].set_plug_value('format_string', new_scan_name)

        process = job.process()
        plug_name = 'in_file'
        trait = process.trait(plug_name)

        inputs = process.get_inputs()

        attributes = {}
        completion = ProcessCompletionEngine.get_completion_engine(process)

        if completion:
            attributes = completion.get_attribute_values().export_to_dict()

        has_document = pipeline_manager.project.session.has_document

        # Plug value is file location outside project directory
        pipeline_manager.add_plug_value_to_database(DOCUMENT_1, brick_id, '',
                                                    'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)
        pipeline_manager.project.session.get_document(COLLECTION_CURRENT,
                                                      DOCUMENT_1)
        self.assertTrue(has_document(COLLECTION_CURRENT, DOCUMENT_1))
        # Plug values outside the directory are not registered into the
        # database, therefore only plug values inside the project will be used
        # from now on.

        # Plug value is file location inside project directory
        inside_project = os.path.join(pipeline_manager.project.folder,
                                      DOCUMENT_1.split('/')[-1])
        pipeline_manager.add_plug_value_to_database(inside_project, brick_id,
                                                    '', 'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # Plug value that is already in the database
        pipeline_manager.add_plug_value_to_database(inside_project, brick_id,
                                                    '', 'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # Plug value is tag
        tag_value = os.path.join(pipeline_manager.project.folder, 'tag.gz')
        pipeline_manager.add_plug_value_to_database(tag_value, brick_id, '',
                                                    'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # Plug value is .mat
        mat_value = os.path.join(pipeline_manager.project.folder, 'file.mat')
        pipeline_manager.add_plug_value_to_database(mat_value, brick_id, '',
                                                    'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # Plug value is .txt
        txt_value = os.path.join(pipeline_manager.project.folder, 'file.txt')
        pipeline_manager.add_plug_value_to_database(txt_value, brick_id, '',
                                                    'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # 'parent_files' are extracted from the 'inheritance_dict' and
        # 'auto_inheritance_dict' attributes of 'job'. They test cases are
        # listed below:

        # 'parent_files' inside 'auto_inheritance_dict'
        job.auto_inheritance_dict = {inside_project: 'parent_files_value'}
        pipeline_manager.add_plug_value_to_database(inside_project, brick_id,
                                                    '', 'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # 'parent_files' inside 'inheritance_dict'
        job.auto_inheritance_dict = None
        job.inheritance_dict = {inside_project: 'parent_files_value'}
        pipeline_manager.add_plug_value_to_database(inside_project, brick_id,
                                                    '', 'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # 'parent_files' inside 'inheritance_dict', dict type
        job.inheritance_dict = {
            inside_project: {
                'own_tags': [
                    {
                        'name': 'tag_name',
                        'field_type': 'string',
                        'description': 'description_content',
                        'visibility': 'visibility_content',
                        'origin': 'origin_content',
                        'unit': 'unit_content',
                        'value': 'value_content',
                        'default_value': 'default_value_content'
                    }
                ],
                'parent': 'parent_content'
            }
        }
        pipeline_manager.add_plug_value_to_database(inside_project, brick_id,
                                                    '', 'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

        # 'parent_files' inside 'inheritance_dict', output is one of the inputs
        job.inheritance_dict = {
            inside_project: {
                'own_tags': [
                    {
                        'name': 'tag_name',
                        'field_type': 'string',
                        'description': 'description_content',
                        'visibility': 'visibility_content',
                        'origin': 'origin_content',
                        'unit': 'unit_content',
                        'value': 'value_content',
                        'default_value': 'default_value_content'
                    }
                ],
                'parent': 'parent_content',
                'output': inside_project
            }
        }

        pipeline_manager.add_plug_value_to_database(inside_project, brick_id,
                                                    '', 'rename_1', plug_name,
                                                    'rename_1', job, trait,
                                                    inputs, attributes)

    def test_ask_iterated_pipeline_plugs(self):
        '''
        Adds the process 'Rename', export mandatory input and output plug 
        and opens an iteration dialog for each plug.

        Notes
        -----
        Tests the PipelineManagerTab.ask_iterated_pipeline_plugs.
        '''

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs

        # Adds the processes Smooth, creates the "rename_1" node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        pipeline = ppl_edt_tabs.get_current_pipeline()
        pipeline_manager = self.main_window.pipeline_manager

        # Exports the mandatory input and output plugs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = 'rename_1'
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        QTimer.singleShot(1000, self.execute_QDialogAccept)
        pipeline_manager.ask_iterated_pipeline_plugs(pipeline)

    def test_build_iterated_pipeline(self):
        '''
        Adds a 'Select' process, exports its mandatory inputs, mocks 
        some methods of the pipeline manager and builds an iterated 
        pipeline.

        Notes
        -----
        Tests the method 'PipelineManagerTab.build_iterated_pipeline'.
        '''

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        ppl_manager = self.main_window.pipeline_manager

        # Adds the processes Select, creates the "select_1" node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Select)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "select_1"
        ppl_edt_tabs.get_current_editor().current_node_name = 'select_1'
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Mocks 'parent_pipeline' and returns a 'Process' instead of a 
        # 'Pipeline'
        pipeline = pipeline.nodes['select_1'].process
        pipeline.parent_pipeline = True

        ppl_manager.get_pipeline_or_process = MagicMock(return_value=pipeline)

        # Mocks 'ask_iterated_pipeline_plugs' and returns the tuple 
        # '(iterated_plugs, database_plugs)'
        ppl_manager.ask_iterated_pipeline_plugs = MagicMock(
                                      return_value=(['index', 'inlist', '_out'],
                                                    ['inlist']))

        # Mocks 'update_nodes_and_plugs_activation' with no returned values
        pipeline.update_nodes_and_plugs_activation = MagicMock()

        # Builds iterated pipeline
        print('\n\n** an exception message is expected below\n')
        ppl_manager.build_iterated_pipeline()

        # Asserts the mock methods were called as expected
        ppl_manager.get_pipeline_or_process.assert_called_once_with()
        (ppl_manager.ask_iterated_pipeline_plugs.
                                              assert_called_once_with)(pipeline)
        pipeline.update_nodes_and_plugs_activation.assert_called_once_with()
    
    def test_check_requirements(self):
        '''
        Adds a 'Select' process, appends it to the nodes list and checks
        the requirements for the given node.

        Notes
        -----
        Tests PipelineManagerTab.check_requirements.
        '''

        ppl_edt_tabs = self.main_window.pipeline_manager.pipelineEditorTabs
        pipeline_manager = self.main_window.pipeline_manager

        # Adds the processes Select, creates the "select_1" node
        process_class = Select
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(process_class)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Appends a 'Process' to 'pipeline_manager.node_list' and checks
        # requirements
        pipeline_manager.node_list.append(pipeline.nodes['select_1'].process)
        config = pipeline_manager.check_requirements()

        # Asserts the output
        self.assertTrue(isinstance(config, dict))
        self.assertTrue(list(config.keys()) == ['capsul_engine',
                                                'capsul.engine.module.nipype'])

    def test_cleanup_older_init(self):
        """
        Mocks a brick list, mocks some methods from the pipeline manager
        and cleans older inits.

        Notes
        -----
        Tests PipelineManagerTab.cleanup_older_init.
        """

        ppl_manager = self.main_window.pipeline_manager

        # Mocks a 'pipeline_manager.brick_list'
        brick_id = str(uuid.uuid4())
        ppl_manager.brick_list.append(brick_id)

        # Mocks methods used in the test
        (ppl_manager.main_window.data_browser.table_data.
                                                delete_from_brick) = MagicMock()
        ppl_manager.project.cleanup_orphan_nonexisting_files = MagicMock()

        # Cleans up older init
        ppl_manager.cleanup_older_init()

        # Asserts that the mock methods were called as expected
        (ppl_manager.main_window.data_browser.table_data.delete_from_brick.
                                              assert_called_once_with(brick_id))
        (ppl_manager.project.cleanup_orphan_nonexisting_files.
                                                      assert_called_once_with())

        # Asserts that both 'brick_list' and 'node_list' were cleaned
        self.assertTrue(len(ppl_manager.brick_list) == 0)
        self.assertTrue(len(ppl_manager.node_list) == 0)

    def test_complete_pipeline_parameters(self):
        """
        Mocks a method of pipeline manager and completes the pipeline
        parameters.

        Notes
        -----
        Tests PipelineManagerTab.complete_pipeline_parameters.
        """

        ppl_manager = self.main_window.pipeline_manager

        # Mocks method used in the test
        ppl_manager.get_capsul_engine = MagicMock(
                             return_value=ppl_manager.get_pipeline_or_process())

        # Complete pipeline parameters
        ppl_manager.complete_pipeline_parameters()

        # Asserts that the mock method was called as expected
        ppl_manager.get_capsul_engine.assert_called_once_with()

    def test_delete_processes(self):
        """
        Deletes a process and makes the undo/redo action
        """

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)

        # Adding processes
        process_class = Smooth

        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        # Creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        # Creates a node called "smooth_2"
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        # Creates a node called "smooth_3"
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        pipeline = pipeline_editor_tabs.get_current_pipeline()

        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())

        pipeline_editor_tabs.get_current_editor().add_link(
                                                ("smooth_1", "_smoothed_files"),
                                                ("smooth_2", "in_files"),
                                                active=True, weak=False)

        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        pipeline_editor_tabs.get_current_editor().add_link(
                                                ("smooth_2", "_smoothed_files"),
                                                ("smooth_3", "in_files"),
                                                active=True, weak=False)

        self.assertEqual(1,
                         len(pipeline.nodes["smooth_3"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                   "_smoothed_files"].links_to))

        pipeline_editor_tabs.get_current_editor().current_node_name = "smooth_2"
        pipeline_editor_tabs.get_current_editor().del_node()

        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_3"].plugs[
                                                        "in_files"].links_from))

        pipeline_manager.undo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_3"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                   "_smoothed_files"].links_to))

        pipeline_manager.redo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertTrue("smooth_3" in pipeline.nodes.keys())
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_3"].plugs[
                                                        "in_files"].links_from))

    def test_finish_execution(self):
        '''
        Mocks several objects of the pipeline manager and finishes the 
        execution of the pipeline.

        Notes
        -----
        Tests the method PipelineManagerTab.finish_execution.
        '''

        ppl_manager = self.main_window.pipeline_manager

        # Mock objects of 'pipeline_manager' used during the test
        ppl_manager.progress = Mock()
        ppl_manager.progress.worker.status = 'status_value'
        ppl_manager.last_run_pipeline = Mock()
        ppl_manager.last_pipeline_name = 'last_pipeline_name_value'
        ppl_manager._mmovie = Mock()

        # Mock methods of 'ppl_manager' used during the test
        ppl_manager.main_window.statusBar().showMessage = MagicMock()
        ppl_manager.show_pipeline_status_action.setIcon = MagicMock()
        ppl_manager.nodeController.update_parameters = MagicMock()
        ppl_manager.run_pipeline_action.setDisabled = MagicMock()
        ppl_manager.garbage_collect_action.setDisabled = MagicMock()
        ppl_manager.stop_pipeline_action.setEnabled = MagicMock()

        # Connect 'worker' to 'finished_execution' method
        (ppl_manager.progress.worker.finished.
                                          connect(ppl_manager.finish_execution))

        # Finish the execution of the pipeline (no errors are thrown)
        ppl_manager.finish_execution()

        # Asserts that the mocked objects were called as expected
        self.assertEqual('status_value', ppl_manager.last_status)
        self.assertFalse(hasattr(ppl_manager, '_mmovie'))
        self.assertIsNone(ppl_manager.last_run_log)

        # Asserts that the mocked methods were called as expected
        (ppl_manager.stop_pipeline_action.
                                      setEnabled.assert_called_once_with(False))
        (ppl_manager.last_run_pipeline.get_study_config().
                                   engine.raise_for_status.assert_called_once())
        (ppl_manager.main_window.statusBar().showMessage.
                                                       assert_called_once_with)(
                                'Pipeline "{0}" has been correctly run.'.format(
                                                ppl_manager.last_pipeline_name))
        ppl_manager.show_pipeline_status_action.setIcon.assert_called_once()
        ppl_manager.nodeController.update_parameters.assert_called_once_with()
        (ppl_manager.run_pipeline_action.
                                     setDisabled.assert_called_once_with(False))
        (ppl_manager.garbage_collect_action.
                                     setDisabled.assert_called_once_with(False))

        # Mock objects in order to induce a 'RuntimeError' which is 
        # treated by the method
        ppl_manager.progress = Mock()
        ppl_manager.progress.worker.status = swconstants.WORKFLOW_DONE
        delattr(ppl_manager.progress.worker, 'exec_id')
        ppl_manager._mmovie = Mock()

        # Finish the execution of the pipeline with no 'worker.exec_id' 
        # (an error is thrown)
        ppl_manager.finish_execution()

        # Asserts that the execution of the pipeline failed
        self.assertEqual(ppl_manager.last_run_log, 
                         'Execution aborted before running')

    def test_garbage_collect(self):
        '''
        Mocks several objects of the pipeline manager and collects the 
        garbage of the pipeline.

        Notes
        -----
        Tests PipelineManagerTab.test_garbage_collect.
        '''

        ppl_manager = self.main_window.pipeline_manager

        # INTEGRATED TEST

        # Mocks the 'initialized' object
        ppl_manager.pipelineEditorTabs.get_current_editor().initialized = True

        # Collects the garbage
        ppl_manager.garbage_collect()

        # Asserts that the 'initialized' object changed state
        self.assertFalse(ppl_manager.pipelineEditorTabs.get_current_editor().
                                                                    initialized)

        # ISOLATED TEST

        # Mocks again the 'initialized' object
        ppl_manager.pipelineEditorTabs.get_current_editor().initialized = True

        # Mocks the methods used in the test
        ppl_manager.postprocess_pipeline_execution = MagicMock()
        ppl_manager.project.cleanup_orphan_nonexisting_files = MagicMock()
        ppl_manager.project.cleanup_orphan_history = MagicMock()
        (ppl_manager.main_window.data_browser.table_data.
                                                     update_table) = MagicMock()
        ppl_manager.update_user_buttons_states = MagicMock()

        # Collects the garbage
        ppl_manager.garbage_collect()

        # Asserts that the 'initialized' object changed state
        self.assertFalse(ppl_manager.pipelineEditorTabs.get_current_editor().
                                                                    initialized)

        # Assertes that the mocked methods were called as expected
        ppl_manager.postprocess_pipeline_execution.assert_called_once_with()
        (ppl_manager.project.
                     cleanup_orphan_nonexisting_files.assert_called_once_with())
        ppl_manager.project.cleanup_orphan_history.assert_called_once_with()
        (ppl_manager.main_window.data_browser.table_data.
                                         update_table.assert_called_once_with())
        ppl_manager.update_user_buttons_states.assert_called_once_with()

    def test_get_capsul_engine(self):
        """
        Mocks an object in the pipeline manager and gets the capsul engine
        of the pipeline.

        Notes
        -----
        Tests PipelineManagerTab.get_capsul_engine.
        """

        ppl_manager = self.main_window.pipeline_manager

        # INTEGRATED

        # Gets the capsul engine
        capsul_engine = ppl_manager.get_capsul_engine()  # integrated

        # Asserts that the 'capsul_engine' is of class 'CapsulEngine'
        self.assertIsInstance(capsul_engine, CapsulEngine)

        # ISOLATED
        ppl_manager.pipelineEditorTabs.get_capsul_engine = MagicMock()

        # Gets the capsul engine
        _ = ppl_manager.get_capsul_engine()  # isolated

        # Asserts that the mocked method was called as expected
        (ppl_manager.pipelineEditorTabs.
         get_capsul_engine.assert_called_once_with())

    def test_get_missing_mandatory_parameters(self):
        '''
        Adds a process, exports input and output plugs and tries to initialize
        the pipeline with missing mandatory parameters.

        Notes
        -----
        Tests PipelineManagerTab.get_missing_mandatory_parameters.
        '''

        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory inputs and outputs for "rename_1"
        ppl_edt_tabs.get_current_editor().current_node_name = 'rename_1'
        (ppl_edt_tabs.
                     get_current_editor)().export_unconnected_mandatory_inputs()
        (ppl_edt_tabs.get_current_editor)()._export_plug(
                                       temp_plug_name=('rename_1', '_out_file'),
                                       pipeline_parameter='_out_file',
                                       optional=False,
                                       weak_link=False)

        # Initializes the pipeline
        ppl_manager.workflow = workflow_from_pipeline(pipeline,
                                                      complete_parameters=True)
        ppl_manager.update_node_list()

        # Asserts that 2 mandatory parameters are missing
        ppl_manager.update_node_list()
        missing_inputs = ppl_manager.get_missing_mandatory_parameters()
        self.assertEqual(len(missing_inputs), 2)
        self.assertEqual(missing_inputs[0], 'Pipeline.rename_1.format_string')
        self.assertEqual(missing_inputs[1], 'Pipeline.rename_1.in_file')

        # Empties the jobs list
        ppl_manager.workflow.jobs = []

        # Asserts that 2 mandatory parameters are still missing
        missing_inputs = ppl_manager.get_missing_mandatory_parameters()
        self.assertEqual(len(missing_inputs), 2)
        self.assertEqual(missing_inputs[0], 'Pipeline.rename_1.format_string')
        self.assertEqual(missing_inputs[1], 'Pipeline.rename_1.in_file')

    def test_get_pipeline_or_process(self):
        """
        Adds a process and gets a pipeline and a process from the pipeline
        manager.

        Notes
        -----
        Tests PipelineManagerTab.get_pipeline_or_process.
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
        '''
        Adds Select process, exports its plugs, mocks objects from the 
        pipeline manager and initializes the workflow.

        Notes
        -----
        Tests the PipelineManagerTab.initialize.
        '''

        # Gets the paths of 2 documents
        config = Config(config_path=self.config_path)
        folder = os.path.abspath(os.path.join(config.get_mia_path(),
                                              'resources', 'mia', 'project_8',
                                              'data', 'raw_data'))
        
        NII_FILE_1 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_'
                      'Guerbet_MDEFT-MDEFTpvm-000940_800.nii')

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        
        # Adds the process 'Select' as the node 'select_1'
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)
        pipeline = ppl_edt_tabs.get_current_pipeline()

        # Exports the mandatory inputs and outputs for 'select_1'
        ppl_edt_tabs.get_current_editor().current_node_name = 'rename_1'
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        # Sets mandatory parameters 'select_1'
        pipeline.nodes[''].set_plug_value('in_file', DOCUMENT_1)
        pipeline.nodes[''].set_plug_value('format_string', 'new_name.nii')

        # Checks that there is no workflowindex
        self.assertIsNone(ppl_manager.workflow)

        # Mocks objects
        ppl_manager.init_clicked = True
        ppl_manager.ignore_node = True
        ppl_manager.key = {'item': 'item_value'}
        ppl_manager.ignore = {'item': 'item_value'}

        # Mocks methods
        ppl_manager.init_pipeline = Mock()
        # FIXME: if the method 'init_pipeline' is not mocked the whole
        #        test routine fails with a 'Segmentation Fault'

        # Initializes the pipeline
        ppl_manager.initialize()

        # Asserts that a workflow has been created
        #self.assertIsNotNone(ppl_manager.workflow)
        #from soma_workflow.client_types import Workflow
        #self.assertIsInstance(ppl_manager.workflow, Workflow)
        # FiXME: the above code else leads to 'Segmentation Fault'

        self.assertFalse(ppl_manager.ignore_node)
        self.assertEqual(len(ppl_manager.key), 0)
        self.assertEqual(len(ppl_manager.ignore), 0)
        ppl_manager.init_pipeline.assert_called_once_with()

        # Mocks an object to induce an exception
        ppl_manager.init_pipeline = None

        # Induces an exception in the pipeline initialization
        print('\n\n** an exception message is expected below')
        ppl_manager.initialize()

        self.assertFalse(ppl_manager.ignore_node)

    def test_register_node_io_in_database(self):
        '''
        Adds a process, sets input and output parameters and registers them
        in database.

        Notes
        -----
        Tests PipelineManagerTab._register_node_io_in_database.
        '''

        # Opens project 8 and switches to it
        project_8_path = self.get_new_test_project()
        self.main_window.switch_project(project_8_path, 'project_9')

        DOCUMENT_1 = (self.main_window.project.session.
                      get_documents_names)("current")[0]

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                pipelineEditorTabs)

        # Adds the processes Smooth, creates the "rename_1" node
        process_class = Rename
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exports the mandatory input and output plugs for "rename_1"
        pipeline_editor_tabs.get_current_editor().current_node_name = 'rename_1'
        (pipeline_editor_tabs.
                     get_current_editor)().export_unconnected_mandatory_inputs()
        (pipeline_editor_tabs.
                          get_current_editor)().export_all_unconnected_outputs()

        old_scan_name = DOCUMENT_1.split('/')[-1]
        new_scan_name = 'new_name.nii'

        # Sets the mandatory plug values in the "inputs" node
        pipeline.nodes[''].set_plug_value('in_file', DOCUMENT_1)
        pipeline.nodes[''].set_plug_value('format_string', new_scan_name)

        # Changes the "_out_file" in the "outputs" node
        pipeline.nodes[''].set_plug_value('_out_file',
                                          DOCUMENT_1.replace(old_scan_name,
                                                             new_scan_name))

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_manager.workflow = workflow_from_pipeline(
                                                       pipeline,
                                                       complete_parameters=True)

        job = pipeline_manager.workflow.jobs[0]

        brick_id = str(uuid.uuid4())
        job.uuid = brick_id
        pipeline_manager.brick_list.append(brick_id)

        pipeline_manager.project.session.add_document(COLLECTION_BRICK,
                                                      brick_id)

        pipeline_manager._register_node_io_in_database(job, job.process())

        # Simulates a 'ProcessNode()' as 'process'
        process_node = ProcessNode(pipeline, '', job.process())
        pipeline_manager._register_node_io_in_database(job, process_node)

        # Simulates a 'PipelineNode()' as 'process'
        pipeline_node = PipelineNode(pipeline, '', job.process())
        pipeline_manager._register_node_io_in_database(job, pipeline_node)

        # Simulates a 'Switch()' as 'process'
        switch = Switch(pipeline, '', [''], [''])
        switch.completion_engine = None
        pipeline_manager._register_node_io_in_database(job, switch)

        # Simulates a list of outputs in 'process'
        job.process().list_outputs = []
        job.process().outputs = []
        pipeline_manager._register_node_io_in_database(job, job.process())

    def test_register_completion_attributes(self):
        '''
        Mocks methods of the pipeline manager and registers completion 
        attributes.

        Notes
        ------
        Tests PipelineManagerTab.register_completion_attributes.
        Since a method of the ProcessCompletionEngine class is mocked, 
        this test may render the upcoming testing routine instable.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Gets the path of one document
        config = Config(config_path=self.config_path)
        folder = os.path.abspath(os.path.join(config.get_mia_path(),
                                              'resources', 'mia', 'project_8',
                                              'data', 'raw_data'))

        NII_FILE_1 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_'
                      'Guerbet_Anat-RAREpvm-000220_000.nii')
        NII_FILE_2 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_'
                      'Guerbet_MDEFT-MDEFTpvm-000940_800.nii')

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        DOCUMENT_2 = os.path.abspath(os.path.join(folder, NII_FILE_2))

        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Select)

        # Export plugs and sets their values
        print('\n\n** an exception message is expected below\n')
        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()
        ppl.nodes[''].set_plug_value('inlist', [DOCUMENT_1, DOCUMENT_2])
        proj_dir = (os.path.join(os.path.abspath(os.path.normpath(
                                                   ppl_manager.project.folder)),
                                 ''))
        output_dir = os.path.join(proj_dir, 'output_file.nii')
        ppl.nodes[''].set_plug_value('_out', output_dir)

        # Register completion without 'attributes'
        ppl_manager.register_completion_attributes(ppl)

        # Mocks 'get_capsul_engine' for the method not to throw an error
        # with the insertion of the upcoming mock
        capsul_engine = ppl_edt_tabs.get_capsul_engine()
        ppl_manager.get_capsul_engine = Mock(return_value=capsul_engine)

        # Mocks attributes values that are in the tags list
        attributes = {'Checksum':'Checksum_value'}
        (ProcessCompletionEngine.get_completion_engine(ppl).
                                  get_attribute_values)().export_to_dict = Mock(
                                                      return_value=attributes)

        # Register completion with mocked 'attributes'
        ppl_manager.register_completion_attributes(ppl)

    def test_remove_progress(self):
        """
        Mocks an object of the pipeline manager and removes its progress.

        Notes
        -----
        Tests the method PipelineManagerTab.remove_progress.
        """

        pipeline_manager = self.main_window.pipeline_manager

        # Mocks the 'progress' object
        pipeline_manager.progress = Mock()

        # Removes progress
        pipeline_manager.remove_progress()

        # Asserts that the object 'progress' was deleted
        self.assertFalse(hasattr(pipeline_manager, 'progress'))

    def test_savePipeline(self):
        '''
        Mocks methods of the pipeline manager and tries to save the 
        pipeline over several conditions.

        Notes
        -----
        Tests PipelineManagerTab.savePipeline.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        config = Config(config_path=self.config_path)
        ppl_path = os.path.join(config.get_mia_path(), 'processes',
                                'User_processes', 'test_pipeline_1.py')

        ppl_edt_tabs.get_current_editor()._pipeline_filename = ppl_path

        # Mocks methods
        #ppl_manager.main_window.statusBar().showMessage = Mock()

        # Save pipeline as with empty filename, checked
        ppl_manager.savePipeline(uncheck=True)

        # Mocks 'savePipeline' from 'ppl_edt_tabs'
        ppl_edt_tabs.save_pipeline = Mock(return_value='not_empty')

        # Saves pipeline as with empty filename, checked
        ppl_manager.savePipeline(uncheck=True)

        # Sets the path to save the pipeline
        ppl_edt_tabs.get_current_editor()._pipeline_filename = ppl_path

        # Saves pipeline as with filled filename, uncheck
        ppl_manager.savePipeline(uncheck=True)

        # Aborts pipeline saving with filled filename
        QTimer.singleShot(1000, self.execute_QDialogClose)
        ppl_manager.savePipeline()
        
        # Accept pipeline saving with filled filename
        QTimer.singleShot(1000, self.execute_QMessageBox_clickYes)
        ppl_manager.savePipeline()
    
    def test_savePipelineAs(self):
        '''
        Mocks a method from pipeline manager and saves a pipeline under
        another name.

        Notes
        -----
        Tests PipelineManagerTab.savePipelineAs.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs

        # Saves pipeline with empty filename
        ppl_manager.savePipelineAs()

        # Mocks 'savePipeline' from 'ppl_edt_tabs'
        ppl_edt_tabs.save_pipeline = Mock(return_value='not_empty')

        # Saves pipeline with not empty filename
        ppl_manager.savePipelineAs()

    def test_set_anim_frame(self):
      """
      Runs the 'rotatingBrainVISA.gif' animation.
      """

      pipeline_manager = self.main_window.pipeline_manager
      
      config = Config()
      sources_images_dir = config.getSourceImageDir()
      self.assertTrue(sources_images_dir)  # if the string is not empty

      pipeline_manager._mmovie = QtGui.QMovie(os.path.join(
                                                       sources_images_dir,
                                                       'rotatingBrainVISA.gif'))
      pipeline_manager._set_anim_frame()

    def test_show_status(self):
        '''
        Shows the status window of the pipeline manager.
        Tests PipelineManagerTab.test_show_status.        
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager

        ppl_manager.show_status()

        # Asserts that the status windows was created
        self.assertTrue(hasattr(ppl_manager, 'status_widget'))

    def test_stop_execution(self):
        '''
        Shows the status window of the pipeline manager.
        Tests PipelineManagerTab.test_show_status.        
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager

        # Creates a 'RunProgress' object
        ppl_manager.progress = RunProgress(ppl_manager)

        ppl_manager.stop_execution()

        self.assertTrue(ppl_manager.progress.worker.interrupt_request)

    def test_undo_redo(self):
        """
        Tests the undo/redo actions
        """

        pipeline_manager = self.main_window.pipeline_manager
        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                pipelineEditorTabs)

        # Add a process => creates a node called "smooth_1",
        # test if Smooth_1 is a node in the current pipeline / editor
        process_class = Smooth
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        pipeline = pipeline_editor_tabs.get_current_pipeline()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        # Undo (remove the node), test if the node was removed
        pipeline_manager.undo()
        self.assertFalse("smooth_1" in pipeline.nodes.keys())

        # Redo (add again the node), test if the node was added
        pipeline_manager.redo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        # Delete the node, test if the node was removed
        pipeline_editor_tabs.get_current_editor().current_node_name = "smooth_1"
        pipeline_editor_tabs.get_current_editor().del_node()
        self.assertFalse("smooth_1" in pipeline.nodes.keys())

        # Undo (add again the node), test if the node was added
        pipeline_manager.undo()
        self.assertTrue("smooth_1" in pipeline.nodes.keys())

        # Redo (delete again the node), test if the node was removed
        pipeline_manager.redo()
        self.assertFalse("smooth1" in pipeline.nodes.keys())

        # Adding a new process => creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)

        # Creates a node called "smooth_1"
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        # Export the "out_prefix" plug,
        # test if the Input node have a prefix_smooth plug
        pipeline_editor_tabs.get_current_editor()._export_plug(
                                      temp_plug_name=("smooth_1", "out_prefix"),
                                      pipeline_parameter="prefix_smooth",
                                      optional=False,
                                      weak_link=False)
        self.assertTrue("prefix_smooth" in pipeline.nodes[''].plugs.keys())

        # Undo (remove prefix_smooth from Input node),
        # test if the prefix_smooth plug was deleted from Input node
        pipeline_manager.undo()
        self.assertFalse("prefix_smooth" in pipeline.nodes[''].plugs.keys())

        # redo (export again the "out_prefix" plug),
        # test if the Input node have a prefix_smooth plug
        pipeline_manager.redo()
        self.assertTrue("prefix_smooth" in pipeline.nodes[''].plugs.keys())

        # Delete the "prefix_smooth" plug from the Input node,
        # test if the Input node have not a prefix_smooth plug
        pipeline_editor_tabs.get_current_editor()._remove_plug(
                                    _temp_plug_name=("inputs", "prefix_smooth"))
        self.assertFalse("prefix_smooth" in pipeline.nodes[''].plugs.keys())

        # Undo (export again the "out_prefix" plug),
        # test if the Input node have a prefix_smooth plug
        pipeline_manager.undo()
        self.assertTrue("prefix_smooth" in pipeline.nodes[''].plugs.keys())

        # redo (deleting the "prefix_smooth" plug from the Input node),
        # test if the Input node have not a prefix_smooth plug
        pipeline_manager.redo()
        self.assertFalse("prefix_smooth" in pipeline.nodes[''].plugs.keys())

        # FIXME: export_plugs (currently there is a bug if a plug is
        #        of type list)

        # Adding a new process => creates a node called "smooth_2"
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 550)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)

        # Adding a link
        pipeline_editor_tabs.get_current_editor().add_link(
                                                ("smooth_1", "_smoothed_files"),
                                                ("smooth_2", "in_files"),
                                                active=True, weak=False)

        # test if the 2 nodes have the good links
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Undo (remove the link), test if the 2 nodes have not the links
        pipeline_manager.undo()
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Redo (add again the link), test if the 2 nodes have the good links
        pipeline_manager.redo()
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Removing the link, test if the 2 nodes have not the links
        link = "smooth_1._smoothed_files->smooth_2.in_files"
        pipeline_editor_tabs.get_current_editor()._del_link(link)
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Undo (add again the link), test if the 2 nodes have the good links
        pipeline_manager.undo()
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Redo (remove the link), test if the 2 nodes have not the links
        pipeline_manager.redo()
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(0,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Re-adding a link
        pipeline_editor_tabs.get_current_editor().add_link(
                                                ("smooth_1", "_smoothed_files"),
                                                ("smooth_2", "in_files"),
                                                active=True, weak=False)

        # Updating the node name
        process = pipeline.nodes['smooth_2'].process
        pipeline_manager.displayNodeParameters("smooth_2", process)
        node_controller = self.main_window.pipeline_manager.nodeController
        node_controller.display_parameters("smooth_2", process, pipeline)
        node_controller.line_edit_node_name.setText("my_smooth")
        keyEvent = QtGui.QKeyEvent(QEvent.KeyPress, Qt.Key_Return,
                                   Qt.NoModifier)
        QCoreApplication.postEvent(node_controller.line_edit_node_name,
                                   keyEvent)
        QTest.qWait(100)

        # test if the smooth_2 node has been replaced by the
        # my_smooth node and test the links
        self.assertTrue("my_smooth" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertEqual(1,
                         len(pipeline.nodes["my_smooth"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Undo (Updating the node name from my_smooth to smooth_2),
        # test if it's ok
        pipeline_manager.undo()
        QTest.qWait(100)
        self.assertFalse("my_smooth" in pipeline.nodes.keys())
        self.assertTrue("smooth_2" in pipeline.nodes.keys())
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_2"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Redo (Updating the node name from smooth_2 to my_smooth),
        # test if it's ok
        pipeline_manager.redo()
        QTest.qWait(100)
        self.assertTrue("my_smooth" in pipeline.nodes.keys())
        self.assertFalse("smooth_2" in pipeline.nodes.keys())
        self.assertEqual(1,
                         len(pipeline.nodes["my_smooth"].plugs[
                                                        "in_files"].links_from))
        self.assertEqual(1,
                         len(pipeline.nodes["smooth_1"].plugs[
                                                   "_smoothed_files"].links_to))

        # Updating a plug value
        if hasattr(node_controller, 'get_index_from_plug_name'):
            index = node_controller.get_index_from_plug_name("out_prefix",
                                                             "in")
            node_controller.line_edit_input[index].setText("PREFIX")
            node_controller.update_plug_value("in", "out_prefix",
                                              pipeline, str)

            self.assertEqual("PREFIX",
                             pipeline.nodes["my_smooth"].get_plug_value(
                                                                  "out_prefix"))

            pipeline_manager.undo()
            self.assertEqual("s",
                             pipeline.nodes["my_smooth"].get_plug_value(
                                                                  "out_prefix"))

            pipeline_manager.redo()
            self.assertEqual("PREFIX",
                             pipeline.nodes["my_smooth"].get_plug_value(
                                                                  "out_prefix"))

    def test_update_auto_inheritance(self):
        '''
        Tests PipelineManagerTab.update_auto_inheritance.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        config = Config(config_path=self.config_path)
        folder = os.path.abspath(os.path.join(config.get_mia_path(),
                                              'resources', 'mia', 'project_8',
                                              'data', 'raw_data'))

        NII_FILE_1 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_'
                      'Guerbet_Anat-RAREpvm-000220_000.nii')
        NII_FILE_2 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-04-G3_'
                      'Guerbet_MDEFT-MDEFTpvm-000940_800.nii')

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        DOCUMENT_2 = os.path.abspath(os.path.join(folder, NII_FILE_2))

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()
        
        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Select)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        print('\n\n** an exception message is expected below\n')
        ppl.nodes['select_1'].set_plug_value('inlist', [DOCUMENT_1,DOCUMENT_2])
        node = ppl.nodes['select_1']

        # Initializes the workflow manually
        ppl_manager.workflow = workflow_from_pipeline(ppl,
                                                      complete_parameters=True)

        job = ppl_manager.workflow.jobs[0]

        # Mocks the node's parameters
        node.auto_inheritance_dict = {}
        process = node.process
        process.study_config.project = Mock()
        process.study_config.project.folder = config.get_mia_path()
        process.outputs = []
        process.list_outputs = []
        process.auto_inheritance_dict = {}

        # 'job.param_dict' as single object
        job.param_dict['_out'] = '_out_value'
        ppl_manager.update_auto_inheritance(job, node)

        # 'job.param_dict' as list of objects
        job.param_dict['inlist'] = [DOCUMENT_1, DOCUMENT_2]
        process.get_outputs = Mock(return_value={'_out': ['_out_value']})
        job.param_dict['_out'] = ['_out_value']
        ppl_manager.update_auto_inheritance(job, node)

        # 'node' does not have a 'project'
        del node.process.study_config.project
        ppl_manager.update_auto_inheritance(job, node)

        # 'node.process' is not a process
        #node.process = {}
        #ppl_manager.update_auto_inheritance(job, node)

        # 'node' is not a 'Process'
        node = {}
        ppl_manager.update_auto_inheritance(job, node)

    def test_update_inheritance(self):
        '''
        Adds a process and updates the job's inheritance dict.
        Tests PipelineManagerTab.update_inheritance.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()
        
        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()

        node = ppl.nodes['rename_1']

        # Initializes the workflow manually
        ppl_manager.workflow = workflow_from_pipeline(ppl,
                                                      complete_parameters=True)

        # Gets the 'job' and mocks adding a brick to the collection
        job = ppl_manager.workflow.jobs[0]

        # Node's name does not contains 'Pipeline'
        node.context_name = ''
        node.process.inheritance_dict = {'item': 'value'}
        ppl_manager.project.node_inheritance_history = {}
        ppl_manager.update_inheritance(job, node)
        
        self.assertEqual(job.inheritance_dict, {'item': 'value'})

        # Node's name contains 'Pipeline'
        node.context_name = 'Pipeline.rename_1'
        ppl_manager.update_inheritance(job, node)

        self.assertEqual(job.inheritance_dict, {'item': 'value'})

        # Node's name in 'node_inheritance_history'
        (ppl_manager.project
         .node_inheritance_history['rename_1']) = [{0: 'new_value'}]
        ppl_manager.update_inheritance(job, node)

        self.assertEqual(job.inheritance_dict, {0: 'new_value'})

    def test_update_node_list(self):
        """
        Adds a process, exports input and output plugs, initializes a workflow
        and adds the process to the "pipline_manager.node_list".

        Notes
        -----
        Tests the PipelineManagerTab.update_node_list.
        """

        pipeline_editor_tabs = (self.main_window.pipeline_manager.
                                                             pipelineEditorTabs)
        pipeline_manager = self.main_window.pipeline_manager

        process_class = Rename
        pipeline_editor_tabs.get_current_editor().click_pos = QPoint(450, 500)
        pipeline_editor_tabs.get_current_editor().add_named_process(
                                                                  process_class)
        pipeline = pipeline_editor_tabs.get_current_pipeline()

        # Exports the mandatory inputs and outputs for "rename_1"
        pipeline_editor_tabs.get_current_editor().current_node_name = 'rename_1'
        (pipeline_editor_tabs.
                     get_current_editor)().export_unconnected_mandatory_inputs()
        (pipeline_editor_tabs.
                          get_current_editor)().export_all_unconnected_outputs()

        # Initializes the workflow
        pipeline_manager.workflow = workflow_from_pipeline(
                                                       pipeline,
                                                       complete_parameters=True)

        # Asserts that the "node_list" is empty by default
        node_list = self.main_window.pipeline_manager.node_list
        self.assertEqual(len(node_list), 0)

        # Asserts that the process "Rename" was added to "node_list"
        pipeline_manager.update_node_list()
        self.assertEqual(len(node_list), 1)
        self.assertEqual(node_list[0]._nipype_class, 'Rename')

    def test_z_init_pipeline(self):
        '''
        Adds a process, mocks several parameters from the pipeline
        manager and initializes the pipeline.

        Notes
        -----
        Tests PipelineManagerTab.init_pipeline.
        The 'z' prefix places this test at the end of the alphabetically
        organized routine. This prevents the 'Segmentation Fault' error 
        to be thrown during the test.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Gets the path of one document
        config = Config(config_path=self.config_path)
        folder = os.path.abspath(os.path.join(config.get_mia_path(),
                                              'resources', 'mia', 'project_8',
                                              'data', 'raw_data'))

        NII_FILE_1 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_'
                      'Guerbet_Anat-RAREpvm-000220_000.nii')

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        
        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()
        
        # Verifies that all the processes were added
        self.assertEqual(['', 'rename_1'], ppl.nodes.keys())
        
        # Initialize the pipeline with missing mandatory parameters
        ppl_manager.workflow = workflow_from_pipeline(ppl,
                                                      complete_parameters=True)
        
        ppl_manager.update_node_list()
        QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)
        
        # Sets the mandatory parameters
        ppl.nodes[''].set_plug_value('in_file', DOCUMENT_1)
        ppl.nodes[''].set_plug_value('format_string', 'new_name.nii')

        # Mocks an iteration pipeline
        ppl.name = 'Iteration_pipeline'
        process_it = ProcessIteration(ppl.nodes['rename_1'].process, '')
        ppl.list_process_in_pipeline.append(process_it)

        # Initialize the pipeline with mandatory parameters set
        QTimer.singleShot(1000, self.execute_QDialogAccept)
        #init_result = ppl_manager.init_pipeline(pipeline=ppl)

        # Mocks null requirements and initializes the pipeline
        ppl_manager.check_requirements = Mock(return_value=None)
        QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)
        ppl_manager.check_requirements.assert_called_once_with('global', 
                                                               message_list=[])

        # Mocks external packages as requirements and initializes the 
        # pipeline
        pkgs = ['fsl', 'afni', 'ants', 'matlab', 'spm']
        req = {'capsul_engine':{'uses': Mock()}}

        for pkg in pkgs:                
            req['capsul.engine.module.{}'.format(pkg)] = {'directory': False}

        req['capsul_engine']['uses'].get = Mock(return_value=1)
        ppl_manager.check_requirements = Mock(return_value=req)

        QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        # Extra steps for SPM
        req['capsul.engine.module.spm']['directory'] = True
        req['capsul.engine.module.spm']['standalone'] = True
        Config().set_matlab_standalone_path(None)

        QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        req['capsul.engine.module.spm']['standalone'] = False

        QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        # Deletes an attribute of each package requirement
        for pkg in pkgs:
            del req['capsul.engine.module.{}'.format(pkg)]

        QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        # Mocks a 'ValueError' in 'workflow_from_pipeline'
        ppl.find_empty_parameters = Mock(side_effect=ValueError)

        QTimer.singleShot(1000, self.execute_QDialogAccept)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)
    
    @unittest.skip
    def test_z_init_pipeline_2(self):
        '''
        Adds a process, mocks several parameters from the pipeline
        manager and initializes the pipeline.

        Notes
        -----
        Tests PipelineManagerTab.init_pipeline.
        The 'z' prefix places this test at the end of the alphabetically
        organized routine. This prevents the 'Segmentation Fault' error 
        to be thrown during the test.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Gets the path of one document
        config = Config(config_path=self.config_path)
        folder = os.path.abspath(os.path.join(config.get_mia_path(),
                                              'resources', 'mia', 'project_8',
                                              'data', 'raw_data'))

        NII_FILE_1 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_'
                      'Guerbet_Anat-RAREpvm-000220_000.nii')

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        
        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()
        
        # Verifies that all the processes were added
        self.assertEqual(['', 'rename_1'], ppl.nodes.keys())
        
        # Initialize the pipeline with missing mandatory parameters
        ppl_manager.workflow = workflow_from_pipeline(ppl,
                                                      complete_parameters=True)
        
        ppl_manager.update_node_list()
        init_result = ppl_manager.init_pipeline()
        #self.assertFalse(init_result)
        
        # Sets the mandatory parameters
        ppl.nodes[''].set_plug_value('in_file', DOCUMENT_1)
        ppl.nodes[''].set_plug_value('format_string', 'new_name.nii')

        # Mocks an iteration pipeline
        ppl.name = 'Iteration_pipeline'
        process_it = ProcessIteration(ppl.nodes['rename_1'].process, '')
        ppl.list_process_in_pipeline.append(process_it)

        # Initialize the pipeline with mandatory parameters set
        init_result = ppl_manager.init_pipeline(pipeline=ppl)

        # Mocks null requirements and initializes the pipeline
        ppl_manager.check_requirements = Mock(return_value=None)
        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)
        ppl_manager.check_requirements.assert_called_once_with('global', 
                                                               message_list=[])

        # Mocks external packages as requirements and initializes the 
        # pipeline
        pkgs = ['fsl', 'afni', 'ants', 'matlab', 'spm']
        req = {'capsul_engine': {'uses': Mock()}}

        for pkg in pkgs:                
            req['capsul.engine.module.{}'.format(pkg)] = {'directory': False}

        req['capsul_engine']['uses'].get = Mock(return_value=1)
        ppl_manager.check_requirements = Mock(return_value=req)

        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        # Extra steps for SPM
        req['capsul.engine.module.spm']['directory'] = True
        req['capsul.engine.module.spm']['standalone'] = True
        Config().set_matlab_standalone_path(None)

        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        req['capsul.engine.module.spm']['standalone'] = False

        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        # Deletes an attribute of each package requirement
        for pkg in pkgs:
            del req['capsul.engine.module.{}'.format(pkg)]

        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

        # Mocks a 'ValueError' in 'workflow_from_pipeline'
        ppl.find_empty_parameters = Mock(side_effect=ValueError)

        init_result = ppl_manager.init_pipeline()
        self.assertFalse(init_result)

    def test_z_runPipeline(self):
        '''
        Adds a process, export plugs and runs a pipeline.

        Notes
        -----
        Tests PipelineManagerTab.runPipeline.
        '''

        # Sets shortcuts for objects that are often used
        ppl_manager = self.main_window.pipeline_manager
        ppl_edt_tabs = ppl_manager.pipelineEditorTabs
        ppl = ppl_edt_tabs.get_current_pipeline()

        # Gets the path of one document
        config = Config(config_path=self.config_path)
        folder = os.path.abspath(os.path.join(config.get_mia_path(),
                                              'resources', 'mia', 'project_8',
                                              'data', 'raw_data'))

        NII_FILE_1 = ('Guerbet-C6-2014-Rat-K52-Tube27-2014-02-14102317-01-G1_'
                      'Guerbet_Anat-RAREpvm-000220_000.nii')

        DOCUMENT_1 = os.path.abspath(os.path.join(folder, NII_FILE_1))
        
        # Adds a Rename processes, creates the 'rename_1' node
        ppl_edt_tabs.get_current_editor().click_pos = QPoint(450, 500)
        ppl_edt_tabs.get_current_editor().add_named_process(Rename)

        ppl_edt_tabs.get_current_editor().export_unconnected_mandatory_inputs()
        ppl_edt_tabs.get_current_editor().export_all_unconnected_outputs()
        
        # Sets the mandatory parameters
        ppl.nodes[''].set_plug_value('in_file', DOCUMENT_1)
        ppl.nodes[''].set_plug_value('format_string', 'new_name.nii')

        # Mocks 'initialize' in order to avoid 'Segmentation Fault'
        #ppl_manager.test_init = True
        #ppl_manager.initialize = Mock()

        # Runs the pipeline assuring that the it will be initialized
        ppl_manager.runPipeline()

        # Asserts that the pipeline has run
        #ppl_manager.initialize.assert_called_once_with()
        self.assertEqual(len(ppl_manager.brick_list), 0)
        self.assertEqual(ppl_manager.last_run_pipeline, ppl)
        self.assertTrue(hasattr(ppl_manager, '_mmovie'))

    def test_zz_del_pack(self):
        """ We remove the brick created during the unit tests, and we take
        advantage of this to cover the part of the code used to remove the
        packages """

        pkg = PackageLibraryDialog(self.main_window)
        # The Test_pipeline brick was added in the package library
        self.assertTrue("Test_pipeline_1" in
                        pkg.package_library.package_tree['User_processes'])

        pkg.delete_package(to_delete="User_processes.Test_pipeline_1", loop=True)

        # The Test_pipeline brick has been removed from the package library
        self.assertFalse("Test_pipeline_1" in
                         pkg.package_library.package_tree['User_processes'])


if __name__ == '__main__':
    unittest.main()
