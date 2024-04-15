# -*- coding: utf-8 -*-
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
from populse_mia.data_manager.project import (
    COLLECTION_CURRENT,
    TAG_HISTORY,
    Project,
)

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

CLINICAL_TAGS = [
    "Site",
    "Spectro",
    "MR",
    "PatientRef",
    "Pathology",
    "Age",
    "Sex",
    "Message",
]


console_shell_running = False
_ipsubprocs_lock = threading.RLock()
_ipsubprocs = []


class _ProcDeleter(threading.Thread):
    """Used by open_shell."""

    def __init__(self, o):
        threading.Thread.__init__(self)
        self.o = o

    def __del__(self):
        """Blabla"""

        try:
            self.o.kill()
        except Exception:
            pass
        if getattr(self, "console", False):
            global console_shell_running
            console_shell_running = False

    def run(self):
        """Blabla"""

        try:
            self.o.communicate()
        except Exception as e:
            print("exception in ipython process:", e)
        global _ipsubprocs
        try:
            with _ipsubprocs_lock:
                _ipsubprocs.remove(self)
        except Exception:
            pass


class MainWindow(QMainWindow):
    """Initialize software appearance and define interactions with the user.

    .. Methods:
        - __init__ : initialise the object MainWindow
        - add_clinical_tags: add the clinical tags to the database and the
                             data browser
        - check_unsaved_modifications: check if there are differences
          between the current project and the database
        - check_database: check if files in database have been modified or
                          removed since they have been converted for the
                          first time
        - closeEvent: override the closing event to check if there are
          unsaved modifications
        - create_view_actions: create the actions in each menu
        - create_view_menus: create the menu-bar
        - create_view_window: create the main window view
        - create_project_pop_up: create a new project
        - create_tabs: create the tabs
        - credits: open the credits in a web browser
        - del_clinical_tags: Remove the clinical tags to the database and the
                             data browser
        - documentation: open the documentation in a web browser
        - get_controller_version: returns controller_version_changed attribute
        - import_data: call the import software (MRI File Manager)
        - install_processes_pop_up: open the install processes pop-up
        - open_project_pop_up: open a pop-up to open a project and updates
          the recent projects
        - open_recent_project: open a recent project
        - package_library_pop_up: open the package library pop-up
        - project_properties_pop_up: open the project properties pop-up
        - redo: redo the last action made by the user
        - remove_raw_files_useless: remove the useless raw files of the
          current project
        - save: save either the current project or the current pipeline
        - save_as: save either the current project or the current pipeline
          under a new name
        - save_project_as: open a pop-up to save the current project as
        - saveChoice: checks if the project needs to be saved as or just saved
        - see_all_projects: open a pop-up to show the recent projects
        - set_controller_version: Reverses controller_version_changed attribute
        - software_preferences_pop_up: open the Mia preferences pop-up
        - switch_project: switches project if it's possible
        - tab_changed: method called when the tab is changed
        - undo: undoes the last action made by the user
        - update_package_library_action: update the package library action
          depending on the mode
        - update_project: update the project once the database has been
          updated
        - update_recent_projects_actions: update the list of recent projects

    """

    def __init__(self, project, test=False, deleted_projects=None):
        """Main window class, initializes the software appearance and defines
        interactions with the user.

            :Parameter:
                - :project: current project in the software
                - :test: boolean if the widget is launched from unit tests
                     or not
                - :deleted_projects: projects that have been deleted

        """
        super(MainWindow, self).__init__()

        QApplication.restoreOverrideCursor()

        # We associate these methods and the instance to be able to call them
        # from anywhere.
        QCoreApplication.instance().title = self.windowTitle
        QCoreApplication.instance().set_title = self.setWindowTitle

        if deleted_projects is not None and deleted_projects:
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
        sources_images_dir = Config().getSourceImageDir()
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

        # Connect actions & menus views
        self.create_view_actions()
        self.create_view_menus()

        # Create Tabs
        self.create_tabs()
        self.setCentralWidget(self.centralWindow)
        if self.config.get_mainwindow_maximized():
            self.showMaximized()
        else:
            size = self.config.get_mainwindow_size()
            if size:
                self.resize(size[0], size[1])

    @staticmethod
    def last_window_closed():
        """Force exit the event loop after ipython console is closed.

        If the ipython console has been run, something prevents Qt from
        quitting after the window is closed. The cause is not known yet.
        So: force exit the event loop.
        """

        from soma.qt_gui.qt_backend import Qt

        Qt.QTimer.singleShot(10, Qt.qApp.exit)

    def add_clinical_tags(self):
        """Add the clinical tags to the database and the data browser"""

        added_tags = self.project.add_clinical_tags()

        for tag in added_tags:
            column = self.data_browser.table_data.get_index_insertion(tag)
            self.data_browser.table_data.add_column(column, tag)
            # self.project.unsavedModifications = True

    def check_unsaved_modifications(self):
        """Check if there are differences between the current project and the
        database.

        :return: Boolean. True if there are unsaved modifications,
           False otherwise
        """
        if self.project.isTempProject:
            if (
                len(
                    self.project.session.get_documents_names(
                        COLLECTION_CURRENT
                    )
                )
                > 0
            ):
                return True
            else:
                return False
        elif self.project.hasUnsavedModifications():
            return True
        else:
            return False

    def check_database(self):
        """Check if files in database have been modified since first import."""

        if self.project is None:
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        print("verify scans...")
        t0 = time.time()
        problem_list = data_loader.verify_scans(self.project)
        print("check time:", time.time() - t0)

        QApplication.restoreOverrideCursor()

        # Message if invalid files
        if problem_list:
            str_msg = ""
            for element in problem_list:
                str_msg += element + "\n\n"
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

    def closeEvent(self, event):
        """Override the QWidget closing event to check if there are unsaved
        modifications

        :param event: closing event
        """
        if self.check_unsaved_modifications() is False or self.test:
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
                    "A change of controller version, from {0} to {1}, "
                    "is planned for next start-up. Do you confirm that "
                    "you would like to perform this "
                    "change?".format(
                        "V1" if config.isControlV1() else "V2",
                        "V2" if config.isControlV1() else "V1",
                    )
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
        else:
            event.ignore()

        if self.data_browser.viewer:
            self.data_browser.viewer.clear()

        if self.data_viewer:
            self.data_viewer.clear()

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
        # if Config().get_user_mode() == True:
        #     self.action_package_library.setDisabled(True)
        # else:
        #     self.action_package_library.setEnabled(True)

        if Config().get_user_mode() is True:
            self.action_delete_project.setDisabled(True)
        else:
            self.action_delete_project.setEnabled(True)

        self.action_exit.setShortcut("Ctrl+W")

        self.action_undo.setShortcut("Ctrl+Z")

        self.action_redo.setShortcut("Ctrl+Y")

        # if Config().get_user_mode() == True:
        #     self.action_install_processes.setDisabled(True)
        # else:
        #     self.action_install_processes.setEnabled(True)

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
            self.windowName += " (Admin mode)"
        self.windowName += " - "

        self.setStyleSheet(
            "background-color:"
            + background_color
            + ";color:"
            + text_color
            + ";"
        )
        self.statusBar().showMessage(
            "Please create a new project (Ctrl+N) or "
            "open an existing project (Ctrl+O)"
        )

        self.setWindowTitle(self.windowName + self.projectName)

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
                print("\ncreate_project_pop_up: ", e)
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Critical)
                self.msg.setText("Invalid projects folder path")
                self.msg.setInformativeText(
                    "The projects folder path in MIA preferences is invalid!"
                )
                self.msg.setWindowTitle("Error")
                yes_button = self.msg.addButton(
                    "Open MIA preferences", QMessageBox.YesRole
                )
                self.msg.addButton(QMessageBox.Ok)
                self.msg.exec()

                if self.msg.clickedButton() == yes_button:
                    self.software_preferences_pop_up()
                    self.msg.close()

                else:
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

                    self.remove_raw_files_useless()  # We remove the useless
                    # files from the old project

                    self.project = Project(self.exPopup.relative_path, True)

                    self.update_project(
                        file_name
                    )  # project updated everywhere

    def create_tabs(self):
        """Create the tabs and initializes the DataBrowser and PipelineManager
        classes."""
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
            # self.project.unsavedModifications = True

    def delete_project(self):
        """Open a pop-up to open a project and updates the recent projects."""

        try:
            self.exPopup = PopUpDeleteProject(self)

        except Exception as e:
            print("\ndelete_project: ", e)
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("Invalid projects folder path")
            self.msg.setInformativeText(
                "The projects folder path in MIA preferences is invalid!"
            )
            self.msg.setWindowTitle("Error")
            yes_button = self.msg.addButton(
                "Open MIA preferences", QMessageBox.YesRole
            )
            self.msg.addButton(QMessageBox.Ok)
            self.msg.exec()

            if self.msg.clickedButton() == yes_button:
                self.software_preferences_pop_up()
                self.msg.close()

            else:
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

    def import_data(self):
        """Call the import software (MRI File Manager), reads the imported
        files and loads them into the database.

        """
        # Opens the conversion software to convert the MRI files in Nifti/Json
        config = Config()
        home = expanduser("~")
        print("\nmri_conv opening ...\n")

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
                    "[ProjectsDir] " + home,
                    "[ExportNifti] "
                    + os.path.join(self.project.folder, "data", "raw_data"),
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
            print(
                "\nMri_conv: Test with lower maximum heap "
                "size (4096M -> 1024M)...\n"
            )
            code_exit = subprocess.call(
                [
                    "java",
                    "-Xmx1024M",
                    "-jar",
                    config.get_mri_conv_path(),
                    "[ProjectsDir] " + home,
                    "[ExportNifti] "
                    + os.path.join(self.project.folder, "data", "raw_data"),
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
            documents = self.project.session.get_documents_names(
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
            print(
                "\nmri_conv, did not work properly. Current absolute"
                "path to MRIManager.jar defined in File > MIA Preferences:"
                "\n{0}\n".format(config.get_mri_conv_path())
            )

            if not os.path.isfile(config.get_mri_conv_path()):
                mssgText = (
                    "Warning: mri_conv did not work properly. The "
                    "current absolute path to MRIManager.jar doesn't "
                    "seem to be correctly defined.\nCurrent absolute "
                    "path to MRIManager.jar defined in\nFile > MIA "
                    "Preferences:\n{0}".format(config.get_mri_conv_path())
                )

            else:
                mssgText = (
                    "Warning : mri_conv did not work properly. Please "
                    "check if the currently installed mri_conv Java "
                    "ARchive is not corrupted.\nCurrent absolute path "
                    "to MRIManager.jar defined in\nFile > MIA "
                    "Preferences:\n{0}".format(config.get_mri_conv_path())
                )

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("populse_mia - Warning: Data import issue!")
            msg.setText(mssgText)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()

    def open_project_pop_up(self):
        """Open a pop-up to open a project and updates the recent projects."""
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
                print("\nopen_project_pop_up: ", e)
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Critical)
                self.msg.setText("Invalid projects folder path")
                self.msg.setInformativeText(
                    "The projects folder path in MIA preferences is invalid!"
                )
                self.msg.setWindowTitle("Error")
                yes_button = self.msg.addButton(
                    "Open MIA preferences", QMessageBox.YesRole
                )
                self.msg.addButton(QMessageBox.Ok)
                self.msg.exec()

                if self.msg.clickedButton() == yes_button:
                    self.software_preferences_pop_up()
                    self.msg.close()

                else:
                    self.msg.close()

            else:
                if self.exPopup.exec():
                    project_name = self.exPopup.selectedFiles()
                    self.exPopup.get_filename(project_name)
                    project_name = self.exPopup.relative_path
                    self.data_browser.data_sent = False

                    # We switch the project
                    self.switch_project(project_name, self.exPopup.name)
                    field_names = self.project.session.get_fields_names(
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
                field_names = self.project.session.get_fields_names(
                    COLLECTION_CURRENT
                )
                documents = self.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )
                self.data_viewer.set_documents(self.project, documents)

                if all(ele in field_names for ele in CLINICAL_TAGS):
                    Config().set_clinical_mode(True)

                else:
                    Config().set_clinical_mode(False)

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

        old_tags = self.project.session.get_shown_tags()
        self.pop_up_settings = PopUpProperties(
            self.project, self.data_browser, old_tags
        )
        self.pop_up_settings.setGeometry(300, 200, 800, 600)
        self.pop_up_settings.show()

        if self.pop_up_settings.exec():
            self.data_browser.table_data.update_visualized_columns(
                old_tags, self.project.session.get_shown_tags()
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

        # If it's unnamed project, we can remove the whole project
        if self.project.isTempProject:
            # close database, and files
            self.project.session = None
            self.project.database.__exit__(None, None, None)
            self.project.database = None
            shutil.rmtree(folder)

        else:
            # I don't understand why files from raw_data are automatically
            # transferred to derived_data, if they are not in db. I comment
            # on this feature in the following lines. We can uncomment if
            # this action makes sense ...
            # for filename in glob.glob(
            #    os.path.join(os.path.abspath(folder), "data", "raw_data", "*")
            # ):
            #    scan = os.path.basename(filename)
            #    # The file is removed only if it's not a scan in the project,
            #    # and if it's not a logExport
            #    # Json files associated to nii files are kept for the raw_
            #    # data folder
            #    file_name, file_extension = os.path.splitext(scan)
            #    file_in_database = False
            #
            #    for database_scan in self.project.session.get_documents_names(
            #        COLLECTION_CURRENT
            #    ):
            #        if file_name in database_scan:
            #            file_in_database = True
            #
            #    if "logExport" in scan:
            #        file_in_database = True
            #
            #    if not file_in_database:
            #        os.rename(filename, filename.replace("raw_data",
            #                                             "derived_data"))

            # I don't understand why files from derived_data are automatically
            # deleted if they are not in db. I comment on this feature in the
            # following lines. We can uncomment if this action makes sense ...
            # for filename in glob.glob(
            #         os.path.join(os.path.relpath(
            #             self.project.folder), 'data', 'derived_data', '*')):
            #     scan = os.path.basename(filename)
            #     # The file is removed only if it's not a scan in the project,
            #     # and if it's not a logExport
            #     if (self.project.session.get_document(
            #             COLLECTION_CURRENT, os.path.join(
            #                 "data", "derived_data", scan)) is None and
            #             "logExport" not in scan):
            #         os.remove(filename)

            # I don't understand why files in downloaded_data are
            # automatically deleted if they are not in db. I comment on this
            # feature in the following line. We can uncomment if this action
            # makes sense...
            # for filename in glob.glob(
            #     os.path.join(
            #        os.path.abspath(self.project.folder),
            #        "data",
            #        "downloaded_data",
            #        "*",
            #    )
            # ):
            #    scan = os.path.basename(filename)
            #
            #    # The file is removed only if it's not a scan in the project,
            #    # and if it's not a logExport
            #    if (
            #        self.project.session.get_document(
            #            COLLECTION_CURRENT,
            #            os.path.join("data", "downloaded_data", scan),
            #        )
            #        is None
            #        and "logExport" not in scan
            #    ):
            #        os.remove(filename)
            #        self.project.unsavedModifications = True

            # close database, and files
            self.project.session = None
            self.project.database.__exit__(None, None, None)
            self.project.database = None

        self.project = None

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
            print("\nsave_project_as: ", e)
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("Invalid projects folder path")
            self.msg.setInformativeText(
                "The projects folder path in MIA preferences is invalid!"
            )
            self.msg.setWindowTitle("Error")
            yes_button = self.msg.addButton(
                "Open MIA preferences", QMessageBox.YesRole
            )
            self.msg.addButton(QMessageBox.Ok)
            self.msg.exec()

            if self.msg.clickedButton() == yes_button:
                self.software_preferences_pop_up()
                self.msg.close()

            else:
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
                    # os.mkdir(derived_data_path)
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

                    # for filename in glob.glob(
                    #     os.path.join(old_folder, "data", "derived_data", "*")
                    # ):
                    #     shutil.copy(
                    #         filename, os.path.join(data_path, "derived_data")
                    #     )
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

                # First we register the Database before commiting the last
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

                # We copy the Database with all the modifications commited in
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

        # Modifying the options in the Pipeline Manager
        # (verify if user mode)
        self.pop_up_preferences.signal_preferences_change.connect(
            self.pipeline_manager.update_user_mode
        )
        # self.pop_up_preferences.signal_preferences_change.connect(
        #     self.update_package_library_action)

    def open_shell(self):
        """Open a Qt console shell with an IPython kernel seeing the program
        internals
        """

        from soma.qt_gui import qt_backend

        ipfunc = None
        mode = "qtconsole"
        print("startShell")

        try:
            # to check it is installed
            import jupyter_core.application  # noqa: F401
            import qtconsole  # noqa: F401

            ipfunc = (
                "from jupyter_core import application; "
                "app = application.JupyterApp(); app.initialize(); app.start()"
            )

        except ImportError:
            print("failed to run Qt console")
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
                    'import os; os.environ["QT_API"] = "%s"; %s'
                    % (qt_api_code, ipfunc),
                    mode,
                    "--existing",
                    "--shell=%d" % ipConsole.shell_port,
                    "--iopub=%d" % ipConsole.iopub_port,
                    "--stdin=%d" % ipConsole.stdin_port,
                    "--hb=%d" % ipConsole.hb_port,
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

    @staticmethod
    def run_ipconsole_kernel(mode="qtconsole"):
        """blabla"""

        print("run_ipconsole_kernel:", mode)
        import IPython  # noqa: F401
        from IPython.lib import guisupport
        from soma.qt_gui.qt_backend import Qt

        qtapp = Qt.QApplication.instance()
        qtapp._in_event_loop = True
        guisupport.in_event_loop = True
        # ipversion = [int(x) for x in IPython.__version__.split(".")]

        from ipykernel.kernelapp import IPKernelApp

        app = IPKernelApp.instance()

        if not app.initialized() or not app.kernel:
            print("runing IP console kernel")
            app.hb_port = 50042  # don't know why this is not set automatically
            app.initialize(
                [
                    mode,
                    "--gui=qt",  # '--pylab=qt',
                    "--KernelApp.parent_appname='ipython-%s'" % mode,
                ]
            )
            # in ipython >= 1.2, app.start() blocks until a ctrl-c is issued in
            # the terminal. Seems to block in tornado.ioloop.PollIOLoop.start()
            #
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
                    """Blabla"""

                    if hasattr(self, "_callbacks"):
                        ncallbacks = len(self._callbacks)
                        for i in range(ncallbacks):
                            self._run_callback(self._callbacks.popleft())

            else:

                def my_start_ioloop_callbacks(self):
                    """Blabla"""

                    with self._callback_lock:
                        callbacks = self._callbacks
                        self._callbacks = []

                    for callback in callbacks:
                        self._run_callback(callback)

            my_start_ioloop_callbacks(ioloop.IOLoop.instance())

        return app

    def switch_project(self, file_path, name):
        """Check if it's possible to open the selected project
        and quit the current one.

        :param file_path: raw file_path
        :param name: project name

        :return: Boolean
        """
        # /!\ file_path and path are the same param

        # Switching project only if it's a different one
        if file_path != self.project.folder:
            # If the file exists
            if os.path.exists(os.path.join(file_path)):
                # If it is a MIA project
                if (
                    os.path.exists(
                        os.path.join(file_path, "properties", "properties.yml")
                    )
                    and os.path.exists(
                        os.path.join(file_path, "database", "mia.db")
                    )
                    and os.path.exists(
                        os.path.join(file_path, "data", "raw_data")
                    )
                    and os.path.exists(
                        os.path.join(file_path, "data", "derived_data")
                    )
                    and os.path.exists(
                        os.path.join(file_path, "data", "downloaded_data")
                    )
                    and os.path.exists(os.path.join(file_path, "filters"))
                ):
                    # We check if the name of the project directory is the
                    # same in its properties
                    with open(
                        os.path.join(
                            file_path, "properties", "properties.yml"
                        ),
                        "r+",
                    ) as stream:
                        if version.parse(yaml.__version__) > version.parse(
                            "5.1"
                        ):
                            properties = yaml.load(
                                stream, Loader=yaml.FullLoader
                            )

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

                    except IOError:
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("project already opened")
                        msg.setInformativeText(
                            "The project at "
                            + str(file_path)
                            + " is already opened in another "
                            "instance of the software."
                        )
                        msg.setWindowTitle("Warning")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.buttonClicked.connect(msg.close)
                        msg.exec()
                        return False

                    # We check for valid version of the project

                    if not (temp_database.session.get_fields_names)(
                        COLLECTION_CURRENT
                    ) or (
                        TAG_HISTORY
                        not in (temp_database.session.get_fields_names)(
                            COLLECTION_CURRENT
                        )
                    ):
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText(
                            "The project cannot be read by Mia. Please check "
                            "if the version of the project is compatible with "
                            "the version of the running mia..."
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

                # Not a MIA project
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText(
                        "The project selected isn't a valid MIA project"
                    )
                    msg.setInformativeText(
                        "The project selected " + name + " isn't a MIA project"
                        ".\nPlease select a "
                        "valid one."
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
                    "The project selected " + name + " doesn't exist anymore."
                    "\nPlease select "
                    "another one."
                )
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                return False

    def tab_changed(self):
        """Update the window when the tab is changed."""

        if (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Data Browser"
        ):
            # data_browser refreshed after working with pipelines
            old_scans = self.data_browser.table_data.scans_to_visualize
            documents = self.project.session.get_documents_names(
                COLLECTION_CURRENT
            )

            self.data_browser.table_data.add_columns()
            self.data_browser.table_data.fill_headers()

            self.data_browser.table_data.add_rows(documents)

            self.data_browser.table_data.scans_to_visualize = documents
            self.data_browser.table_data.scans_to_search = documents

            self.data_browser.table_data.itemChanged.disconnect()
            self.data_browser.table_data.fill_cells_update_table()
            self.data_browser.table_data.itemChanged.connect(
                self.data_browser.table_data.change_cell_color
            )

            self.data_browser.table_data.update_visualized_rows(old_scans)

            # Advanced search + search_bar opened
            old_search = self.project.currentFilter.search_bar
            self.data_browser.reset_search_bar()
            self.data_browser.search_bar.setText(old_search)

            if len(self.project.currentFilter.nots) > 0:
                self.data_browser.frame_advanced_search.setHidden(False)
                self.data_browser.advanced_search.scans_list = (
                    self.data_browser.table_data.scans_to_visualize
                )
                self.data_browser.advanced_search.show_search()
                self.data_browser.advanced_search.apply_filter(
                    self.project.currentFilter
                )

        elif (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Data Viewer"
        ):
            self.data_viewer.load_viewer(self.data_viewer.current_viewer())
            documents = self.project.session.get_documents_names(
                COLLECTION_CURRENT
            )
            self.data_viewer.set_documents(self.project, documents)

        elif (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Pipeline Manager"
        ):
            if self.data_browser.data_sent is False:
                scans = self.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )
                self.pipeline_manager.scan_list = scans
                self.pipeline_manager.nodeController.scan_list = scans
                self.pipeline_manager.pipelineEditorTabs.scan_list = scans
            self.pipeline_manager.pipelineEditorTabs.update_scans_list()
            self.pipeline_manager.update_user_buttons_states()

            # fmt: off
            if (
                self.pipeline_manager.pipelineEditorTabs.
                    get_current_editor().iterated_tag
            ):
                self.pipeline_manager.iterationTable.update_iterated_tag(
                    self.pipeline_manager.pipelineEditorTabs.
                    get_current_editor().iterated_tag
                )
            # fmt: on

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
        """Undo the last action made by the user."""
        if (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Data Browser"
        ):
            # In Data Browser
            self.project.undo(self.data_browser.table_data)
            # Action reverted in the Database
        elif (
            self.tabs.tabText(self.tabs.currentIndex()).replace("&", "", 1)
            == "Pipeline Manager"
        ):
            # In Pipeline Manager
            self.pipeline_manager.undo()

    # def update_package_library_action(self):
    #     """Update the package library action depending on the mode."""
    #     if Config().get_user_mode() == True:
    #         self.action_package_library.setDisabled(True)
    #         # self.action_install_processes.setDisabled(True)
    #     else:
    #         self.action_package_library.setEnabled(True)
    #         # self.action_install_processes.setEnabled(True)

    def update_project(self, file_path, call_update_table=True):
        """Update the project once the database has been updated.
        Update the database, the window title and the recent and saved
        projects menus.

        :param file_path: File name of the new project
        :param call_update_table: boolean, True if we need to call
        """

        self.data_browser.update_database(self.project)

        # Database update data_browser
        self.pipeline_manager.update_project(self.project)

        if call_update_table:
            self.data_browser.table_data.update_table()  # Table updated

        # Window name updated
        if self.project.isTempProject:
            self.projectName = "Unnamed project"
        else:
            self.projectName = self.project.getName()
        self.setWindowTitle(self.windowName + self.projectName)

        # List of project updated
        if not self.test and not self.project.isTempProject:
            self.saved_projects_list = self.saved_projects.addSavedProject(
                file_path
            )
        self.update_recent_projects_actions()

    def update_recent_projects_actions(self):
        """Update the list of recent projects."""
        for j in range(0, self.config.get_max_projects()):
            self.saved_projects_actions[j].setVisible(False)
        if self.saved_projects_list:
            if len(self.saved_projects_list) > 0:
                for i in range(
                    min(
                        len(self.saved_projects_list),
                        self.config.get_max_projects(),
                    )
                ):
                    text = os.path.basename(self.saved_projects_list[i])
                    self.saved_projects_actions[i].setText(text)
                    self.saved_projects_actions[i].setData(
                        self.saved_projects_list[i]
                    )
                    self.saved_projects_actions[i].setVisible(True)
