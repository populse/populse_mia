"""
Module to define the advanced search.

Contains:
    Class:
        - AdvancedSearch
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import logging
import os
from typing import get_origin

# PyQt5 imports
from PyQt5.QtCore import QObjectCleanupHandler
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from populse_mia.data_manager import (
    ALL_TYPES,
    COLLECTION_CURRENT,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_STRING,
    TAG_FILENAME,
)

# Populse_MIA imports
from populse_mia.software_properties import Config
from populse_mia.user_interface.pop_ups import ClickableLabel

logger = logging.getLogger(__name__)


class AdvancedSearch(QWidget):
    """Class that manages the widget of the advanced search

    The advanced search creates a complex query to the database and is a
    combination of several "query lines" which are linked with AND or OR and
    all composed of:
    - A negation or not
    - A tag name or all visible tags
    - A condition (==, !=, >, <, >=, <=, CONTAINS, IN, BETWEEN)
    - A value

    .. Methods:
        - add_search_bar: create and define the advanced research bar
        - apply_filter: apply an opened filter to update the table.
        - clearLayout: called to clear a layout (not used currently in order
                       to fix issue #72)
        - displayConditionRules: set the list of condition choices, depending
                                 on the tag type
        - displayValueRules: update the placeholder text when the condition
                             choice is changed
        - get_filters: get the filters in list form
        - launch_search: start the search and update the table
        - prepare_filters: prepare the str representation of the filter
        - refresh_search: refresh the widget
        - remove_row: remove a row
        - rows_borders_added: add the links and the added row to the good rows
        - rows_borders_removed: link and adds row removed from every row
        - rowsContainsWidget: check if the widget is still used
                              (not used currently)
        - show_search: reset the rows when the Advanced Search button is
                       clicked
    """

    def __init__(
        self,
        project,
        data_browser,
        scans_list=None,
        tags_list=None,
        from_pipeline=False,
    ):
        """Initialization of the AdvancedSearch class.

        :param project: current project in the software
        :param data_browser: parent data browser widget
        :param scans_list: current list of the documents
        :param tags_list: list of the visualized tags
        :param from_pipeline: True if the widget is called from the pipeline
          manager

        """
        super().__init__()

        if scans_list is None:
            scans_list = []

        if tags_list is None:
            tags_list = []

        self.project = project
        self.dataBrowser = data_browser
        self.rows = []
        self.scans_list = scans_list
        self.tags_list = tags_list
        self.from_pipeline = from_pipeline
        self.search = QPushButton("Search")
        self.search.setFixedWidth(100)

    def add_search_bar(self):
        """Create and define the advanced research bar."""
        row_layout = []
        # NOT choice
        not_choice = QComboBox()
        not_choice.setObjectName("not")
        not_choice.addItem("")
        not_choice.addItem("NOT")
        # Field choice
        field_choice = QComboBox()
        field_choice.setObjectName("field")

        if len(self.tags_list) > 0:

            for tag in self.tags_list:
                field_choice.addItem(tag)

        else:

            with self.project.database.data() as database_data:

                for tag in database_data.get_shown_tags():
                    field_choice.addItem(tag)

        field_choice.model().sort(0)
        field_choice.addItem("All visualized tags")
        # Value choice
        condition_value = QLineEdit()
        condition_value.setObjectName("value")
        # Condition choice
        condition_choice = QComboBox()
        condition_choice.setObjectName("condition")
        condition_choice.addItem("==")
        condition_choice.addItem("!=")
        condition_choice.addItem(">=")
        condition_choice.addItem("<=")
        condition_choice.addItem(">")
        condition_choice.addItem("<")
        condition_choice.addItem("BETWEEN")
        condition_choice.addItem("IN")
        condition_choice.addItem("CONTAINS")
        condition_choice.addItem("HAS VALUE")
        condition_choice.addItem("HAS NO VALUE")
        condition_choice.model().sort(0)
        # Signal to update the placeholder text of the value
        condition_choice.currentTextChanged.connect(
            lambda: self.displayValueRules(condition_choice, condition_value)
        )
        # Signal to update the list of conditions, depending on the tag type
        field_choice.currentTextChanged.connect(
            lambda: self.displayConditionRules(field_choice, condition_choice)
        )
        # Minus to remove the row
        sources_images_dir = Config().getSourceImageDir()
        remove_row_label = ClickableLabel()
        remove_row_picture = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "red_minus.png"))
        )
        remove_row_picture = remove_row_picture.scaledToHeight(30)
        remove_row_label.setPixmap(remove_row_picture)
        # Everything appended to the row
        row_layout.append(None)  # Link room
        row_layout.append(not_choice)
        row_layout.append(field_choice)
        row_layout.append(condition_choice)
        row_layout.append(condition_value)
        row_layout.append(remove_row_label)
        row_layout.append(None)  # Add row room
        # Signal to remove the row
        remove_row_label.clicked.connect(lambda: self.remove_row(row_layout))
        self.rows.append(row_layout)
        self.refresh_search()
        self.displayConditionRules(field_choice, condition_choice)

    def apply_filter(self, filter):
        """
        Applies a filter to update the table data by refining the displayed
        scans based on the filter criteria. The filter is used to query
        documents from the database, and the results are reflected in the
        data browser.

        This function handles the following tasks:
        - Retrieves filter parameters (e.g., conditions, values, links)
          from the provided filter object.
        - Updates the table rows based on the filter values, including
          conditions and fields.
        - Prepares and applies the filter query to the database to fetch
          relevant results.
        - If the filter is successfully applied, updates the table data
          with the filtered results.
        - If an error occurs during the filtering process, displays a warning
          message and reverts to the full set of scans.

        :param filter: A filter object that contains the criteria
                      (e.g., conditions, values, and fields) to apply when
                      querying the database. The filter is applied to update
                      the visible scans in the table.
        """
        # Data
        nots = filter.nots
        values = filter.values
        conditions = filter.conditions
        links = filter.links
        fields = filter.fields

        with self.project.database.data() as database_data:

            for i in range(0, len(nots)):

                if i >= len(self.rows):
                    self.add_search_bar()

                row = self.rows[i]

                if i > 0:
                    row[0].setCurrentText(links[i - 1])

                row[1].setCurrentText(nots[i])
                row[2].setCurrentText(fields[i][0])

                # Replacing all visualized tags by the current list of
                # visible tags
                if fields[i][0] == "All visualized tags":
                    fields[i] = database_data.get_shown_tags()

                row[3].setCurrentText(conditions[i])
                row[4].setText(str(values[i]))

            old_rows = self.dataBrowser.table_data.scans_to_visualize

            # Filter applied only if at least one row
            if len(nots) > 0:

                # Result gotten
                try:
                    filter_query = self.prepare_filters(
                        links,
                        fields,
                        conditions,
                        values,
                        nots,
                        self.scans_list,
                    )
                    result = database_data.filter_documents(
                        COLLECTION_CURRENT, filter_query
                    )
                    # data_browser updated with the new selection
                    result_names = [
                        document[TAG_FILENAME] for document in result
                    ]

                except Exception:
                    logger.warning(
                        "Exception occurred in populse_mia.user_interface."
                        "data_browser.advanced_search.AdvancedSearch."
                        "apply_filter()",
                        exc_info=True,
                    )
                    # Error message if the search can't be done,
                    # and visualization of all scans in the data_browser
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Error in the search")
                    msg.setInformativeText(
                        "An issue occurred during the search. Please "
                        "correct it and try again..."
                    )
                    msg.setWindowTitle("Warning")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()
                    result_names = self.scans_list

                # data_browser updated with the new selection
                self.dataBrowser.table_data.scans_to_visualize = result_names

            # Otherwise, all the scans are reput
            else:

                # data_browser updated with every scan
                if self.scans_list:
                    self.dataBrowser.table_data.scans_to_visualize = (
                        self.scans_list
                    )

                else:
                    self.dataBrowser.table_data.scans_to_visualize = (
                        database_data.get_document_names(COLLECTION_CURRENT)
                    )

        self.dataBrowser.table_data.update_visualized_rows(old_rows)

    # def clearLayout(self, layout):
    #     """
    #     Called to clear a layout
    #
    #     :param layout: layout to clear
    #     """
    #     if layout is not None:
    #         while layout.count():
    #             item = layout.takeAt(0)
    #             widget = item.widget()
    #             # We clear the widget only if the row does not exist anymore
    #             if widget is not None and not self.rowsContainsWidget(
    #                     widget):
    #                 pass
    #                 widget.deleteLater()
    #             else:
    #                 self.clearLayout(item.layout())

    def displayConditionRules(self, field, condition):
        """
        Updates the available condition choices based on the field's tag
        type.

        This function adjusts the list of conditions (e.g., `<`, `>`,
        `BETWEEN`, `IN`) available in the `condition` widget, depending on
        the type of the tag selected in the `field` widget. Certain
        conditions are removed or added based on the tag's field type,
        and the condition choices are sorted afterward.

        The rules for updating the condition choices are as follows:
        - For tags with a field type of list, string, or boolean, or if
          the tag name is "All visualized tags", certain operators
          like `<`, `>`, `<=`, `>=`, and `BETWEEN` are removed.
        - If the tag's field type is compatible with numeric comparisons
          (i.e., not list, string, or boolean), operators like `<`, `>`,
          `<=`, `>=`, and `BETWEEN` are added.
        - If the tag is a list, the "IN" condition is removed.
        - Otherwise, the "IN" condition is added.

        :param field: The field widget representing the selected tag. Used to
                      determine the tag type and adjust the condition choices
                      accordingly.
        :param condition: The condition widget where the available conditions
                          are updated based on the tag type.
        """

        tag_name = field.currentText()

        with self.project.database.data() as database_data:
            tag_attrib = database_data.get_field_attributes(
                COLLECTION_CURRENT, tag_name
            )

        no_operators_tags = [t for t in ALL_TYPES if get_origin(t) is list]
        no_operators_tags.append(FIELD_TYPE_STRING)
        no_operators_tags.append(FIELD_TYPE_BOOLEAN)
        no_operators_tags.append(None)

        if (
            tag_attrib is not None
            and tag_attrib["field_type"] in no_operators_tags
        ) or tag_name == "All visualized tags":
            condition.removeItem(condition.findText("<"))
            condition.removeItem(condition.findText(">"))
            condition.removeItem(condition.findText("<="))
            condition.removeItem(condition.findText(">="))
            condition.removeItem(condition.findText("BETWEEN"))

        elif (
            tag_attrib is None
            or tag_attrib["field_type"] not in no_operators_tags
        ):
            operators_to_reput = ["<", ">", "<=", ">=", "BETWEEN"]

            for operator in operators_to_reput:
                is_op_existing = condition.findText(operator) != -1

                if not is_op_existing:
                    condition.addItem(operator)

        if (tag_attrib is not None) and (
            get_origin(tag_attrib["field_type"]) is list
        ):
            condition.removeItem(condition.findText("IN"))

        elif (tag_attrib is None) or (
            not get_origin(tag_attrib["field_type"]) is list
        ):
            operators_to_reput = ["IN"]

            for operator in operators_to_reput:
                is_op_existing = condition.findText(operator) != -1

                if not is_op_existing:
                    condition.addItem(operator)

        condition.model().sort(0)

    def displayValueRules(self, choice, value):
        """
        Update the placeholder text and the enabled/disabled state of the
        value input based on the selected condition choice.

        This function adjusts the `value` widget's state (enabled/disabled)
        and its placeholder text depending on the condition selected in the
        `choice` widget.

        The rules are as follows:
        - "BETWEEN": Enables the `value` input and sets a placeholder text
                     asking the user to separate the two inclusive borders
                     with a semicolon and a space.
        - "IN": Enables the `value` input and sets a placeholder text asking
                the user to separate each list item with a semicolon and a
                space.
        - "HAS VALUE" or "HAS NO VALUE": Disables the `value` input and
                                         clears any placeholder text or value.
        - For all other conditions: Enables the `value` input and clears the
                                    placeholder text.

        :param choice: The choice widget, which determines the selected
                       condition.
        :param value: The value widget, which represents the input field
                      whose state will be updated.
        """

        if choice.currentText() == "BETWEEN":
            value.setDisabled(False)
            value.setPlaceholderText(
                "Please separate the two inclusive borders of the range by a "
                "semicolon and a space"
            )

        elif choice.currentText() == "IN":
            value.setDisabled(False)
            value.setPlaceholderText(
                "Please separate each list item by a semicolon and a space"
            )

        elif (
            choice.currentText() == "HAS VALUE"
            or choice.currentText() == "HAS NO VALUE"
        ):
            value.setDisabled(True)
            value.setPlaceholderText("")
            value.setText("")

        else:
            value.setDisabled(False)
            value.setPlaceholderText("")

    def get_filters(self, replace_all_by_fields):
        """Get the filters in a list.

        :param replace_all_by_fields: to replace All visualized tags by the
           list of visible fields
        :return: Lists of filters (fields, conditions, values, links, nots)
        """

        # Lists to get all the data of the search
        fields = []
        conditions = []
        values = []
        links = []
        nots = []

        with self.project.database.data() as database_data:

            for row in self.rows:

                for widget in row:

                    if widget is not None:
                        child = widget
                        child_name = child.objectName()

                        if child_name == "link":
                            links.append(child.currentText())

                        elif child_name == "condition":
                            conditions.append(child.currentText())

                        elif child_name == "field":

                            if child.currentText() != "All visualized tags":
                                fields.append([child.currentText()])

                            else:

                                if replace_all_by_fields:
                                    fields.append(
                                        database_data.get_shown_tags()
                                    )

                                else:
                                    fields.append([child.currentText()])

                        elif child_name == "value":
                            values.append(child.displayText())

                        elif child_name == "not":
                            nots.append(child.currentText())

            operators = ["<", ">", "<=", ">=", "BETWEEN"]
            no_operators_tags = [t for t in ALL_TYPES if get_origin(t) is list]
            no_operators_tags.append(FIELD_TYPE_STRING)
            no_operators_tags.append(FIELD_TYPE_BOOLEAN)

            # Converting BETWEEN and IN values into lists
            for i in range(0, len(conditions)):

                if conditions[i] == "BETWEEN" or conditions[i] == "IN":
                    values[i] = values[i].split("; ")

                if conditions[i] == "IN":

                    for tag in fields[i].copy():
                        tag_attrib = database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag
                        )

                        if get_origin(tag_attrib["field_type"]) is list:
                            fields[i].remove(tag)

                elif conditions[i] in operators:

                    for tag in fields[i].copy():
                        tag_attrib = database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag
                        )

                        if tag_attrib["field_type"] in no_operators_tags:
                            fields[i].remove(tag)

        return fields, conditions, values, links, nots

    def launch_search(self):
        """Start the search and update the table."""

        # Filters gotten
        (fields, conditions, values, links, nots) = self.get_filters(True)
        old_scans_list = self.dataBrowser.table_data.scans_to_visualize

        try:
            # Result gotten
            filter_query = self.prepare_filters(
                links, fields, conditions, values, nots, self.scans_list
            )

            with self.project.database.data() as database_data:
                result = database_data.filter_documents(
                    COLLECTION_CURRENT, filter_query
                )

            # data_browser updated with the new selection
            result_names = [document[TAG_FILENAME] for document in result]

            if not self.from_pipeline:
                self.project.currentFilter.nots = nots
                self.project.currentFilter.values = values
                self.project.currentFilter.fields = fields
                self.project.currentFilter.links = links
                self.project.currentFilter.conditions = conditions

        except Exception:
            logger.warning(
                "Exception occurred in populse_mia.user_interface."
                "data_browser.advanced_search.AdvancedSearch."
                "launch_search():",
                exc_info=True,
            )
            # Error message if the search can't be done, and visualization
            # of all scans in the databrowser
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Error in the search")
            msg.setInformativeText(
                "An issue occurred during the search. Please correct it and "
                "try again...."
            )
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()
            result_names = self.scans_list

        self.dataBrowser.table_data.scans_to_visualize = result_names
        self.dataBrowser.table_data.scans_to_search = result_names
        self.dataBrowser.table_data.update_visualized_rows(old_scans_list)

    @staticmethod
    def prepare_filters(links, fields, conditions, values, nots, scans):
        """Prepare the str representation of the filter.

        :param links: list of links (AND/OR)
        :param fields: list of fields
        :param conditions: list of conditions (==, !=, <, >, <=, >=, IN,
                           BETWEEN, CONTAINS, HAS VALUE, HAS NO VALUE)
        :param values: list of values
        :param nots: list of negations ("" or NOT)
        :param scans: list of scans to search in
        :return: str representation of the filter
        """

        row_queries = []

        for row_fields, row_condition, row_value, row_not in zip(
            fields, conditions, values, nots
        ):
            row_query_parts = []

            for row_field in row_fields:

                if row_condition == "IN":
                    escaped_row_value = str(row_value).replace("'", '"')
                    row_field_query = (
                        f"({{{row_field}}} IN {escaped_row_value})"
                    )

                elif row_condition == "BETWEEN":
                    row_field_query = (
                        f'(({{{row_field}}} >= "{row_value[0]}") AND '
                        f'({{{row_field}}} <= "{row_value[1]}"))'
                    )

                elif row_condition == "HAS VALUE":
                    row_field_query = f"({{{row_field}}} != null)"

                elif row_condition == "HAS NO VALUE":
                    row_field_query = f"({{{row_field}}} == null)"

                elif row_condition == "CONTAINS":
                    row_field_query = f'({{{row_field}}} LIKE "%{row_value}%")'

                else:
                    row_field_query = (
                        f'({{{row_field}}} {row_condition} "{row_value}")'
                    )

                row_query_parts.append(row_field_query)

            # Combine all parts with "OR"
            row_query = " OR ".join(row_query_parts)

            # Apply negation if necessary
            if row_not == "NOT":
                row_query = f"(NOT {row_query})"

            row_queries.append(f"({row_query})")

        # Combine all row queries with specified links
        final_query = row_queries[0]

        for link, next_query in zip(links, row_queries[1:]):
            final_query = f"{final_query} {link} {next_query}"

        # Add the scans condition
        formatted_scans = str(scans).replace("'", '"')
        final_query = (
            f"{final_query} AND " f"({{{TAG_FILENAME}}} IN {formatted_scans})"
        )
        # Enclose the entire query in parentheses
        return f"({final_query})"

    def refresh_search(self):
        """
        Refresh the widget.
        """

        # Old values stored
        (fields, conditions, values, links, nots) = self.get_filters(False)
        # We remove the old layout
        # self.clearLayout(self.layout())
        QObjectCleanupHandler().add(self.layout())
        # Links and add rows removed from every row
        self.rows_borders_removed()
        # Links and add rows put back in the good rows
        self.rows_borders_added(links)
        master_layout = QVBoxLayout()
        main_layout = QGridLayout()

        # Everything added to the layout
        for i in range(0, len(self.rows)):

            for j in range(0, 7):
                widget = self.rows[i][j]

                if widget is not None:
                    main_layout.addWidget(widget, i, j)

        # Search button added at the end
        search_layout = QHBoxLayout(None)
        search_layout.setObjectName("search layout")
        self.search.clicked.connect(self.launch_search)
        search_layout.addWidget(self.search)
        search_layout.setParent(None)
        # New layout added
        master_layout.addLayout(main_layout)
        master_layout.addLayout(search_layout)
        self.setLayout(master_layout)

    def remove_row(self, row_layout):
        """Remove a row.

        :param row_layout: Row to remove
        """

        # We remove the row only if there is at least 2 rows, because we
        # always must keep at least one
        if len(self.rows) > 1:
            index = self.rows.index(row_layout)

            for i in range(0, len(self.rows[-1])):

                if self.rows[index][i] is not None:
                    self.rows[index][i].setParent(None)
                    self.rows[index][i].deleteLater()
                    self.rows[index][i] = None

            del self.rows[index]

        # We refresh the view
        self.refresh_search()

    def rows_borders_added(self, links):
        """Add the links and the added row to the good rows.

        :param links: Old links to reput
        """

        # Plus added to the last row
        sources_images_dir = Config().getSourceImageDir()
        add_search_bar_label = ClickableLabel()
        add_search_bar_label.setObjectName("plus")
        add_search_bar_picture = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "green_plus.png"))
        )
        add_search_bar_picture = add_search_bar_picture.scaledToHeight(20)
        add_search_bar_label.setPixmap(add_search_bar_picture)
        add_search_bar_label.clicked.connect(self.add_search_bar)
        self.rows[len(self.rows) - 1][6] = add_search_bar_label

        # Link added to every row, except the first one
        for i in range(1, len(self.rows)):
            row = self.rows[i]
            link_choice = QComboBox()
            link_choice.setObjectName("link")
            link_choice.addItem("AND")
            link_choice.addItem("OR")

            if len(links) >= i:
                link_choice.setCurrentText(links[i - 1])

            row[0] = link_choice

    def rows_borders_removed(self):
        """Link and add row removed from every row."""

        # We remove all the links and the add rows
        for i in range(0, len(self.rows)):

            # Plus removed from every row
            if self.rows[i][6] is not None:
                self.rows[i][6].setParent(None)
                self.rows[i][6].deleteLater()
                self.rows[i][6] = None

            # Link removed from every row
            if self.rows[i][0] is not None:
                self.rows[i][0].setParent(None)
                self.rows[i][0].deleteLater()
                self.rows[i][0] = None

    # def rowsContainsWidget(self, widget):
    #     """Check if the widget is still used
    #
    #     :param widget: widget to check
    #     :return: True or False
    #     """
    #     for row in self.rows:
    #         if widget in row:
    #             return True
    #     return False

    def show_search(self):
        """Reset the rows when the Advanced Search button is clicked."""

        if len(self.rows) < 1:
            self.rows = []
            self.add_search_bar()
