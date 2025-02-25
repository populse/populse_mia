"""
Module that defines all the pop-ups used across the Mia software.

:Contains:
    :Class:
        - ClickableLabel
        - DefaultValueListCreation
        - DefaultValueQLineEdit
        - PopUpAddPath
        - PopUpAddTag
        - PopUpCloneTag
        - PopUpClosePipeline
        - PopUpDataBrowserCurrentSelection
        - PopUpDeletedProject
        - PopUpDeleteProject
        - PopUpFilterSelection
        - PopUpInformation
        - PopUpInheritanceDict
        - PopUpMultipleSort
        - PopUpNewProject
        - PopUpOpenProject
        - PopUpPreferences
        - PopUpProperties
        - PopUpQuit
        - PopUpRemoveScan
        - PopUpRemoveTag
        - PopUpSaveProjectAs
        - PopUpSeeAllProjects
        - PopUpSelectFilter
        - PopUpSelectIteration
        - PopUpTagSelection  (must precede PopUpSelectTag)
        - PopUpSelectTag
        - PopUpSelectTagCountTable
        - PopUpShowHistory
        - PopUpVisualizedTags
        - QLabel_clickable

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import ast
import glob
import hashlib
import logging
import os
import platform
import re
import shutil
import subprocess
from datetime import datetime
from functools import partial
from typing import get_origin

import yaml

# Capsul imports
from capsul.api import capsul_engine
from capsul.pipeline.pipeline_nodes import PipelineNode
from capsul.qt_gui.widgets.pipeline_developer_view import PipelineDeveloperView
from capsul.qt_gui.widgets.settings_editor import SettingsEditor

# PyQt5 imports
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QCoreApplication, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Populse_mia imports
from populse_mia.data_manager import (
    BRICK_EXEC,
    BRICK_EXEC_TIME,
    BRICK_INIT,
    BRICK_INIT_TIME,
    BRICK_INPUTS,
    BRICK_NAME,
    BRICK_OUTPUTS,
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
    HISTORY_BRICKS,
    HISTORY_PIPELINE,
    TAG_CHECKSUM,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_ORIGIN_USER,
    TAG_TYPE,
    TAG_UNIT_DEGREE,
    TAG_UNIT_HZPIXEL,
    TAG_UNIT_MHZ,
    TAG_UNIT_MM,
    TAG_UNIT_MS,
    TYPE_MAT,
    TYPE_NII,
    TYPE_TXT,
    TYPE_UNKNOWN,
)
from populse_mia.data_manager.project import Project
from populse_mia.software_properties import Config
from populse_mia.user_interface.data_browser import data_browser

logger = logging.getLogger(__name__)


class ClickableLabel(QLabel):
    """
    A QLabel subclass that emits a signal when clicked.

    .. Methods:
        - mousePressEvent: overrides the mousePressEvent method by emitting
          the clicked signal

    .. Signals:
        - clicked(): Emitted when the label is clicked.
    """

    clicked = pyqtSignal()

    def __init__(self):
        """Initializes the ClickableLabel."""
        super().__init__()

    def mousePressEvent(self, event):
        """
        Handles the mouse press event by emitting the `clicked` signal.

        :param event (QMouseEvent): The mouse event triggering the signal.
        """
        self.clicked.emit()


class DefaultValueListCreation(QDialog):
    """
    A dialog for creating or editing a list's default value.

    This widget allows users to input and manage a list of values
    based on a specified type (e.g., integers, floats, booleans, etc.).

    .. Methods:
        - add_element(): Adds one more element to the list.
        - default_init_table(): Initializes the table with a default value
                                when no previous value exists.
        - remove_element(): Removes the last element from the list.
        - resize_table(): Adjusts the popup size based on the table content.
        - update_default_value(): Validates user input and updates the
                                  parent's default value.

    """

    def __init__(self, parent, type):
        """
        Initializes the DefaultValueListCreation dialog.

        :param parent (DefaultValueQLineEdit): The parent object.
        :param type (Type): The type of the list elements (e.g., int,
                            float, str).

        """
        super().__init__()
        self.setModal(True)
        # Current type chosen
        self.type = type
        self.parent = parent
        self.setWindowTitle(
            f"Adding a list of {self.type.__args__[0].__name__}"
        )
        # The table that will be filled
        self.table = QtWidgets.QTableWidget()
        self.table.setRowCount(1)
        value = self.parent.text()

        if value:

            try:
                list_value = ast.literal_eval(value)

                if isinstance(list_value, list):
                    # If the previous value was already a list, we fill it
                    self.table.setColumnCount(len(list_value))

                    for i, val in enumerate(list_value):
                        self.table.setItem(
                            0, i, QtWidgets.QTableWidgetItem(str(val))
                        )

                else:
                    self.default_init_table()

            except Exception:
                self.default_init_table()

        else:
            self.default_init_table()

        self.resize_table()
        # Ok button
        self.ok_button = QtWidgets.QPushButton("Ok")
        self.ok_button.clicked.connect(self.update_default_value)
        # Cancel button
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        # Button to add an element to the list
        sources_images_dir = Config().getSourceImageDir()
        self.add_element_label = ClickableLabel()
        self.add_element_label.setObjectName("plus")
        self.add_element_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(sources_images_dir, "green_plus.png")
            ).scaledToHeight(15)
        )
        self.add_element_label.clicked.connect(self.add_element)
        # Button to remove the last element of the list
        self.remove_element_label = ClickableLabel()
        self.remove_element_label.setObjectName("minus")
        self.remove_element_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(sources_images_dir, "red_minus.png")
            ).scaledToHeight(20)
        )
        self.remove_element_label.clicked.connect(self.remove_element)
        # Layouts
        self.list_layout = QHBoxLayout()
        self.list_layout.addWidget(self.table)
        self.list_layout.addWidget(self.remove_element_label)
        self.list_layout.addWidget(self.add_element_label)
        self.h_box_final = QHBoxLayout()
        self.h_box_final.addWidget(self.ok_button)
        self.h_box_final.addWidget(cancel_button)
        self.v_box_final = QVBoxLayout()
        self.v_box_final.addLayout(self.list_layout)
        self.v_box_final.addLayout(self.h_box_final)
        self.setLayout(self.v_box_final)

    def add_element(self):
        """
        Adds a new empty element to the list.

        Increases the number of columns in the table by one and adds
        an empty `QTableWidgetItem` for user input.
        """
        self.table.setColumnCount(self.table.columnCount() + 1)
        self.table.setItem(
            0, self.table.columnCount() - 1, QtWidgets.QTableWidgetItem()
        )
        self.resize_table()

    def default_init_table(self):
        """
        Initializes the table with a default value.

        If no previous value exists, the table is set up with a single empty
        column to allow user input.
        """
        # Table filled with a single element at the beginning if no value
        self.table.setColumnCount(1)
        self.table.setItem(0, 0, QtWidgets.QTableWidgetItem())

    def remove_element(self):
        """
        Removes the last element from the list.

        Ensures that at least one column remains to prevent an empty table.
        Adjusts the table size accordingly.
        """

        if self.table.columnCount() <= 1:
            return

        self.table.setColumnCount(self.table.columnCount() - 1)
        self.resize_table()
        self.adjustSize()

    def resize_table(self):
        """
        Adjusts the size of the popup window based on the table content.

        Dynamically resizes the table width and height based on the number
        of columns and rows, with a maximum width limit of 900 pixels.
        """
        self.table.resizeColumnsToContents()
        total_width = sum(
            self.table.columnWidth(i) for i in range(self.table.columnCount())
        )
        total_height = sum(
            self.table.rowHeight(i) for i in range(self.table.rowCount())
        )
        max_width = 900
        padding = 20 if total_width + 20 < max_width else 40
        self.table.setFixedWidth(min(total_width + 20, max_width))
        self.table.setFixedHeight(total_height + padding)

    def update_default_value(self):
        """
        Validates user input and updates the parent's default value.

        Converts table values to the specified list type, ensuring that
        each entry is valid. If any value is invalid, a warning message
        is displayed, and the update is aborted.

        If all values are valid, they are stored in the parent widget,
        and the dialog is closed.
        """
        type_parsers = {
            FIELD_TYPE_LIST_INTEGER: int,
            FIELD_TYPE_LIST_FLOAT: float,
            FIELD_TYPE_LIST_BOOLEAN: lambda x: {"True": True, "False": False}[
                x
            ],
            FIELD_TYPE_LIST_STRING: str,
            FIELD_TYPE_LIST_DATE: lambda x: datetime.strptime(
                x, "%d/%m/%Y"
            ).date(),
            FIELD_TYPE_LIST_DATETIME: lambda x: datetime.strptime(
                x, "%d/%m/%Y %H:%M:%S.%f"
            ),
            FIELD_TYPE_LIST_TIME: lambda x: datetime.strptime(
                x, "%H:%M:%S.%f"
            ).time(),
        }
        database_value = []

        for i in range(self.table.columnCount()):
            item = self.table.item(0, i)
            text = item.text() if item else ""

            try:
                database_value.append(type_parsers[self.type](text))

            except (ValueError, KeyError):
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Warning")
                msg.setText("Invalid value")
                msg.setInformativeText(
                    f"The value '{text}' is invalid for type {self.type}."
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
                return

        self.parent.setText(str(database_value))
        self.close()


class DefaultValueQLineEdit(QtWidgets.QLineEdit):
    """
    A QLineEdit override for handling default values.

    This class customizes QLineEdit to handle list-type default values by
    displaying a popup when clicked.

    .. Methods:
        - mousePressEvent: Mouse pressed on the QLineEdit

    """

    def __init__(self, parent):
        """
        :param parent: The parent widget, expected to have a `type` attribute.
        """
        super().__init__()
        self.parent = parent

    def mousePressEvent(self, event):
        """
        Handles mouse press events.

        If the parent's type is a list, displays a popup for list creation.

        :param event (QMouseEvent): The mouse press event (unused).

        """
        if get_origin(self.parent.type) is list:
            # We display the pop up to create the list if the checkbox is
            # checked, otherwise we do nothing
            self.list_creation = DefaultValueListCreation(
                self, self.parent.type
            )
            self.list_creation.show()


class PopUpAddPath(QDialog):
    """
    Dialog for adding a document to the project without using the MRI Files
    Manager (File > Import).

    .. Methods:
        - file_to_choose: Opens a file dialog to choose a document.
        - find_type: Determines the document type when the file path changes.
        - save_path: Adds the file path to the database and updates the UI.
    """

    def __init__(self, project, databrowser):
        """
        Initializes the pop-up for adding a document.

        :param project (Project): The current project instance.
        :param databrowser (DataBrowser): The application's data browser.
        """
        super().__init__()
        self.project = project
        self.databrowser = databrowser
        self.setWindowTitle("Add a document")
        self.setModal(True)
        vbox_layout = QVBoxLayout()
        # File selection layout
        file_layout = QHBoxLayout()
        file_label = QLabel("File: ")
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setFixedWidth(300)
        self.file_line_edit.textChanged.connect(self.find_type)
        file_button = QPushButton("Choose a document")
        file_button.clicked.connect(self.file_to_choose)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_line_edit)
        file_layout.addWidget(file_button)
        vbox_layout.addLayout(file_layout)
        # File type layout
        type_layout = QHBoxLayout()
        type_label = QLabel("Type: ")
        self.type_line_edit = QLineEdit()
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_line_edit)
        vbox_layout.addLayout(type_layout)
        # Action buttons layout
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.save_path)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(cancel_button)
        vbox_layout.addLayout(button_layout)
        self.setLayout(vbox_layout)

    def file_to_choose(self):
        """
        Opens a file dialog for selecting documents.
        """
        fname, _ = QFileDialog.getOpenFileNames(
            self, "Choose a document to import", os.path.expanduser("~")
        )

        if fname:
            self.file_line_edit.setText(str(fname))

    def find_type(self):
        """
        Determines the document type when the file path changes.
        """
        file_paths = self.file_line_edit.text()

        # If the input is empty, clear the type field
        if not file_paths:
            self.type_line_edit.clear()
            return

        try:
            file_list = ast.literal_eval(file_paths)

        except (SyntaxError, ValueError):
            self.type_line_edit.setText(str([TYPE_UNKNOWN] * len(file_paths)))
            return

        type_mapping = {".nii": TYPE_NII, ".mat": TYPE_MAT, ".txt": TYPE_TXT}
        file_types = [
            type_mapping.get(os.path.splitext(f)[1], TYPE_UNKNOWN)
            for f in file_list
        ]
        self.type_line_edit.setText(str(file_types))

    def save_path(self):
        """
        Adds the selected document paths to the database and updates the UI.
        """

        try:
            path_list = (
                ast.literal_eval(self.file_line_edit.text())
                if self.file_line_edit.text()
                else []
            )
            path_type_list = (
                ast.literal_eval(self.type_line_edit.text())
                if self.type_line_edit.text()
                else []
            )

        except (SyntaxError, ValueError):
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setText("- Invalid Data! -")
            self.msg.setInformativeText(
                f"Invalid file(s) in:\n"
                f"{path_list}\n"
                f" or type format(s) in:\n"
                f"{path_type_list}"
            )
            self.msg.setWindowTitle("Warning: Invalid data!")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.buttonClicked.connect(self.msg.close)
            self.msg.show()
            return

        with self.project.database.data() as database_data:
            doc_in_db = {
                os.path.basename(doc)
                for doc in database_data.get_document_names(COLLECTION_CURRENT)
            }

        self.project.unsavedModifications = True

        for path, path_type in zip(path_list, path_type_list):
            filename = os.path.basename(path)

            if filename in doc_in_db:
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setText(f"- {os.path.basename(path)} -")
                self.msg.setInformativeText(
                    f"The document '{path}' \n "
                    f"already exists in the Data Browser!"
                )
                self.msg.setWindowTitle("Warning: existing data!")
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.buttonClicked.connect(self.msg.close)
                self.msg.show()
                continue

            if not path or not os.path.exists(path) or not path_type:
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setText("Invalid arguments")
                self.msg.setInformativeText(
                    "The path must exist.\nThe path type can't be empty."
                )
                self.msg.setWindowTitle("Warning")
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.buttonClicked.connect(self.msg.close)
                self.msg.show()
                continue

            # Prepare history tracking
            history_maker = ["add_scans"]
            values_added = []
            # Copy file to project directory
            rel_path = os.path.join("data", "downloaded_data", filename)
            copy_path = os.path.join(self.project.folder, rel_path)
            shutil.copy(path, copy_path)

            # Compute file checksum
            with open(path, "rb") as scan_file:
                checksum = hashlib.md5(scan_file.read()).hexdigest()

            # Add document to database
            with self.project.database.data() as database_data:

                for collection in (COLLECTION_INITIAL, COLLECTION_CURRENT):
                    database_data.add_document(collection, rel_path)
                    database_data.set_value(
                        collection_name=collection,
                        primary_key=rel_path,
                        values_dict={TAG_TYPE: path_type},
                    )
                    database_data.set_value(
                        collection_name=collection,
                        primary_key=rel_path,
                        values_dict={TAG_CHECKSUM: checksum},
                    )

            values_added.extend(
                [
                    [rel_path, TAG_TYPE, path_type, path_type],
                    [rel_path, TAG_CHECKSUM, checksum, checksum],
                ]
            )
            # Update history
            history_maker.extend([[rel_path], values_added])
            self.project.undos.append(history_maker)
            self.project.redos.clear()

            # Update data browser
            with self.project.database.data() as database_data:
                scans = database_data.get_document_names(COLLECTION_CURRENT)

            table_data = self.databrowser.table_data
            table_data.scans_to_visualize = scans
            table_data.scans_to_search = scans
            table_data.add_columns()
            table_data.fill_headers()
            table_data.add_rows([rel_path])

        self.databrowser.reset_search_bar()
        self.databrowser.frame_advanced_search.setHidden(True)
        self.databrowser.advanced_search.rows = []
        self.close()


class PopUpAddTag(QDialog):
    """
    Dialog for adding a new tag to the project.

    This dialog allows users to create a new tag by specifying its name,
    default value, description, unit, and type.

    Attributes:
        signal_add_tag: Signal emitted when a new tag is successfully added

    Methods:
        - _connect_signals: Connect signals to slots
        - _setup_layouts: Set up the layout of UI elements
        - _setup_ui: Set up the dialog UI elements
        - _show_error: Display an error message box
        - ok_action: Validates input fields and adds the new tag if valid
        - on_activated: Updates form fields when tag type is changed
    """

    # Signal emitted when tag is successfully added
    signal_add_tag = pyqtSignal()

    def __init__(self, databrowser, project):
        """
        Initialize the dialog for adding a new tag.

        :param databrowser: The data browser instance
        :param project: The current project in the software
        """
        super().__init__()
        self.project = project
        self.databrowser = databrowser
        # Default tag type is string
        self.type = FIELD_TYPE_STRING
        self.setObjectName("Add a tag")
        self.setWindowTitle("Add a tag")
        self.setMinimumWidth(700)
        self.setModal(True)
        self._setup_ui()
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals to slots."""
        self.push_button_ok.clicked.connect(self.ok_action)
        self.combo_box_type.currentTextChanged.connect(self.on_activated)

    def _setup_layouts(self):
        """Set up the layout of UI elements."""
        # Labels column
        v_box_labels = QVBoxLayout()
        v_box_labels.addWidget(self.label_tag_name)
        v_box_labels.addWidget(self.label_default_value)
        v_box_labels.addWidget(self.label_description_value)
        v_box_labels.addWidget(self.label_unit_value)
        v_box_labels.addWidget(self.label_type)
        # Edit fields column
        v_box_edits = QVBoxLayout()
        v_box_edits.addWidget(self.text_edit_tag_name)
        default_layout = QHBoxLayout()
        default_layout.addWidget(self.text_edit_default_value)
        v_box_edits.addLayout(default_layout)
        v_box_edits.addWidget(self.text_edit_description_value)
        v_box_edits.addWidget(self.combo_box_unit)
        v_box_edits.addWidget(self.combo_box_type)
        # Main content layout
        h_box_top = QHBoxLayout()
        h_box_top.addLayout(v_box_labels)
        h_box_top.addSpacing(50)
        h_box_top.addLayout(v_box_edits)
        # OK button layout
        h_box_ok = QHBoxLayout()
        h_box_ok.addStretch(1)
        h_box_ok.addWidget(self.push_button_ok)
        # Main dialog layout
        v_box_total = QVBoxLayout()
        v_box_total.addLayout(h_box_top)
        v_box_total.addLayout(h_box_ok)
        self.setLayout(v_box_total)

    def _setup_ui(self):
        """Set up the dialog UI elements."""
        _translate = QtCore.QCoreApplication.translate
        # Create UI components
        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setObjectName("push_button_ok")
        self.push_button_ok.setText(_translate("Add a tag", "OK"))
        # Tag name components
        self.label_tag_name = QtWidgets.QLabel(
            _translate("Add a tag", "Tag name:"), self
        )
        self.label_tag_name.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_name.setObjectName("tag_name")
        self.text_edit_tag_name = QtWidgets.QLineEdit(self)
        self.text_edit_tag_name.setObjectName("textEdit_tag_name")
        # Default value components
        self.label_default_value = QtWidgets.QLabel(
            _translate("Add a tag", "Default value:"), self
        )
        self.label_default_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_default_value.setObjectName("default_value")
        self.text_edit_default_value = DefaultValueQLineEdit(self)
        self.text_edit_default_value.setObjectName("textEdit_default_value")
        # Default value for string type
        self.text_edit_default_value.setText("Undefined")
        # Description components
        self.label_description_value = QtWidgets.QLabel(
            _translate("Add a tag", "Description:"), self
        )
        self.label_description_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_description_value.setObjectName("description_value")
        self.text_edit_description_value = QtWidgets.QLineEdit(self)
        self.text_edit_description_value.setObjectName(
            "textEdit_description_value"
        )
        # Unit components
        self.label_unit_value = QtWidgets.QLabel(
            _translate("Add a tag", "Unit:"), self
        )
        self.label_unit_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_unit_value.setObjectName("unit_value")
        self.combo_box_unit = QtWidgets.QComboBox(self)
        self.combo_box_unit.setObjectName("combo_box_unit")
        self.combo_box_unit.addItems(
            [
                None,
                TAG_UNIT_MS,
                TAG_UNIT_MM,
                TAG_UNIT_MHZ,
                TAG_UNIT_HZPIXEL,
                TAG_UNIT_DEGREE,
            ]
        )
        # Type components
        self.label_type = QtWidgets.QLabel(
            _translate("Add a tag", "Tag type:"), self
        )
        self.label_type.setTextFormat(QtCore.Qt.AutoText)
        self.label_type.setObjectName("type")
        self.combo_box_type = QtWidgets.QComboBox(self)
        self.combo_box_type.setObjectName("combo_box_type")
        self.combo_box_type.addItems(
            [
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
        )
        # Set up layouts
        self._setup_layouts()

    def _show_error(self, text, informative_text):
        """
        Display an error message box.

        :param text: The main error message text
        :param informative_text: The additional informative text
        """
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Critical)
        self.msg.setText(text)
        self.msg.setInformativeText(informative_text)
        self.msg.setWindowTitle("Error")
        self.msg.setStandardButtons(QMessageBox.Close)
        self.msg.exec()

    def ok_action(self):
        """Validate inputs and add the new tag if all fields are correct.

        Performs validation on the tag name, type and default value to ensure
        they are valid before adding the tag to the project.
        """
        # Import check_value_type here to prevent circular import issues
        from populse_mia.utils import check_value_type

        # Get existing tag names
        with self.project.database.data() as database_data:
            existing_tags = database_data.get_field_names(COLLECTION_CURRENT)

        tag_name = self.text_edit_tag_name.text()
        default_value = self.text_edit_default_value.text()

        # Validation checks
        # Tag name can't be empty
        if not tag_name:
            self._show_error(
                "The tag name cannot be empty", "Please enter a tag name"
            )
            return

        # Tag name can't exist already
        if tag_name in existing_tags:
            self._show_error(
                "This tag name already exists",
                "Please select another tag name",
            )
            return

        # Special validation for PatientName tag
        if tag_name == "PatientName":

            if self.type != "string":
                self._show_error(
                    "PatientName is a special tag that must be a character "
                    "string containing no spaces!",
                    "Please select string type.",
                )
                return

            # Remove spaces from PatientName default value
            self.text_edit_default_value.setText(
                default_value.replace(" ", "")
            )
            default_value = self.text_edit_default_value.text()

        # Validate default value type
        if not check_value_type(default_value, self.type, False):
            self._show_error(
                "Invalid default value",
                f"The default value '{default_value}' is invalid "
                f"with the '{self.type}' type!",
            )
            return

        # All validations passed, add the tag
        self.accept()
        # Store values for databrowser
        self.new_tag_name = tag_name
        self.new_default_value = default_value
        self.new_tag_description = self.text_edit_description_value.text()
        self.new_tag_unit = self.combo_box_unit.currentText() or None
        # Add tag to project
        self.databrowser.add_tag_infos(
            self.new_tag_name,
            self.new_default_value,
            self.type,
            self.new_tag_description,
            self.new_tag_unit,
        )
        self.close()

    def on_activated(self, text):
        """
        Update the default value when the tag type changes.

        :param text: The new type selected from combo box
        """
        type_mapping = {
            "String": (FIELD_TYPE_STRING, "Undefined"),
            "Integer": (FIELD_TYPE_INTEGER, "0"),
            "Float": (FIELD_TYPE_FLOAT, "0.0"),
            "Boolean": (FIELD_TYPE_BOOLEAN, "True"),
            "Date": (FIELD_TYPE_DATE, datetime.now().strftime("%d/%m/%Y")),
            "Datetime": (
                FIELD_TYPE_DATETIME,
                datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f"),
            ),
            "Time": (FIELD_TYPE_TIME, datetime.now().strftime("%H:%M:%S.%f")),
        }

        # Handle list types separately to avoid repetition
        list_types = {
            "String List": (
                FIELD_TYPE_LIST_STRING,
                "['Undefined', 'Undefined']",
            ),
            "Integer List": (FIELD_TYPE_LIST_INTEGER, "[0, 0]"),
            "Float List": (FIELD_TYPE_LIST_FLOAT, "[0.0, 0.0]"),
            "Boolean List": (FIELD_TYPE_LIST_BOOLEAN, "[True, True]"),
        }

        # Handle date-based list types which need current time formatting
        now = datetime.now()
        date_list_types = {
            "Date List": (
                FIELD_TYPE_LIST_DATE,
                f"['{now.strftime('%d/%m/%Y')}',"
                f" '{now.strftime('%d/%m/%Y')}']",
            ),
            "Datetime List": (
                FIELD_TYPE_LIST_DATETIME,
                f"['{now.strftime('%d/%m/%Y %H:%M:%S.%f')}',"
                f" '{now.strftime('%d/%m/%Y %H:%M:%S.%f')}']",
            ),
            "Time List": (
                FIELD_TYPE_LIST_TIME,
                f"['{now.strftime('%H:%M:%S.%f')}',"
                f" '{now.strftime('%H:%M:%S.%f')}']",
            ),
        }
        # Combine all type mappings
        all_types = {**type_mapping, **list_types, **date_list_types}

        if text in all_types:
            self.type, default_value = all_types[text]
            self.text_edit_default_value.setText(default_value)


class PopUpCloneTag(QDialog):
    """
    Dialog for cloning an existing tag with a new name.

    This dialog allows users to select an existing tag from the project and
    clone it with a new name.

    Attributes:
        signal_clone_tag: Signal emitted when a tag is successfully cloned

    Methods:
        - _connect_signals: Connect signals to slots
        - _populate_tag_list: Populate the tag list with available tags
        - _setup_ui: Set up the dialog UI elements
        - _show_error: Display an error message box
        - ok_action: Validates the new tag name and clones the selected tag
        - search_str: Filters the tag list based on a search string
    """

    # Signal emitted when tag is successfully cloned
    signal_clone_tag = pyqtSignal()

    def __init__(self, databrowser, project):
        """
        Initialize the dialog for cloning a tag.

        :param databrowser: The data browser instance
        :param project: The current project in the software
        """
        super().__init__()
        self.databrowser = databrowser
        self.project = project
        self.setWindowTitle("Clone a tag")
        self.setObjectName("Clone a tag")
        self.setModal(True)
        self._setup_ui()
        self._populate_tag_list(project)
        self._connect_signals(project)

    def _connect_signals(self, project):
        """Connect signals to slots.

        :param project: The current project
        """
        self.push_button_ok.clicked.connect(lambda: self.ok_action(project))
        self.search_bar.textChanged.connect(partial(self.search_str, project))

    def _populate_tag_list(self, project):
        """
        Populate the tag list with available tags from the project.

        :param project: The current project
        """
        _translate = QtCore.QCoreApplication.translate

        # Get all tags except system tags
        with project.database.data() as database_data:
            tags_list = database_data.get_field_names(COLLECTION_CURRENT)

        tags_list.remove(TAG_CHECKSUM)
        tags_list.remove(TAG_HISTORY)

        # Add tags to list widget
        for tag in tags_list:
            item = QtWidgets.QListWidgetItem(_translate("Dialog", tag))
            self.list_widget_tags.addItem(item)

        self.list_widget_tags.sortItems()

    def _setup_ui(self):
        """Set up the dialog UI elements."""
        _translate = QtCore.QCoreApplication.translate
        # New tag name components
        self.label_new_tag_name = QtWidgets.QLabel(
            _translate("Clone a tag", "New tag name:"), self
        )
        self.label_new_tag_name.setTextFormat(QtCore.Qt.AutoText)
        self.label_new_tag_name.setObjectName("label_new_tag_name")
        self.line_edit_new_tag_name = QtWidgets.QLineEdit(self)
        self.line_edit_new_tag_name.setObjectName("lineEdit_new_tag_name")
        # OK button
        self.push_button_ok = QtWidgets.QPushButton(
            _translate("Clone a tag", "OK"), self
        )
        self.push_button_ok.setObjectName("push_button_ok")
        # Bottom row layout
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.label_new_tag_name)
        hbox_buttons.addWidget(self.line_edit_new_tag_name)
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        # Tag list components
        self.label_tag_list = QtWidgets.QLabel(
            _translate("Clone a tag", "Available tags:"), self
        )
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        # Top row layout
        hbox_top = QHBoxLayout()
        hbox_top.addWidget(self.label_tag_list)
        hbox_top.addStretch(1)
        hbox_top.addWidget(self.search_bar)
        # Tag list widget
        self.list_widget_tags = QtWidgets.QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        self.list_widget_tags.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        # Main dialog layout
        vbox = QVBoxLayout()
        vbox.addLayout(hbox_top)
        vbox.addWidget(self.list_widget_tags)
        vbox.addLayout(hbox_buttons)
        self.setLayout(vbox)

    def _show_error(self, text, informative_text):
        """Display an error message box.

        :param text: The main error message text
        :param informative_text: The additional informative text
        """
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Critical)
        self.msg.setText(text)
        self.msg.setInformativeText(informative_text)
        self.msg.setWindowTitle("Error")
        self.msg.setStandardButtons(QMessageBox.Ok)
        self.msg.buttonClicked.connect(self.msg.close)
        self.msg.show()

    def ok_action(self, project):
        """
        Validate new tag name and clone the selected tag if valid.

        :param project: The current project
        """
        new_tag_name = self.line_edit_new_tag_name.text()
        selected_items = self.list_widget_tags.selectedItems()

        # Check if tag name already exists
        with project.database.data() as database_data:
            existing_tags = [
                tag["index"].split("|")[1]
                for tag in database_data.get_field_attributes(
                    COLLECTION_CURRENT
                )
            ]

        if new_tag_name in existing_tags:
            self._show_error(
                "This tag name already exists",
                "Please select another tag name",
            )

        elif not new_tag_name:
            self._show_error(
                "The tag name can't be empty", "Please select a tag name"
            )

        elif not selected_items:
            self._show_error(
                "The tag to clone must be selected",
                "Please select a tag to clone",
            )

        else:
            self.accept()
            self.tag_to_replace = selected_items[0].text()
            self.new_tag_name = new_tag_name
            self.databrowser.clone_tag_infos(
                self.tag_to_replace, self.new_tag_name
            )
            self.close()

    def search_str(self, project, search_text):
        """Filter the tag list based on the search string.

        :param project: The current project
        :param search_text: The search string to filter by
        """
        _translate = QtCore.QCoreApplication.translate

        # Get all tags except system tags
        with project.database.data() as database_data:
            all_tags = database_data.get_field_names(COLLECTION_CURRENT)

        all_tags.remove(TAG_CHECKSUM)
        all_tags.remove(TAG_HISTORY)

        # Filter tags by search text (case-insensitive)
        if search_text:
            search_text = search_text.upper()
            filtered_tags = [
                tag for tag in all_tags if search_text in tag.upper()
            ]

        else:
            filtered_tags = all_tags

        # Update the list widget
        self.list_widget_tags.clear()

        for tag_name in filtered_tags:
            self.list_widget_tags.addItem(
                QtWidgets.QListWidgetItem(_translate("Dialog", tag_name))
            )

        self.list_widget_tags.sortItems()


class PopUpClosePipeline(QDialog):
    """
    Dialog displayed when closing a modified pipeline editor.

    This dialog asks the user whether they want to save changes before
    closing the pipeline editor. It provides three options: save, don't
    save, or cancel.

    Signals:
        save_as_signal: Emitted when the user chooses to save the pipeline.
        do_not_save_signal: Emitted when the user chooses not to save
                            the pipeline.
        cancel_signal: Emitted when the user cancels the closing action.

    Attributes:
        bool_save_as (bool): Indicates if the pipeline should be saved
                             under a new name.
        bool_exit (bool): Indicates if the editor can be closed.
        pipeline_name (str): Name of the pipeline being edited.

    .. Methods:
        - _connect_signals: Connect button signals to their respective slots
        - _setup_ui: Set up the dialog's user interface
        - can_exit: returns the value of bool_exit
        - cancel_clicked: makes the actions to cancel the action
        - do_not_save_clicked: makes the actions not to save the pipeline
        - save_as_clicked: makes the actions to save the pipeline
    """

    save_as_signal = pyqtSignal()
    do_not_save_signal = pyqtSignal()
    cancel_signal = pyqtSignal()

    def __init__(self, pipeline_name):
        """
        Initialize the dialog with the pipeline name.

        :param pipeline_name (str):  Name of the pipeline (basename).

        """
        super().__init__()
        self.pipeline_name = pipeline_name
        self.bool_exit = False
        self.bool_save_as = False
        self._setup_ui()
        self._connect_signals()

    def _connect_signals(self):
        """
        Connect button signals to their respective slots.
        """
        self.push_button_save_as.clicked.connect(self.save_as_clicked)
        self.push_button_do_not_save.clicked.connect(self.do_not_save_clicked)
        self.push_button_cancel.clicked.connect(self.cancel_clicked)

    def _setup_ui(self):
        """
        Set up the dialog's user interface.
        """
        self.setWindowTitle("Confirm pipeline closing")
        label = QLabel(
            f"Do you want to close the pipeline without "
            f"saving {self.pipeline_name}?",
            self,
        )
        self.push_button_save_as = QPushButton("Save", self)
        self.push_button_do_not_save = QPushButton("Do not save", self)
        self.push_button_cancel = QPushButton("Cancel", self)
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.push_button_save_as)
        button_layout.addWidget(self.push_button_do_not_save)
        button_layout.addWidget(self.push_button_cancel)
        button_layout.addStretch(1)
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(label)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def can_exit(self):
        """Check if the editor can be closed.

        Returns (bool): True if the editor can be closed, False otherwise.
        """
        return self.bool_exit

    def cancel_clicked(self):
        """Handle the cancel button click.

        Sets bool_exit to False, emits cancel_signal, and closes the dialog.
        """
        self.bool_exit = False
        self.cancel_signal.emit()
        self.close()

    def do_not_save_clicked(self):
        """Handle the 'Do not save' button click.

        Sets bool_exit to True, emits do_not_save_signal,
        and closes the dialog.
        """
        self.bool_exit = True
        self.do_not_save_signal.emit()
        self.close()

    def save_as_clicked(self):
        """Handle the 'Save' button click.

        Sets bool_save_as and bool_exit to True, emits save_as_signal,
        and closes the dialog.
        """
        self.bool_save_as = True
        self.bool_exit = True
        self.save_as_signal.emit()
        self.close()


class PopUpDataBrowserCurrentSelection(QDialog):
    """
    Dialog to display and confirm the current data browser selection.

    This dialog shows a table of the currently selected document
    from the data browser and allows the user to confirm or cancel the
    selection. When confirmed, it updates the scan_list attribute of
    relevant components in the main window.

    Attributes:
        project: Current project in the software.
        databrowser: Data browser instance of the software.
        filter: List of the current documents in the data browser.
        main_window: Main window of the software.

    .. Methods:
        - _set_dialog_size: Set the dialog size based on screen resolution
        - _setup_ui: Set up the dialog's user interface
        - ok_clicked: updates the "scan_list" attribute of several widgets

    """

    def __init__(self, project, databrowser, filter, main_window):
        """
        Initialize the dialog with the current project and selection data.

        :param project: Current project in the software
        :param databrowser: Data browser instance of the software
        :param filter (list): List of the current documents in the data
                              browser
        :param main_window: Main window of the software

        """
        super().__init__()
        self.project = project
        self.databrowser = databrowser
        self.filter = filter
        self.main_window = main_window
        self._setup_ui()

    def _set_dialog_size(self):
        """Set the dialog size based on screen resolution."""
        screen_resolution = QApplication.instance().desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        self.setMinimumWidth(round(0.5 * width))
        self.setMinimumHeight(round(0.8 * height))

    def _setup_ui(self):
        """Set up the dialog's user interface."""
        self.setWindowTitle("Confirm the selection")
        self.setModal(True)
        # Create layout
        layout = QVBoxLayout()
        # Create and configure data browser table
        databrowser_table = data_browser.TableDataBrowser(
            self.project, self.databrowser, [TAG_FILENAME], False, False
        )
        old_scan_list = databrowser_table.scans_to_visualize
        databrowser_table.scans_to_visualize = self.filter
        databrowser_table.update_visualized_rows(old_scan_list)
        # Create buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.ok_clicked)
        buttons.rejected.connect(self.close)
        # Add widgets to layout
        layout.addWidget(databrowser_table)
        layout.addWidget(buttons)
        self.setLayout(layout)
        # Set dialog size based on screen resolution
        self._set_dialog_size()

    def ok_clicked(self):
        """
        Update the scan_list attribute of components when OK is clicked.

        This method propagates the current filter (selected documents)
        to various components in the main window's pipeline manager, and
        marks the data as sent in the data browser before closing the dialog.
        """
        # Update scan_list in all required components
        pipeline_manager = self.main_window.pipeline_manager
        components = [
            pipeline_manager,
            pipeline_manager.nodeController,
            pipeline_manager.pipelineEditorTabs,
            pipeline_manager.iterationTable,
        ]

        for component in components:
            component.scan_list = self.filter

        self.databrowser.data_sent = True
        self.close()


class PopUpDeletedProject(QMessageBox):
    """
    Message box that displays a list of deleted, renamed, or moved projects.

    This dialog appears when the software starts and detects that previously
    available projects are no longer accessible at their expected locations.

    Attributes:
        deleted_projects (list): List of project names that are no longer
                                 accessible.

    .. Methods:
        - _connect_signals: Connect button signals to their respective slots
        - _setup_message_box: Configure the message box appearance and
                              content
    """

    def __init__(self, deleted_projects):
        """
        Initialize the message box with a list of inaccessible projects.

        :param deleted_projects (list): List of project names that are no
                                        longer accessible (deleted, renamed,
                                        or moved).
        """
        super().__init__()
        self.deleted_projects = deleted_projects
        self._setup_message_box()
        self._connect_signals()
        self.exec()

    def _connect_signals(self):
        """Connect button signals to their respective slots."""
        self.buttonClicked.connect(self.close)

    def _setup_message_box(self):
        """Configure the message box appearance and content."""
        # Create the message with the list of deleted projects
        project_list = "\n".join(
            f"- {project}" for project in self.deleted_projects
        )
        message = (
            f"These projects have been renamed, "
            f"moved or deleted:\n{project_list}"
        )
        # Set message box properties
        self.setIcon(QMessageBox.Warning)
        self.setText("Deleted projects")
        self.setInformativeText(message)
        self.setWindowTitle("Warning")
        self.setStandardButtons(QMessageBox.Ok)


class PopUpDeleteProject(QDialog):
    """
    Dialog for deleting selected projects.

    Allows the user to select and delete one or more projects
    from the projects directory after confirmation.

    .. Methods:
        - _delete_project: Handles project deletion
        - _setup_buttons: Creates and configures the dialog buttons
        - _setup_layout: Configures the main layout of the dialog
        - _setup_ui: Sets up the user interface components
        - ok_clicked: delete the selected projects after confirmation

    """

    def __init__(self, main_window):
        """
        Initializes the delete project dialog.

        :param main_window (QMainWindow): The main application window
        """
        super().__init__()
        self.setWindowTitle("Delete project")
        config = Config()
        self.project_path = config.getPathToProjectsFolder()
        self.main_window = main_window
        self._setup_ui()

    def _delete_project(self, project_path, opened_projects):
        """
        Handles project deletion, updating application state accordingly.

        :param project_path (str): The path of the project to delete
        :param opened_projects (list): The list of currently opened projects
        """

        if os.path.abspath(self.main_window.project.folder) == os.path.abspath(
            project_path
        ):
            self.main_window.project = Project(None, True)
            self.main_window.update_project("")

        project_rel_path = os.path.relpath(project_path)

        if project_rel_path in self.main_window.saved_projects.pathsList:
            self.main_window.saved_projects.removeSavedProject(
                project_rel_path
            )
            self.main_window.update_recent_projects_actions()

        if project_rel_path in opened_projects:
            opened_projects.remove(project_rel_path)

        shutil.rmtree(project_path)

    def _setup_buttons(self):
        """Creates and configures the dialog buttons."""
        self.h_box_bottom = QHBoxLayout()
        self.h_box_bottom.addStretch(1)
        self.push_button_ok = QPushButton("OK")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)
        self.h_box_bottom.addWidget(self.push_button_ok)
        self.push_button_cancel = QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)
        self.h_box_bottom.addWidget(self.push_button_cancel)

    def _setup_layout(self):
        """Configures the main layout of the dialog."""
        self.scroll = QScrollArea()
        self.widget = QWidget()
        self.widget.setLayout(self.v_box)
        self.scroll.setWidget(self.widget)
        self.final = QVBoxLayout()
        self.final.addWidget(self.scroll)
        self.final_layout = QVBoxLayout()
        self.final_layout.addLayout(self.final)
        self.final_layout.addLayout(self.h_box_bottom)
        self.setLayout(self.final_layout)

    def _setup_ui(self):
        """Sets up the user interface components."""
        self.v_box = QVBoxLayout()
        self.v_box.addWidget(QLabel("Select projects to delete:"))
        self.check_boxes = [
            QCheckBox(project)
            for project in os.listdir(self.project_path)
            if os.path.isdir(os.path.join(self.project_path, project))
        ]

        for check_box in self.check_boxes:
            self.v_box.addWidget(check_box)

        self._setup_buttons()
        self._setup_layout()

    def ok_clicked(self):
        """
        Deletes the selected projects after user confirmation.
        """
        selected_projects = [
            cb.text() for cb in self.check_boxes if cb.isChecked()
        ]

        if not selected_projects:
            self.accept()
            self.close()
            return

        config = Config()
        opened_projects = config.get_opened_projects()
        reply = None

        for name in selected_projects:
            project_path = os.path.join(self.project_path, name)

            if reply not in (QMessageBox.YesToAll, QMessageBox.NoToAll):
                reply = QMessageBox.warning(
                    self,
                    "populse_mia - Warning: Delete project",
                    f"Do you really want to delete the {name} project?",
                    QMessageBox.Yes
                    | QMessageBox.No
                    | QMessageBox.YesToAll
                    | QMessageBox.NoToAll,
                )

            if reply in (QMessageBox.Yes, QMessageBox.YesToAll):
                self._delete_project(project_path, opened_projects)

        config.set_opened_projects(opened_projects)
        config.saveConfig()
        self.accept()
        self.close()


class PopUpFilterSelection(QDialog):
    """Is called when the user wants to open a filter that has already been
       saved.

    :Methods:
        - cancel_clicked: closes the pop-up
        - ok_clicked: actions when the "OK" button is clicked
        - search_str: matches the searched pattern with the saved filters

    """

    def __init__(self, project):
        """Initialization.

        :param project: current project in the software

        """

        super().__init__()
        self.project = project
        self.setModal(True)

        _translate = QtCore.QCoreApplication.translate

        # The "Filter list" label
        self.label_filter_list = QtWidgets.QLabel(self)
        self.label_filter_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_filter_list.setObjectName("label_filter_list")
        self.label_filter_list.setText(
            _translate("main_window", "Available filters:")
        )

        # The search bar to search in the list of filters
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.search_str)

        # The list of filters
        self.list_widget_filters = QtWidgets.QListWidget(self)
        self.list_widget_filters.setObjectName("listWidget_tags")
        self.list_widget_filters.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )

        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.setText("OK")
        self.push_button_ok.clicked.connect(self.ok_clicked)

        self.push_button_cancel = QtWidgets.QPushButton(self)
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.setText("Cancel")
        self.push_button_cancel.clicked.connect(self.cancel_clicked)

        hbox_top_left = QHBoxLayout()
        hbox_top_left.addWidget(self.label_filter_list)
        hbox_top_left.addWidget(self.search_bar)

        vbox_top_left = QVBoxLayout()
        vbox_top_left.addLayout(hbox_top_left)
        vbox_top_left.addWidget(self.list_widget_filters)

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        hbox_buttons.addWidget(self.push_button_cancel)

        vbox_final = QVBoxLayout()
        vbox_final.addLayout(vbox_top_left)
        vbox_final.addLayout(hbox_buttons)

        self.setLayout(vbox_final)

    def cancel_clicked(self):
        """Closes the pop-up."""

        self.close()

    def ok_clicked(self):
        """Actions when the "OK" button is clicked."""

        # Has to be override in the PopUpSelectFilter* classes
        pass

    def search_str(self, str_search):
        """Matches the searched pattern with the saved filters.

        :param str_search: string pattern to search

        """

        return_list = []
        if str_search != "":
            for filter in self.project.filters:
                if str_search.upper() in filter.name.upper():
                    return_list.append(filter.name)
        else:
            for filter in self.project.filters:
                return_list.append(filter.name)

        for idx in range(self.list_widget_filters.count()):
            item = self.list_widget_filters.item(idx)
            if item.text() in return_list:
                item.setHidden(False)
            else:
                item.setHidden(True)


class PopUpInformation(QWidget):
    """Is called when the user wants to display the current project's
    information."""

    # Signal that will be emitted at the end to tell that the project
    # has been created
    signal_preferences_change = pyqtSignal()

    def __init__(self, project):
        """Initialization.

        :param project: current project in the software

        """
        super().__init__()
        name_label = QLabel("Name: ")
        self.name_value = QLineEdit(project.getName())
        folder_label = QLabel(f"Root folder: {project.folder}")
        date_label = QLabel(f"Date of creation: {project.getDate()}")
        box = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(name_label)
        row.addWidget(self.name_value)
        box.addLayout(row)
        box.addWidget(folder_label)
        box.addWidget(date_label)
        box.addStretch(1)
        self.setLayout(box)


class PopUpInheritanceDict(QDialog):
    """Is called to select from which input the output will inherit the tags.

    :Methods:
        - on_clicked: event when radiobutton is clicked
        - ok_clicked: event when ok button is clicked
        - okall_clicked: event when Ok all button is clicked
        - ignore_clicked: event when ignore button is clicked
        - ignoreall_clicked:event when ignore all plugs button is clicked
        - ignore_node_clicked: event when ignore all nodes button is clicked

    """

    def __init__(self, values, node_name, plug_name, iterate):
        """Initialization

        :param values: A dictionary with input name as key and their paths
         as values
        :param node_name: name of the current node
        :param plug_name: name of the current output plug
        :param iterate: boolean, iteration or not
        """
        super().__init__()
        self.setModal(True)
        self.setObjectName("Dialog")
        self.setWindowTitle(f"Plug inherited in {node_name}")
        self.ignore = False
        self.all = False
        self.everything = False
        label = (
            f"In the node <b><i>{node_name}</i></b>, from which input plug, "
            f"the output plug <b><i>{plug_name}</i></b> should inherit "
            f"the tags?:"
        )
        v_box_values = QtWidgets.QVBoxLayout()
        v_box_values.addWidget(QLabel(label))
        checked = True

        for key in values:
            radiobutton = QRadioButton(key, self)
            radiobutton.value = values[key]
            radiobutton.key = key
            radiobutton.setChecked(checked)

            if checked:
                self.value = radiobutton.value
                self.key = radiobutton.key

            checked = False
            radiobutton.toggled.connect(self.on_clicked)
            v_box_values.addWidget(radiobutton)
            v_box_values.addStretch(1)

        h_box_buttons = QtWidgets.QHBoxLayout()
        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setText("OK")
        self.push_button_ok.clicked.connect(self.ok_clicked)
        self.push_button_ok.setToolTip(
            f"<i>{plug_name}</i> will inherit tags from {self.key}."
        )
        h_box_buttons.addWidget(self.push_button_ok)

        self.push_button_ignore = QtWidgets.QPushButton(self)
        self.push_button_ignore.setText("Ignore")
        self.push_button_ignore.clicked.connect(self.ignore_clicked)
        self.push_button_ignore.setToolTip(
            f"<i>{plug_name}</i> will not inherit any tags."
        )
        h_box_buttons.addWidget(self.push_button_ignore)

        self.push_button_okall = QtWidgets.QPushButton(self)
        self.push_button_okall.setText("OK for all output plugs")
        self.push_button_okall.clicked.connect(self.okall_clicked)
        self.push_button_okall.setToolTip(
            f"All the output plugs from <i>{node_name}</i> will inherit tags"
            f" from {self.key}."
        )
        h_box_buttons.addWidget(self.push_button_okall)

        self.push_button_ignoreall = QtWidgets.QPushButton(self)
        self.push_button_ignoreall.setText("Ignore for all output plugs")
        self.push_button_ignoreall.clicked.connect(self.ignoreall_clicked)
        self.push_button_ignoreall.setToolTip(
            f"All the output plugs from <i>{node_name}</i> will not "
            f"inherit any tags."
        )
        h_box_buttons.addWidget(self.push_button_ignoreall)

        self.push_button_ignore_node = QtWidgets.QPushButton(self)
        self.push_button_ignore_node.setText(
            "Ignore for all nodes in the pipeline"
        )
        self.push_button_ignore_node.clicked.connect(self.ignore_node_clicked)
        self.push_button_ignore_node.setToolTip(
            "No tags will be inherited for the whole pipeline."
        )
        v_box_values.addLayout(h_box_buttons)

        v_box_values.addWidget(self.push_button_ignore_node)

        if iterate:
            label = "<i>These choices will be valid for each iteration.</i>"
            v_box_values.addWidget(QLabel(label))

        self.setLayout(v_box_values)

    def on_clicked(self):
        """Event when radiobutton is clicked"""
        radiobutton = self.sender()
        self.value = radiobutton.value
        self.key = radiobutton.key

    def ok_clicked(self):
        """Event when ok button is clicked"""
        self.accept()
        self.close()

    def okall_clicked(self):
        """Event when Ok all button is clicked"""
        self.all = True
        self.accept()
        self.close()

    def ignore_clicked(self):
        """Event when ignore button is clicked"""
        self.ignore = True
        self.accept()
        self.close()

    def ignoreall_clicked(self):
        """Event when ignore all plugs button is clicked"""
        self.ignore = True
        self.all = True
        self.accept()
        self.close()

    def ignore_node_clicked(self):
        """Event when ignore all nodes button is clicked"""
        self.ignore = True
        self.all = True
        self.everything = True
        self.accept()
        self.close()


class PopUpMultipleSort(QDialog):
    """Is called to sort the data browser's table depending on multiple tags.

    .. Methods:
        - add_tag: adds a push button
        - fill_values: fills the values list when a tag is added or removed
        - refresh_layout: updates the layouts (especially when a tag push
          button is added or removed)
        - remove_tag: removes a push buttons and makes the changes in the
          list of values
        - select_tag: calls a pop-up to choose a tag
        - sort_scans: collects the information and send them to the data
          browser

    """

    def __init__(self, project, table_data_browser):
        """Initialization.

        :param project: current project in the software
        :param table_data_browser: data browser's table of the software

        """

        super().__init__()
        self.project = project
        self.table_data_browser = table_data_browser

        self.setModal(True)
        self.setWindowTitle("Multiple sort")

        # values_list will contain the different values of each selected tag
        self.values_list = [[], []]
        self.list_tags = []

        self.label_tags = QLabel("Tags: ")

        # Each push button will allow the user to add a tag to the count table
        push_button_tag_1 = QPushButton()
        push_button_tag_1.setText("Tag n°1")
        push_button_tag_1.clicked.connect(lambda: self.select_tag(0))

        push_button_tag_2 = QPushButton()
        push_button_tag_2.setText("Tag n°2")
        push_button_tag_2.clicked.connect(lambda: self.select_tag(1))

        # The list of all the push buttons (the user can add as many as
        # he or she wants)
        self.push_buttons = []
        self.push_buttons.insert(0, push_button_tag_1)
        self.push_buttons.insert(1, push_button_tag_2)

        # Labels to add/remove a tag (a push button)
        sources_images_dir = Config().getSourceImageDir()
        self.remove_tag_label = ClickableLabel()
        remove_tag_picture = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "red_minus.png"))
        )
        remove_tag_picture = remove_tag_picture.scaledToHeight(20)
        self.remove_tag_label.setPixmap(remove_tag_picture)
        self.remove_tag_label.clicked.connect(self.remove_tag)

        self.add_tag_label = ClickableLabel()
        self.add_tag_label.setObjectName("plus")
        add_tag_picture = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "green_plus.png"))
        )
        add_tag_picture = add_tag_picture.scaledToHeight(15)
        self.add_tag_label.setPixmap(add_tag_picture)
        self.add_tag_label.clicked.connect(self.add_tag)

        # Combobox to choose if the sort order is ascending or descending
        self.combo_box = QComboBox()
        self.combo_box.addItems(["Ascending", "Descending"])

        # Push button that is pressed to launch the computations
        self.push_button_sort = QPushButton()
        self.push_button_sort.setText("Sort scans")
        self.push_button_sort.clicked.connect(self.sort_scans)

        # Layouts
        self.v_box_final = QVBoxLayout()
        self.setLayout(self.v_box_final)
        self.refresh_layout()

    def add_tag(self):
        """Adds a push button."""

        push_button = QPushButton()
        push_button.setText(f"Tag n°{len(self.push_buttons) + 1}")
        push_button.clicked.connect(
            lambda: self.select_tag(len(self.push_buttons) - 1)
        )
        self.push_buttons.insert(len(self.push_buttons), push_button)
        self.refresh_layout()

    def fill_values(self, idx):
        """Fills the values list when a tag is added or removed.

        :param idx: index of the pressed push button

        """
        tag_name = self.push_buttons[idx].text()

        if len(self.values_list) <= idx:
            self.values_list.insert(idx, [])

        if self.values_list[idx] is not None:
            self.values_list[idx] = []

        with self.project.database.data() as database_data:

            for scan in database_data.get_field_names(COLLECTION_CURRENT):
                current_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan,
                    field=tag_name,
                )

                if current_value not in self.values_list[idx]:
                    self.values_list[idx].append(current_value)

    def refresh_layout(self):
        """Updates the layouts (especially when a tag push button is added or
        removed).

        """

        self.h_box_top = QHBoxLayout()
        self.h_box_top.setSpacing(10)
        self.h_box_top.addWidget(self.label_tags)

        for tag_label in self.push_buttons:
            self.h_box_top.addWidget(tag_label)

        self.h_box_top.addWidget(self.add_tag_label)
        self.h_box_top.addWidget(self.remove_tag_label)
        self.h_box_top.addWidget(self.combo_box)
        self.h_box_top.addWidget(self.push_button_sort)
        self.h_box_top.addStretch(1)

        self.v_box_final.addLayout(self.h_box_top)

    def remove_tag(self):
        """Removes a push buttons and makes the changesn in the list of
        values.

        """

        push_button = self.push_buttons[-1]
        push_button.deleteLater()
        push_button = None
        del self.push_buttons[-1]
        del self.values_list[-1]
        self.refresh_layout()

    def select_tag(self, idx):
        """Calls a pop-up to choose a tag.

        :param idx: index of the pressed push button

        """

        with self.project.database.data() as database_data:
            pop_up = PopUpSelectTagCountTable(
                self.project,
                database_data.get_shown_tags(),
                self.push_buttons[idx].text(),
            )

        if pop_up.exec_():
            self.push_buttons[idx].setText(pop_up.selected_tag)
            self.fill_values(idx)

    def sort_scans(self):
        """Collects the information and send them to the data browser."""
        self.order = self.combo_box.itemText(self.combo_box.currentIndex())

        with self.project.database.data() as database_data:

            for push_button in self.push_buttons:

                if push_button.text() in database_data.get_field_names(
                    COLLECTION_CURRENT
                ):
                    self.list_tags.append(push_button.text())

        self.accept()
        self.table_data_browser.multiple_sort_infos(self.list_tags, self.order)


class PopUpNewProject(QFileDialog):
    """Is called when the user wants to create a new project.

    .. Method:
        - get_filename: sets the widget's attributes depending on the
          selected file name

    """

    # Signal that will be emitted at the end to tell that the project
    # has been created
    signal_create_project = pyqtSignal()

    def __init__(self):
        """Initialization."""

        # import set_projects_directory_as_default only here to prevent
        # circular import issue
        from populse_mia.utils import set_projects_directory_as_default

        super().__init__()
        self.setLabelText(QFileDialog.Accept, "Create")
        self.setAcceptMode(QFileDialog.AcceptSave)

        # Setting the projects directory as default
        set_projects_directory_as_default(self)

    def get_filename(self, file_name_tuple):
        """Sets the widget's attributes depending on the selected file name.

        :param file_name_tuple: tuple obtained with the selectedFiles method
        :return: real file name

        """
        # import message_already_exists only here to prevent
        # circular import issue
        from populse_mia.utils import message_already_exists

        file_name = file_name_tuple[0]
        if file_name:
            entire_path = os.path.abspath(file_name)
            self.path, self.name = os.path.split(entire_path)
            self.relative_path = os.path.relpath(file_name)
            self.relative_subpath = os.path.relpath(self.path)

            if not os.path.exists(self.relative_path):
                self.close()
                # A signal is emitted to tell that the project has been created
                self.signal_create_project.emit()
            else:
                message_already_exists()

        return file_name


class PopUpOpenProject(QFileDialog):
    """Is called when the user wants to open project.

    .. Method:
        - get_filename: sets the widget's attributes depending on the selected
           file name

    """

    # Signal that will be emitted at the end to tell that the project
    # has been created
    signal_create_project = pyqtSignal()

    def __init__(self):
        # import set_projects_directory_as_default only here to prevent
        # circular import issue
        from populse_mia.utils import set_projects_directory_as_default

        super().__init__()

        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setFileMode(QFileDialog.Directory)

        # Setting the projects directory as default
        set_projects_directory_as_default(self)

    def get_filename(self, file_name_tuple):
        """Sets the widget's attributes depending on the selected file name.

        :param file_name_tuple: tuple obtained with the selectedFiles method

        """
        # import message_already_exists only here to prevent
        # circular import issue
        from populse_mia.utils import message_already_exists

        file_name = file_name_tuple[0]

        if file_name:
            entire_path = os.path.abspath(file_name)
            self.path, self.name = os.path.split(entire_path)
            self.relative_path = os.path.relpath(file_name)

            # If the file exists
            if os.path.exists(entire_path):
                self.close()
                # A signal is emitted to tell that the project has been created
                self.signal_create_project.emit()
            else:
                message_already_exists()


class PopUpPreferences(QDialog):
    """Is called when the user wants to change the software preferences.

    .. Methods:
        - browse_afni: called when afni browse button is clicked
        - browse_ants: called when ants browse button is clicked
        - browse_fsl: called when fsl browse button is clicked
        - browse_matlab: called when matlab browse button is clicked
        - browse_matlab_standalone: called when matlab browse button is clicked
        - browse_mri_conv_path: called when "MRIManager.jar" browse
          button is clicked
        - browse_mrtrix: called when mrtrix browse button is clicked
        - browse_projects_save_path: called when "Projects folder" browse
          button is clicked
        - browse_resources_path: called when "resources" browse button is
          clicked
        - browse_spm: called when spm browse button is clicked
        - browse_spm_standalone: called when spm standalone browse button
          is clicked
        - change_admin_psswd: method to change the admin password
        - control_checkbox_toggled: check before changing controller version
        - edit_capsul_config: capsul engine edition
        - edit_config_file: create a window to view, edit the mia
           configuration file
        - findChar: highlights characters in red when using the Find button
            when editing configuration
        - ok_clicked: saves the modifications to the config file and apply them
        - use_afni_changed: called when the use_afni checkbox is changed
        - use_ants_changed: called when the use_ants checkbox is changed
        - use_fsl_changed: called when the use_fsl checkbox is changed
        - use_matlab_changed: called when the use_matlab checkbox is changed
        - use_matlab_standalone_changed: called when the use_matlab_standalone
           checkbox is changed
        - use_mrtrix_changed: called when the use_mrtrix checkbox is changed
        - use_spm_changed: called when the use_spm checkbox is changed
        - use_spm_standalone_changed: called when the use_spm_standalone
          checkbox is changed
        - admin_mode_switch: called when the admin mode checkbox
           is clicked

    """

    # Signal that will be emitted at the end to tell that the project
    # has been created
    signal_preferences_change = pyqtSignal()
    use_clinical_mode_signal = pyqtSignal()
    not_use_clinical_mode_signal = pyqtSignal()

    def __init__(self, main_window):
        """Initialization.

        :param main_window: main window object of the software

        """

        super().__init__()
        self.setModal(True)
        self.main_window = main_window

        _translate = QtCore.QCoreApplication.translate

        self.setObjectName("Dialog")
        self.setWindowTitle("MIA preferences")

        self.clicked = 0

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setEnabled(True)
        self.salt = "P0pulseM1@"

        config = Config()

        # The 'Tools" tab
        self.tab_tools = QtWidgets.QWidget()
        self.tab_tools.setObjectName("tab_tools")
        self.tab_widget.addTab(self.tab_tools, _translate("Dialog", "Tools"))

        # Groupbox "Global preferences"
        self.groupbox_global = QtWidgets.QGroupBox("Global preferences")

        # Auto save
        self.save_checkbox = QCheckBox("", self)
        self.save_label = QLabel("Auto save")

        if config.isAutoSave() is True:
            self.save_checkbox.setChecked(1)

        h_box_auto_save = QtWidgets.QHBoxLayout()
        h_box_auto_save.addWidget(self.save_checkbox)
        h_box_auto_save.addWidget(self.save_label)
        h_box_auto_save.addStretch(1)

        # Clinical mode
        self.clinical_mode_checkbox = QCheckBox("", self)

        if config.get_use_clinical() is True:
            self.clinical_mode_checkbox.setChecked(1)

        self.clinical_mode_label = QLabel("Clinical mode")
        h_box_clinical = QtWidgets.QHBoxLayout()
        h_box_clinical.addWidget(self.clinical_mode_checkbox)
        h_box_clinical.addWidget(self.clinical_mode_label)
        h_box_clinical.addStretch(1)

        # Admin mode + Change password + Edit config
        self.admin_mode_checkbox = QCheckBox("", self)
        self.admin_mode_checkbox.clicked.connect(self.admin_mode_switch)
        self.admin_mode_label = QLabel("Admin mode")
        self.change_psswd = QPushButton(
            "Change password", default=False, autoDefault=False
        )
        self.edit_config = QPushButton(
            "Edit config", default=False, autoDefault=False
        )
        self.change_psswd.clicked.connect(partial(self.change_admin_psswd, ""))
        self.edit_config.clicked.connect(self.edit_config_file)

        if not config.get_user_mode():
            self.admin_mode_checkbox.setChecked(1)
            self.change_psswd.setVisible(True)
            self.edit_config.setVisible(True)

        else:
            self.admin_mode_checkbox.setChecked(0)
            self.change_psswd.setVisible(False)
            self.edit_config.setVisible(False)

        h_box_admin_mode = QtWidgets.QHBoxLayout()
        h_box_admin_mode.addWidget(self.admin_mode_checkbox)
        h_box_admin_mode.addWidget(self.admin_mode_label)
        h_box_admin_mode.addStretch(1)

        h_box_change_psswd = QtWidgets.QHBoxLayout()
        h_box_change_psswd.addWidget(self.change_psswd)
        h_box_change_psswd.addStretch(1)

        h_box_edit_config = QtWidgets.QHBoxLayout()
        h_box_edit_config.addWidget(self.edit_config)
        h_box_edit_config.addStretch(1)

        # Version 1 controller
        self.control_checkbox = QCheckBox("", self)
        self.control_label = QLabel("Version 1 controller")

        if config.isControlV1() is True:
            self.control_checkbox.setChecked(1)

        self.control_checkbox_changed = main_window.get_controller_version()
        self.control_checkbox.clicked.connect(
            partial(self.control_checkbox_toggled, main_window)
        )

        h_box_control = QtWidgets.QHBoxLayout()
        h_box_control.addWidget(self.control_checkbox)
        h_box_control.addWidget(self.control_label)
        h_box_control.addStretch(1)

        # Max thumbnails number at the data browser bottom
        self.max_thumbnails_label = QLabel(
            "Number of thumbnails in Data Browser:"
        )
        self.max_thumbnails_box = QtWidgets.QSpinBox()
        self.max_thumbnails_box.setMinimum(1)
        self.max_thumbnails_box.setMaximum(15)
        self.max_thumbnails_box.setValue(config.get_max_thumbnails())
        self.max_thumbnails_box.setSingleStep(1)

        h_box_max_thumbnails = QtWidgets.QHBoxLayout()
        h_box_max_thumbnails.addWidget(self.max_thumbnails_box)
        h_box_max_thumbnails.addStretch(1)

        # Radiological vs neurological orientation in miniviewer data browser
        self.radioView_checkbox = QCheckBox("", self)
        self.radioView_label = QLabel(
            "Radiological orientation in miniviewer (data browser)"
        )

        if config.isRadioView() is True:
            self.radioView_checkbox.setChecked(1)

        h_box_radioView = QtWidgets.QHBoxLayout()
        h_box_radioView.addWidget(self.radioView_checkbox)
        h_box_radioView.addWidget(self.radioView_label)
        h_box_radioView.addStretch(1)

        # Draws graphic objects
        v_box_global = QtWidgets.QVBoxLayout()
        v_box_global.addLayout(h_box_auto_save)
        v_box_global.addLayout(h_box_clinical)
        v_box_global.addLayout(h_box_admin_mode)
        v_box_global.addLayout(h_box_change_psswd)
        v_box_global.addLayout(h_box_edit_config)
        v_box_global.addLayout(h_box_control)
        v_box_global.addWidget(self.max_thumbnails_label)
        v_box_global.addLayout(h_box_max_thumbnails)
        v_box_global.addLayout(h_box_radioView)

        self.groupbox_global.setLayout(v_box_global)

        # Groupbox "Projects preferences"
        self.groupbox_projects = QtWidgets.QGroupBox("Projects preferences")

        # Projects folder label/line edit
        self.projects_save_path_label = QLabel("Projects folder:")
        self.projects_save_path_line_edit = QLineEdit(
            config.get_projects_save_path()
        )
        self.projects_save_path_browse = QPushButton("Browse")
        self.projects_save_path_browse.clicked.connect(
            self.browse_projects_save_path
        )

        # Max projects in "Saved projects"
        self.max_projects_label = QLabel(
            'Number of projects in "Saved projects":'
        )
        self.max_projects_box = QtWidgets.QSpinBox()
        self.max_projects_box.setMinimum(1)
        self.max_projects_box.setMaximum(20)
        self.max_projects_box.setValue(config.get_max_projects())
        # self.max_projects_box.setDecimals(0)
        self.max_projects_box.setSingleStep(1)

        # Draws graphic objects
        h_box_projects_save = QtWidgets.QHBoxLayout()
        h_box_projects_save.addWidget(self.projects_save_path_line_edit)
        h_box_projects_save.addWidget(self.projects_save_path_browse)

        v_box_projects_save = QtWidgets.QVBoxLayout()
        v_box_projects_save.addWidget(self.projects_save_path_label)
        v_box_projects_save.addLayout(h_box_projects_save)

        h_box_max_projects = QtWidgets.QHBoxLayout()
        h_box_max_projects.addWidget(self.max_projects_box)
        h_box_max_projects.addStretch(1)

        v_box_max_projects = QtWidgets.QVBoxLayout()
        v_box_max_projects.addWidget(self.max_projects_label)
        v_box_max_projects.addLayout(h_box_max_projects)

        projects_layout = QVBoxLayout()
        projects_layout.addLayout(v_box_projects_save)
        projects_layout.addLayout(v_box_max_projects)

        self.groupbox_projects.setLayout(projects_layout)

        # Groupbox "POPULSE third party preferences"
        self.groupbox_populse = QtWidgets.QGroupBox(
            "POPULSE third party preference"
        )

        # MRI File Manager folder label/line edit
        self.mri_conv_path_label = QLabel(
            "Absolute path to MRIManager.jar "
            "file (e.g., mri_conv_dir/"
            "MRIFileManager/MRIManager.jar):"
        )
        self.mri_conv_path_line_edit = QLineEdit(config.get_mri_conv_path())
        self.mri_conv_path_browse = QPushButton("Browse")
        self.mri_conv_path_browse.clicked.connect(self.browse_mri_conv_path)

        # Draws graphic objects
        h_box_mri_conv = QtWidgets.QHBoxLayout()
        h_box_mri_conv.addWidget(self.mri_conv_path_line_edit)
        h_box_mri_conv.addWidget(self.mri_conv_path_browse)

        v_box_mri_conv = QtWidgets.QVBoxLayout()
        v_box_mri_conv.addWidget(self.mri_conv_path_label)
        v_box_mri_conv.addLayout(h_box_mri_conv)

        populse_layout = QVBoxLayout()
        populse_layout.addLayout(v_box_mri_conv)

        self.groupbox_populse.setLayout(populse_layout)

        # Groupbox "External resources preferences"
        self.groupbox_resources = QtWidgets.QGroupBox(
            "External resources preferences"
        )

        # Resources folder label/line edit
        self.resources_path_label = QLabel(
            "Absolute path to the external resources data (some processes may "
            "require external data to function properly):"
        )
        self.resources_path_line_edit = QLineEdit(config.get_resources_path())
        self.resources_path_browse = QPushButton("Browse")
        self.resources_path_browse.clicked.connect(self.browse_resources_path)

        # Draws graphic objects
        h_box_resources = QtWidgets.QHBoxLayout()
        h_box_resources.addWidget(self.resources_path_line_edit)
        h_box_resources.addWidget(self.resources_path_browse)

        v_box_resources = QtWidgets.QVBoxLayout()
        v_box_resources.addWidget(self.resources_path_label)
        v_box_resources.addLayout(h_box_resources)

        resources_layout = QVBoxLayout()
        resources_layout.addLayout(v_box_resources)

        self.groupbox_resources.setLayout(resources_layout)

        # Final tab layouts
        h_box_top = QtWidgets.QHBoxLayout()
        h_box_top.addWidget(self.groupbox_global)
        h_box_top.addStretch(1)

        self.tab_tools_layout = QtWidgets.QVBoxLayout()
        self.tab_tools_layout.addLayout(h_box_top)
        self.tab_tools_layout.addWidget(self.groupbox_projects)
        self.tab_tools_layout.addWidget(self.groupbox_populse)
        self.tab_tools_layout.addWidget(self.groupbox_resources)
        self.tab_tools_layout.addStretch(1)
        self.tab_tools.setLayout(self.tab_tools_layout)

        # The 'OK' push button
        self.push_button_ok = QtWidgets.QPushButton("OK")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)

        # The 'Cancel' push button
        self.push_button_cancel = QtWidgets.QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)

        self.status_label = QLabel("")

        # Buttons layouts
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.status_label)
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        hbox_buttons.addWidget(self.push_button_cancel)

        vbox = QVBoxLayout()
        vbox.addWidget(self.tab_widget)
        vbox.addLayout(hbox_buttons)

        # The 'Pipeline' tab
        self.tab_pipeline = QtWidgets.QWidget()
        self.tab_pipeline.setObjectName("tab_pipeline")
        self.tab_widget.addTab(
            self.tab_pipeline, _translate("Dialog", "Pipeline")
        )

        # Groupbox "Matlab"
        self.groupbox_matlab = QtWidgets.QGroupBox("Matlab")
        self.use_matlab_label = QLabel("Use Matlab")
        self.use_matlab_checkbox = QCheckBox("", self)

        self.matlab_label = QLabel(
            "Matlab path (e.g., matlab_dir/bin/matlab):"
        )
        self.matlab_choice = QLineEdit(config.get_matlab_path())
        self.matlab_browse = QPushButton("Browse")
        self.matlab_browse.clicked.connect(self.browse_matlab)

        self.use_matlab_standalone_label = QLabel("Use Matlab standalone")
        self.use_matlab_standalone_checkbox = QCheckBox("", self)
        self.matlab_standalone_label = QLabel(
            "Matlab standalone path (e.g., MCR_dir/v95):"
        )
        self.matlab_standalone_choice = QLineEdit(
            config.get_matlab_standalone_path()
        )
        self.matlab_standalone_browse = QPushButton("Browse")
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

        h_box_use_matlab_standalone = QtWidgets.QHBoxLayout()
        h_box_use_matlab_standalone.addWidget(
            self.use_matlab_standalone_checkbox
        )
        h_box_use_matlab_standalone.addWidget(self.use_matlab_standalone_label)
        h_box_use_matlab_standalone.addStretch(1)

        h_box_matlab_standalone_path = QtWidgets.QHBoxLayout()
        h_box_matlab_standalone_path.addWidget(self.matlab_standalone_choice)
        h_box_matlab_standalone_path.addWidget(self.matlab_standalone_browse)

        v_box_matlab_standalone_path = QtWidgets.QVBoxLayout()
        v_box_matlab_standalone_path.addLayout(h_box_use_matlab_standalone)
        v_box_matlab_standalone_path.addWidget(self.matlab_standalone_label)
        v_box_matlab_standalone_path.addLayout(h_box_matlab_standalone_path)

        v_box_matlab = QtWidgets.QVBoxLayout()
        v_box_matlab.addLayout(h_box_use_matlab)
        v_box_matlab.addLayout(v_box_matlab_path)
        v_box_matlab.addLayout(v_box_matlab_standalone_path)

        self.groupbox_matlab.setLayout(v_box_matlab)

        # Groupbox "SPM"
        self.groupbox_spm = QtWidgets.QGroupBox("SPM")

        self.use_spm_label = QLabel("Use SPM")
        self.use_spm_checkbox = QCheckBox("", self)

        self.spm_label = QLabel("SPM path (e.g., spm_dir/spm12):")
        self.spm_choice = QLineEdit(config.get_spm_path())
        self.spm_browse = QPushButton("Browse")
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

        self.use_spm_standalone_label = QLabel("Use SPM standalone")
        self.use_spm_standalone_checkbox = QCheckBox("", self)

        self.spm_standalone_label = QLabel(
            "SPM standalone path (e.g., the "
            "directory hosting the run_spm12.sh "
            "file):"
        )
        self.spm_standalone_choice = QLineEdit(
            config.get_spm_standalone_path()
        )
        self.spm_standalone_browse = QPushButton("Browse")
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

        # Groupbox "FSL"
        self.groupbox_fsl = QtWidgets.QGroupBox("FSL")

        self.use_fsl_label = QLabel("Use FSL")
        self.use_fsl_checkbox = QCheckBox("", self)

        self.fsl_label = QLabel(
            "FSL config file (e.g., fsl_dir/etc/fslconf/fsl.sh):"
        )
        self.fsl_choice = QLineEdit(config.get_fsl_config())
        self.fsl_browse = QPushButton("Browse")
        self.fsl_browse.clicked.connect(self.browse_fsl)

        h_box_use_fsl = QtWidgets.QHBoxLayout()
        h_box_use_fsl.addWidget(self.use_fsl_checkbox)
        h_box_use_fsl.addWidget(self.use_fsl_label)
        h_box_use_fsl.addStretch(1)

        h_box_fsl_path = QtWidgets.QHBoxLayout()
        h_box_fsl_path.addWidget(self.fsl_choice)
        h_box_fsl_path.addWidget(self.fsl_browse)

        v_box_fsl_path = QtWidgets.QVBoxLayout()
        v_box_fsl_path.addWidget(self.fsl_label)
        v_box_fsl_path.addLayout(h_box_fsl_path)

        v_box_fsl = QtWidgets.QVBoxLayout()
        v_box_fsl.addLayout(h_box_use_fsl)
        v_box_fsl.addLayout(v_box_fsl_path)

        self.groupbox_fsl.setLayout(v_box_fsl)

        # Groupbox "AFNI"
        self.groupbox_afni = QtWidgets.QGroupBox("AFNI")

        self.use_afni_label = QLabel("Use AFNI")
        self.use_afni_checkbox = QCheckBox("", self)

        self.afni_label = QLabel("AFNI path (e.g. dir_containing_abin/abin):")
        self.afni_choice = QLineEdit(config.get_afni_path())
        self.afni_browse = QPushButton("Browse")
        self.afni_browse.clicked.connect(self.browse_afni)

        h_box_use_afni = QtWidgets.QHBoxLayout()
        h_box_use_afni.addWidget(self.use_afni_checkbox)
        h_box_use_afni.addWidget(self.use_afni_label)
        h_box_use_afni.addStretch(1)

        h_box_afni_path = QtWidgets.QHBoxLayout()
        h_box_afni_path.addWidget(self.afni_choice)
        h_box_afni_path.addWidget(self.afni_browse)

        v_box_afni_path = QtWidgets.QVBoxLayout()
        v_box_afni_path.addWidget(self.afni_label)
        v_box_afni_path.addLayout(h_box_afni_path)

        v_box_afni = QtWidgets.QVBoxLayout()
        v_box_afni.addLayout(h_box_use_afni)
        v_box_afni.addLayout(v_box_afni_path)

        self.groupbox_afni.setLayout(v_box_afni)

        # Groupbox "ANTS"
        self.groupbox_ants = QtWidgets.QGroupBox("ANTS")

        self.use_ants_label = QLabel("Use ANTS")
        self.use_ants_checkbox = QCheckBox("", self)

        self.ants_label = QLabel("ANTS path (e.g. ANTs_dir/bin):")
        self.ants_choice = QLineEdit(config.get_ants_path())
        self.ants_browse = QPushButton("Browse")
        self.ants_browse.clicked.connect(self.browse_ants)

        h_box_use_ants = QtWidgets.QHBoxLayout()
        h_box_use_ants.addWidget(self.use_ants_checkbox)
        h_box_use_ants.addWidget(self.use_ants_label)
        h_box_use_ants.addStretch(1)

        h_box_ants_path = QtWidgets.QHBoxLayout()
        h_box_ants_path.addWidget(self.ants_choice)
        h_box_ants_path.addWidget(self.ants_browse)

        v_box_ants_path = QtWidgets.QVBoxLayout()
        v_box_ants_path.addWidget(self.ants_label)
        v_box_ants_path.addLayout(h_box_ants_path)

        v_box_ants = QtWidgets.QVBoxLayout()
        v_box_ants.addLayout(h_box_use_ants)
        v_box_ants.addLayout(v_box_ants_path)

        self.groupbox_ants.setLayout(v_box_ants)

        # Groupbox "freesurfer"
        self.groupbox_freesurfer = QtWidgets.QGroupBox("FreeSurfer")

        self.use_freesurfer_label = QLabel("Use FreeSurfer")
        self.use_freesurfer_checkbox = QCheckBox("", self)

        self.freesurfer_label = QLabel(
            "FreeSurfer path (e.g. FreeSurfer_dir/FreeSurferEnv.sh):"
        )
        self.freesurfer_choice = QLineEdit(config.get_freesurfer_setup())
        self.freesurfer_browse = QPushButton("Browse")
        self.freesurfer_browse.clicked.connect(self.browse_freesurfer)

        h_box_use_freesurfer = QtWidgets.QHBoxLayout()
        h_box_use_freesurfer.addWidget(self.use_freesurfer_checkbox)
        h_box_use_freesurfer.addWidget(self.use_freesurfer_label)
        h_box_use_freesurfer.addStretch(1)

        h_box_freesurfer_path = QtWidgets.QHBoxLayout()
        h_box_freesurfer_path.addWidget(self.freesurfer_choice)
        h_box_freesurfer_path.addWidget(self.freesurfer_browse)

        v_box_freesurfer_path = QtWidgets.QVBoxLayout()
        v_box_freesurfer_path.addWidget(self.freesurfer_label)
        v_box_freesurfer_path.addLayout(h_box_freesurfer_path)

        v_box_freesurfer = QtWidgets.QVBoxLayout()
        v_box_freesurfer.addLayout(h_box_use_freesurfer)
        v_box_freesurfer.addLayout(v_box_freesurfer_path)

        self.groupbox_freesurfer.setLayout(v_box_freesurfer)

        # Groupbox "mrtrix"
        self.groupbox_mrtrix = QtWidgets.QGroupBox("mrtrix")

        self.use_mrtrix_label = QLabel("Use mrtrix")
        self.use_mrtrix_checkbox = QCheckBox("", self)

        self.mrtrix_label = QLabel("mrtrix path (e.g. mrtrix_dir/bin):")
        self.mrtrix_choice = QLineEdit(config.get_mrtrix_path())
        self.mrtrix_browse = QPushButton("Browse")
        self.mrtrix_browse.clicked.connect(self.browse_mrtrix)

        h_box_use_mrtrix = QtWidgets.QHBoxLayout()
        h_box_use_mrtrix.addWidget(self.use_mrtrix_checkbox)
        h_box_use_mrtrix.addWidget(self.use_mrtrix_label)
        h_box_use_mrtrix.addStretch(1)

        h_box_mrtrix_path = QtWidgets.QHBoxLayout()
        h_box_mrtrix_path.addWidget(self.mrtrix_choice)
        h_box_mrtrix_path.addWidget(self.mrtrix_browse)

        v_box_mrtrix_path = QtWidgets.QVBoxLayout()
        v_box_mrtrix_path.addWidget(self.mrtrix_label)
        v_box_mrtrix_path.addLayout(h_box_mrtrix_path)

        v_box_mrtrix = QtWidgets.QVBoxLayout()
        v_box_mrtrix.addLayout(h_box_use_mrtrix)
        v_box_mrtrix.addLayout(v_box_mrtrix_path)

        self.groupbox_mrtrix.setLayout(v_box_mrtrix)

        # Groupbox "CAPSUL"
        groupbox_capsul = Qt.QGroupBox("CAPSUL")
        capsul_config_button = Qt.QPushButton(
            "Edit CAPSUL config", default=False, autoDefault=False
        )
        capsul_config_button.clicked.connect(self.edit_capsul_config)
        h_box_capsul = Qt.QHBoxLayout()
        h_box_capsul.addWidget(capsul_config_button)
        h_box_capsul.addStretch(1)
        v_box_capsul = Qt.QVBoxLayout()
        v_box_capsul.addLayout(h_box_capsul)

        groupbox_capsul.setLayout(v_box_capsul)

        # general layout
        self.tab_pipeline_layout = QtWidgets.QVBoxLayout()
        self.tab_pipeline_layout.addWidget(self.groupbox_matlab)
        self.tab_pipeline_layout.addWidget(self.groupbox_spm)
        self.tab_pipeline_layout.addWidget(self.groupbox_fsl)
        self.tab_pipeline_layout.addWidget(self.groupbox_afni)
        self.tab_pipeline_layout.addWidget(self.groupbox_ants)
        self.tab_pipeline_layout.addWidget(self.groupbox_freesurfer)
        self.tab_pipeline_layout.addWidget(self.groupbox_mrtrix)
        self.tab_pipeline_layout.addWidget(groupbox_capsul)

        self.tab_pipeline_layout.addStretch(1)
        self.tab_pipeline.setLayout(self.tab_pipeline_layout)

        if config.get_use_spm_standalone():
            archi = platform.architecture()

            if "Windows" in archi[1]:
                self.use_matlab_standalone_checkbox.setChecked(False)

            else:
                self.use_matlab_standalone_checkbox.setChecked(True)

            self.use_spm_standalone_checkbox.setChecked(True)
            self.use_matlab_checkbox.setChecked(False)
            self.use_spm_checkbox.setChecked(False)

        elif config.get_use_spm():
            self.use_matlab_checkbox.setChecked(True)
            self.use_spm_checkbox.setChecked(True)
            self.use_matlab_standalone_checkbox.setChecked(False)
            self.use_spm_standalone_checkbox.setChecked(False)

        elif config.get_use_matlab():
            self.use_matlab_checkbox.setChecked(True)
            self.use_matlab_standalone_checkbox.setChecked(False)
            self.use_spm_standalone_checkbox.setChecked(False)
            self.use_spm_checkbox.setChecked(False)

        elif config.get_use_matlab_standalone():
            self.use_matlab_standalone_checkbox.setChecked(True)
            self.use_matlab_checkbox.setChecked(False)
            self.use_spm_standalone_checkbox.setChecked(False)
            self.use_spm_checkbox.setChecked(False)

        # elif config.get_use_matlab():
        #
        #     if config.get_use_matlab_standalone():
        #         self.use_matlab_standalone_checkbox.setChecked(True)
        #
        #     else:
        #         self.use_matlab_checkbox.setChecked(True)
        #
        # else:
        #     self.use_matlab_checkbox.setChecked(False)
        #     self.use_matlab_standalone_checkbox.setChecked(False)

        if config.get_use_fsl():
            self.use_fsl_checkbox.setChecked(True)

        if config.get_use_afni():
            self.use_afni_checkbox.setChecked(True)

        if config.get_use_ants():
            self.use_ants_checkbox.setChecked(True)

        if config.get_use_freesurfer():
            self.use_freesurfer_checkbox.setChecked(True)

        if config.get_use_mrtrix():
            self.use_mrtrix_checkbox.setChecked(True)

        # The 'Appearance' tab
        self.tab_appearance = QtWidgets.QWidget()
        self.tab_appearance.setObjectName("tab_appearance")
        self.tab_widget.addTab(
            self.tab_appearance, _translate("Dialog", "Appearance")
        )

        colors = [
            "Black",
            "Blue",
            "Green",
            "Grey",
            "Orange",
            "Red",
            "Yellow",
            "White",
        ]

        self.appearance_layout = QVBoxLayout()
        self.label_background_color = QLabel("Background color")
        self.background_color_combo = QComboBox(self)
        self.background_color_combo.addItem("")
        self.label_text_color = QLabel("Text color")
        self.text_color_combo = QComboBox(self)
        self.text_color_combo.addItem("")
        txt = config.getTextColor()
        bkgnd = config.getBackgroundColor()

        if txt == "":
            txt = "Black"

        if bkgnd == "":
            bkgnd = "White"

        for color in colors:
            if txt != color:
                self.background_color_combo.addItem(color)
            if bkgnd != color:
                self.text_color_combo.addItem(color)

        background_color = config.getBackgroundColor()
        self.background_color_combo.setCurrentText(background_color)
        text_color = config.getTextColor()
        self.text_color_combo.setCurrentText(text_color)

        self.fullscreen_cbox = QCheckBox("Use full screen")
        mainwindow_size_lay = QHBoxLayout()
        mainwindow_size_lay.addWidget(QLabel("Main window size"))
        self.mainwindow_size_x_spinbox = QtWidgets.QSpinBox()
        mainwindow_size_lay.addWidget(self.mainwindow_size_x_spinbox)
        mainwindow_size_lay.addWidget(QLabel(" x "))
        self.mainwindow_size_y_spinbox = QtWidgets.QSpinBox()
        mainwindow_size_lay.addWidget(self.mainwindow_size_y_spinbox)
        self.fullscreen_cbox.setChecked(config.get_mainwindow_maximized())
        wsize = config.get_mainwindow_size()
        self.mainwindow_size_x_spinbox.setMaximum(
            QApplication.instance().desktop().width()
        )
        self.mainwindow_size_y_spinbox.setMaximum(
            QApplication.instance().desktop().height()
        )
        if isinstance(wsize, list) and len(wsize) >= 2:
            self.mainwindow_size_x_spinbox.setValue(wsize[0])
            self.mainwindow_size_y_spinbox.setValue(wsize[1])
        self.mainwindow_size_button = QPushButton("use current size")
        mainwindow_size_lay.addWidget(self.mainwindow_size_button)
        self.mainwindow_size_button.clicked.connect(
            partial(self.use_current_mainwindow_size, main_window)
        )

        self.appearance_layout.addWidget(self.label_background_color)
        self.appearance_layout.addWidget(self.background_color_combo)
        self.appearance_layout.addWidget(self.label_text_color)
        self.appearance_layout.addWidget(self.text_color_combo)
        self.appearance_layout.addWidget(self.fullscreen_cbox)
        self.appearance_layout.addLayout(mainwindow_size_lay)
        self.appearance_layout.addStretch(1)
        self.tab_appearance.setLayout(self.appearance_layout)

        # Global layout - scrollable global window
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(vbox)
        self.scroll.setWidget(self.widget)
        self.final_layout = QVBoxLayout()
        self.final_layout.addWidget(self.scroll)
        self.setLayout(self.final_layout)

        # Disabling widgets
        self.use_spm_changed()
        self.use_matlab_changed()
        self.use_matlab_standalone_changed()
        self.use_spm_standalone_changed()
        self.use_fsl_changed()
        self.use_afni_changed()
        self.use_ants_changed()
        self.use_freesurfer_changed()
        self.use_mrtrix_changed()

        # Signals
        self.use_matlab_checkbox.stateChanged.connect(self.use_matlab_changed)
        self.use_matlab_standalone_checkbox.stateChanged.connect(
            self.use_matlab_standalone_changed
        )
        self.use_spm_checkbox.stateChanged.connect(self.use_spm_changed)
        self.use_spm_standalone_checkbox.stateChanged.connect(
            self.use_spm_standalone_changed
        )
        self.use_fsl_checkbox.stateChanged.connect(self.use_fsl_changed)
        self.use_afni_checkbox.stateChanged.connect(self.use_afni_changed)
        self.use_ants_checkbox.stateChanged.connect(self.use_ants_changed)
        self.use_mrtrix_checkbox.stateChanged.connect(self.use_mrtrix_changed)
        self.use_freesurfer_checkbox.stateChanged.connect(
            self.use_freesurfer_changed
        )

    def browse_fsl(self):
        """Called when fsl browse button is clicked."""

        fname = QFileDialog.getOpenFileName(
            self, "Choose FSL config file", os.path.expanduser("~")
        )[0]
        if fname:
            self.fsl_choice.setText(fname)

    def browse_afni(self):
        """Called when afni browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self, "Choose AFNI directory", os.path.expanduser("~")
        )
        if fname:
            self.afni_choice.setText(fname)

    def browse_ants(self):
        """Called when ants browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self, "Choose ANTS directory", os.path.expanduser("~")
        )
        if fname:
            self.ants_choice.setText(fname)

    def browse_mrtrix(self):
        """Called when mrtrix browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self, "Choose mrtrix directory", os.path.expanduser("~")
        )
        if fname:
            self.mrtrix_choice.setText(fname)

    def browse_freesurfer(self):
        """Called when freesurfer browse button is clicked."""

        fname = QFileDialog.getOpenFileName(
            self, "Choose freesurfer env file", os.path.expanduser("~")
        )[0]
        if fname:
            self.freesurfer_choice.setText(fname)

    def browse_matlab(self):
        """Called when matlab browse button is clicked."""

        fname = QFileDialog.getOpenFileName(
            self, "Choose Matlab file", os.path.expanduser("~")
        )[0]
        if fname:
            self.matlab_choice.setText(fname)

    def browse_matlab_standalone(self):
        """Called when matlab browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self, "Choose MCR directory", os.path.expanduser("~")
        )
        if fname:
            self.matlab_standalone_choice.setText(fname)

    def browse_mri_conv_path(self):
        """Called when "MRIFileManager.jar" browse button is clicked."""

        fname = QFileDialog.getOpenFileName(
            self,
            "Select the location of the MRIManager.jar file",
            os.path.expanduser("~"),
        )[0]
        if fname:
            self.mri_conv_path_line_edit.setText(fname)

    def browse_projects_save_path(self):
        """Called when "Projects folder" browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self,
            "Select a folder where to save the projects",
            os.path.expanduser("~"),
        )

        if fname:
            self.projects_save_path_line_edit.setText(fname)

            with open(os.path.join(fname, ".gitignore"), "w") as myFile:
                myFile.write("/*")

    def browse_resources_path(self):
        """Called when "resources" browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self,
            "Select the location of the External resources folder",
            os.path.expanduser("~"),
        )
        if fname:
            self.resources_path_line_edit.setText(fname)

    def browse_spm(self):
        """Called when spm browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self, "Choose SPM directory", os.path.expanduser("~")
        )
        if fname:
            self.spm_choice.setText(fname)

    def browse_spm_standalone(self):
        """Called when spm standalone browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self, "Choose SPM standalone directory", os.path.expanduser("~")
        )
        if fname:
            self.spm_standalone_choice.setText(fname)

    def change_admin_psswd(self, status):
        """Method to change the admin password.

        :param status: String
        """
        change = QDialog()
        change.old_psswd = QLineEdit()
        change.new_psswd = QLineEdit()
        change.new_psswd_conf = QLineEdit()
        status = f"<i>{status}</i>"
        change.status = QLabel(status)
        change.status.setStyleSheet("color:red")

        change.old_psswd.setEchoMode(QLineEdit.Password)
        change.new_psswd.setEchoMode(QLineEdit.Password)
        change.new_psswd_conf.setEchoMode(QLineEdit.Password)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )

        layout = QFormLayout()
        layout.addRow("Old password", change.old_psswd)
        layout.addRow("New password", change.new_psswd)
        layout.addRow("Confirm new password", change.new_psswd_conf)
        layout.addRow(change.status)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(change.accept)
        buttonBox.rejected.connect(change.reject)
        change.setLayout(layout)

        event = change.exec()

        if not event:
            change.close()
        else:
            config = Config()
            old_psswd = f"{self.salt}{change.old_psswd.text()}"
            hash_psswd = hashlib.sha256(old_psswd.encode()).hexdigest()
            if (
                hash_psswd == config.get_admin_hash()
                and change.new_psswd.text() == change.new_psswd_conf.text()
                and len(change.new_psswd.text()) > 6
            ):
                new_psswd = f"{self.salt}{change.new_psswd.text()}"
                config.set_admin_hash(
                    hashlib.sha256(new_psswd.encode()).hexdigest()
                )
            elif hash_psswd != config.get_admin_hash():
                self.change_admin_psswd("The old password is incorrect.")
            elif len(change.new_psswd.text()) <= 6:
                self.change_admin_psswd(
                    "Your password must have more than 6 characters"
                )
            elif change.new_psswd.text() != change.new_psswd_conf.text():
                self.change_admin_psswd("The new passwords are not the same.")

    def control_checkbox_toggled(self, main_window):
        """Check if the user really wants to change the controller version.

        :param main_window: main window object of the software
        """
        self.control_checkbox.toggle()
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Warning)
        self.msg.setText("Controller version change")
        self.msg.setWindowTitle("Warning")
        self.msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        config = Config()

        if not self.control_checkbox_changed:
            self.msg.setInformativeText(
                f"To change the controller from "
                f"{'V1' if config.isControlV1() else 'V2'} to "
                f"{'V2' if config.isControlV1() else 'V1'}, MIA must be "
                f"restarted. Would you like to plan this change for next "
                f"start-up?"
            )

        else:
            self.msg.setInformativeText(
                f"Change of controller from "
                f"{'V1' if config.isControlV1() else 'V2'} to "
                f"{'V2' if config.isControlV1() else 'V1'} is already planned "
                f"for next start-up. Would you like to cancel this change?"
            )

        return_value = self.msg.exec()

        if return_value == QMessageBox.Yes:
            self.control_checkbox_changed = not self.control_checkbox_changed
            main_window.set_controller_version()

        QApplication.restoreOverrideCursor()

    def edit_config_file(self):
        """Create a window to view, edit the mia configuration file."""

        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        config = Config()

        self.editConf = QDialog()
        self.editConf.setWindowTitle(
            os.path.join(
                config.get_properties_path(), "properties", "config.yml"
            )
        )
        self.editConf.txt = QPlainTextEdit()
        stream = yaml.dump(
            config.config, default_flow_style=False, allow_unicode=True
        )
        self.editConf.txt.insertPlainText(str(stream))
        textWidth = self.editConf.txt.width() + 100
        textHeight = self.editConf.txt.height() + 200
        self.editConf.txt.setMinimumSize(textWidth, textHeight)
        self.editConf.txt.resize(textWidth, textHeight)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttonBox.button(QDialogButtonBox.Ok).setDefault(False)
        buttonBox.button(QDialogButtonBox.Cancel).setDefault(False)

        self.findChar_line_edit = QLineEdit()
        findChar_button = QPushButton("Find")
        findChar_button.setDefault(True)

        h_box_find = QtWidgets.QHBoxLayout()
        h_box_find.addWidget(self.findChar_line_edit)
        h_box_find.addWidget(findChar_button)
        findChar_button.clicked.connect(self.findChar)

        layout = QFormLayout()
        layout.addWidget(self.editConf.txt)
        layout.addRow(h_box_find)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.editConf.accept)
        buttonBox.rejected.connect(self.editConf.reject)
        self.editConf.setLayout(layout)
        event = self.editConf.exec()

        if not event:
            self.editConf.close()

        else:
            stream = self.editConf.txt.toPlainText()

            if verCmp(yaml.__version__, "5.1", "sup"):
                config.config = yaml.load(stream, Loader=yaml.FullLoader)

            else:
                config.config = yaml.load(stream)

            config.saveConfig()
            self.editConf.close()

    def findChar(self):
        """Highlights characters in red when using the Find button'
        when editing configuration.

        """
        cursor = self.editConf.txt.textCursor()
        cursor.select(QtGui.QTextCursor.Document)
        cursor.setCharFormat(QtGui.QTextCharFormat())
        cursor.clearSelection()
        self.editConf.txt.setTextCursor(cursor)
        pattern = self.findChar_line_edit.text()

        if pattern == "":
            return

        cursor = self.editConf.txt.textCursor()
        format = QtGui.QTextCharFormat()
        format.setBackground(QtGui.QBrush(QtGui.QColor(255, 0, 0, 50)))
        regex = QtCore.QRegExp(pattern)
        pos = 0
        index = regex.indexIn(self.editConf.txt.toPlainText(), pos)

        while index != -1:
            cursor.setPosition(index)

            for _ in pattern:
                cursor.movePosition(QtGui.QTextCursor.Right, 1)

            cursor.mergeCharFormat(format)
            pos = index + regex.matchedLength()
            index = regex.indexIn(self.editConf.txt.toPlainText(), pos)

    def edit_capsul_config(self):
        """Capsul engine edition

        This method is used when user hit the Edit CAPSUL config button (File >
        MIA preferences, Pipeline tab).
        """

        # from capsul.api import capsul_engine
        # from capsul.qt_gui.widgets.settings_editor import SettingsEditor

        # validate the current Mia config first
        if not self.validate_and_save():
            return

        config = Config()
        capsul_config = config.get_capsul_config(sync_from_engine=False)
        modules = capsul_config.get("engine_modules", [])

        # build a temporary new engine (because it may not be validated)
        engine = capsul_engine()
        for module in modules + [
            "fom",
            "axon",
            "python",
            "fsl",
            "freesurfer",
            "nipype",
            "afni",
            "ants",
            "mrtrix",
            "somaworkflow",
        ]:
            engine.load_module(module)
        envs = capsul_config.get("engine", {})
        for env, conf in envs.items():
            c = dict(conf)
            if "capsul_engine" not in c or "uses" not in c["capsul_engine"]:
                c["capsul_engine"] = {
                    "uses": {
                        engine.settings.module_name(m): "ALL"
                        for m in conf.keys()
                    }
                }
            # for mod, val in conf.items():
            # if 'config_id' not in val:
            # val['config_id'] = mod.split('.')[-1]
            engine.settings.import_configs(env, c, cont_on_error=True)

        dialog = SettingsEditor(engine)
        try:
            result = dialog.exec()
        except Exception as e:
            logger.warning(e)
            return

        if result:
            settings = engine.settings.export_config_dict()

            capsul_config["engine"] = settings
            capsul_config["engine_modules"] = list(engine._loaded_modules)

            try:
                config.set_capsul_config(capsul_config)

            except Exception as e:
                logger.warning(f"{e}")
                return

            # update Mia preferences GUI which might have changed

            # afni
            use_afni = config.get_use_afni()

            if use_afni:
                self.afni_choice.setText(config.get_afni_path())

            use_afni = Qt.Qt.Checked if use_afni else Qt.Qt.Unchecked
            self.use_afni_checkbox.setCheckState(use_afni)

            # ants
            use_ants = config.get_use_ants()

            if use_ants:
                self.ants_choice.setText(config.get_ants_path())

            use_ants = Qt.Qt.Checked if use_ants else Qt.Qt.Unchecked
            self.use_ants_checkbox.setCheckState(use_ants)

            # freesurfer
            use_freesurfer = config.get_use_freesurfer()

            if use_freesurfer:
                self.freesurfer_choice.setText(config.get_freesurfer_setup())

            use_freesurfer = (
                Qt.Qt.Checked if use_freesurfer else Qt.Qt.Unchecked
            )
            self.use_freesurfer_checkbox.setCheckState(use_freesurfer)

            # fsl
            use_fsl = config.get_use_fsl()

            if use_fsl:
                self.fsl_choice.setText(config.get_fsl_config())

            use_fsl = Qt.Qt.Checked if use_fsl else Qt.Qt.Unchecked
            self.use_fsl_checkbox.setCheckState(use_fsl)

            # matlab
            use_matlab = config.get_use_matlab()
            use_matlab = Qt.Qt.Checked if use_matlab else Qt.Qt.Unchecked
            self.use_matlab_checkbox.setCheckState(use_matlab)
            self.matlab_choice.setText(config.get_matlab_path())
            use_matlab_sa = config.get_use_matlab_standalone()
            use_matlab_sa = Qt.Qt.Checked if use_matlab_sa else Qt.Qt.Unchecked
            self.use_matlab_standalone_checkbox.setCheckState(use_matlab_sa)
            self.matlab_standalone_choice.setText(
                config.get_matlab_standalone_path()
            )

            # mrtrix
            use_mrtrix = config.get_use_mrtrix()

            if use_mrtrix:
                self.mrtrix_choice.setText(config.get_mrtrix_path())

            use_mrtrix = Qt.Qt.Checked if use_mrtrix else Qt.Qt.Unchecked
            self.use_mrtrix_checkbox.setCheckState(use_mrtrix)

            # spm
            use_spm = config.get_use_spm()
            use_spm = Qt.Qt.Checked if use_spm else Qt.Qt.Unchecked
            self.use_spm_checkbox.setCheckState(use_spm)
            self.spm_choice.setText(config.get_spm_path())
            use_spm_sa = config.get_use_spm_standalone()
            use_spm_sa = Qt.Qt.Checked if use_spm_sa else Qt.Qt.Unchecked
            self.use_spm_standalone_checkbox.setCheckState(use_spm_sa)
            self.spm_standalone_choice.setText(
                config.get_spm_standalone_path()
            )

        del dialog
        del engine

    def validate_and_save(self, OK_clicked=False):
        """Saves the modifications to the config file and apply them.

        :param OK_clicked: a boolean. If False, only make a minimal backup of
                           the settings to allow synchronisation with
                           capsul config. If True, should only correspond to
                           the moment when we finally exit the Mia config, all
                           parameters are saved and tested.

        :return: True if all is fine, False if a problem has been encountered
        """

        config = Config()
        # Minimum config backup (for Edit CAPSUL config synchronisation):

        if not OK_clicked:
            # Use AFNI
            afni_dir = self.afni_choice.text()
            config.set_afni_path(afni_dir)

            if self.use_afni_checkbox.isChecked():
                config.set_use_afni(True)

            else:
                config.set_use_afni(False)

            # Use ANTS
            ants_dir = self.ants_choice.text()
            config.set_ants_path(ants_dir)

            if self.use_ants_checkbox.isChecked():
                config.set_use_ants(True)

            else:
                config.set_use_ants(False)

            # Use freesurfer
            freesurfer_setup = self.freesurfer_choice.text()
            config.set_freesurfer_setup(freesurfer_setup)

            if self.use_freesurfer_checkbox.isChecked():
                config.set_use_freesurfer(True)

            else:
                config.set_use_freesurfer(False)

            # Use FSL
            fsl_conf = self.fsl_choice.text()
            config.set_fsl_config(fsl_conf)

            if self.use_fsl_checkbox.isChecked():
                config.set_use_fsl(True)

            else:
                config.set_use_fsl(False)

            # Use Matlab
            matlab_input = self.matlab_choice.text()
            config.set_matlab_path(matlab_input)

            if self.use_matlab_checkbox.isChecked():
                config.set_use_matlab(True)

            else:
                config.set_use_matlab(False)

            # Use Matlab Runtime:
            matlab_input = self.matlab_standalone_choice.text()
            config.set_matlab_standalone_path(matlab_input)

            if self.use_matlab_standalone_checkbox.isChecked():
                config.set_use_matlab_standalone(True)

            else:
                config.set_use_matlab_standalone(False)

            # Use mrtrix
            mrtrix_dir = self.mrtrix_choice.text()
            config.set_mrtrix_path(mrtrix_dir)

            if self.use_mrtrix_checkbox.isChecked():
                config.set_use_mrtrix(True)

            else:
                config.set_use_mrtrix(False)

            # Use SPM
            spm_input = self.spm_choice.text()
            config.set_spm_path(spm_input)

            if self.use_spm_checkbox.isChecked():
                config.set_use_spm(True)

            else:
                config.set_use_spm(False)

            # Use SPM standalone
            spm_input = self.spm_standalone_choice.text()
            config.set_spm_standalone_path(spm_input)

            if self.use_spm_standalone_checkbox.isChecked():
                config.set_use_spm_standalone(True)

            else:
                config.set_use_spm_standalone(False)

        # complete backup and testing
        else:
            # Auto-save
            if self.save_checkbox.isChecked():
                config.setAutoSave(True)

            else:
                config.setAutoSave(False)

            # RadioView in miniviewer (databrowser)
            if self.radioView_checkbox.isChecked():
                config.set_radioView(True)

            else:
                config.set_radioView(False)

            # Version 1 controller
            if self.control_checkbox.isChecked():
                config.setControlV1(True)

            else:
                config.setControlV1(False)

            # Max thumbnails number at the data browser bottom
            max_thumbnails = min(max(self.max_thumbnails_box.value(), 1), 15)
            config.set_max_thumbnails(max_thumbnails)

            # Max projects in "Saved projects"
            max_projects = min(max(self.max_projects_box.value(), 1), 20)
            config.set_max_projects(max_projects)

            # User / Admin mode
            main_window = self.main_window
            main_window.windowName = "MIA - Multiparametric Image Analysis"

            if self.admin_mode_checkbox.isChecked():
                config.set_user_mode(False)
                main_window.windowName = (
                    f"{main_window.windowName} (Admin mode)"
                )

            else:
                config.set_user_mode(True)

            # Clinical mode
            if self.clinical_mode_checkbox.isChecked():
                config.set_clinical_mode(True)
                self.use_clinical_mode_signal.emit()

            else:
                config.set_clinical_mode(False)
                self.not_use_clinical_mode_signal.emit()

            # Window name
            main_window.windowName = f"{main_window.windowName} - "
            main_window.setWindowTitle(
                f"{main_window.windowName}{main_window.projectName}"
            )

            # Configuration test
            QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.status_label.setText("Testing configuration ...")
            QCoreApplication.processEvents()

            # AFNI config test
            if self.use_afni_checkbox.isChecked():
                afni_dir = self.afni_choice.text()
                afni_cmd = "afni"

                if os.path.isdir(afni_dir):
                    afni_cmd = os.path.join(afni_dir, afni_cmd)

                else:
                    self.wrong_path(afni_dir, "AFNI")
                    QApplication.restoreOverrideCursor()
                    return False

                try:
                    p = subprocess.Popen(
                        [afni_cmd, "-version"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    output, err = p.communicate()

                    if err == b"":
                        config.set_afni_path(afni_dir)
                        config.set_use_afni(True)

                    else:
                        self.wrong_path(afni_dir, "AFNI")
                        QApplication.restoreOverrideCursor()
                        return False

                except Exception:
                    self.wrong_path(afni_dir, "AFNI")
                    QApplication.restoreOverrideCursor()
                    return False

            else:
                config.set_use_afni(False)

            # ANTS config test
            if self.use_ants_checkbox.isChecked():
                ants_dir = self.ants_choice.text()
                ants_cmd = "SmoothImage"

                if os.path.isdir(ants_dir):
                    ants_cmd = os.path.join(ants_dir, ants_cmd)

                else:
                    self.wrong_path(ants_dir, "ANTS")
                    QApplication.restoreOverrideCursor()
                    return False

                try:
                    p = subprocess.Popen(
                        [ants_cmd, "-version"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    output, err = p.communicate()

                    if err == b"":
                        config.set_ants_path(ants_dir)
                        config.set_use_ants(True)

                    else:
                        self.wrong_path(ants_dir, "ANTS")
                        QApplication.restoreOverrideCursor()
                        return False

                except Exception:
                    self.wrong_path(ants_dir, "ANTS")
                    QApplication.restoreOverrideCursor()
                    return False
            else:
                config.set_use_ants(False)

            # freesurfer config test
            if self.use_freesurfer_checkbox.isChecked():
                freesurfer_setup = self.freesurfer_choice.text()
                freesurfer_dir = os.path.dirname(freesurfer_setup)

                if "FREESURFER_HOME" not in os.environ:
                    os.environ["FREESURFER_HOME"] = freesurfer_dir

                freesurfer_cmd = "recon-all"

                if os.path.isdir(freesurfer_dir):
                    freesurfer_cmd = os.path.join(
                        freesurfer_dir, "bin", freesurfer_cmd
                    )

                else:
                    self.wrong_path(freesurfer_dir, "freesurfer")
                    QApplication.restoreOverrideCursor()
                    return False

                try:
                    p = subprocess.Popen(
                        [freesurfer_cmd, "--version"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    output, err = p.communicate()
                    warning_pattern = re.compile(r"warning", re.IGNORECASE)
                    errors = []

                    for line in err.decode().split("\n"):

                        if not re.search(warning_pattern, line):
                            errors.append(line)

                    if errors in [[], [""]]:
                        config.set_freesurfer_setup(freesurfer_setup)
                        config.set_use_freesurfer(True)

                    else:
                        self.wrong_path(freesurfer_dir, "freesurfer")
                        QApplication.restoreOverrideCursor()
                        return False

                except Exception:
                    self.wrong_path(freesurfer_dir, "freesurfer")
                    QApplication.restoreOverrideCursor()
                    return False
            else:
                config.set_use_freesurfer(False)

            # FSL config test
            if self.use_fsl_checkbox.isChecked():
                fsl_conf = self.fsl_choice.text()

                if fsl_conf == "":
                    fsl_cmd = "flirt"

                else:
                    fsl_dir = os.path.dirname(fsl_conf)

                    if fsl_dir.endswith(os.path.join("etc", "fslconf")):
                        fsl_dir = os.path.dirname(os.path.dirname(fsl_dir))

                    elif fsl_dir.endswith("etc"):
                        fsl_dir = os.path.dirname(fsl_dir)

                    fsl_cmd = os.path.join(fsl_dir, "bin", "flirt")

                try:
                    p = subprocess.Popen(
                        [fsl_cmd, "-version"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    output, err = p.communicate()

                    if err == b"":
                        config.set_fsl_config(fsl_conf)
                        config.set_use_fsl(True)

                    else:
                        self.wrong_path(fsl_conf, "FSL", "config file")
                        QApplication.restoreOverrideCursor()
                        return False

                except Exception:
                    self.wrong_path(fsl_conf, "FSL", "config file")
                    QApplication.restoreOverrideCursor()
                    return False

            else:
                config.set_use_fsl(False)

            # mrtrix config test
            if self.use_mrtrix_checkbox.isChecked():
                mrtrix_dir = self.mrtrix_choice.text()
                mrtrix_cmd = "mrinfo"

                if os.path.isdir(mrtrix_dir):
                    mrtrix_cmd = os.path.join(mrtrix_dir, mrtrix_cmd)

                else:
                    self.wrong_path(mrtrix_dir, "mrtrix")
                    QApplication.restoreOverrideCursor()
                    return False

                try:
                    p = subprocess.Popen(
                        [mrtrix_cmd, "-version"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    output, err = p.communicate()

                    if err == b"":
                        config.set_mrtrix_path(mrtrix_dir)
                        config.set_use_mrtrix(True)

                    else:
                        self.wrong_path(mrtrix_dir, "mrtrix")
                        QApplication.restoreOverrideCursor()
                        return False

                except Exception:
                    self.wrong_path(mrtrix_dir, "mrtrix")
                    QApplication.restoreOverrideCursor()
                    return False
            else:
                config.set_use_mrtrix(False)

            # SPM & Matlab (license) config test
            matlab_input = self.matlab_choice.text()
            spm_input = self.spm_choice.text()

            if (
                matlab_input != "" and spm_input != ""
            ) or self.use_spm_checkbox.isChecked():
                if not os.path.isfile(matlab_input):
                    self.wrong_path(matlab_input, "Matlab")
                    QApplication.restoreOverrideCursor()
                    return False

                if (
                    matlab_input == config.get_matlab_path()
                    and spm_input == config.get_spm_path()
                ):
                    if self.use_spm_checkbox.isChecked():
                        config.set_use_spm(True)
                        config.set_use_matlab(True)
                        config.set_use_matlab_standalone(False)
                        config.set_use_spm_standalone(False)

                elif os.path.isdir(spm_input):
                    try:
                        matlab_cmd = (
                            f"restoredefaultpath; "
                            f"addpath('{spm_input}'); "
                            f"[name, ~]=spm('Ver'); "
                            f"exit"
                        )
                        p = subprocess.Popen(
                            [
                                matlab_input,
                                "-nodisplay",
                                "-nodesktop",
                                "-nosplash",
                                "-singleCompThread",
                                "-r",
                                matlab_cmd,
                            ],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        output, err = p.communicate()

                        if err == b"":
                            config.set_matlab_path(matlab_input)

                            if self.use_spm_checkbox.isChecked():
                                config.set_use_matlab(True)
                                config.set_use_matlab_standalone(False)
                                config.set_use_spm(True)
                                config.set_use_spm_standalone(False)

                            config.set_spm_path(spm_input)

                        elif "spm" in str(err):
                            self.wrong_path(spm_input, "SPM")
                            QApplication.restoreOverrideCursor()
                            return False

                        else:
                            self.wrong_path(matlab_input, "Matlab")
                            QApplication.restoreOverrideCursor()
                            return False

                    except Exception:
                        self.wrong_path(matlab_input, "Matlab")
                        QApplication.restoreOverrideCursor()
                        return False

                else:
                    self.wrong_path(spm_input, "SPM")
                    QApplication.restoreOverrideCursor()
                    return False

            # Matlab alone config test
            if matlab_input != "" or self.use_matlab_checkbox.isChecked():
                if matlab_input == config.get_matlab_path():
                    if (
                        self.use_matlab_checkbox.isChecked()
                        and not self.use_spm_checkbox.isChecked()
                    ):
                        config.set_use_matlab(True)
                        config.set_use_matlab_standalone(False)
                        config.set_use_spm(False)
                        config.set_use_spm_standalone(False)

                elif os.path.isfile(matlab_input):
                    try:
                        matlab_cmd = "ver; exit"
                        p = subprocess.Popen(
                            [
                                matlab_input,
                                "-nodisplay",
                                "-nodesktop",
                                "-nosplash",
                                "-singleCompThread",
                                "-r",
                                matlab_cmd,
                            ],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        output, err = p.communicate()

                        if err == b"":
                            config.set_matlab_path(matlab_input)

                            if self.use_matlab_checkbox.isChecked():
                                config.set_use_matlab(True)
                                config.set_use_matlab_standalone(False)
                                config.set_use_spm(False)
                                config.set_use_spm_standalone(False)

                        else:
                            self.wrong_path(matlab_input, "Matlab")
                            QApplication.restoreOverrideCursor()
                            return False

                    except Exception:
                        self.wrong_path(matlab_input, "Matlab")
                        QApplication.restoreOverrideCursor()
                        return False
                else:
                    self.wrong_path(matlab_input, "Matlab")
                    QApplication.restoreOverrideCursor()
                    return False

            # SPM (standalone) & Matlab (MCR) config test
            spm_input = self.spm_standalone_choice.text()
            matlab_input = self.matlab_standalone_choice.text()
            archi = platform.architecture()

            if (
                matlab_input != "" and spm_input != ""
            ) or self.use_spm_standalone_checkbox.isChecked():
                if (not os.path.isdir(matlab_input)) and (
                    "Windows" not in archi[1]
                ):
                    self.wrong_path(matlab_input, "Matlab standalone")
                    QApplication.restoreOverrideCursor()
                    return False

                if (matlab_input == config.get_matlab_standalone_path()) and (
                    spm_input == config.get_spm_standalone_path()
                ):
                    if self.use_spm_standalone_checkbox.isChecked():
                        config.set_use_spm_standalone(True)

                        if "Windows" in archi[1]:
                            config.set_use_matlab(True)
                            config.set_use_matlab_standalone(False)

                        else:
                            config.set_use_matlab_standalone(True)

                elif os.path.isdir(spm_input):
                    if "Windows" in archi[1]:
                        mcr = glob.glob(
                            os.path.join(spm_input, "spm*_win*.exe")
                        )
                        pos = -1
                        nb_bit_sys = archi[0]

                        for i in range(len(mcr)):
                            spm_path, spm_file_name = os.path.split(mcr[i])

                            if nb_bit_sys[:2] in spm_file_name:
                                pos = i

                        if pos == -1:
                            self.wrong_path(spm_input, "SPM standalone")
                            QApplication.restoreOverrideCursor()
                            return False

                    elif os.path.isdir(matlab_input):
                        mcr = glob.glob(os.path.join(spm_input, "run_spm*.sh"))

                    if mcr:
                        try:
                            if "Windows" in archi[1]:
                                p = subprocess.Popen(
                                    [mcr[pos], "--version"],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                )

                            else:
                                p = subprocess.Popen(
                                    [mcr[0], matlab_input, "--version"],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                )

                            output, err = p.communicate()

                            if (
                                err == b"" and output != b""
                            ) or output.startswith(b"SPM8 "):
                                # spm8 standalone doesn't accept --version
                                # argument but prints a message that we can
                                # interpret as saying that SPM8 is working
                                # anyway.

                                if (
                                    self.use_spm_standalone_checkbox.isChecked
                                )():
                                    config.set_use_spm_standalone(True)
                                    config.set_use_matlab_standalone(True)

                                config.set_spm_standalone_path(spm_input)
                                config.set_matlab_standalone_path(matlab_input)

                            elif (
                                (err != b"")
                                and (b"version" in output.split()[2:])
                                and (b"(standalone)" in output.split()[2:])
                            ):
                                if (
                                    self.use_spm_standalone_checkbox.isChecked
                                )():
                                    config.set_use_spm_standalone(True)
                                    config.set_use_matlab_standalone(True)
                                config.set_spm_standalone_path(spm_input)
                                config.set_matlab_standalone_path(matlab_input)

                                if isinstance(err, bytes):
                                    err = err.decode("utf-8")

                                logger.warning(
                                    "The configuration for Matlab MCR and "
                                    "SPM standalone as defined in Mia's "
                                    "preferences seems to be valid, but the "
                                    "following issue has been detected:"
                                )
                                logger.warning(f"{err}")
                                logger.warning(
                                    "Please fix this issue to avoid a "
                                    "malfunction..."
                                )

                            elif err != b"":
                                if "shared libraries" in str(err):
                                    self.wrong_path(
                                        matlab_input, "Matlab standalone"
                                    )
                                    QApplication.restoreOverrideCursor()
                                    return False

                                else:
                                    self.wrong_path(
                                        spm_input, "SPM standalone"
                                    )
                                    QApplication.restoreOverrideCursor()
                                    return False

                            else:
                                self.wrong_path(spm_input, "SPM standalone")
                                QApplication.restoreOverrideCursor()
                                return False

                        except Exception:
                            self.wrong_path(spm_input, "SPM standalone")
                            QApplication.restoreOverrideCursor()
                            return False

                    else:
                        self.wrong_path(spm_input, "SPM standalone")
                        QApplication.restoreOverrideCursor()
                        return False

                else:
                    self.wrong_path(spm_input, "SPM standalone")
                    QApplication.restoreOverrideCursor()
                    return False

            # Matlab (MCR) alone config test
            if (
                matlab_input != ""
                or self.use_matlab_standalone_checkbox.isChecked()
            ):
                if "Windows" in archi[1]:
                    logger.warning(
                        "Matlab Standalone Path enter, this is unnecessary "
                        "to use SPM12."
                    )
                    config.set_use_matlab(True)
                    config.set_use_matlab_standalone(False)
                    config.set_matlab_standalone_path(matlab_input)

                elif os.path.isdir(matlab_input):
                    if (
                        self.use_matlab_standalone_checkbox.isChecked()
                        and not self.use_spm_standalone_checkbox.isChecked()
                    ):
                        config.set_use_matlab_standalone(True)
                        config.set_matlab_standalone_path(matlab_input)
                        config.set_use_matlab(False)
                        config.set_use_spm_standalone(False)
                        config.set_use_spm(False)

                else:
                    self.wrong_path(matlab_input, "Matlab standalone")
                    QApplication.restoreOverrideCursor()
                    return False

            # Colors
            background_color = self.background_color_combo.currentText()
            text_color = self.text_color_combo.currentText()
            config.setBackgroundColor(background_color)
            config.setTextColor(text_color)
            main_window.setStyleSheet(
                f"background-color:{background_color};color:{text_color};"
            )
            # main window setup
            fullscreen = self.fullscreen_cbox.isChecked()
            config.set_mainwindow_maximized(fullscreen)
            w = self.mainwindow_size_x_spinbox.value()
            h = self.mainwindow_size_y_spinbox.value()
            config.set_mainwindow_size([w, h])

            if fullscreen:
                main_window.showMaximized()

            else:
                main_window.showNormal()

            # Projects folder
            projects_folder = self.projects_save_path_line_edit.text()

            if os.path.isdir(projects_folder):
                config.set_projects_save_path(projects_folder)

            else:
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Critical)
                self.msg.setText("Invalid projects folder path")
                self.msg.setInformativeText(
                    f"The projects folder path entered `{projects_folder}` is "
                    f"invalid."
                )
                self.msg.setWindowTitle("Error")
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.buttonClicked.connect(self.msg.close)
                self.msg.show()
                QApplication.restoreOverrideCursor()
                return False

            # MRIFileManager.jar path
            mri_conv_path = self.mri_conv_path_line_edit.text()

            if mri_conv_path == "":
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setText("Empty MRIFileManager.jar path")
                self.msg.setInformativeText(
                    "No path has been entered for MRIFileManager.jar."
                )
                self.msg.setWindowTitle("Warning")
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.buttonClicked.connect(self.msg.close)
                self.msg.show()
                config.set_mri_conv_path(mri_conv_path)

            elif os.path.isfile(mri_conv_path):
                config.set_mri_conv_path(mri_conv_path)

            else:
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Critical)
                self.msg.setText("Invalid MRIFileManager.jar path")
                self.msg.setInformativeText(
                    f"The MRIFileManager.jar path entered '{mri_conv_path}' "
                    f"is invalid."
                )
                self.msg.setWindowTitle("Error")
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.buttonClicked.connect(self.msg.close)
                self.msg.show()
                QApplication.restoreOverrideCursor()
                return False

            # Resources folder
            resources_folder = self.resources_path_line_edit.text()

            if os.path.isdir(resources_folder):
                config.set_resources_path(resources_folder)

            else:
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Critical)
                self.msg.setText("Invalid resources folder path")
                self.msg.setInformativeText(
                    f"The resources folder path entered '{resources_folder}' "
                    f"is invalid."
                )
                self.msg.setWindowTitle("Error")
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.buttonClicked.connect(self.msg.close)
                self.msg.show()
                QApplication.restoreOverrideCursor()
                return False

            self.signal_preferences_change.emit()
            QApplication.restoreOverrideCursor()

        c_c = config.config.setdefault("capsul_config", {})
        c_e = config.get_capsul_engine()

        if c_c and c_e:
            # sync capsul config from mia config, if module is not used:

            # AFNI CapsulConfig
            if not config.get_use_afni():
                # TODO: We only deal here with the global environment
                cif = c_e.settings.config_id_field

                with c_e.settings as settings:
                    configafni = settings.config("afni", "global")

                    if configafni:
                        settings.remove_config(
                            "afni", "global", getattr(configafni, cif)
                        )

                # TODO: We could use a generic method to deal with c_c?
                try:
                    del c_c["engine"]["global"]["capsul.engine.module.afni"][
                        "afni"
                    ]["directory"]

                except KeyError:
                    pass

            # ANTS CapsulConfig
            if not config.get_use_ants():
                # TODO: We only deal here with the global environment
                cif = c_e.settings.config_id_field

                with c_e.settings as settings:
                    configants = settings.config("ants", "global")

                    if configants:
                        settings.remove_config(
                            "ants", "global", getattr(configants, cif)
                        )

                # TODO: We could use a generic method to deal with c_c?
                try:
                    del c_c["engine"]["global"]["capsul.engine.module.ants"][
                        "ants"
                    ]["directory"]

                except KeyError:
                    pass

            # freesurfer CapsulConfig
            if not config.get_use_freesurfer():
                # TODO: We only deal here with the global environment
                cif = c_e.settings.config_id_field

                with c_e.settings as settings:
                    configants = settings.config("freesurfer", "global")

                    if configants:
                        settings.remove_config(
                            "freesurfer", "global", getattr(configants, cif)
                        )

                # TODO: We could use a generic method to deal with c_c?
                # try:
                #     del c_c["engine"]["global"][
                #         "capsul.engine.module.freesurfer"
                #         ]["freesurfer"
                #          ]["directory"]
                #
                # except KeyError:
                #     pass

            # FSL CapsulConfig
            if not config.get_use_fsl():
                # TODO: We only deal here with the global environment
                cif = c_e.settings.config_id_field

                with c_e.settings as settings:
                    configfsl = settings.config("fsl", "global")

                    if configfsl:
                        settings.remove_config(
                            "fsl", "global", getattr(configfsl, cif)
                        )

                # TODO: We could use a generic method to deal with c_c?
                try:
                    del c_c["engine"]["global"]["capsul.engine.module.fsl"][
                        "fsl"
                    ]["directory"]

                except KeyError:
                    pass

                try:
                    del c_c["engine"]["global"]["capsul.engine.module.fsl"][
                        "fsl"
                    ]["config"]

                except KeyError:
                    pass

            # mrtrix CapsulConfig
            if not config.get_use_mrtrix():
                # TODO: We only deal here with the global environment
                cif = c_e.settings.config_id_field

                with c_e.settings as settings:
                    configants = settings.config("mrtrix", "global")

                    if configants:
                        settings.remove_config(
                            "mrtrix", "global", getattr(configants, cif)
                        )

                # TODO: We could use a generic method to deal with c_c?
                try:
                    del c_c["engine"]["global"]["capsul.engine.module.mrtrix"][
                        "mrtrix"
                    ]["directory"]

                except KeyError:
                    pass

            # SPM standalone CapsulConfig
            if not config.get_use_spm_standalone():
                try:
                    keys = c_c["engine"]["global"][
                        "capsul.engine.module.spm"
                    ].keys()

                except KeyError:
                    pass

                else:
                    dict4clean = dict.fromkeys(keys, False)

                    for i in keys:
                        if (
                            "standalone"
                            in c_c["engine"]["global"][
                                "capsul.engine.module.spm"
                            ][i]
                        ):
                            if (
                                c_c["engine"]["global"][
                                    "capsul.engine.module.spm"
                                ][i]["standalone"]
                                is True
                            ):
                                dict4clean[i] = True

                        else:
                            # TODO: What we do if standalone is not a key ?
                            pass

                    for i in dict4clean:
                        if dict4clean[i]:
                            del c_c["engine"]["global"][
                                "capsul.engine.module.spm"
                            ][i]

            if not config.get_use_spm():
                try:
                    keys = c_c["engine"]["global"][
                        "capsul.engine.module.spm"
                    ].keys()

                except KeyError:
                    pass

                else:
                    dict4clean = dict.fromkeys(keys, False)

                    for i in keys:
                        if (
                            "standalone"
                            in c_c["engine"]["global"][
                                "capsul.engine.module.spm"
                            ][i]
                        ):
                            if (
                                c_c["engine"]["global"][
                                    "capsul.engine.module.spm"
                                ][i]["standalone"]
                                is False
                            ):
                                dict4clean[i] = True

                    for i in dict4clean:
                        if dict4clean[i]:
                            del c_c["engine"]["global"][
                                "capsul.engine.module.spm"
                            ][i]

            try:
                if not c_c["engine"]["global"]["capsul.engine.module.spm"]:
                    del c_c["engine"]["global"]["capsul.engine.module.spm"]

            except KeyError:
                pass

            if not config.get_use_matlab():
                try:
                    keys = c_c["engine"]["global"][
                        "capsul.engine.module.matlab"
                    ].keys()

                except KeyError:
                    pass

                else:
                    dict4clean = dict.fromkeys(keys, False)

                    for i in keys:
                        if (
                            "executable"
                            in c_c["engine"]["global"][
                                "capsul.engine.module.matlab"
                            ][i]
                        ):
                            dict4clean[i] = True

                    for i in dict4clean:
                        if dict4clean[i]:
                            del c_c["engine"]["global"][
                                "capsul.engine.module.matlab"
                            ][i]["executable"]

            if not config.get_use_matlab_standalone():
                try:
                    keys = c_c["engine"]["global"][
                        "capsul.engine.module.matlab"
                    ].keys()

                except KeyError:
                    pass

                else:
                    dict4clean = dict.fromkeys(keys, False)

                    for i in keys:
                        if (
                            "mcr_directory"
                            in c_c["engine"]["global"][
                                "capsul.engine.module.matlab"
                            ][i]
                        ):
                            dict4clean[i] = True

                    for i in dict4clean:
                        if dict4clean[i]:
                            del c_c["engine"]["global"][
                                "capsul.engine.module.matlab"
                            ][i]["mcr_directory"]

            try:
                if not c_c["engine"]["global"]["capsul.engine.module.matlab"]:
                    del c_c["engine"]["global"]["capsul.engine.module.matlab"]

            except KeyError:
                pass

            # if not config.get_use_spm_standalone():
            #
            #     try:
            #         del c_c['engine']['global'][
            #             'capsul.engine.module.spm'][
            #                                    'spm12-standalone']
            #
            #     except KeyError:
            #         pass
            #
            #     # try:
            #     #     del c_c['engine']['global'][
            #     #         'capsul.engine.module.spm'][
            #     #                           'spm12-standalone']['standalone']
            #     #
            #     # except KeyError:
            #     #     pass
            #
            #     cif = c_e.settings.config_id_field
            #
            #     with c_e.settings as settings:
            #
            #         for c in settings.configs('spm', 'global'):
            #             settings.remove_config('spm', 'global',
            #                                    getattr(c, cif))
            #
            #         # settings.new_config('spm', 'global',
            #         #        {'config_id': 'spm',
            #         #         'standalone': False,
            #         #         'directory': config.get_spm_standalone_path()})
            #
            #         # for c in settings.configs('matlab', 'global'):
            #         #     settings.remove_config('matlab', 'global',
            #         #                            getattr(c, cif))
            #
            #     # try:
            #     #     del c_c['engine']['global'][
            #     #         'capsul.engine.module.matlab'][
            #     #             'executable']
            #     #
            #     # except KeyError:
            #     #     pass
            #
            # # SPM
            # elif not config.get_use_spm():
            #
            #     try:
            #         c_c['engine']['global'][
            #             'capsul.engine.module.spm']['spm'[
            #                 'directory'] = config.get_spm_path()
            #
            #     except KeyError:
            #         pass
            #
            #     cif = c_e.settings.config_id_field
            #
            #     with c_e.settings as settings:
            #
            #         for c in settings.configs('spm', 'global'):
            #             settings.remove_config('spm', 'global',
            #                                    getattr(c, cif))
            #
            #         # settings.new_config('spm', 'global',
            #         #                {'config_id': 'spm',
            #         #                 'directory': config.get_spm_path(),
            #         #                 'standalone': False})
            #
            #         # for c in settings.configs('matlab', 'global'):
            #         #     settings.remove_config('matlab', 'global',
            #         #                            getattr(c, cif))
            #         #
            #         # settings.new_config('matlab', 'global',
            #         #               {'config_id': 'matlab',
            #         #                'executable': config.get_matlab_path()})
            #     # try:
            #     #     c_c['engine']['global'][
            #     #         'capsul.engine.module.matlab'][
            #     #             'executable'] = config.get_matlab_path()
            #     #
            #     # except KeyError:
            #     #     pass
            #
            # # no SPM at all
            # else:
            #     cif = c_e.settings.config_id_field
            #
            #     with c_e.settings as settings:
            #
            #         for c in settings.configs('spm', 'global'):
            #             settings.remove_config('spm', 'global',
            #                                    getattr(c, cif))
            #
            #     try:
            #         del c_c['engine']['global'][
            #             'capsul.engine.module.spm'][
            #                 'directory']
            #
            #     except KeyError:
            #         pass
            #
            # # no MATLAB at all
            # if (not config.get_use_matlab() and
            #                        not config.get_use_matlab_standalone()):
            #     cif = c_e.settings.config_id_field
            #
            #     with c_e.settings as settings:
            #
            #         for c in settings.configs('matlab', 'global'):
            #             settings.remove_config('matlab', 'global',
            #                                    getattr(c, cif))
            #
            #     try:
            #         del c_c['engine']['global'][
            #             'capsul.engine.module.matlab'][
            #                 'executable']
            #
            #     except KeyError:
            #         pass
            #
            # # only MATLAB
            # if config.get_use_matlab() and not config.get_use_spm():
            #
            #     try:
            #         c_c['engine']['global'][
            #             'capsul.engine.module.matlab'][
            #                 'executable'] = config.get_matlab_path()
            #
            #     except KeyError:
            #         pass
            #
            #     cif = c_e.settings.config_id_field
            #
            #     with c_e.settings as settings:
            #
            #         for c in settings.configs('matlab', 'global'):
            #             settings.remove_config('matlab', 'global',
            #                                    getattr(c, cif))
            #
            #         settings.new_config('matlab', 'global',
            #                        {'config_id': 'matlab',
            #                         'executable': config.get_matlab_path()})
            #
            #         for c in settings.configs('spm', 'global'):
            #             settings.remove_config('spm', 'global',
            #                                    getattr(c, cif))

        config.get_capsul_config(sync_from_engine=False)
        config.saveConfig()
        return True

    def ok_clicked(self):
        """Blabla"""

        if self.validate_and_save(OK_clicked=True):
            self.accept()
            self.close()

    def use_afni_changed(self):
        """Called when the use_afni checkbox is changed."""

        if not self.use_afni_checkbox.isChecked():
            self.afni_choice.setDisabled(True)
            self.afni_label.setDisabled(True)

        else:
            self.afni_choice.setDisabled(False)
            self.afni_label.setDisabled(False)

    def use_ants_changed(self):
        """Called when the use_ants checkbox is changed."""

        if not self.use_ants_checkbox.isChecked():
            self.ants_choice.setDisabled(True)
            self.ants_label.setDisabled(True)

        else:
            self.ants_choice.setDisabled(False)
            self.ants_label.setDisabled(False)

    def use_freesurfer_changed(self):
        """Called when the use_freesurfer checkbox is changed."""

        if not self.use_freesurfer_checkbox.isChecked():
            self.freesurfer_choice.setDisabled(True)
            self.freesurfer_label.setDisabled(True)

        else:
            self.freesurfer_choice.setDisabled(False)
            self.freesurfer_label.setDisabled(False)

    def use_fsl_changed(self):
        """Called when the use_fsl checkbox is changed."""

        if not self.use_fsl_checkbox.isChecked():
            self.fsl_choice.setDisabled(True)
            self.fsl_label.setDisabled(True)

        else:
            self.fsl_choice.setDisabled(False)
            self.fsl_label.setDisabled(False)

    def use_matlab_changed(self):
        """Called when the use_matlab checkbox is changed."""

        if not self.use_matlab_checkbox.isChecked():
            self.matlab_choice.setDisabled(True)
            self.spm_choice.setDisabled(True)
            self.matlab_label.setDisabled(True)
            self.spm_label.setDisabled(True)
            self.spm_browse.setDisabled(True)
            self.matlab_browse.setDisabled(True)
            self.use_spm_checkbox.setChecked(False)
        else:
            self.matlab_choice.setDisabled(False)
            self.matlab_label.setDisabled(False)
            self.matlab_browse.setDisabled(False)
            self.use_matlab_standalone_checkbox.setChecked(False)

    def use_matlab_standalone_changed(self):
        """Called when the use_matlab_standalone checkbox is changed."""

        if not self.use_matlab_standalone_checkbox.isChecked():
            archi = platform.architecture()

            if "Windows" not in archi[1]:
                self.spm_standalone_choice.setDisabled(True)
                self.use_spm_standalone_checkbox.setChecked(False)
                self.spm_standalone_label.setDisabled(True)
                self.spm_standalone_browse.setDisabled(True)

            self.matlab_standalone_choice.setDisabled(True)
            self.matlab_standalone_label.setDisabled(True)
            self.matlab_standalone_browse.setDisabled(True)

        else:
            self.matlab_standalone_choice.setDisabled(False)
            self.matlab_standalone_label.setDisabled(False)
            self.matlab_standalone_browse.setDisabled(False)
            self.use_matlab_checkbox.setChecked(False)

    def use_mrtrix_changed(self):
        """Called when the use_mrtrix checkbox is changed."""

        if not self.use_mrtrix_checkbox.isChecked():
            self.mrtrix_choice.setDisabled(True)
            self.mrtrix_label.setDisabled(True)

        else:
            self.mrtrix_choice.setDisabled(False)
            self.mrtrix_label.setDisabled(False)

    def use_spm_changed(self):
        """Called when the use_spm checkbox is changed."""

        if not self.use_spm_checkbox.isChecked():
            self.spm_choice.setDisabled(True)
            self.spm_label.setDisabled(True)
            self.spm_browse.setDisabled(True)

        else:
            self.use_matlab_checkbox.setChecked(True)
            self.spm_choice.setDisabled(False)
            self.spm_label.setDisabled(False)
            self.spm_browse.setDisabled(False)
            self.spm_standalone_choice.setDisabled(True)
            self.spm_standalone_label.setDisabled(True)
            self.spm_standalone_browse.setDisabled(True)
            self.use_spm_standalone_checkbox.setChecked(False)
            self.use_matlab_standalone_checkbox.setChecked(False)

    def use_spm_standalone_changed(self):
        """Called when the use_spm_standalone checkbox is changed."""

        if not self.use_spm_standalone_checkbox.isChecked():
            self.spm_standalone_choice.setDisabled(True)
            self.spm_standalone_label.setDisabled(True)
            self.spm_standalone_browse.setDisabled(True)

        else:
            archi = platform.architecture()

            if "Windows" not in archi[1]:
                self.use_matlab_standalone_checkbox.setChecked(True)

            self.spm_standalone_choice.setDisabled(False)
            self.spm_standalone_label.setDisabled(False)
            self.spm_standalone_browse.setDisabled(False)
            self.spm_choice.setDisabled(True)
            self.spm_label.setDisabled(True)
            self.spm_browse.setDisabled(True)
            self.use_spm_checkbox.setChecked(False)
            self.use_matlab_checkbox.setChecked(False)

    def admin_mode_switch(self):
        """Called when the admin mode checkbox is clicked."""
        config = Config()

        if self.admin_mode_checkbox.isChecked():
            psswd, ok = QInputDialog.getText(
                self,
                "Password Input Dialog",
                "Enter the admin password:",
                QLineEdit.Password,
            )

            if ok:
                salt_psswd = f"{self.salt}{psswd}"
                hash_psswd = hashlib.sha256(salt_psswd.encode()).hexdigest()

                if hash_psswd != config.get_admin_hash():
                    self.admin_mode_checkbox.setChecked(False)
                    self.status_label.setText(
                        "<i style='color:red'>Wrong password.</i>"
                    )

                else:
                    self.change_psswd.setVisible(True)
                    self.edit_config.setVisible(True)
                    self.status_label.clear()

            else:
                self.admin_mode_checkbox.setChecked(False)

        else:
            self.change_psswd.setVisible(False)
            self.edit_config.setVisible(False)

    def wrong_path(self, path, tool, extra_mess=""):
        """Blabla"""

        QApplication.restoreOverrideCursor()
        self.status_label.setText("")
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Critical)
        self.msg.setText(f"Invalid {tool} path")

        if extra_mess:
            extra_mess = f" {extra_mess}"

        self.msg.setInformativeText(
            f"The {tool}{extra_mess} path entered {path} is invalid."
        )
        self.msg.setWindowTitle("Error")
        self.msg.setStandardButtons(QMessageBox.Ok)
        self.msg.buttonClicked.connect(self.msg.close)
        self.msg.show()

    def use_current_mainwindow_size(self, main_window):
        """Blabla"""

        self.mainwindow_size_x_spinbox.setValue(main_window.width())
        self.mainwindow_size_y_spinbox.setValue(main_window.height())


class PopUpProperties(QDialog):
    """Is called when the user wants to change the current project's
       properties (File > properties).

    .. Methods:
        - ok_clicked: saves the modifications and updates the data browser

    """

    # Signal that will be emitted at the end to tell that the project has
    # been created
    signal_settings_change = pyqtSignal()

    def __init__(self, project, databrowser, old_tags):
        """Initialization

        :param project: current project in the software
        :param databrowser: data browser instance of the software
        :param old_tags: visualized tags before opening this dialog
        """
        super().__init__()
        self.setModal(True)
        self.project = project
        self.databrowser = databrowser
        self.old_tags = old_tags

        _translate = QtCore.QCoreApplication.translate

        self.setObjectName("Dialog")
        self.setWindowTitle("project properties")

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setEnabled(True)

        # The 'Visualized tags" tab
        with self.project.database.data() as database_data:
            self.tab_tags = PopUpVisualizedTags(
                self.project, database_data.get_shown_tags()
            )

        self.tab_tags.setObjectName("tab_tags")
        self.tab_widget.addTab(
            self.tab_tags, _translate("Dialog", "Visualized tags")
        )

        # The 'Informations" tab
        self.tab_infos = PopUpInformation(self.project)
        self.tab_infos.setObjectName("tab_infos")
        self.tab_widget.addTab(
            self.tab_infos, _translate("Dialog", "Information")
        )

        # The 'OK' push button
        self.push_button_ok = QtWidgets.QPushButton("OK")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)

        # The 'Cancel' push button
        self.push_button_cancel = QtWidgets.QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        hbox_buttons.addWidget(self.push_button_cancel)

        vbox = QVBoxLayout()
        vbox.addWidget(self.tab_widget)
        vbox.addLayout(hbox_buttons)

        self.setLayout(vbox)

    def ok_clicked(self):
        """Saves the modifications and updates the data browser."""

        history_maker = ["modified_visibilities", self.old_tags]
        new_visibilities = []

        for x in range(self.tab_tags.list_widget_selected_tags.count()):
            visible_tag = self.tab_tags.list_widget_selected_tags.item(
                x
            ).text()
            new_visibilities.append(visible_tag)

        new_visibilities.append(TAG_FILENAME)

        with self.project.database.data() as database_data:
            database_data.set_shown_tags(new_visibilities)

        history_maker.append(new_visibilities)

        self.project.undos.append(history_maker)
        self.project.redos.clear()
        self.project.unsavedModifications = True

        # Columns updated
        with self.project.database.data() as database_data:
            self.databrowser.table_data.update_visualized_columns(
                self.old_tags, database_data.get_shown_tags()
            )

        self.accept()
        self.close()


class PopUpQuit(QDialog):
    """Is called when the user closes the software and the current project has
      been modified.

    .. Methods:
        - can_exit: returns the value of bool_exit
        - cancel_clicked: makes the actions to cancel the action
        - do_not_save_clicked: makes the actions not to save the project
        - save_as_clicked: makes the actions to save the project

    """

    save_as_signal = pyqtSignal()
    do_not_save_signal = pyqtSignal()
    cancel_signal = pyqtSignal()

    def __init__(self, project):
        """Initialization.

        :param project: current project

        """
        super().__init__()
        self.project = project
        self.bool_exit = False
        self.setWindowTitle("Confirm exit")
        label = QLabel(self)
        label.setText(
            f"Do you want to exit without saving {self.project.getName()}?"
        )
        push_button_save_as = QPushButton("Save", self)
        push_button_do_not_save = QPushButton("Do not save", self)
        push_button_cancel = QPushButton("Cancel", self)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(push_button_save_as)
        hbox.addWidget(push_button_do_not_save)
        hbox.addWidget(push_button_cancel)
        hbox.addStretch(1)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        push_button_save_as.clicked.connect(self.save_as_clicked)
        push_button_do_not_save.clicked.connect(self.do_not_save_clicked)
        push_button_cancel.clicked.connect(self.cancel_clicked)

    def can_exit(self):
        """Return the value of bool_exit.

        :return: bool_exit value

        """
        return self.bool_exit

    def cancel_clicked(self):
        """Makes the actions to cancel the action."""
        self.bool_exit = False
        self.close()

    def do_not_save_clicked(self):
        """Makes the actions not to save the project."""
        self.bool_exit = True
        self.close()

    def save_as_clicked(self):
        """Makes the actions to save the project."""
        self.save_as_signal.emit()
        self.bool_exit = True
        self.close()


class PopUpRemoveScan(QDialog):
    """Is called when the user wants to remove a scan that was previously sent
       to the pipeline manager.

    :param scan: The scan that may be removed
    :param size: The number of scan the user wants to remove

     .. Methods:
         - cancel_clicked:
         - no_all_clicked:
         - yes_all_clicked:
         - yes_clicked:

    """

    def __init__(self, scan, size):
        super().__init__()

        self.setWindowTitle("The document exists in the pipeline manager")
        self.stop = False
        self.repeat = False
        label = QLabel(self)
        label.setText(
            f"The document {scan} \nwas previously sent to the pipeline "
            f"manager, do you really want to delete it?"
        )
        push_button_yes = QPushButton("Ok", self)
        push_button_cancel = QPushButton("No", self)

        if size > 1:
            push_button_yes_all = QPushButton("Ok to all", self)
            push_button_no_all = QPushButton("No to all", self)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(push_button_yes)
        hbox.addWidget(push_button_cancel)
        if size > 1:
            hbox.addWidget(push_button_yes_all)
            hbox.addWidget(push_button_no_all)

        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        push_button_yes.clicked.connect(self.yes_clicked)
        push_button_cancel.clicked.connect(self.cancel_clicked)
        if size > 1:
            push_button_yes_all.clicked.connect(self.yes_all_clicked)
            push_button_no_all.clicked.connect(self.no_all_clicked)

    def cancel_clicked(self):
        """Blabla"""

        self.stop = True
        self.repeat = False
        self.close()

    def no_all_clicked(self):
        """Blabla"""

        self.stop = True
        self.repeat = True
        self.close()

    def yes_all_clicked(self):
        """Blabla"""

        self.stop = False
        self.repeat = True
        self.close()

    def yes_clicked(self):
        """Blabla"""

        self.stop = False
        self.repeat = False
        self.close()


class PopUpRemoveTag(QDialog):
    """Is called when the user wants to remove a user tag from
      populse_mia project.

    .. Methods:
        - ok_action: verifies the selected tags and send the information to
           the data browser
        - search_str: matches the searched pattern with the tags of the project

    """

    # Signal that will be emitted at the end to tell that
    # the project has been created
    signal_remove_tag = pyqtSignal()

    def __init__(self, databrowser, project):
        """Initialization

        :param databrowser: current project in the software
        :param project: data browser instance of the software
        """
        super().__init__()
        self.databrowser = databrowser
        self.project = project
        self.setWindowTitle("Remove a tag")
        self.setModal(True)

        _translate = QtCore.QCoreApplication.translate
        self.setObjectName("Remove a tag")

        # The 'OK' push button
        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setObjectName("push_button_ok")
        self.push_button_ok.setText(_translate("Remove a tag", "OK"))

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)

        # The "Tag list" label
        self.label_tag_list = QtWidgets.QLabel(self)
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.label_tag_list.setText(
            _translate("Remove a tag", "Available tags:")
        )

        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.search_str)

        hbox_top = QHBoxLayout()
        hbox_top.addWidget(self.label_tag_list)
        hbox_top.addStretch(1)
        hbox_top.addWidget(self.search_bar)

        # The list of tags
        self.list_widget_tags = QtWidgets.QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        self.list_widget_tags.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection
        )

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_top)
        vbox.addWidget(self.list_widget_tags)
        vbox.addLayout(hbox_buttons)

        self.setLayout(vbox)

        with self.project.database.data() as database_data:

            for tag in database_data.get_field_attributes(COLLECTION_CURRENT):

                if tag["origin"] == TAG_ORIGIN_USER:
                    item = QtWidgets.QListWidgetItem()
                    self.list_widget_tags.addItem(item)
                    item.setText(
                        _translate("Dialog", tag["index"].split("|")[1])
                    )

        self.setLayout(vbox)

        # Connecting the OK push buttone
        self.push_button_ok.clicked.connect(self.ok_action)

    def ok_action(self):
        """Verifies the selected tags and send the information to the data
        browser.

        """

        self.accept()
        self.tag_names_to_remove = []
        for item in self.list_widget_tags.selectedItems():
            self.tag_names_to_remove.append(item.text())
        self.databrowser.remove_tag_infos(self.tag_names_to_remove)
        self.close()

    def search_str(self, str_search):
        """
        Matches the searched pattern with the tags of the project

        :param str_search: string pattern to search
        """

        _translate = QtCore.QCoreApplication.translate
        return_list = []

        with self.project.database.data() as database_data:
            field_attributes = database_data.get_field_attributes(
                COLLECTION_CURRENT
            )

        if str_search:

            for tag in field_attributes:

                if tag["origin"] == TAG_ORIGIN_USER:

                    if (
                        str_search.upper()
                        in tag["index"].split("|")[1].upper()
                    ):
                        return_list.append(tag.name)

        else:

            for tag in field_attributes:

                if tag["origin"] == TAG_ORIGIN_USER:
                    return_list.append(tag.name)

        self.list_widget_tags.clear()

        for tag_name in return_list:
            item = QtWidgets.QListWidgetItem()
            self.list_widget_tags.addItem(item)
            item.setText(_translate("Dialog", tag_name))


class PopUpSaveProjectAs(QDialog):
    """Is called when the user wants to save a project under another name.

    .. Method:
        - fill_input: fills the input field when a project is clicked on
        - return_value: sets the widget's attributes depending on the
          selected file name

    """

    # Signal that will be emitted at the end to tell
    # that the new file name has been chosen
    signal_saved_project = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Save project as")
        self.validate = False
        self.new_project = QLineEdit()
        self.new_project_label = QLabel("New project name")
        self.config = Config()
        self.project_path = self.config.get_projects_save_path()

        project_list = os.listdir(self.project_path)

        self.v_box = QVBoxLayout()

        # Label
        self.label = QLabel("Projects list:")

        project_list.sort()
        for i in range(0, len(project_list)):
            if os.path.isdir(os.path.join(self.project_path, project_list[i])):
                label = QLabel_clickable(project_list[i])
                label.clicked.connect(
                    partial(self.fill_input, project_list[i])
                )
                self.v_box.addWidget(label)

        # The text input
        self.h_box_text = QHBoxLayout()
        self.h_box_text.addWidget(self.new_project_label)
        self.h_box_text.addWidget(self.new_project)

        self.h_box_bottom = QHBoxLayout()
        self.h_box_bottom.addStretch(1)

        # The 'OK' push button
        self.push_button_ok = QtWidgets.QPushButton("Save as")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.return_value)
        self.h_box_bottom.addWidget(self.push_button_ok)

        # The 'Cancel' push button
        self.push_button_cancel = QtWidgets.QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)
        self.h_box_bottom.addWidget(self.push_button_cancel)

        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setMaximumHeight(250)
        self.widget = QWidget()
        self.widget.setLayout(self.v_box)
        self.scroll.setWidget(self.widget)

        self.final = QVBoxLayout()
        self.final.addWidget(self.scroll)

        self.final_layout = QVBoxLayout()
        self.final_layout.addWidget(self.label)
        self.final_layout.addLayout(self.final)
        self.final_layout.addLayout(self.h_box_text)
        self.final_layout.addLayout(self.h_box_bottom)

        self.setLayout(self.final_layout)

    def fill_input(self, name):
        """Fills the input field with the name of a project."""
        self.new_project.setText(name)

    def return_value(self):
        """Sets the widget's attributes depending on the selected file name.

        :return: new project's file name

        """
        # import message_already_exists only here to prevent circular
        # import issue
        from populse_mia.utils import message_already_exists

        file_name_tuple = self.new_project.text()

        if len(file_name_tuple) > 0:
            file_name = file_name_tuple
            projects_folder = self.project_path

            if file_name:
                entire_path = os.path.abspath(
                    os.path.join(projects_folder, file_name)
                )
                self.path, self.name = os.path.split(entire_path)
                self.total_path = entire_path
                self.relative_path = os.path.relpath(entire_path)
                self.relative_subpath = os.path.relpath(self.path)

                if not os.path.exists(self.relative_path) and self.name != "":
                    self.signal_saved_project.emit()
                    self.validate = True
                    self.close()
                    # A signal is emitted to tell that the project
                    # has been created
                elif file_name == "":
                    return
                else:
                    if self.config.get_user_mode():
                        message_already_exists()
                        return
                    else:
                        msgtext = (
                            f"Do you really want to overwrite the {file_name} "
                            f"project ?\nThis action delete all contents "
                            f"inside this folder!"
                        )
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        title = "populse_mia - Warning: Overwriting project"
                        reply = msg.question(
                            self,
                            title,
                            msgtext,
                            QMessageBox.Yes | QMessageBox.No,
                        )
                        if reply == QMessageBox.Yes:
                            self.validate = True
                            self.close()
                        else:
                            return

            return entire_path


class PopUpSeeAllProjects(QDialog):
    """Is called when the user wants to create a see all the projects.

    .. Methods:
        - checkState: checks if the project still exists and returns the
                      corresponding icon
        - item_to_path: returns the path of the first selected item
        - open_project: switches to the selected project

    """

    def __init__(self, saved_projects, main_window):
        """Initialization.

        :param saved_projects: List of saved projects
        :param main_window: Main window

        """

        super().__init__()

        self.mainWindow = main_window

        self.setWindowTitle("See all saved projects")
        self.setMinimumWidth(500)

        # Tree widget

        self.label = QLabel()
        self.label.setText("List of saved projects")

        self.treeWidget = QTreeWidget()
        self.treeWidget.setColumnCount(3)
        self.treeWidget.setHeaderLabels(["Name", "Path", "State"])

        i = -1
        for path in saved_projects.pathsList:
            i += 1
            text = os.path.basename(path)
            wdg = QTreeWidgetItem()
            wdg.setText(0, text)
            wdg.setText(1, os.path.abspath(path))
            wdg.setIcon(2, self.checkState(path))

            self.treeWidget.addTopLevelItem(wdg)

        hd = self.treeWidget.header()
        hd.setSectionResizeMode(QHeaderView.ResizeToContents)

        # Buttons

        # The 'Open project' push button
        self.pushButtonOpenProject = QPushButton("Open project")
        self.pushButtonOpenProject.setObjectName("pushButton_ok")
        self.pushButtonOpenProject.clicked.connect(self.open_project)

        # The 'Cancel' push button
        self.pushButtonCancel = QPushButton("Cancel")
        self.pushButtonCancel.setObjectName("pushButton_cancel")
        self.pushButtonCancel.clicked.connect(self.close)

        # Layouts
        self.hBoxButtons = QHBoxLayout()
        self.hBoxButtons.addStretch(1)
        self.hBoxButtons.addWidget(self.pushButtonOpenProject)
        self.hBoxButtons.addWidget(self.pushButtonCancel)

        self.vBox = QVBoxLayout()
        self.vBox.addWidget(self.label)
        self.vBox.addWidget(self.treeWidget)
        self.vBox.addLayout(self.hBoxButtons)

        self.setLayout(self.vBox)

    def checkState(self, path):
        """Checks if the project still exists and returns the corresponding
           icon.

        :param path: path of the project
        :return: either a green "v" or a red cross depending on
          the existence of the project

        """

        sources_images_dir = Config().getSourceImageDir()
        if os.path.exists(os.path.join(path)):
            icon = QIcon(os.path.join(sources_images_dir, "green_v.png"))
        else:
            icon = QIcon(os.path.join(sources_images_dir, "red_cross.png"))
        return icon

    def item_to_path(self):
        """Returns the path of the first selected item.

        :return: the path of the first selected item

        """

        nb_items = len(self.treeWidget.selectedItems())
        if nb_items == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a project to open")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()
            return ""
        else:
            item = self.treeWidget.selectedItems()[0]
            text = item.text(1)
            return text

    def open_project(self):
        """Switches to the selected project."""

        file_name = self.item_to_path()
        if file_name != "":
            entire_path = os.path.abspath(file_name)
            self.path, self.name = os.path.split(entire_path)
            self.relative_path = os.path.relpath(file_name)
            project_switched = self.mainWindow.switch_project(
                self.relative_path, self.name
            )

            if project_switched:
                self.accept()
                self.close()


class PopUpSelectFilter(PopUpFilterSelection):
    """Is called when the user wants to open a filter that has already been
       saved.

    .. Methods:
        - ok_clicked: saves the modifications and updates the data browser

    """

    def __init__(self, project, databrowser):
        """Initialization.

        :param project: current project in the software
        :param databrowser: data browser instance of the software

        """

        super().__init__(project)
        self.project = project
        self.databrowser = databrowser
        self.config = Config()
        self.setWindowTitle("Open a filter")

        # Filling the filter list
        for filter in self.project.filters:
            item = QtWidgets.QListWidgetItem()
            self.list_widget_filters.addItem(item)
            item.setText(filter.name)

    def ok_clicked(self):
        """Saves the modifications and updates the data browser."""

        for item in self.list_widget_filters.selectedItems():
            # Current filter updated
            filter_name = item.text()
            filter_object = self.project.getFilter(filter_name)
            self.project.setCurrentFilter(filter_object)
            break

        self.databrowser.open_filter_infos()

        self.accept()
        self.close()


class PopUpSelectIteration(QDialog):
    """Is called when the user wants to run an iterated pipeline.

    .. Methods:
        - ok_clicked: sends the selected values to the pipeline manager

    """

    def __init__(self, iterated_tag, tag_values):
        """Initialization.

        :param iterated_tag: name of the iterated tag
        :param tag_values: values that can take the iterated tag

        """

        super().__init__()

        self.iterated_tag = iterated_tag
        self.tag_values = tag_values
        self.final_values = []
        self.setWindowTitle(
            f"Iterate pipeline run over tag {self.iterated_tag}"
        )

        self.v_box = QVBoxLayout()

        # Label
        self.label = QLabel("Select values to iterate over:")
        self.v_box.addWidget(self.label)

        self.check_boxes = []
        for tag_value in self.tag_values:
            check_box = QCheckBox(tag_value)
            check_box.setCheckState(QtCore.Qt.Checked)
            self.check_boxes.append(check_box)
            self.v_box.addWidget(check_box)

        self.h_box_bottom = QHBoxLayout()
        self.h_box_bottom.addStretch(1)

        # The 'OK' push button
        self.push_button_ok = QtWidgets.QPushButton("OK")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)
        self.h_box_bottom.addWidget(self.push_button_ok)

        # The 'Cancel' push button
        self.push_button_cancel = QtWidgets.QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)
        self.h_box_bottom.addWidget(self.push_button_cancel)

        self.scroll = QScrollArea()
        self.widget = QWidget()
        self.widget.setLayout(self.v_box)
        self.scroll.setWidget(self.widget)

        self.final = QVBoxLayout()
        self.final.addWidget(self.scroll)

        self.final_layout = QVBoxLayout()
        self.final_layout.addLayout(self.final)
        self.final_layout.addLayout(self.h_box_bottom)

        self.setLayout(self.final_layout)

    def ok_clicked(self):
        """Sends the selected values to the pipeline manager."""

        final_values = []
        for check_box in self.check_boxes:
            if check_box.isChecked():
                final_values.append(check_box.text())

        self.final_values = final_values

        self.accept()
        self.close()


class PopUpTagSelection(QDialog):
    """Is called when the user wants to update the tags that are visualized in
       the data browser.

    .. Methods:
        - cancel_clicked: closes the pop-up
        - item_clicked: checks the checkbox of an item when the latter
          is clicked
        - ok_clicked: actions when the "OK" button is clicked
        - search_str: matches the searched pattern with the tags of the project

    """

    def __init__(self, project):
        """Initialization.

        :param project: current project in the software

        """

        super().__init__()
        self.project = project

        _translate = QtCore.QCoreApplication.translate

        # The "Tag list" label
        self.label_tag_list = QtWidgets.QLabel(self)
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.label_tag_list.setText(
            _translate("main_window", "Available tags:")
        )

        # The search bar to search in the list of tags
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.search_str)

        # The list of tags
        self.list_widget_tags = QtWidgets.QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        self.list_widget_tags.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.list_widget_tags.itemClicked.connect(self.item_clicked)

        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.setText("OK")
        self.push_button_ok.clicked.connect(self.ok_clicked)

        self.push_button_cancel = QtWidgets.QPushButton(self)
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.setText("Cancel")
        self.push_button_cancel.clicked.connect(self.cancel_clicked)

        hbox_top_left = QHBoxLayout()
        hbox_top_left.addWidget(self.label_tag_list)
        hbox_top_left.addWidget(self.search_bar)

        vbox_top_left = QVBoxLayout()
        vbox_top_left.addLayout(hbox_top_left)
        vbox_top_left.addWidget(self.list_widget_tags)

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        hbox_buttons.addWidget(self.push_button_cancel)

        vbox_final = QVBoxLayout()
        vbox_final.addLayout(vbox_top_left)
        vbox_final.addLayout(hbox_buttons)

        self.setLayout(vbox_final)

    def cancel_clicked(self):
        """Closes the pop-up."""

        self.close()

    def item_clicked(self, item):
        """Checks the checkbox of an item when the latter is clicked.

        :param item: clicked item

        """

        for idx in range(self.list_widget_tags.count()):
            itm = self.list_widget_tags.item(idx)
            if itm == item:
                itm.setCheckState(QtCore.Qt.Checked)
            else:
                itm.setCheckState(QtCore.Qt.Unchecked)

    def ok_clicked(self):
        """Actions when the "OK" button is clicked."""

        # Has to be override in the PopUpSelectTag* classes
        pass

    def search_str(self, str_search):
        """Matches the searched pattern with the tags of the project.

        :param str_search: string pattern to search

        """
        return_list = []

        with self.project.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)

        if str_search:

            for tag in field_names:

                if tag != TAG_CHECKSUM and tag != TAG_HISTORY:

                    if str_search.upper() in tag.upper():
                        return_list.append(tag)

        else:

            for tag in field_names:

                if tag != TAG_CHECKSUM and tag != TAG_HISTORY:
                    return_list.append(tag)

        for idx in range(self.list_widget_tags.count()):
            item = self.list_widget_tags.item(idx)

            if item.text() in return_list:
                item.setHidden(False)

            else:
                item.setHidden(True)


class PopUpSelectTag(PopUpTagSelection):
    """Is called when the user wants to update the tag to display in the mini
      viewer.

    .. Methods:
        - ok_clicked: saves the modifications and updates the mini viewer

    """

    def __init__(self, project):
        """Initialization.

        :param project: current project in the software

        """
        super().__init__(project)
        self.project = project
        self.config = Config()

        with self.project.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)

        # Filling the list and checking the thumbnail tag
        for tag in field_names:

            if tag != TAG_CHECKSUM and tag != TAG_HISTORY:
                item = QtWidgets.QListWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)

                if tag == self.config.getThumbnailTag():
                    item.setCheckState(QtCore.Qt.Checked)

                else:
                    item.setCheckState(QtCore.Qt.Unchecked)

                self.list_widget_tags.addItem(item)
                item.setText(tag)

        self.list_widget_tags.sortItems()

    def ok_clicked(self):
        """
        Saves the modifications and updates the mini viewer
        """
        for idx in range(self.list_widget_tags.count()):
            item = self.list_widget_tags.item(idx)
            if item.checkState() == QtCore.Qt.Checked:
                self.config.setThumbnailTag(item.text())
                break

        self.accept()
        self.close()


class PopUpSelectTagCountTable(PopUpTagSelection):
    """Is called when the user wants to update a visualized tag of the count
       table.

    .. Methods:
        - ok_clicked: updates the selected tag and closes the pop-up

    """

    def __init__(self, project, tags_to_display, tag_name_checked=None):
        """Initialization.

        :param project: current project in the software
        :param tags_to_display: the tags to display
        :param tag_name_checked: the checked tags

        """

        super().__init__(project)

        self.selected_tag = None
        for tag in tags_to_display:
            if tag != TAG_CHECKSUM and tag != TAG_HISTORY:
                item = QtWidgets.QListWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                if tag == tag_name_checked:
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)
                self.list_widget_tags.addItem(item)
                item.setText(tag)
        self.list_widget_tags.sortItems()

    def ok_clicked(self):
        """Updates the selected tag and closes the pop-up."""

        for idx in range(self.list_widget_tags.count()):
            item = self.list_widget_tags.item(idx)
            if item.checkState() == QtCore.Qt.Checked:
                self.selected_tag = item.text()
                break

        self.accept()
        self.close()


class PopUpShowHistory(QDialog):
    """Class to display the history of a document.

    .. Methods:
        - file_clicked: close the history window and select the file in the
          data browser
        - find_associated_bricks:
        - find_process_from_plug:
        - io_value_is_scan: checks if the I/O value is a scan
        - node_selected: called when a pipeline node is clicked
        - _updateio_table: fill in the input and output sections of the table
        - update_table: update the brick row at the bottom
    """

    def __init__(self, project, brick_uuid, scan, databrowser, main_window):
        """Prepares the brick history popup.

        :param project: current project in the software
        :param scan: filename of the scan
        :param databrowser: data browser instance of the software
        :param main_window: main window of the software

        """

        super().__init__()

        # We do not want few parameters in the outputs parameters display
        self.banished_param = ["notInDb", "dict4runtime"]

        self.setModal(False)
        self.setWindowFlags(
            self.windowFlags() & QtCore.Qt.WindowStaysOnBottomHint
        )

        self.databrowser = databrowser
        self.main_window = main_window
        self.project = project
        self.setWindowTitle(f"History of {scan}")

        with self.project.database.data() as database_data:
            brick_row = database_data.get_document(
                ollection_name=COLLECTION_BRICK, primary_keys=brick_uuid
            )
            full_brick_name = database_data.get_value(
                collection_name=COLLECTION_BRICK,
                primary_key=brick_uuid,
                field=BRICK_NAME,
            ).split(".")
            layout = QVBoxLayout()
            self.splitter = QSplitter(Qt.Qt.Vertical)
            self.table = QTableWidget()
            self.table.setVerticalScrollMode(
                QtWidgets.QAbstractItemView.ScrollPerPixel
            )
            self.table.setHorizontalScrollMode(
                QtWidgets.QAbstractItemView.ScrollPerPixel
            )
            history_uuid = database_data.get_value(
                collection_name=COLLECTION_CURRENT,
                primary_key=scan,
                field=TAG_HISTORY,
            )
            self.unitary_pipeline = False
            self.uuid_idx = 0

        if history_uuid is not None:

            with self.project.database.data() as database_data:
                self.pipeline_xml = database_data.get_value(
                    collection_name=COLLECTION_HISTORY,
                    primary_key=history_uuid,
                    field=HISTORY_PIPELINE,
                )

            if self.pipeline_xml is not None:

                with self.project.database.data() as database_data:
                    self.brick_list = database_data.get_value(
                        collection_name=COLLECTION_HISTORY,
                        primary_key=history_uuid,
                        field=HISTORY_BRICKS,
                    )

                engine = Config.get_capsul_engine()

                try:
                    pipeline = engine.get_process_instance(self.pipeline_xml)

                except Exception:
                    pipeline = None

                if pipeline is not None:

                    # handle case of pipeline node alone --> exploded view
                    # (e.g. a pipeline alone and plug exported)
                    if len(pipeline.nodes) == 2:

                        for key in pipeline.nodes.keys():

                            if key != "":

                                if isinstance(
                                    pipeline.nodes[key], PipelineNode
                                ):
                                    pipeline = pipeline.nodes[key].process
                                    full_brick_name.pop(0)
                                    self.unitary_pipeline = True

                    # handle cases of named pipeline/brick without being a
                    # single Pipeline node (e.g. a pipeline alone without
                    # exporting plugs)
                    if (
                        not self.unitary_pipeline
                        and pipeline.name != "CustomPipeline"
                    ) or (
                        len(full_brick_name) == 2
                        # FIXME: We have "main" when ?
                        and full_brick_name[1] == "main"
                    ):
                        full_brick_name.pop(0)
                        self.unitary_pipeline = True

                    self.pipeline_view = PipelineDeveloperView(
                        pipeline, allow_open_controller=False
                    )
                    self.pipeline_view.auto_dot_node_positions()
                    self.splitter.addWidget(self.pipeline_view)
                    self.pipeline_view.node_clicked.connect(self.node_selected)
                    (self.pipeline_view.process_clicked.connect)(
                        self.node_selected
                    )
                    bricks = self.find_associated_bricks(full_brick_name[0])

                    for bricks_uuids in bricks.values():

                        for i in range(0, len(bricks_uuids)):

                            if bricks_uuids[i] == brick_uuid:
                                self.uuid_idx = i
                                break

                        else:
                            continue

                        break

                    selected_name = full_brick_name[0]

                    try:
                        self.node_selected(
                            selected_name, pipeline.nodes[selected_name]
                        )

                    except Exception:
                        logger.warning(
                            "Error in naming association brick\\pipeline, "
                            "cannot select node ..."
                        )
                        pass

        inputs = brick_row[0][BRICK_INPUTS]
        outputs = brick_row[0][BRICK_OUTPUTS]

        for k in self.banished_param:
            outputs.pop(k, None)
            inputs.pop(k, None)

        brick_name = brick_row[0][BRICK_NAME]
        init = brick_row[0][BRICK_INIT]
        init_time = brick_row[0][BRICK_INIT_TIME]
        exec = brick_row[0][BRICK_INIT]
        exec_time = brick_row[0][BRICK_INIT_TIME]
        self.update_table(
            inputs, outputs, brick_name, init, init_time, exec, exec_time
        )
        self.splitter.addWidget(self.table)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        screen_resolution = QApplication.instance().desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        self.setGeometry(300, 200, round(0.6 * width), round(0.4 * height))

    def file_clicked(self):
        """
        Close the history window and select the file in the data browser.
        """

        file = self.sender().text()
        self.databrowser.table_data.clearSelection()
        row_to_select = self.databrowser.table_data.get_scan_row(file)
        self.databrowser.table_data.selectRow(row_to_select)
        item_to_scroll_to = self.databrowser.table_data.item(row_to_select, 0)
        self.databrowser.table_data.scrollToItem(item_to_scroll_to)
        self.close()

    def find_associated_bricks(self, node_name):
        """Blabla

        :param node_name: blabla
        :return: blabla
        """
        bricks = {}

        for uuid in self.brick_list:

            with self.project.database.data() as database_data:
                full_brick_name = database_data.get_value(
                    collection_name=COLLECTION_BRICK,
                    primary_key=uuid,
                    field=BRICK_NAME,
                )

            list_full_brick_name = full_brick_name.split(".")

            if self.unitary_pipeline:
                list_full_brick_name.pop(0)

            if list_full_brick_name[0] == node_name:

                if full_brick_name not in bricks:
                    bricks[full_brick_name] = [uuid]

                else:
                    bricks[full_brick_name].append(uuid)

        return bricks

    def find_process_from_plug(self, plug):
        """Blabla

        :param plug: blabla
        :return: blabla
        """

        process_name = ""
        plug_name = ""
        if plug.output:
            link_done = False
            for link in plug.links_from:
                if not link_done:
                    link_done = True
                    process_name = f"{process_name}.{link[2].name}"
                    plug_name = link[1]
                    if isinstance(link[2], PipelineNode):
                        (
                            sub_process_name,
                            plug_name,
                        ) = self.find_process_from_plug(link[2].plugs[link[1]])
                        process_name = f"{process_name}{sub_process_name}"
        else:
            link_done = False
            for link in plug.links_to:
                if not link_done:
                    link_done = True
                    process_name = f"{process_name}.{link[2].name}"
                    plug_name = link[1]
                    if isinstance(link[2], PipelineNode):
                        (
                            sub_process_name,
                            plug_name,
                        ) = self.find_process_from_plug(link[2].plugs[link[1]])
                        process_name = f"{process_name}{sub_process_name}"
        return process_name, plug_name

    def io_value_is_scan(self, value):
        """Checks if the I/O value is a scan.

        :param value: I/O value
        :return: The scan corresponding to the value if it exists,
         None otherwise

        """

        value_scan = None

        with self.project.database.data() as database_data:

            for scan in database_data.get_document_names(COLLECTION_CURRENT):

                if scan in str(value):
                    value_scan = scan

        return value_scan

    def node_selected(self, node_name, process):
        """Emit a signal when a node is clicked.

        :param node_name: node name
        :param process: process of the corresponding node
        """

        if hasattr(process, "pipeline_node"):
            process = process.pipeline_node

        bricks = self.find_associated_bricks(node_name)

        if hasattr(process, "full_name") and node_name in process.full_name:
            full_node_name = process.full_name

        if bricks:

            if len(bricks) == 1:
                brick_row = self.project.database.get_document(
                    collection_name=COLLECTION_BRICK,
                    primary_keys=next(iter(bricks.values()))[self.uuid_idx],
                )
                inputs = brick_row[0][BRICK_INPUTS]
                outputs = brick_row[0][BRICK_OUTPUTS]

                for k in self.banished_param:
                    outputs.pop(k, None)
                    inputs.pop(k, None)

                brick_name = brick_row[0][BRICK_NAME]
                init = brick_row[0][BRICK_INIT]
                init_time = brick_row[0][BRICK_INIT_TIME]
                exec = brick_row[0][BRICK_INIT]
                exec_time = brick_row[0][BRICK_INIT_TIME]
                self.update_table(
                    inputs,
                    outputs,
                    brick_name,
                    init,
                    init_time,
                    exec,
                    exec_time,
                )
            else:
                # subpipeline case
                inputs_dict = {}
                outputs_dict = {}

                if isinstance(process, PipelineNode):

                    for plug_name, plug in process.plugs.items():

                        if plug.activated:
                            (
                                process_name,
                                inner_plug_name,
                            ) = self.find_process_from_plug(plug)

                            for uuid in bricks.values():
                                full_brick_name = (
                                    self.project.database.get_value(
                                        collection_name=COLLECTION_BRICK,
                                        primary_key=uuid[0],
                                        field=BRICK_NAME,
                                    )
                                )

                                if (
                                    full_brick_name
                                    == f"{full_node_name}{process_name}"
                                ):

                                    if plug.output:
                                        plugs = (
                                            self.project.database.get_value(
                                                collection_name=(
                                                    COLLECTION_BRICK
                                                ),
                                                primary_key=uuid[
                                                    self.uuid_idx
                                                ],
                                                field=BRICK_OUTPUTS,
                                            )
                                        )
                                        outputs_dict[plug_name] = plugs[
                                            inner_plug_name
                                        ]

                                    else:
                                        plugs = (
                                            self.project.database.get_value(
                                                collection_name=(
                                                    COLLECTION_BRICK
                                                ),
                                                primary_key=uuid[
                                                    self.uuid_idx
                                                ],
                                                field=BRICK_INPUTS,
                                            )
                                        )
                                        inputs_dict[plug_name] = plugs[
                                            inner_plug_name
                                        ]

                for k in self.banished_param:
                    outputs_dict.pop(k, None)
                    inputs_dict.pop(k, None)

                self.update_table(inputs_dict, outputs_dict, full_node_name)

            for name, gnode in self.pipeline_view.scene.gnodes.items():

                if name == node_name:
                    gnode.fonced_viewer(False)

                else:
                    gnode.fonced_viewer(True)

    def _updateio_table(self, io_dict, item_idx):
        """Fill in the input and output sections of the table.

        :param io_dict: inputs / outputs dictionary
        :param item_idx: current column element index
        :return: new current column element index
        """
        for key, value in sorted(io_dict.items()):
            item = QTableWidgetItem()
            item.setText(key)
            self.table.setHorizontalHeaderItem(item_idx, item)

            if isinstance(value, list) and value:
                widget = QWidget()
                v_layout = QVBoxLayout()
                v_layout.setAlignment(QtCore.Qt.AlignTop)
                label = QLabel("[")
                v_layout.addWidget(label)

                for sub_value in value:
                    if isinstance(sub_value, list) and sub_value:
                        label = QLabel("[")
                        v_layout.addWidget(label)

                        for sub_sub_value in sub_value:
                            sub_sub_value = str(sub_sub_value)
                            value_scan = self.io_value_is_scan(sub_sub_value)

                            if value_scan is None:
                                del v_layout
                                del label
                                v_layout = QVBoxLayout()
                                # v_layout.setAlignment(QtCore.Qt.AlignTop)
                                v_layout.setAlignment(
                                    QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
                                )
                                label = QLabel(str(value))
                                v_layout.addWidget(label)
                                break

                            else:
                                h_layout = QHBoxLayout()
                                h_layout.setAlignment(QtCore.Qt.AlignLeft)
                                button = QPushButton(value_scan)
                                button.clicked.connect(self.file_clicked)
                                h_layout.addWidget(button)
                                label = QLabel(",")
                                h_layout.addWidget(label)
                                v_layout.addLayout(h_layout)

                        else:
                            label = QLabel("],")
                            v_layout.addWidget(label)
                            continue

                        break

                    else:
                        sub_value = str(sub_value)
                        value_scan = self.io_value_is_scan(sub_value)

                        if value_scan is None:
                            del v_layout
                            del label
                            v_layout = QVBoxLayout()
                            # v_layout.setAlignment(QtCore.Qt.AlignTop)
                            v_layout.setAlignment(
                                QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
                            )
                            label = QLabel(str(value))
                            v_layout.addWidget(label)
                            break

                        else:
                            h_layout = QHBoxLayout()
                            button = QPushButton(value_scan)
                            button.clicked.connect(self.file_clicked)
                            h_layout.addWidget(button)
                            label = QLabel(",")
                            h_layout.addWidget(label)
                            v_layout.addLayout(h_layout)

                else:
                    label = QLabel("]")
                    v_layout.addWidget(label)

                widget.setLayout(v_layout)
                self.table.setCellWidget(0, item_idx, widget)

            else:
                value_scan = self.io_value_is_scan(str(value))

                if value_scan is not None:
                    widget = QWidget()
                    v_layout = QVBoxLayout()
                    button = QPushButton(value_scan)
                    button.clicked.connect(self.file_clicked)
                    v_layout.addWidget(button)
                    # v_layout.setAlignment(QtCore.Qt.AlignTop)
                    # v_layout.setAlignment(QtCore.Qt.AlignCenter)
                    v_layout.setAlignment(
                        QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
                    )
                    widget.setLayout(v_layout)
                    self.table.setCellWidget(0, item_idx, widget)

                else:
                    widget = QWidget()
                    v_layout = QVBoxLayout()
                    # v_layout.setAlignment(QtCore.Qt.AlignTop)
                    v_layout.setAlignment(
                        QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
                    )
                    label = QLabel(str(value))
                    v_layout.addWidget(label)
                    widget.setLayout(v_layout)
                    self.table.setCellWidget(0, item_idx, widget)

            item_idx += 1

        return item_idx

    def update_table(
        self,
        inputs,
        outputs,
        brick_name,
        init="",
        init_time=None,
        exec="",
        exec_time=None,
    ):
        """Filling the table.

        :param inputs: inputs dictionary
        :param outputs: outputs dictionary
        :param brick_name: name of the brick
        :param init: initialisation status
        :param init_time: init date / time
        :param exec: execution status
        :param exec_time: execution date / time

        """

        self.table.removeRow(0)
        self.table.setRowCount(1)
        nbColumn = 1

        if init != "":
            nbColumn += 2

        if exec != "":
            nbColumn += 2

        self.table.setColumnCount(nbColumn + len(inputs) + len(outputs))
        # Brick name
        item_idx = 0
        item = QTableWidgetItem()
        item.setText(BRICK_NAME)
        self.table.setHorizontalHeaderItem(item_idx, item)
        widget = QWidget()
        v_layout = QVBoxLayout()
        v_layout.setAlignment(QtCore.Qt.AlignTop)
        label = QLabel(brick_name)
        v_layout.addWidget(label)
        widget.setLayout(v_layout)
        self.table.setCellWidget(0, item_idx, widget)
        item_idx += 1

        # Brick init
        if init != "":
            item = QTableWidgetItem()
            item.setText(BRICK_INIT)
            self.table.setHorizontalHeaderItem(item_idx, item)
            widget = QWidget()
            v_layout = QVBoxLayout()
            v_layout.setAlignment(QtCore.Qt.AlignTop)
            label = QLabel(init)
            v_layout.addWidget(label)
            widget.setLayout(v_layout)
            self.table.setCellWidget(0, item_idx, widget)
            item_idx += 1

            # Brick init time
            item = QTableWidgetItem()
            item.setText(BRICK_INIT_TIME)
            self.table.setHorizontalHeaderItem(item_idx, item)
            widget = QWidget()
            v_layout = QVBoxLayout()
            v_layout.setAlignment(QtCore.Qt.AlignTop)

            if init_time is not None:
                label = QLabel(str(init_time))

            v_layout.addWidget(label)
            widget.setLayout(v_layout)
            self.table.setCellWidget(0, item_idx, widget)
            item_idx += 1

        # Brick execution
        if exec != "":
            item = QTableWidgetItem()
            item.setText(BRICK_EXEC)
            self.table.setHorizontalHeaderItem(item_idx, item)
            widget = QWidget()
            v_layout = QVBoxLayout()
            v_layout.setAlignment(QtCore.Qt.AlignTop)
            label = QLabel(exec)
            v_layout.addWidget(label)
            widget.setLayout(v_layout)
            self.table.setCellWidget(0, item_idx, widget)
            item_idx += 1

            # Brick execution time
            item = QTableWidgetItem()
            item.setText(BRICK_EXEC_TIME)
            self.table.setHorizontalHeaderItem(item_idx, item)
            widget = QWidget()
            v_layout = QVBoxLayout()
            v_layout.setAlignment(QtCore.Qt.AlignTop)

            if exec_time is not None:
                label = QLabel(str(exec_time))

            v_layout.addWidget(label)
            widget.setLayout(v_layout)
            self.table.setCellWidget(0, item_idx, widget)
            item_idx += 1

        item_idx = self._updateio_table(inputs, item_idx)
        _ = self._updateio_table(outputs, item_idx)
        self.table.verticalHeader().setMinimumSectionSize(30)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()


class PopUpVisualizedTags(QWidget):
    """
    Is called when the user wants to update the tags that are visualized.

    .. Methods:
        - search_str: matches the searched pattern with the tags of the project
        - click_select_tag: puts the selected tags in the "selected tag" table
        - click_unselect_tag: removes the unselected tags from populse_mia
           "selected tag" table

    """

    # Signal that will be emitted at the end to tell that the preferences
    # have been changed
    signal_preferences_change = pyqtSignal()

    def __init__(self, project, visualized_tags):
        """Initialization.

        :param project: current project in the software
        :param visualized_tags: project's visualized tags before opening
          this widget

        """

        super().__init__()

        self.project = project
        self.visualized_tags = visualized_tags

        _translate = QtCore.QCoreApplication.translate

        # Two buttons to select or unselect tags
        self.push_button_select_tag = QtWidgets.QPushButton(self)
        self.push_button_select_tag.setObjectName("pushButton_select_tag")
        self.push_button_select_tag.clicked.connect(self.click_select_tag)

        self.push_button_unselect_tag = QtWidgets.QPushButton(self)
        self.push_button_unselect_tag.setObjectName("pushButton_unselect_tag")
        self.push_button_unselect_tag.clicked.connect(self.click_unselect_tag)

        self.push_button_select_tag.setText(_translate("main_window", "-->"))
        self.push_button_unselect_tag.setText(_translate("main_window", "<--"))

        vbox_tag_buttons = QVBoxLayout()
        vbox_tag_buttons.addWidget(self.push_button_select_tag)
        vbox_tag_buttons.addWidget(self.push_button_unselect_tag)

        # The "Tag list" label
        self.label_tag_list = QtWidgets.QLabel(self)
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.label_tag_list.setText(
            _translate("main_window", "Available tags:")
        )

        # The search bar to search in the list of tags
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.search_str)

        # The list of tags
        self.list_widget_tags = QtWidgets.QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        (
            self.list_widget_tags.setSelectionMode(
                QtWidgets.QAbstractItemView.MultiSelection
            )
        )

        hbox_top_left = QHBoxLayout()
        hbox_top_left.addWidget(self.label_tag_list)
        hbox_top_left.addWidget(self.search_bar)

        vbox_top_left = QVBoxLayout()
        vbox_top_left.addLayout(hbox_top_left)
        vbox_top_left.addWidget(self.list_widget_tags)

        # List of the tags selected by the user
        self.label_visualized_tags = QtWidgets.QLabel(self)
        self.label_visualized_tags.setTextFormat(QtCore.Qt.AutoText)
        self.label_visualized_tags.setObjectName("label_visualized_tags")
        self.label_visualized_tags.setText("Visualized tags:")

        self.list_widget_selected_tags = QtWidgets.QListWidget(self)
        (
            self.list_widget_selected_tags.setObjectName(
                "listWidget_visualized_tags"
            )
        )
        (
            self.list_widget_selected_tags.setSelectionMode(
                QtWidgets.QAbstractItemView.MultiSelection
            )
        )

        v_box_top_right = QVBoxLayout()
        v_box_top_right.addWidget(self.label_visualized_tags)
        v_box_top_right.addWidget(self.list_widget_selected_tags)

        hbox_tags = QHBoxLayout()
        hbox_tags.addLayout(vbox_top_left)
        hbox_tags.addLayout(vbox_tag_buttons)
        hbox_tags.addLayout(v_box_top_right)

        self.setLayout(hbox_tags)

        self.left_tags = []  # List that will keep track on
        # the tags on the left (invisible tags)

        with self.project.database.data() as database_data:

            for tag in database_data.get_field_names(COLLECTION_CURRENT):

                if (
                    tag != TAG_CHECKSUM
                    and tag != TAG_FILENAME
                    and tag != TAG_HISTORY
                ):
                    item = QtWidgets.QListWidgetItem()

                    if tag not in self.visualized_tags:
                        # Tag not visible: left side
                        self.list_widget_tags.addItem(item)
                        self.left_tags.append(tag)

                    else:
                        # Tag visible: right side
                        self.list_widget_selected_tags.addItem(item)

                    item.setText(tag)

        self.list_widget_tags.sortItems()

    def search_str(self, str_search):
        """Matches the searched pattern with the tags of the project.

        :param str_search: string pattern to search

        """

        return_list = []
        if str_search != "":
            for tag in self.left_tags:
                if str_search.upper() in tag.upper():
                    return_list.append(tag)
        else:
            for tag in self.left_tags:
                return_list.append(tag)

        # Selection updated
        self.list_widget_tags.clear()
        for tag_name in return_list:
            item = QtWidgets.QListWidgetItem()
            self.list_widget_tags.addItem(item)
            item.setText(tag_name)
        self.list_widget_tags.sortItems()

    def click_select_tag(self):
        """Puts the selected tags in the "selected tag" table."""

        rows = sorted(
            [index.row() for index in self.list_widget_tags.selectedIndexes()],
            reverse=True,
        )

        for row in rows:
            # assuming the other listWidget is called listWidget_2
            self.left_tags.remove(self.list_widget_tags.item(row).text())
            (
                self.list_widget_selected_tags.addItem(
                    self.list_widget_tags.takeItem(row)
                )
            )

    def click_unselect_tag(self):
        """Removes the unselected tags from populse_mia table."""

        rows = sorted(
            [
                index.row()
                for index in self.list_widget_selected_tags.selectedIndexes()
            ],
            reverse=True,
        )

        for row in rows:
            (
                self.left_tags.append(
                    self.list_widget_selected_tags.item(row).text()
                )
            )
            (
                self.list_widget_tags.addItem(
                    self.list_widget_selected_tags.takeItem(row)
                )
            )

        self.list_widget_tags.sortItems()


class QLabel_clickable(QLabel):
    """Custom class to click on a QLabel"""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, ev):
        """Blabla"""

        self.clicked.emit()
