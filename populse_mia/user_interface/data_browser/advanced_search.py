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
        """
        Initialize the AdvancedSearch widget.

        :param project: The current project instance.
        :param data_browser: The parent DataBrowser widget that contains this
                             search.
        :param scans_list:  List of document scans to search within. Defaults
                            to empty list.
        :param tags_list: List of tags to display in the search interface.
                          Defaults to empty list.
        :param from_pipeline (bool): Whether the widget is instantiated from
                                     the pipeline manager. Defaults to False.

        """
        super().__init__()
        self.project = project
        self.data_browser = data_browser
        self.scans_list = scans_list or []
        self.tags_list = tags_list or []
        self.from_pipeline = from_pipeline
        self.rows = []
        self.search = QPushButton("Search")
        self.search.setFixedWidth(100)

    def add_search_bar(self):
        """
        Add an advanced search bar row to the search interface.

        Creates a complete search row containing:
            - NOT operator toggle
            - Field selector (populated with available tags)
            - Condition operator selector (==, !=, >, <, etc.)
            - Value input field
            - Remove button to delete this row

        The row components are connected with signals to update dynamically
        based on field type and selected condition.

        """

        def _create_combo_box(name, items):
            """
            Create and return a QComboBox populated with the given items.

            :param name (str): Object name assigned to the QComboBox.
            :param items (iterable of str): Items to add to the combo box,
                                            in order.

            :return (QComboBox): The initialized combo box.
            """
            combo = QComboBox()
            combo.setObjectName(name)

            for item in items:
                combo.addItem(item)

            return combo

        def _get_shown_tags_from_db():
            """
            Retrieve the tags currently marked as visible from the project
            database.

            :return (list): A list of tags configured to be shown in the
                            project.
            """

            with self.project.database.data() as database_data:

                return database_data.get_shown_tags()

        # Create NOT operator toggle
        not_choice = _create_combo_box("not", ["", "NOT"])
        # Create and populate field selector with available tags
        field_choice = QComboBox()
        field_choice.setObjectName("field")
        tags = self.tags_list if self.tags_list else _get_shown_tags_from_db()

        for tag in tags:
            field_choice.addItem(tag)

        field_choice.model().sort(0)
        field_choice.addItem("All visualized tags")
        # Create value input
        condition_value = QLineEdit()
        condition_value.setObjectName("value")
        # Create condition operator selector
        conditions = [
            "==",
            "!=",
            ">=",
            "<=",
            ">",
            "<",
            "BETWEEN",
            "IN",
            "CONTAINS",
            "HAS VALUE",
            "HAS NO VALUE",
        ]
        condition_choice = _create_combo_box("condition", conditions)
        condition_choice.model().sort(0)
        # Connect dynamic update signals
        condition_choice.currentTextChanged.connect(
            lambda: self.displayValueRules(condition_choice, condition_value)
        )
        field_choice.currentTextChanged.connect(
            lambda: self.displayConditionRules(field_choice, condition_choice)
        )
        # Create remove button with red minus icon
        sources_dir = Config().getSourceImageDir()
        icon_path = os.path.join(sources_dir, "red_minus.png")
        remove_row_label = ClickableLabel()
        pixmap = QPixmap(os.path.relpath(icon_path)).scaledToHeight(30)
        remove_row_label.setPixmap(pixmap)
        # Assemble row layout
        row_layout = [
            None,  # Link room (reserved for future use)
            not_choice,
            field_choice,
            condition_choice,
            condition_value,
            remove_row_label,
            None,  # Add row room (reserved for future use)
        ]
        # Connect remove functionality
        remove_row_label.clicked.connect(lambda: self.remove_row(row_layout))
        # Register and initialize the row
        self.rows.append(row_layout)
        self.refresh_search()
        self.displayConditionRules(field_choice, condition_choice)

    def apply_filter(self, filter):
        """
        Apply a filter to update the displayed scans in the data browser.

        Retrieves documents from the database based on the provided filter
        criteria and updates the table visualization accordingly. If the filter
        is invalid or an error occurs, displays a warning and reverts to
        showing all scans.

        :param filter: Filter object containing the query criteria with
                       attributes:
                           - nots (list): Negation flags for each condition
                           - values (list): Values to match against
                           - conditions (list): Comparison operators
                                                (e.g., '==', '>', '<')
                           - links (list): Logical operators connecting
                                           conditions ('AND', 'OR')
                           - fields (list): Database fields to query

        Side Effects:
            - Updates self.rows with filter parameters
            - Modifies self.data_browser.table_data.scans_to_visualize
            - May display a warning dialog on error
            - Calls self.data_browser.table_data.update_visualized_rows()
        """
        # Extract filter parameters
        nots = filter.nots
        values = filter.values
        conditions = filter.conditions
        links = filter.links
        fields = filter.fields

        with self.project.database.data() as database_data:

            # Update UI rows with filter parameters
            for i, (not_val, field, condition, value) in enumerate(
                zip(nots, fields, conditions, values)
            ):

                if i >= len(self.rows):
                    self.add_search_bar()

                row = self.rows[i]

                # Set link operator for all rows except the first
                if i > 0:
                    row[0].setCurrentText(links[i - 1])

                row[1].setCurrentText(not_val)
                row[2].setCurrentText(field[0])

                # Replace "All visualized tags" with actual visible tag list
                if field[0] == "All visualized tags":
                    fields[i] = database_data.get_shown_tags()

                row[3].setCurrentText(condition)
                row[4].setText(str(value))

            old_rows = self.data_browser.table_data.scans_to_visualize

            # Apply filter if conditions exist, otherwise show all scans
            if nots:

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
                    result_names = [
                        document[TAG_FILENAME] for document in result
                    ]

                except Exception:
                    logger.warning(
                        "Exception in AdvancedSearch.apply_filter()",
                        exc_info=True,
                    )
                    # Display an error dialog when filter execution fails
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Error in the search")
                    msg.setInformativeText(
                        "An issue occurred during the search. Please "
                        "correct it and try again."
                    )
                    msg.setWindowTitle("Warning")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()
                    result_names = self.scans_list

            else:
                result_names = (
                    self.scans_list
                    if self.scans_list
                    else database_data.get_document_names(COLLECTION_CURRENT)
                )

            self.data_browser.table_data.scans_to_visualize = result_names
            self.data_browser.table_data.update_visualized_rows(old_rows)

    def displayConditionRules(self, field, condition):
        """
        Update available condition operators based on the selected field's
        type.

        Dynamically adjusts the condition dropdown to show only operators that
        are
        valid for the selected field's data type. Numeric fields allow
        comparison operators (<, >, <=, >=, BETWEEN), while non-numeric fields
        exclude them. List fields exclude the IN operator, while non-list
        fields include it.

        :param field: QComboBox widget containing the selected tag name.
        :param condition: QComboBox widget whose items will be updated based
                          on the field's type.

        Behavior:
            - Numeric types: Include <, >, <=, >=, BETWEEN operators
            - String/Boolean/List types: Exclude comparison operators
            - List types: Exclude IN operator
            - Non-list types: Include IN operator
            - Special case "All visualized tags": Treated as non-numeric
        """

        def _update_operators(condition_widget, operators, should_add):
            """
            Add or remove operators from the condition widget.

            :param condition_widget: QComboBox to modify.
            :param operators: List of operator strings to add or remove.
            :param should_add: If True, add missing operators; if False, remove
                               existing ones.
            """

            for operator in operators:
                index = condition_widget.findText(operator)
                exists = index != -1

                if should_add and not exists:
                    condition_widget.addItem(operator)

                elif not should_add and exists:
                    condition_widget.removeItem(index)

        tag_name = field.currentText()

        with self.project.database.data() as database_data:
            tag_attrib = database_data.get_field_attributes(
                COLLECTION_CURRENT, tag_name
            )

        # Define field types that don't support numeric comparison operators
        non_numeric_types = [t for t in ALL_TYPES if get_origin(t) is list] + [
            FIELD_TYPE_STRING,
            FIELD_TYPE_BOOLEAN,
            None,
        ]
        field_type = tag_attrib["field_type"] if tag_attrib else None
        is_numeric = (
            field_type not in non_numeric_types
            and tag_name != "All visualized tags"
        )
        is_list = tag_attrib and get_origin(field_type) is list
        # Update comparison operators (<, >, <=, >=, BETWEEN)
        comparison_operators = ["<", ">", "<=", ">=", "BETWEEN"]
        _update_operators(
            condition, comparison_operators, should_add=is_numeric
        )
        # Update IN operator
        _update_operators(condition, ["IN"], should_add=not is_list)
        condition.model().sort(0)

    def displayValueRules(self, choice, value):
        """
        Configure the value input widget based on the selected condition
        operator.

        Adjusts the enabled state and placeholder text of the value input to
        match the requirements of the selected condition operator.

        :param choice: QComboBox containing the selected condition operator.
        :param value: QLineEdit widget that will be configured.

        Behavior:
            - BETWEEN: Enabled with placeholder "value1; value2"
            - IN: Enabled with placeholder for semicolon-separated list
            - HAS VALUE/HAS NO VALUE: Disabled and cleared
            - Other operators: Enabled with no placeholder
        """
        operator = choice.currentText()
        # Configuration map: operator ->
        # (enabled, placeholder_text, clear_text)
        config = {
            "BETWEEN": (
                True,
                "Please separate the two inclusive borders of the range by a "
                "semicolon and a space",
                False,
            ),
            "IN": (
                True,
                "Please separate each list item by a semicolon and a space",
                False,
            ),
            "HAS VALUE": (False, "", True),
            "HAS NO VALUE": (False, "", True),
        }
        enabled, placeholder, should_clear = config.get(
            operator, (True, "", False)
        )
        value.setDisabled(not enabled)
        value.setPlaceholderText(placeholder)

        if should_clear:
            value.setText("")

    def get_filters(self, replace_all_by_fields):
        """
        Extract filter criteria from UI widgets.

        Parses the filter rows to extract search criteria including fields,
        conditions, values, logical operators, and negation flags. Handles
        special cases like "All visualized tags" expansion and operator
        compatibility validation.

        :param replace_all_by_fields: If True, replaces "All visualized tags"
                                      with the actual list of visible fields.
                                      If False, keeps the literal
                                      "All visualized tags" text.

        :return (tuple): A 5-tuple containing:
            - fields (list): Field names to filter on
            - conditions (list): Comparison operators (e.g., '=', 'BETWEEN')
            - values (list): Filter values (strings or lists for BETWEEN/IN)
            - links (list): Logical operators connecting filters (AND/OR)
            - nots (list): Negation flags for each filter

        Note:
            - BETWEEN and IN conditions have their values split into lists
            - Fields incompatible with operators are automatically removed
        """
        comparison_operators = {"<", ">", "<=", ">=", "BETWEEN"}
        incompatible_types = {
            *[t for t in ALL_TYPES if get_origin(t) is list],
            FIELD_TYPE_STRING,
            FIELD_TYPE_BOOLEAN,
        }
        # Result containers
        fields = []
        conditions = []
        values = []
        links = []
        nots = []

        # Extract widget data
        with self.project.database.data() as database_data:

            for row in self.rows:

                for widget in (w for w in row if w is not None):
                    widget_name = widget.objectName()

                    if widget_name == "link":
                        links.append(widget.currentText())

                    elif widget_name == "condition":
                        conditions.append(widget.currentText())

                    elif widget_name == "field":
                        field_value = widget.currentText()
                        is_all_tags = field_value == "All visualized tags"

                        if is_all_tags and replace_all_by_fields:
                            fields.append(database_data.get_shown_tags())

                        else:
                            fields.append([field_value])

                    elif widget_name == "value":
                        values.append(widget.displayText())

                    elif widget_name == "not":
                        nots.append(widget.currentText())

            # Post-process values and validate field compatibility
            for i in range(len(conditions)):
                condition = conditions[i]

                # Split multi-value conditions
                if condition in {"BETWEEN", "IN"}:
                    values[i] = values[i].split("; ")

                # Remove incompatible fields based on condition
                if condition == "IN":

                    for tag in fields[i].copy():
                        field_type = database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag
                        )["field_type"]

                        if get_origin(field_type) is list:
                            fields[i].remove(tag)

                elif condition in comparison_operators:

                    for tag in fields[i].copy():
                        field_type = database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag
                        )["field_type"]

                        if field_type in incompatible_types:
                            fields[i].remove(tag)

        return fields, conditions, values, links, nots

    def launch_search(self):
        """
        Execute search query and update the data browser table.

        Retrieves filter parameters, constructs and executes a database query,
        then updates the data browser's visualized scans with the results.
        If the search fails, displays an error dialog and reverts to showing
        all available scans.

        Side Effects:
            - Updates self.data_browser.table_data.scans_to_visualize
            - Updates self.data_browser.table_data.scans_to_search
            - Updates self.project.currentFilter (if not from_pipeline)
            - Displays error dialog on search failure
        """
        # Retrieve filter parameters
        fields, conditions, values, links, nots = self.get_filters(True)
        old_scans_list = self.data_browser.table_data.scans_to_visualize

        try:
            # Construct and execute database query
            filter_query = self.prepare_filters(
                links, fields, conditions, values, nots, self.scans_list
            )

            with self.project.database.data() as database_data:
                result = database_data.filter_documents(
                    COLLECTION_CURRENT, filter_query
                )

            # Extract document names from results
            result_names = [doc[TAG_FILENAME] for doc in result]

            if not self.from_pipeline:
                current_filter = self.project.currentFilter
                current_filter.nots = nots
                current_filter.values = values
                current_filter.fields = fields
                current_filter.links = links
                current_filter.conditions = conditions

        except Exception:
            logger.warning(
                "Exception in populse_mia.user_interface.data_browser."
                "advanced_search.AdvancedSearch.launch_search():",
                exc_info=True,
            )
            # Display error dialog when search fails.
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Error in the search")
            msg.setInformativeText(
                "An issue occurred during the search. Please correct it and "
                "try again."
            )
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()
            result_names = self.scans_list

        self.data_browser.table_data.scans_to_visualize = result_names
        self.data_browser.table_data.scans_to_search = result_names
        self.data_browser.table_data.update_visualized_rows(old_scans_list)

    @staticmethod
    def prepare_filters(links, fields, conditions, values, nots, scans):
        """
        Construct a filter query string from filter components.

        Builds a query by combining multiple filter rows with logical
        operators (AND/OR), where each row can filter across multiple fields
        with optional negation.

        :param links: Logical operators joining filter rows
                      (e.g., ['AND', 'OR']). Length should be len(fields) - 1.
        :param fields: Nested list where each sublist contains field names to
                       filter on. Fields within a row are OR-combined.
        :param conditions: Filter operators for each row. Supported values:
                           '==', '!=', '<', '>', '<=', '>=', 'IN', 'BETWEEN',
                           'CONTAINS', 'HAS VALUE', 'HAS NO VALUE'.
        :param values: Filter values corresponding to each condition. For
                       'BETWEEN', provide a two-element sequence [min, max].
        :param nots: Negation flags for each row ('NOT' to negate, empty
                     string otherwise).
        :param scans: List of scan identifiers to restrict the search scope.

        :return: Complete filter query string with all conditions and scan
                 restrictions.
        """

        def _format_value(value):
            """
            Convert a Python value into a string safe for use in queries.

            This function casts the input `value` to a string and replaces
            single quotes with double quotes to reduce the risk of
            breaking query syntax.

            :param value: The Python value to format (e.g., int, float,
                          str, bool).

            :return (str): A string representation of the value with single
                           quotes replaced by double quotes.
            """
            return str(value).replace("'", '"')

        condition_handlers = {
            "IN": lambda field, value: (
                f"({{{field}}} IN {_format_value(value)})"
            ),
            "BETWEEN": lambda field, value: (
                f'(({{{field}}} >= "{value[0]}") AND '
                f'({{{field}}} <= "{value[1]}"))'
            ),
            "HAS VALUE": lambda field, _: f"({{{field}}} != null)",
            "HAS NO VALUE": lambda field, _: f"({{{field}}} == null)",
            "CONTAINS": lambda field, value: f'({{{field}}} LIKE "%{value}%")',
        }
        # Build individual row queries
        row_queries = []

        for row_fields, condition, value, negation in zip(
            fields, conditions, values, nots
        ):
            # Build condition for each field in the row
            handler = condition_handlers.get(condition)

            if handler:
                field_queries = [handler(field, value) for field in row_fields]

            else:
                field_queries = [
                    f'({{{field}}} {condition} "{value}")'
                    for field in row_fields
                ]

            # Combine fields with OR and apply negation if needed
            combined = " OR ".join(field_queries)
            row_query = (
                f"(NOT ({combined}))" if negation == "NOT" else f"({combined})"
            )
            row_queries.append(row_query)

        # Combine rows with logical operators
        query = row_queries[0]

        for link, next_query in zip(links, row_queries[1:]):
            query = f"{query} {link} {next_query}"

        # Add scan restrictions
        query = f"{query} AND ({{{TAG_FILENAME}}} IN {_format_value(scans)})"

        return f"({query})"

    def refresh_search(self):
        """
        Refresh the search widget by rebuilding its layout with the current
        filters.

        This method performs the following steps:
            1. Retrieves the current filter values without replacing
               "All visualized tags".
            2. Clears the old layout and cleans up its widgets.
            3. Removes and restores row borders according to the links.
            4. Rebuilds the main grid layout with all row widgets.
            5. Adds the search button in a horizontal layout at the bottom.
            6. Sets the new combined layout as the widget's layout.
        """
        # Retrieve current filter values
        _, _, _, links, _ = self.get_filters(replace_all_by_fields=False)
        # Clean up the old layout
        QObjectCleanupHandler().add(self.layout())
        # Update row borders
        self.rows_borders_removed()
        self.rows_borders_added(links)
        # Create new layouts
        master_layout = QVBoxLayout()
        main_layout = QGridLayout()

        # Populate grid layout with widgets
        for i, row in enumerate(self.rows):

            for j, widget in enumerate(row):

                if widget is not None:
                    main_layout.addWidget(widget, i, j)

        # Add search button at the bottom
        search_layout = QHBoxLayout()
        search_layout.setObjectName("search_layout")
        self.search.clicked.connect(self.launch_search)
        search_layout.addWidget(self.search)
        # Combine layouts and set the widget layout
        master_layout.addLayout(main_layout)
        master_layout.addLayout(search_layout)
        self.setLayout(master_layout)

    def remove_row(self, row_layout):
        """
        Remove a specified row from the layout while ensuring at least one row
        remains.

        This method deletes all widgets in the specified row, removes the row
        from the internal `rows` list, and refreshes the view.

        :param row_layout: The row (list of widgets) to remove.
        """

        # Remove the row only if more than one exists
        if len(self.rows) > 1:

            try:
                index = self.rows.index(row_layout)

            except ValueError:
                index = None

            if index is not None:
                # Remove widgets in the row
                for i, widget in enumerate(self.rows[index]):
                    if widget is not None:
                        widget.setParent(None)
                        widget.deleteLater()
                        self.rows[index][i] = None

                # Remove the row from the list
                del self.rows[index]

        # Refresh the view always, even if no row was removed
        self.refresh_search()

    def rows_borders_added(self, links):
        """
        Add UI controls (links and add button) to search query rows.

        Adds a green plus button to the last row for adding new search bars,
        and adds AND/OR combo boxes to all rows except the first one for
        linking query conditions.

        :param links: List of previously selected link operators ('AND'/'OR')
                      to restore when rebuilding the UI.
        """
        # Add plus button to the last row for adding new search bars
        sources_images_dir = Config().getSourceImageDir()
        plus_icon_path = os.path.join(sources_images_dir, "green_plus.png")
        add_button = ClickableLabel()
        add_button.setObjectName("plus")
        add_button.setPixmap(
            QPixmap(os.path.relpath(plus_icon_path)).scaledToHeight(20)
        )
        add_button.clicked.connect(self.add_search_bar)
        self.rows[-1][6] = add_button
        # Add link combo boxes to all rows except the first
        link_operators = ("AND", "OR")

        for i, row in enumerate(self.rows[1:], start=1):
            link_choice = QComboBox()
            link_choice.setObjectName("link")
            link_choice.addItems(link_operators)

            # Restore previous selection if available
            if i <= len(links):
                link_choice.setCurrentText(links[i - 1])

            row[0] = link_choice

    def rows_borders_removed(self):
        """
        Remove the link widget and the "add row" widget from every row.

        This ensures that these widgets are properly removed from the layout
        and scheduled for deletion, preventing memory leaks.
        """

        def _remove_widget(widget_ref):
            """
            Safely removes a QWidget from its parent and schedules it for
            deletion.

            This helper function ensures that the given widget is properly
            detached from its parent layout and deleted later, preventing
            potential memory leaks. If the widget reference is `None`, it does
            nothing.

            :param widget_ref: The QWidget instance to remove, or `None`.

            :return: Always returns `None` after removing the widget.
            """

            if widget_ref is not None:
                widget_ref.setParent(None)
                widget_ref.deleteLater()

            return None

        for row in self.rows:
            # Remove "add row" widget (assumed at index 6)
            row[6] = _remove_widget(row[6])
            # Remove link widget (assumed at index 0)
            row[0] = _remove_widget(row[0])

    def show_search(self):
        """
        Reset the search rows and display the search bar.

        This method clears the current rows if there are none or fewer than
        one, and initializes the search bar for the advanced search
        functionality.
        """

        if not self.rows:
            self.rows.clear()
            self.add_search_bar()
