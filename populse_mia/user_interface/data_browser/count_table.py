"""
This module provides a tool designed to verify and visualize the presence of
scans in a project based on selected tags. It allows users to dynamically add
and remove tags, and it displays the results in a table format, indicating the
presence or absence of scans with green plus or red cross icons, respectively.

Key Features:
- Dynamic tag selection and visualization.
- Automatic table generation based on tag combinations.
- Clear visual indicators for scan presence or absence.
- Integration with a project's scan data for real-time verification.

Contains:
    Class:
        - CountTable
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
from functools import reduce  # Valid in Python 2.6+, required in Python 3

# PyQt5 imports
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
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
    Tool to verify the scans of a project by visualizing combinations of
    tags.

    This tool allows users to select tags and visualize their combinations
    in a table format. It is composed of push buttons on its top, each one
    corresponding to a tag selected by the user. When, the "Count scans"
    button is clicked, a table is created with all the combinations possible
    for the values of the first n-1 tags. Then, the m values that can take the
    last tag are displayed in the header of the m last columns of the table.
    The cells are then filled with a green plus or a red cross depending on if
    there is at least a scan that has all the tags values or not.

    .. Methods:
        - _create_clickable_label: Create a clickable label with an image
        - _create_push_button: Create and configure a push button for tag
                               selection
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
        - fill_last_tag: Fills the cells corresponding to the last selected tag
        - fill_values: Fill values_list depending on the visualized tags
        - prepare_filter: Prepares the filter in order to fill the count table
        - refresh_layout: Updates the layout of the widget
        - remove_tag: Removes a tag to visualize in the count table
        - select_tag: Opens a pop-up to select which tag to visualize in
                      the count table

    :Example:

    Assume that the current project has scans for two patients (P1 and P2)
    and three time points (T1, T2 and T3). For each (patient, time point),
    several sequences have been made (two RARE, one MDEFT and one FLASH).
    Selecting [PatientName, TimePoint, SequenceName] as tags, the table will
    be:

    +-------------+-----------+------+-------+-------+
    | PatientName | TimePoint | RARE | MDEFT | FLASH |
    +=============+===========+======+=======+=======+
    | P1          | T1        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P1          | T2        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P1          | T3        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P2          | T1        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P2          | T2        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P2          | T3        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+

    with v(n) meaning that n scans corresponds of the selected values for
    (PatientName, TimePoint,SequenceName).

    If no scans corresponds for a triplet value, a red cross will be
    displayed. For example, if the user forgets to import one RARE for P1 at
    T2 and one FLASH for P2 at T3. The table will be:

    +-------------+-----------+------+-------+-------+
    | PatientName | TimePoint | RARE | MDEFT | FLASH |
    +=============+===========+======+=======+=======+
    | P1          | T1        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P1          | T2        | v(1) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P1          | T3        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P2          | T1        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P2          | T2        | v(2) | v(1)  | v(1)  |
    +-------------+-----------+------+-------+-------+
    | P2          | T3        | v(2) | v(1)  | x     |
    +-------------+-----------+------+-------+-------+

    Thus, thanks to the CountTable tool, he or she directly knows if some
    scans are missing.

    """

    def __init__(self, project):
        """
        Initialize the CountTable with the given project.

        :param project: The current project in the software.
        """
        super().__init__()
        self.project = project
        self.setWindowTitle("Count table")
        # Font
        self.font = QFont()
        self.font.setBold(True)
        # values_list will contain the different values of each selected tag
        self.values_list = [[], []]
        self.label_tags = QLabel("Tags: ")
        # Each push button will allow the user to add a tag to the count table
        self.push_buttons = [
            self._create_push_button(f"Tag n°{i + 1}", i) for i in range(2)
        ]
        self._setup_labels()
        self._setup_table()
        self._setup_layout()

    def _create_push_button(self, text, idx):
        """
        Create and configure a push button for tag selection.

        :param text (str): The text to display on the button.
        :param idx (int): The index associated with the button for tag
                          selection.

        :return (QPushButton): A configured QPushButton that triggers the
                               tag selection when clicked.
        """
        button = QPushButton(text)
        button.clicked.connect(lambda: self.select_tag(idx))
        return button

    def _setup_labels(self):
        """Set up the add/remove tag labels with icons."""
        self.remove_tag_label = self._create_clickable_label(
            "red_minus.png", self.remove_tag
        )
        self.add_tag_label = self._create_clickable_label(
            "green_plus.png", self.add_tag
        )

    def _create_clickable_label(self, image_name, click_handler):
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
        label.setObjectName(image_name.split("_")[1].split(".")[0])
        pixmap = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, image_name))
        )
        pixmap = pixmap.scaledToHeight(
            20 if image_name == "red_minus.png" else 15
        )
        label.setPixmap(pixmap)
        label.clicked.connect(click_handler)
        return label

    def _setup_table(self):
        """Set up the table and count button."""
        self.table = QTableWidget()
        self.push_button_count = QPushButton("Count Scans")
        self.push_button_count.clicked.connect(self.count_scans)

    def _setup_layout(self):
        """Set up the layout of the widget."""
        self.v_box_final = QVBoxLayout()
        self.setLayout(self.v_box_final)
        self.refresh_layout()

    def add_tag(self):
        """
        Add a new tag to visualize in the count table.
        """
        idx = len(self.push_buttons)
        new_button = self._create_push_button(f"Tag n°{idx +1 }", idx)
        self.push_buttons.append(new_button)
        self.refresh_layout()

    def count_scans(self):
        """
        Count the number of scans based on selected tags and display the
        result.
        """

        if any(not tag_values for tag_values in self.values_list):
            return

        with self.project.database.data() as database_data:

            if (
                database_data.get_field_attributes(
                    COLLECTION_CURRENT, self.push_buttons[-1].text()
                )
                is None
            ):
                return

        # Clearing the table
        self.table.clear()
        # nb_values will contain, for each index, the number of
        # different values that a tag can take
        self.nb_values = [len(values) for values in self.values_list]
        # The number of rows will be the multiplication of all these
        # values
        self.nb_row = reduce(operator.mul, self.nb_values[:-1], 1)
        # The number of columns will be the addition of the number of
        # selected tags (minus 1) and the number of different values
        # that can take the last selected tag
        self.nb_col = len(self.values_list) - 1 + self.nb_values[-1]
        self.table.setRowCount(self.nb_row)
        self.table.setColumnCount(self.nb_col)
        self.fill_headers()
        self.fill_first_tags()
        self.fill_last_tag()
        self.table.resizeColumnsToContents()

    def fill_first_tags(self):
        """
        Fill the table cells for the first (n-1) selected tags."
        """
        # import set_item_data only here to prevent circular import issue
        from populse_mia.utils import set_item_data

        with self.project.database.data() as database_data:
            cell_text = []

            for col in range(len(self.values_list) - 1):
                # cell_text will contain the n-1 element to display
                cell_text.append(self.values_list[col][0])
                # Filling the last "Total" column
                item = QTableWidgetItem()
                item.setText(str(self.nb_values[col]))
                item.setFont(self.font)
                self.table.setItem(self.nb_row, col, item)

            # Filling the cells of the n-1 first tags
            for row in range(self.nb_row):

                for col in range(len(self.values_list) - 1):
                    item = QTableWidgetItem()
                    tag_name = self.push_buttons[col].text()
                    tag_type = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag_name
                    )["field_type"]
                    set_item_data(item, cell_text[col], tag_type)
                    self.table.setItem(row, col, item)

                # Looping from the (n-1)th tag
                col_checked = len(self.values_list) - 2
                # Flag up will be True when all values of the tag
                # have been iterated
                flag_up = False

                while col_checked >= 0:

                    if flag_up:

                        # In this case, the value of the right column has
                        # reach its last value
                        # This value has been reset to the first value
                        if (
                            cell_text[col_checked]
                            == self.values_list[col_checked][-1]
                        ):
                            # If the value that has been displayed is the
                            # last one, the flag stays the same, the value
                            # of the column on the left has to be changed
                            cell_text[col_checked] = self.values_list[
                                col_checked
                            ][0]

                        else:
                            # Else we iterate on the next value
                            idx = self.values_list[col_checked].index(
                                cell_text[col_checked]
                            )
                            cell_text[col_checked] = self.values_list[
                                col_checked
                            ][idx + 1]
                            flag_up = False

                    if (col_checked > 0 and len(self.values_list) - 1 > 1) or (
                        len(self.values_list) - 1 == 1
                    ):

                        if (
                            cell_text[col_checked]
                            == self.values_list[col_checked][-1]
                        ):
                            # If the value that has been displayed is the
                            # last one, the flag is set to True, the value of
                            # the column on the left has to be changed
                            cell_text[col_checked] = self.values_list[
                                col_checked
                            ][0]
                            flag_up = True

                        else:
                            # Else we iterate on the next value and reset the
                            # flag
                            idx = self.values_list[col_checked].index(
                                cell_text[col_checked]
                            )
                            cell_text[col_checked] = self.values_list[
                                col_checked
                            ][idx + 1]
                            flag_up = False

                        if not flag_up:
                            # If there is nothing to do, we quit the loop
                            break

                    col_checked -= 1

    def fill_headers(self):
        """
        Fills the headers of the table depending on the selected tags
        """

        # import set_item_data only here to prevent circular import issue
        from populse_mia.utils import set_item_data

        idx_end = 0

        # Headers
        for idx in range(len(self.values_list) - 1):
            header_name = self.push_buttons[idx].text()
            item = QTableWidgetItem()
            item.setText(header_name)
            self.table.setHorizontalHeaderItem(idx, item)
            idx_end = idx

        # idx_last_tag corresponds to the index of the (n-1)th tag
        self.idx_last_tag = idx_end
        last_tag = self.push_buttons[len(self.values_list) - 1].text()

        with self.project.database.data() as database_data:
            last_tag_type = database_data.get_field_attributes(
                COLLECTION_CURRENT, last_tag
            )["field_type"]

        for header_name in self.values_list[-1]:
            idx_end += 1
            item = QTableWidgetItem()
            set_item_data(item, header_name, last_tag_type)
            self.table.setHorizontalHeaderItem(idx_end, item)

        # Adding a "Total" row and to count the scans
        self.table.insertRow(self.nb_row)
        item = QTableWidgetItem()
        item.setText("Total")
        item.setFont(self.font)
        self.table.setVerticalHeaderItem(self.nb_row, item)

    def fill_last_tag(self):
        """
        Fills the cells corresponding to the last selected tag
        """
        # import table_to_database only here to prevent circular import issue
        from populse_mia.utils import table_to_database

        with self.project.database.data() as database_data:

            # Cells of the last tag
            for col in range(self.idx_last_tag + 1, self.nb_col):
                nb_scans_ok = 0

                # Creating a tag_list that will contain
                # couples tag_name/tag_value that
                # will then querying the Database
                for row in range(self.nb_row):
                    tag_list = []

                    for idx_first_columns in range(self.idx_last_tag + 1):
                        tag_name = self.table.horizontalHeaderItem(
                            idx_first_columns
                        ).text()
                        tag_type = database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag_name
                        )["field_type"]
                        value_str = self.table.item(
                            row, idx_first_columns
                        ).data(Qt.EditRole)
                        value_database = table_to_database(value_str, tag_type)
                        tag_list.append([tag_name, value_database])

                    tag_last_columns = self.push_buttons[-1].text()
                    tag_last_columns_type = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag_last_columns
                    )["field_type"]
                    value_last_columns_str = self.table.horizontalHeaderItem(
                        col
                    ).data(Qt.EditRole)
                    value_last_columns_database = table_to_database(
                        value_last_columns_str, tag_last_columns_type
                    )
                    tag_list.append(
                        [tag_last_columns, value_last_columns_database]
                    )
                    item = QTableWidgetItem()
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                    # Getting the list of the scans that corresponds to the
                    # couples tag_name/tag_values
                    filtered_scans = database_data.filter_documents(
                        COLLECTION_CURRENT, self.prepare_filter(tag_list)
                    )
                    # List of scans created, given the generator
                    list_scans = [
                        scan[TAG_FILENAME] for scan in filtered_scans
                    ]
                    sources_images_dir = Config().getSourceImageDir()

                    if list_scans:
                        icon = QIcon(
                            os.path.join(sources_images_dir, "green_v.png")
                        )
                        length = len(list_scans)
                        nb_scans_ok += length
                        text = str(length)
                        item.setText(text)
                        # Setting as tooltip all the corresponding scans
                        tool_tip = "\n".join(list_scans)
                        item.setToolTip(tool_tip)

                    else:
                        icon = QIcon(
                            os.path.join(sources_images_dir, "red_cross.png")
                        )

                    item.setIcon(icon)
                    self.table.setItem(row, col, item)

                item = QTableWidgetItem()
                item.setText(str(nb_scans_ok))
                item.setFont(self.font)
                self.table.setItem(self.nb_row, col, item)

    def fill_values(self, idx):
        """
        Fill values_list depending on the visualized tags

        :param idx: index of the select tag
        """

        tag_name = self.push_buttons[idx].text()
        values = []

        with self.project.database.data() as database_data:

            for scan in database_data.get_document_names(COLLECTION_CURRENT):
                current_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan,
                    field=tag_name,
                )
                if current_value is not None:
                    values.append(current_value)

        idx_to_fill = len(self.values_list)

        while len(self.values_list) <= idx:
            self.values_list.insert(idx_to_fill, [])
            idx_to_fill += 1

        if self.values_list[idx] is not None:
            self.values_list[idx] = []

        for value in values:
            if value not in self.values_list[idx]:
                self.values_list[idx].append(value)

    @staticmethod
    def prepare_filter(couples):
        """
        Prepares the filter in order to fill the count table.

        :param couples: (tag, value) couples
        :return: Str query of the corresponding filter
        """
        query_parts = []

        for tag, value in couples:

            if isinstance(value, list):
                query_parts.append(f"({{{tag}}} == {value})")

            else:
                query_parts.append(f'({{{tag}}} == "{value}")')

        return f"({' AND '.join(query_parts)})"

    def refresh_layout(self):
        """
        Updates the layout of the widget
        """

        self.h_box_top = QHBoxLayout()
        self.h_box_top.setSpacing(10)
        self.h_box_top.addWidget(self.label_tags)

        for tag_label in self.push_buttons:
            self.h_box_top.addWidget(tag_label)

        self.h_box_top.addWidget(self.add_tag_label)
        self.h_box_top.addWidget(self.remove_tag_label)
        self.h_box_top.addWidget(self.push_button_count)
        self.h_box_top.addStretch(1)

        self.v_box_final.addLayout(self.h_box_top)
        self.v_box_final.addWidget(self.table)

    def remove_tag(self):
        """
        Removes a tag to visualize in the count table
        """

        push_button = self.push_buttons[-1]
        push_button.deleteLater()
        push_button = None
        del self.push_buttons[-1]
        del self.values_list[-1]
        self.refresh_layout()

    def select_tag(self, idx):
        """
        Opens a pop-up to select which tag to visualize in the count table

        :param idx: the index of the selected push button
        """

        with self.project.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)

        pop_up = PopUpSelectTagCountTable(
            self.project,
            field_names,
            self.push_buttons[idx].text(),
        )
        if pop_up.exec_():
            if pop_up.selected_tag is not None:
                self.push_buttons[idx].setText(pop_up.selected_tag)
                self.fill_values(idx)
