"""
Database cell editor module for list-type values.

This module provides dialog interfaces for editing complex data types
in the Mia data browser. It specifically handles the editing of list-type
values such as arrays of numbers, strings, or dates.

The ModifyTable dialog creates an interactive table representation of lists,
allowing users to add, edit, or remove items while ensuring type safety
and database consistency.

Contains:
    Class:
        - ModifyTable
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import logging
from datetime import datetime

# PyQt5 imports
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

# Populse_MIA imports
from populse_mia.data_manager import (
    COLLECTION_CURRENT,
    FIELD_TYPE_LIST_BOOLEAN,
    FIELD_TYPE_LIST_DATE,
    FIELD_TYPE_LIST_DATETIME,
    FIELD_TYPE_LIST_FLOAT,
    FIELD_TYPE_LIST_INTEGER,
    FIELD_TYPE_LIST_STRING,
    FIELD_TYPE_LIST_TIME,
)

logger = logging.getLogger(__name__)


class ModifyTable(QDialog):
    """
    Dialog to modify cell contents containing lists in the data browser tab.

    This dialog provides a user interface to edit cells that contain list
    values. It displays the list elements in a table and allows users to add
    or remove elements.

    .. Methods:
        - _convert_value: Convert a text value to the appropriate type
        - _show_error_message: Display an error message
        - add_item: Add one more element to self.value
        - fill_table: Fill the table
        - rem_last_item: Remove last element of self.value
        - update_table_values: Update the table in the database
    """

    def __init__(self, project, value, types, scans, tags):
        """
        Initialize the ModifyTable dialog.

        :param project: Instance of the current project
        :param value: List of values in the cell to be modified
        :param types: Allowed value types for validation
        :param scans: Scan identifiers corresponding to rows
        :param tags: Tag identifiers corresponding to columns
        """
        super().__init__()
        self.setModal(True)
        # Initialize instance variables
        self.types = types
        self.scans = scans
        self.tags = tags
        self.project = project
        self.value = value
        # Create and configure the table
        self.table = QTableWidget()
        self.fill_table()
        # Create control buttons
        ok_button = QPushButton("Ok")
        ok_button.clicked.connect(self.update_table_values)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        # plus_button = QPushButton("+")
        add_button = QPushButton("+")
        add_button.setToolTip("Add one more element to the list")
        add_button.clicked.connect(self.add_item)
        # minus_button = QPushButton("-")
        remove_button = QPushButton("-")
        remove_button.setToolTip("Remove the last element of the list")
        remove_button.clicked.connect(self.rem_last_item)
        # Set up layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(ok_button)
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(add_button)
        self.button_layout.addWidget(remove_button)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.table)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def _convert_value(self, text, field_type):
        """
        Convert a text value to the appropriate type based on field_type.

        :param text: String value to convert
        :param field_type: Database field type constant

        :return: The converted value in the appropriate type
        """

        if field_type == FIELD_TYPE_LIST_INTEGER:
            return int(text)

        elif field_type == FIELD_TYPE_LIST_FLOAT:
            return float(text)

        elif field_type == FIELD_TYPE_LIST_STRING:
            return str(text)

        elif field_type == FIELD_TYPE_LIST_BOOLEAN:
            return eval(text)

        elif field_type == FIELD_TYPE_LIST_DATE:
            return datetime.strptime(text, "%d/%m/%Y").date()

        elif field_type == FIELD_TYPE_LIST_DATETIME:
            return datetime.strptime(text, "%d/%m/%Y %H:%M:%S.%f")

        elif field_type == FIELD_TYPE_LIST_TIME:
            return datetime.strptime(text, "%H:%M:%S.%f").time()

    def _show_error_message(self, value, type_problem):
        """
        Display an error message for invalid values.

        :param value: The invalid value
        :param type_problem: The specific type that failed validation
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Invalid value")
        msg.setInformativeText(
            f"The value {value} is invalid with the type {type_problem}"
        )
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(msg.close)
        msg.exec()

    def add_item(self):
        """
        Add a new element to the list with default value 0.
        """
        self.value.append(0)
        # Filling the table
        self.fill_table()

    def fill_table(self):
        """
        Populate the table with the current list elements.

        Configures the table dimensions, populates cells with values,
        and adjusts table size to fit content within reasonable bounds.
        """
        # Set table dimensions
        self.table.setColumnCount(len(self.value))
        self.table.setRowCount(1)

        # Populate cells with values
        for col, value in enumerate(self.value):
            item = QTableWidgetItem(str(value))
            self.table.setItem(0, col, item)

        # Resize columns to fit content
        self.table.resizeColumnsToContents()
        # Calculate total dimensions
        total_width = sum(
            self.table.columnWidth(i) for i in range(self.table.columnCount())
        )
        total_height = sum(
            self.table.rowHeight(i) for i in range(self.table.rowCount())
        )
        # Set table dimensions with constraints
        width = min(total_width + 20, 900)
        height = total_height + (25 if total_width + 20 < 900 else 40)
        self.table.setFixedWidth(width)
        self.table.setFixedHeight(height)

    def rem_last_item(self):
        """
        Remove the last element of the list if there's more than one element.

        Lists must maintain at least one element.
        """

        if len(self.value) > 1:
            self.value.pop()
            # Filling the table
            self.fill_table()

        else:
            logger.info(
                "The list must contain at least one element. "
                "Deletion of the last element is aborted!"
            )

    def update_table_values(self, test=False):
        """
        Validate user input and update the database with new values.

        Validates each value against specified types and updates the database
        only if all values are valid.

        :param test (bool): Flag for testing mode, defaults to False
        """

        # import check_value_type only here to prevent circular import issue
        from populse_mia.utils import check_value_type

        valid = True

        # Validate each cell value against allowed types
        for col in range(0, self.table.columnCount()):
            item = self.table.item(0, col)
            text = item.text()
            type_problem = None

            # Check if value is valid for each of the allowed types
            for tag_type in self.types:

                if not check_value_type(text, tag_type, True):
                    valid = False
                    type_problem = tag_type
                    break

            # If not valid, show error and stop validation
            if not valid:

                if not test:
                    self._show_error_message(text, type_problem)

                return

        # Only update database if all values are valid
        # Update database for each cell with validated values

        with self.project.database.data() as database_data:

            for scan, tag in zip(self.scans, self.tags):
                # Get field attributes
                tag_attrib = database_data.get_field_attributes(
                    COLLECTION_CURRENT, tag
                )
                tag_type = tag_attrib["field_type"]
                # Convert values according to field type
                database_value = []

                for i in range(self.table.columnCount()):
                    item = self.table.item(0, i)
                    text = item.text()
                    database_value.append(self._convert_value(text, tag_type))

                # Update database
                database_data.set_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan,
                    values_dict={tag: database_value},
                )

        self.close()
