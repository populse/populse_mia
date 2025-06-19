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
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
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

    clicked = QtCore.pyqtSignal()

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
        self.table = QTableWidget()
        self.table.setRowCount(1)
        value = self.parent.text()

        if value:

            try:
                list_value = ast.literal_eval(value)

                if isinstance(list_value, list):
                    # If the previous value was already a list, we fill it
                    self.table.setColumnCount(len(list_value))

                    for i, val in enumerate(list_value):
                        self.table.setItem(0, i, QTableWidgetItem(str(val)))

                else:
                    self.default_init_table()

            except Exception:
                self.default_init_table()

        else:
            self.default_init_table()

        self.resize_table()
        # Ok button
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.update_default_value)
        # Cancel button
        cancel_button = QPushButton("Cancel")
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
        self.table.setItem(0, self.table.columnCount() - 1, QTableWidgetItem())
        self.resize_table()

    def default_init_table(self):
        """
        Initializes the table with a default value.

        If no previous value exists, the table is set up with a single empty
        column to allow user input.
        """
        # Table filled with a single element at the beginning if no value
        self.table.setColumnCount(1)
        self.table.setItem(0, 0, QTableWidgetItem())

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


class DefaultValueQLineEdit(QLineEdit):
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
                else [""]
            )
            path_type_list = (
                ast.literal_eval(self.type_line_edit.text())
                if self.type_line_edit.text()
                else [""]
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
            with self.project.database.data(write=True) as database_data:

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
    signal_add_tag = QtCore.pyqtSignal()

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
        self.push_button_ok = QPushButton(self)
        self.push_button_ok.setObjectName("push_button_ok")
        self.push_button_ok.setText(_translate("Add a tag", "OK"))
        # Tag name components
        self.label_tag_name = QLabel(
            _translate("Add a tag", "Tag name:"), self
        )
        self.label_tag_name.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_name.setObjectName("tag_name")
        self.text_edit_tag_name = QLineEdit(self)
        self.text_edit_tag_name.setObjectName("textEdit_tag_name")
        # Default value components
        self.label_default_value = QLabel(
            _translate("Add a tag", "Default value:"), self
        )
        self.label_default_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_default_value.setObjectName("default_value")
        self.text_edit_default_value = DefaultValueQLineEdit(self)
        self.text_edit_default_value.setObjectName("textEdit_default_value")
        # Default value for string type
        self.text_edit_default_value.setText("Undefined")
        # Description components
        self.label_description_value = QLabel(
            _translate("Add a tag", "Description:"), self
        )
        self.label_description_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_description_value.setObjectName("description_value")
        self.text_edit_description_value = QLineEdit(self)
        self.text_edit_description_value.setObjectName(
            "textEdit_description_value"
        )
        # Unit components
        self.label_unit_value = QLabel(_translate("Add a tag", "Unit:"), self)
        self.label_unit_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_unit_value.setObjectName("unit_value")
        self.combo_box_unit = QComboBox(self)
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
        self.label_type = QLabel(_translate("Add a tag", "Tag type:"), self)
        self.label_type.setTextFormat(QtCore.Qt.AutoText)
        self.label_type.setObjectName("type")
        self.combo_box_type = QComboBox(self)
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

            if self.type is not FIELD_TYPE_STRING:
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
    signal_clone_tag = QtCore.pyqtSignal()

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
            item = QListWidgetItem(_translate("Dialog", tag))
            self.list_widget_tags.addItem(item)

        self.list_widget_tags.sortItems()

    def _setup_ui(self):
        """Set up the dialog UI elements."""
        _translate = QtCore.QCoreApplication.translate
        # New tag name components
        self.label_new_tag_name = QLabel(
            _translate("Clone a tag", "New tag name:"), self
        )
        self.label_new_tag_name.setTextFormat(QtCore.Qt.AutoText)
        self.label_new_tag_name.setObjectName("label_new_tag_name")
        self.line_edit_new_tag_name = QLineEdit(self)
        self.line_edit_new_tag_name.setObjectName("lineEdit_new_tag_name")
        # OK button
        self.push_button_ok = QPushButton(
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
        self.label_tag_list = QLabel(
            _translate("Clone a tag", "Available tags:"), self
        )
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.search_bar = QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        # Top row layout
        hbox_top = QHBoxLayout()
        hbox_top.addWidget(self.label_tag_list)
        hbox_top.addStretch(1)
        hbox_top.addWidget(self.search_bar)
        # Tag list widget
        self.list_widget_tags = QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        self.list_widget_tags.setSelectionMode(
            QAbstractItemView.SingleSelection
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
                QListWidgetItem(_translate("Dialog", tag_name))
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

    save_as_signal = QtCore.pyqtSignal()
    do_not_save_signal = QtCore.pyqtSignal()
    cancel_signal = QtCore.pyqtSignal()

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

        Return (bool): True if the editor can be closed, False otherwise.
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
        self.project_path = config.get_projects_save_path()
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
    """
    Dialog for selecting a previously saved filter.

    :Methods:
        - cancel_clicked: Closes the pop-up.
        - ok_clicked: Handles actions when the "OK" button is clicked.
        - search_str: Filters the list based on the search input.
    """

    def __init__(self, project):
        """
        Initializes the pop-up dialog.

        :param project (object): The current project containing saved filters
        """
        super().__init__()
        self.project = project
        self.setModal(True)
        _translate = QtCore.QCoreApplication.translate
        # Label for the filter list
        self.label_filter_list = QLabel(
            _translate("main_window", "Available filters:"), self
        )
        self.label_filter_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_filter_list.setObjectName("label_filter_list")
        # Search bar for filtering the list
        self.search_bar = QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.search_str)
        # List widget for displaying filters
        self.list_widget_filters = QListWidget(self)
        self.list_widget_filters.setObjectName("listWidget_tags")
        self.list_widget_filters.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        # OK and Cancel buttons
        self.push_button_ok = QPushButton("OK", self)
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)
        self.push_button_cancel = QPushButton("Cancel", self)
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.cancel_clicked)
        # Layout setup
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
        """Closes the pop-up dialog."""
        self.close()

    def ok_clicked(self):
        """
        Handles actions when the "OK" button is clicked.

        This method should be overridden in subclasses to implement
        specific behavior.
        """
        pass

    def search_str(self, search_text):
        """
        Filters the list of saved filters based on the search input.

        :param search_text (str): The text pattern to search for

        """
        search_text = search_text.strip().upper()

        if search_text:
            matching_filters = [
                f.name
                for f in self.project.filters
                if search_text in f.name.upper()
            ]

        else:
            matching_filters = [f.name for f in self.project.filters]

        for idx in range(self.list_widget_filters.count()):
            item = self.list_widget_filters.item(idx)
            item.setHidden(item.text() not in matching_filters)


class PopUpInformation(QWidget):
    """
    Popup window displaying the current project's information.
    """

    # Signal emitted when project preferences change
    signal_preferences_change = QtCore.pyqtSignal()

    def __init__(self, project):
        """
        Initializes the popup window with project details.

        :param project (Project): The current project instance
        """
        super().__init__()
        # UI Elements
        name_label = QLabel("Name: ")
        self.name_value = QLineEdit(project.getName())
        folder_label = QLabel(f"Root folder: {project.folder}")
        date_label = QLabel(f"Date of creation: {project.getDate()}")
        # Layout Setup
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
    """
    Dialog for selecting tag inheritance between input and output plugs.

    This dialog allows users to select which input plug should pass its tags
    to a specific output plug, or to choose to ignore tag inheritance
    altogether.

    :Methods:
        - _setup_buttons: Set up action buttons for the dialog
        - _setup_radio_buttons: Set up radio buttons for each input option
        - ok_clicked: Event when ok button is clicked
        - okall_clicked: Event when Ok all button is clicked
        - on_clicked: Event when radiobutton is clicked
        - ignoreall_clicked: Event when ignore all plugs button is clicked
        - ignore_clicked: Event when ignore button is clicked
        - ignore_node_clicked: Event when ignore all nodes button is clicked
    """

    def __init__(self, values, node_name, plug_name, iterate):
        """
        Initialize the inheritance selection dialog.

        :param values (dict): Dict mapping input names (keys) to their
                              paths (values)
        :param node_name (str): Name of the current node
        :param plug_name (str): Name of the current output plug
        :param iterate (bool): Boolean indicating if the choice applies
                               to iterations
        """
        super().__init__()
        self.setModal(True)
        self.setObjectName("Dialog")
        self.setWindowTitle(f"Plug inherited in {node_name}")
        # Initialize state flags
        self.ignore = False
        self.all = False
        self.everything = False
        # Create the main layout
        v_box_values = QVBoxLayout()
        label = (
            f"In the node <b><i>{node_name}</i></b>, from which input plug, "
            f"the output plug <b><i>{plug_name}</i></b> should inherit "
            f"the tags?:"
        )
        v_box_values.addWidget(QLabel(label))
        # Add radio buttons for each input option
        self._setup_radio_buttons(values, v_box_values)
        # Add button row
        h_box_buttons = QHBoxLayout()
        self._setup_buttons(node_name, plug_name, h_box_buttons)
        v_box_values.addLayout(h_box_buttons)
        # Add ignore node button
        self.push_button_ignore_node = QPushButton(
            "Ignore for all nodes in the pipeline", self
        )
        self.push_button_ignore_node.clicked.connect(self.ignore_node_clicked)
        self.push_button_ignore_node.setToolTip(
            "No tags will be inherited for the whole pipeline."
        )
        v_box_values.addWidget(self.push_button_ignore_node)

        # Add iteration notice if needed
        if iterate:
            label = "<i>These choices will be valid for each iteration.</i>"
            v_box_values.addWidget(QLabel(label))

        self.setLayout(v_box_values)

    def _setup_buttons(self, node_name, plug_name, layout):
        """Set up action buttons for the dialog.

        :param  node_name: Name of the current node
        :param  plug_name: Name of the current output plug
        :param  layout: Layout to add the buttons to
        """
        # OK button
        self.push_button_ok = QPushButton("OK", self)
        self.push_button_ok.clicked.connect(self.ok_clicked)
        self.push_button_ok.setToolTip(
            f"<i>{plug_name}</i> will inherit tags from {self.key}."
        )
        layout.addWidget(self.push_button_ok)
        # Ignore button
        self.push_button_ignore = QPushButton("Ignore", self)
        self.push_button_ignore.clicked.connect(self.ignore_clicked)
        self.push_button_ignore.setToolTip(
            f"<i>{plug_name}</i> will not inherit any tags."
        )
        layout.addWidget(self.push_button_ignore)
        # OK all button
        self.push_button_okall = QPushButton("OK for all output plugs", self)
        self.push_button_okall.clicked.connect(self.okall_clicked)
        self.push_button_okall.setToolTip(
            f"All the output plugs from <i>{node_name}</i> "
            f"will inherit tags from {self.key}."
        )
        layout.addWidget(self.push_button_okall)
        # Ignore all button
        self.push_button_ignoreall = QPushButton(
            "Ignore for all output plugs", self
        )
        self.push_button_ignoreall.clicked.connect(self.ignoreall_clicked)
        self.push_button_ignoreall.setToolTip(
            f"All the output plugs from <i>{node_name}</i> will not "
            f"inherit any tags."
        )
        layout.addWidget(self.push_button_ignoreall)

    def _setup_radio_buttons(self, values, layout):
        """Set up radio buttons for each input option.

        :param values: Dict mapping input names to their paths
        :param layout: Layout to add the radio buttons to
        """
        first_button = True

        for key, value in values.items():
            radiobutton = QRadioButton(key, self)
            radiobutton.value = value
            radiobutton.key = key
            radiobutton.setChecked(first_button)

            if first_button:
                self.value = value
                self.key = key
                first_button = False

            radiobutton.toggled.connect(self.on_clicked)
            layout.addWidget(radiobutton)
            layout.addStretch(1)

    def ok_clicked(self):
        """
        Handle OK button click.

        Accepts the dialog with current selection applied to current plug.
        """
        self.accept()
        self.close()

    def okall_clicked(self):
        """
        Handle 'OK for all output plugs' button click.

        Accepts the dialog with current selection applied to all output
        plugs.
        """
        self.all = True
        self.accept()
        self.close()

    def on_clicked(self):
        """
        Handle radio button selection event.

        Updates the currently selected input value and key.
        """
        radiobutton = self.sender()
        self.value = radiobutton.value
        self.key = radiobutton.key

        # Update OK button tooltips with new selection
        self.push_button_ok.setToolTip(
            f"Output plug will inherit tags from {self.key}."
        )
        self.push_button_okall.setToolTip(
            f"All output plugs will inherit tags from {self.key}."
        )

    def ignoreall_clicked(self):
        """
        Handle 'Ignore for all output plugs' button click.

        Accepts the dialog with tag inheritance ignored for all output plugs.
        """
        self.ignore = True
        self.all = True
        self.accept()
        self.close()

    def ignore_clicked(self):
        """
        Handle Ignore button click.

        Accepts the dialog with tag inheritance ignored for current plug.
        """
        self.ignore = True
        self.accept()
        self.close()

    def ignore_node_clicked(self):
        """
        Handle 'Ignore for all nodes in the pipeline' button click.

        Accepts the dialog with tag inheritance ignored for the entire
        pipeline.
        """
        self.ignore = True
        self.all = True
        self.everything = True
        self.accept()
        self.close()


class PopUpMultipleSort(QDialog):
    """
    Dialog for sorting the data browser's table based on multiple tags.

    This dialog allows users to select multiple tags (columns) for sorting
    table data in either ascending or descending order. Users can dynamically
    add or remove sort criteria.

    .. Methods:
        - _setup_ui_elements: Create and configure all UI elements
        - add_tag: Adds a push button
        - fill_values: Fills the values list when a tag is added or removed
        - refresh_layout: Updates the layouts (especially when a tag push
                          button is added or removed)
        - remove_tag: Removes a push buttons and makes the changes in the
                      list of values
        - select_tag: Calls a pop-up to choose a tag
        - sort_scans: Collects the information and send them to the data
                      browser
    """

    def __init__(self, project, table_data_browser):
        """
        Initialize the multiple sort dialog.

        :param project: Current project in the software
        :param table_data_browser: Data browser's table to be sorted

        """
        super().__init__()
        self.project = project
        self.table_data_browser = table_data_browser
        self.setModal(True)
        self.setWindowTitle("Multiple Sort")
        # Initialize data structures
        # Contains unique values for each selected tag
        self.values_list = [[], []]
        # Will hold the final list of tags for sorting
        self.list_tags = []
        # Buttons for tag selection
        self.push_buttons = []
        # Create UI elements
        self._setup_ui_elements()
        # Create and set layout
        self.v_box_final = QVBoxLayout()
        self.setLayout(self.v_box_final)
        self.refresh_layout()

    def _setup_ui_elements(self):
        """Create and configure all UI elements."""
        # Tag selection section
        self.label_tags = QLabel("Tags: ")
        # Create initial tag buttons
        push_button_tag_1 = QPushButton("Tag n°1")
        push_button_tag_1.clicked.connect(lambda: self.select_tag(0))
        push_button_tag_2 = QPushButton("Tag n°2")
        push_button_tag_2.clicked.connect(lambda: self.select_tag(1))
        self.push_buttons = [push_button_tag_1, push_button_tag_2]
        # Add/remove tag controls
        sources_images_dir = Config().getSourceImageDir()
        # Remove tag button
        self.remove_tag_label = ClickableLabel()
        remove_tag_picture = QtGui.QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "red_minus.png"))
        ).scaledToHeight(20)
        self.remove_tag_label.setPixmap(remove_tag_picture)
        self.remove_tag_label.clicked.connect(self.remove_tag)
        # Add tag button
        self.add_tag_label = ClickableLabel()
        self.add_tag_label.setObjectName("plus")
        add_tag_picture = QtGui.QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "green_plus.png"))
        ).scaledToHeight(15)
        self.add_tag_label.setPixmap(add_tag_picture)
        self.add_tag_label.clicked.connect(self.add_tag)
        # Sort order selection
        self.combo_box = QComboBox()
        self.combo_box.addItems(["Ascending", "Descending"])
        # Sort button
        self.push_button_sort = QPushButton("Sort Scans")
        self.push_button_sort.clicked.connect(self.sort_scans)

    def add_tag(self):
        """Add a new tag button to the sort criteria."""
        button_index = len(self.push_buttons)
        push_button = QPushButton(f"Tag n°{button_index + 1}")
        push_button.clicked.connect(lambda: self.select_tag(button_index - 1))
        self.push_buttons.insert(button_index, push_button)
        self.refresh_layout()

    def fill_values(self, idx):
        """
        Collect unique values for the selected tag.

        :param idx: Index of the tag button in the push_buttons list

        """
        tag_name = self.push_buttons[idx].text()

        # Ensure values_list has enough slots
        while len(self.values_list) <= idx:
            self.values_list.append([])

        # Clear existing values for this tag
        self.values_list[idx] = []

        with self.project.database.data() as database_data:

            for scan in database_data.get_document_names(COLLECTION_CURRENT):
                current_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan,
                    field=tag_name,
                )

                if current_value not in self.values_list[idx]:
                    self.values_list[idx].append(current_value)

    def refresh_layout(self):
        """
        Update the dialog layout to reflect current tag buttons.
        """
        self.h_box_top = QHBoxLayout()
        self.h_box_top.setSpacing(10)
        self.h_box_top.addWidget(self.label_tags)

        # Add all tag buttons
        for tag_button in self.push_buttons:
            self.h_box_top.addWidget(tag_button)

        # Add control buttons
        self.h_box_top.addWidget(self.add_tag_label)
        self.h_box_top.addWidget(self.remove_tag_label)
        self.h_box_top.addWidget(self.combo_box)
        self.h_box_top.addWidget(self.push_button_sort)
        self.h_box_top.addStretch(1)

        # Clear the previous layout if it exists
        if self.v_box_final.count() > 0:
            # Remove the previous h_box_top
            item = self.v_box_final.takeAt(0)

            if item.layout():

                while item.layout().count():
                    item.layout().takeAt(0)

        self.v_box_final.addLayout(self.h_box_top)

    def remove_tag(self):
        """
        Remove the last tag button from the sort criteria.
        """

        if not self.push_buttons:
            return

        # Remove the last button
        push_button = self.push_buttons.pop()
        push_button.deleteLater()
        push_button = None

        # Remove corresponding values
        if self.values_list:
            self.values_list.pop()

        self.refresh_layout()

    def select_tag(self, idx):
        """
        Open a pop-up dialog to choose a tag for the specified button.

        :param idx: Index of the button in the push_buttons list
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
        """Collect sorting parameters and send them to the data browser."""
        self.order = self.combo_box.itemText(self.combo_box.currentIndex())
        # Clear previous tag list
        self.list_tags = []

        # Collect valid tag names
        with self.project.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)

        for push_button in self.push_buttons:
            tag_name = push_button.text()

            if tag_name in field_names:
                self.list_tags.append(tag_name)

        # Close dialog and trigger sorting
        self.accept()
        self.table_data_browser.multiple_sort_infos(self.list_tags, self.order)


class PopUpNewProject(QFileDialog):
    """
    Dialog for creating a new project.

    This dialog is displayed when the user wants to create a new project.
    It manages file selection and handles the creation process.

    .. Method:
        - get_filename: Sets the widget's attributes depending on the
          selected file name

    .. Signals:
        - signal_create_project: Emitted when a project has been
                                 successfully created

    """

    # Signal emitted when project creation is successful
    signal_create_project = QtCore.pyqtSignal()

    def __init__(self):
        """Initialize the new project dialog with appropriate settings."""

        # Import here to prevent circular import issues
        from populse_mia.utils import set_projects_directory_as_default

        super().__init__()
        self.setLabelText(QFileDialog.Accept, "Create")
        self.setAcceptMode(QFileDialog.AcceptSave)
        # Set the projects directory as default
        set_projects_directory_as_default(self)

    def get_filename(self, file_name_tuple):
        """
        Process the selected filename and set up project attributes.

        :param file_name_tuple (tuple): Tuple containing the selected
                                        filename(s), obtained from the
                                        selectedFiles method

        Note:
            If the file already exists, displays an error message.
            Otherwise, closes the dialog and emits signal_create_project.
        """
        # Import here to prevent circular import issues
        from populse_mia.utils import message_already_exists

        # Handle the case where file_name_tuple might be empty
        if not file_name_tuple:
            return ""

        file_name = file_name_tuple[0]

        if not file_name:
            return ""

        entire_path = os.path.abspath(file_name)
        self.path, self.name = os.path.split(entire_path)
        self.relative_path = os.path.relpath(file_name)
        self.relative_subpath = os.path.relpath(self.path)

        # Check if project already exists
        if os.path.exists(self.relative_path):
            message_already_exists()

        else:
            self.close()
            # Emit signal to notify that project has been created
            self.signal_create_project.emit()

        return file_name


class PopUpOpenProject(QFileDialog):
    """
    Dialog for opening an existing MIA project.

    This dialog allows users to select an existing project directory from
    the filesystem. It uses the default projects directory as the starting
    location and emits a signal when a valid project is selected.

    .. Method:
        - get_filename: Sets the widget's attributes depending on the
                        selected file name

    .. Signals:
        - signal_create_project: Signal emitted when a valid project is
                                 selected
    """

    # Signal emitted when a valid project is selected
    signal_create_project = QtCore.pyqtSignal()

    def __init__(self):
        # Import here to prevent circular imports
        from populse_mia.utils import set_projects_directory_as_default

        super().__init__()

        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setFileMode(QFileDialog.Directory)
        # Set the projects directory as default location
        set_projects_directory_as_default(self)

    def get_filename(self, file_name_tuple):
        """
        Process the selected directory and emit signal if valid.

        Sets the path, name, and relative_path attributes based on the
        selected directory. If the directory exists, emits
        signal_create_project.

        :param file_name_tuple (tuple): Tuple containing selected directory
                                        path(s). Typically obtained from
                                        selectedFiles() method.
        """
        # Import here to prevent circular imports
        from populse_mia.utils import message_already_exists

        if not file_name_tuple:
            return

        file_name = file_name_tuple[0]

        if not file_name:
            return

        entire_path = os.path.abspath(file_name)
        self.path, self.name = os.path.split(entire_path)
        self.relative_path = os.path.relpath(file_name)

        # Check if directory exists and emit signal
        if os.path.exists(entire_path):
            self.close()
            self.signal_create_project.emit()

        else:
            message_already_exists()


class PopUpPreferences(QDialog):
    """
    Dialog for changing software preferences.

    This class manages the preferences dialog for the software, allowing users
    to configure various settings related to tools, projects, and appearance.

    .. Methods:
        - admin_mode_switch: Called when the admin mode checkbox
                             is clicked
        - browse_afni: Called when afni browse button is clicked
        - browse_ants: Called when ants browse button is clicked
        - browse_freesurfer: Browse for the FreeSurfer env file
        - browse_fsl: Called when fsl browse button is clicked
        - browse_matlab: Called when matlab browse button is clicked
        - browse_matlab_standalone: Called when matlab browse button is clicked
        - browse_mri_conv_path: Called when "MRIManager.jar" browse
                                button is clicked
        - browse_mrtrix: Called when mrtrix browse button is clicked
        - browse_projects_save_path: Called when "Projects folder" browse
                                     button is clicked
        - browse_resources_path: Called when "resources" browse button is
                                 clicked
        - browse_spm: Called when spm browse button is clicked
        - browse_spm_standalone: Called when spm standalone browse button
                                 is clicked
        - change_admin_psswd: Method to change the admin password
        - control_checkbox_toggled: Check before changing controller version
        - create_afni_group: Create the AFNI group box

        - create_ants_group: Create the ANTS group box
        - create_appearance_tab: Create the 'Appearance' tab
        - create_capsul_group: Create the CAPSUL group box
        - create_freesurfer_group: Create the FreeSurfer group box
        - create_fsl_group: Create the FSL group box
        - create_global_preferences: Create the global preferences group box
        - create_horizontal_box: Create a horizontal box layout with the
                                 given widgets
        - create_matlab_group: Create the Matlab group box
        - create_mrtrix_group: Create the mrtrix group box
        - create_pipeline_tab: Create the 'Pipeline' tab
        - create_projects_preferences: Create the projects preferences group
                                       box
        - create_populse_preferences: Create the Populse third party
                                      preferences group box
        - create_resources_preferences: Create the external resources
                                        preferences group box
        - create_spm_group: Create the SPM group box
        - create_tools_tab: Create the 'Tools' tab
        - edit_capsul_config: Capsul engine edition
        - edit_config_file: Create a window to view, edit the mia
                            configuration file
        - findChar: Highlights characters in red when using the Find button
                    when editing configuration
        - load_config: Load the configuration settings
        - ok_clicked: Saves the modifications to the config file and apply
                      them
        - save_minimal_config: Save minimal configuration for CAPSUL config
                               sync purposes
        - save_full_config: Save the full configuration and validate settings
        - setup_ui: Set up the user interface components
        - show_error_message: Show an error message dialog
        - show_warning_message: Show a warning message dialog
        - update_gui_from_capsul_config: Update the GUI based on the CAPSUL
                                         configuration
        - use_afni_changed: Called when the use_afni checkbox is changed
        - use_ants_changed: Called when the use_ants checkbox is changed
        - use_current_mainwindow_size: Use the current main window size
        - use_freesurfer_changed: Handle the use_freesurfer checkbox change
                                  event
        - use_fsl_changed: Called when the use_fsl checkbox is changed
        - use_matlab_changed: Called when the use_matlab checkbox is changed
        - use_matlab_standalone_changed: Called when the use_matlab_standalone
                                         checkbox is changed
        - use_mrtrix_changed: Called when the use_mrtrix checkbox is changed
        - use_spm_changed: Called when the use_spm checkbox is changed
        - use_spm_standalone_changed: Called when the use_spm_standalone
                                      checkbox is changed
        - validate_and_save: Validate and save the preferences
        - validate_matlab_path: Validate the Matlab path
        - validate_matlab_standalone_path: Validate the Matlab standalone path
        - validate_paths: Validate the paths and settings
        - validate_spm_path: Validate the SPM path
        - validate_spm_standalone_path: Validate the SPM standalone path
        - validate_tool_path: Validate the tool path
        - wrong_path: Show a wrong path message


    .. Signals:
        - signal_preferences_change: Signal emitted when the preferences are
                                     successfully validated and saved
        - use_clinical_mode_signal: Signal emitted when the clinical mode is
                                    enabled
        - not_use_clinical_mode_signal: Signal emitted when the clinical mode
                                        is disabled
    """

    signal_preferences_change = QtCore.pyqtSignal()
    use_clinical_mode_signal = QtCore.pyqtSignal()
    not_use_clinical_mode_signal = QtCore.pyqtSignal()

    def __init__(self, main_window):
        """
        Initialize the preferences dialog.

        :param main_window: The main window object of the software
        """
        super().__init__()
        self.setModal(True)
        self.main_window = main_window
        self.clicked = 0
        self.salt = "P0pulseM1@"
        self.setup_ui()
        self.load_config()
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
        # Connects the change of state event for a checkbox
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

    def admin_mode_switch(self):
        """Handle the admin mode checkbox click event."""
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

    def browse_afni(self):
        """Browse for the AFNI directory."""
        fname = QFileDialog.getExistingDirectory(
            self, "Choose AFNI directory", os.path.expanduser("~")
        )

        if fname:
            self.afni_choice.setText(fname)

    def browse_ants(self):
        """Browse for the ANTS directory."""
        fname = QFileDialog.getExistingDirectory(
            self, "Choose ANTS directory", os.path.expanduser("~")
        )

        if fname:
            self.ants_choice.setText(fname)

    def browse_freesurfer(self):
        """Browse for the FreeSurfer env file."""
        fname = QFileDialog.getOpenFileName(
            self, "Choose freesurfer env file", os.path.expanduser("~")
        )[0]

        if fname:
            self.freesurfer_choice.setText(fname)

    def browse_fsl(self):
        """Browse for the FSL config file."""
        fname = QFileDialog.getOpenFileName(
            self, "Choose FSL config file", os.path.expanduser("~")
        )[0]

        if fname:
            self.fsl_choice.setText(fname)

    def browse_matlab(self):
        """Browse for the Matlab file."""
        fname = QFileDialog.getOpenFileName(
            self, "Choose Matlab file", os.path.expanduser("~")
        )[0]

        if fname:
            self.matlab_choice.setText(fname)

    def browse_matlab_standalone(self):
        """Browse for the Matlab standalone directory."""
        fname = QFileDialog.getExistingDirectory(
            self, "Choose MCR directory", os.path.expanduser("~")
        )

        if fname:
            self.matlab_standalone_choice.setText(fname)

    def browse_mri_conv_path(self):
        """Browse for the MRIFileManager.jar file."""
        fname = QFileDialog.getOpenFileName(
            self,
            "Select the location of the MRIManager.jar file",
            os.path.expanduser("~"),
        )[0]

        if fname:
            self.mri_conv_path_line_edit.setText(fname)

    def browse_mrtrix(self):
        """Browse for the mrtrix directory."""
        fname = QFileDialog.getExistingDirectory(
            self, "Choose mrtrix directory", os.path.expanduser("~")
        )

        if fname:
            self.mrtrix_choice.setText(fname)

    def browse_projects_save_path(self):
        """Browse for the projects folder."""
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
        """Browse for the resources folder."""
        fname = QFileDialog.getExistingDirectory(
            self,
            "Select the location of the external resources folder",
            os.path.expanduser("~"),
        )

        if fname:
            self.resources_path_line_edit.setText(fname)

    def browse_spm(self):
        """Browse for the SPM directory."""
        fname = QFileDialog.getExistingDirectory(
            self, "Choose SPM directory", os.path.expanduser("~")
        )

        if fname:
            self.spm_choice.setText(fname)

    def browse_spm_standalone(self):
        """Browse for the SPM standalone directory."""
        fname = QFileDialog.getExistingDirectory(
            self, "Choose SPM standalone directory", os.path.expanduser("~")
        )

        if fname:
            self.spm_standalone_choice.setText(fname)

    def change_admin_psswd(self, status):
        """
        Open a dialog to change the admin password with validation checks.

        :param status (str): Initial status message to display in the dialog.
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

    def control_checkbox_toggled(self):
        """Check if the user really wants to change the controller version."""
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
                f"{'V2' if config.isControlV1() else 'V1'} is already "
                f"planned for next start-up. Would you like to cancel "
                f"this change?"
            )

        return_value = self.msg.exec()

        if return_value == QMessageBox.Yes:
            self.control_checkbox_changed = not self.control_checkbox_changed
            self.main_window.set_controller_version()

        QApplication.restoreOverrideCursor()

    def create_afni_group(self):
        """Create the AFNI group box."""
        self.use_afni_label = QLabel("Use AFNI")
        self.use_afni_checkbox = QCheckBox("", self)
        self.afni_label = QLabel("AFNI path (e.g. dir_containing_abin/abin):")
        self.afni_choice = QLineEdit()
        self.afni_browse = QPushButton("Browse")
        self.afni_browse.clicked.connect(self.browse_afni)
        v_box_afni_path = QVBoxLayout()
        v_box_afni_path.addWidget(self.afni_label)
        v_box_afni_path.addLayout(
            self.create_horizontal_box(
                self.afni_choice, self.afni_browse, add_stretch=False
            )
        )
        v_box_afni = QVBoxLayout()
        v_box_afni.addLayout(
            self.create_horizontal_box(
                self.use_afni_checkbox, self.use_afni_label
            )
        )
        v_box_afni.addLayout(v_box_afni_path)
        self.groupbox_afni.setLayout(v_box_afni)

    def create_ants_group(self):
        """Create the ANTS group box."""
        self.use_ants_label = QLabel("Use ANTS")
        self.use_ants_checkbox = QCheckBox("", self)
        self.ants_label = QLabel("ANTS path (e.g. ANTs_dir/bin):")
        self.ants_choice = QLineEdit()
        self.ants_browse = QPushButton("Browse")
        self.ants_browse.clicked.connect(self.browse_ants)
        v_box_ants_path = QVBoxLayout()
        v_box_ants_path.addWidget(self.ants_label)
        v_box_ants_path.addLayout(
            self.create_horizontal_box(
                self.ants_choice, self.ants_browse, add_stretch=False
            )
        )
        v_box_ants = QVBoxLayout()
        v_box_ants.addLayout(
            self.create_horizontal_box(
                self.use_ants_checkbox, self.use_ants_label
            )
        )
        v_box_ants.addLayout(v_box_ants_path)
        self.groupbox_ants.setLayout(v_box_ants)

    def create_appearance_tab(self, _translate):
        """
        Create and configure the 'Appearance' tab with color and display
        settings.

        :param _translate (callable): Function used to translate UI text
                                      (translate method of QCoreApplication
                                      in the Qt framework.)
        """
        self.tab_appearance = QWidget()
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
        self.label_text_color = QLabel("Text color")
        self.text_color_combo = QComboBox(self)
        self.background_color_combo.addItem("")
        self.text_color_combo.addItem("")

        for color in colors:
            self.background_color_combo.addItem(color)
            self.text_color_combo.addItem(color)

        self.fullscreen_cbox = QCheckBox("Use full screen")
        self.mainwindow_size_x_spinbox = QSpinBox()
        self.mainwindow_size_x_spinbox.setMaximum(
            QApplication.instance().desktop().width()
        )
        self.mainwindow_size_y_spinbox = QSpinBox()
        self.mainwindow_size_y_spinbox.setMaximum(
            QApplication.instance().desktop().height()
        )
        self.mainwindow_size_button = QPushButton("use current size")
        self.mainwindow_size_button.clicked.connect(
            self.use_current_mainwindow_size
        )
        mainwindow_size_lay = QHBoxLayout()
        mainwindow_size_lay.addWidget(QLabel("Main window size"))
        mainwindow_size_lay.addWidget(self.mainwindow_size_x_spinbox)
        mainwindow_size_lay.addWidget(QLabel(" x "))
        mainwindow_size_lay.addWidget(self.mainwindow_size_y_spinbox)
        mainwindow_size_lay.addWidget(self.mainwindow_size_button)
        self.appearance_layout.addWidget(self.label_background_color)
        self.appearance_layout.addWidget(self.background_color_combo)
        self.appearance_layout.addWidget(self.label_text_color)
        self.appearance_layout.addWidget(self.text_color_combo)
        self.appearance_layout.addWidget(self.fullscreen_cbox)
        self.appearance_layout.addLayout(mainwindow_size_lay)
        self.appearance_layout.addStretch(1)
        self.tab_appearance.setLayout(self.appearance_layout)

    def create_capsul_group(self, groupbox_capsul):
        """
        Create and configure the CAPSUL group box with a configuration
        button.

        :param groupbox_capsul (QGroupBox): The group box to be configured
                                            for CAPSUL settings.
        """
        capsul_config_button = QPushButton(
            "Edit CAPSUL config", default=False, autoDefault=False
        )
        capsul_config_button.clicked.connect(self.edit_capsul_config)
        h_box_capsul = QHBoxLayout()
        h_box_capsul.addWidget(capsul_config_button)
        h_box_capsul.addStretch(1)
        v_box_capsul = QVBoxLayout()
        v_box_capsul.addLayout(h_box_capsul)
        groupbox_capsul.setLayout(v_box_capsul)

    def create_freesurfer_group(self):
        """Create the FreeSurfer group box."""
        self.use_freesurfer_label = QLabel("Use FreeSurfer")
        self.use_freesurfer_checkbox = QCheckBox("", self)
        self.freesurfer_label = QLabel(
            "FreeSurfer path (e.g. FreeSurfer_dir/FreeSurferEnv.sh):"
        )
        self.freesurfer_choice = QLineEdit()
        self.freesurfer_browse = QPushButton("Browse")
        self.freesurfer_browse.clicked.connect(self.browse_freesurfer)
        v_box_freesurfer_path = QVBoxLayout()
        v_box_freesurfer_path.addWidget(self.freesurfer_label)
        v_box_freesurfer_path.addLayout(
            self.create_horizontal_box(
                self.freesurfer_choice,
                self.freesurfer_browse,
                add_stretch=False,
            )
        )
        v_box_freesurfer = QVBoxLayout()
        v_box_freesurfer.addLayout(
            self.create_horizontal_box(
                self.use_freesurfer_checkbox, self.use_freesurfer_label
            )
        )
        v_box_freesurfer.addLayout(v_box_freesurfer_path)
        self.groupbox_freesurfer.setLayout(v_box_freesurfer)

    def create_fsl_group(self):
        """Create the FSL group box."""
        self.use_fsl_label = QLabel("Use FSL")
        self.use_fsl_checkbox = QCheckBox("", self)
        self.fsl_label = QLabel(
            "FSL config file (e.g., fsl_dir/etc/fslconf/fsl.sh):"
        )
        self.fsl_choice = QLineEdit()
        self.fsl_browse = QPushButton("Browse")
        self.fsl_browse.clicked.connect(self.browse_fsl)
        v_box_fsl_path = QVBoxLayout()
        v_box_fsl_path.addWidget(self.fsl_label)
        v_box_fsl_path.addLayout(
            self.create_horizontal_box(
                self.fsl_choice, self.fsl_browse, add_stretch=False
            )
        )
        v_box_fsl = QVBoxLayout()
        v_box_fsl.addLayout(
            self.create_horizontal_box(
                self.use_fsl_checkbox, self.use_fsl_label
            )
        )
        v_box_fsl.addLayout(v_box_fsl_path)
        self.groupbox_fsl.setLayout(v_box_fsl)

    def create_global_preferences(self):
        """Create the global preferences group box."""
        self.save_checkbox = QCheckBox("", self)
        self.save_label = QLabel("Auto save")
        self.clinical_mode_checkbox = QCheckBox("", self)
        self.clinical_mode_label = QLabel("Clinical mode")
        self.admin_mode_checkbox = QCheckBox("", self)
        self.admin_mode_checkbox.clicked.connect(self.admin_mode_switch)
        self.admin_mode_label = QLabel("Admin mode")
        self.change_psswd = QPushButton(
            "Change password", default=False, autoDefault=False
        )
        self.change_psswd.clicked.connect(partial(self.change_admin_psswd, ""))
        self.edit_config = QPushButton(
            "Edit config", default=False, autoDefault=False
        )
        self.edit_config.clicked.connect(self.edit_config_file)
        self.control_checkbox = QCheckBox("", self)
        self.control_label = QLabel("Version 1 controller")
        self.control_checkbox_changed = (
            self.main_window.get_controller_version()
        )
        self.control_checkbox.clicked.connect(self.control_checkbox_toggled)
        self.max_thumbnails_label = QLabel(
            "Number of thumbnails in Data Browser:"
        )
        self.max_thumbnails_box = QSpinBox()
        self.max_thumbnails_box.setMinimum(1)
        self.max_thumbnails_box.setMaximum(15)
        self.max_thumbnails_box.setSingleStep(1)
        self.radioView_checkbox = QCheckBox("", self)
        self.radioView_label = QLabel(
            "Radiological orientation in miniviewer (data browser)"
        )

        v_box_global = QVBoxLayout()
        v_box_global.addLayout(
            self.create_horizontal_box(self.save_checkbox, self.save_label)
        )
        v_box_global.addLayout(
            self.create_horizontal_box(
                self.clinical_mode_checkbox, self.clinical_mode_label
            )
        )
        v_box_global.addLayout(
            self.create_horizontal_box(
                self.admin_mode_checkbox, self.admin_mode_label
            )
        )
        v_box_global.addLayout(self.create_horizontal_box(self.change_psswd))
        v_box_global.addLayout(self.create_horizontal_box(self.edit_config))
        v_box_global.addLayout(
            self.create_horizontal_box(
                self.control_checkbox, self.control_label
            )
        )
        v_box_global.addWidget(self.max_thumbnails_label)
        v_box_global.addLayout(
            self.create_horizontal_box(self.max_thumbnails_box)
        )
        v_box_global.addLayout(
            self.create_horizontal_box(
                self.radioView_checkbox, self.radioView_label
            )
        )
        self.groupbox_global.setLayout(v_box_global)

    def create_horizontal_box(self, *widgets, add_stretch=True):
        """
        Create a horizontal box layout containing the specified widgets.

        :param widgets (tuple[QtWidgets.QWidget, ...]): The widgets to add
                                                        to the layout.
        :param add_stretch (bool): Whether to add stretch at the end to push
                                   the widgets to the left. Defaults to True.

        :return (QHBoxLayout): The created horizontal box layout.
        """
        h_box = QHBoxLayout()

        for widget in widgets:
            h_box.addWidget(widget)

        if add_stretch:
            h_box.addStretch(1)

        return h_box

    def create_matlab_group(self):
        """Create the Matlab group box."""
        self.use_matlab_label = QLabel("Use Matlab")
        self.use_matlab_checkbox = QCheckBox("", self)
        self.matlab_label = QLabel(
            "Matlab path (e.g., matlab_dir/bin/matlab):"
        )
        self.matlab_choice = QLineEdit()
        self.matlab_browse = QPushButton("Browse")
        self.matlab_browse.clicked.connect(self.browse_matlab)
        self.use_matlab_standalone_label = QLabel("Use Matlab standalone")
        self.use_matlab_standalone_checkbox = QCheckBox("", self)
        self.matlab_standalone_label = QLabel(
            "Matlab standalone path (e.g., MCR_dir/v95):"
        )
        self.matlab_standalone_choice = QLineEdit()
        self.matlab_standalone_browse = QPushButton("Browse")
        self.matlab_standalone_browse.clicked.connect(
            self.browse_matlab_standalone
        )
        v_box_matlab_path = QVBoxLayout()
        v_box_matlab_path.addWidget(self.matlab_label)
        v_box_matlab_path.addLayout(
            self.create_horizontal_box(
                self.matlab_choice, self.matlab_browse, add_stretch=False
            )
        )
        v_box_matlab_standalone_path = QVBoxLayout()
        v_box_matlab_standalone_path.addLayout(
            self.create_horizontal_box(
                self.use_matlab_standalone_checkbox,
                self.use_matlab_standalone_label,
            )
        )
        v_box_matlab_standalone_path.addWidget(self.matlab_standalone_label)
        v_box_matlab_standalone_path.addLayout(
            self.create_horizontal_box(
                self.matlab_standalone_choice,
                self.matlab_standalone_browse,
                add_stretch=False,
            )
        )
        v_box_matlab = QVBoxLayout()
        v_box_matlab.addLayout(
            self.create_horizontal_box(
                self.use_matlab_checkbox, self.use_matlab_label
            )
        )
        v_box_matlab.addLayout(v_box_matlab_path)
        v_box_matlab.addLayout(v_box_matlab_standalone_path)
        self.groupbox_matlab.setLayout(v_box_matlab)

    def create_mrtrix_group(self):
        """Create the mrtrix group box."""
        self.use_mrtrix_label = QLabel("Use mrtrix")
        self.use_mrtrix_checkbox = QCheckBox("", self)
        self.mrtrix_label = QLabel("mrtrix path (e.g. mrtrix_dir/bin):")
        self.mrtrix_choice = QLineEdit()
        self.mrtrix_browse = QPushButton("Browse")
        self.mrtrix_browse.clicked.connect(self.browse_mrtrix)
        v_box_mrtrix_path = QVBoxLayout()
        v_box_mrtrix_path.addWidget(self.mrtrix_label)
        v_box_mrtrix_path.addLayout(
            self.create_horizontal_box(
                self.mrtrix_choice, self.mrtrix_browse, add_stretch=False
            )
        )
        v_box_mrtrix = QVBoxLayout()
        v_box_mrtrix.addLayout(
            self.create_horizontal_box(
                self.use_mrtrix_checkbox, self.use_mrtrix_label
            )
        )
        v_box_mrtrix.addLayout(v_box_mrtrix_path)
        self.groupbox_mrtrix.setLayout(v_box_mrtrix)

    def create_pipeline_tab(self, _translate):
        """
        Create the 'Pipeline' tab in the settings interface.

        This tab allows configuring various neuroimaging tool settings,
        including Matlab, SPM, FSL, AFNI, ANTS, FreeSurfer, MRtrix, and
        CAPSUL.

        :param _translate (Callable): Function used to translate UI text
                                      (translate method of QCoreApplication
                                      in the Qt framework.)
        """
        self.tab_pipeline = QWidget()
        self.tab_pipeline.setObjectName("tab_pipeline")
        self.tab_widget.addTab(
            self.tab_pipeline, _translate("Dialog", "Pipeline")
        )
        self.groupbox_matlab = QGroupBox("Matlab")
        self.create_matlab_group()
        self.groupbox_spm = QGroupBox("SPM")
        self.create_spm_group()
        self.groupbox_fsl = QGroupBox("FSL")
        self.create_fsl_group()
        self.groupbox_afni = QGroupBox("AFNI")
        self.create_afni_group()
        self.groupbox_ants = QGroupBox("ANTS")
        self.create_ants_group()
        self.groupbox_freesurfer = QGroupBox("FreeSurfer")
        self.create_freesurfer_group()
        self.groupbox_mrtrix = QGroupBox("mrtrix")
        self.create_mrtrix_group()
        groupbox_capsul = QGroupBox("CAPSUL")
        self.create_capsul_group(groupbox_capsul)
        # general layout
        self.tab_pipeline_layout = QVBoxLayout()
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

    def create_projects_preferences(self):
        """Create the projects preferences group box."""
        self.projects_save_path_label = QLabel("Projects folder:")
        self.projects_save_path_line_edit = QLineEdit()
        self.projects_save_path_browse = QPushButton("Browse")
        self.projects_save_path_browse.clicked.connect(
            self.browse_projects_save_path
        )
        self.max_projects_label = QLabel(
            'Number of projects in "Saved projects":'
        )
        self.max_projects_box = QSpinBox()
        self.max_projects_box.setMinimum(1)
        self.max_projects_box.setMaximum(20)
        self.max_projects_box.setSingleStep(1)
        v_box_projects_save = QVBoxLayout()
        v_box_projects_save.addWidget(self.projects_save_path_label)
        v_box_projects_save.addLayout(
            self.create_horizontal_box(
                self.projects_save_path_line_edit,
                self.projects_save_path_browse,
                add_stretch=False,
            )
        )
        v_box_max_projects = QVBoxLayout()
        v_box_max_projects.addWidget(self.max_projects_label)
        v_box_max_projects.addLayout(
            self.create_horizontal_box(self.max_projects_box)
        )
        projects_layout = QVBoxLayout()
        projects_layout.addLayout(v_box_projects_save)
        projects_layout.addLayout(v_box_max_projects)
        self.groupbox_projects.setLayout(projects_layout)

    def create_populse_preferences(self):
        """Create the POPULSE third party preferences group box."""
        self.mri_conv_path_label = QLabel(
            "Absolute path to MRIManager.jar file: (e.g., mri_conv_dir/"
            "MRIFileManager/MRIManager.jar)"
        )
        self.mri_conv_path_line_edit = QLineEdit()
        self.mri_conv_path_browse = QPushButton("Browse")
        self.mri_conv_path_browse.clicked.connect(self.browse_mri_conv_path)
        v_box_mri_conv = QVBoxLayout()
        v_box_mri_conv.addWidget(self.mri_conv_path_label)
        v_box_mri_conv.addLayout(
            self.create_horizontal_box(
                self.mri_conv_path_line_edit,
                self.mri_conv_path_browse,
                add_stretch=False,
            )
        )
        populse_layout = QVBoxLayout()
        populse_layout.addLayout(v_box_mri_conv)
        self.groupbox_populse.setLayout(populse_layout)

    def create_resources_preferences(self):
        """Create the external resources preferences group box."""
        self.resources_path_label = QLabel(
            "Absolute path to the external resource data (required by "
            "certain processes for proper functionality):"
        )
        self.resources_path_line_edit = QLineEdit()
        self.resources_path_browse = QPushButton("Browse")
        self.resources_path_browse.clicked.connect(self.browse_resources_path)
        v_box_resources = QVBoxLayout()
        v_box_resources.addWidget(self.resources_path_label)
        v_box_resources.addLayout(
            self.create_horizontal_box(
                self.resources_path_line_edit,
                self.resources_path_browse,
                add_stretch=False,
            )
        )
        resources_layout = QVBoxLayout()
        resources_layout.addLayout(v_box_resources)
        self.groupbox_resources.setLayout(resources_layout)

    def create_spm_group(self):
        """Create the SPM group box."""
        self.use_spm_label = QLabel("Use SPM")
        self.use_spm_checkbox = QCheckBox("", self)
        self.spm_label = QLabel("SPM path (e.g., spm_dir/spm12):")
        self.spm_choice = QLineEdit()
        self.spm_browse = QPushButton("Browse")
        self.spm_browse.clicked.connect(self.browse_spm)
        self.use_spm_standalone_label = QLabel("Use SPM standalone")
        self.use_spm_standalone_checkbox = QCheckBox("", self)
        self.spm_standalone_label = QLabel(
            "SPM standalone path (e.g., the directory hosting the "
            "run_spm12.sh file):"
        )
        self.spm_standalone_choice = QLineEdit()
        self.spm_standalone_browse = QPushButton("Browse")
        self.spm_standalone_browse.clicked.connect(self.browse_spm_standalone)
        v_box_spm_path = QVBoxLayout()
        v_box_spm_path.addWidget(self.spm_label)
        v_box_spm_path.addLayout(
            self.create_horizontal_box(
                self.spm_choice, self.spm_browse, add_stretch=False
            )
        )
        v_box_spm_standalone_path = QVBoxLayout()
        v_box_spm_standalone_path.addWidget(self.spm_standalone_label)
        v_box_spm_standalone_path.addLayout(
            self.create_horizontal_box(
                self.spm_standalone_choice,
                self.spm_standalone_browse,
                add_stretch=False,
            )
        )
        v_box_spm = QVBoxLayout()
        v_box_spm.addLayout(
            self.create_horizontal_box(
                self.use_spm_checkbox, self.use_spm_label
            )
        )
        v_box_spm.addLayout(v_box_spm_path)
        v_box_spm.addLayout(
            self.create_horizontal_box(
                self.use_spm_standalone_checkbox, self.use_spm_standalone_label
            )
        )
        v_box_spm.addLayout(v_box_spm_standalone_path)
        self.groupbox_spm.setLayout(v_box_spm)

    def create_tools_tab(self, _translate):
        """
        Create the 'Tools' tab in the settings interface.

        This tab contains various sections for configuring global preferences,
        project-specific settings, third-party tool integration, and external
        resources.

        :param _translate (Callable): Function used to translate UI text
                                      (translate method of QCoreApplication
                                      in the Qt framework.)
        """
        self.tab_tools = QWidget()
        self.tab_tools.setObjectName("tab_tools")
        self.tab_widget.addTab(self.tab_tools, _translate("Dialog", "Tools"))
        self.groupbox_global = QGroupBox("Global preferences")
        self.create_global_preferences()
        self.groupbox_projects = QGroupBox("Projects preferences")
        self.create_projects_preferences()
        self.groupbox_populse = QGroupBox("POPULSE third party preference")
        self.create_populse_preferences()
        self.groupbox_resources = QGroupBox("External resources preferences")
        self.create_resources_preferences()
        self.tab_tools_layout = QVBoxLayout()
        self.tab_tools_layout.addLayout(
            self.create_horizontal_box(self.groupbox_global)
        )
        self.tab_tools_layout.addWidget(self.groupbox_projects)
        self.tab_tools_layout.addWidget(self.groupbox_populse)
        self.tab_tools_layout.addWidget(self.groupbox_resources)
        self.tab_tools_layout.addStretch(1)
        self.tab_tools.setLayout(self.tab_tools_layout)

    def edit_capsul_config(self):
        """
        Capsul engine edition.

        This method is used when user hit the Edit CAPSUL config button
        (File > MIA preferences > Pipeline tab).
        """

        # Validate the current Mia config first
        if not self.validate_and_save():
            return

        config = Config()
        capsul_config = config.get_capsul_config(sync_from_engine=False)
        modules = capsul_config.get("engine_modules", [])
        # Build a temporary new engine (because it may not be validated)
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
                logger.warning(e)
                return

            # Update Mia preferences GUI which might have changed
            self.update_gui_from_capsul_config(config)

        del dialog
        del engine

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
        h_box_find = QHBoxLayout()
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
        """
        Highlights characters in red when using the Find button in the
        configuration editor.

        This method searches for a pattern entered in the find field and
        highlights all matching occurrences in the text editor.
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

    def load_config(self):
        """Load the configuration settings."""
        config = Config()
        self.save_checkbox.setChecked(config.isAutoSave())
        self.clinical_mode_checkbox.setChecked(config.get_use_clinical())
        self.admin_mode_checkbox.setChecked(not config.get_user_mode())
        self.change_psswd.setVisible(not config.get_user_mode())
        self.edit_config.setVisible(not config.get_user_mode())
        self.control_checkbox.setChecked(config.isControlV1())
        self.max_thumbnails_box.setValue(config.get_max_thumbnails())
        self.radioView_checkbox.setChecked(config.isRadioView())
        self.projects_save_path_line_edit.setText(
            config.get_projects_save_path()
        )
        self.max_projects_box.setValue(config.get_max_projects())
        self.mri_conv_path_line_edit.setText(config.get_mri_conv_path())
        self.resources_path_line_edit.setText(config.get_resources_path())
        self.use_afni_checkbox.setChecked(config.get_use_afni())
        self.afni_choice.setText(config.get_afni_path())
        self.use_ants_checkbox.setChecked(config.get_use_ants())
        self.ants_choice.setText(config.get_ants_path())
        self.use_freesurfer_checkbox.setChecked(config.get_use_freesurfer())
        self.freesurfer_choice.setText(config.get_freesurfer_setup())
        self.use_fsl_checkbox.setChecked(config.get_use_fsl())
        self.fsl_choice.setText(config.get_fsl_config())
        self.matlab_choice.setText(config.get_matlab_path())
        self.matlab_standalone_choice.setText(
            config.get_matlab_standalone_path()
        )
        self.use_mrtrix_checkbox.setChecked(config.get_use_mrtrix())
        self.mrtrix_choice.setText(config.get_mrtrix_path())
        self.spm_choice.setText(config.get_spm_path())

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
            self.use_spm_standalone_checkbox.setChecked(False)
            self.use_matlab_checkbox.setChecked(True)
            self.use_spm_checkbox.setChecked(True)
            self.use_matlab_standalone_checkbox.setChecked(False)

        elif config.get_use_matlab():
            self.use_spm_standalone_checkbox.setChecked(False)
            self.use_matlab_checkbox.setChecked(True)
            self.use_spm_checkbox.setChecked(False)
            self.use_matlab_standalone_checkbox.setChecked(False)

        elif config.get_use_matlab_standalone():
            self.use_spm_standalone_checkbox.setChecked(False)
            self.use_matlab_checkbox.setChecked(False)
            self.use_spm_checkbox.setChecked(False)
            self.use_matlab_standalone_checkbox.setChecked(True)

        self.spm_standalone_choice.setText(config.get_spm_standalone_path())
        self.background_color_combo.setCurrentText(
            config.getBackgroundColor() or "White"
        )
        self.text_color_combo.setCurrentText(config.getTextColor() or "Black")
        self.fullscreen_cbox.setChecked(config.get_mainwindow_maximized())
        wsize = config.get_mainwindow_size()

        if isinstance(wsize, list) and len(wsize) >= 2:
            self.mainwindow_size_x_spinbox.setValue(wsize[0])
            self.mainwindow_size_y_spinbox.setValue(wsize[1])

    def ok_clicked(self):
        """Handle the OK button click event."""

        if self.validate_and_save(OK_clicked=True):
            self.accept()
            self.close()

    def save_minimal_config(self, config):
        """
        Saves a minimal configuration for CAPSUL config synchronization.

        :param config (Config): The configuration object to update and save.
        """
        config.set_afni_path(self.afni_choice.text())
        config.set_use_afni(self.use_afni_checkbox.isChecked())
        config.set_ants_path(self.ants_choice.text())
        config.set_use_ants(self.use_ants_checkbox.isChecked())
        config.set_freesurfer_setup(self.freesurfer_choice.text())
        config.set_use_freesurfer(self.use_freesurfer_checkbox.isChecked())
        config.set_fsl_config(self.fsl_choice.text())
        config.set_use_fsl(self.use_fsl_checkbox.isChecked())
        config.set_matlab_path(self.matlab_choice.text())
        config.set_use_matlab(self.use_matlab_checkbox.isChecked())
        config.set_matlab_standalone_path(self.matlab_standalone_choice.text())
        config.set_use_matlab_standalone(
            self.use_matlab_standalone_checkbox.isChecked()
        )
        config.set_mrtrix_path(self.mrtrix_choice.text())
        config.set_use_mrtrix(self.use_mrtrix_checkbox.isChecked())
        config.set_spm_path(self.spm_choice.text())
        config.set_use_spm(self.use_spm_checkbox.isChecked())
        config.set_spm_standalone_path(self.spm_standalone_choice.text())
        config.set_use_spm_standalone(
            self.use_spm_standalone_checkbox.isChecked()
        )

    def save_full_config(self, config):
        """
        Saves the full configuration and validates settings.

        :param config (Config): The configuration object to update and save.

        :return (bool): True if the configuration is valid and successfully
                        saved, False otherwise.
        """
        config.setAutoSave(self.save_checkbox.isChecked())
        config.set_radioView(self.radioView_checkbox.isChecked())
        config.setControlV1(self.control_checkbox.isChecked())
        config.set_max_thumbnails(
            min(max(self.max_thumbnails_box.value(), 1), 15)
        )
        config.set_max_projects(min(max(self.max_projects_box.value(), 1), 20))
        self.main_window.windowName = "MIA - Multiparametric Image Analysis"

        if self.admin_mode_checkbox.isChecked():
            config.set_user_mode(False)
            self.main_window.windowName = (
                f"{self.main_window.windowName} (Admin mode)"
            )

        else:
            config.set_user_mode(True)

        # Final Window name
        self.main_window.windowName = f"{self.main_window.windowName} - "
        self.main_window.setWindowTitle(
            f"{self.main_window.windowName}{self.main_window.projectName}"
        )

        if self.clinical_mode_checkbox.isChecked():
            config.set_clinical_mode(True)
            self.use_clinical_mode_signal.emit()

        else:
            config.set_clinical_mode(False)
            self.not_use_clinical_mode_signal.emit()

        fullscreen = self.fullscreen_cbox.isChecked()
        config.set_mainwindow_maximized(fullscreen)

        if fullscreen:
            self.main_window.showMaximized()

        else:
            self.main_window.showNormal()

        config.set_mainwindow_size(
            [
                self.mainwindow_size_x_spinbox.value(),
                self.mainwindow_size_y_spinbox.value(),
            ]
        )
        config.setBackgroundColor(self.background_color_combo.currentText())
        config.setTextColor(self.text_color_combo.currentText())
        self.main_window.setStyleSheet(
            f"background-color:{self.background_color_combo.currentText()};"
            f"color:{self.text_color_combo.currentText()};"
        )

        if not self.validate_paths(config):
            return False

        self.signal_preferences_change.emit()
        return True

    def setup_ui(self):
        """Set up the user interface components."""
        self.setObjectName("Dialog")
        self.setWindowTitle("MIA preferences")
        _translate = QtCore.QCoreApplication.translate
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setEnabled(True)
        # Create tabs
        self.create_tools_tab(_translate)
        self.create_pipeline_tab(_translate)
        self.create_appearance_tab(_translate)
        # Buttons layout
        self.push_button_ok = QPushButton("OK")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)
        self.push_button_cancel = QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)
        self.status_label = QLabel("")
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.status_label)
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        hbox_buttons.addWidget(self.push_button_cancel)
        vbox = QVBoxLayout()
        vbox.addWidget(self.tab_widget)
        vbox.addLayout(hbox_buttons)
        # Global layout - scrollable global window
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.widget = QWidget()
        self.widget.setLayout(vbox)
        self.scroll.setWidget(self.widget)
        self.final_layout = QVBoxLayout()
        self.final_layout.addWidget(self.scroll)
        self.setLayout(self.final_layout)

    def show_error_message(self, title, message):
        """
        Displays an error message dialog.

        :param title (str): The title of the error message dialog.
        :param message (str): The detailed error message to display.
        """
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Critical)
        self.msg.setText(title)
        self.msg.setInformativeText(message)
        self.msg.setWindowTitle("Error")
        self.msg.setStandardButtons(QMessageBox.Ok)
        self.msg.buttonClicked.connect(self.msg.close)
        self.msg.show()

    def show_warning_message(self, title, message):
        """
        Displays a warning message dialog.

        :param title (str): The title of the warning message dialog.
        :param message (str): The detailed warning message to display.
        """
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Warning)
        self.msg.setText(title)
        self.msg.setInformativeText(message)
        self.msg.setWindowTitle("Warning")
        self.msg.setStandardButtons(QMessageBox.Ok)
        self.msg.buttonClicked.connect(self.msg.close)
        self.msg.show()

    def update_gui_from_capsul_config(self, conf):
        """
        Updates the GUI elements based on the CAPSUL configuration.

        This method retrieves the configuration settings for various
        neuroimaging tools (e.g., AFNI, ANTs, FreeSurfer, FSL, Matlab,
        SPM, etc.) and updates the corresponding GUI fields, including
        checkboxes and text fields.

        :param conf (CapsulConfig): The CAPSUL configuration object containing
                                    the paths and usage states of different
                                    tools.
        """
        # afni
        use_afni = conf.get_use_afni()

        if use_afni:
            self.afni_choice.setText(conf.get_afni_path())

        self.use_afni_checkbox.setChecked(use_afni)
        # ants
        use_ants = conf.get_use_ants()

        if use_ants:
            self.ants_choice.setText(conf.get_ants_path())

        self.use_ants_checkbox.setChecked(use_ants)
        # freesurfer
        use_freesurfer = conf.get_use_freesurfer()

        if use_freesurfer:
            self.freesurfer_choice.setText(conf.get_freesurfer_setup())

        self.use_freesurfer_checkbox.setChecked(use_freesurfer)
        # fsl
        use_fsl = conf.get_use_fsl()

        if use_fsl:
            self.fsl_choice.setText(conf.get_fsl_config())

        self.use_fsl_checkbox.setChecked(use_fsl)
        # matlab
        use_matlab = conf.get_use_matlab()
        self.use_matlab_checkbox.setChecked(use_matlab)
        self.matlab_choice.setText(conf.get_matlab_path())
        # matlab - MCR
        use_matlab_sa = conf.get_use_matlab_standalone()
        self.use_matlab_standalone_checkbox.setChecked(use_matlab_sa)
        self.matlab_standalone_choice.setText(
            conf.get_matlab_standalone_path()
        )
        # mrtrix
        use_mrtrix = conf.get_use_mrtrix()

        if use_mrtrix:
            self.mrtrix_choice.setText(conf.get_mrtrix_path())

        self.use_mrtrix_checkbox.setChecked(use_mrtrix)
        # spm
        use_spm = conf.get_use_spm()
        self.use_spm_checkbox.setChecked(use_spm)
        self.spm_choice.setText(conf.get_spm_path())
        # spm - Standalone
        use_spm_sa = conf.get_use_spm_standalone()
        self.use_spm_standalone_checkbox.setChecked(use_spm_sa)
        self.spm_standalone_choice.setText(conf.get_spm_standalone_path())

    def use_afni_changed(self):
        """Handle the use_afni checkbox change event."""
        self.afni_choice.setDisabled(not self.use_afni_checkbox.isChecked())
        self.afni_label.setDisabled(not self.use_afni_checkbox.isChecked())

    def use_ants_changed(self):
        """Handle the use_ants checkbox change event."""
        self.ants_choice.setDisabled(not self.use_ants_checkbox.isChecked())
        self.ants_label.setDisabled(not self.use_ants_checkbox.isChecked())

    def use_current_mainwindow_size(self):
        """Use the current main window size."""
        self.mainwindow_size_x_spinbox.setValue(self.main_window.width())
        self.mainwindow_size_y_spinbox.setValue(self.main_window.height())

    def use_freesurfer_changed(self):
        """Handle the use_freesurfer checkbox change event."""
        self.freesurfer_choice.setDisabled(
            not self.use_freesurfer_checkbox.isChecked()
        )
        self.freesurfer_label.setDisabled(
            not self.use_freesurfer_checkbox.isChecked()
        )

    def use_fsl_changed(self):
        """Handle the use_fsl checkbox change event."""
        self.fsl_choice.setDisabled(not self.use_fsl_checkbox.isChecked())
        self.fsl_label.setDisabled(not self.use_fsl_checkbox.isChecked())

    def use_matlab_changed(self):
        """Handle the use_matlab checkbox change event."""

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
        """Handle the use_matlab_standalone checkbox change event."""

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
        """Handle the use_mrtrix checkbox change event."""
        self.mrtrix_choice.setDisabled(
            not self.use_mrtrix_checkbox.isChecked()
        )
        self.mrtrix_label.setDisabled(not self.use_mrtrix_checkbox.isChecked())

    def use_spm_changed(self):
        """Handle the use_spm checkbox change event."""

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
        """Handle the use_spm_standalone checkbox change event."""

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

    def validate_and_save(self, OK_clicked=False):
        """
        Validate and save the preferences.

        :param ok_clicked (bool): Whether the OK button was clicked (True)
                                  when this method was launched.

        :Contains:
            - remove_capsul_config: Helper function to remove a
                                    module's configuration
            - clean_spm_config: Cleans the SPM configuration based
                                on standalone mode
            - clean_matlab_config: Removes MATLAB-related configuration keys
        """
        config = Config()

        if not OK_clicked:
            self.save_minimal_config(config)

        elif not self.save_full_config(config):
            return False

        c_c = config.config.setdefault("capsul_config", {})
        c_e = config.get_capsul_engine()

        if not (c_c and c_e):
            config.get_capsul_config(sync_from_engine=False)
            config.saveConfig()
            return True

        def remove_capsul_config(module, key):
            """
            Helper function to remove a module's configuration.

            :param module (str): The name of the module to remove.
            :param key (str): The specific configuration key to remove.

            """
            # TODO: We only deal here with the global environment
            cif = c_e.settings.config_id_field

            with c_e.settings as settings:
                config_module = settings.config(module, "global")

                if config_module:
                    settings.remove_config(
                        module, "global", getattr(config_module, cif)
                    )

            if not module == "freesurfer":
                c_c.get("engine", {}).get("global", {}).get(
                    f"capsul.engine.module.{module}", {}
                ).get(module, {}).pop(key, None)

        # Sync capsul config from mia config, if module is not used:
        for module in ["afni", "ants", "freesurfer", "fsl", "mrtrix"]:

            if not getattr(config, f"get_use_{module}")():
                remove_capsul_config(module, "directory")

                if module == "fsl":
                    remove_capsul_config(module, "config")

        def clean_spm_config(standalone_check):
            """
            Cleans the SPM configuration based on standalone mode.

            :param standalone_check (bool): Indicates whether to clean based
                                            on standalone mode.
            """

            try:
                keys = list(
                    c_c["engine"]["global"]["capsul.engine.module.spm"].keys()
                )

            except KeyError:
                return

            dict4clean = {
                k: bool(
                    "standalone"
                    in c_c["engine"]["global"]["capsul.engine.module.spm"][k]
                    and c_c["engine"]["global"]["capsul.engine.module.spm"][k][
                        "standalone"
                    ]
                    == standalone_check
                )
                for k in keys
            }
            for k, should_remove in dict4clean.items():

                if should_remove:
                    del c_c["engine"]["global"]["capsul.engine.module.spm"][k]

        if not config.get_use_spm_standalone():
            clean_spm_config(True)

        if not config.get_use_spm():
            clean_spm_config(False)

        if (
            not c_c.get("engine", {})
            .get("global", {})
            .get("capsul.engine.module.spm", {})
        ):
            c_c["engine"]["global"].pop("capsul.engine.module.spm", None)

        def clean_matlab_config(key):
            """
            Removes MATLAB-related configuration keys.

            :param key (str): The configuration key to remove from the MATLAB
                              module.
            """

            try:
                keys = list(
                    c_c["engine"]["global"][
                        "capsul.engine.module.matlab"
                    ].keys()
                )

            except KeyError:
                return

            for k in keys:
                c_c["engine"]["global"]["capsul.engine.module.matlab"][k].pop(
                    key, None
                )

        if not config.get_use_matlab():
            clean_matlab_config("executable")

        if not config.get_use_matlab_standalone():
            clean_matlab_config("mcr_directory")

        if (
            not c_c.get("engine", {})
            .get("global", {})
            .get("capsul.engine.module.matlab", {})
        ):
            c_c["engine"]["global"].pop("capsul.engine.module.matlab", None)

        config.get_capsul_config(sync_from_engine=False)
        config.saveConfig()
        return True

    def validate_matlab_path(self, path, config):
        """
        Validates the given Matlab executable path.

        :param path (str): The path to the Matlab executable.
        :param config (Config): The configuration object to update.

        :return (bool): True if the path is valid and updated in the
                        configuration, False otherwise.
        """

        if not os.path.isfile(path):
            self.wrong_path(path, "Matlab")
            return False

        if path == config.get_matlab_path():
            config.set_use_matlab(True)
            config.set_use_matlab_standalone(False)

            if not self.use_spm_checkbox.isChecked():
                config.set_use_spm(False)
                config.set_use_spm_standalone(False)
                # We don't test matlab because it has already been
                # tested before

            return True

        elif not self.use_spm_checkbox.isChecked():

            try:
                matlab_cmd = "ver; exit"
                result = subprocess.run(
                    [
                        path,
                        "-nodisplay",
                        "-nodesktop",
                        "-nosplash",
                        "-singleCompThread",
                        "-r",
                        matlab_cmd,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                err = result.stderr

            except subprocess.CalledProcessError:
                self.wrong_path(path, "Matlab")
                return False

            except Exception as e:  # Catch any other unexpected errors
                logger.warning(f"❌ Unexpected error: {e}")
                self.wrong_path(path, "Matlab")
                return False

            if err == "":
                config.set_matlab_path(path)
                config.set_use_matlab(True)
                config.set_use_matlab_standalone(False)
                config.set_use_spm(False)
                config.set_use_spm_standalone(False)
                return True

            else:
                self.wrong_path(path, "Matlab")
                return False

        else:
            # If self.use_spm_checkbox.isChecked() is True, the test will
            # take place when SPM is validated.
            return True

    def validate_matlab_standalone_path(self, path, config):
        """
        Validate the Matlab standalone path.

        This method does not thoroughly test the configuration for Matlab
        MCR alone (without SPM standalone) due to the lack of a concrete
        example.

        :param path (str): The path to the Matlab standalone directory.
        :param config (Config): The configuration object to update.

        :return (bool): True if the path is valid and updated in the
                        configuration, False otherwise.
        """

        if not os.path.isdir(path):
            self.wrong_path(path, "Matlab standalone")
            return False

        if not self.use_spm_standalone_checkbox.isChecked():
            archi = platform.architecture()
            config.set_matlab_standalone_path(path)

            if "Windows" in archi[1]:
                logger.info(
                    "Matlab Standalone Path enter, this is "
                    "unnecessary to use SPM12 with Windows OS."
                )
                config.set_use_matlab(True)
                config.set_use_matlab_standalone(False)
                config.set_use_spm_standalone(False)
                config.set_use_spm(False)
                return True

            else:
                config.set_use_matlab(False)
                config.set_use_matlab_standalone(True)
                config.set_use_spm_standalone(False)
                config.set_use_spm(False)
                return True

        else:
            # If self.use_spm_standalone_checkbox.isChecked() is True,
            # the test will take place when SPM Stadalone is validated.
            pass

    def validate_paths(self, config):
        """
        Validate the paths and settings.

        This method checks the validity of paths for various neuroimaging
        tools (AFNI, ANTS, FreeSurfer, FSL, MRtrix, Matlab, SPM, etc.) and
        updates the configuration accordingly. It also validates additional
        paths such as the projects folder, MRIFileManager.jar path, and
        resources folder.

        :param config (Config): The configuration object where validated
                                paths and settings will be stored.

        :return (bool): True if all paths and settings are valid, False
                        otherwise.
        """
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.status_label.setText("Testing configuration ...")
        QtCore.QCoreApplication.processEvents()
        tools = [
            (
                "AFNI",
                self.afni_choice.text(),
                self.use_afni_checkbox.isChecked(),
                config.set_use_afni,
                config.set_afni_path,
                "afni",
                "afni",
            ),
            (
                "ANTS",
                self.ants_choice.text(),
                self.use_ants_checkbox.isChecked(),
                config.set_use_ants,
                config.set_ants_path,
                "antsRegistration",
                "ANTS",
            ),
            (
                "FreeSurfer",
                self.freesurfer_choice.text(),
                self.use_freesurfer_checkbox.isChecked(),
                config.set_use_freesurfer,
                config.set_freesurfer_setup,
                "recon-all",
                "freesurfer",
            ),
            (
                "FSL",
                self.fsl_choice.text(),
                self.use_fsl_checkbox.isChecked(),
                config.set_use_fsl,
                config.set_fsl_config,
                "flirt",
                "FSL",
            ),
            (
                "mrtrix",
                self.mrtrix_choice.text(),
                self.use_mrtrix_checkbox.isChecked(),
                config.set_use_mrtrix,
                config.set_mrtrix_path,
                "mrinfo",
                "mrtrix",
            ),
            (
                "Matlab",
                self.matlab_choice.text(),
                self.use_matlab_checkbox.isChecked(),
                config.set_use_matlab,
                config.set_matlab_path,
                None,
                "Matlab",
            ),
            (
                "SPM",
                self.spm_choice.text(),
                self.use_spm_checkbox.isChecked(),
                config.set_use_spm,
                config.set_spm_path,
                None,
                "SPM",
            ),
            (
                "Matlab Standalone",
                self.matlab_standalone_choice.text(),
                self.use_matlab_standalone_checkbox.isChecked(),
                config.set_use_matlab_standalone,
                config.set_matlab_standalone_path,
                None,
                "Matlab standalone",
            ),
            (
                "SPM Standalone",
                self.spm_standalone_choice.text(),
                self.use_spm_standalone_checkbox.isChecked(),
                config.set_use_spm_standalone,
                config.set_spm_standalone_path,
                None,
                "SPM standalone",
            ),
        ]

        for (
            tool_name,
            path,
            is_checked,
            set_in_use,
            set_path,
            cmd,
            config_name,
        ) in tools:

            if not is_checked:
                set_in_use(is_checked)

            elif not self.validate_tool_path(
                tool_name, path, cmd, config, config_name, set_in_use, set_path
            ):
                QApplication.restoreOverrideCursor()
                return False

        # Projects folder
        projects_folder = self.projects_save_path_line_edit.text()

        if os.path.isdir(projects_folder):
            config.set_projects_save_path(projects_folder)

        else:
            self.show_error_message(
                "Invalid projects folder path",
                f"The projects folder path entered `{projects_folder}` is "
                f"invalid.",
            )
            QApplication.restoreOverrideCursor()
            return False

        # MRIFileManager.jar path
        mri_conv_path = self.mri_conv_path_line_edit.text()

        if mri_conv_path == "":
            self.show_warning_message(
                "Empty MRIFileManager.jar path",
                "No path has been entered for MRIFileManager.jar.",
            )
            config.set_mri_conv_path(mri_conv_path)

        elif os.path.isfile(mri_conv_path):
            config.set_mri_conv_path(mri_conv_path)

        else:
            self.show_error_message(
                "Invalid MRIFileManager.jar path",
                f"The MRIFileManager.jar path entered '{mri_conv_path}' is "
                f"invalid.",
            )
            QApplication.restoreOverrideCursor()
            return False

        # Resources folder
        resources_folder = self.resources_path_line_edit.text()

        if os.path.isdir(resources_folder):
            config.set_resources_path(resources_folder)

        else:
            self.show_error_message(
                "Invalid resources folder path",
                f"The resources folder path entered '{resources_folder}' is "
                f"invalid.",
            )
            QApplication.restoreOverrideCursor()
            return False

        QApplication.restoreOverrideCursor()
        return True

    def validate_spm_path(self, path, config):
        """
        Validates the SPM path and its compatibility with Matlab.

        This method checks whether the provided SPM and Matlab paths are
        valid. If they are already configured correctly, it enables SPM and
        Matlab usage without further checks. Otherwise, it attempts to run
        an SPM command via Matlab to confirm the setup.

        :param path (str): The file path to the SPM installation.
        :param config (Config): The configuration object where validated
                                paths and settings will be stored.

        :return (bool): True if the SPM path and Matlab path are valid,
                        False otherwise.
        """
        matlab_path = self.matlab_choice.text()

        if not os.path.isdir(path):
            self.wrong_path(path, "SPM")
            return False

        if not os.path.isfile(matlab_path):
            self.wrong_path(matlab_path, "Matlab")
            return False

        if (
            path == config.get_spm_path()
            and matlab_path == config.get_matlab_path()
        ):
            config.set_use_spm(True)
            config.set_use_matlab(True)
            config.set_use_matlab_standalone(False)
            config.set_use_spm_standalone(False)
            # We don't test Matlab and SPM because it has already been
            # tested before
            return True

        else:

            try:
                matlab_cmd = (
                    f"restoredefaultpath; "
                    f"addpath('{path}'); "
                    f"[name, ~]=spm('Ver'); "
                    f"exit"
                )
                result = subprocess.run(
                    [
                        matlab_path,
                        "-nodisplay",
                        "-nodesktop",
                        "-nosplash",
                        "-singleCompThread",
                        "-r",
                        matlab_cmd,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                err = result.stderr

            except subprocess.CalledProcessError:
                self.wrong_path(matlab_path, "Matlab")
                return False

            except Exception as e:  # Catch any other unexpected errors
                logger.warning(f"❌ Unexpected error: {e}")
                self.wrong_path(matlab_path, "Matlab")
                return False

            if err == "":
                config.set_matlab_path(matlab_path)
                config.set_spm_path(path)
                config.set_use_matlab(True)
                config.set_use_spm(True)
                config.set_use_matlab_standalone(False)
                config.set_use_spm_standalone(False)
                return True

            elif "spm" in err:
                self.wrong_path(path, "SPM")
                return False

            else:
                self.wrong_path(matlab_path, "Matlab")
                return False

    def validate_spm_standalone_path(self, path, config):
        """
        Validates the SPM standalone path and its compatibility with
        Matlab standalone.

        This method checks whether the provided paths for SPM standalone
        and Matlab standalone (if applicable) are valid. It also verifies
        system architecture compatibility and attempts to execute SPM
        standalone to confirm its functionality.

        :param path (str): The file path to the SPM standalone installation.
        :param config (Config): The configuration object where validated
                                paths and settings will be stored.

        :return (bool): True if the SPM standalone and Matlab standalone
                        paths are valid, False otherwise.
        """
        matlab_path = self.matlab_standalone_choice.text()
        archi = platform.architecture()

        if (not os.path.isdir(matlab_path)) and ("Windows" not in archi[1]):
            self.wrong_path(matlab_path, "Matlab standalone")
            return False

        if (matlab_path == config.get_matlab_standalone_path()) and (
            path == config.get_spm_standalone_path()
        ):
            config.set_use_spm_standalone(True)

            if "Windows" in archi[1]:
                config.set_use_matlab(True)
                config.set_use_matlab_standalone(False)

            else:
                config.set_use_matlab_standalone(True)

            return True

        if os.path.isdir(path):

            if "Windows" in archi[1]:
                mcr = glob.glob(os.path.join(path, "spm*_win*.exe"))
                pos = False
                nb_bit_sys = archi[0]

                for i, mcr_path in enumerate(mcr):
                    spm_path, spm_file_name = os.path.split(mcr_path)

                    if nb_bit_sys[:2] in spm_file_name:
                        pos = i

                if pos is False:
                    self.wrong_path(path, "SPM standalone")
                    return False

            elif os.path.isdir(matlab_path):
                mcr = glob.glob(os.path.join(path, "run_spm*.sh"))

            if mcr:

                try:

                    if "Windows" in archi[1]:
                        result = subprocess.run(
                            [mcr[pos], "--version"],
                            capture_output=True,
                            text=True,
                            check=True,
                        )

                    else:
                        result = subprocess.run(
                            [mcr[0], matlab_path, "--version"],
                            capture_output=True,
                            text=True,
                            check=True,
                        )

                    err = result.stderr
                    output = result.stdout

                except subprocess.CalledProcessError:
                    self.wrong_path(path, "SPM standalone")
                    return False

                except Exception as e:  # Catch any other unexpected errors
                    logger.warning(f"❌ Unexpected error: {e}")
                    self.wrong_path(path, "SPM standalone")
                    return False

                if (err == "" and output != "") or output.startswith("SPM8 "):
                    # spm8 standalone doesn't accept --version but prints a
                    # message that we can interpret as saying that SPM8 is
                    # working anyway.
                    config.set_use_spm_standalone(True)
                    config.set_spm_standalone_path(path)
                    config.set_matlab_standalone_path(matlab_path)

                    if "Windows" not in archi[1]:
                        config.set_use_matlab_standalone(True)

                    return True

                elif (
                    (err != "")
                    and ("version" in output.split()[2:])
                    and ("(standalone)" in output.split()[2:])
                ):
                    config.set_use_spm_standalone(True)
                    config.set_spm_standalone_path(path)
                    config.set_matlab_standalone_path(matlab_path)

                    if "Windows" not in archi[1]:
                        config.set_use_matlab_standalone(True)

                    logger.warning(
                        "The configuration for Matlab MCR and SPM "
                        "standalone as defined in Mia's preferences "
                        "seems to be valid, but the following issue has "
                        "been detected:"
                    )
                    logger.warning(f"{err}")
                    logger.warning(
                        "Please fix this issue to avoid a malfunction..."
                    )
                    return True

                elif err != "":

                    if "shared libraries" in err:
                        self.wrong_path(matlab_path, "Matlab standalone")
                        return False

                    else:
                        self.wrong_path(path, "SPM standalone")
                        return False

            else:
                self.wrong_path(path, "SPM standalone")
                return False

        else:
            self.wrong_path(path, "SPM standalone")
            return False

    def validate_tool_path(
        self, tool_name, path, cmd, config, config_name, set_in_use, set_path
    ):
        """
        Validates the specified tool's path and checks its functionality.

        This method checks if the given tool path exists and verifies that
        the tool is functional by running a command to check its version.
        It also handles tool-specific setup for FreeSurfer and FSL by setting
        environment variables and adjusting paths as necessary.

        :param tool_name (str): The name of the tool to validate
                                (e.g., "FreeSurfer", "FSL", "Matlab", etc.).
        :param path (str): The file path to the tool's installation directory.
        :param cmd (str): The command to execute within the tool's directory
                          to check its version.
        :param config (Config): The configuration object where validated
                                paths and settings will be stored.
        :param config_name (str): The name of the configuration setting for
                                  the tool.
        :param set_in_use (Callable): A function to set the tool's "in use"
                                     status in the configuration.
        :param set_path (Callable): A function to set the tool's path in the
                                   configuration.

        :return (bool): True if the tool's path is valid and functional,
                        False otherwise.
        """
        extra = ""
        option = "--version"

        if tool_name in ["FreeSurfer", "FSL"]:
            path_setup = path
            path = os.path.dirname(path)
            extra = "bin"

            if "FREESURFER_HOME" not in os.environ:
                os.environ["FREESURFER_HOME"] = path

            if tool_name == "FSL":
                option = "-version"

                if path.endswith(os.path.join("etc", "fslconf")):
                    path = os.path.dirname(os.path.dirname(path))

                elif path.endswith("etc"):
                    path = os.path.dirname(path)

        if tool_name not in [
            "Matlab",
            "Matlab Standalone",
            "SPM",
            "SPM Standalone",
        ] and not os.path.isdir(path):
            self.wrong_path(path, tool_name)
            return False

        cmd = os.path.join(path, extra, cmd) if cmd else None

        if cmd:

            try:
                result = subprocess.run(
                    [cmd, option],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                err = result.stderr

            except subprocess.CalledProcessError:
                self.wrong_path(path, tool_name, "config file")
                return False

            except Exception as e:  # Catch any other unexpected errors
                logger.warning(f"❌ Unexpected error: {e}")
                self.wrong_path(path, tool_name)
                return False

            # Filter out lines containing 'warning' (case-insensitive)
            filtered_lines = [
                line
                for line in err.split("\n")
                if "warning" not in line.lower()
            ]
            # If no lines left after filtering, set err to an empty string
            err = "\n".join(filtered_lines) if filtered_lines else ""

            if err == "":

                if tool_name in ["FreeSurfer", "FSL"]:
                    set_path(path_setup)

                else:
                    set_path(path)

                set_in_use(True)

            else:
                self.wrong_path(path, tool_name)
                return False

        if tool_name == "Matlab":

            if not self.validate_matlab_path(path, config):
                return False

        elif tool_name == "SPM":

            if not self.validate_spm_path(path, config):
                return False

        elif tool_name == "Matlab Standalone":

            if not self.validate_matlab_standalone_path(path, config):
                return False

        elif tool_name == "SPM Standalone":

            if not self.validate_spm_standalone_path(path, config):
                return False

        return True

    def wrong_path(self, path, tool, extra_mess=""):
        """
        Displays an error message for an invalid tool path.

        This method restores the cursor, clears the status label,
        and shows a QMessageBox with an error message indicating
        that the provided path for a specified tool is invalid.

        :param path (str): The invalid path entered by the user.
        :param tool (str): The name of the tool for which the path is
                           being validated.
        :param extra_mess (str, optional): Additional context for the
                                           error message, such as specifying
                                           a configuration file.

        :return (None): This function does not return anything.
        """
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


class PopUpProperties(QDialog):
    """
    Dialog for modifying project properties.

    Allows users to change project settings, including visualized tags
    and information.
    Is called when the user wants to change the current project's
    properties (File > properties).

    .. Methods:
        - ok_clicked: saves the modifications and updates the data browser

    .. Signals:
        - signal_settings_change: Qt signal emitted when project settings are
                                  modified.

    """

    # Signal that will be emitted at the end to tell that the project has
    # been created
    signal_settings_change = QtCore.pyqtSignal()

    def __init__(self, project, databrowser, old_tags):
        """
        Initialize the project properties dialog.

        :param project: current project in the software
        :param databrowser: data browser instance of the software
        :param old_tags: visualized tags before opening this dialog
        """
        super().__init__()
        # Dialog setup
        self.setModal(True)
        self.project = project
        self.databrowser = databrowser
        self.old_tags = old_tags
        _translate = QtCore.QCoreApplication.translate
        self.setObjectName("Dialog")
        self.setWindowTitle("project properties")
        # Create tab widget
        self.tab_widget = QTabWidget(self)
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
        # Create buttons
        # The 'OK' push button
        self.push_button_ok = QPushButton("OK")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)
        # The 'Cancel' push button
        self.push_button_cancel = QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)
        # Layout setup
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
        # Prepare history tracking
        history_maker = ["modified_visibilities", self.old_tags]
        # Collect newly selected tags
        new_visibilities = [
            self.tab_tags.list_widget_selected_tags.item(x).text()
            for x in range(self.tab_tags.list_widget_selected_tags.count())
        ]
        new_visibilities.append(TAG_FILENAME)

        with self.project.database.data(write=True) as database_data:
            database_data.set_shown_tags(new_visibilities)

        history_maker.append(new_visibilities)
        self.project.undos.append(history_maker)
        self.project.redos.clear()
        self.project.unsavedModifications = True

        # Update data browser columns
        with self.project.database.data() as database_data:
            self.databrowser.table_data.update_visualized_columns(
                self.old_tags, database_data.get_shown_tags()
            )

        # Close dialog
        self.accept()
        self.close()


class PopUpQuit(QDialog):
    """
     Dialog to handle unsaved project modifications when closing the software.

    Provides options to save, discard, or cancel the exit process.
    Is called when the user closes the software and the current project has
    been modified.

    .. Signals:
        - save_as_signal: Signal emitted when user chooses to save the
                          project.
        - do_not_save_signal: Signal emitted when user chooses to exit
                              without saving.
        - cancel_signal: Signal emitted when user cancels the exit process.

    .. Methods:
        - can_exit: returns the value of _bool_exit
        - cancel_clicked: makes the actions to cancel the action
        - do_not_save_clicked: makes the actions not to save the project
        - save_as_clicked: makes the actions to save the project
    """

    save_as_signal = QtCore.pyqtSignal()
    do_not_save_signal = QtCore.pyqtSignal()
    cancel_signal = QtCore.pyqtSignal()

    def __init__(self, project):
        """
         Initialize the quit confirmation dialog.

        :param project: Current project with unsaved modifications.
        """
        super().__init__()
        self.project = project
        self._bool_exit = False
        self.setWindowTitle("Confirm exit")
        # Create confirmation label
        label = QLabel(
            f"Do you want to exit without saving {self.project.getName()}?"
        )
        # Create action buttons
        push_button_save_as = QPushButton("Save", self)
        push_button_do_not_save = QPushButton("Do not save", self)
        push_button_cancel = QPushButton("Cancel", self)
        # Button connections
        push_button_save_as.clicked.connect(self.save_as_clicked)
        push_button_do_not_save.clicked.connect(self.do_not_save_clicked)
        push_button_cancel.clicked.connect(self.cancel_clicked)
        # Create horizontal layout for buttons
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(push_button_save_as)
        hbox.addWidget(push_button_do_not_save)
        hbox.addWidget(push_button_cancel)
        hbox.addStretch(1)
        # Create vertical layout
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def can_exit(self):
        """
        Check if the application can exit.

        :return (bool): True if  exit is allowed.
        """
        return self._bool_exit

    def cancel_clicked(self):
        """
        Handle cancel action by preventing exit.
        """
        self._bool_exit = False
        self.cancel_signal.emit()
        self.close()

    def do_not_save_clicked(self):
        """
        Handle 'do not save' action by allowing exit without saving.
        """
        self._bool_exit = True
        self.do_not_save_signal.emit()
        self.close()

    def save_as_clicked(self):
        """
        Handle save action by emitting save signal and allowing exit.
        """
        self.save_as_signal.emit()
        self._bool_exit = True
        self.close()


class PopUpRemoveScan(QDialog):
    """
    Dialog to confirm removal of a scan previously sent to the pipeline
    manager.

    Provides options to remove or keep a scan, with additional 'apply to all'
    functionality when multiple scans are involved.
    Is called when the user wants to remove a scan that was previously sent
    to the pipeline manager.

     .. Methods:
         - cancel_clicked:
         - no_all_clicked:
         - yes_all_clicked:
         - yes_clicked:
    """

    def __init__(self, scan, size):
        """
        Initialize the remove scan confirmation dialog.

        :param scan: Identifier of the scan to be potentially removed.
        :param size: Total number of scans in the removal process.
        """
        super().__init__()
        self.setWindowTitle("Document exists in Pipeline Manager")
        # Flags to control removal behavior
        self.stop = False
        self.repeat = False
        # Create confirmation message
        label = QLabel(
            f"The document {scan} \nwas previously sent to the pipeline "
            f"manager, do you really want to delete it?"
        )
        # Create buttons
        push_button_yes = QPushButton("Ok", self)
        push_button_cancel = QPushButton("No", self)
        # Setup layout
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(push_button_yes)
        hbox.addWidget(push_button_cancel)

        # Add 'apply to all' buttons if multiple scans
        if size > 1:
            push_button_yes_all = QPushButton("Ok to all", self)
            push_button_no_all = QPushButton("No to all", self)
            hbox.addWidget(push_button_yes_all)
            hbox.addWidget(push_button_no_all)
            push_button_yes_all.clicked.connect(self.yes_all_clicked)
            push_button_no_all.clicked.connect(self.no_all_clicked)

        hbox.addStretch(1)
        # Create main layout
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        # Connect standard buttons
        push_button_yes.clicked.connect(self.yes_clicked)
        push_button_cancel.clicked.connect(self.cancel_clicked)

    def cancel_clicked(self):
        """
        Handle 'Cancel' action.

        Sets stop flag to True and indicates no global action.
        """
        self.stop = True
        self.repeat = False
        self.close()

    def no_all_clicked(self):
        """
        Handle 'No to All' action.

        Sets stop flag to True and indicates a global 'No' action.
        """

        self.stop = True
        self.repeat = True
        self.close()

    def yes_all_clicked(self):
        """
        Handle 'Yes to All' action.

        Clears stop flag and indicates a global 'Yes' action.
        """

        self.stop = False
        self.repeat = True
        self.close()

    def yes_clicked(self):
        """
        Handle 'Yes' action.

        Clears both stop and repeat flags for a single item removal.
        """

        self.stop = False
        self.repeat = False
        self.close()


class PopUpRemoveTag(QDialog):
    """
    Dialog for removing user-defined tags from a Populse MIA project.

    Allows users to select and remove custom tags from the project's database.

    .. Methods:
        - ok_action: Verifies the selected tags and send the information to
                     the data browser.
        - search_str: Matches the searched pattern with the tags of the
                      project.

    .. Signals:
        - signal_remove_tag: Qt signal emitted when tags are removed.

    """

    # Signal that will be emitted at the end to tell that
    # the project has been created
    signal_remove_tag = QtCore.pyqtSignal()

    def __init__(self, databrowser, project):
        """
        Initialize the remove tag dialog.

        :param databrowser: Data browser instance managing project data.
        :param project: Current project containing tags to be removed.
        """
        super().__init__()
        self.databrowser = databrowser
        self.project = project
        self.setWindowTitle("Remove a tag")
        self.setModal(True)
        self._translate = QtCore.QCoreApplication.translate
        self.setObjectName("Remove a tag")

        # The 'OK' push button
        self.push_button_ok = QPushButton(self)
        self.push_button_ok.setObjectName("push_button_ok")
        self.push_button_ok.setText(self._translate("Remove a tag", "OK"))
        # The "Tag list" label
        self.label_tag_list = QLabel(self)
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.label_tag_list.setText(
            self._translate("Remove a tag", "Available tags:")
        )
        # Search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        # Tag list widget
        self.list_widget_tags = QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        self.list_widget_tags.setSelectionMode(
            QAbstractItemView.MultiSelection
        )
        # Layout setup
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        hbox_top = QHBoxLayout()
        hbox_top.addWidget(self.label_tag_list)
        hbox_top.addStretch(1)
        hbox_top.addWidget(self.search_bar)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox_top)
        vbox.addWidget(self.list_widget_tags)
        vbox.addLayout(hbox_buttons)
        self.setLayout(vbox)

        with self.project.database.data() as database_data:
            user_tags = [
                tag["index"].split("|")[1]
                for tag in database_data.get_field_attributes(
                    COLLECTION_CURRENT
                )
                if tag["origin"] == TAG_ORIGIN_USER
            ]

        for tag in user_tags:
            QListWidgetItem(
                self._translate("Dialog", tag), self.list_widget_tags
            )

        # Connect signals
        self.push_button_ok.clicked.connect(self.ok_action)
        self.search_bar.textChanged.connect(self.search_str)

    def ok_action(self):
        """
        Process selected tags for removal and update the data browser.

        Retrieves selected tags and passes them to the data browser for
        removal.
        Closes the dialog after processing.
        """
        self.accept()
        # Collect selected tag names
        self.tag_names_to_remove = [
            item.text() for item in self.list_widget_tags.selectedItems()
        ]
        # Remove selected tags
        self.databrowser.remove_tag_infos(self.tag_names_to_remove)
        self.close()

    def search_str(self, search_pattern):
        """
        Filter tags based on search pattern.

        :param search_pattern: String to match against tag names.
        """

        with self.project.database.data() as database_data:
            field_attributes = database_data.get_field_attributes(
                COLLECTION_CURRENT
            )

        # Filter tags based on search pattern
        matching_tags = [
            tag["index"].split("|")[1]
            for tag in field_attributes
            if (
                tag["origin"] == TAG_ORIGIN_USER
                and (
                    not search_pattern
                    or search_pattern.upper()
                    in tag["index"].split("|")[1].upper()
                )
            )
        ]
        # Update list widget
        self.list_widget_tags.clear()

        for tag in matching_tags:
            QListWidgetItem(
                self._translate("Dialog", tag), self.list_widget_tags
            )


class PopUpSaveProjectAs(QDialog):
    """
    Dialog for saving a project under a new name.

    Provides a user interface to select and save a project with a new name,
    with options to browse existing projects and validate the new project
    name.

    .. Method:
        - fill_input: Fills the input field when a project is clicked on
        - return_value: Sets the widget's attributes depending on the
          selected file name

    .. Signals:
        - signal_saved_project: Qt signal emitted when a new project name
                                is selected.

    """

    # Signal that will be emitted at the end to tell
    # that the new file name has been chosen
    signal_saved_project = QtCore.pyqtSignal()

    def __init__(self):
        """
        Initialize the save project as dialog.

        Sets up the user interface with a scrollable list of existing
        projects, input field for new project name, and save/cancel buttons.
        """
        super().__init__()
        self.setWindowTitle("Save project as")
        self.validate = False
        # Configuration and path setup
        self.config = Config()
        self.project_path = self.config.get_projects_save_path()
        # Project name input
        self.new_project = QLineEdit()
        self.new_project_label = QLabel("New project name")
        # Projects list setup
        self.v_box = QVBoxLayout()
        project_list = sorted(
            [
                proj
                for proj in os.listdir(self.project_path)
                if os.path.isdir(os.path.join(self.project_path, proj))
            ]
        )

        for project_name in project_list:
            label = QLabel_clickable(project_name)
            label.clicked.connect(partial(self.fill_input, project_name))
            self.v_box.addWidget(label)

        # Scroll area for projects list
        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setMaximumHeight(250)
        self.final = QVBoxLayout()
        self.final.addWidget(self.scroll)
        # Wrap projects list in a widget
        self.widget = QWidget()
        self.widget.setLayout(self.v_box)
        self.scroll.setWidget(self.widget)
        # Create input layout
        self.h_box_text = QHBoxLayout()
        self.h_box_text.addWidget(self.new_project_label)
        self.h_box_text.addWidget(self.new_project)
        self.h_box_bottom = QHBoxLayout()
        self.h_box_bottom.addStretch(1)
        # Save button
        self.push_button_ok = QPushButton("Save as")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.return_value)
        self.h_box_bottom.addWidget(self.push_button_ok)
        # Cancel button
        self.push_button_cancel = QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)
        self.h_box_bottom.addWidget(self.push_button_cancel)
        # Final layout
        self.final_layout = QVBoxLayout()
        self.final_layout.addWidget(QLabel("Projects list:"))
        self.final_layout.addLayout(self.final)
        self.final_layout.addLayout(self.h_box_text)
        self.final_layout.addLayout(self.h_box_bottom)
        self.setLayout(self.final_layout)

    def fill_input(self, name):
        """
        Fill the project name input field with the selected project name.

        :param name: Name of the project to fill in the input field.
        """
        self.new_project.setText(name)

    def return_value(self):
        """
        Validate and process the selected project name.

        Checks project name validity, handles potential naming conflicts,
        and emits a signal when a valid project name is selected.

        :return (str): Full path of the new project if successful,
                       None otherwise.
        """
        # import message_already_exists only here to prevent circular
        # import issue
        from populse_mia.utils import message_already_exists

        file_name = self.new_project.text().strip()

        if not file_name:
            return None

        projects_folder = self.project_path
        entire_path = os.path.abspath(os.path.join(projects_folder, file_name))
        # Set path attributes
        self.path, self.name = os.path.split(entire_path)
        self.total_path = entire_path
        self.relative_path = os.path.relpath(entire_path)
        self.relative_subpath = os.path.relpath(self.path)

        # Handle project name conflicts
        if not os.path.exists(self.relative_path):
            self.signal_saved_project.emit()
            self.validate = True
            self.close()
            return entire_path

        # Project already exists - handle based on user mode
        if self.config.get_user_mode():
            message_already_exists()
            return None

        # Confirm project overwrite
        msgtext = (
            f"Do you really want to overwrite the {file_name} "
            f"project?\nThis action will delete all contents "
            f"inside this folder!"
        )
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        reply = msg.question(
            self,
            "populse_mia - Warning: Overwriting project",
            msgtext,
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.validate = True
            self.close()
            return entire_path

        return None


class PopUpSeeAllProjects(QDialog):
    """
    A dialog window for displaying and managing saved projects.

    This dialog allows users to view a list of saved projects,
    check their existence, and open a selected project.

    .. Methods:
        - checkState: Checks if the project still exists and returns the
                      corresponding icon
        - item_to_path: Returns the path of the first selected item
        - open_project: Switches to the selected project

    """

    def __init__(self, saved_projects, main_window):
        """
        Initialize the PopUpSeeAllProjects dialog.

        :param saved_projects: Container with a list of project paths.
        :param main_window: Main window.

        """
        super().__init__()
        self.mainWindow = main_window
        self.setWindowTitle("See all saved projects")
        self.setMinimumWidth(500)
        # Create and configure widgets
        self.label = QLabel("List of Saved Projects")
        self.treeWidget = QTreeWidget()
        self.treeWidget.setColumnCount(3)
        self.treeWidget.setHeaderLabels(["Name", "Path", "State"])

        for path in saved_projects.pathsList:
            item = QTreeWidgetItem()
            item.setText(0, os.path.basename(path))
            item.setText(1, os.path.abspath(path))
            item.setIcon(2, self.checkState(path))
            self.treeWidget.addTopLevelItem(item)

        header = self.treeWidget.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # Create buttons
        self.pushButtonOpenProject = QPushButton("Open project")
        self.pushButtonOpenProject.setObjectName("pushButton_ok")
        self.pushButtonOpenProject.clicked.connect(self.open_project)
        self.pushButtonCancel = QPushButton("Cancel")
        self.pushButtonCancel.setObjectName("pushButton_cancel")
        self.pushButtonCancel.clicked.connect(self.close)
        # Button layout
        self.hBoxButtons = QHBoxLayout()
        self.hBoxButtons.addStretch(1)
        self.hBoxButtons.addWidget(self.pushButtonOpenProject)
        self.hBoxButtons.addWidget(self.pushButtonCancel)
        # Main vertical layout
        self.vBox = QVBoxLayout()
        self.vBox.addWidget(self.label)
        self.vBox.addWidget(self.treeWidget)
        self.vBox.addLayout(self.hBoxButtons)
        self.setLayout(self.vBox)

    def checkState(self, path):
        """
        Determine the icon based on project existence.

        :param path (str): Path to the project directory.

        :return: QIcon: Green checkmark if project exists, red cross if not.
        """
        sources_images_dir = Config().getSourceImageDir()
        icon_name = "green_v.png" if os.path.exists(path) else "red_cross.png"
        return QtGui.QIcon(os.path.join(sources_images_dir, icon_name))

    def item_to_path(self):
        """
        Returns the path of the first selected item.

        :return (str): Absolute path of the selected project, or empty string
                       if no selection.

        """
        selected_items = self.treeWidget.selectedItems()

        if not selected_items:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select a project to open")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()
            return ""

        return selected_items[0].text(1)

    def open_project(self):
        """
        Attempt to switch to the selected project.

        Opens the selected project in the main window if a valid project
        is chosen. Closes the dialog upon successful project switch.
        """
        file_name = self.item_to_path()

        if file_name:
            self.path, self.name = os.path.split(os.path.abspath(file_name))
            self.relative_path = os.path.relpath(file_name)

            if self.mainWindow.switch_project(self.relative_path, self.name):
                self.accept()
                self.close()


class PopUpSelectFilter(PopUpFilterSelection):
    """
    Popup window for selecting and opening a previously saved filter.

    .. Methods:
        - ok_clicked: Saves the modifications and updates the data browser.
    """

    def __init__(self, project, databrowser):
        """
        Initializes the PopUpSelectFilter dialog

        :param project (Project): The current project instance.
        :param databrowser (DataBrowser): The data browser instance.
        """
        super().__init__(project)
        self.project = project
        self.databrowser = databrowser
        self.config = Config()
        self.setWindowTitle("Open a filter")

        # Populate the filter list
        for filter_obj in self.project.filters:
            item = QListWidgetItem(filter_obj.name)
            self.list_widget_filters.addItem(item)

    def ok_clicked(self):
        """
        Saves the selected filter as the current filter and updates the
        data browser.
        """
        selected_items = self.list_widget_filters.selectedItems()

        if selected_items:
            filter_name = selected_items[0].text()
            self.project.setCurrentFilter(self.project.getFilter(filter_name))

        self.databrowser.open_filter_infos()
        self.accept()
        self.close()


class PopUpSelectIteration(QDialog):
    """
    Dialog for selecting values to iterate over when running an
    iterated pipeline.

    .. Methods:
        - ok_clicked: Stores selected values and closes the dialog.
    """

    def __init__(self, iterated_tag, tag_values):
        """
        Initializes the selection popup.

        :param iterated_tag (str): The name of the tag being iterated.
        :param tag_values (list[str]): The possible values for the
                                       iterated tag.
        """
        super().__init__()
        self.iterated_tag = iterated_tag
        self.tag_values = tag_values
        self.final_values = []
        self.setWindowTitle(
            f"Iterate pipeline run over tag {self.iterated_tag}"
        )
        self.v_box = QVBoxLayout()
        self.v_box.addWidget(QLabel("Select values to iterate over:"))
        self.check_boxes = []

        for tag_value in self.tag_values:
            check_box = QCheckBox(tag_value)
            check_box.setCheckState(QtCore.Qt.Checked)
            self.check_boxes.append(check_box)
            self.v_box.addWidget(check_box)

        self.h_box_bottom = QHBoxLayout()
        self.h_box_bottom.addStretch(1)
        # The 'OK' push button
        self.push_button_ok = QPushButton("OK")
        self.push_button_ok.setObjectName("pushButton_ok")
        self.push_button_ok.clicked.connect(self.ok_clicked)
        # The 'Cancel' push button
        self.push_button_cancel = QPushButton("Cancel")
        self.push_button_cancel.setObjectName("pushButton_cancel")
        self.push_button_cancel.clicked.connect(self.close)
        self.h_box_bottom.addWidget(self.push_button_ok)
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
        """Stores selected values and closes the dialog."""
        self.final_values = [
            cb.text() for cb in self.check_boxes if cb.isChecked()
        ]
        self.accept()
        self.close()


class PopUpTagSelection(QDialog):
    """
    A dialog for selecting and filtering tags in a data browser.

    This class provides a user interface for:
    - Displaying available tags
    - Searching through tags
    - Selecting a single tag

    Is called when the user wants to update the tags that are visualized in
       the data browser.

    .. Methods:
        - _create_button: Create a standard button with text and click handler
        - _setup_ui: Set up the user interface components
        - cancel_clicked: closes the pop-up
        - item_clicked: checks the checkbox of an item when the latter
                        is clicked
        - ok_clicked: actions when the "OK" button is clicked
        - search_str: matches the searched pattern with the tags of the
                      project
    """

    def __init__(self, project):
        """
        Initialize the tag selection dialog.

        :param project: The current project containing the database
                        with available tags
        """
        super().__init__()
        self.project = project
        _translate = QtCore.QCoreApplication.translate
        # Create UI components
        self._setup_ui(_translate)

    def _setup_ui(self, _translate):
        """
        Set up the user interface components.

        :param_translate (callable): Localization translation function
        """
        # The "Tag list" label
        self.label_tag_list = QLabel(self)
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.label_tag_list.setText(
            _translate("main_window", "Available tags:")
        )
        # The search bar to search in the list of tags
        self.search_bar = QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.search_str)
        # The list of tags
        self.list_widget_tags = QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        self.list_widget_tags.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.list_widget_tags.itemClicked.connect(self.item_clicked)
        # OK and Cancel buttons
        self.push_button_ok = self._create_button("OK", self.ok_clicked)
        self.push_button_cancel = self._create_button(
            "Cancel", self.cancel_clicked
        )
        # Top layout with label and search bar
        hbox_top_left = QHBoxLayout()
        hbox_top_left.addWidget(self.label_tag_list)
        hbox_top_left.addWidget(self.search_bar)
        # Vertical layout for top section
        vbox_top_left = QVBoxLayout()
        vbox_top_left.addLayout(hbox_top_left)
        vbox_top_left.addWidget(self.list_widget_tags)
        # Buttons layout
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)
        hbox_buttons.addWidget(self.push_button_cancel)
        # Final vertical layout
        vbox_final = QVBoxLayout()
        vbox_final.addLayout(vbox_top_left)
        vbox_final.addLayout(hbox_buttons)
        self.setLayout(vbox_final)

    def _create_button(self, text, clicked_handler):
        """
        Create a standard button with text and click handler.

        :param text (str): Button text
        :param clicked_handler (callable): Function to call when button
                                           is clicked

        :return (QPushButton): Configured button
        """
        button = QPushButton(self)
        button.setObjectName(f"pushButton_{text}")
        button.setText(text)
        button.clicked.connect(clicked_handler)
        return button

    def cancel_clicked(self):
        """Close the dialog without selecting a tag."""
        self.close()

    def item_clicked(self, item):
        """
        Handle item selection by checking/unchecking tags.

        :param (QListWidgetItem): The clicked list item
        """

        for idx in range(self.list_widget_tags.count()):
            itm = self.list_widget_tags.item(idx)
            itm.setCheckState(
                QtCore.Qt.Checked if itm == item else QtCore.Qt.Unchecked
            )

    def ok_clicked(self):
        """
        Placeholder method to be overridden by subclasses.

        Defines actions to take when the OK button is clicked.
        """
        # Has to be override in the PopUpSelectTag* classes
        pass

    def search_str(self, str_search):
        """
        Filter tags based on search term.


        :param str_search (str): Text to search for in tag names

        """

        with self.project.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)

        # Filter tags based on search term
        filtered_tags = [
            tag
            for tag in field_names
            if tag not in [TAG_CHECKSUM, COLLECTION_HISTORY]
            and (not str_search or str_search.upper() in tag.upper())
        ]

        # Update visibility of list items
        for idx in range(self.list_widget_tags.count()):
            item = self.list_widget_tags.item(idx)
            item.setHidden(item.text() not in filtered_tags)


class PopUpSelectTag(PopUpTagSelection):
    """
    A dialog for selecting and updating the thumbnail tag in the mini viewer.

    This class allows users to choose which tag will be displayed as the
    thumbnail in the application's mini viewer. It presents a list of
    available tags and allows selecting a single tag to be used as the
    thumbnail.

    .. Methods:
        - _populate_tag_list: Populate the list widget with tags from
                              the database.
        - ok_clicked: saves the modifications and updates the mini viewer

    """

    def __init__(self, project):
        """
        Initialize the tag selection dialog.

        :param project: The current project in the software context.
        """
        super().__init__(project)
        self.project = project
        self.config = Config()

        with self.project.database.data() as database_data:
            self._populate_tag_list(
                database_data.get_field_names(COLLECTION_CURRENT)
            )

    def _populate_tag_list(self, field_names):
        """
        Populate the list widget with tags from the database.

        :param field_names (list): List of available field names/tags.
        """
        # Filter out special tags and create checkable list items
        filtered_tags = [
            tag
            for tag in field_names
            if tag not in {TAG_CHECKSUM, TAG_HISTORY}
        ]
        current_thumbnail_tag = self.config.getThumbnailTag()

        for tag in sorted(filtered_tags):
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)

            # Set initial check state based on current thumbnail tag
            check_state = (
                QtCore.Qt.Checked
                if tag == current_thumbnail_tag
                else QtCore.Qt.Unchecked
            )
            item.setCheckState(check_state)
            self.list_widget_tags.addItem(item)

        self.list_widget_tags.sortItems()

    def ok_clicked(self):
        """
        Save the selected tag and update the mini viewer.

        Finds the checked tag and sets it as the new thumbnail tag.
        Closes the dialog after selection.
        """

        for idx in range(self.list_widget_tags.count()):
            item = self.list_widget_tags.item(idx)

            if item.checkState() == QtCore.Qt.Checked:
                self.config.setThumbnailTag(item.text())
                break

        # Close the dialog
        self.accept()
        self.close()


class PopUpSelectTagCountTable(PopUpTagSelection):
    """
    A pop-up dialog for selecting a tag from a count table.

    Allows users to choose a single tag from a list of available tags,
    with an option to pre-select a specific tag.

    .. Methods:
        - ok_clicked: updates the selected tag and closes the pop-up
    """

    def __init__(self, project, tags_to_display, tag_name_checked=None):
        """
        Initialize the tag selection pop-up.

        :param project: The current project context.
        :param tags_to_display (list): List of tags to be displayed for
                                       selection.
        :param tag_name_checked (str): Optional tag to be pre-checked on
                                 initialization.
        """
        super().__init__(project)
        self.selected_tag = None
        # Filtered tags, excluding specific system tags
        filterable_tags = [
            tag
            for tag in tags_to_display
            if tag not in {TAG_CHECKSUM, TAG_HISTORY}
        ]

        # Populate list widget with checkable items
        for tag in sorted(filterable_tags):
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            # Set initial check state
            check_state = (
                QtCore.Qt.Checked
                if tag == tag_name_checked
                else QtCore.Qt.Unchecked
            )
            item.setCheckState(check_state)
            self.list_widget_tags.addItem(item)

        self.list_widget_tags.sortItems()

    def ok_clicked(self):
        """
        Determine the selected tag and close the dialog.

        Finds the first checked item and sets it as the selected tag,
        then closes the dialog.
        """

        for idx in range(self.list_widget_tags.count()):
            item = self.list_widget_tags.item(idx)

            if item.checkState() == QtCore.Qt.Checked:
                self.selected_tag = item.text()
                break

        # Close the dialog
        self.accept()
        self.close()


class PopUpShowHistory(QDialog):
    """
    A dialog for displaying the history of a document in a software pipeline.

    This class creates a popup window that provides comprehensive information
    about a specific brick (processing node) in a pipeline, including:
    - Pipeline visualization
    - Input and output parameters
    - Initialization and execution details

    The dialog allows users to:
    - View the pipeline structure
    - Inspect node details
    - Navigate between associated bricks
    - Select and highlight specific files

    .. Methods:
        - _updateio_table: fill in the input and output sections of the table
        - adjust_size: Adjust the size of the dialog based on screen
                       resolution
        - file_clicked: close the history window and select the file in the
                        data browser
        - find_associated_bricks: Find bricks associated with a given node
                                  name.
        - find_process_from_plug: Find the process and plug name from a
                                  given plug.
        - handle_pipeline_nodes: Handle pipeline nodes and initialize the
                                 pipeline visualization
        - highlight_selected_node: Highlight the selected node in the pipeline
                                   view
        - initialize_pipeline: Initialize the pipeline view using the given
                               pipeline XML.
        - io_value_is_scan: Checks if the I/O value is a scan
        - load_data: Load data from the project database
        - load_pipeline_data: Load pipeline data from the database
        - node_selected: Handle node selection and update the table.
        - select_node: Select the node in the pipeline view based on the
                       provided brick UUID
        - setup_ui: Set up the user interface components
        - update_table: Update the brick row at the bottom of the table.
        - update_table_for_single_brick: Update the table for a single brick
        - update_table_for_subpipeline: Update the table for a subpipeline
        - update_table_with_brick_data: Update the table with the brick's
                                        input and output data after processing
    """

    def __init__(self, project, brick_uuid, scan, databrowser, main_window):
        """
        Initialize the document history popup.

        :param project: Current project in the software
        :param brick_uuid (str): Unique identifier of the brick
        :param scan (str): Filename of the scan
        :param databrowser: Data browser instance
        :param main_window: Main window of the software
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
        self.setup_ui()
        self.load_data(brick_uuid, scan)

    def _updateio_table(self, io_dict, item_idx):
        """
        Populate the table's input and output sections with given
        dictionary data.

        This method dynamically creates table headers and cell widgets
        based on the input dictionary, handling nested lists and detecting
        scanned file paths.

        :param io_dict (dict): Dictionary containing input or output data
                               to be displayed. Keys represent column
                               headers, and values can be strings, lists,
                               or nested lists.
        :param item_idx (int): The starting column index for populating
                               the table

        :return (int): The updated column index after processing the
                       dictionary.
        """

        for key, value in sorted(io_dict.items()):
            item = QTableWidgetItem(key)
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
                    v_layout.setAlignment(
                        QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
                    )
                    widget.setLayout(v_layout)
                    self.table.setCellWidget(0, item_idx, widget)

                else:
                    widget = QWidget()
                    v_layout = QVBoxLayout()
                    v_layout.setAlignment(
                        QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
                    )
                    label = QLabel(str(value))
                    v_layout.addWidget(label)
                    widget.setLayout(v_layout)
                    self.table.setCellWidget(0, item_idx, widget)

            item_idx += 1

        return item_idx

    def adjust_size(self):
        """Adjust the size of the dialog based on screen resolution."""
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
        """
        Find bricks associated with a given node name.

        :param node_name (str): The name of the node to find associated
                                bricks for.

        :return (dict): A dictionary where the keys are the full brick
                        names and the values are lists of associated UUIDs.
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
                bricks.setdefault(full_brick_name, []).append(uuid)

        return bricks

    def find_process_from_plug(self, plug):
        """
        Find the process and plug name from a given plug.

        :param plug (Plug): The plug object to find the process and plug
                            name from.

        :return (tuple): A tuple containing the process name (str) and
                         plug name (str).
        """
        process_name = ""
        plug_name = ""

        for link in plug.links_from if plug.output else plug.links_to:
            process_name = f"{process_name}.{link[2].name}"
            plug_name = link[1]

            if isinstance(link[2], PipelineNode):
                sub_process_name, plug_name = self.find_process_from_plug(
                    link[2].plugs[link[1]]
                )
                process_name += sub_process_name

            break

        return process_name, plug_name

    def handle_pipeline_nodes(self, pipeline, full_brick_name):
        """
        Handle pipeline nodes, set up the view, and initialize the
        pipeline visualization.

        :param pipeline (Pipeline): The pipeline object containing the
                                    nodes to handle.
        :param full_brick_name (list): The full name of the brick, split
                                       into parts.
        """

        # handle case of pipeline node alone --> exploded view
        # (e.g. a pipeline alone and plug exported)
        if len(pipeline.nodes) == 2:

            for key, node in pipeline.nodes.items():

                if key and isinstance(node, PipelineNode):
                    pipeline = node.process
                    full_brick_name.pop(0)
                    self.unitary_pipeline = True
                    break

        if (
            not self.unitary_pipeline and pipeline.name != "CustomPipeline"
        ) or (len(full_brick_name) == 2 and full_brick_name[1] == "main"):
            full_brick_name.pop(0)
            self.unitary_pipeline = True

        self.pipeline_view = PipelineDeveloperView(
            pipeline, allow_open_controller=False
        )
        self.pipeline_view.auto_dot_node_positions()
        self.splitter.addWidget(self.pipeline_view)
        self.pipeline_view.node_clicked.connect(self.node_selected)
        self.pipeline_view.process_clicked.connect(self.node_selected)
        bricks = self.find_associated_bricks(full_brick_name[0])
        self.select_node(pipeline, bricks, full_brick_name)

    def highlight_selected_node(self, node_name):
        """
        Highlight the selected node in the pipeline view.

        :param node_name (str): The name of the node to highlight.
        """

        for name, gnode in self.pipeline_view.scene.gnodes.items():
            gnode.fonced_viewer(name != node_name)

    def initialize_pipeline(self, full_brick_name):
        """
        Initialize the pipeline view using the given pipeline XML.

        :param full_brick_name (list): The full name of the brick,
                                       split into parts.
        """
        engine = Config.get_capsul_engine()

        try:
            pipeline = engine.get_process_instance(self.pipeline_xml)

        except Exception:
            pipeline = None

        if pipeline:
            self.handle_pipeline_nodes(pipeline, full_brick_name)

    def io_value_is_scan(self, value):
        """
        Check if the I/O value is a scan.

        :param value: I/O value

        :return: The scan corresponding to the value if it exists,
         None otherwise

        """

        with self.project.database.data() as database_data:

            for scan in database_data.get_document_names(COLLECTION_CURRENT):

                if scan in str(value):
                    return scan

        return None

    def load_data(self, brick_uuid, scan):
        """
        Load data from the project database and update the table with brick
        data.

        :param brick_uuid (str): The UUID of the brick to load.
        :param scan (str): The identifier of the scan associated with the
                           brick.
        """
        with self.project.database.data() as database_data:
            brick_row = database_data.get_document(
                collection_name=COLLECTION_BRICK, primary_keys=brick_uuid
            )
            full_brick_name = database_data.get_value(
                collection_name=COLLECTION_BRICK,
                primary_key=brick_uuid,
                field=BRICK_NAME,
            ).split(".")
            history_uuid = database_data.get_value(
                collection_name=COLLECTION_CURRENT,
                primary_key=scan,
                field=TAG_HISTORY,
            )

        self.unitary_pipeline = False
        self.uuid_idx = 0

        if history_uuid:
            self.load_pipeline_data(history_uuid, full_brick_name)

        self.update_table_with_brick_data(brick_row, full_brick_name)

    def load_pipeline_data(self, history_uuid, full_brick_name):
        """
        Load pipeline data from the database based on the provided
        history UUID.

        :param history_uuid (str): The UUID of the history record to load
                                   pipeline data from.
        :param full_brick_name (list): The full name of the brick, split
                                       into parts.
        """

        with self.project.database.data() as database_data:
            self.pipeline_xml = database_data.get_value(
                collection_name=COLLECTION_HISTORY,
                primary_key=history_uuid,
                field=HISTORY_PIPELINE,
            )

            if self.pipeline_xml:
                self.brick_list = database_data.get_value(
                    collection_name=COLLECTION_HISTORY,
                    primary_key=history_uuid,
                    field=HISTORY_BRICKS,
                )
                self.initialize_pipeline(full_brick_name)

    def node_selected(self, node_name, process):
        """
        Handle node selection and update the table.

        :param node_name: node name
        :param process: process of the corresponding node
        """

        if hasattr(process, "pipeline_node"):
            process = process.pipeline_node

        bricks = self.find_associated_bricks(node_name)
        full_node_name = getattr(process, "full_name", "")

        if node_name not in full_node_name:
            full_node_name = ""

        if bricks:

            if len(bricks) == 1:
                self.update_table_for_single_brick(
                    bricks, node_name, full_node_name
                )

            else:
                self.update_table_for_subpipeline(
                    bricks, process, full_node_name
                )

        self.highlight_selected_node(node_name)

    def select_node(self, pipeline, bricks, full_brick_name):
        """
        Select the node in the pipeline view based on the provided brick UUID.

        :param pipeline (Pipeline): The pipeline object containing the
                                    nodes to handle.
        :param bricks (dict): A dictionary of bricks with UUIDs as values.
        :param full_brick_name (list): The full name of the brick, split into
                                       parts.
        """

        for bricks_uuids in bricks.values():

            if bricks_uuids[self.uuid_idx] == full_brick_name[0]:
                break

        selected_name = full_brick_name[0]

        try:
            self.node_selected(selected_name, pipeline.nodes[selected_name])

        except Exception as e:
            logger.warning(
                f"Error in naming association brick/pipeline, "
                f"cannot select node: {e}"
            )

    def setup_ui(self):
        """Set up the user interface components."""
        self.layout = QVBoxLayout()
        self.splitter = QSplitter(QtCore.Qt.Vertical)
        self.table = QTableWidget()
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
        self.adjust_size()

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
        """
        Updates the table with information about a brick's execution state.

        :param inputs (dict): Dictionary containing input data.
        :param outputs (dict): Dictionary containing output data.
        :param brick_name (str): Name of the brick.
        :param init (str, optional): Initialization status.
        :param init_time (Any, optional): Initialization timestamp.
        :param exec (str, optional): Execution status.
        :param exec_time (Any, optional): Execution timestamp.

        :Contains:
            - create_cell_widget: Creates a QWidget containing a vertically
                                  aligned QLabel
        """
        self.table.clear()
        self.table.setRowCount(1)
        column_count = (
            1
            + (2 if init else 0)
            + (2 if exec else 0)
            + len(inputs)
            + len(outputs)
        )
        self.table.setColumnCount(column_count)

        def create_cell_widget(text):
            """
            Creates a QWidget containing a vertically aligned QLabel with
            the given text.

            :param text (str): The text to display in the QLabel.

            :return (QWidget): A QWidget containing a QLabel with the
                               specified text, aligned to the top within
                               a vertical layout.
            """
            widget = QWidget()
            layout = QVBoxLayout()
            layout.setAlignment(QtCore.Qt.AlignTop)
            layout.addWidget(QLabel(text))
            widget.setLayout(layout)
            return widget

        # Brick name column
        item_idx = 0
        self.table.setHorizontalHeaderItem(
            item_idx, QTableWidgetItem(BRICK_NAME)
        )
        self.table.setCellWidget(0, item_idx, create_cell_widget(brick_name))
        item_idx += 1

        # Brick initialization columns
        if init:
            self.table.setHorizontalHeaderItem(
                item_idx, QTableWidgetItem(BRICK_INIT)
            )
            self.table.setCellWidget(0, item_idx, create_cell_widget(init))
            item_idx += 1
            self.table.setHorizontalHeaderItem(
                item_idx, QTableWidgetItem(BRICK_INIT_TIME)
            )
            self.table.setCellWidget(
                0,
                item_idx,
                create_cell_widget(str(init_time) if init_time else ""),
            )
            item_idx += 1

        # Brick execution columns
        if exec:
            self.table.setHorizontalHeaderItem(
                item_idx, QTableWidgetItem(BRICK_EXEC)
            )
            self.table.setCellWidget(0, item_idx, create_cell_widget(exec))
            item_idx += 1
            self.table.setHorizontalHeaderItem(
                item_idx, QTableWidgetItem(BRICK_EXEC_TIME)
            )
            self.table.setCellWidget(
                0,
                item_idx,
                create_cell_widget(str(exec_time) if exec_time else ""),
            )
            item_idx += 1

        # Update inputs and outputs
        item_idx = self._updateio_table(inputs, item_idx)
        _ = self._updateio_table(outputs, item_idx)
        # Final table adjustments
        self.table.verticalHeader().setMinimumSectionSize(30)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def update_table_for_single_brick(self, bricks, node_name, full_node_name):
        """
        Update the table for a single brick, using the provided brick data.

        :param bricks (dict): A dictionary of bricks with UUIDs as values.
        :param node_name (str): The name of the node associated with the
                                brick.
        :param full_node_name (list): The full name of the node, split
                                      into parts.
        """

        with self.project.database.data() as database_data:
            brick_row = database_data.get_document(
                collection_name=COLLECTION_BRICK,
                primary_keys=next(iter(bricks.values()))[self.uuid_idx],
            )

        inputs = brick_row[0][BRICK_INPUTS]
        outputs = brick_row[0][BRICK_OUTPUTS]

        for param in self.banished_param:
            outputs.pop(param, None)
            inputs.pop(param, None)

        brick_name = brick_row[0][BRICK_NAME]
        init = brick_row[0][BRICK_INIT]
        init_time = brick_row[0][BRICK_INIT_TIME]
        exec = brick_row[0][BRICK_INIT]
        exec_time = brick_row[0][BRICK_INIT_TIME]
        self.update_table(
            inputs, outputs, brick_name, init, init_time, exec, exec_time
        )

    def update_table_for_subpipeline(self, bricks, process, full_node_name):
        """
        Update the table for a subpipeline based on the given process and
        brick data.

        :param bricks (dict): A dictionary of bricks with UUIDs as values.
        :param process (PipelineNode): The process node associated with the
                                       subpipeline.
        :param full_node_name (list): The full name of the node, split into
                                      parts.
        """
        inputs_dict = {}
        outputs_dict = {}

        if isinstance(process, PipelineNode):

            with self.project.database.data() as database_data:

                for plug_name, plug in process.plugs.items():

                    if plug.activated:
                        process_result = self.find_process_from_plug(plug)
                        process_name = process_result[0]
                        inner_plug_name = process_result[1]

                        for uuid in bricks.values():
                            full_brick_name = database_data.get_value(
                                collection_name=COLLECTION_BRICK,
                                primary_key=uuid[0],
                                field=BRICK_NAME,
                            )

                            if full_brick_name == (
                                f"{full_node_name}{process_name}"
                            ):
                                plugs = database_data.get_value(
                                    collection_name=COLLECTION_BRICK,
                                    primary_key=uuid[self.uuid_idx],
                                    field=(
                                        BRICK_OUTPUTS
                                        if plug.output
                                        else BRICK_INPUTS
                                    ),
                                )
                                (outputs_dict if plug.output else inputs_dict)[
                                    plug_name
                                ] = plugs[inner_plug_name]

        for param in self.banished_param:
            outputs_dict.pop(param, None)
            inputs_dict.pop(param, None)

        self.update_table(inputs_dict, outputs_dict, full_node_name)

    def update_table_with_brick_data(self, brick_row, full_brick_name):
        """
        Update the table with the brick's input and output data after
        processing.

        :param brick_row (list): A list containing the brick data to update
                                 the table with.
        :param full_brick_name (list): The full name of the brick, split into
                                       parts.
        """
        inputs = brick_row[0][BRICK_INPUTS]
        outputs = brick_row[0][BRICK_OUTPUTS]

        for param in self.banished_param:
            outputs.pop(param, None)
            inputs.pop(param, None)

        brick_name = brick_row[0][BRICK_NAME]
        init = brick_row[0][BRICK_INIT]
        init_time = brick_row[0][BRICK_INIT_TIME]
        exec = brick_row[0][BRICK_INIT]
        exec_time = brick_row[0][BRICK_INIT_TIME]
        self.update_table(
            inputs, outputs, brick_name, init, init_time, exec, exec_time
        )
        self.splitter.addWidget(self.table)


class PopUpVisualizedTags(QWidget):
    """
    A widget for managing tag visualization preferences in a project.

    This class provides an interface for users to select and unselect tags
    to be displayed in the project. It allows searching through available tags
    and moving them between available and visualized lists.

    .. Methods:
        - _create_button: Create a customized QPushButton with specified
                          properties
        - _create_button_layout: Create the layout for selection buttons
        - _create_label: Create a customized QLabel with specified properties
        - _create_left_layout: Create the layout for available tags
        - _create_right_layout: Create the layout for visualized tags
        - _create_search_bar: Create the search bar with placeholder and
                              connection
        - _create_tag_list: Create a QListWidget configured for
                            multi-selection of tags
        - _populate_tags: Populate the tags list from the project database
        - _setup_ui: Create and layout the user interface components
        - search_str: Matches the searched pattern with the tags of the project
        - click_select_tag: Puts the selected tags in the "selected tag" table
        - click_unselect_tag: removes the unselected tags from populse_mia
                              "selected tag" table

    .. Signals:
        - signal_preferences_change (QtCore.pyqtSignal): Emitted when tag
                                                         visualization
                                                         preferences are
                                                         modified.
    """

    # Signal to indicate preference changes
    signal_preferences_change = QtCore.pyqtSignal()

    def __init__(self, project, visualized_tags):
        """
        Initialize the tag visualization management widget.

        :param project: The current project in the software.
        :param visualized_tags: Tags currently being visualized before
                                opening this widget.
        """
        super().__init__()
        self.project = project
        self.visualized_tags = visualized_tags
        self._translate = QtCore.QCoreApplication.translate
        # Track available (non-visualized) tags
        self.left_tags = []
        # Setup the user interface
        self._setup_ui()
        self._populate_tags()

    def _create_button(self, object_name, text, click_handler):
        """
        Create a customized QPushButton with specified properties.

        This method instantiates a QPushButton, sets its object name,
        translates and sets its text, and connects a click event handler.

        :param object_name (str): The unique identifier name for the button.
        :param text (str): The text to be displayed on the button, will
                           be translated.
        :param click_handler (callable): The function to be called when the
                                         button is clicked.

        :return (QPushButton): A configured button with the specified
                               properties.
        """
        button = QPushButton(self)
        button.setObjectName(object_name)
        button.setText(self._translate("main_window", text))
        button.clicked.connect(click_handler)
        return button

    def _create_button_layout(self):
        """Create the layout for selection buttons."""
        layout = QVBoxLayout()
        layout.addWidget(self.push_button_select_tag)
        layout.addWidget(self.push_button_unselect_tag)
        return layout

    def _create_label(self, object_name, text):
        """
        Create a customized QLabel with specified properties.

        This method instantiates a QLabel, sets its text format,
        object name, and translates its text.

        :param object_name (str): The unique identifier name for the label.
        :param text (str): The text to be displayed on the label, will be
                           translated.

        :return (QLabel): A configured label with the specified properties.
        """
        label = QLabel(self)
        label.setTextFormat(QtCore.Qt.AutoText)
        label.setObjectName(object_name)
        label.setText(self._translate("main_window", text))
        return label

    def _create_left_layout(self):
        """Create the layout for available tags."""
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.label_tag_list)
        top_layout.addWidget(self.search_bar)
        layout.addLayout(top_layout)
        layout.addWidget(self.list_widget_tags)
        return layout

    def _create_right_layout(self):
        """Create the layout for visualized tags."""
        layout = QVBoxLayout()
        layout.addWidget(self.label_visualized_tags)
        layout.addWidget(self.list_widget_selected_tags)
        return layout

    def _create_search_bar(self):
        """Create the search bar with placeholder and connection."""
        search_bar = QLineEdit(self)
        search_bar.setObjectName("lineEdit_search_bar")
        search_bar.setPlaceholderText("Search")
        search_bar.textChanged.connect(self.search_str)
        return search_bar

    def _create_tag_list(self, text=""):
        """
        Create a QListWidget configured for multi-selection of tags.

        This method initializes a QListWidget with multi-selection mode
        nabled, allowing users to select multiple items simultaneously.
        The list widget is assigned a unique object name based on the
        optional text parameter.

        :param text (str): A prefix used to create a unique object name
                           for the QListWidget.

        :return (QListWidget): A configured QListWidget with multi-selection
                               mode enabled.
        """
        tag_list = QListWidget(self)
        tag_list.setObjectName(f"listWidget_{text}tags")
        tag_list.setSelectionMode(QAbstractItemView.MultiSelection)
        return tag_list

    def _populate_tags(self):
        """Populate the tags list from the project database."""
        excluded_tags = {TAG_CHECKSUM, TAG_FILENAME, TAG_HISTORY}

        with self.project.database.data() as database_data:

            for tag in database_data.get_field_names(COLLECTION_CURRENT):

                if tag not in excluded_tags:
                    item = QListWidgetItem(tag)

                    if tag not in self.visualized_tags:
                        # Tag not visible: left side
                        self.list_widget_tags.addItem(item)
                        self.left_tags.append(tag)

                    else:
                        # Tag visible: right side
                        self.list_widget_selected_tags.addItem(item)

            self.list_widget_tags.sortItems()

    def _setup_ui(self):
        """Create and layout the user interface components."""
        # Selection buttons
        self.push_button_select_tag = self._create_button(
            "pushButton_select_tag", "-->", self.click_select_tag
        )
        self.push_button_unselect_tag = self._create_button(
            "pushButton_unselect_tag", "<--", self.click_unselect_tag
        )
        # Available tags section
        self.label_tag_list = self._create_label(
            "label_tag_list", "Available tags:"
        )
        self.search_bar = self._create_search_bar()
        self.list_widget_tags = self._create_tag_list()
        # Visualized tags section
        self.label_visualized_tags = self._create_label(
            "label_visualized_tags", "Visualized tags:"
        )
        self.list_widget_selected_tags = self._create_tag_list("visualized_")
        main_layout = QHBoxLayout()
        main_layout.addLayout(self._create_left_layout())
        main_layout.addLayout(self._create_button_layout())
        main_layout.addLayout(self._create_right_layout())
        self.setLayout(main_layout)

    def search_str(self, str_search):
        """
        Filter tags based on search string.

        :param str_search (str): Search pattern to match against tags
        """

        # Find matching tags, case-insensitive
        return_list = [
            tag
            for tag in self.left_tags
            if not str_search or str_search.upper() in tag.upper()
        ]
        # Selection updated
        self.list_widget_tags.clear()

        for tag_name in return_list:
            item = QListWidgetItem(tag_name)
            self.list_widget_tags.addItem(item)

        self.list_widget_tags.sortItems()

    def click_select_tag(self):
        """
        Move selected tags from available to visualized list.

        Removes selected tags from the left (available) list and
        adds them to the right (visualized) list.
        """

        rows = sorted(
            [index.row() for index in self.list_widget_tags.selectedIndexes()],
            reverse=True,
        )

        for row in rows:
            tag_item = self.list_widget_tags.takeItem(row)
            tag_text = tag_item.text()
            # assuming the other listWidget is called listWidget_2
            self.left_tags.remove(tag_text)
            self.list_widget_selected_tags.addItem(tag_text)

        # Emit signal to indicate preferences have changed
        self.signal_preferences_change.emit()

    def click_unselect_tag(self):
        """
        Remove selected tags from the visualized list and
        return them to the available tags list.

        Moves selected tags from the right (visualized) list
        to the left (available) list, maintaining sorted order.
        """

        rows = sorted(
            [
                index.row()
                for index in self.list_widget_selected_tags.selectedIndexes()
            ],
            reverse=True,
        )

        for row in rows:
            # Add tag back to left tags and available list
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
    """
    A custom QLabel that emits a clicked signal when mouse pressed.

    This class extends the standard QLabel to provide a signal that can be
    connected to other methods when the label is clicked, enabling more
    interactive label behaviors.

     .. Signals:
        - clicked (pyqtSignal): Signal emitted when the label is clicked.
    """

    clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialize the clickable label.

        :param parent (QWidget): Parent widget.
        """
        super().__init__(parent)

    def mousePressEvent(self, event):
        """
        Override the default mouse press event to emit the clicked signal.

        :parm event (QMouseEvent): Mouse press event details.
        """
        self.clicked.emit()
        super().mousePressEvent(event)
