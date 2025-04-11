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


import os

# PyQt5 imports
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

from populse_mia.data_manager import COLLECTION_CURRENT, TAG_FILENAME
from populse_mia.software_properties import Config

# MIA imports
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
        - add_tag: adds a tag to visualize in the iteration table
        - emit_iteration_table_updated: emits a signal when the iteration
                                        scans have been updated
        - fill_values: fill values_list depending on the visualized tags
        - filter_values: select the tag values used for the iteration
        - refresh_layout: updates the layout of the widget
        - remove_tag: removes a tag to visualize in the iteration table
        - select_iteration_tag: opens a pop-up to let the user select on which
                                tag to iterate
        - select_visualized_tag: opens a pop-up to let the user select which
                                 tag to visualize in the iteration table
        - update_iterated_tag: updates the widget
        - update_table: updates the iteration table
        - update_selected_tag: updates the selected tag for current pipeline
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
        # Set up layout
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)
        self.refresh_layout()

    def _create_tag_button(self, text, index):
        """Create a new tag button with the given text and index.

        :param text (str): Text to display on the button.
        :param index (int): Index of the button in the push_buttons list.
        """
        button = QPushButton(text)
        button.clicked.connect(lambda: self.select_visualized_tag(index))
        self.push_buttons.insert(index, button)
        return button

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

        if self.check_box_iterate.checkState():

            if hasattr(self, "scans"):
                self.iteration_table_updated.emit(
                    self.iteration_scans, self.all_iterations_scans
                )

            else:
                self.iteration_table_updated.emit(
                    self.scan_list, [self.scan_list]
                )

        else:
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

                if current_value is not None:
                    values.append(current_value)

        # Ensure values_list has enough slots
        while len(self.values_list) <= idx:
            self.values_list.append([])

        # Reset and fill values for this tag
        self.values_list[idx] = list(set(values))

    def filter_values(self):
        """Open a dialog to select specific tag values for iteration."""
        # fmt: off
        current_editor = (
            self.main_window.pipeline_manager.pipelineEditorTabs
            .get_current_editor()
        )
        # fmt: on
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

    def refresh_layout(self):
        """Update the layout of the widget.

        Called in widget's initialization and when a tag push button
        is added or removed.
        """

        # Clear existing layout
        for i in reversed(range(self.v_layout.count())):
            item = self.v_layout.itemAt(i)

            if item:
                self.v_layout.removeItem(item)

        # Create top row controls
        first_v_layout = QVBoxLayout()
        first_v_layout.addWidget(self.check_box_iterate)
        second_v_layout = QVBoxLayout()
        second_v_layout.addWidget(self.label_iterate)
        second_v_layout.addWidget(self.iterated_tag_label)
        third_v_layout = QVBoxLayout()
        third_v_layout.addWidget(self.iterated_tag_push_button)
        hbox = QHBoxLayout()
        hbox.addWidget(self.combo_box)
        hbox.addWidget(self.filter_button)
        third_v_layout.addLayout(hbox)
        top_layout = QHBoxLayout()
        top_layout.addLayout(first_v_layout)
        top_layout.addLayout(second_v_layout)
        top_layout.addLayout(third_v_layout)
        # Add components to main layout
        self.v_layout.addLayout(top_layout)
        self.v_layout.addWidget(self.iteration_table)
        # Create tag visualization controls
        self.h_box = QHBoxLayout()
        self.h_box.setSpacing(10)
        self.h_box.addWidget(self.label_tags)

        for tag_button in self.push_buttons:
            self.h_box.addWidget(tag_button)

        self.h_box.addWidget(self.add_tag_label)
        self.h_box.addWidget(self.remove_tag_label)
        self.h_box.addStretch(1)
        self.v_layout.addLayout(self.h_box)

    def remove_tag(self):
        """Remove the last tag button from the visualization list."""

        if self.push_buttons:
            # Remove the last button
            button = self.push_buttons.pop()
            button.deleteLater()

            # Remove corresponding values
            if len(self.values_list) > 0:
                self.values_list.pop()

            # Update UI
            self.refresh_layout()
            self.update_table()

    def select_iteration_tag(self):
        """Open a dialog to let the user select which tag to iterate over."""
        # fmt: off
        current_editor = (
            self.main_window.pipeline_manager
            .pipelineEditorTabs.get_current_editor()
        )
        # fmt: on
        available_fields = self.project.session.get_fields_names(
            COLLECTION_CURRENT
        )
        ui_select = PopUpSelectTagCountTable(
            self.project,
            available_fields,
            current_editor.iterated_tag,
        )

        if ui_select.exec_():

            if not (
                current_editor.iterated_tag is None
                and ui_select.selected_tag is None
            ):
                current_editor.iterated_tag = ui_select.selected_tag
                self.update_selected_tag(ui_select.selected_tag)

    def select_visualized_tag(self, idx):
        """
        Open a dialog to select which tag to visualize in the iteration table.

        :param idx (int): Index of the clicked push button.
        """
        available_fields = self.project.session.get_fields_names(
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
            self.iteration_table.setColumnCount(len(self.push_buttons))

        else:
            # Update tag selection UI
            self.iterated_tag_push_button.setText(tag_name)
            self.iterated_tag_label.setText(f"{tag_name}:")
            # Get tag values from current editor
            # fmt: off
            current_editor = (
                self.main_window.pipeline_manager
                .pipelineEditorTabs.get_current_editor()
            )
            # fmt: on
            self.all_tag_values = list(current_editor.all_tag_values_list)
            self.combo_box.addItems(current_editor.tag_values_list)
            # Update table
            self.update_table()

    def update_table(self):
        """
        Update the iteration table with current data.
        """

        with self.project.database.data() as database_data:

            # Update scan list if empty
            if not self.scan_list:
                self.scan_list = database_data.get_document_names(
                    COLLECTION_CURRENT
                )

            # Clear and prepare table
            self.iteration_table.clear()
            self.iteration_table.setColumnCount(len(self.push_buttons))
            # fmt: off
            current_editor = (
                self.main_window.pipeline_manager
                .pipelineEditorTabs.get_current_editor()
            )
            # fmt: on
            iterated_tag = current_editor.iterated_tag

            if iterated_tag is None:
                return

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
            filter_query = f'({{{iterated_tag}}} == "{current_filter}")'
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
                filter_query = f'({{{iterated_tag}}} == "{tag_value}")'
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
                tag_values.add(str(tag_value))

        tag_values_list = sorted(list(tag_values))
        # Get current editor and update its tag value lists
        # fmt: off
        current_editor = (
            self.main_window.pipeline_manager
            .pipelineEditorTabs.get_current_editor()
        )
        # fmt: on
        current_editor.tag_values_list = tag_values_list
        current_editor.all_tag_values_list = tag_values_list
        # Update iterated tag
        self.update_iterated_tag(selected_tag)
