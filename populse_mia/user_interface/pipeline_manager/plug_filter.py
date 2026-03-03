"""
Plug filter widget for pipeline node inputs.

This module provides the :class:`PlugFilter` widget, a PyQt-based interface
used in the Mia pipeline manager to filter and select database scans for
assignment to a pipeline node plug.

The widget integrates several components of the user interface:

    - A tag-based data browser (TableDataBrowser)
    - Rapid text search (RapidSearch)
    - Advanced multi-criteria filtering (AdvancedSearch)
    - Tag visualization management dialogs
    - Automatic exclusion of pipeline brick outputs to prevent circular
      dependencies in workflows

It interacts with:
    - The project database (COLLECTION_CURRENT, COLLECTION_BRICK)
    - The pipeline manager to determine existing brick outputs
    - The node controller to manage visible tags and plug updates
    - The main application window for integration in the pipeline editor

When the user confirms a selection, the widget emits the ``plug_value_changed``
signal containing the selected values (absolute file paths or tag values
depending on the selected filter).

:Contains:

    Class:
        - PlugFilter
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from populse_mia.data_manager import (
    BRICK_OUTPUTS,
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    NOT_DEFINED_VALUE,
    TAG_FILENAME,
)

# Populse_MIA imports
from populse_mia.software_properties import Config
from populse_mia.user_interface.data_browser.advanced_search import (
    AdvancedSearch,
)
from populse_mia.user_interface.data_browser.data_browser import (
    TableDataBrowser,
)
from populse_mia.user_interface.data_browser.rapid_search import RapidSearch
from populse_mia.user_interface.pop_ups import (
    PopUpSelectTagCountTable,
    PopUpVisualizedTags,
)


class PlugFilter(QWidget):
    """
    A PyQt widget for interactively filtering and selecting database scans to
    assign to a pipeline node plug.

    This widget provides a powerful interface for browsing, searching, and
    filtering files from the project database. It features:
        - A customizable data browser with tag columns.
        - Rapid text search for quick filtering.
        - Advanced multi-criteria filtering for precise selection.
        - Tag visibility controls to customize the displayed information.
        - Automatic exclusion of files that are outputs from existing pipeline
          bricks to prevent circular dependencies.

    The widget is designed to integrate seamlessly with a pipeline editor,
    allowing users to select and assign files to a specific node plug. When
    the selection is confirmed, the chosen files are emitted as a list via
    the `plug_value_changed` signal.


    .. Methods:
        - ok_clicked: Applies the selected files to the node plug and closes
                      the widget.
        - reset_search_bar: Resets the search interface to its initial state,
                            clearing all filters.
        - search_str: Filters and updates the displayed scans based on the
                      provided search string.
        - set_plug_value: Extracts the selected or filtered scan values and
                          emits them via the `plug_value_changed` signal.
        - update_tag_to_filter: Opens a dialog to select a tag for filtering
                                and updates the filter button text.
        - update_tags: Opens a dialog to update the list of visualized tags
                       and refreshes the table view.
    """

    # Signal emitted when the user confirms their selection. The signal carries
    # a list of selected file paths or attribute values.
    plug_value_changed = pyqtSignal(list)

    def __init__(
        self,
        project,
        scans_list,
        process,
        node_name,
        plug_name,
        node_controller,
        main_window,
    ):
        """
        Initialize the PlugFilter widget for filtering database scans.

        Creates a filterable data browser interface with search capabilities,
        tag visualization controls, and scan selection. Automatically excludes
        scans that are outputs from existing pipeline bricks.

        :param project: Current project instance containing database and
                        folder paths
        :param scans_list: Initial list of database file paths to filter. If
                           empty, all scans from COLLECTION_CURRENT are
                           included
        :param process: Process instance associated with the selected pipeline
                        node
        :param node_name: Display name of the current pipeline node
        :param plug_name: Name of the selected node plug/connection point
        :param node_controller: Parent controller managing node visibility and
                                tags
        :param main_window: Main application window containing the pipeline
                            manager
        """
        super().__init__(None)
        self.project = project
        self.node_controller = node_controller
        self.main_window = main_window
        self.process = process
        self.plug_name = plug_name
        # Collect all brick output paths to exclude from scan list
        brick_outputs = set()

        with self.project.database.data() as database_data:

            for brick in self.main_window.pipeline_manager.brick_list:
                doc = database_data.get_document(
                    collection_name=COLLECTION_BRICK, primary_keys=brick
                )

                if doc and BRICK_OUTPUTS in doc[0]:
                    # Extract non-empty string outputs as relative paths
                    outputs = (
                        os.path.relpath(value, self.project.folder)
                        for value in doc[0][BRICK_OUTPUTS].values()
                        if isinstance(value, str) and value
                    )
                    brick_outputs.update(outputs)

            # Filter scans or use all current collection documents
            if scans_list:
                self.scans_list = [
                    scan.replace(self.project.folder, "").lstrip("\\/")
                    for scan in scans_list
                    if scan.replace(self.project.folder, "").lstrip("\\/")
                    not in brick_outputs
                ]

            else:
                self.scans_list = database_data.get_document_names(
                    COLLECTION_CURRENT
                )

        # Configure window
        self.setWindowTitle(f"Filter - {node_name} - {plug_name}")
        # Create main table browser
        self.table_data = TableDataBrowser(
            self.project,
            self,
            self.node_controller.visibles_tags,
            False,
            True,
            link_viewer=False,
        )
        # Reducing the list of scans to selection
        all_scans = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.scans_list
        self.table_data.scans_to_search = self.scans_list
        self.table_data.update_visualized_rows(all_scans)
        # Create search bar with clear button
        self.rapid_search = RapidSearch(self)
        self.rapid_search.textChanged.connect(self.search_str)
        self.button_cross = QToolButton()
        self.button_cross.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.button_cross.setIcon(
            QIcon(os.path.join(Config().getSourceImageDir(), "gray_cross.png"))
        )
        self.button_cross.clicked.connect(self.reset_search_bar)
        search_bar_layout = QHBoxLayout()
        search_bar_layout.addWidget(self.rapid_search)
        search_bar_layout.addWidget(self.button_cross)
        # Create advanced search
        self.advanced_search = AdvancedSearch(
            self.project,
            self,
            self.scans_list,
            self.node_controller.visibles_tags,
            from_pipeline=True,
        )
        self.advanced_search.show_search()
        # Create control buttons
        push_button_tags = QPushButton("Visualized tags")
        push_button_tags.clicked.connect(self.update_tags)
        self.push_button_tag_filter = QPushButton(TAG_FILENAME)
        self.push_button_tag_filter.clicked.connect(self.update_tag_to_filter)
        push_button_ok = QPushButton("OK")
        push_button_ok.clicked.connect(self.ok_clicked)
        push_button_cancel = QPushButton("Cancel")
        push_button_cancel.clicked.connect(self.close)
        # Assemble layouts
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(push_button_tags)
        buttons_layout.addWidget(self.push_button_tag_filter)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(push_button_ok)
        buttons_layout.addWidget(push_button_cancel)
        main_layout = QVBoxLayout()
        main_layout.addLayout(search_bar_layout)
        main_layout.addWidget(self.advanced_search)
        main_layout.addWidget(self.table_data)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        # Set window size based on screen resolution
        screen_resolution = QApplication.instance().desktop().screenGeometry()
        self.setMinimumWidth(round(0.6 * screen_resolution.width()))
        self.setMinimumHeight(round(0.8 * screen_resolution.height()))

    def ok_clicked(self):
        """
        Handle OK button click by applying changes and closing the dialog.

        Commits the current widget value to the associated node plug, then
        closes the widget dialog.
        """
        self.set_plug_value()
        self.close()

    def reset_search_bar(self):
        """
        Reset search interface to initial state and restore all scan rows.

        Clears the rapid search text field, resets advanced search rows,
        and restores the full scan list to the table view, updating the
        display to reflect all available scans.
        """
        # Clear search UI components
        self.rapid_search.setText("")
        self.advanced_search.rows = []
        self.advanced_search.show_search()
        # Restore full scan list
        old_scan_list = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.scans_list
        self.table_data.scans_to_search = self.scans_list
        self.table_data.update_visualized_rows(old_scan_list)

    def search_str(self, str_search):
        """
        Filter and update the list of scans displayed in the browser based on
        search criteria.

        This method updates `scans_to_visualize` by applying either a rapid
        search filter or showing all available scans when the search is empty.
        Special handling is provided for the NOT_DEFINED_VALUE constant to
        filter scans with undefined tag values.

        :parm str_search (str): The search string entered by the user. An
                                empty string shows all scans, NOT_DEFINED_VALUE
                                filters for scans with undefined tags, and any
                                other value performs a rapid search filter.

        Side Effects:
            - Updates self.table_data.scans_to_visualize with filtered scan
              list
            - Updates self.advanced_search.scans_list with the same filtered
              list
            - Triggers UI update via self.table_data.update_visualized_rows()
        """
        old_scan_list = self.table_data.scans_to_visualize

        # Return all scans if search is empty
        if not str_search:
            filtered_scans = self.table_data.scans_to_search

        else:

            with self.project.database.data() as database_data:
                shown_tags = database_data.get_shown_tags()
                # Determine filter based on search type
                filter_func = (
                    self.prepare_not_defined_filter(shown_tags)
                    if str_search == NOT_DEFINED_VALUE
                    else self.rapid_search.prepare_filter(
                        str_search, shown_tags, self.table_data.scans_to_search
                    )
                )
                scans = database_data.filter_documents(
                    COLLECTION_CURRENT, filter_func
                )

            # Extract filenames from filtered scans
            filtered_scans = [scan[TAG_FILENAME] for scan in scans]

        # Update state with filtered results
        self.table_data.scans_to_visualize = filtered_scans
        self.advanced_search.scans_list = filtered_scans
        self.table_data.update_visualized_rows(old_scan_list)

    def set_plug_value(self):
        """
        Extract selected or filtered scan values and emit to node plug.

        Retrieves values from the database for the currently filtered tag.
        If items are selected in the table, only those values are extracted.
        Otherwise, all filtered items are processed. For filename tags,
        paths are converted to absolute paths within the project folder.

        :Emits: plug_value_changed: Signal with list of extracted values.
        """

        def _get_scan_value(database_data, scan_name, tag_name):
            """
            Retrieve and process a single scan value from the database.

            :param database_data: Database connection object.
            :param scan_name: Primary key identifying the scan.
            :param tag_name: Field name to retrieve.

            :return: The field value, with absolute path conversion for
                     filename tags.
            """
            value = database_data.get_value(
                collection_name=COLLECTION_CURRENT,
                primary_key=scan_name,
                field=tag_name,
            )

            if tag_name == TAG_FILENAME:
                value = os.path.abspath(
                    os.path.join(self.project.folder, value)
                )

            return value

        tag_name = self.push_button_tag_filter.text().lstrip("&")

        with self.project.database.data() as database_data:

            # Determine which scans to process
            if selected_points := self.table_data.selectedIndexes():
                scan_names = [
                    self.table_data.item(point.row(), 0).text()
                    for point in selected_points
                ]

            else:
                scan_names = self.table_data.get_current_filter()

            # Extract values for each scan
            result_names = [
                _get_scan_value(database_data, scan_name, tag_name)
                for scan_name in scan_names
            ]

        self.plug_value_changed.emit(result_names)

    def update_tag_to_filter(self):
        """
        Open a dialog to select a tag filter and update the button text.

        Displays a popup dialog allowing the user to select a tag from the
        available visible tags. If a tag is selected (dialog accepted), updates
        the filter button's text to reflect the chosen tag.
        """
        popup = PopUpSelectTagCountTable(
            self.project,
            self.node_controller.visibles_tags,
            self.push_button_tag_filter.text(),
        )

        if popup.exec_():
            self.push_button_tag_filter.setText(popup.selected_tag)

    def update_tags(self):
        """
        Open a dialog to update the list of visualized tags.

        Displays a modal dialog allowing users to select which tags should be
        visualized in the table. If accepted, updates the visible columns in
        the data table, refreshes the node controller's visible tags list, and
        updates all advanced search field dropdowns with the new tag selection.

        The 'Filename' tag is always included in the visible tags list.
        """

        # Clean up existing dialog if present
        if hasattr(self, "dialog") and self.dialog:
            self.dialog.deleteLater()
            self.dialog = None

        # Create and configure dialog
        self.dialog = QDialog()
        self.dialog.setMinimumSize(600, 600)
        # Set up dialog content
        visualized_tags = PopUpVisualizedTags(
            self.project, self.node_controller.visibles_tags
        )
        # Create dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.dialog.accept)
        buttons.rejected.connect(self.dialog.reject)
        # Build dialog layout
        layout = QVBoxLayout()
        layout.addWidget(visualized_tags)
        layout.addWidget(buttons)
        self.dialog.setLayout(layout)
        # Show dialog and process result
        self.dialog.show()

        if self.dialog.exec():
            # Extract selected tags from list widget
            new_visibilities = [
                visualized_tags.list_widget_selected_tags.item(i).text()
                for i in range(
                    visualized_tags.list_widget_selected_tags.count()
                )
            ]
            new_visibilities.append(TAG_FILENAME)
            # Update table columns and node controller
            self.table_data.update_visualized_columns(
                self.node_controller.visibles_tags, new_visibilities
            )
            self.node_controller.visibles_tags = new_visibilities

            # Update all advanced search field dropdowns
            for row in self.advanced_search.rows:
                fields = row[2]
                fields.clear()

                for visible_tag in new_visibilities:
                    fields.addItem(visible_tag)

                fields.model().sort(0)
                fields.addItem("All visualized tags")

        # Clean up dialog reference
        self.dialog.deleteLater()
        self.dialog = None
