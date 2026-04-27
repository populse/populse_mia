"""Module that handles pipeline iteration.

:Contains:
    :Class:
        - IterationTable

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################


import ast
import json
import os
from functools import partial

# PyQt5 import
from PyQt5 import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Populse_mia import
from populse_mia.data_manager import COLLECTION_CURRENT, TAG_FILENAME
from populse_mia.software_properties import Config
from populse_mia.user_interface.pipeline_manager.process_mia import ProcessMIA
from populse_mia.user_interface.pop_ups import (
    ClickableLabel,
    PopUpSelectIteration,
    PopUpSelectTagCountTable,
)


class IterationTable(QWidget):
    """
    Widget that handles pipeline iteration.

    This widget allows users to select tags for iteration and visualization,
    filter values, and manage the iteration process for pipeline execution.


    .. Methods:
        - _create_tag_button: Create a new tag button
        - add_tag: Add a tag to visualize in the iteration table
        - current_editor: Return the currently active pipeline editor
        - emit_iteration_table_updated: Emit a signal when the iteration
                                        scans have been updated
        - fill_values: Fill values_list depending on the visualized tags
        - filter_values: Select the tag values used for the iteration
        - format_filter_value: Convert a value into a JSON-formatted string
        - refresh_layout: Update the layout of the widget
        - remove_tag: Remove a tag to visualize in the iteration table
        - select_iteration_tag: Open a pop-up to let the user select on which
                                tag to iterate
        - select_visualized_tag: Open a pop-up to let the user select which
                                 tag to visualize in the iteration table
        - update_iterated_tag: Update the widget
        - update_table: Update the iteration table
        - update_selected_tag: Update the selected tag for current pipeline
                               manager tab

    .. Signals:
        - iteration_table_updated: Emitted when iteration scans have been
                                   updated.
    """

    iteration_table_updated = pyqtSignal(list, list)

    def __init__(self, project, scan_list=None, main_window=None):
        """
        Initialize the IterationTable widget.

        :param project: Current project in the software.
        :param scan_list: List of the selected database files. If None, all
                          documents from the current collection will be used.
        :param main_window: Software's main window reference.
        """
        super().__init__()
        # Necessary for using Mia bricks
        ProcessMIA.project = project
        self.project = project
        self.main_window = main_window

        # Initialize scan list
        with self.project.database.data() as database_data:
            self.scan_list = (
                scan_list
                if scan_list
                else database_data.get_document_names(COLLECTION_CURRENT)
            )

        # Initialize tag values data structures
        # values_list will contain the different values of each selected tag
        self.values_list = [[], []]
        self.all_tag_values = []
        # Set up iteration controls
        self.check_box_iterate = QCheckBox("Iterate pipeline")
        self.check_box_iterate.stateChanged.connect(
            self.emit_iteration_table_updated
        )
        self.label_iterate = QLabel("Iterate over:")
        self.iterated_tag_label = QLabel("Select a tag")
        self.iterated_tag_push_button = QPushButton("Select")
        self.iterated_tag_push_button.clicked.connect(
            self.select_iteration_tag
        )
        # Set up filtering and value selection
        self.combo_box = QComboBox()
        self.combo_box.currentIndexChanged.connect(self.update_table)
        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.filter_values)
        # Set up table widget
        self.iteration_table = QTableWidget()
        # Set up tag visualization controls
        self.label_tags = QLabel("Tags to visualize:")
        # Create default tag buttons
        self.push_buttons = []
        self._create_tag_button("SequenceName", 0)
        self._create_tag_button("AcquisitionDate", 1)
        # Set up add/remove tag controls
        sources_images_dir = Config().getSourceImageDir()
        self.add_tag_label = ClickableLabel()
        self.add_tag_label.setObjectName("plus")
        add_tag_picture = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "green_plus.png"))
        )
        add_tag_picture = add_tag_picture.scaledToHeight(15)
        self.add_tag_label.setPixmap(add_tag_picture)
        self.add_tag_label.clicked.connect(self.add_tag)
        self.remove_tag_label = ClickableLabel()
        remove_tag_picture = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "red_minus.png"))
        )
        remove_tag_picture = remove_tag_picture.scaledToHeight(20)
        self.remove_tag_label.setPixmap(remove_tag_picture)
        self.remove_tag_label.clicked.connect(self.remove_tag)

        # Create a container for iteration controls
        self.iteration_controls_container = QWidget()
        self.iteration_controls_layout = QVBoxLayout(
            self.iteration_controls_container
        )

        # First line: self.label_iterate and self.iterated_tag_push_button
        first_line_layout = QHBoxLayout()
        first_line_layout.addWidget(self.label_iterate)
        first_line_layout.addWidget(self.iterated_tag_push_button)
        self.iteration_controls_layout.addLayout(first_line_layout)

        # Second line: self.iterated_tag_label, self.combo_box, and
        # self.filter_button
        second_line_layout = QHBoxLayout()
        second_line_layout.addWidget(self.iterated_tag_label)
        second_line_layout.addWidget(self.combo_box)
        second_line_layout.addWidget(self.filter_button)
        self.iteration_controls_layout.addLayout(second_line_layout)

        # Create a container for tags to visualize and its buttons
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setSpacing(10)
        self.tags_layout.addWidget(self.label_tags)

        for tag_button in self.push_buttons:
            self.tags_layout.addWidget(tag_button)

        self.tags_layout.addWidget(self.add_tag_label)
        self.tags_layout.addWidget(self.remove_tag_label)
        self.tags_layout.addStretch(1)

        # Initially hide the iteration controls container and tags container
        self.iteration_controls_container.setVisible(False)
        self.tags_container.setVisible(False)

        # --- Main layout: Use QGridLayout ---
        self.main_layout = Qt.QGridLayout(self)

        # Add the checkbox to the top-left cell (row 0, column 0)
        self.main_layout.addWidget(self.check_box_iterate, 0, 0, 1, 1)

        # Add the iteration controls container to the top-right
        # (row 0, column 1)
        self.main_layout.addWidget(
            self.iteration_controls_container, 0, 1, 1, 1
        )

        # Add the table to the second row, spanning both columns
        # (row 1, column 0 to 1)
        self.main_layout.addWidget(self.iteration_table, 1, 0, 1, 2)

        # Add the tags container to the third row, spanning both columns
        # (row 2, column 0 to 1)
        self.main_layout.addWidget(self.tags_container, 2, 0, 1, 2)

        # Ensure the table and containers expand to fill the available space
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setRowStretch(1, 1)

    def _create_tag_button(self, text, index):
        """Create a new tag button with the given text and index.

        :param text (str): Text to display on the button.
        :param index (int): Index of the button in the push_buttons list.
        """
        button = QPushButton(text)
        button.clicked.connect(partial(self.select_visualized_tag, index))
        self.push_buttons.insert(index, button)
        return button

    @property
    def current_editor(self):
        """
        Return the currently active pipeline editor.

        This property provides convenient access to the current editor from the
        pipeline manager without repeating the full attribute chain.

        :return: The active pipeline editor instance.
        """
        # fmt: off
        return (
            self.main_window.pipeline_manager
            .pipelineEditorTabs.get_current_editor()
        )
        # fmt: on

    def add_tag(self):
        """
        Add a new tag button to visualize in the iteration table.

        Used only for tests.
        """

        idx = len(self.push_buttons)
        button_text = f"Tag n°{idx + 1}"
        self._create_tag_button(button_text, idx)
        self.refresh_layout()

    def emit_iteration_table_updated(self):
        """Emit a signal when the iteration scans have been updated."""
        visible = self.check_box_iterate.isChecked()
        # Toggle visibility of the iteration controls and tags containers
        self.iteration_controls_container.setVisible(visible)
        self.tags_container.setVisible(visible)

        if not visible:
            # Clear the table completely
            self.iteration_table.clear()
            self.iteration_table.setRowCount(0)
            self.iteration_table.setColumnCount(0)
            # Reset combo box
            self.combo_box.clear()
            # Reset labels if needed
            self.iterated_tag_label.setText("Select a tag")
            self.iterated_tag_push_button.setText("Select")

        # Emit signal with default scan list
        self.iteration_table_updated.emit(self.scan_list, [self.scan_list])

    def fill_values(self, idx):
        """
        Fill values_list with unique tag values for the specified tag.

        :param idx (int): Index of the tag in push_buttons list.
        """
        tag_name = self.push_buttons[idx].text()
        values = []

        # Get all unique values for this tag from current documents
        with self.project.database.data() as database_data:

            for scan in database_data.get_document_names(COLLECTION_CURRENT):
                current_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan,
                    field=tag_name,
                )

                if current_value is not None and current_value not in values:
                    values.append(current_value)

        # Ensure values_list has enough slots
        while len(self.values_list) <= idx:
            self.values_list.append([])

        self.values_list[idx] = values

    def filter_values(self):
        """Open a dialog to select specific tag values for iteration."""

        if self.check_box_iterate.isChecked():
            current_editor = self.current_editor
            iterated_tag = current_editor.iterated_tag
            tag_values = current_editor.all_tag_values_list
            ui_iteration = PopUpSelectIteration(iterated_tag, tag_values)

            if ui_iteration.exec_():
                # Remove ampersands from tag values (used for shortcuts in Qt)
                tag_values_list = [
                    t.replace("&", "") for t in ui_iteration.final_values
                ]
                current_editor.tag_values_list = tag_values_list
                # Update the combo box with filtered values
                self.combo_box.clear()
                self.combo_box.addItems(tag_values_list)
                self.update_table()

    def format_filter_value(self, value):
        """
        Convert a value into a JSON-formatted string.

        If ``value`` is a string, this method first attempts to interpret it as
        a Python literal (for example a list, dict, number, or boolean) using
        ``ast.literal_eval()``. If parsing fails, the original string is
        preserved.

        :param value (Any): The value to serialize.

        :return (str): The JSON representation of the resulting value.
        """

        if isinstance(value, str):

            try:
                value = ast.literal_eval(value)

            except (ValueError, SyntaxError):
                pass

        return json.dumps(value)

    def refresh_layout(self):
        """Update the layout of the widget.

        Called in widget's initialization and when a tag push button
        is added or removed.
        """

        # Clear and rebuild the tags container layout
        for i in reversed(range(self.tags_layout.count())):
            item = self.tags_layout.itemAt(i)
            if item:
                self.tags_layout.removeItem(item)

        # Rebuild the tags container layout
        self.tags_layout.addWidget(self.label_tags)

        for tag_button in self.push_buttons:
            self.tags_layout.addWidget(tag_button)

        self.tags_layout.addWidget(self.add_tag_label)
        self.tags_layout.addWidget(self.remove_tag_label)
        self.tags_layout.addStretch(1)

    def remove_tag(self):
        """Remove the last tag button from the visualization list."""

        if self.push_buttons:
            # Remove the last button
            button = self.push_buttons.pop()
            button.close()
            button.deleteLater()

            # Remove corresponding values
            if len(self.values_list) > 0:
                self.values_list.pop()

            # Update UI
            self.refresh_layout()
            self.update_table()

    def select_iteration_tag(self):
        """Open a dialog to let the user select which tag to iterate over."""

        if self.check_box_iterate.isChecked():

            with self.project.database.data() as database_data:
                available_fields = database_data.get_field_names(
                    COLLECTION_CURRENT
                )

            ui_select = PopUpSelectTagCountTable(
                self.project,
                available_fields,
                self.current_editor.iterated_tag,
            )

            if ui_select.exec_():

                if not (
                    self.current_editor.iterated_tag is None
                    and ui_select.selected_tag is None
                ):
                    self.current_editor.iterated_tag = ui_select.selected_tag
                    self.update_selected_tag(ui_select.selected_tag)

    def select_visualized_tag(self, idx):
        """
        Open a dialog to select which tag to visualize in the iteration table.

        :param idx (int): Index of the clicked push button.
        """

        with self.project.database.data() as database_data:
            available_fields = database_data.get_field_names(
                COLLECTION_CURRENT
            )

        current_tag = self.push_buttons[idx].text()
        popUp = PopUpSelectTagCountTable(
            self.project,
            available_fields,
            current_tag,
        )

        if popUp.exec_() and popUp.selected_tag is not None:
            self.push_buttons[idx].setText(popUp.selected_tag)
            self.fill_values(idx)
            self.update_table()

    def update_iterated_tag(self, tag_name=None):
        """
        Update the widget when the iterated tag is modified.

        :param tag_name (str): Name of the iterated tag.
        """

        if not self.check_box_iterate.isChecked():
            return

        # Update scan list
        if self.main_window.pipeline_manager.scan_list:
            self.scan_list = self.main_window.pipeline_manager.scan_list

        else:

            with self.project.database.data() as database_data:
                self.scan_list = database_data.get_document_names(
                    COLLECTION_CURRENT
                )

        # Clear combo box
        self.combo_box.clear()

        if tag_name is None:
            # Reset tag selection UI
            self.iterated_tag_push_button.setText("Select")
            self.iterated_tag_label.setText("Select a tag")
            self.iteration_table.clear()
            self.iteration_table.setRowCount(0)
            self.iteration_table.setColumnCount(0)

        else:
            # Update tag selection UI
            self.iterated_tag_push_button.setText(tag_name)
            self.iterated_tag_label.setText(f"{tag_name}:")
            # Get tag values from current editor
            current_editor = self.current_editor
            self.all_tag_values = list(current_editor.all_tag_values_list)
            self.combo_box.addItems(current_editor.tag_values_list)

    def update_table(self):
        """
        Update the iteration table with current data.
        """
        current_editor = self.current_editor

        if (
            not self.check_box_iterate.isChecked()
            or current_editor.iterated_tag is None
        ):
            return

        with self.project.database.data() as database_data:

            # Update scan list if empty
            if not self.scan_list:
                self.scan_list = database_data.get_document_names(
                    COLLECTION_CURRENT
                )

            # Clear and prepare table
            iterated_tag = current_editor.iterated_tag
            self.iteration_table.clear()

            if iterated_tag is None:
                self.iteration_table.setRowCount(0)
                self.iteration_table.setColumnCount(0)
                return

            self.iteration_table.setColumnCount(len(self.push_buttons))

            # Set up table headers
            for idx, button in enumerate(self.push_buttons):
                # FIXME should not use GUI text values !!
                header_name = button.text().replace("&", "")

                # Skip if tag doesn't exist in project
                if header_name not in database_data.get_field_names(
                    COLLECTION_CURRENT
                ):
                    print(f"{header_name} not in the project's tags")
                    return

                item = QTableWidgetItem(header_name)
                self.iteration_table.setHorizontalHeaderItem(idx, item)

            # Get current filter value
            current_filter = self.combo_box.currentText().replace("&", "")
            # Create filter query
            filter_query = (
                f"{{{iterated_tag}}} == "
                f"{self.format_filter_value(current_filter)}"
            )
            # Get filtered scans
            filtered_scans = database_data.filter_documents(
                COLLECTION_CURRENT, filter_query
            )
            filtered_filenames = [
                document[TAG_FILENAME] for document in filtered_scans
            ]
            # Get intersection with selected scans
            self.iteration_scans = list(
                set(filtered_filenames).intersection(self.scan_list)
            )
            self.iteration_table.setRowCount(len(self.iteration_scans))

            # Fill table cells
            for row, scan_name in enumerate(self.iteration_scans):

                for col, button in enumerate(self.push_buttons):
                    tag_name = button.text().replace("&", "")
                    value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan_name,
                        field=tag_name,
                    )
                    item = QTableWidgetItem(str(value))
                    self.iteration_table.setItem(row, col, item)

            # Get all iterations scans
            all_iterations_scans = []

            for tag_value in current_editor.tag_values_list:
                filter_query = (
                    f"{{{iterated_tag}}} == "
                    f"{self.format_filter_value(tag_value)}"
                )
                filtered_scans = database_data.filter_documents(
                    COLLECTION_CURRENT, filter_query
                )
                filtered_filenames = [
                    document[TAG_FILENAME] for document in filtered_scans
                ]
                intersection = list(
                    set(filtered_filenames).intersection(self.scan_list)
                )
                all_iterations_scans.append(intersection)

        self.all_iterations_scans = all_iterations_scans
        # Emit signal to update pipeline manager
        self.iteration_table_updated.emit(
            self.iteration_scans, self.all_iterations_scans
        )

    def update_selected_tag(self, selected_tag):
        """
        Update the lists of values corresponding to the selected tag.

        Retrieves all unique values of the selected tag from scans in the
        current collection that also exist in the scan list. Then updates
        the tag value lists in the current pipeline editor.

        :param selected_tag (str): The tag whose values should be
                                   retrieved and updated.
        """

        with self.project.database.data() as database_data:
            # Get intersection of available scans and loaded scan list
            available_scans = database_data.get_document_names(
                COLLECTION_CURRENT
            )

            if not self.scan_list:
                self.scan_list = available_scans

            scans_to_process = set(available_scans).intersection(
                self.scan_list
            )
            # Collect unique tag values from the scans
            tag_values = set()

            for scan_name in scans_to_process:
                tag_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan_name,
                    field=selected_tag,
                )

                # Skip None values
                if tag_value is not None:
                    tag_values.add(str(tag_value))

        tag_values_list = sorted(list(tag_values))
        # Get current editor and update its tag value lists
        current_editor = self.current_editor
        current_editor.tag_values_list = tag_values_list
        current_editor.all_tag_values_list = tag_values_list
        # Update iterated tag
        self.update_iterated_tag(selected_tag)
