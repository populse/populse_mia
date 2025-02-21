"""Module to define main window appearance, functions and settings.

Initialize the software appearance and defines interactions with the user.

:Contains:
    :Class:
        - MainWindow
        - _ProcDeleter

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import glob
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from os.path import expanduser

import yaml
from packaging import version
from PyQt5.QtCore import QCoreApplication, Qt

# PyQt5 imports
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import populse_mia.data_manager.data_loader as data_loader
from populse_mia.data_manager import (
    CLINICAL_TAGS,
    COLLECTION_CURRENT,
    TAG_HISTORY,
)
from populse_mia.data_manager.project import Project

# Populse_MIA imports
from populse_mia.data_manager.project_properties import SavedProjects
from populse_mia.software_properties import Config
from populse_mia.user_interface.data_browser.data_browser import DataBrowser
from populse_mia.user_interface.data_viewer.data_viewer_tab import (
    DataViewerTab,
)
from populse_mia.user_interface.pipeline_manager.pipeline_manager_tab import (
    PipelineManagerTab,
)
from populse_mia.user_interface.pipeline_manager.process_library import (
    InstallProcesses,
    PackageLibraryDialog,
)
from populse_mia.user_interface.pop_ups import (
    PopUpDeletedProject,
    PopUpDeleteProject,
    PopUpNewProject,
    PopUpOpenProject,
    PopUpPreferences,
    PopUpProperties,
    PopUpQuit,
    PopUpSaveProjectAs,
    PopUpSeeAllProjects,
)

console_shell_running = False
_ipsubprocs_lock = threading.RLock()
_ipsubprocs = []

logger = logging.getLogger(__name__)


class _ProcDeleter(threading.Thread):
    """
    A helper class to manage the lifecycle of a subprocess.

    This class is used internally by `MainWindow.open_shell()` to handle
    subprocesses in a thread-safe manner. It ensures proper cleanup of the
    subprocess when it is no longer needed and updates global state
    variables as required.

    :attr o (subprocess.Popen): The subprocess object to manage.
    :attr console (bool): Indicates if the subprocess is associated with
                          a console.

    :methods:
        __del__(): Ensures the subprocess is terminated and updates global
                   state variables related to the subprocess.
        run(): Waits for the subprocess to complete and cleans up global
               references to it.
    """

    def __init__(self, o, console=False):
        """
        Initializes the _ProcDeleter thread with the given subprocess.

        :param o (subprocess.Popen): The subprocess object to be managed by
                                     this thread.
        :param console (bool): Indicates if the subprocess is associated
                               with a console.
        """
        super().__init__()
        self.o = o
        self.console = console

    def __del__(self):
        """
        Ensures proper cleanup when the _ProcDeleter instance is deleted.

        This method attempts to terminate the managed subprocess (`o`).
        If the subprocess is associated with a console, it also updates
        the global `console_shell_running` variable to indicate that the
        console is no longer active.
        """

        try:
            self.o.kill()

        except Exception as e:
            logger.warning(f"Failed to kill subprocess: {e}")

        if self.console:
            global console_shell_running
            console_shell_running = False

    def run(self):
        """
        Runs the thread to wait for the subprocess to finish.

        This method waits for the subprocess to terminate by calling
        `communicate` on the managed subprocess object. It then removes
        itself from the global list `_ipsubprocs` in a thread-safe manner.
        """

        try:
            self.o.communicate()

        except Exception as e:
            logger.warning(f"Exception in subprocess communication: {e}")

        global _ipsubprocs

        with _ipsubprocs_lock:

            try:
                _ipsubprocs.remove(self)

            except ValueError:
                logger.warning(
                    "Attempted to remove a non-existent "
                    "subprocess from _ipsubprocs."
                )


class MainWindow(QMainWindow):
    """Initialize software appearance and define interactions with the user.

    .. Methods:
        - __init__ : Initialise the object MainWindow
        - add_clinical_tags: Add the clinical tags to the database and the
                             data browser
        - check_database: Check if files in database have been modified or
                          removed since they have been converted for the
                          first time
        - check_unsaved_modifications: Check if there are differences between
                                       the current project and the database

        - closeEvent: Override the closing event to check if there are
                      unsaved modifications
        - create_project_pop_up: Create a new project
        - create_view_actions: Create the actions in each menu
        - create_view_menus: Create the menu-bar
        - create_view_window: Create the main window view
        - create_tabs: Create the tabs
        - credits: Open the credits in a web browser
        - del_clinical_tags: Remove the clinical tags to the database and the
                             data browser
        - delete_project: Open a project and updates the recent projects list
        - documentation: Open the documentation in a web browser
        - get_controller_version: Returns controller_version_changed attribute
        - import_data: Call the import software (MRI File Manager)
        - install_processes_pop_up: Open the install processes pop-up
        - last_window_closed: Force exit the event loop after ipython console
                              is closed
        - open_project_pop_up: Open a pop-up to open a project and updates
                               the recent projects
        - open_recent_project: Open a recent project
        - open_shell: Open a Qt console shell with an IPython kernel seeing
                      the program internals.
        - package_library_pop_up: Open the package library pop-up
        - project_properties_pop_up: Open the project properties pop-up
        - redo: Redo the last action made by the user
        - remove_raw_files_useless: Remove the useless raw files of the
                                    current project
        - run_ipconsole_kernel: Starts and initializes an IPython kernel with
                                support for a Qt-based GUI.
        - save: Save either the current project or the current pipeline
        - save_as: Save either the current project or the current pipeline
                   under a new name
        - save_project_as: Open a pop-up to save the current project as
        - saveChoice: Checks if the project needs to be saved as or just saved
        - see_all_projects: Open a pop-up to show the recent projects
        - set_controller_version: Reverses controller_version_changed attribute
        - setup_menu_actions: Initialize menu actions
        - setup_window_size: Set the window size and maximize if needed
        - software_preferences_pop_up: Open the Mia preferences pop-up
        - switch_project: Switches project if it's possible
        - tab_changed: Method called when the tab is changed
        - undo: Undoes the last action made by the user
        - update_project: Update the project once the database has been
                          updated
        - update_recent_projects_actions: Update the list of recent projects

    """

    def __init__(self, project, test=False, deleted_projects=None):
        """
        Main window class, initializes the software appearance and defines
        interactions with the user.

        :param project: Current project in the software.
        :param test: Boolean indicating if the widget is launched from unit
                     tests or not.
        :param deleted_projects: Projects that have been deleted.

        """
        super().__init__()
        QApplication.restoreOverrideCursor()
        # Associate methods and instance to call them from anywhere
        QCoreApplication.instance().title = self.windowTitle
        QCoreApplication.instance().set_title = self.setWindowTitle

        if deleted_projects:
            self.msg = PopUpDeletedProject(deleted_projects)

        self.config = Config()
        self.config.setSourceImageDir(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                "sources_images",
            )
        )
        self.windowName = "MIA - Multiparametric Image Analysis"
        self.projectName = "Unnamed project"
        self.project = project
        self.test = test
        self.saved_projects = SavedProjects()
        self.saved_projects_list = self.saved_projects.pathsList
        self.saved_projects_actions = []
        self.controller_version_changed = False
        # Define main window view
        self.create_view_window()
        # Initialize menu
        self.menu_file = self.menuBar().addMenu("File")
        self.menu_edition = self.menuBar().addMenu("Edit")
        self.menu_help = self.menuBar().addMenu("Help")
        self.menu_about = self.menuBar().addMenu("About")
        self.menu_more = self.menuBar().addMenu("More")
        self.menu_install_process = QMenu("Install processes", self)
        self.menu_saved_projects = QMenu("Saved projects", self)
        # Initialize tabs
        self.tabs = QTabWidget()
        self.data_browser = DataBrowser(self.project, self)
        self.data_viewer = DataViewerTab(self)
        self.pipeline_manager = PipelineManagerTab(self.project, [], self)
        self.centralWindow = QWidget()
        # Initialize menu actions
        sources_images_dir = self.config.getSourceImageDir()
        self.setup_menu_actions(sources_images_dir)
        # Connect actions & menus views
        self.create_view_actions()
        self.create_view_menus()
        # Create Tabs
        self.create_tabs()
        self.setCentralWidget(self.centralWindow)
        # Set window size and maximize if needed
        self.setup_window_size()

    def add_clinical_tags(self):
        """Add the clinical tags to the database and the data browser."""

        added_tags = self.project.add_clinical_tags()

        for tag in added_tags:
            column = self.data_browser.table_data.get_index_insertion(tag)
            self.data_browser.table_data.add_column(column, tag)

    def check_database(self):
        """
        Check if files in database have been modified since first import.
        """

        if self.project is None:
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        logger.info("Verify scans...")
        t0 = time.time()
        problem_list = data_loader.verify_scans(self.project)
        logger.info(f"check time: {time.time() - t0}")
        QApplication.restoreOverrideCursor()

        # Message if invalid files
        if problem_list:
            str_msg = "".join(f"{element}\n\n" for element in problem_list)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "These files have been modified or removed since "
                "they have been converted for the first time:"
            )
            msg.setInformativeText(str_msg)
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()

    def check_unsaved_modifications(self):
        """
        Check if there are differences between the current project and the
        database.

        :returns (bool): True if there are unsaved modifications,
                         False otherwise
        """

        if self.project.isTempProject:

            with self.project.database.data() as database_data:
                return bool(
                    database_data.get_document_names(COLLECTION_CURRENT)
                )

        return self.project.hasUnsavedModifications()

    def closeEvent(self, event):
        """
        Override the QWidget closing event to check if there are unsaved
        modifications.

        :param event: closing event
        """
        if not self.check_unsaved_modifications() or self.test:
            can_exit = True

        else:
            self.pop_up_close = PopUpQuit(self.project)
            self.pop_up_close.save_as_signal.connect(self.saveChoice)
            self.pop_up_close.exec()
            can_exit = self.pop_up_close.can_exit()

        if can_exit:

            if self.pipeline_manager.init_clicked:
                self.project.unsaveModifications()

                for brick in self.pipeline_manager.brick_list:
                    self.data_browser.table_data.delete_from_brick(brick)

            # Clean up
            config = Config()
            opened_projects = config.get_opened_projects()

            if self.project.folder in opened_projects:
                opened_projects.remove(self.project.folder)

            config.set_opened_projects(opened_projects)

            # Change controller version if needed
            if self.controller_version_changed:
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setText("Controller version change")
                self.msg.setInformativeText(
                    f"A change of controller version, from "
                    f"{'V1' if config.isControlV1() else 'V2'} to "
                    f"{'V2' if config.isControlV1() else 'V1'}, "
                    f"is planned for next start-up. Do you confirm that "
                    f"you would like to perform this "
                    f"change?"
                )
                self.msg.setWindowTitle("Warning")
                self.msg.setStandardButtons(
                    QMessageBox.Yes | QMessageBox.Cancel
                )
                return_value = self.msg.exec()

                if return_value == QMessageBox.Yes:
                    config.setControlV1(not config.isControlV1())

                self.msg.close()

            config.saveConfig()
            self.remove_raw_files_useless()
            event.accept()
            event.ignore()

        if self.data_browser.viewer:
            self.data_browser.viewer.clear()

        if self.data_viewer:
            self.data_viewer.clear()

    def create_project_pop_up(self):
        """Create a new project."""

        if self.check_unsaved_modifications():
            self.pop_up_close = PopUpQuit(self.project)
            self.pop_up_close.save_as_signal.connect(self.saveChoice)
            self.pop_up_close.exec()
            can_switch = self.pop_up_close.can_exit()

        else:
            can_switch = True

        if can_switch:
            # Opens a pop-up when the 'New project' action is clicked and
            # updates the recent projects

            try:
                self.exPopup = PopUpNewProject()

            except Exception as e:
                logger.warning(f"Create_project_pop_up: {e}")
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Critical)
                self.msg.setText("Invalid projects folder path")
                self.msg.setInformativeText(
                    "The projects folder path in Mia preferences is invalid!"
                )
                self.msg.setWindowTitle("Error")
                yes_button = self.msg.addButton(
                    "Open Mia preferences", QMessageBox.YesRole
                )
                self.msg.addButton(QMessageBox.Ok)
                self.msg.exec()

                if self.msg.clickedButton() == yes_button:
                    self.software_preferences_pop_up()

                self.msg.close()

            else:

                if self.exPopup.exec():
                    self.exPopup.get_filename(self.exPopup.selectedFiles())
                    file_name = self.exPopup.relative_path
                    # Removing the old project from the list of
                    # currently opened projects
                    config = Config()
                    opened_projects = config.get_opened_projects()
                    opened_projects.remove(self.project.folder)
                    config.set_opened_projects(opened_projects)
                    config.saveConfig()
                    # We remove the useless files from the old project
                    self.remove_raw_files_useless()
                    self.project = Project(self.exPopup.relative_path, True)
                    self.update_project(
                        file_name
                    )  # project updated everywhere

    def create_view_actions(self):
        """Create the actions and their shortcuts in each menu"""

        self.action_create.setShortcut("Ctrl+N")
        self.action_open.setShortcut("Ctrl+O")
        self.action_save.setShortcut("Ctrl+S")
        self.addAction(self.action_save)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.addAction(self.action_save_as)
        self.addAction(self.action_delete)
        self.action_import.setShortcut("Ctrl+I")

        for i in range(self.config.get_max_projects()):
            self.saved_projects_actions.append(
                QAction(
                    self, visible=False, triggered=self.open_recent_project
                )
            )

        if Config().get_user_mode() is True:
            self.action_delete_project.setDisabled(True)

        else:
            self.action_delete_project.setEnabled(True)

        self.action_exit.setShortcut("Ctrl+W")
        self.action_undo.setShortcut("Ctrl+Z")
        self.action_redo.setShortcut("Ctrl+Y")
        # Connection of the several triggered signals of the actions to some
        # other methods
        self.action_create.triggered.connect(self.create_project_pop_up)
        self.action_open.triggered.connect(self.open_project_pop_up)
        self.action_exit.triggered.connect(self.close)
        self.action_check_database.triggered.connect(self.check_database)
        self.action_open_shell.triggered.connect(self.open_shell)
        self.action_save.triggered.connect(self.save)
        self.action_save_as.triggered.connect(self.save_as)
        self.action_delete.triggered.connect(self.delete_project)
        self.action_import.triggered.connect(self.import_data)
        self.action_see_all_projects.triggered.connect(self.see_all_projects)
        self.action_project_properties.triggered.connect(
            self.project_properties_pop_up
        )
        self.action_software_preferences.triggered.connect(
            self.software_preferences_pop_up
        )
        self.action_package_library.triggered.connect(
            self.package_library_pop_up
        )
        self.action_undo.triggered.connect(self.undo)
        self.action_redo.triggered.connect(self.redo)
        self.action_documentation.triggered.connect(self.documentation)
        self.action_credits.triggered.connect(self.credits)
        self.action_install_processes_folder.triggered.connect(
            lambda: self.install_processes_pop_up(folder=True)
        )
        self.action_install_processes_zip.triggered.connect(
            lambda: self.install_processes_pop_up(folder=False)
        )

    def create_view_menus(self):
        """Create the menu-bar view."""

        self.menu_more.addMenu(self.menu_install_process)
        # Actions in the "File" menu
        self.menu_file.addAction(self.action_create)
        self.menu_file.addAction(self.action_open)
        self.menu_file.addAction(self.action_check_database)
        self.action_save_project.triggered.connect(self.saveChoice)
        self.action_save_project_as.triggered.connect(self.save_project_as)
        self.action_delete_project.triggered.connect(self.delete_project)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_import)
        self.menu_file.addSeparator()
        self.menu_file.addMenu(self.menu_saved_projects)

        for i in range(self.config.get_max_projects()):
            self.menu_saved_projects.addAction(self.saved_projects_actions[i])

        self.menu_saved_projects.addSeparator()
        self.menu_saved_projects.addAction(self.action_see_all_projects)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_software_preferences)
        self.menu_file.addAction(self.action_project_properties)
        self.menu_file.addAction(self.action_package_library)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_open_shell)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        self.update_recent_projects_actions()
        # Actions in the "Edition" menu
        self.menu_edition.addAction(self.action_undo)
        self.menu_edition.addAction(self.action_redo)
        # Actions in the "Help" menu
        self.menu_help.addAction(self.action_documentation)
        self.menu_help.addAction(self.action_credits)
        # Actions in the "More > Install processes" menu
        self.menu_install_process.addAction(
            self.action_install_processes_folder
        )
        self.menu_install_process.addAction(self.action_install_processes_zip)

    def create_view_window(self):
        """Create the main window view."""
        sources_images_dir = Config().getSourceImageDir()
        app_icon = QIcon(
            os.path.join(sources_images_dir, "Logo_populse_mia_LR.jpeg")
        )
        self.setWindowIcon(app_icon)
        background_color = self.config.getBackgroundColor()
        text_color = self.config.getTextColor()

        if not self.config.get_user_mode():
            self.windowName = f"{self.windowName} (Admin mode)"

        self.windowName = f"{self.windowName} - "
        self.setStyleSheet(
            f"background-color:{background_color};color:{text_color};"
        )
        self.statusBar().showMessage(
            "Please create a new project (Ctrl+N) or "
            "open an existing project (Ctrl+O)"
        )
        self.setWindowTitle(f"{self.windowName}{self.projectName}")

    def create_tabs(self):
        """
        Create the tabs and initializes the DataBrowser and PipelineManager
        classes.
        """
        self.config = Config()
        self.tabs.setAutoFillBackground(False)
        self.tabs.setStyleSheet("QTabBar{font-size:16pt;text-align: center}")
        self.tabs.setMovable(True)
        self.tabs.addTab(self.data_browser, "Data Browser")
        self.tabs.addTab(self.data_viewer, "Data Viewer")
        self.tabs.addTab(self.pipeline_manager, "Pipeline Manager")
        self.tabs.currentChanged.connect(self.tab_changed)
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.tabs)
        self.centralWindow.setLayout(vertical_layout)

    def credits(self):
        """Open the credits in a web browser"""
        webbrowser.open(
            "https://github.com/populse/populse_mia/graphs/contributors"
        )

    def del_clinical_tags(self):
        """Remove the clinical tags to the database and the data browser"""

        removed_tags = self.project.del_clinical_tags()

        for tag in removed_tags:
            self.data_browser.table_data.removeColumn(
                self.data_browser.table_data.get_tag_column(tag)
            )

    def delete_project(self):
        """
        Open a pop-up to open a project and updates the recent projects list.
        """

        try:
            self.exPopup = PopUpDeleteProject(self)

        except Exception as e:
            logger.warning(f"Delete_project: {e}")
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("Invalid projects folder path")
            self.msg.setInformativeText(
                "The projects folder path in Mia preferences is invalid!"
            )
            self.msg.setWindowTitle("Error")
            yes_button = self.msg.addButton(
                "Open Mia preferences", QMessageBox.YesRole
            )
            self.msg.addButton(QMessageBox.Ok)
            self.msg.exec()

            if self.msg.clickedButton() == yes_button:
                self.software_preferences_pop_up()

            self.msg.close()

        else:
            self.exPopup.exec()

    @staticmethod
    def documentation():
        """Open the documentation in a web browser."""
        webbrowser.open(
            "https://populse.github.io/populse_mia/html/index.html"
        )

    def get_controller_version(self):
        """Gives the value of the controller_version_changed attribute.

        :return: Boolean
        """
        return self.controller_version_changed

    def import_data(self):
        """
        Import MRI data using the MRI File Manager and load it into
        the database.

        This method performs the following steps:
        1. Launches the MRI conversion software to convert MRI files to
           Nifti/JSON format
        2. Attempts import with maximum heap size of 4096M, falls back to
           1024M if needed
        3. Updates the database with newly imported scans
        4. Refreshes the data browser UI with new scan information
        """
        # Opens the conversion software to convert the MRI files in Nifti/Json
        config = Config()
        home = expanduser("~")
        export_nifti_path = os.path.join(
            self.project.folder, "data", "raw_data"
        )
        logger.info("Starting MRI conversion process...")

        try:
            # Xmxsize: Specifies the maximum size (in bytes) of the memory
            #          allocation pool in bytes
            # Start with 4096M
            code_exit = subprocess.call(
                [
                    "java",
                    "-Xmx4096M",
                    "-jar",
                    config.get_mri_conv_path(),
                    f"[ProjectsDir] {home}",
                    f"[ExportNifti] {export_nifti_path}",
                    "[ExportToMIA] PatientName-StudyName-"
                    "CreationDate-SeqNumber-Protocol-"
                    "SequenceName-AcquisitionTime",
                    "CloseAfterExport",
                    "[ExportOptions] 00013",
                ]
            )

            if code_exit != 0 and code_exit != 100:
                raise ValueError("mri_conv did not run properly!")

        except ValueError:
            logger.warning(
                "Mri_conv: Test with lower maximum heap "
                "size (4096M -> 1024M)..."
            )
            export_nifti_path = os.path.join(
                self.project.folder, "data", "raw_data"
            )
            code_exit = subprocess.call(
                [
                    "java",
                    "-Xmx1024M",
                    "-jar",
                    config.get_mri_conv_path(),
                    f"[ProjectsDir] {home}",
                    f"[ExportNifti] {export_nifti_path}",
                    "[ExportToMIA] PatientName-StudyName-"
                    "CreationDate-SeqNumber-Protocol-"
                    "SequenceName-AcquisitionTime",
                    "CloseAfterExport",
                    "[ExportOptions] 00013",
                ]
            )

        # 'NoLogExport' if we don't want log export
        if code_exit == 0:
            # Database filled
            new_scans = data_loader.read_log(self.project, self)
            # Table updated

            with self.project.database.data() as database_data:
                documents = database_data.get_document_names(
                    COLLECTION_CURRENT
                )
            self.data_browser.table_data.scans_to_visualize = documents
            self.data_browser.table_data.scans_to_search = documents
            self.data_browser.table_data.add_columns()
            self.data_browser.table_data.fill_headers()
            self.data_browser.table_data.add_rows(new_scans)
            self.data_browser.reset_search_bar()
            self.data_browser.frame_advanced_search.setHidden(True)
            self.data_browser.advanced_search.rows = []
            self.project.unsavedModifications = True

        elif code_exit == 100:  # User only close mri_conv and do nothing
            pass

        else:
            logger.warning(
                "Mri_conv, did not work properly. Current absolute"
                " path to MRIManager.jar defined in File > MIA Preferences:"
            )
            logger.warning(f"{config.get_mri_conv_path}")

            if not os.path.isfile(config.get_mri_conv_path()):
                mssgText = (
                    f"Warning: mri_conv did not work properly. The "
                    f"current absolute path to MRIManager.jar doesn't "
                    f"seem to be correctly defined.\nCurrent absolute "
                    f"path to MRIManager.jar defined in\nFile > MIA "
                    f"Preferences:\n{config.get_mri_conv_path()}"
                )

            else:
                mssgText = (
                    f"Warning : mri_conv did not work properly. Please "
                    f"check if the currently installed mri_conv Java "
                    f"ARchive is not corrupted.\nCurrent absolute path "
                    f"to MRIManager.jar defined in\nFile > MIA "
                    f"Preferences:\n{config.get_mri_conv_path()}"
                )

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("populse_mia - Warning: Data import issue!")
            msg.setText(mssgText)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()

    def install_processes_pop_up(self, folder=False):
        """Open the install processes pop-up.

        :param folder: boolean, True if installing from a folder

        """
        self.pop_up_install_processes = InstallProcesses(self, folder=folder)
        self.pop_up_install_processes.show()
        self.pop_up_install_processes.process_installed.connect(
            self.pipeline_manager.processLibrary.update_process_library
        )
        self.pop_up_install_processes.process_installed.connect(
            self.pipeline_manager.processLibrary.pkg_library.update_config
        )

    @staticmethod
    def last_window_closed():
        """Force exit the event loop after ipython console is closed.

        If the ipython console has been run, something prevents Qt from
        quitting after the window is closed. The cause is not known yet.
        So: force exit the event loop.
        """

        from soma.qt_gui.qt_backend import Qt

        Qt.QTimer.singleShot(10, Qt.qApp.exit)

    def open_project_pop_up(self):
        """
        Open a dialog to select and open a project, updating recent
        projects list.

        This method handles:
        1. Checking for unsaved modifications in current project
        2. Opening project selection dialog
        3. Validating project path
        4. Switching to new project
        5. Updating clinical mode based on database fields
        6. Updating database paths if project is external
        """

        # Ui_Dialog() is defined in pop_ups.py
        # We check for unsaved modifications
        if self.check_unsaved_modifications():
            # If there are unsaved modifications, we ask the user what he
            # wants to do
            self.pop_up_close = PopUpQuit(self.project)
            self.pop_up_close.save_as_signal.connect(self.saveChoice)
            self.pop_up_close.exec()
            can_switch = self.pop_up_close.can_exit()

        else:
            can_switch = True

        # We can open a new project
        if can_switch:

            try:
                self.exPopup = PopUpOpenProject()

            except Exception as e:
                logger.warning(f"Open_project_pop_up: {e}")
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Critical)
                self.msg.setText("Invalid projects folder path")
                self.msg.setInformativeText(
                    "The projects folder path in Mia preferences is invalid!"
                )
                self.msg.setWindowTitle("Error")
                yes_button = self.msg.addButton(
                    "Open Mia preferences", QMessageBox.YesRole
                )
                self.msg.addButton(QMessageBox.Ok)
                self.msg.exec()

                if self.msg.clickedButton() == yes_button:
                    self.software_preferences_pop_up()

                self.msg.close()

            else:

                if self.exPopup.exec():
                    project_name = self.exPopup.selectedFiles()
                    self.exPopup.get_filename(project_name)
                    project_name = self.exPopup.relative_path
                    self.data_browser.data_sent = False

                    # We switch the project
                    self.switch_project(project_name, self.exPopup.name)

                    with self.project.database.data() as database_data:
                        field_names = database_data.get_field_names(
                            COLLECTION_CURRENT
                        )

                    if all(ele in field_names for ele in CLINICAL_TAGS):
                        Config().set_clinical_mode(True)

                    else:
                        Config().set_clinical_mode(False)

                    # Update the history and brick tables in the newly opened
                    # project, if it comes from outside.
                    path_name = os.path.dirname(
                        os.path.abspath(os.path.normpath(project_name))
                    )
                    projectsPath = os.path.abspath(
                        self.config.getPathToProjectsFolder()
                    )

                    if path_name != projectsPath:
                        self.project.update_db_for_paths(path_name)

    def open_recent_project(self):
        """Open a recent project."""

        # We check for unsaved modifications
        if self.check_unsaved_modifications():
            # If there are unsaved modifications, we ask the user what he
            # wants to do
            self.pop_up_close = PopUpQuit(self.project)
            self.pop_up_close.save_as_signal.connect(self.saveChoice)
            self.pop_up_close.exec()
            can_switch = self.pop_up_close.can_exit()

        else:
            can_switch = True

        # We can open a new project
        if can_switch:
            action = self.sender()

            if action:
                project_name = action.data()
                entire_path = os.path.abspath(project_name)
                path, name = os.path.split(entire_path)
                relative_path = os.path.relpath(project_name)
                self.switch_project(relative_path, name)
                # We switch the project

                with self.project.database.data() as database_data:
                    field_names = database_data.get_field_names(
                        COLLECTION_CURRENT
                    )
                    documents = database_data.get_document_names(
                        COLLECTION_CURRENT
                    )

                self.data_viewer.set_documents(self.project, documents)

                if all(ele in field_names for ele in CLINICAL_TAGS):
                    Config().set_clinical_mode(True)

                else:
                    Config().set_clinical_mode(False)

    def open_shell(self):
        """
        Open a Qt console shell with an IPython kernel seeing the program
        internals.
        """

        from soma.qt_gui import qt_backend

        ipfunc = None
        mode = "qtconsole"
        logger.info("StartShell...")

        try:
            # to check it is installed
            import jupyter_core.application  # noqa: F401
            import qtconsole  # noqa: F401

            ipfunc = (
                "from jupyter_core import application; "
                "app = application.JupyterApp(); app.initialize(); app.start()"
            )

        except ImportError:
            logger.warning("Failed to run Qt console...")
            return

        if ipfunc:
            import soma.subprocess

            ipConsole = self.run_ipconsole_kernel(mode)

            if ipConsole:
                global _ipsubprocs
                qt_api = qt_backend.get_qt_backend()
                qt_apis = {
                    "PyQt4": "pyqt",
                    "PyQt5": "pyqt5",
                    "PySide": "pyside",
                }
                qt_api_code = qt_apis.get(qt_api, "pyq5t")
                cmd = [
                    sys.executable,
                    "-c",
                    f'import os; os.environ["QT_API"] = '
                    f'"{qt_api_code}"; {ipfunc}',
                    mode,
                    "--existing",
                    f"--shell={ipConsole.shell_port}",
                    f"--iopub={ipConsole.iopub_port}",
                    f"--stdin={ipConsole.stdin_port}",
                    f"--hb={ipConsole.hb_port}",
                ]
                sp = soma.subprocess.Popen(cmd)
                pd = _ProcDeleter(sp)

                with _ipsubprocs_lock:
                    _ipsubprocs.append(pd)

                pd.start()
                # hack the lastWindowClosed event because it becomes inactive
                # otherwise
                QApplication.instance().lastWindowClosed.connect(
                    self.last_window_closed
                )

    def package_library_pop_up(self):
        """Open the package library pop-up"""

        self.pop_up_package_library = PackageLibraryDialog(
            mia_main_window=self
        )
        self.pop_up_package_library.setGeometry(300, 200, 800, 600)
        self.pop_up_package_library.show()
        self.pop_up_package_library.signal_save.connect(
            self.pipeline_manager.processLibrary.update_process_library
        )

    def project_properties_pop_up(self):
        """Open the project properties pop-up"""

        with self.project.database.data() as database_data:
            old_tags = database_data.get_shown_tags()

        self.pop_up_settings = PopUpProperties(
            self.project, self.data_browser, old_tags
        )
        self.pop_up_settings.setGeometry(300, 200, 800, 600)
        self.pop_up_settings.show()

        if self.pop_up_settings.exec():

            with self.project.database.data() as database_data:
                self.data_browser.table_data.update_visualized_columns(
                    old_tags, database_data.get_shown_tags()
                )

    def redo(self):
        """Redo the last action made by the user."""

        if (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Data Browser"
        ):
            # In Data Browser
            self.project.redo(self.data_browser.table_data)
            # Action remade in the Database

        elif (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Pipeline Manager"
        ):
            # In Pipeline Manager
            self.pipeline_manager.redo()

    def remove_raw_files_useless(self):
        """Remove the useless raw files of the current project, close the
        database connection. The project is not valid any longer after this
        call."""

        folder = self.project.folder
        self.project.database.close()
        self.project.database = None

        # If it's unnamed project, we can remove the whole project
        if self.project.isTempProject:
            shutil.rmtree(folder)

        self.project = None

    @staticmethod
    def run_ipconsole_kernel(mode="qtconsole"):
        """
        Starts and initializes an IPython kernel with support for
        a Qt-based GUI.

        This method is designed to set up and run an IPython kernel
        for interactive computing, with the specified mode (defaulting
        to `qtconsole`). It handles initialization of the kernel and
        associated event loops, ensuring proper integration with Qt-based
        applications.

        :param mode (str): The mode for running the IPython kernel. Default
                           is "qtconsole". It determines the GUI integration
                           mode of the kernel.

        :returns (IPKernelApp): The instance of the IPython kernel
                                application.

        Notes:
            - The method ensures that the kernel is properly initialized if
              it hasn't been set up already.
            - To support Qt-based GUIs, the Qt event loop is properly
              integrated with the IPython kernel.
            - Special handling for Tornado versions >= 4.5 ensures
              compatibility with its callback mechanism.
        """

        logger.info(f"Run_ipconsole_kernel: {mode}")
        import IPython  # noqa: F401
        from IPython.lib import guisupport
        from soma.qt_gui.qt_backend import Qt

        qtapp = Qt.QApplication.instance()
        qtapp._in_event_loop = True
        guisupport.in_event_loop = True

        from ipykernel.kernelapp import IPKernelApp

        app = IPKernelApp.instance()

        if not app.initialized() or not app.kernel:
            logger.info("Running IP console kernel")
            # don't know why this is not set automatically
            app.hb_port = 50042
            app.initialize(
                [
                    mode,
                    "--gui=qt",  # '--pylab=qt',
                    "--KernelApp.parent_appname='ipython-{mode}'",
                ]
            )
            # in ipython >= 1.2, app.start() blocks until a ctrl-c is issued
            # in the terminal. Seems to block in
            # tornado.ioloop.PollIOLoop.start()
            # So, don't call app.start because it would begin a zmq/tornado
            # loop instead we must just initialize its callback.
            # if app.poller is not None:
            # app.poller.start()
            app.kernel.start()

            # IP 2 allows just calling the current callbacks.
            # For IP 1 it is not sufficient.
            import tornado
            from zmq.eventloop import ioloop

            if tornado.version_info >= (4, 5):
                # tornado 5 is using a decque for _callbacks, not a
                # list + explicit locking

                def my_start_ioloop_callbacks(self):
                    """
                    Executes pending callbacks in the Tornado
                    IOLoop (Tornado >= 4.5).

                    This method processes the `_callbacks` deque in the
                    Tornado IOLoop, executing each callback in the order
                    they were added. The use of `popleft` ensures efficient
                    removal of executed callbacks.

                    Notes:
                        - Tornado 4.5 and later versions use a `deque`
                          for `_callbacks`, allowing lock-free access to
                          pending callbacks.

                    Raises:
                        AttributeError: If `_callbacks` is not defined for
                                        the IOLoop instance.
                    """

                    if hasattr(self, "_callbacks"):
                        ncallbacks = len(self._callbacks)

                        for i in range(ncallbacks):
                            self._run_callback(self._callbacks.popleft())

            else:

                def my_start_ioloop_callbacks(self):
                    """
                    Executes pending callbacks in the Tornado IOLoop
                    (Tornado < 4.5).

                    This method processes the `_callbacks` list in the
                    Tornado IOLoop, executing each callback in the order
                    they were added. The method ensures thread safety by
                    using a lock (`_callback_lock`) to protect access to
                    the `_callbacks` list during execution.

                    Notes:
                        - Tornado versions before 4.5 use a list
                          (`_callbacks`) for pending callbacks, requiring
                          explicit locking to avoid race conditions.
                        - After processing all callbacks, the `_callbacks`
                          list is reset to an empty list.

                    Raises:
                        AttributeError: If `_callbacks` or `_callback_lock`
                                        is not defined for the IOLoop
                                        instance.
                    """

                    with self._callback_lock:
                        callbacks = self._callbacks
                        self._callbacks = []

                    for callback in callbacks:
                        self._run_callback(callback)

            my_start_ioloop_callbacks(ioloop.IOLoop.instance())

        return app

    def save(self):
        """Save either the current project or the current pipeline"""

        if (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Data Browser"
        ):
            # In Data Browser
            self.saveChoice()

        elif (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Pipeline Manager"
        ):
            # In Pipeline Manager
            self.pipeline_manager.savePipeline()

    def save_as(self):
        """Save either the current project or the current pipeline under a new
        name.
        """
        if (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Data Browser"
        ):
            # In Data Browser
            self.save_project_as()

        elif (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Pipeline Manager"
        ):
            # In Pipeline Manager
            self.pipeline_manager.savePipelineAs()

    def save_project_as(self):
        """Open a pop-up to save the current project as"""

        try:
            self.exPopup = PopUpSaveProjectAs()

        except Exception as e:
            logger.warning(f"Save_project_as: {e}")
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("Invalid projects folder path")
            self.msg.setInformativeText(
                "The projects folder path in Mia preferences is invalid!"
            )
            self.msg.setWindowTitle("Error")
            yes_button = self.msg.addButton(
                "Open Mia preferences", QMessageBox.YesRole
            )
            self.msg.addButton(QMessageBox.Ok)
            self.msg.exec()

            if self.msg.clickedButton() == yes_button:
                self.software_preferences_pop_up()

            self.msg.close()

        else:

            if self.test:
                self.exPopup.exec = lambda x=0: True
                self.exPopup.validate = True
                self.exPopup.new_project.text = lambda x=0: "something"
                self.exPopup.return_value()

            self.exPopup.exec()

            if self.exPopup.validate:
                old_folder_rel = self.project.folder
                old_folder = os.path.abspath(old_folder_rel)
                as_folder_rel = self.exPopup.relative_path
                as_folder = os.path.abspath(as_folder_rel)

                if as_folder_rel == old_folder_rel:
                    self.project.saveModifications()
                    return True

                database_path = os.path.join(as_folder, "database")
                properties_path = os.path.join(as_folder, "properties")
                filters_path = os.path.join(as_folder, "filters")
                data_path = os.path.join(as_folder, "data")
                raw_data_path = os.path.join(data_path, "raw_data")
                downloaded_data_path = os.path.join(
                    data_path, "downloaded_data"
                )

                # List of projects updated
                if not self.test:
                    self.saved_projects_list = (
                        self.saved_projects
                    ).addSavedProject(as_folder_rel)

                self.update_recent_projects_actions()

                if os.path.exists(as_folder_rel):
                    # Prevent by a careful message
                    # see PopUpSaveProjectAs/return_value
                    # in admin mode only
                    shutil.rmtree(as_folder_rel)

                if not os.path.exists(as_folder_rel):
                    os.makedirs(as_folder_rel)
                    os.mkdir(data_path)
                    os.mkdir(raw_data_path)
                    os.mkdir(downloaded_data_path)
                    os.mkdir(filters_path)

                # Data files copied
                if os.path.exists(os.path.join(old_folder_rel, "data")):

                    for filename in glob.glob(
                        os.path.join(old_folder, "data", "raw_data", "*")
                    ):
                        shutil.copy(
                            filename, os.path.join(data_path, "raw_data")
                        )

                    shutil.copytree(
                        os.path.join(old_folder, "data", "derived_data"),
                        os.path.join(data_path, "derived_data"),
                    )

                    for filename in glob.glob(
                        os.path.join(
                            old_folder, "data", "downloaded_data", "*"
                        )
                    ):
                        shutil.copy(
                            filename,
                            os.path.join(data_path, "downloaded_data"),
                        )

                if os.path.exists(os.path.join(old_folder_rel, "filters")):

                    for filename in glob.glob(
                        os.path.join(old_folder, "filters", "*")
                    ):
                        shutil.copy(filename, os.path.join(filters_path))

                # First we register the Database before committing the last
                # pending modifications
                shutil.copy(
                    os.path.join(old_folder, "database", "mia.db"),
                    os.path.join(
                        old_folder, "database", "mia_before_commit.db"
                    ),
                )
                # We commit the last pending modifications
                self.project.saveModifications()
                os.mkdir(properties_path)
                shutil.copy(
                    os.path.join(old_folder, "properties", "properties.yml"),
                    properties_path,
                )
                # We copy the Database with all the modifications committed in
                # the new project
                os.mkdir(database_path)
                shutil.copy(
                    os.path.join(old_folder, "database", "mia.db"),
                    database_path,
                )
                reset_old_db = not self.project.isTempProject
                # Removing the old project from the list of
                # currently opened projects
                config = Config()
                opened_projects = config.get_opened_projects()

                if self.project.folder in opened_projects:
                    opened_projects.remove(self.project.folder)

                config.set_opened_projects(opened_projects)
                config.saveConfig()
                # We remove the useless files from the old project
                self.remove_raw_files_useless()

                if reset_old_db:
                    # We remove the Database with all the modifications saved
                    # in the old project
                    os.remove(os.path.join(old_folder, "database", "mia.db"))
                    # We reput the Database without the last modifications
                    # in the old project
                    shutil.copy(
                        os.path.join(
                            old_folder, "database", "mia_before_commit.db"
                        ),
                        os.path.join(old_folder, "database", "mia.db"),
                    )
                    os.remove(
                        os.path.join(
                            old_folder, "database", "mia_before_commit.db"
                        )
                    )

                # project updated everywhere
                self.project = Project(as_folder_rel, False)
                self.project.setName(os.path.basename(as_folder_rel))
                self.project.setDate(
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                )
                self.project.saveModifications()
                self.update_project(as_folder_rel, call_update_table=False)
                # project updated everywhere

                # If some files have been set in the pipeline editors,
                # display a warning message
                if (
                    self.pipeline_manager.pipelineEditorTabs
                ).has_pipeline_nodes():
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(
                        "This action moves the current database. "
                        "All pipelines will need to be initialized "
                        "again before they can run."
                    )
                    msg.setWindowTitle("Warning")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()

        # Update of the history and the brick table in the newly
        # created project
        self.project.update_db_for_paths()

    def saveChoice(self):
        """Check if the project needs to be 'saved as' or just 'saved'."""

        if self.project.isTempProject:
            self.save_project_as()

        else:
            self.project.saveModifications()

    def see_all_projects(self):
        """Open a pop-up to show the recent projects."""
        # Ui_Dialog() is defined in pop_ups.py
        self.exPopup = PopUpSeeAllProjects(self.saved_projects, self)

        if self.exPopup.exec():
            file_path = self.exPopup.relative_path

            if not self.test:
                self.saved_projects_list = self.saved_projects.addSavedProject(
                    file_path
                )
            self.update_recent_projects_actions()

    def set_controller_version(self):
        """Reverses the value of the controller_version_changed attribute.

        From False to True and vice versa
        """
        self.controller_version_changed = not self.controller_version_changed

    def setup_menu_actions(self, sources_images_dir):
        """
        Initialize menu actions with icons and descriptions.

        :param sources_images_dir: Directory containing source images
                                   for icons.
        """
        self.action_save_project = self.menu_file.addAction("Save project")
        self.action_save_project_as = self.menu_file.addAction(
            "Save project as"
        )
        self.action_delete_project = self.menu_file.addAction("Delete project")
        self.action_create = QAction("New project", self)
        self.action_open = QAction("Open project", self)
        self.action_save = QAction("Save", self)
        self.action_save_as = QAction("Save as", self)
        self.action_delete = QAction("Delete project", self)
        self.action_import = QAction(
            QIcon(os.path.join(sources_images_dir, "Blue.png")), "Import", self
        )
        self.action_check_database = QAction("Check the whole database", self)
        self.action_see_all_projects = QAction("See all projects", self)
        self.action_project_properties = QAction("Project properties", self)
        self.action_software_preferences = QAction("MIA preferences", self)
        self.action_package_library = QAction("Package library manager", self)
        self.action_open_shell = QAction("Open python shell", self)
        self.action_exit = QAction(
            QIcon(os.path.join(sources_images_dir, "exit.png")), "Exit", self
        )
        self.action_undo = QAction("Undo", self)
        self.action_redo = QAction("Redo", self)
        self.action_documentation = QAction("Documentation", self)
        self.action_credits = QAction("Credits", self)
        self.action_install_processes_folder = QAction("From folder", self)
        self.action_install_processes_zip = QAction("From zip file", self)

    def setup_window_size(self):
        """
        Set the window size and maximize if needed.
        """

        if self.config.get_mainwindow_maximized():
            self.showMaximized()

        else:
            size = self.config.get_mainwindow_size()

            if size:
                self.resize(size[0], size[1])

    def software_preferences_pop_up(self):
        """Open the Mia preferences pop-up."""
        self.pop_up_preferences = PopUpPreferences(self)
        self.pop_up_preferences.setGeometry(300, 200, 800, 600)
        self.pop_up_preferences.show()
        self.pop_up_preferences.use_clinical_mode_signal.connect(
            self.add_clinical_tags
        )
        self.pop_up_preferences.not_use_clinical_mode_signal.connect(
            self.del_clinical_tags
        )
        # Modifying the options in the Pipeline Manager (verify if user mode)
        self.pop_up_preferences.signal_preferences_change.connect(
            self.pipeline_manager.update_user_mode
        )

    def switch_project(self, file_path, name):
        """
        Check if it's possible to open the selected project and quit the
        current one.

        :param file_path: raw file_path
        :param name: project name

        :return: Boolean
        """
        # /!\ file_path and path are the same param

        # Switching project only if it's a different one
        if file_path == self.project.folder:
            return False

        # If the file exists
        if os.path.exists(os.path.join(file_path)):
            # If it is a Mia project
            required_paths = [
                os.path.join(file_path, "properties", "properties.yml"),
                os.path.join(file_path, "database", "mia.db"),
                os.path.join(file_path, "data", "raw_data"),
                os.path.join(file_path, "data", "derived_data"),
                os.path.join(file_path, "data", "downloaded_data"),
                os.path.join(file_path, "filters"),
            ]

            if all(os.path.exists(path) for path in required_paths):

                # We check if the name of the project directory is the
                # same in its properties
                with open(
                    os.path.join(file_path, "properties", "properties.yml"),
                    "r+",
                ) as stream:

                    if version.parse(yaml.__version__) > version.parse("5.1"):
                        properties = yaml.load(stream, Loader=yaml.FullLoader)

                    else:
                        properties = yaml.load(stream)

                    path, name = os.path.split(file_path)

                    if properties["name"] != name:
                        properties["name"] = name
                        yaml.dump(
                            properties,
                            stream,
                            default_flow_style=False,
                            allow_unicode=True,
                        )

                # We check for invalid scans in the project
                try:
                    temp_database = Project(file_path, False)

                except OSError:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("project already opened")
                    msg.setInformativeText(
                        f"The project at {file_path} is already opened "
                        f"in another instance of the software."
                    )
                    msg.setWindowTitle("Warning")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()
                    return False

                # We check for valid version of the project
                try:

                    with temp_database.database.data() as database_data:
                        field_names = database_data.get_field_names(
                            COLLECTION_CURRENT
                        )

                except ValueError:
                    field_names = None

                if (not field_names) or (TAG_HISTORY not in field_names):
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(
                        "The project cannot be read by Mia. Please check "
                        "if the project version is compatible with "
                        "the Mia version..."
                    )
                    msg.setWindowTitle("Warning")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()
                    config = Config()
                    opened_projects = config.get_opened_projects()

                    if file_path in opened_projects:
                        opened_projects.remove(file_path)
                        config.set_opened_projects(opened_projects)
                        config.saveConfig()

                    return False

                # project removed from the opened projects list
                config = Config()
                opened_projects = config.get_opened_projects()

                if self.project.folder in opened_projects:
                    opened_projects.remove(self.project.folder)

                config.set_opened_projects(opened_projects)
                config.saveConfig()
                # We remove the useless files from the old project
                self.remove_raw_files_useless()
                self.project = temp_database  # New Database
                self.update_project(file_path)
                # project updated everywhere
                return True

            # Not a Mia project
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("The project selected isn't a valid MIA project")
                msg.setInformativeText(
                    f"The project selected {name} isn't a Mia project"
                    f".\nPlease select a valid one."
                )
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                return False

        # The project doesn't exist anymore
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("The project selected doesn't exist anymore")
            msg.setInformativeText(
                f"The project selected {name} doesn't exist anymore."
                f"\nPlease select another one."
            )
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()
            return False

    def tab_changed(self):
        """
        Update the window when switching between application tab.

        Updates the UI state and data when switching between Data Browser,
        Data Viewer, and Pipeline Manager tabs. Handles data synchronization,
        search state preservation, and unsaved changes warnings.

        The method performs the following operations based on the selected
        tab:
        - Data Browser: Refreshes table data, preserves search state and
                        visualization settings
        - Data Viewer: Loads current viewer and updates document list
        - Pipeline Manager: Updates scan lists and handles unsaved
                            modifications
        """

        current_tab = self.tabs.tabText(self.tabs.currentIndex()).replace(
            "&", "", 1
        )

        if current_tab == "Data Browser":
            # data_browser refreshed after working in other tab
            old_scans = self.data_browser.table_data.scans_to_visualize

            with self.project.database.data() as database_data:
                documents = database_data.get_document_names(
                    COLLECTION_CURRENT
                )

            table_data = self.data_browser.table_data
            table_data.add_columns()
            table_data.fill_headers()
            table_data.add_rows(documents)
            table_data.scans_to_visualize = documents
            table_data.scans_to_search = documents
            table_data.itemChanged.disconnect()
            table_data.fill_cells_update_table()
            table_data.itemChanged.connect(table_data.change_cell_color)
            table_data.update_visualized_rows(old_scans)
            # Advanced search + search_bar opened
            old_search = self.project.currentFilter.search_bar
            self.data_browser.reset_search_bar()
            self.data_browser.search_bar.setText(old_search)

            if self.project.currentFilter.nots:
                self.data_browser.frame_advanced_search.setHidden(False)
                self.data_browser.advanced_search.scans_list = (
                    table_data.scans_to_visualize
                )
                self.data_browser.advanced_search.show_search()
                self.data_browser.advanced_search.apply_filter(
                    self.project.currentFilter
                )

        elif current_tab == "Data Viewer":
            self.data_viewer.load_viewer(self.data_viewer.current_viewer())

            with self.project.database.data() as database_data:
                documents = database_data.get_document_names(
                    COLLECTION_CURRENT
                )

            self.data_viewer.set_documents(self.project, documents)

        elif current_tab == "Pipeline Manager":

            if not self.data_browser.data_sent:

                with self.project.database.data() as database_data:
                    scans = database_data.get_document_names(
                        COLLECTION_CURRENT
                    )

                self.pipeline_manager.scan_list = scans
                self.pipeline_manager.nodeController.scan_list = scans
                self.pipeline_manager.pipelineEditorTabs.scan_list = scans

            self.pipeline_manager.pipelineEditorTabs.update_scans_list()
            self.pipeline_manager.update_user_buttons_states()
            current_editor = (
                self.pipeline_manager.pipelineEditorTabs.get_current_editor()
            )

            if current_editor.iterated_tag:
                self.pipeline_manager.iterationTable.update_iterated_tag(
                    current_editor.iterated_tag
                )

            # Pipeline Manager
            # The pending modifications must be saved before
            # working with pipelines (auto_commit)
            if self.project.hasUnsavedModifications():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Unsaved modifications in the Data Browser !")
                msg.setInformativeText(
                    "There are unsaved modifications in the database, "
                    "you need to save or remove them before working "
                    "with pipelines."
                )
                msg.setWindowTitle("Warning")
                save_button = QPushButton("Save")
                save_button.clicked.connect(self.project.saveModifications)
                unsave_button = QPushButton("Not Save")
                unsave_button.clicked.connect(self.project.unsaveModifications)
                msg.addButton(save_button, QMessageBox.AcceptRole)
                msg.addButton(unsave_button, QMessageBox.AcceptRole)
                msg.exec()

    def undo(self):
        """
        Reverts the last action performed by the user, depending on the
        active tab.

        If the "Data Browser" tab is active, the undo operation is applied
        to the project's database. If the "Pipeline Manager" tab is active,
        the pipeline manager's undo function is invoked.
        """
        tab_name = self.tabs.tabText(self.tabs.currentIndex()).replace(
            "&", "", 1
        )

        if tab_name == "Data Browser":
            # In Data Browser
            self.project.undo(self.data_browser.table_data)
            # Action reverted in the Database

        elif tab_name == "Pipeline Manager":
            # In Pipeline Manager
            self.pipeline_manager.undo()

    def update_project(self, file_path, call_update_table=True):
        """
        Updates the project after a database change.

        This method updates the database, the window title, and the recent
        and saved projects menus.

        :param file_path (str): The file path of the new project.
        :param call_update_table (bool): Whether to update the table data.
                                         Defaults to True.
        """

        self.data_browser.update_database(self.project)
        # Database update data_browser
        self.pipeline_manager.update_project(self.project)

        if call_update_table:
            self.data_browser.table_data.update_table()  # Table updated

        # Update window title
        self.projectName = (
            "Unnamed project"
            if self.project.isTempProject
            else self.project.getName()
        )
        self.setWindowTitle(f"{self.windowName}{self.projectName}")

        # List of project updated
        if not self.test and not self.project.isTempProject:
            self.saved_projects_list = self.saved_projects.addSavedProject(
                file_path
            )
        self.update_recent_projects_actions()

    def update_recent_projects_actions(self):
        """
        Updates the list of recent projects in the UI.

        Hides all recent project actions first, then updates and displays
        the most recent ones based on the configured maximum.
        """
        max_projects = self.config.get_max_projects()

        # Hide all project actions
        for action in self.saved_projects_actions[:max_projects]:
            action.setVisible(False)

        # Update recent projects if available
        for i, project in enumerate(self.saved_projects_list[:max_projects]):
            self.saved_projects_actions[i].setText(os.path.basename(project))
            self.saved_projects_actions[i].setData(project)
            self.saved_projects_actions[i].setVisible(True)
