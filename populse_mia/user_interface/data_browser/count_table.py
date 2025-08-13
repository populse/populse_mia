"""
Medical Scan Completeness Verification Tool

This module provides a sophisticated quality assurance tool for medical
imaging projects, enabling systematic verification of scan completeness
through interactive tag-based analysis. The tool helps identify missing
scans, incomplete datasets, and data inconsistencies across multiple metadata
dimensions.

The primary component is a dynamic table-based interface that visualizes all
possible combinations of selected metadata tags (patient names, scan types,
time points, etc.) and indicates which combinations have corresponding scan
data available.

Core Functionality:
    - Interactive tag selection with expandable interface (2 to n tags)
    - Real-time database querying and scan counting
    - Matrix visualization of tag combinations vs. data availability
    - Visual indicators: ✓ (green checkmark) for present data,
                         ✗ (red cross) for missing
    - Detailed tooltips showing specific scan filenames
    - Statistical summaries with total counts per category

Use Cases:
    - Quality assurance before data analysis
    - Identifying incomplete patient visits or missing sequences
    - Verifying protocol compliance across studies
    - Dataset completeness reporting
    - Pre-processing validation for longitudinal studies

Technical Features:
    - Efficient database integration with lazy loading
    - Dynamic UI generation based on selected metadata
    - Scalable to handle large datasets with multiple tag dimensions
    - Qt-based interface with responsive table resizing
    - Memory-efficient combination generation using odometer algorithms

Example Workflow:
    1. Select relevant metadata tags (e.g., PatientName, TimePoint,
       SequenceName)
    2. Generate combination matrix showing all expected data points
    3. Review visual indicators to identify missing scans
    4. Use tooltips to examine specific scan files
    5. Export or act on completeness findings

Contains:
    Class:
        - CountTable: Main dialog class providing the scan verification
                      interface
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import operator
import os
from functools import reduce
from typing import Any, Callable

# PyQt5 imports
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from populse_mia.data_manager import COLLECTION_CURRENT, TAG_FILENAME

# Populse_MIA imports
from populse_mia.software_properties import Config
from populse_mia.user_interface.pop_ups import (
    ClickableLabel,
    PopUpSelectTagCountTable,
)


class CountTable(QDialog):
    """
    A visual tool for verifying medical scan completeness through tag
    combination analysis.

    This dialog provides an interactive interface to analyze medical scan
    data by selecting multiple tags (metadata fields) and displaying their
    combinations in a matrix format. The tool helps identify missing scans
    by showing which combinations of tag values have corresponding data.

    The interface consists of:
    - Dynamic tag selection buttons (expandable from 2 to n tags)
    - Add/remove controls for tag management
    - A results table showing all possible combinations
    - Visual indicators (✓/✗) for data presence/absence

    Table Structure:
        - Rows: All combinations of the first (n-1) selected tags
        - Columns: First (n-1) tag names + values of the last tag
        - Cells: Count of matching scans or absence indicator
        - Footer: Total counts per column

    Example:
        With tags [PatientName, TimePoint, SequenceName] for 2 patients
        (P1, P2), 3 timepoints (T1, T2, T3), and sequences
        (RARE, MDEFT, FLASH):

        +-------------+-----------+------+-------+-------+
        | PatientName | TimePoint | RARE | MDEFT | FLASH |
        +=============+===========+======+=======+=======+
        | P1          | T1        | ✓(2) | ✓(1)  | ✓(1)  |
        | P1          | T2        | ✓(1) | ✓(1)  | ✓(1)  |  ← Missing 1 RARE
        | P1          | T3        | ✓(2) | ✓(1)  | ✓(1)  |
        | P2          | T1        | ✓(2) | ✓(1)  | ✓(1)  |
        | P2          | T2        | ✓(2) | ✓(1)  | ✓(1)  |
        | P2          | T3        | ✓(2) | ✓(1)  | ✗     |  ← Missing FLASH
        +-------------+-----------+------+-------+-------+
        | Total       |           | 11   | 6     | 5     |
        +-------------+-----------+------+-------+-------+

    Key Features:
        - Dynamic tag addition/removal
        - Real-time scan counting
        - Visual missing data indicators
        - Hover tooltips showing specific scan files
        - Automatic table resizing

    .. Methods:
        - _create_clickable_label: Create a clickable label with an image
        - _create_push_button: Create and configure a push button for tag
                               selection
        - _setup_components: Initialize basic UI components
        - _setup_labels: Set up the add/remove tag labels with icons
        - _setup_layout: Set up the layout of the widget
        - _setup_table: Set up the table and count button
        - add_tag: Adds a tag to visualize in the count table
        - count_scans: Counts the number of scans depending on the selected
                       tags and displays the result in the table
        - fill_first_tags: Fills the cells of the table corresponding to the
                           (n-1) first selected tags
        - fill_headers: Fills the headers of the table depending on the
                        selected tags
        - fill_last_tag: Fills the cells corresponding to the last selected
                         tag
        - fill_values: Fill values_list depending on the visualized tags
        - prepare_filter: Prepares the filter in order to fill the count table
        - refresh_layout: Updates the layout of the widget
        - remove_tag: Removes a tag to visualize in the count table
        - select_tag: Opens a pop-up to select which tag to visualize in
                      the count table
    """

    def __init__(self, project) -> None:
        """
        Initialize the CountTable with the given project.

        :param project: The current medical imaging project containing
                        scan database
        """
        super().__init__()
        self.project = project
        self.setWindowTitle("Count table")
        # UI properties
        self.font = QFont()
        self.font.setBold(True)
        # Data structures
        # Tag values for each selected tag
        self.values_list: list[list[Any]] = [[], []]
        self.push_buttons: list[QPushButton] = []
        # Initialize UI components
        self._setup_components()
        self._setup_labels()
        self._setup_table()
        self._setup_layout()

    def _create_clickable_label(
        self, image_name: str, click_handler: Callable
    ) -> "ClickableLabel":
        """
         Create a clickable label with an image.

        :param image_name (str): The filename of the image to display on the
                                 label.
        :param click_handler (Callable): The function to be called when the
                                         label is clicked.

        :return (ClickableLabel): A label displaying the specified image,
                                  which triggers the click handler when
                                  clicked.
        """
        sources_images_dir = Config().getSourceImageDir()
        label = ClickableLabel()
        # Extract color from filename for object naming
        color = image_name.split("_")[1].split(".")[0]
        label.setObjectName(color)
        # Load and scale icon
        pixmap_path = os.path.join(sources_images_dir, image_name)
        pixmap = QPixmap(os.path.relpath(pixmap_path))
        height = 20 if image_name == "red_minus.png" else 15
        pixmap = pixmap.scaledToHeight(height)
        label.setPixmap(pixmap)
        label.clicked.connect(click_handler)
        return label

    def _create_push_button(self, text: str, idx: int) -> QPushButton:
        """
        Create and configure a tag selection button.

        :param text (str): The text to display on the button.
        :param idx (int): The index associated with the button for tag
                          selection.

        :return (QPushButton): A configured QPushButton that triggers the
                               tag selection when clicked.
        """
        button = QPushButton(text)
        button.clicked.connect(lambda: self.select_tag(idx))
        return button

    def _setup_components(self) -> None:
        """
        Initialize basic UI components.
        """
        self.label_tags = QLabel("Tags: ")
        # Each push button will allow the user to add a tag to the count table
        self.push_buttons = [
            self._create_push_button(f"Tag n°{i + 1}", i) for i in range(2)
        ]

    def _setup_labels(self) -> None:
        """
        Initialize add/remove control labels with icons.
        """
        self.remove_tag_label = self._create_clickable_label(
            "red_minus.png", self.remove_tag
        )
        self.add_tag_label = self._create_clickable_label(
            "green_plus.png", self.add_tag
        )

    def _setup_layout(self) -> None:
        """
        Initialize main widget layout.
        """
        self.v_box_final = QVBoxLayout()
        self.setLayout(self.v_box_final)
        # Stacked area to switch between table and placeholder message
        self.content_stack = QStackedLayout()
        self.content_stack.addWidget(self.table)  # index 0
        self.content_stack.addWidget(self.placeholder)  # index 1
        self.content_stack.setCurrentWidget(self.table)
        self.refresh_layout()
        self.v_box_final.addLayout(self.content_stack)

    def _setup_table(self) -> None:
        """
        Initialize table widget, placeholder label and count button.
        """
        self.table = QTableWidget()
        # Placeholder message shown when tags are missing
        self.placeholder = QLabel(
            "At least one of the tags does not contain any values.\n"
            "The result cannot be constructed."
        )
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.push_button_count = QPushButton("Count Scans")
        self.push_button_count.clicked.connect(self.count_scans)

    def add_tag(self) -> None:
        """
        Add a new tag to visualize in the count table.
        """
        idx = len(self.push_buttons)
        new_button = self._create_push_button(f"Tag n°{idx + 1}", idx)
        self.push_buttons.append(new_button)
        self.refresh_layout()

    def count_scans(self) -> None:
        """
        Generate and populate the scan count table.

        Creates a matrix showing all combinations of selected tag values,
        with counts or indicators for each combination's scan availability.
        Early returns if no tags are selected or if database access fails.
        """

        # Validate that all tags have values
        if any(not tag_values for tag_values in self.values_list):
            self.content_stack.setCurrentWidget(self.placeholder)
            return

        # Validate last button corresponds to database field
        with self.project.database.data() as database_data:

            if (
                database_data.get_field_attributes(
                    COLLECTION_CURRENT, self.push_buttons[-1].text()
                )
                is None
            ):
                # Show message if the last tag isn't a valid field
                self.content_stack.setCurrentWidget(self.placeholder)
                return

        # We have valid tags: show the table view
        self.content_stack.setCurrentWidget(self.table)
        # Reset and build the table
        self.table.clear()
        # Calculate dimensions
        # nb_values: number of distinct values for each selected tag
        self.nb_values = [len(values) for values in self.values_list]
        # The number of rows will be the multiplication of all these
        # values
        self.nb_row = reduce(operator.mul, self.nb_values[:-1], 1)
        # The number of columns will be the addition of the number of
        # selected tags (minus 1) and the number of different values
        # that can take the last selected tag
        self.nb_col = len(self.values_list) - 1 + self.nb_values[-1]
        # Configure table
        self.table.setRowCount(self.nb_row)
        self.table.setColumnCount(self.nb_col)
        # Fill table with headers and data
        self.fill_headers()
        self.fill_first_tags()
        self.fill_last_tag()
        self.table.resizeColumnsToContents()

    def fill_first_tags(self) -> None:
        """
        Populate table cells for the first (n-1) selected tags.

        Generates all possible combinations of the first n-1 tag values
        and fills corresponding table cells. Also adds total counts
        in the bottom row.
        """
        # import set_item_data only here to prevent circular import issue
        from populse_mia.utils import set_item_data

        with self.project.database.data() as database_data:
            # Initialize with first values for each tag
            # current_combination will contain the n-1 element to display
            current_combination = [
                values[0] for values in self.values_list[:-1]
            ]

            # Fill the total row with tag value counts
            for col, count in enumerate(self.nb_values[:-1]):
                item = QTableWidgetItem(str(count))
                item.setFont(self.font)
                self.table.setItem(self.nb_row, col, item)

            # Generate all combinations and fill cells
            for row in range(self.nb_row):

                # Fill a single row with tag combination values
                for col, value in enumerate(current_combination):
                    item = QTableWidgetItem()
                    tag_name = self.push_buttons[col].text()
                    tag_type = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag_name
                    )["field_type"]
                    set_item_data(item, value, tag_type)
                    self.table.setItem(row, col, item)

                # Advance to next combination using odometer-like logic
                if not current_combination:
                    return

                # Start from rightmost position
                pos = len(current_combination) - 1

                while pos >= 0:
                    current_idx = self.values_list[pos].index(
                        current_combination[pos]
                    )

                    if current_idx < len(self.values_list[pos]) - 1:
                        # Can increment this position
                        current_combination[pos] = self.values_list[pos][
                            current_idx + 1
                        ]
                        break

                    else:
                        # Reset this position and carry over
                        current_combination[pos] = self.values_list[pos][0]
                        pos -= 1

    def fill_headers(self) -> None:
        """
        Populate table headers with tag names and last tag values.

        Sets horizontal headers for:
            - First n-1 columns: tag names
            - Remaining columns: values of the last selected tag

        Also adds a "Total" row header.
        """

        # import set_item_data only here to prevent circular import issue
        from populse_mia.utils import set_item_data

        # Set headers for first n-1 tags
        for idx in range(len(self.values_list) - 1):
            header_name = self.push_buttons[idx].text()
            item = QTableWidgetItem(header_name)
            self.table.setHorizontalHeaderItem(idx, item)

        # idx_last_tag corresponds to the index of the (n-1)th tag
        self.idx_last_tag = len(self.values_list) - 2

        # Set headers for last tag values
        # Fill headers with last tag's possible values
        last_tag = self.push_buttons[-1].text()

        with self.project.database.data() as database_data:
            last_tag_type = database_data.get_field_attributes(
                COLLECTION_CURRENT, last_tag
            )["field_type"]

        for col_offset, header_value in enumerate(self.values_list[-1]):
            col_idx = self.idx_last_tag + 1 + col_offset
            item = QTableWidgetItem()
            set_item_data(item, header_value, last_tag_type)
            self.table.setHorizontalHeaderItem(col_idx, item)

        # Add and configure the totals row
        self.table.insertRow(self.nb_row)
        item = QTableWidgetItem("Total")
        item.setFont(self.font)
        self.table.setVerticalHeaderItem(self.nb_row, item)

    def fill_last_tag(self) -> None:
        """
        Populate cells for the last selected tag with scan counts or
        indicators.

        For each combination of first n-1 tags and each value of the last tag:
            - Queries database for matching scans
            - Shows count with checkmark if scans exist
            - Shows red X if no scans found
            - Adds scan filenames as tooltip
            - Updates column totals
        """
        # import table_to_database only here to prevent circular import issue
        from populse_mia.utils import table_to_database

        sources_images_dir = Config().getSourceImageDir()

        with self.project.database.data() as database_data:

            # Process each column for the last tag
            for col in range(self.idx_last_tag + 1, self.nb_col):
                total_scans = 0

                # Creating a tag_list that will contain
                # couples tag_name/tag_value that
                # will then querying the Database
                for row in range(self.nb_row):
                    tag_list = []

                    # Add filters for first n-1 tags
                    for tag_col in range(self.idx_last_tag + 1):
                        tag_name = self.table.horizontalHeaderItem(
                            tag_col
                        ).text()
                        tag_type = database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag_name
                        )["field_type"]
                        value_display = self.table.item(row, tag_col).data(
                            Qt.EditRole
                        )
                        value_db = table_to_database(value_display, tag_type)
                        tag_list.append([tag_name, value_db])

                    # Add filter for the last tag
                    last_tag_name = self.push_buttons[-1].text()
                    last_tag_type = database_data.get_field_attributes(
                        COLLECTION_CURRENT, last_tag_name
                    )["field_type"]
                    last_value_display = self.table.horizontalHeaderItem(
                        col
                    ).data(Qt.EditRole)
                    last_value_db = table_to_database(
                        last_value_display, last_tag_type
                    )
                    tag_list.append([last_tag_name, last_value_db])
                    # Query database for scans matching the filter criteria
                    filter_query = self.prepare_filter(tag_list)
                    filtered_scans = database_data.filter_documents(
                        COLLECTION_CURRENT, filter_query
                    )
                    matching_scans = [
                        scan[TAG_FILENAME] for scan in filtered_scans
                    ]
                    # Create table item showing scan count with appropriate
                    # icon
                    item = QTableWidgetItem()
                    item.setFlags(QtCore.Qt.ItemIsEnabled)

                    if matching_scans:
                        icon = QIcon(
                            os.path.join(sources_images_dir, "green_v.png")
                        )
                        item.setText(str(len(matching_scans)))
                        # Setting as tooltip all the corresponding scans
                        item.setToolTip("\n".join(matching_scans))

                    else:
                        # No scans - show red X
                        icon = QIcon(
                            os.path.join(sources_images_dir, "red_cross.png")
                        )

                    item.setIcon(icon)
                    self.table.setItem(row, col, item)
                    total_scans += len(matching_scans)

                item = QTableWidgetItem(str(total_scans))
                item.setFont(self.font)
                self.table.setItem(self.nb_row, col, item)

    def fill_values(self, idx: int) -> None:
        """
        Populate values list for the tag at the specified index.

        Extracts all unique values for the selected tag from the database
        and stores them for table generation.

        :param idx (Int): Index of the select tag
        """

        tag_name = self.push_buttons[idx].text()
        unique_values = []

        with self.project.database.data() as database_data:

            for scan in database_data.get_document_names(COLLECTION_CURRENT):
                value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan,
                    field=tag_name,
                )
                if value is not None and value not in unique_values:
                    unique_values.append(value)

        # Ensure values_list has enough slots
        while len(self.values_list) < idx + 1:
            self.values_list.append([])

        self.values_list[idx] = sorted(unique_values)

    @staticmethod
    def prepare_filter(tag_value_pairs: list[tuple[str, Any]]) -> str:
        """
        Build database query string from tag-value pairs.

        :param tag_value_pairs: List of (tag_name, value) tuples

        :return: Query string for database filtering
        """
        conditions = []

        for tag, value in tag_value_pairs:

            if isinstance(value, list):
                conditions.append(f"({{{tag}}} == {value})")

            else:
                conditions.append(f'({{{tag}}} == "{value}")')

        return f"({' AND '.join(conditions)})"

    def refresh_layout(self) -> None:
        """
        Update the widget layout after adding/removing tags.
        """

        # Clear existing top layout content
        if hasattr(self, "h_box_top"):

            while self.h_box_top.count():
                child = self.h_box_top.takeAt(0)

                if child.widget():
                    child.widget().setParent(None)

        # Rebuild top controls
        self.h_box_top = QHBoxLayout()
        self.h_box_top.setSpacing(10)

        # Add all components
        self.h_box_top.addWidget(self.label_tags)

        for button in self.push_buttons:
            self.h_box_top.addWidget(button)

        self.h_box_top.addWidget(self.add_tag_label)
        self.h_box_top.addWidget(self.remove_tag_label)
        self.h_box_top.addWidget(self.push_button_count)
        self.h_box_top.addStretch(1)

        # Add to main layout
        self.v_box_final.addLayout(self.h_box_top)

    def remove_tag(self) -> None:
        """
        Remove the last tag selection button and its data.
        """

        if len(self.push_buttons) <= 2:  # Maintain minimum of 2 tags
            return

        # Clean up last button
        last_button = self.push_buttons.pop()
        last_button.deleteLater()

        # Remove corresponding data
        if self.values_list:
            self.values_list.pop()

        self.refresh_layout()

    def select_tag(self, idx: int) -> None:
        """
        Open tag selection dialog for the specified button.

        :param idx (Int): The index of the button/tag to configure
        """

        with self.project.database.data() as database_data:
            available_fields = database_data.get_field_names(
                COLLECTION_CURRENT
            )

        popup = PopUpSelectTagCountTable(
            self.project,
            available_fields,
            self.push_buttons[idx].text(),
        )
        if popup.exec_():

            if popup.selected_tag is not None:
                self.push_buttons[idx].setText(popup.selected_tag)
                self.fill_values(idx)
