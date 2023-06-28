# -*- coding: utf-8 -*-
""" Module that defines all the pop-ups used across the software

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
import os
import platform
import shutil
import subprocess
from datetime import datetime
from functools import partial

import yaml

# Capsul imports
from capsul.api import capsul_engine
from capsul.pipeline.pipeline_nodes import PipelineNode
from capsul.qt_gui.widgets.pipeline_developer_view import PipelineDeveloperView
from capsul.qt_gui.widgets.settings_editor import SettingsEditor

# Populse_db imports
from populse_db.database import (
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
)

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
from populse_mia.data_manager.database_mia import (
    TAG_ORIGIN_USER,
    TAG_UNIT_DEGREE,
    TAG_UNIT_HZPIXEL,
    TAG_UNIT_MHZ,
    TAG_UNIT_MM,
    TAG_UNIT_MS,
)
from populse_mia.data_manager.project import (
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
    HISTORY_BRICKS,
    HISTORY_PIPELINE,
    TAG_CHECKSUM,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_TYPE,
    TYPE_MAT,
    TYPE_NII,
    TYPE_TXT,
    TYPE_UNKNOWN,
    Project,
)
from populse_mia.software_properties import Config, verCmp
from populse_mia.user_interface.data_browser import data_browser
from populse_mia.utils import utils
from populse_mia.utils.utils import check_value_type


class ClickableLabel(QLabel):
    """
    QLabel with a clicked signal

    .. Methods:
        - mousePressEvent: overrides the mousePressEvent method by emitting
          the clicked signal
    """

    # Signal that will be emitted when the widget is clicked
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

    def mousePressEvent(self, event):
        """
        Overrides the mousePressEvent method by emitting the clicked signal

        :param event: clicked event
        """
        self.clicked.emit()


class DefaultValueListCreation(QDialog):
    """Widget that is called when to create a list's default value.

    .. Methods:
        - add_element: one more element added to the list
        - default_init_table: default init table when no previous value
        - remove_element: removes the last element of the list
        - resize_table: to resize the pop up depending on the table
        - update_default_value: checks if the values are correct and updates
           the parent value

    """

    def __init__(self, parent, type):
        """Initialization.

        :param parent: the DefaultValueQLineEdit parent object
        :param type: type of the list (e.g. list of int, list of float, etc.)

        """

        super().__init__()

        self.setModal(True)

        # Current type chosen
        self.type = type

        self.parent = parent
        self.setWindowTitle("Adding a " + self.type.replace("_", " of "))

        # The table that will be filled
        self.table = QtWidgets.QTableWidget()
        self.table.setRowCount(1)

        value = self.parent.text()

        if value != "":
            try:
                list_value = ast.literal_eval(value)

                if isinstance(list_value, list):
                    # If the previous value was already a list, we fill it
                    self.table.setColumnCount(len(list_value))

                    for i in range(0, self.table.columnCount()):
                        item = QtWidgets.QTableWidgetItem()
                        item.setText(str(list_value[i]))
                        self.table.setItem(0, i, item)

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
        add_element_picture = QtGui.QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "green_plus.png"))
        )
        add_element_picture = add_element_picture.scaledToHeight(15)
        self.add_element_label.setPixmap(add_element_picture)
        self.add_element_label.clicked.connect(self.add_element)

        # Button to remove the last element of the list
        self.remove_element_label = ClickableLabel()
        self.remove_element_label.setObjectName("minus")
        remove_element_picture = QtGui.QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "red_minus.png"))
        )
        remove_element_picture = remove_element_picture.scaledToHeight(20)
        self.remove_element_label.setPixmap(remove_element_picture)
        self.remove_element_label.clicked.connect(self.remove_element)

        # Layouts
        self.v_box_final = QVBoxLayout()
        self.h_box_final = QHBoxLayout()
        self.list_layout = QHBoxLayout()

        self.h_box_final.addWidget(self.ok_button)
        self.h_box_final.addWidget(cancel_button)

        self.list_layout.addWidget(self.table)
        self.list_layout.addWidget(self.remove_element_label)
        self.list_layout.addWidget(self.add_element_label)

        self.v_box_final.addLayout(self.list_layout)
        self.v_box_final.addLayout(self.h_box_final)

        self.setLayout(self.v_box_final)

    def add_element(self):
        """One more element added to the list."""

        self.table.setColumnCount(self.table.columnCount() + 1)
        item = QtWidgets.QTableWidgetItem()
        self.table.setItem(0, self.table.columnCount() - 1, item)
        self.resize_table()

    def default_init_table(self):
        """
        Default init table when no previous value
        """

        # Table filled with a single element at the beginning if no value
        self.table.setColumnCount(1)
        item = QtWidgets.QTableWidgetItem()
        self.table.setItem(0, 0, item)

    def remove_element(self):
        """Removes the last element of the list."""

        if self.table.columnCount() > 1:
            self.table.setColumnCount(self.table.columnCount() - 1)
            self.resize_table()
            self.adjustSize()

    def resize_table(self):
        """To resize the pop up depending on the table."""

        self.table.resizeColumnsToContents()
        total_width = 0
        total_height = 0
        i = 0
        while i < self.table.columnCount():
            total_width += self.table.columnWidth(i)
            total_height += self.table.rowHeight(i)
            i += 1
        if total_width + 20 < 900:
            self.table.setFixedWidth(total_width + 20)
            self.table.setFixedHeight(total_height + 25)
        else:
            self.table.setFixedWidth(900)
            self.table.setFixedHeight(total_height + 40)

    def update_default_value(self):
        """Checks if the values are correct and updates the parent value."""

        database_value = []
        valid_values = True

        # For each value
        for i in range(0, self.table.columnCount()):
            item = self.table.item(0, i)
            text = item.text()

            try:
                if self.type == FIELD_TYPE_LIST_INTEGER:
                    database_value.append(int(text))
                elif self.type == FIELD_TYPE_LIST_FLOAT:
                    database_value.append(float(text))
                elif self.type == FIELD_TYPE_LIST_BOOLEAN:
                    if text == "True":
                        database_value.append(True)
                    elif text == "False":
                        database_value.append(False)
                    else:
                        raise ValueError("Not a boolean value")
                elif self.type == FIELD_TYPE_LIST_STRING:
                    database_value.append(str(text))
                elif self.type == FIELD_TYPE_LIST_DATE:
                    format = "%d/%m/%Y"
                    datetime.strptime(text, format).date()
                    database_value.append(text)
                elif self.type == FIELD_TYPE_LIST_DATETIME:
                    format = "%d/%m/%Y %H:%M:%S.%f"
                    datetime.strptime(text, format)
                    database_value.append(text)
                elif self.type == FIELD_TYPE_LIST_TIME:
                    format = "%H:%M:%S.%f"
                    datetime.strptime(text, format).time()
                    database_value.append(text)

            except Exception:
                # Error if invalid value
                valid_values = False
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Invalid value")
                msg.setInformativeText(
                    "The value "
                    + text
                    + " is invalid with the type "
                    + self.type
                )
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                break

        if valid_values:
            self.parent.setText(str(database_value))
            self.close()


class DefaultValueQLineEdit(QtWidgets.QLineEdit):
    """Overrides the QLineEdit for the default value.

    We need to override the mousePressEvent.

    .. Methods:
        - mousePressEvent: mouse pressed on the QLineEdit

    """

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def mousePressEvent(self, event):
        """Mouse pressed on the QLineEdit.

        :param event: used ?

        """

        if self.parent.type.startswith("list_"):
            # We display the pop up to create the list if the checkbox is
            # checked, otherwise we do nothing
            self.list_creation = DefaultValueListCreation(
                self, self.parent.type
            )
            self.list_creation.show()


class PopUpAddPath(QDialog):
    """Is called when the user wants to add a document to the project
       without importing from MRI Files Manager (File > Import).

    .. Methods:
        - file_to_choose: lets the user choose a file to import
        - find_type: tries to find the document type when the document is
           changed
        - save_path: adds the path to the database and the data browser

    """

    def __init__(self, project, databrowser):
        """Initialization of the PopUp AddPath.

        :param project: current project in the software
        :param databrowser: data browser instance of the software

        """

        super().__init__()
        self.project = project
        self.databrowser = databrowser
        self.setWindowTitle("Add a document")
        self.setModal(True)

        vbox_layout = QVBoxLayout()

        hbox_layout = QHBoxLayout()
        file_label = QLabel("File: ")
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setFixedWidth(300)
        self.file_line_edit.textChanged.connect(self.find_type)
        file_button = QPushButton("Choose a document")
        file_button.clicked.connect(self.file_to_choose)
        hbox_layout.addWidget(file_label)
        hbox_layout.addWidget(self.file_line_edit)
        hbox_layout.addWidget(file_button)
        vbox_layout.addLayout(hbox_layout)

        hbox_layout = QHBoxLayout()
        type_label = QLabel("Type: ")
        self.type_line_edit = QLineEdit()
        hbox_layout.addWidget(type_label)
        hbox_layout.addWidget(self.type_line_edit)
        vbox_layout.addLayout(hbox_layout)

        hbox_layout = QHBoxLayout()
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.save_path)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        hbox_layout.addWidget(self.ok_button)
        hbox_layout.addWidget(cancel_button)
        vbox_layout.addLayout(hbox_layout)
        self.setLayout(vbox_layout)

    def file_to_choose(self):
        """Lets the user choose a file to import."""

        fname, _ = QFileDialog.getOpenFileNames(
            self, "Choose a document to import", os.path.expanduser("~")
        )

        if fname != []:
            self.file_line_edit.setText(str(fname))

    def find_type(self):
        """Tries to find the document type when the document is changed."""

        new_file = self.file_line_edit.text()
        new_file = ast.literal_eval(new_file)
        new_type = []

        for elmt in new_file:
            filename, file_extension = os.path.splitext(elmt)

            if file_extension == ".nii":
                new_type.append(TYPE_NII)

            elif file_extension == ".mat":
                new_type.append(TYPE_MAT)

            elif file_extension == ".txt":
                new_type.append(TYPE_TXT)

            else:
                new_type.append(TYPE_UNKNOWN)

        self.type_line_edit.setText(str(new_type))

    def save_path(self):
        """Adds the path to the database and the data browser."""

        path_list = self.file_line_edit.text()

        if path_list != "":
            path_list = ast.literal_eval(path_list)

        else:
            path_list = [path_list]

        path_type_list = self.type_line_edit.text()

        if path_type_list != "":
            path_type_list = ast.literal_eval(path_type_list)

        else:
            path_type_list = [path_type_list]

        for path, path_type in zip(path_list, path_type_list):
            docInDb = [
                os.path.basename(i)
                for i in self.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )
            ]
            self.project.unsavedModifications = True

            if os.path.basename(path) in docInDb:
                self.msg = QMessageBox()
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setText("- {0} -".format(os.path.basename(path)))
                self.msg.setInformativeText(
                    "The document '{0}' \n "
                    "already exists in the Data Browser!".format(path)
                )
                self.msg.setWindowTitle("Warning: existing data!")
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.buttonClicked.connect(self.msg.close)
                self.msg.show()

            elif path != "" and os.path.exists(path) and path_type != "":
                # For history
                history_maker = []
                history_maker.append("add_scans")

                path = os.path.relpath(path)
                filename = os.path.basename(path)
                copy_path = os.path.join(
                    self.project.folder, "data", "downloaded_data", filename
                )
                shutil.copy(path, copy_path)
                with open(path, "rb") as scan_file:
                    data = scan_file.read()
                    checksum = hashlib.md5(data).hexdigest()
                path = os.path.join("data", "downloaded_data", filename)
                self.project.session.add_document(COLLECTION_CURRENT, path)
                self.project.session.add_document(COLLECTION_INITIAL, path)
                values_added = []
                self.project.session.add_value(
                    COLLECTION_INITIAL, path, TAG_TYPE, path_type
                )
                self.project.session.add_value(
                    COLLECTION_CURRENT, path, TAG_TYPE, path_type
                )
                values_added.append([path, TAG_TYPE, path_type, path_type])
                self.project.session.add_value(
                    COLLECTION_INITIAL, path, TAG_CHECKSUM, checksum
                )
                self.project.session.add_value(
                    COLLECTION_CURRENT, path, TAG_CHECKSUM, checksum
                )
                values_added.append([path, TAG_CHECKSUM, checksum, checksum])

                # For history
                history_maker.append([path])
                history_maker.append(values_added)
                self.project.undos.append(history_maker)
                self.project.redos.clear()

                # Databrowser updated

                (
                    self.databrowser.table_data.scans_to_visualize
                ) = self.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )

                (
                    self.databrowser.table_data.scans_to_search
                ) = self.project.session.get_documents_names(
                    COLLECTION_CURRENT
                )
                self.databrowser.table_data.add_columns()
                self.databrowser.table_data.fill_headers()
                self.databrowser.table_data.add_rows([path])
                self.databrowser.reset_search_bar()
                self.databrowser.frame_advanced_search.setHidden(True)
                self.databrowser.advanced_search.rows = []
                self.close()
            else:
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


class PopUpAddTag(QDialog):
    """Is called when the user wants to add a tag to the project.

    .. Methods:
        - ok_action: verifies that each field is correct and send the new tag
           to the data browser
        - on_activated: type updated

    """

    # Signal that will be emitted at the end to tell that the project
    # has been created
    signal_add_tag = pyqtSignal()

    def __init__(self, databrowser, project):
        """Initialization.

        :param project: current project in the software
        :param databrowser: data browser instance of the software
        :param type: type of the tag to add

        """

        super().__init__()
        self.project = project
        self.databrowser = databrowser
        self.type = FIELD_TYPE_STRING  # Type is string by default

        self.setObjectName("Add a tag")

        # The 'OK' push button
        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setObjectName("push_button_ok")

        # The 'Tag name' label
        self.label_tag_name = QtWidgets.QLabel(self)
        self.label_tag_name.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_name.setObjectName("tag_name")

        # The 'Tag name' text edit
        self.text_edit_tag_name = QtWidgets.QLineEdit(self)
        self.text_edit_tag_name.setObjectName("textEdit_tag_name")

        # The 'Default value' label
        self.label_default_value = QtWidgets.QLabel(self)
        self.label_default_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_default_value.setObjectName("default_value")

        # The 'Default value' text edit
        self.text_edit_default_value = DefaultValueQLineEdit(self)
        self.text_edit_default_value.setObjectName("textEdit_default_value")
        # By default the tag is a string
        self.text_edit_default_value.setText("Undefined")

        # The 'Description value' label
        self.label_description_value = QtWidgets.QLabel(self)
        self.label_description_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_description_value.setObjectName("description_value")

        # The 'Description value' text edit
        self.text_edit_description_value = QtWidgets.QLineEdit(self)
        self.text_edit_description_value.setObjectName(
            "textEdit_" "description_value"
        )

        # The 'Unit value' label
        self.label_unit_value = QtWidgets.QLabel(self)
        self.label_unit_value.setTextFormat(QtCore.Qt.AutoText)
        self.label_unit_value.setObjectName("unit_value")

        # The 'Unit value' text edit
        self.combo_box_unit = QtWidgets.QComboBox(self)
        self.combo_box_unit.setObjectName("combo_box_unit")
        self.combo_box_unit.addItem(None)
        self.combo_box_unit.addItem(TAG_UNIT_MS)
        self.combo_box_unit.addItem(TAG_UNIT_MM)
        self.combo_box_unit.addItem(TAG_UNIT_MHZ)
        self.combo_box_unit.addItem(TAG_UNIT_HZPIXEL)
        self.combo_box_unit.addItem(TAG_UNIT_DEGREE)

        # The 'Type' label
        self.label_type = QtWidgets.QLabel(self)
        self.label_type.setTextFormat(QtCore.Qt.AutoText)
        self.label_type.setObjectName("type")

        # The 'Type' text edit
        self.combo_box_type = QtWidgets.QComboBox(self)
        self.combo_box_type.setObjectName("combo_box_type")
        self.combo_box_type.addItem("String")
        self.combo_box_type.addItem("Integer")
        self.combo_box_type.addItem("Float")
        self.combo_box_type.addItem("Boolean")
        self.combo_box_type.addItem("Date")
        self.combo_box_type.addItem("Datetime")
        self.combo_box_type.addItem("Time")
        self.combo_box_type.addItem("String List")
        self.combo_box_type.addItem("Integer List")
        self.combo_box_type.addItem("Float List")
        self.combo_box_type.addItem("Boolean List")
        self.combo_box_type.addItem("Date List")
        self.combo_box_type.addItem("Datetime List")
        self.combo_box_type.addItem("Time List")
        self.combo_box_type.currentTextChanged.connect(self.on_activated)

        # Layouts
        v_box_labels = QVBoxLayout()
        v_box_labels.addWidget(self.label_tag_name)
        v_box_labels.addWidget(self.label_default_value)
        v_box_labels.addWidget(self.label_description_value)
        v_box_labels.addWidget(self.label_unit_value)
        v_box_labels.addWidget(self.label_type)

        v_box_edits = QVBoxLayout()
        v_box_edits.addWidget(self.text_edit_tag_name)
        default_layout = QHBoxLayout()
        default_layout.addWidget(self.text_edit_default_value)
        v_box_edits.addLayout(default_layout)
        v_box_edits.addWidget(self.text_edit_description_value)
        v_box_edits.addWidget(self.combo_box_unit)
        v_box_edits.addWidget(self.combo_box_type)

        h_box_top = QHBoxLayout()
        h_box_top.addLayout(v_box_labels)
        h_box_top.addSpacing(50)
        h_box_top.addLayout(v_box_edits)

        h_box_ok = QHBoxLayout()
        h_box_ok.addStretch(1)
        h_box_ok.addWidget(self.push_button_ok)

        v_box_total = QVBoxLayout()
        v_box_total.addLayout(h_box_top)
        v_box_total.addLayout(h_box_ok)

        self.setLayout(v_box_total)

        # Filling the title of the labels and push buttons
        _translate = QtCore.QCoreApplication.translate
        self.push_button_ok.setText(_translate("Add a tag", "OK"))
        self.label_tag_name.setText(_translate("Add a tag", "Tag name:"))
        self.label_default_value.setText(
            _translate("Add a tag", "Default value:")
        )
        self.label_description_value.setText(
            _translate("Add a tag", "Description:")
        )
        self.label_unit_value.setText(_translate("Add a tag", "Unit:"))
        self.label_type.setText(_translate("Add a tag", "Tag type:"))

        # Connecting the OK push button
        self.push_button_ok.clicked.connect(self.ok_action)

        self.setMinimumWidth(700)
        self.setWindowTitle("Add a tag")
        self.setModal(True)

    def ok_action(self):
        """Verifies that each field is correct and send the new tag
        to the data browser.

        """

        name_already_exists = False

        # Tag name checked
        if (
            self.text_edit_tag_name.text()
            in self.project.session.get_fields_names(COLLECTION_CURRENT)
        ):
            name_already_exists = True

        # Tag name can't be empty
        if self.text_edit_tag_name.text() == "":
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("The tag name cannot be empty")
            self.msg.setInformativeText("Please enter a tag name")
            self.msg.setWindowTitle("Error")
            self.msg.setStandardButtons(QMessageBox.Close)
            self.msg.exec()
            return

        # Tag name can't exist already
        elif name_already_exists:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("This tag name already exists")
            self.msg.setInformativeText("Please select another tag name")
            self.msg.setWindowTitle("Error")
            self.msg.setStandardButtons(QMessageBox.Close)
            self.msg.exec()
            return

        # Default value checked
        wrong_default_value_type = not check_value_type(
            self.text_edit_default_value.text(), self.type, False
        )

        # The default value must be valid
        if wrong_default_value_type:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("Invalid default value")
            self.msg.setInformativeText(
                "The default value '{0}' is invalid "
                "with the '{1}' type!".format(
                    self.text_edit_default_value.text(), self.type
                )
            )
            self.msg.setWindowTitle("Error")
            self.msg.setStandardButtons(QMessageBox.Close)
            self.msg.exec()
            return

        # Everything is Ok
        self.accept()
        self.new_tag_name = self.text_edit_tag_name.text()
        self.new_default_value = self.text_edit_default_value.text()
        self.new_tag_description = self.text_edit_description_value.text()
        self.new_tag_unit = self.combo_box_unit.currentText()

        if self.new_tag_unit == "":
            self.new_tag_unit = None

        self.databrowser.add_tag_infos(
            self.new_tag_name,
            self.new_default_value,
            self.type,
            self.new_tag_description,
            self.new_tag_unit,
        )
        self.close()

    def on_activated(self, text):
        """Type updated.

        :param text: New type

        """

        if text == "String":
            self.type = FIELD_TYPE_STRING
            self.text_edit_default_value.setText("Undefined")
        elif text == "Integer":
            self.type = FIELD_TYPE_INTEGER
            self.text_edit_default_value.setText("0")
        elif text == "Float":
            self.type = FIELD_TYPE_FLOAT
            self.text_edit_default_value.setText("0.0")
        elif text == "Boolean":
            self.type = FIELD_TYPE_BOOLEAN
            self.text_edit_default_value.setText("True")
        elif text == "Date":
            self.type = FIELD_TYPE_DATE
            date_value = datetime.now()
            date_format = date_value.strftime("%d/%m/%Y")
            self.text_edit_default_value.setText(date_format)
        elif text == "Datetime":
            self.type = FIELD_TYPE_DATETIME
            datetime_value = datetime.now()
            datetime_format = datetime_value.strftime("%d/%m/%Y %H:%M:%S.%f")
            self.text_edit_default_value.setText(datetime_format)
        elif text == "Time":
            self.type = FIELD_TYPE_TIME
            time_value = datetime.now()
            time_format = time_value.strftime("%H:%M:%S.%f")
            self.text_edit_default_value.setText(time_format)
        elif text == "String List":
            self.type = FIELD_TYPE_LIST_STRING
            self.text_edit_default_value.setText("['Undefined', 'Undefined']")
        elif text == "Integer List":
            self.type = FIELD_TYPE_LIST_INTEGER
            self.text_edit_default_value.setText("[0, 0]")
        elif text == "Float List":
            self.type = FIELD_TYPE_LIST_FLOAT
            self.text_edit_default_value.setText("[0.0, 0.0]")
        elif text == "Boolean List":
            self.type = FIELD_TYPE_LIST_BOOLEAN
            self.text_edit_default_value.setText("[True, True]")
        elif text == "Date List":
            self.type = FIELD_TYPE_LIST_DATE
            date_value = datetime.now()
            date_format = date_value.strftime("%d/%m/%Y")
            self.text_edit_default_value.setText(
                "{}".format([date_format, date_format])
            )
        elif text == "Datetime List":
            self.type = FIELD_TYPE_LIST_DATETIME
            datetime_value = datetime.now()
            datetime_format = datetime_value.strftime("%d/%m/%Y %H:%M:%S.%f")
            self.text_edit_default_value.setText(
                "{}".format([datetime_format, datetime_format])
            )
        elif text == "Time List":
            self.type = FIELD_TYPE_LIST_TIME
            time_value = datetime.now()
            time_format = time_value.strftime("%H:%M:%S.%f")
            self.text_edit_default_value.setText(
                "{}".format([time_format, time_format])
            )


class PopUpCloneTag(QDialog):
    """Is called when the user wants to clone a tag to the project.

    .. Methods:
        - ok_action: verifies the specified name is correct and send the
           information to the data browser
        - search_str: matches the searched pattern with the tags of the project

    """

    # Signal that will be emitted at the end to tell that the project
    # has been created
    signal_clone_tag = pyqtSignal()

    def __init__(self, databrowser, project):
        """Initialization.

        :param project: current project in the software
        :param databrowser: data browser instance of the software

        """

        super().__init__()
        self.setWindowTitle("Clone a tag")

        self.databrowser = databrowser
        self.project = project
        self.setModal(True)

        _translate = QtCore.QCoreApplication.translate
        self.setObjectName("Clone a tag")

        # The 'OK' push button
        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setObjectName("push_button_ok")
        self.push_button_ok.setText(_translate("Clone a tag", "OK"))

        # The 'New tag name' text edit
        self.line_edit_new_tag_name = QtWidgets.QLineEdit(self)
        self.line_edit_new_tag_name.setObjectName("lineEdit_new_tag_name")

        # The 'New tag name' label
        self.label_new_tag_name = QtWidgets.QLabel(self)
        self.label_new_tag_name.setTextFormat(QtCore.Qt.AutoText)
        self.label_new_tag_name.setObjectName("label_new_tag_name")
        self.label_new_tag_name.setText(
            _translate("Clone a tag", "New tag name:")
        )

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.label_new_tag_name)
        hbox_buttons.addWidget(self.line_edit_new_tag_name)
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(self.push_button_ok)

        # The "Tag list" label
        self.label_tag_list = QtWidgets.QLabel(self)
        self.label_tag_list.setTextFormat(QtCore.Qt.AutoText)
        self.label_tag_list.setObjectName("label_tag_list")
        self.label_tag_list.setText(
            _translate("Clone a tag", "Available tags:")
        )

        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setObjectName("lineEdit_search_bar")
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(partial(self.search_str, project))

        hbox_top = QHBoxLayout()
        hbox_top.addWidget(self.label_tag_list)
        hbox_top.addStretch(1)
        hbox_top.addWidget(self.search_bar)

        # The list of tags
        self.list_widget_tags = QtWidgets.QListWidget(self)
        self.list_widget_tags.setObjectName("listWidget_tags")
        self.list_widget_tags.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_top)
        vbox.addWidget(self.list_widget_tags)
        vbox.addLayout(hbox_buttons)

        self.setLayout(vbox)

        tags_lists = project.session.get_fields_names(COLLECTION_CURRENT)
        tags_lists.remove(TAG_CHECKSUM)
        tags_lists.remove(TAG_HISTORY)
        for tag in tags_lists:
            item = QtWidgets.QListWidgetItem()
            self.list_widget_tags.addItem(item)
            item.setText(_translate("Dialog", tag))
        self.list_widget_tags.sortItems()

        self.setLayout(vbox)

        # Connecting the OK push button
        self.push_button_ok.clicked.connect(lambda: self.ok_action(project))

    def ok_action(self, project):
        """Verifies the specified name is correct and send the
          information to the data browser.

        :param project: current project

        """

        name_already_exists = False
        for tag in project.session.get_fields(COLLECTION_CURRENT):
            if tag.field_name == self.line_edit_new_tag_name.text():
                name_already_exists = True
        if name_already_exists:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("This tag name already exists")
            self.msg.setInformativeText("Please select another tag name")
            self.msg.setWindowTitle("Error")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.buttonClicked.connect(self.msg.close)
            self.msg.show()
        elif self.line_edit_new_tag_name.text() == "":
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("The tag name can't be empty")
            self.msg.setInformativeText("Please select a tag name")
            self.msg.setWindowTitle("Error")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.buttonClicked.connect(self.msg.close)
            self.msg.show()
        elif len(self.list_widget_tags.selectedItems()) == 0:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("The tag to clone must be selected")
            self.msg.setInformativeText("Please select a tag to clone")
            self.msg.setWindowTitle("Error")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.buttonClicked.connect(self.msg.close)
            self.msg.show()
        else:
            self.accept()
            self.tag_to_replace = self.list_widget_tags.selectedItems()[
                0
            ].text()
            self.new_tag_name = self.line_edit_new_tag_name.text()
            self.databrowser.clone_tag_infos(
                self.tag_to_replace, self.new_tag_name
            )
            self.close()

    def search_str(self, project, str_search):
        """Matches the searched pattern with the tags of the project.

        :param project: current project
        :param str_search: string pattern to search

        """

        _translate = QtCore.QCoreApplication.translate
        return_list = []
        tags_lists = project.session.get_fields_names(COLLECTION_CURRENT)
        tags_lists.remove(TAG_CHECKSUM)
        tags_lists.remove(TAG_HISTORY)
        if str_search != "":
            for tag in tags_lists:
                if str_search.upper() in tag.upper():
                    return_list.append(tag)
        else:
            for tag in tags_lists:
                return_list.append(tag)

        self.list_widget_tags.clear()
        for tag_name in return_list:
            item = QtWidgets.QListWidgetItem()
            self.list_widget_tags.addItem(item)
            item.setText(_translate("Dialog", tag_name))
        self.list_widget_tags.sortItems()


class PopUpClosePipeline(QDialog):
    """Is called when the user closes a pipeline editor that has been modified.

    :param bool_save_as: boolean to True if the pipeline needs to be saved
    :param bool_exit: boolean to True if we can exit the editor
    :param save_as_signal: signal emitted to save the pipeline under
                           another name
    :param do_not_save_signal: signal emitted to close the editor
    :param cancel_signal: signal emitted to cancel the action

    .. Methods:
        - can_exit: returns the value of bool_exit
        - cancel_clicked: makes the actions to cancel the action
        - do_not_save_clicked: makes the actions not to save the pipeline
        - save_as_clicked: makes the actions to save the pipeline

    """

    save_as_signal = pyqtSignal()
    do_not_save_signal = pyqtSignal()
    cancel_signal = pyqtSignal()

    def __init__(self, pipeline_name):
        """Initialization.

        :param pipeline_name: name of the pipeline (basename)

        """

        super().__init__()

        self.pipeline_name = pipeline_name

        self.bool_exit = False
        self.bool_save_as = False

        self.setWindowTitle("Confirm pipeline closing")

        label = QLabel(self)
        label.setText(
            "Do you want to close the pipeline without saving "
            + self.pipeline_name
            + "?"
        )

        self.push_button_save_as = QPushButton("Save", self)
        self.push_button_do_not_save = QPushButton("Do not save", self)
        self.push_button_cancel = QPushButton("Cancel", self)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.push_button_save_as)
        hbox.addWidget(self.push_button_do_not_save)
        hbox.addWidget(self.push_button_cancel)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.push_button_save_as.clicked.connect(self.save_as_clicked)
        self.push_button_do_not_save.clicked.connect(self.do_not_save_clicked)
        self.push_button_cancel.clicked.connect(self.cancel_clicked)

    def can_exit(self):
        """Returns the value of bool_exit.

        :return: bool_exit value

        """

        return self.bool_exit

    def cancel_clicked(self):
        """Makes the actions to cancel the action."""

        self.bool_exit = False
        self.close()

    def do_not_save_clicked(self):
        """Makes the actions not to save the pipeline."""

        self.bool_exit = True
        self.close()

    def save_as_clicked(self):
        """Makes the actions to save the pipeline."""

        self.save_as_signal.emit()
        self.bool_save_as = True
        self.bool_exit = True
        self.close()


class PopUpDataBrowserCurrentSelection(QDialog):
    """Is called to display the current data_browser selection.

    .. Methods:
        - ok_clicked: updates the "scan_list" attribute of several widgets

    """

    def __init__(self, project, databrowser, filter, main_window):
        """Initialization.

        :param project: current project in the software
        :param databrowser: data browser instance of the software
        :param filter: list of the current documents in the data browser
        :param main_window: main window of the software

        """

        super().__init__()
        self.project = project
        self.databrowser = databrowser
        self.filter = filter
        self.main_window = main_window
        self.setWindowTitle("Confirm the selection")
        self.setModal(True)

        vbox_layout = QVBoxLayout()

        # Adding databrowser table
        databrowser_table = data_browser.TableDataBrowser(
            self.project, self.databrowser, [TAG_FILENAME], False, False
        )
        old_scan_list = databrowser_table.scans_to_visualize
        databrowser_table.scans_to_visualize = self.filter
        databrowser_table.update_visualized_rows(old_scan_list)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        vbox_layout.addWidget(databrowser_table)
        vbox_layout.addWidget(buttons)
        buttons.accepted.connect(self.ok_clicked)
        buttons.rejected.connect(self.close)
        self.setLayout(vbox_layout)
        screen_resolution = QApplication.instance().desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        self.setMinimumWidth(round(0.5 * width))
        self.setMinimumHeight(round(0.8 * height))

    def ok_clicked(self):
        """Updates the "scan_list" attribute of several widgets."""

        self.main_window.pipeline_manager.scan_list = self.filter
        self.main_window.pipeline_manager.nodeController.scan_list = (
            self.filter
        )
        self.main_window.pipeline_manager.pipelineEditorTabs.scan_list = (
            self.filter
        )
        self.main_window.pipeline_manager.iterationTable.scan_list = (
            self.filter
        )
        self.databrowser.data_sent = True
        self.close()


class PopUpDeletedProject(QMessageBox):
    """Indicate the names of deleted project when the software starts."""

    def __init__(self, deleted_projects):
        super().__init__()

        message = "These projects have been renamed, moved or deleted:\n"
        for deleted_project in deleted_projects:
            message += "- {0}\n".format(deleted_project)

        self.setIcon(QMessageBox.Warning)
        self.setText("Deleted projects")
        self.setInformativeText(message)
        self.setWindowTitle("Warning")
        self.setStandardButtons(QMessageBox.Ok)
        self.buttonClicked.connect(self.close)
        self.exec()


class PopUpDeleteProject(QDialog):
    """Is called when the user wants to delete a project.

    .. Methods:
        - ok_clicked: delete the selected projects after confirmation

    """

    def __init__(self, main_window):
        """Initialization."""

        super().__init__()

        self.setWindowTitle("Delete project")

        config = Config()
        self.project_path = config.getPathToProjectsFolder()
        self.main_window = main_window

        project_list = os.listdir(self.project_path)

        self.v_box = QVBoxLayout()

        # Label
        self.label = QLabel("Select projects to delete:")
        self.v_box.addWidget(self.label)

        self.check_boxes = []
        for project in project_list:
            if os.path.isdir(os.path.join(self.project_path, project)):
                check_box = QCheckBox(project)
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
        """Delete the selected projects after confirmation."""

        final_values = []
        for check_box in self.check_boxes:
            if check_box.isChecked():
                final_values.append(check_box.text())

        reply = None
        config = Config()
        opened_projects = config.get_opened_projects()
        for name in final_values:
            project = os.path.join(self.project_path, name)
            if reply != QMessageBox.YesToAll and reply != QMessageBox.NoToAll:
                msgtext = (
                    "Do you really want to delete the " + name + " project ?"
                )
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                title = "populse_mia - Warning: Delete project"
                reply = msg.question(
                    self,
                    title,
                    msgtext,
                    QMessageBox.Yes
                    | QMessageBox.No
                    | QMessageBox.YesToAll
                    | QMessageBox.NoToAll,
                )
            if reply == QMessageBox.Yes or reply == QMessageBox.YesToAll:
                if os.path.abspath(
                    self.main_window.project.folder
                ) == os.path.abspath(project):
                    self.main_window.project = Project(None, True)
                    self.main_window.update_project("")
                if (
                    os.path.relpath(project)
                    in self.main_window.saved_projects.pathsList
                ):
                    self.main_window.saved_projects.removeSavedProject(
                        os.path.relpath(project)
                    )
                    self.main_window.update_recent_projects_actions()
                if os.path.relpath(project) in opened_projects:
                    opened_projects.remove(os.path.relpath(project))

                config.set_opened_projects(opened_projects)
                config.saveConfig()
                shutil.rmtree(project)

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
        folder_label = QLabel("Root folder: " + project.folder)
        date_label = QLabel("Date of creation: " + project.getDate())

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
        self.setWindowTitle("Plug inherited in " + node_name)
        self.ignore = False
        self.all = False
        self.everything = False

        label = (
            "In the node <b><i>" + node_name + "</i></b>, from which "
            "input plug, the output plug <b><i>" + plug_name + "</i></b>"
            " should inherit the tags:"
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
            "<i>" + plug_name + "</i> will inherit " "tags from " + self.key
        )
        h_box_buttons.addWidget(self.push_button_ok)

        self.push_button_ignore = QtWidgets.QPushButton(self)
        self.push_button_ignore.setText("Ignore")
        self.push_button_ignore.clicked.connect(self.ignore_clicked)
        self.push_button_ignore.setToolTip(
            "<i>" + plug_name + "</i> will " "not inherit any tags."
        )
        h_box_buttons.addWidget(self.push_button_ignore)

        self.push_button_okall = QtWidgets.QPushButton(self)
        self.push_button_okall.setText("OK for all output plugs")
        self.push_button_okall.clicked.connect(self.okall_clicked)
        self.push_button_okall.setToolTip(
            "All the output plugs from <i>"
            + node_name
            + "</i> will inherit tags"
            " from " + self.key
        )
        h_box_buttons.addWidget(self.push_button_okall)

        self.push_button_ignoreall = QtWidgets.QPushButton(self)
        self.push_button_ignoreall.setText("Ignore for all output plugs")
        self.push_button_ignoreall.clicked.connect(self.ignoreall_clicked)
        self.push_button_ignoreall.setToolTip(
            "All the output plugs from <i>" + node_name + "</i> will not "
            "inherit any tags."
        )
        h_box_buttons.addWidget(self.push_button_ignoreall)

        self.push_button_ignore_node = QtWidgets.QPushButton(self)
        self.push_button_ignore_node.setText(
            "Ignore for all nodes in the " "pipeline"
        )
        self.push_button_ignore_node.clicked.connect(self.ignore_node_clicked)
        self.push_button_ignore_node.setToolTip(
            "No tags will be inherited " "for the whole pipeline."
        )
        v_box_values.addLayout(h_box_buttons)

        v_box_values.addWidget(self.push_button_ignore_node)

        if iterate:
            label = "<i>Theses choices will be valid for each iteration.</i>"
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
        push_button.setText("Tag n°" + str(len(self.push_buttons) + 1))
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
        for scan in self.project.session.get_fields_names(COLLECTION_CURRENT):
            current_value = self.project.session.get_value(
                COLLECTION_CURRENT, scan, tag_name
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

        pop_up = PopUpSelectTagCountTable(
            self.project,
            self.project.session.get_shown_tags(),
            self.push_buttons[idx].text(),
        )

        if pop_up.exec_():
            self.push_buttons[idx].setText(pop_up.selected_tag)
            self.fill_values(idx)

    def sort_scans(self):
        """Collects the information and send them to the data browser."""

        self.order = self.combo_box.itemText(self.combo_box.currentIndex())

        for push_button in self.push_buttons:
            if push_button.text() in self.project.session.get_fields_names(
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

        super().__init__()
        self.setLabelText(QFileDialog.Accept, "Create")
        self.setAcceptMode(QFileDialog.AcceptSave)

        # Setting the projects directory as default
        utils.set_projects_directory_as_default(self)

    def get_filename(self, file_name_tuple):
        """Sets the widget's attributes depending on the selected file name.

        :param file_name_tuple: tuple obtained with the selectedFiles method
        :return: real file name

        """

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
                utils.message_already_exists()

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
        super().__init__()

        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setFileMode(QFileDialog.Directory)

        # Setting the projects directory as default
        utils.set_projects_directory_as_default(self)

    def get_filename(self, file_name_tuple):
        """Sets the widget's attributes depending on the selected file name.

        :param file_name_tuple: tuple obtained with the selectedFiles method

        """

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
                utils.message_already_exists()


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
            "Number of thumbnails " "in Data Browser:"
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
            "Radiological orientation in " "miniviewer (data browser)"
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
            "Matlab path (e.g., matlab_dir/" "bin/matlab):"
        )
        self.matlab_choice = QLineEdit(config.get_matlab_path())
        self.matlab_browse = QPushButton("Browse")
        self.matlab_browse.clicked.connect(self.browse_matlab)

        self.use_matlab_standalone_label = QLabel("Use Matlab standalone")
        self.use_matlab_standalone_checkbox = QCheckBox("", self)
        self.matlab_standalone_label = QLabel(
            "Matlab standalone path (e.g., " "MCR_dir/v95):"
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
            "FSL config file (e.g., " "fsl_dir/etc/fslconf/fsl.sh):"
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
        self.groupbox_freesurfer = QtWidgets.QGroupBox("freesurfer")

        self.use_freesurfer_label = QLabel("Use freesurfer")
        self.use_freesurfer_checkbox = QCheckBox("", self)

        self.freesurfer_label = QLabel(
            "freesurfer path (e.g. freesurfer_dir/FreeSurferEnv.sh):"
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
            "Select the location of the " "MRIManager.jar file",
            os.path.expanduser("~"),
        )[0]
        if fname:
            self.mri_conv_path_line_edit.setText(fname)

    def browse_projects_save_path(self):
        """Called when "Projects folder" browse button is clicked."""

        fname = QFileDialog.getExistingDirectory(
            self,
            "Select a folder where " "to save the projects",
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
            "Select the location of the " "External resources folder",
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
            self, "Choose SPM standalone " "directory", os.path.expanduser("~")
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
        status = "<i>" + status + "</i>"
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
            old_psswd = self.salt + change.old_psswd.text()
            hash_psswd = hashlib.sha256(old_psswd.encode()).hexdigest()
            if (
                hash_psswd == config.get_admin_hash()
                and change.new_psswd.text() == change.new_psswd_conf.text()
                and len(change.new_psswd.text()) > 6
            ):
                new_psswd = self.salt + change.new_psswd.text()
                config.set_admin_hash(
                    hashlib.sha256(new_psswd.encode()).hexdigest()
                )
            elif hash_psswd != config.get_admin_hash():
                self.change_admin_psswd("The old password is incorrect.")
            elif len(change.new_psswd.text()) <= 6:
                self.change_admin_psswd(
                    "Your password must have more than 6 " "characters"
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
                "To change the controller from {0} to {1}, "
                "MIA must be restarted. Would you like to plan "
                "this change for next "
                "start-up?".format(
                    "V1" if config.isControlV1() else "V2",
                    "V2" if config.isControlV1() else "V1",
                )
            )

        else:
            self.msg.setInformativeText(
                "Change of controller from {0} to {1} is already "
                "planned for next start-up. Would you like to "
                "cancel this "
                "change?".format(
                    "V1" if config.isControlV1() else "V2",
                    "V2" if config.isControlV1() else "V1",
                )
            )

        return_value = self.msg.exec()

        if return_value == QMessageBox.Yes:
            self.control_checkbox_changed = not self.control_checkbox_changed
            main_window.set_controller_version()

        QApplication.restoreOverrideCursor()

    def edit_config_file(self):
        """Create a window to view, edit the mia configuration file."""
        config = Config()

        self.editConf = QDialog()
        self.editConf.setWindowTitle(
            os.path.join(config.get_config_path(), "config.yml")
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
            print(e)
            return

        if result:
            settings = engine.settings.export_config_dict()

            capsul_config["engine"] = settings
            capsul_config["engine_modules"] = list(engine._loaded_modules)

            try:
                config.set_capsul_config(capsul_config)

            except Exception as e:
                print(e)
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
                main_window.windowName += " (Admin mode)"

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
            main_window.windowName += " - "
            main_window.setWindowTitle(
                main_window.windowName + main_window.projectName
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

                    if err == b"":
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
                            "restoredefaultpath; "
                            "addpath('" + spm_input + "'); "
                            "[name, ~]=spm('Ver'); "
                            "exit"
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

                                print(
                                    "\nWarning: The configuration for Matlab"
                                    " MCR and SPM standalone as defined in"
                                    " Mia's preferences seems to be valid "
                                    "but the following issue has been "
                                    "detected:\n{}\nPlease fix this issue"
                                    " to avoid a malfunction ...".format(err)
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
                    print(
                        "WARNING: Matlab Standalone Path enter, this "
                        "is unnecessary to use SPM12."
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
                "background-color:"
                + background_color
                + ";color:"
                + text_color
                + ";"
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
                    "The projects folder path entered "
                    "{0} is "
                    "invalid.".format(projects_folder)
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
                    "No path has been entered for " "MRIFileManager.jar."
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
                    "The MRIFileManager.jar path "
                    "entered {0} "
                    "is invalid.".format(mri_conv_path)
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
                    "The resources folder path entered "
                    "{0} is "
                    "invalid.".format(resources_folder)
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
                salt_psswd = self.salt + psswd
                hash_psswd = hashlib.sha256(salt_psswd.encode()).hexdigest()

                if hash_psswd != config.get_admin_hash():
                    self.admin_mode_checkbox.setChecked(False)
                    self.status_label.setText(
                        "<i style='color:red'>Wrong " "password.</i>"
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
        self.msg.setText("Invalid " + tool + " path")
        if extra_mess:
            extra_mess = " " + extra_mess
        self.msg.setInformativeText(
            "The {0}{1} path entered {2} is invalid.".format(
                tool, extra_mess, path
            )
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
        self.tab_tags = PopUpVisualizedTags(
            self.project, self.project.session.get_shown_tags()
        )
        self.tab_tags.setObjectName("tab_tags")
        self.tab_widget.addTab(
            self.tab_tags, _translate("Dialog", "Visualized tags")
        )

        # The 'Informations" tab
        self.tab_infos = PopUpInformation(self.project)
        self.tab_infos.setObjectName("tab_infos")
        self.tab_widget.addTab(
            self.tab_infos, _translate("Dialog", "Informations")
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
        self.project.session.set_shown_tags(new_visibilities)
        history_maker.append(new_visibilities)

        self.project.undos.append(history_maker)
        self.project.redos.clear()
        self.project.unsavedModifications = True

        # Columns updated
        self.databrowser.table_data.update_visualized_columns(
            self.old_tags, self.project.session.get_shown_tags()
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

    def __init__(self, database):
        """Initialization.

        :param database: current database in the project

        """

        super().__init__()

        self.database = database

        self.bool_exit = False

        self.setWindowTitle("Confirm exit")

        label = QLabel(self)
        label.setText(
            "Do you want to exit without saving "
            + self.database.getName()
            + "?"
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
            "The document " + scan + "\nwas previously sent to the "
            "pipeline manager, do you "
            "really want to delete it ?"
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

        for tag in self.project.session.get_fields(COLLECTION_CURRENT):
            if tag.origin == TAG_ORIGIN_USER:
                item = QtWidgets.QListWidgetItem()
                self.list_widget_tags.addItem(item)
                item.setText(_translate("Dialog", tag.field_name))

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

        if str_search != "":
            return_list = []
            for tag in self.project.session.get_fields(COLLECTION_CURRENT):
                if tag.origin == TAG_ORIGIN_USER:
                    if str_search.upper() in tag.name.upper():
                        return_list.append(tag.name)
        else:
            return_list = []
            for tag in self.project.session.get_fields(COLLECTION_CURRENT):
                if tag.origin == TAG_ORIGIN_USER:
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
                        utils.message_already_exists()
                        return
                    else:
                        msgtext = (
                            "Do you really want to overwrite the "
                            + file_name
                            + " project ?\nThis action "
                            "delete all contents inside this folder!"
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

        super(PopUpSelectFilter, self).__init__(project)
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
            "Iterate pipeline run over tag {0}".format(self.iterated_tag)
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
        if str_search != "":
            for tag in self.project.session.get_fields_names(
                COLLECTION_CURRENT
            ):
                if tag != TAG_CHECKSUM and tag != TAG_HISTORY:
                    if str_search.upper() in tag.upper():
                        return_list.append(tag)
        else:
            for tag in self.project.session.get_fields_names(
                COLLECTION_CURRENT
            ):
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

        super(PopUpSelectTag, self).__init__(project)
        self.project = project
        self.config = Config()

        # Filling the list and checking the thumbnail tag
        for tag in self.project.session.get_fields_names(COLLECTION_CURRENT):
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

        super(PopUpSelectTagCountTable, self).__init__(project)

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
        - io_value_is_scan: checks if the I/O value is a scan
        - file_clicked: called when a file is clicked
        - node_selected: called when a pipeline node is clicked
        - update_table: update the brick row at the bottom
    """

    def __init__(self, project, brick_uuid, scan, databrowser, main_window):
        """Prepares the brick history popup.

        :param project: current project in the software
        :param scan: filename of the scan
        :param databrowser; data browser instance of the software
        :param main_window: main window of the software

        """

        super().__init__()

        self.setModal(False)
        self.setWindowFlags(
            self.windowFlags() & QtCore.Qt.WindowStaysOnBottomHint
        )

        self.databrowser = databrowser
        self.main_window = main_window
        self.project = project
        self.setWindowTitle("History of " + scan)

        brick_row = project.session.get_document(COLLECTION_BRICK, brick_uuid)
        full_brick_name = project.session.get_value(
            COLLECTION_BRICK, brick_uuid, BRICK_NAME
        ).split(".")

        layout = QVBoxLayout()
        self.splitter = QSplitter(Qt.Qt.Vertical)

        self.table = QTableWidget()
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        history_uuid = self.project.session.get_value(
            COLLECTION_CURRENT, scan, TAG_HISTORY
        )

        self.unitary_pipeline = False
        self.uuid_idx = 0
        if history_uuid is not None:
            self.pipeline_xml = self.project.session.get_value(
                COLLECTION_HISTORY, history_uuid, HISTORY_PIPELINE
            )
            if self.pipeline_xml is not None:
                self.brick_list = self.project.session.get_value(
                    COLLECTION_HISTORY, history_uuid, HISTORY_BRICKS
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
                        print(
                            "\nerror in naming association brick\\pipeline, "
                            "cannot select node ..."
                        )
                        pass

        inputs = getattr(brick_row, BRICK_INPUTS)
        outputs = getattr(brick_row, BRICK_OUTPUTS)
        brick_name = getattr(brick_row, BRICK_NAME)
        init = getattr(brick_row, BRICK_INIT)
        init_time = getattr(brick_row, BRICK_INIT_TIME)
        exec = getattr(brick_row, BRICK_INIT)
        exec_time = getattr(brick_row, BRICK_INIT_TIME)
        self.update_table(
            inputs, outputs, brick_name, init, init_time, exec, exec_time
        )

        self.splitter.addWidget(self.table)

        layout.addWidget(self.splitter)
        self.setLayout(layout)

        screen_resolution = QApplication.instance().desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        self.setGeometry(300, 200, round(0.6 * width), round(0.4 * height))

    def io_value_is_scan(self, value):
        """Checks if the I/O value is a scan.

        :param value: I/O value
        :return: The scan corresponding to the value if it exists,
          None otherwise

        """

        value_scan = None

        for scan in self.project.session.get_documents_names(
            COLLECTION_CURRENT
        ):
            if scan in str(value):
                value_scan = scan

        return value_scan

    def file_clicked(self):
        """Called when a file is clicked."""

        file = self.sender().text()
        self.databrowser.table_data.clearSelection()
        row_to_select = self.databrowser.table_data.get_scan_row(file)
        self.databrowser.table_data.selectRow(row_to_select)
        item_to_scroll_to = self.databrowser.table_data.item(row_to_select, 0)
        self.databrowser.table_data.scrollToItem(item_to_scroll_to)
        self.close()

    def find_associated_bricks(self, node_name):
        """Blabla"""

        bricks = {}
        for uuid in self.brick_list:
            full_brick_name = self.project.session.get_value(
                COLLECTION_BRICK, uuid, BRICK_NAME
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
        """Blabla"""

        process_name = ""
        plug_name = ""
        if plug.output:
            link_done = False
            for link in plug.links_from:
                if not link_done:
                    link_done = True
                    process_name += "." + link[2].name
                    plug_name = link[1]
                    if isinstance(link[2], PipelineNode):
                        (
                            sub_process_name,
                            plug_name,
                        ) = self.find_process_from_plug(link[2].plugs[link[1]])
                        process_name += sub_process_name
        else:
            link_done = False
            for link in plug.links_to:
                if not link_done:
                    link_done = True
                    process_name += "." + link[2].name
                    plug_name = link[1]
                    if isinstance(link[2], PipelineNode):
                        (
                            sub_process_name,
                            plug_name,
                        ) = self.find_process_from_plug(link[2].plugs[link[1]])
                        process_name += sub_process_name
        return process_name, plug_name

    def node_selected(self, node_name, process):
        """Emit a signal when a node is clicked.

        :param node_name: node name
        :param process: process of the corresponding node
        """

        if hasattr(process, "pipeline_node"):
            process = process.pipeline_node

        bricks = self.find_associated_bricks(node_name)

        if bricks:
            if len(bricks) == 1:
                brick_row = self.project.session.get_document(
                    COLLECTION_BRICK,
                    next(iter(bricks.values()))[self.uuid_idx],
                )
                inputs = getattr(brick_row, BRICK_INPUTS)
                outputs = getattr(brick_row, BRICK_OUTPUTS)
                brick_name = getattr(brick_row, BRICK_NAME)
                init = getattr(brick_row, BRICK_INIT)
                init_time = getattr(brick_row, BRICK_INIT_TIME)
                exec = getattr(brick_row, BRICK_INIT)
                exec_time = getattr(brick_row, BRICK_INIT_TIME)
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
                                    self.project.session.get_value(
                                        COLLECTION_BRICK, uuid[0], BRICK_NAME
                                    )
                                )
                                if full_brick_name == node_name + process_name:
                                    if plug.output:
                                        plugs = self.project.session.get_value(
                                            COLLECTION_BRICK,
                                            uuid[self.uuid_idx],
                                            BRICK_OUTPUTS,
                                        )
                                        outputs_dict[plug_name] = plugs[
                                            inner_plug_name
                                        ]
                                    else:
                                        plugs = self.project.session.get_value(
                                            COLLECTION_BRICK,
                                            uuid[self.uuid_idx],
                                            BRICK_INPUTS,
                                        )
                                        inputs_dict[plug_name] = plugs[
                                            inner_plug_name
                                        ]

                self.update_table(inputs_dict, outputs_dict, node_name)

            for name, gnode in self.pipeline_view.scene.gnodes.items():
                if name == node_name:
                    gnode.fonced_viewer(False)
                else:
                    gnode.fonced_viewer(True)

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
        """Filling the table."""

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
        item = QTableWidgetItem()
        item.setText(brick_name)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        self.table.setItem(0, item_idx, item)
        item_idx += 1

        # Brick init
        if init != "":
            item = QTableWidgetItem()
            item.setText(BRICK_INIT)
            self.table.setHorizontalHeaderItem(item_idx, item)
            item = QTableWidgetItem()
            item.setText(init)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(0, item_idx, item)
            item_idx += 1

            # Brick init time
            item = QTableWidgetItem()
            item.setText(BRICK_INIT_TIME)
            self.table.setHorizontalHeaderItem(item_idx, item)
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            if init_time is not None:
                item.setText(str(init_time))
            self.table.setItem(0, item_idx, item)
            item_idx += 1

        # Brick execution
        if init != "":
            item = QTableWidgetItem()
            item.setText(BRICK_EXEC)
            self.table.setHorizontalHeaderItem(item_idx, item)
            item = QTableWidgetItem()
            item.setText(exec)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(0, item_idx, item)
            item_idx += 1

            # Brick execution time
            item = QTableWidgetItem()
            item.setText(BRICK_EXEC_TIME)
            self.table.setHorizontalHeaderItem(item_idx, item)
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            if exec_time is not None:
                item.setText(str(exec_time))
            self.table.setItem(0, item_idx, item)
            item_idx += 1

        # Inputs
        for key, value in sorted(inputs.items()):
            item = QTableWidgetItem()
            item.setText(key)
            self.table.setHorizontalHeaderItem(item_idx, item)
            if isinstance(value, list):
                # value = str(value).strip('[]')
                value = str(value)

            value_scan = self.io_value_is_scan(value)
            if value_scan is not None:
                widget = QWidget()
                output_layout = QVBoxLayout()
                button = QPushButton(value_scan)
                button.clicked.connect(self.file_clicked)
                output_layout.addWidget(button)
                widget.setLayout(output_layout)
                self.table.setCellWidget(0, item_idx, widget)
            else:
                item = QTableWidgetItem()
                item.setText(str(value))
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(0, item_idx, item)
            item_idx += 1

        # Outputs
        for key, value in sorted(outputs.items()):
            item = QTableWidgetItem()
            item.setText(key)
            self.table.setHorizontalHeaderItem(item_idx, item)
            value = outputs[key]
            if isinstance(value, list):
                sub_widget = QWidget()
                sub_layout = QVBoxLayout()
                for sub_value in value:
                    value_scan = self.io_value_is_scan(sub_value)
                    if value_scan is not None:
                        button = QPushButton(value_scan)
                        button.clicked.connect(self.file_clicked)
                        sub_layout.addWidget(button)
                    else:
                        label = QLabel(str(sub_value))
                        sub_layout.addWidget(label)
                sub_widget.setLayout(sub_layout)
                self.table.setCellWidget(0, item_idx, sub_widget)
            else:
                value_scan = self.io_value_is_scan(value)
                if value_scan is not None:
                    widget = QWidget()
                    output_layout = QVBoxLayout()
                    button = QPushButton(value_scan)
                    button.clicked.connect(self.file_clicked)
                    output_layout.addWidget(button)
                    widget.setLayout(output_layout)
                    self.table.setCellWidget(0, item_idx, widget)
                else:
                    item = QTableWidgetItem()
                    item.setText(str(value))
                    item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.table.setItem(0, item_idx, item)
            item_idx += 1

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

        for tag in project.session.get_fields_names(COLLECTION_CURRENT):
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
