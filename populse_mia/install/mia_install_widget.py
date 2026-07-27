"""The module used for mia's installation and configuration.

Basically, this module is dedicated to the GUI used at the installation time

:Contains:
    :Class:
        - MIAInstallWidget
"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################


import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from PyQt5 import QtCore, QtGui, QtWidgets


###############################################################################
# Currently in host installation, we make installation from sources for capsul,
# soma-base and soma-workflow.
# We'll have to switch to using pypi for these packages when master will be on
# V3 in populse.
###############################################################################
class MIAInstallWidget(QtWidgets.QWidget):
    """The main class for mia's installation and configuration.

    :Contains:
        :Method:
            - __init__
            - browse_matlab
            - browse_matlab_standalone
            - browse_mia_config_path
            - browse_projects_path
            - browse_spm
            - browse_spm_standalone
            - btnstate
            - clone_miaResources
            - find_matlab_path
            - install
            - install_matlab_api
            - install_package
            - last_layout
            - make_mrifilemanager_folder
            - ok_or_abort
            - set_new_layout
            - uninstall_package
            - upgrade_soma_capsul
            - use_matlab_changed
            - use_spm_changed
            - use_spm_standalone_changed
    """

    def __init__(self):
        """Constructor"""
        super().__init__()
        # Check if running in a virtual environment
        self.is_venv = sys.prefix != sys.base_prefix
        self.matlab_path = ""
        self.top_label_font = QtGui.QFont()
        self.top_label_font.setBold(True)

        self.middle_label_text = (
            "Please select a configuration installation "
            "path, a folder to store the projects and "
            "the paths to run Matlab and SPM.\nThe "
            "paths to Matlab and SPM can then be "
            "modified in the Mia preferences.\n\n"
        )
        self.middle_label = QtWidgets.QLabel(self.middle_label_text)
        h_box_middle_label = QtWidgets.QHBoxLayout()
        h_box_middle_label.addStretch(1)
        h_box_middle_label.addWidget(self.middle_label)
        h_box_middle_label.addStretch(1)

        # Groupbox
        self.groupbox = QtWidgets.QGroupBox()
        self.mia_config_path_label = QtWidgets.QLabel(
            "Mia configuration path:"
        )
        self.mia_config_path_choice = QtWidgets.QLineEdit(
            os.path.join(os.path.expanduser("~"), ".populse_mia")
        )
        self.mia_config_path_browse = QtWidgets.QPushButton("Browse")
        self.mia_config_path_browse.clicked.connect(
            self.browse_mia_config_path
        )

        self.mia_config_path_info = QtWidgets.QPushButton(" ? ")
        self.mia_config_path_info.setFixedHeight(27)
        self.mia_config_path_info.setFixedWidth(27)
        self.mia_config_path_info.setStyleSheet(
            "background-color:rgb(150,150,200)"
        )
        rect = QtCore.QRect(4, 4, 17, 17)
        region = QtGui.QRegion(rect, QtGui.QRegion.Ellipse)
        self.mia_config_path_info.setMask(region)
        tool_tip_message = (
            "Three folders will be created in the selected "
            "folder:\n"
            "- usr/properties: containing Mia's configuration "
            "and resources files.\n"
            "- usr/processes: containing personal pipelines "
            "and bricks.\n"
            "- usr/MRIFileManager: containing the data "
            "converter used in Mia.\n"
            "- usr/MiaResources: containing reference data "
            "(ROI, templates, etc.)"
        )
        self.mia_config_path_info.setToolTip(tool_tip_message)

        h_box_mia_config = QtWidgets.QHBoxLayout()
        h_box_mia_config.addWidget(self.mia_config_path_choice)
        h_box_mia_config.addWidget(self.mia_config_path_browse)
        h_box_mia_config.addWidget(self.mia_config_path_info)

        v_box_mia_config = QtWidgets.QVBoxLayout()
        v_box_mia_config.addWidget(self.mia_config_path_label)
        v_box_mia_config.addLayout(h_box_mia_config)

        projects_path_default = os.path.join(
            os.path.expanduser("~"), "Documents", "user_mia_projects"
        )

        self.projects_path_label = QtWidgets.QLabel("Mia projects path:")
        self.projects_path_choice = QtWidgets.QLineEdit(projects_path_default)
        self.projects_path_browse = QtWidgets.QPushButton("Browse")
        self.projects_path_browse.clicked.connect(self.browse_projects_path)

        self.projects_path_info = QtWidgets.QPushButton(" ? ")
        self.projects_path_info.setFixedHeight(27)
        self.projects_path_info.setFixedWidth(27)
        self.projects_path_info.setStyleSheet(
            "background-color:" "rgb(150,150,200)"
        )
        rect = QtCore.QRect(4, 4, 17, 17)
        region = QtGui.QRegion(rect, QtGui.QRegion.Ellipse)
        self.projects_path_info.setMask(region)
        tool_tip_message = (
            'A "projects" folder will be created in this ' "specified folder."
        )
        self.projects_path_info.setToolTip(tool_tip_message)

        h_box_projects_path = QtWidgets.QHBoxLayout()
        h_box_projects_path.addWidget(self.projects_path_choice)
        h_box_projects_path.addWidget(self.projects_path_browse)
        h_box_projects_path.addWidget(self.projects_path_info)

        v_box_projects_path = QtWidgets.QVBoxLayout()
        v_box_projects_path.addWidget(self.projects_path_label)
        v_box_projects_path.addLayout(h_box_projects_path)

        v_box_paths = QtWidgets.QVBoxLayout()
        v_box_paths.addLayout(v_box_mia_config)
        v_box_paths.addLayout(v_box_projects_path)

        self.groupbox.setLayout(v_box_paths)

        # Installation target groupbox
        self.install_target_group_box = QtWidgets.QGroupBox(
            "Installation target:"
        )

        self.casa_target_push_button = QtWidgets.QRadioButton("Casa_Distro")
        self.casa_target_push_button.toggled.connect(
            lambda: self.btnstate(self.casa_target_push_button)
        )
        self.host_target_push_button = QtWidgets.QRadioButton("Host")
        self.host_target_push_button.setChecked(True)
        self.host_target_push_button.toggled.connect(
            lambda: self.btnstate(self.host_target_push_button)
        )

        v_box_install_target = QtWidgets.QVBoxLayout()
        v_box_install_target.addWidget(self.casa_target_push_button)
        v_box_install_target.addWidget(self.host_target_push_button)

        self.install_target_group_box.setLayout(v_box_install_target)

        h_box_install_target = QtWidgets.QVBoxLayout()
        h_box_install_target.addWidget(self.install_target_group_box)
        h_box_install_target.addStretch(1)

        # Clinical mode groupbox
        self.clinical_mode_group_box = QtWidgets.QGroupBox("Operating mode:")

        self.clinical_mode_push_button = QtWidgets.QRadioButton(
            "Clinical mode"
        )
        self.clinical_mode_push_button.toggled.connect(
            lambda: self.btnstate(self.clinical_mode_push_button)
        )

        v_box_clinical_mode = QtWidgets.QVBoxLayout()
        v_box_clinical_mode.addWidget(self.clinical_mode_push_button)

        self.clinical_mode_group_box.setLayout(v_box_clinical_mode)

        h_box_clinical_mode = QtWidgets.QVBoxLayout()
        h_box_clinical_mode.addWidget(self.clinical_mode_group_box)
        h_box_clinical_mode.addStretch(1)

        # Push buttons
        self.push_button_install = QtWidgets.QPushButton("Install")
        self.push_button_install.clicked.connect(self.install)

        self.push_button_cancel = QtWidgets.QPushButton("Cancel")
        self.push_button_cancel.clicked.connect(self.close)

        h_box_buttons = QtWidgets.QHBoxLayout()
        h_box_buttons.addStretch(1)
        h_box_buttons.addWidget(self.push_button_install)
        h_box_buttons.addWidget(self.push_button_cancel)

        # Matlab and SPM12 groupboxes
        # Groupbox "Matlab"
        self.groupbox_matlab = QtWidgets.QGroupBox("Matlab")
        self.use_matlab_label = QtWidgets.QLabel("Use Matlab")
        self.use_matlab_checkbox = QtWidgets.QCheckBox("", self)

        matlab_path = self.find_matlab_path()
        self.matlab_label = QtWidgets.QLabel("Matlab path:")
        self.matlab_choice = QtWidgets.QLineEdit(matlab_path)
        self.matlab_browse = QtWidgets.QPushButton("Browse")
        self.matlab_browse.clicked.connect(self.browse_matlab)

        self.matlab_standalone_label = QtWidgets.QLabel(
            "Matlab standalone " "path:"
        )
        self.matlab_standalone_choice = QtWidgets.QLineEdit()
        self.matlab_standalone_browse = QtWidgets.QPushButton("Browse")
        self.matlab_standalone_browse.clicked.connect(
            self.browse_matlab_standalone
        )

        h_box_use_matlab = QtWidgets.QHBoxLayout()
        h_box_use_matlab.addWidget(self.use_matlab_checkbox)
        h_box_use_matlab.addWidget(self.use_matlab_label)
        h_box_use_matlab.addStretch(1)

        h_box_matlab_path = QtWidgets.QHBoxLayout()
        h_box_matlab_path.addWidget(self.matlab_choice)
        h_box_matlab_path.addWidget(self.matlab_browse)

        v_box_matlab_path = QtWidgets.QVBoxLayout()
        v_box_matlab_path.addWidget(self.matlab_label)
        v_box_matlab_path.addLayout(h_box_matlab_path)

        h_box_matlab_standalone_path = QtWidgets.QHBoxLayout()
        h_box_matlab_standalone_path.addWidget(self.matlab_standalone_choice)
        h_box_matlab_standalone_path.addWidget(self.matlab_standalone_browse)

        v_box_matlab_standalone_path = QtWidgets.QVBoxLayout()
        v_box_matlab_standalone_path.addWidget(self.matlab_standalone_label)
        v_box_matlab_standalone_path.addLayout(h_box_matlab_standalone_path)

        v_box_matlab = QtWidgets.QVBoxLayout()
        v_box_matlab.addLayout(h_box_use_matlab)
        v_box_matlab.addLayout(v_box_matlab_path)
        v_box_matlab.addLayout(v_box_matlab_standalone_path)

        self.groupbox_matlab.setLayout(v_box_matlab)

        # Groupbox "SPM"
        self.groupbox_spm = QtWidgets.QGroupBox("SPM")

        self.use_spm_label = QtWidgets.QLabel("Use SPM")
        self.use_spm_checkbox = QtWidgets.QCheckBox("", self)

        self.spm_label = QtWidgets.QLabel("SPM path:")
        self.spm_choice = QtWidgets.QLineEdit()
        self.spm_browse = QtWidgets.QPushButton("Browse")
        self.spm_browse.clicked.connect(self.browse_spm)

        h_box_use_spm = QtWidgets.QHBoxLayout()
        h_box_use_spm.addWidget(self.use_spm_checkbox)
        h_box_use_spm.addWidget(self.use_spm_label)
        h_box_use_spm.addStretch(1)

        h_box_spm_path = QtWidgets.QHBoxLayout()
        h_box_spm_path.addWidget(self.spm_choice)
        h_box_spm_path.addWidget(self.spm_browse)

        v_box_spm_path = QtWidgets.QVBoxLayout()
        v_box_spm_path.addWidget(self.spm_label)
        v_box_spm_path.addLayout(h_box_spm_path)

        self.use_spm_standalone_label = QtWidgets.QLabel("Use SPM standalone")
        self.use_spm_standalone_checkbox = QtWidgets.QCheckBox("", self)

        self.spm_standalone_label = QtWidgets.QLabel("SPM standalone path:")
        self.spm_standalone_choice = QtWidgets.QLineEdit()
        self.spm_standalone_browse = QtWidgets.QPushButton("Browse")
        self.spm_standalone_browse.clicked.connect(self.browse_spm_standalone)

        h_box_use_spm_standalone = QtWidgets.QHBoxLayout()
        h_box_use_spm_standalone.addWidget(self.use_spm_standalone_checkbox)
        h_box_use_spm_standalone.addWidget(self.use_spm_standalone_label)
        h_box_use_spm_standalone.addStretch(1)

        h_box_spm_standalone_path = QtWidgets.QHBoxLayout()
        h_box_spm_standalone_path.addWidget(self.spm_standalone_choice)
        h_box_spm_standalone_path.addWidget(self.spm_standalone_browse)

        v_box_spm_standalone_path = QtWidgets.QVBoxLayout()
        v_box_spm_standalone_path.addWidget(self.spm_standalone_label)
        v_box_spm_standalone_path.addLayout(h_box_spm_standalone_path)

        v_box_spm = QtWidgets.QVBoxLayout()
        v_box_spm.addLayout(h_box_use_spm)
        v_box_spm.addLayout(v_box_spm_path)
        v_box_spm.addLayout(h_box_use_spm_standalone)
        v_box_spm.addLayout(v_box_spm_standalone_path)

        self.groupbox_spm.setLayout(v_box_spm)

        # Final layout

        qradiobutton_layout = QtWidgets.QVBoxLayout()
        qradiobutton_layout.addLayout(h_box_install_target)
        qradiobutton_layout.addLayout(h_box_clinical_mode)

        h_box_mode_paths = QtWidgets.QHBoxLayout()
        h_box_mode_paths.addLayout(qradiobutton_layout)
        h_box_mode_paths.addWidget(self.groupbox)

        h_box_matlab_spm = QtWidgets.QHBoxLayout()
        h_box_matlab_spm.addWidget(self.groupbox_matlab)
        h_box_matlab_spm.addWidget(self.groupbox_spm)

        self.global_layout = QtWidgets.QVBoxLayout()
        # self.global_layout.addLayout(h_box_top_label)
        self.global_layout.addLayout(h_box_middle_label)
        self.global_layout.addStretch(1)
        self.global_layout.addLayout(h_box_mode_paths)
        self.global_layout.addLayout(h_box_matlab_spm)
        self.global_layout.addLayout(h_box_buttons)

        self.setLayout(self.global_layout)
        self.setWindowTitle("MIA installation")

        # Setting the checkbox values
        if matlab_path == "":
            self.matlab_choice.setDisabled(True)
            self.matlab_standalone_choice.setDisabled(True)
            self.matlab_label.setDisabled(True)
            self.matlab_standalone_label.setDisabled(True)
            self.matlab_browse.setDisabled(True)
            self.matlab_standalone_browse.setDisabled(True)
        else:
            self.install_matlab_api()
            self.use_matlab_checkbox.setChecked(True)
        self.spm_choice.setDisabled(True)
        self.spm_standalone_choice.setDisabled(True)
        self.spm_label.setDisabled(True)
        self.spm_standalone_label.setDisabled(True)
        self.spm_browse.setDisabled(True)
        self.spm_standalone_browse.setDisabled(True)
        self.use_spm_checkbox.setChecked(False)
        self.use_spm_standalone_checkbox.setChecked(False)

        # Signals
        self.use_matlab_checkbox.stateChanged.connect(self.use_matlab_changed)
        self.use_spm_checkbox.stateChanged.connect(self.use_spm_changed)
        self.use_spm_standalone_checkbox.stateChanged.connect(
            self.use_spm_standalone_changed
        )

    def browse_matlab(self):
        """
        Opens a file dialog for the user to select a MATLAB executable file.

        This method presents a file selection dialog to the user, allowing
        them to choose the MATLAB executable file from their file system.
        If a file is selected, the file path is displayed in the
        `matlab_choice` widget.

        Behavior:
            - Opens a `QFileDialog` for file selection with the title
              'Choose Matlab executable file'.
            - The dialog starts in the user's home directory.
            - If the user selects a file, sets the `matlab_choice` widget
              text to the selected file path.
        """
        fname = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose Matlab executable file", os.path.expanduser("~")
        )[0]

        if fname:
            self.matlab_choice.setText(fname)

    def browse_matlab_standalone(self):
        """
        Opens a directory dialog for the user to select the MATLAB Compile
        Runtime (MCR) directory.

        This method opens a directory selection dialog, allowing the user
        to choose the folder where the MATLAB Compiler Runtime (MCR) is
        installed. If a directory is selected, the path is displayed in
        the `matlab_standalone_choice` widget.

        Behavior:
            - Opens a `QFileDialog` for directory selection with the title
              'Choose MCR directory'.
            - The dialog starts in the user's home directory.
            - If the user selects a directory, sets the
              `matlab_standalone_choice` widget text to the selected
              directory path.
        """
        fname = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose MCR directory", os.path.expanduser("~")
        )

        if fname:
            self.matlab_standalone_choice.setText(fname)

    def browse_mia_config_path(self):
        """
        Opens a directory dialog for the user to select a folder for
        installing the MIA configuration.

        This method displays a dialog that allows the user to choose a
        directory in which the MIA configuration files will be installed.
        If a directory is selected, its path is displayed in the
        `mia_config_path_choice` widget.

        Behavior:
            - Opens a `QFileDialog` for directory selection with the title
              'Select a folder where to install Mia configuration'.
            - Starts the dialog in the user's home directory.
            - If a directory is selected, updates the `mia_config_path_choice`
              widget text with the selected directory path.
        """
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select a folder where to install Mia configuration",
            os.path.expanduser("~"),
        )

        if folder_name:
            self.mia_config_path_choice.setText(folder_name)

    def browse_projects_path(self):
        """
        Opens a directory dialog for the user to select a folder to store
        Mia's projects.

        This method opens a directory selection dialog, allowing the user
        to choose a folder where Mia's projects will be stored. If a folder
        is selected, its path is displayed in the `projects_path_choice`
        widget.

        Behavior:
            - Opens a `QFileDialog` for directory selection with the title
              "Select a folder where to store Mia's projects".
            - Starts the dialog in the user's home directory.
            - If a directory is selected, updates the `projects_path_choice`
              widget text with the selected folder path.
        """
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select a folder where to store Mia's projects",
            os.path.expanduser("~"),
        )

        if folder_name:
            self.projects_path_choice.setText(folder_name)

    def browse_spm(self):
        """
        Opens a directory dialog for the user to select the SPM (Statistical
        Parametric Mapping) directory.

        This method displays a directory selection dialog, allowing the user
        to choose the folder where the SPM software is installed. If a
        directory is selected, its path is displayed in the `spm_choice`
        widget.

        Behavior:
            - Opens a `QFileDialog` for directory selection with the title
              'Choose SPM directory'.
            - Starts the dialog in the user's home directory.
            - If a directory is selected, updates the `spm_choice` widget
              text with the selected directory path.
        """
        fname = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose SPM directory", os.path.expanduser("~")
        )

        if fname:
            self.spm_choice.setText(fname)

    def browse_spm_standalone(self):
        """
        Opens a directory dialog for the user to select the SPM (Statistical
        Parametric Mapping) standalone directory.

        This method opens a directory selection dialog, allowing the user
        to choose the folder where the standalone version of SPM is installed.
        If a directory is selected, its path is displayed in the
        `spm_standalone_choice` widget.

        Behavior:
            - Opens a `QFileDialog` for directory selection with the title
              'Choose SPM standalone directory'.
            - Starts the dialog in the user's home directory.
            - If a directory is selected, updates the `spm_standalone_choice`
              widget text with the selected directory path.
        """

        fname = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose SPM standalone directory", os.path.expanduser("~")
        )

        if fname:
            self.spm_standalone_choice.setText(fname)

    def btnstate(self, button):
        """
        Toggles the state of two related buttons based on the text of the
        clicked button.

        This method manages the state of two buttons
        (`host_target_push_button` and `casa_target_push_button`) based on
        the text of the button that is clicked. If the button text is
        'Casa_Distro', it ensures that the `host_target_push_button` is
        unchecked when the button is checked and vice versa. If the button
        text is 'Host', it ensures that the `casa_target_push_button` is
        unchecked when the button is checked and vice versa.

        Args:
            button (QtWidgets.QPushButton): The button that was clicked to
                                            trigger the state change.

        Behavior:
            - If the clicked button's text is "Casa_Distro", toggles the
              state of the `host_target_push_button`.
            - If the clicked button's text is "Host", toggles the state of
              the `casa_target_push_button`.
            - Ensures that when one button is checked, the other is unchecked.
        """
        if button.text() == "Casa_Distro":

            if button.isChecked() is True:
                self.host_target_push_button.setChecked(False)

            else:
                self.host_target_push_button.setChecked(True)

        if button.text() == "Host":

            if button.isChecked() is True:
                self.casa_target_push_button.setChecked(False)

            else:
                self.casa_target_push_button.setChecked(True)

    def find_matlab_path(self):
        """
        Attempts to find the installation path of MATLAB on the system.

        This method tries to locate the MATLAB installation by running the
        `matlab` command with specific options to retrieve the root directory
        of MATLAB. It checks if the path is valid and whether the MATLAB
        executable (`matlab` or `matlab.exe`) exists in the 'bin' directory
        under the root directory. If the executable is found, it returns the
        full path to the MATLAB executable.

        If MATLAB cannot be found or an error occurs during the process, an
        empty string is returned.

        Returns:
            str: The path to the MATLAB executable if found, otherwise an
                 empty string.

        Behavior:
            - Runs the MATLAB command
            `matlab -nodisplay -nosplash -nodesktop -r 'disp(matlabroot);exit'`
            to obtain the root installation directory.
            - Checks for the existence of the MATLAB executable (`matlab` or
            `matlab.exe`) under the `bin` folder.
            - Returns the full path to the executable if found, or an empty
            string if not.
            - In case of an exception (e.g., MATLAB is not installed), prints
            a message and returns an empty string.
        """
        return_value = ""

        try:
            out = subprocess.check_output(
                [
                    "matlab",
                    "-nodisplay",
                    "-nosplash",
                    "-nodesktop",
                    "-r",
                    "disp(matlabroot);exit",
                ]
            )
            out_split = out.split()
            valid_lines = [line for line in out_split if os.path.isdir(line)]

            if len(valid_lines) == 1:
                matlab_p = valid_lines[0].decode("utf-8")
                return_v_linux = os.path.join(matlab_p, "bin", "matlab")
                return_v_windows = os.path.join(matlab_p, "bin", "matlab.exe")

                if os.path.isfile(return_v_linux):
                    self.matlab_path = matlab_p
                    return_value = return_v_linux

                elif os.path.isfile(return_v_windows):
                    self.matlab_path = matlab_p
                    return_value = return_v_windows

        except Exception as e:
            print(
                f"{e}\nThe matlab path could not be determined "
                f"automatically ...\n"
            )

        return return_value

    def install(self):
        """
        Manages the installation and configuration of Mia and associated
        software components.

        This method performs the following steps:
        1. Installs populse_mia and mia_processes from PyPi.
        2. Checks the selected installation target (Host or Casa_Distro).
        3. Configures the operating mode (clinical or research).
        4. Optionally integrates with MATLAB and SPM based on user selections.
        5. Manages the creation and initialization of necessary directories and
           configuration files:
            - Creates the directory ~/.populse_mia if it does not exist and
              ensures the presence of configuration files.
            - Initializes user-specific directories for properties, processes,
              and projects.
            - Manages MRI conversion directories and resources.
        6. Prompts the user with warnings and asks for confirmation before
           overwriting existing directories if necessary.
        7. Clones required repositories (MRI conversion tools and
           miaresources).
        8. Updates the configuration file with new paths and settings.
        9. Optionally upgrades packages (soma-base, soma-workflow, capsul) if
           the Host installation target is selected.
        10. Finalizes the installation and updates the GUI with the
            installation status.

        The method requires user input via checkboxes and buttons to configure
        various aspects of the installation.

        Attributes:
            - `host_target_push_button`: Defines whether the host target
              installation is selected.
            - `clinical_mode_push_button`: Defines whether the clinical mode
              is selected.
            - `use_matlab_checkbox`: Defines whether MATLAB integration is
              enabled.
            - `use_spm_checkbox`: Defines whether SPM integration is enabled.
            - `use_spm_standalone_checkbox`: Defines whether standalone SPM
              integration is enabled.
            - `mia_config_path_choice`: Path for the configuration directory.
            - `projects_path_choice`: Path for the projects directory.
            - `check_box_mia`, `check_box_mri_conv`, `check_box_config`,
              `check_box_pkgs`: GUI elements for status display.

        Raises:
            - Exception: If any unexpected issues arise during the directory
                         creation or software installation steps.
        """
        # Installing Populse_mia and mia_processes from pypi
        self.install_package("populse_mia")

        from populse_mia.software_properties import Config
        from populse_mia.utils import verCmp

        # Flag used later
        self.folder_exists_flag = False

        # Checking which installation target has been selected
        if self.host_target_push_button.isChecked():
            host_target_install = True

        else:
            host_target_install = False

        # Checking which operating mode has been selected
        if self.clinical_mode_push_button.isChecked():
            use_clinical_mode = True
            self.operating_mode = "clinical"

        else:
            use_clinical_mode = False
            self.operating_mode = "research"

        if self.use_matlab_checkbox.isChecked():
            use_matlab = True
            matlab = self.matlab_choice.text()
            matlab_standalone = self.matlab_standalone_choice.text()

        else:
            use_matlab = False
            matlab = ""
            matlab_standalone = ""

        if self.use_spm_checkbox.isChecked():
            use_spm = True
            spm = self.spm_choice.text()

        else:
            use_spm = False
            spm = ""

        if self.use_spm_standalone_checkbox.isChecked():
            use_spm_standalone = True
            spm_standalone = self.spm_standalone_choice.text()

        else:
            use_spm_standalone = False
            spm_standalone = ""

        # The directory in which the configuration is located must be
        # declared in ~/.populse_mia/configuration_path.yml
        dot_mia_config = os.path.join(
            os.path.expanduser("~"), ".populse_mia", "configuration_path.yml"
        )
        # ~/.populse_mia/configuration_path.yml management/initialisation
        if not os.path.exists(os.path.dirname(dot_mia_config)):
            os.mkdir(os.path.dirname(dot_mia_config))
            print(
                "\nThe {} directory is created "
                "...".format(os.path.dirname(dot_mia_config))
            )
            Path(os.path.join(dot_mia_config)).touch()

        if not os.path.exists(dot_mia_config):
            Path(os.path.join(dot_mia_config)).touch()

        # We try to keep the old values in dot_mia_config file
        with open(dot_mia_config) as stream:

            try:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    mia_home_properties_path = yaml.load(
                        stream, Loader=yaml.FullLoader
                    )

                else:
                    mia_home_properties_path = yaml.load(stream)

                if mia_home_properties_path is None or not isinstance(
                    mia_home_properties_path, dict
                ):
                    mia_home_properties_path = dict()

            except yaml.YAMLError:
                mia_home_properties_path = dict()

        mia_home_properties_path_new = dict()

        properties_path = self.mia_config_path_choice.text()

        if properties_path.endswith(os.sep):
            properties_path = properties_path[:-1]
            self.mia_config_path_choice.setText(properties_path)

        properties_path = os.path.join(properties_path, "usr")

        # properties folder management / initialisation:
        properties_dir = os.path.join(properties_path, "properties")

        if not os.path.exists(properties_dir):
            os.makedirs(properties_dir, exist_ok=True)
            print(f"\nThe {properties_dir} directory is created...")

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

            print(
                "\nThe {} file is created...".format(
                    os.path.join(properties_dir, "saved_projects.yml")
                )
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

            print(
                "\nThe {} file is created...".format(
                    os.path.join(properties_dir, "config.yml")
                )
            )

            # processes/User_processes folder management / initialisation:
            user_processes_dir = os.path.join(
                properties_path, "processes", "User_processes"
            )

            if not os.path.exists(user_processes_dir):
                os.makedirs(user_processes_dir, exist_ok=True)
                print(
                    "\nThe {} directory is created...".format(
                        user_processes_dir
                    )
                )

            if not os.path.exists(
                os.path.join(user_processes_dir, "__init__.py")
            ):
                Path(
                    os.path.join(
                        user_processes_dir,
                        "__init__.py",
                    )
                ).touch()
                print(
                    "\nThe {} file is created...".format(
                        os.path.join(properties_dir, "config.yml")
                    )
                )

        # project folder management / initialisation:
        projects_path = os.path.join(
            self.projects_path_choice.text(), "projects_mia"
        )

        if not os.path.isdir(projects_path):
            os.makedirs(projects_path, exist_ok=True)
            print(f"\nThe {projects_path} directory is created...")

            if len(os.listdir(projects_path)) != 0:
                message = "The {} folder already contains data!".format(
                    projects_path
                )
                self.msg = QtWidgets.QMessageBox()
                self.msg.setIcon(QtWidgets.QMessageBox.Warning)
                self.msg.setText(message)
                self.msg.setInformativeText(
                    "Hit 'OK' to overwrite this "
                    "folder and its contents.\nPress "
                    "'Cancel' to continue with the "
                    "installation, retaining the "
                    "contents of the folder."
                )
                self.msg.setWindowTitle("Warning")
                self.msg.setStandardButtons(
                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
                )
                self.msg.buttonClicked.connect(self.ok_or_abort)
                self.msg.exec()

            # If the user has clicked on "Cancel" we do nothing. If he clicks
            # OK, we delete the entire contents of the folder
            if not self.folder_exists_flag:

                for elmt in os.listdir(projects_path):
                    elmt_path = os.path.join(projects_path, elmt)

                    try:

                        if os.path.isfile(elmt_path) or os.path.islink(
                            elmt_path
                        ):
                            os.remove(elmt_path)

                        elif os.path.isdir(elmt_path):
                            shutil.rmtree(elmt_path)

                    except Exception as e:
                        print(
                            "Failed to delete {}. Reason: {}".format(
                                elmt_path, e
                            )
                        )

        # MRIFileManager folder management / initialisation:
        mri_conv_dir = os.path.join(properties_path, "mri_conv")

        if os.path.isdir(mri_conv_dir):
            message = (
                "A 'mri_conv' folder already exists in the {} "
                "folder!".format(properties_path)
            )
            self.msg = QtWidgets.QMessageBox()
            self.msg.setIcon(QtWidgets.QMessageBox.Warning)
            self.msg.setText(message)
            self.msg.setInformativeText(
                "Hit 'OK' to overwrite this folder "
                "and its contents.\nPressing 'Cancel' "
                "will abort the installation."
            )
            self.msg.setWindowTitle("Warning")
            self.msg.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )
            self.msg.buttonClicked.connect(self.ok_or_abort)
            self.msg.exec()

        # If the user has clicked on "Cancel" the installation is aborted
        if self.folder_exists_flag:
            return

        else:
            shutil.rmtree(mri_conv_dir, ignore_errors=True)

        self.properties_dir = os.path.abspath(properties_dir)
        self.projects_save_path = os.path.abspath(projects_path)
        self.mri_conv_path = os.path.abspath(mri_conv_dir)

        self.set_new_layout()

        # Updating the checkbox
        self.check_box_mia.setChecked(True)
        QtWidgets.QApplication.processEvents()

        # Clones the MRI conversion repository into the specified directory
        self.make_mrifilemanager_folder(mri_conv_dir)

        # Clone MiaResources
        miaresources_dir = os.path.join(properties_path, "miaresources")
        self.mia_resources_path = os.path.abspath(miaresources_dir)

        if os.path.isdir(miaresources_dir):
            message = (
                "A 'miaresources' folder already exists in the {} "
                "folder!".format(properties_path)
            )
            self.msg = QtWidgets.QMessageBox()
            self.msg.setIcon(QtWidgets.QMessageBox.Warning)
            self.msg.setText(message)
            self.msg.setInformativeText(
                "Hit 'OK' to overwrite this folder "
                "and its contents.\nPressing 'Cancel' "
                "will abort the installation."
            )
            self.msg.setWindowTitle("Warning")
            self.msg.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )
            self.msg.buttonClicked.connect(self.ok_or_abort)
            self.msg.exec()

        # If the user has clicked on "Cancel" the installation is aborted
        if self.folder_exists_flag:
            return

        else:
            shutil.rmtree(miaresources_dir, ignore_errors=True)

        self.clone_miaResources(miaresources_dir)

        # Updating the checkbox
        self.check_box_mri_conv.setChecked(True)
        QtWidgets.QApplication.processEvents()

        # Adding properties_user_path to dot_mia_config file
        mia_home_properties_path_new["properties_user_path"] = os.path.dirname(
            properties_path
        )
        mia_home_properties_path = {
            **mia_home_properties_path,
            **mia_home_properties_path_new,
        }
        with open(dot_mia_config, "w", encoding="utf8") as configfile:
            yaml.dump(
                mia_home_properties_path,
                configfile,
                default_flow_style=False,
                allow_unicode=True,
            )

        config = Config()
        config.set_projects_save_path(projects_path)
        config.set_resources_path(miaresources_dir)
        config.set_mri_conv_path(
            os.path.join(mri_conv_dir, "MRIFileManager", "MRIManager.jar")
        )
        config.set_clinical_mode(use_clinical_mode)
        config.set_use_matlab(use_matlab)
        config.set_matlab_path(matlab)
        config.set_matlab_standalone_path(matlab_standalone)
        config.set_use_spm(use_spm)
        config.set_spm_path(spm)
        config.set_use_spm_standalone(use_spm_standalone)
        config.set_spm_standalone_path(spm_standalone)

        # Updating the checkbox
        self.check_box_config.setChecked(True)
        QtWidgets.QApplication.processEvents()

        # Upgrading soma-base, soma_worflow and capsul: we don't know if these
        # packages are up to date in pypi
        if host_target_install:
            self.upgrade_soma_capsul()

        if not host_target_install:
            self.uninstall_package("populse-db")
            self.uninstall_package("capsul")
            self.uninstall_package("soma-base")
            self.uninstall_package("soma-workflow")

        # Updating the checkbox
        self.check_box_pkgs.setChecked(True)
        QtWidgets.QApplication.processEvents()

        # Displaying the result of the installation
        self.last_layout()

    def install_matlab_api(self):
        """
        Installs the MATLAB Engine API for Python.

        This method attempts to install the MATLAB Engine API by calling
        `pip install .` in the MATLAB `extern/engines/python` directory.
        It temporarily changes the working directory to execute the
        installation command and then restores the directory.

        Notes:
            - `self.matlab_path` must be set to the MATLAB installation path.
            - This method uses `subprocess.check_call()` to run `pip install .`
              for compatibility with virtual environments.

        Returns:
            bool: True if the installation succeeds, False otherwise.

        Raises:
            - FileNotFoundError: If the MATLAB installation path is invalid.
            - subprocess.CalledProcessError: If the installation command fails.
        """

        if not os.path.isdir(self.matlab_path):
            raise FileNotFoundError(
                f"The specified MATLAB path "
                f"'{self.matlab_path}' is invalid."
            )

        matlab_engine_path = os.path.join(
            self.matlab_path, "extern", "engines", "python"
        )

        if not os.path.isdir(matlab_engine_path):
            raise FileNotFoundError(
                f"MATLAB Engine API directory not found "
                f"at '{matlab_engine_path}'."
            )

        original_dir = os.getcwd()
        pip_install_command = [sys.executable, "-m", "pip", "install", "."]

        if not self.is_venv:
            pip_install_command.append("--user")

        try:
            print("Starting MATLAB Engine API installation...")
            os.chdir(matlab_engine_path)
            # Install the package with pip
            subprocess.check_call(pip_install_command)
            print("MATLAB Engine API installation completed successfully.")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

        finally:
            os.chdir(original_dir)

    def install_package(self, package):
        """
        Installs or upgrades a Python package using pip.

        This method constructs a pip command to install or upgrade a
        specified package.
        It checks if the current environment is a virtual environment
        and, if not, adds the `--user` flag to the command to install
        the package for the current user.

        The method executes the command using `subprocess.check_call()`
        to ensure that the package is installed or upgraded successfully.

        Args:
            package (str): The name of the package to be installed or upgraded.

        Raises:
            subprocess.CalledProcessError: If the pip installation
                                           command fails.
        """
        pip_install_command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            package,
        ]

        # Add '--user' flag only if not in a virtual environment
        if not self.is_venv:
            pip_install_command.insert(4, "--user")

        subprocess.check_call(pip_install_command)

    def last_layout(self):
        """
        Sets the final layout for the application window after
        Mia installation.

        This method constructs and sets the final user interface layout after
        the successful installation of Mia.
        It displays information about the installation paths and operating
        mode, along with a command to launch the application.
        Additionally, it provides a "Quit" button for the user to exit
        the window.

        The layout includes the following elements:
            - A label confirming that Mia has been installed.
            - Paths for the Mia configuration, project storage
              MRI conversion, and Mia resources.
            - The operating mode used for the installation.
            - Command lines to launch Populse_MIA depending on
              the Python setup.
            - A "Quit" button to close the application.

        It ensures that all widgets and layouts are properly added to the
        window, and that the layout is set as the main layout of the window.
        """
        QtWidgets.QWidget().setLayout(self.v_box_install_status)

        # Setting a new layout
        self.mia_installed_label = QtWidgets.QLabel(
            "Mia has been correctly " "installed."
        )
        self.mia_installed_label.setFont(self.top_label_font)

        h_box_top_label = QtWidgets.QHBoxLayout()
        h_box_top_label.addStretch(1)
        h_box_top_label.addWidget(self.mia_installed_label)
        h_box_top_label.addStretch(1)

        mia_label_text = "- Mia configuration path: {}".format(
            self.properties_dir
        )
        projects_label_text = "- projects path: {}".format(
            self.projects_save_path
        )
        mri_conv_label_text = "- MRIFileManager path: {}".format(
            self.mri_conv_path
        )
        mia_resources_label_text = "- MiaResources path: {}".format(
            self.mia_resources_path
        )
        operating_mode_label_text = (
            "Populse_MIA has been installed with {} " "mode."
        ).format(self.operating_mode)

        mia_label = QtWidgets.QLabel(mia_label_text)
        projects_label = QtWidgets.QLabel(projects_label_text)
        mri_conv_label = QtWidgets.QLabel(mri_conv_label_text)
        mia_resources_label = QtWidgets.QLabel(mia_resources_label_text)
        operating_mode_label = QtWidgets.QLabel(operating_mode_label_text)

        mia_command_label_text = (
            "To launch populse_mia, execute one of these "
            "command lines depending on your Python "
            "setup:\n\n"
            "python3 -m populse_mia\n\n"
            "python -m populse_mia"
        )
        mia_command_label = QtWidgets.QLabel(mia_command_label_text)
        mia_command_label.setFont(self.top_label_font)

        button_quit = QtWidgets.QPushButton("Quit")
        button_quit.clicked.connect(self.close)

        h_box_button = QtWidgets.QHBoxLayout()
        h_box_button.addStretch(1)
        h_box_button.addWidget(button_quit)

        v_box_last_layout = QtWidgets.QVBoxLayout()
        v_box_last_layout.addLayout(h_box_top_label)
        v_box_last_layout.addStretch(1)
        v_box_last_layout.addWidget(mia_label)
        v_box_last_layout.addWidget(projects_label)
        v_box_last_layout.addWidget(mri_conv_label)
        v_box_last_layout.addWidget(mia_resources_label)
        v_box_last_layout.addStretch(1)
        v_box_last_layout.addWidget(operating_mode_label)
        v_box_last_layout.addStretch(1)
        v_box_last_layout.addWidget(mia_command_label)
        v_box_last_layout.addStretch(1)
        v_box_last_layout.addLayout(h_box_button)

        self.setLayout(v_box_last_layout)

        QtWidgets.QApplication.processEvents()

    def make_mrifilemanager_folder(self, mri_conv_dir):
        """
        Clones the MRI conversion repository into the specified directory.

        Args:
            mri_conv_dir (str): The directory where the repository will
                                 be cloned.

        Returns:
            bool: True if cloning succeeds, False otherwise.
        """
        try:
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "https://github.com/populse/mri_conv.git",
                    mri_conv_dir,
                ]
            )
            return True

        except subprocess.CalledProcessError as e:
            # Handle errors related to the git clone process
            print(
                f"Git clone failed with error code {e.returncode}."
                f"\nError message: {e}"
            )
            return False

        except FileNotFoundError as e:
            # Handle cases where 'git' is not installed or not found in PATH
            print(
                f"Error: 'git' command not found. Please ensure Git is "
                f"installed and available in your PATH ({e})."
            )
            return False

        except Exception as e:
            # Catch any other unforeseen errors
            print(f"An unexpected error occurred: {e}")
            return False

    def clone_miaResources(self, miaresources_dir):
        """
        Clones the MiaResources repository from GitLab to the
        specified directory.

        This method uses `git clone` to download the MiaResources repository
        from the specified GitLab URL to the given local directory.

        Args:
            miaresources_dir (str): The directory where the MiaResources
                                    repository will be cloned.

        Returns:
        bool: True if cloning succeeds, False otherwise.
        """
        try:
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "https://gricad-gitlab.univ-grenoble-alpes.fr/"
                    "condamie/miaresources.git",
                    miaresources_dir,
                ]
            )
            return True

        except subprocess.CalledProcessError as e:
            # Handle errors related to the git clone process
            print(
                f"Git clone failed with error code {e.returncode}."
                f"\nError message: {e}"
            )
            return False

        except FileNotFoundError as e:
            # Handle cases where 'git' is not installed or not found in PATH
            print(
                f"Error: 'git' command not found. Please ensure Git is "
                f"installed and available in your PATH ({e})."
            )
            return False

        except Exception as e:
            # Catch any other unforeseen errors
            print(f"An unexpected error occurred: {e}")
            return False

    def ok_or_abort(self, button):
        """
        Handles the action when the user clicks a button in a message box.

        This method checks the role of the clicked button.
        If the "OK" button is clicked, it sets the `folder_exists_flag`
        to `False`. If any other button is clicked, it sets the
        `folder_exists_flag` to `True`.

        Args:
            button (QtWidgets.QPushButton): The button that was clicked
            in the message box.

        Modifies:
            folder_exists_flag (bool): A flag that indicates whether the
                                       folder exists based on the user's
                                       response to the message box.
        """
        role = self.msg.buttonRole(button)

        if role == QtWidgets.QMessageBox.AcceptRole:  # "OK" has been clicked
            self.folder_exists_flag = False

        else:
            self.folder_exists_flag = True

    def set_new_layout(self):
        """
        Changes the layout to show the installation progress.

        This method sets up a temporary layout to display the progress of the
        installation. It includes a label indicating the installation is
        ongoing, and checkboxes for tracking the status of various installation
        steps, such as installing Mia, MRIFileManager, writing the config file,
        and installing Python packages. The layout is then set as the current
        layout for the widget.

        Modifies:
            The layout of the widget to reflect the installation status, with
            labels and checkboxes to indicate progress.
        """
        QtWidgets.QWidget().setLayout(self.global_layout)

        # Setting a new layout
        self.mia_installing_label = QtWidgets.QLabel(
            "Mia is getting installed." " Please wait! ..."
        )
        self.mia_installing_label.setFont(self.top_label_font)

        h_box_top_label = QtWidgets.QHBoxLayout()
        h_box_top_label.addStretch(1)
        h_box_top_label.addWidget(self.mia_installing_label)
        h_box_top_label.addStretch(1)

        self.status_label = QtWidgets.QLabel("Status:")

        self.check_box_mia = QtWidgets.QCheckBox("Installing Mia")

        self.check_box_mri_conv = QtWidgets.QCheckBox(
            "Installing " "MRIFileManager"
        )

        self.check_box_config = QtWidgets.QCheckBox("Writing config file")

        self.check_box_pkgs = QtWidgets.QCheckBox(
            "Installing Python packages " "(may take a few minutes)"
        )

        self.v_box_install_status = QtWidgets.QVBoxLayout()
        self.v_box_install_status.addLayout(h_box_top_label)
        self.v_box_install_status.addWidget(self.status_label)
        self.v_box_install_status.addWidget(self.check_box_mia)
        self.v_box_install_status.addWidget(self.check_box_mri_conv)
        self.v_box_install_status.addWidget(self.check_box_config)
        self.v_box_install_status.addWidget(self.check_box_pkgs)
        self.v_box_install_status.addStretch(1)

        self.setLayout(self.v_box_install_status)

        QtWidgets.QApplication.processEvents()

    @staticmethod
    def uninstall_package(package):
        """
        Uninstalls a Python package using pip.

        This method attempts to uninstall a specified package using pip.
        It first tries to use the current Python interpreter
        (`sys.executable`) to uninstall the package. If an exception occurs
        (e.g., if pip is not available for the current interpreter), it falls
        back to using the `pip3` command to uninstall the package.

        Args:
            package (str): The name of the Python package to uninstall.

        Raises:
            subprocess.CalledProcessError: If the package uninstall
            command fails.
        """
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "uninstall", "--yes", package]
            )

        except Exception:
            subprocess.check_call(["pip3", "uninstall", "--yes", package])

        except subprocess.CalledProcessError:
            print(f"Failed to uninstall {package}.")

    def upgrade_soma_capsul(self):
        """
        Upgrades the soma-base, soma-workflow, and capsul packages by cloning
        their latest versions from GitHub and reinstalling them.

        This method performs the following steps:
            1. Creates a temporary directory to store the cloned repositories.
            2. Uninstalls the current versions of soma-base,
               soma-workflow, and capsul.
            3. Clones each package's repository (soma-base,
               soma-workflow, and capsul) from GitHub.
            4. Installs the cloned package using the current Python
               interpreter with `setup.py install`.

        If any step fails, an error message is printed, and the process
        continues to the next package. After the upgrades, the method
        returns to the original working directory and deletes the
        temporary directory.

        Raises:
            subprocess.CalledProcessError: If any command execution fails.
        """
        temp_dir = tempfile.mkdtemp()
        cwd = os.getcwd()
        repos = [
            ("https://github.com/populse/soma-base.git", "soma-base"),
            ("https://github.com/populse/soma-workflow.git", "soma-workflow"),
            ("https://github.com/populse/capsul.git", "capsul"),
        ]
        pip_install_command = [sys.executable, "-m", "pip", "install", "."]

        if not self.is_venv:
            pip_install_command.append("--user")

        try:

            for repo_url, package_name in repos:
                clone_dir = os.path.join(temp_dir, package_name)
                self.uninstall_package(package_name)
                subprocess.check_call(["git", "clone", repo_url, clone_dir])
                os.chdir(clone_dir)
                subprocess.check_call(pip_install_command)

        except Exception as e:
            print(f"Error while upgrading {package_name}: {e}")

            """if not os.name == 'nt':  # if not on windows
                   self.uninstall_package('capsul')
                   os.chmod('upgrade_capsul.sh', 0o777)
                   subprocess.call('./upgrade_capsul.sh', shell=True)

                    self.uninstall_package('soma-base')
                    os.chmod('upgrade_soma.sh', 0o777)
                    subprocess.call('./upgrade_soma.sh', shell=True)
            """

        os.chdir(cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def use_matlab_changed(self):
        """
        Toggles the state of MATLAB-related options based on the 'use_matlab'
        checkbox. When unchecked, all MATLAB and SPM options are disabled.

        Called when the use_matlab checkbox is changed.
        """

        if not self.use_matlab_checkbox.isChecked():
            self.matlab_choice.setDisabled(True)
            self.matlab_standalone_choice.setDisabled(True)
            self.spm_choice.setDisabled(True)
            self.spm_standalone_choice.setDisabled(True)
            self.matlab_label.setDisabled(True)
            self.matlab_standalone_label.setDisabled(True)
            self.spm_label.setDisabled(True)
            self.spm_standalone_label.setDisabled(True)
            self.spm_browse.setDisabled(True)
            self.spm_standalone_browse.setDisabled(True)
            self.matlab_browse.setDisabled(True)
            self.matlab_standalone_browse.setDisabled(True)
            self.use_spm_checkbox.setChecked(False)
            self.use_spm_standalone_checkbox.setChecked(False)
        else:
            self.matlab_choice.setDisabled(False)
            self.matlab_standalone_choice.setDisabled(False)
            self.matlab_label.setDisabled(False)
            self.matlab_standalone_label.setDisabled(False)
            self.matlab_browse.setDisabled(False)
            self.matlab_standalone_browse.setDisabled(False)

    def use_spm_changed(self):
        """
        Updates the state of SPM-related options based on the 'use_spm'
        checkbox.

        When unchecked, disables all SPM options, and when checked, enables the
        regular SPM options while disabling the standalone SPM options.

        Called when the use_spm checkbox is changed
        """
        if not self.use_spm_checkbox.isChecked():
            self.spm_choice.setDisabled(True)
            self.spm_label.setDisabled(True)
            self.spm_browse.setDisabled(True)

        else:
            self.spm_choice.setDisabled(False)
            self.spm_label.setDisabled(False)
            self.spm_browse.setDisabled(False)
            self.spm_standalone_choice.setDisabled(True)
            self.spm_standalone_label.setDisabled(True)
            self.spm_standalone_browse.setDisabled(True)
            self.use_spm_standalone_checkbox.setChecked(False)

    def use_spm_standalone_changed(self):
        """
        Updates the state of standalone SPM-related options based on the
        'use_spm_standalone' checkbox.

        When checked, enables the standalone SPM options while disabling
        the regular SPM options, and vice versa.

        Called when the use_spm_standalone checkbox is changed
        """

        if not self.use_spm_standalone_checkbox.isChecked():
            self.spm_standalone_choice.setDisabled(True)
            self.spm_standalone_label.setDisabled(True)
            self.spm_standalone_browse.setDisabled(True)
        else:
            self.spm_standalone_choice.setDisabled(False)
            self.spm_standalone_label.setDisabled(False)
            self.spm_standalone_browse.setDisabled(False)
            self.spm_choice.setDisabled(True)
            self.spm_label.setDisabled(True)
            self.spm_browse.setDisabled(True)
            self.use_spm_checkbox.setChecked(False)
