"""
Module to define data browser tab appearance, settings and methods.

Contains:
    Class:
        - DataBrowser
        - DateFormatDelegate
        - DateTimeFormatDelegate
        - NumberFormatDelegate
        - TableDataBrowser
        - TimeFormatDelegate

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import ast
import bisect
import logging
import os
import platform
import subprocess
from functools import partial
from pathlib import Path
from typing import get_origin

# PyQt5 imports
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QDateEdit,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QItemDelegate,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from populse_mia.data_manager import (
    BRICK_INPUTS,
    BRICK_NAME,
    BRICK_OUTPUTS,
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    COLLECTION_INITIAL,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_LIST_BOOLEAN,
    FIELD_TYPE_LIST_DATE,
    FIELD_TYPE_LIST_DATETIME,
    FIELD_TYPE_LIST_FLOAT,
    FIELD_TYPE_LIST_INTEGER,
    FIELD_TYPE_LIST_JSON,
    FIELD_TYPE_LIST_STRING,
    FIELD_TYPE_LIST_TIME,
    FIELD_TYPE_STRING,
    FIELD_TYPE_TIME,
    NOT_DEFINED_VALUE,
    TAG_BRICKS,
    TAG_CHECKSUM,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_ORIGIN_BUILTIN,
    TAG_ORIGIN_USER,
)
from populse_mia.software_properties import Config
from populse_mia.user_interface.data_browser.advanced_search import (
    AdvancedSearch,
)
from populse_mia.user_interface.data_browser.count_table import CountTable
from populse_mia.user_interface.data_browser.mini_viewer import MiniViewer
from populse_mia.user_interface.data_browser.modify_table import ModifyTable

# Populse_MIA imports
from populse_mia.user_interface.data_browser.rapid_search import RapidSearch
from populse_mia.user_interface.pop_ups import (
    ClickableLabel,
    PopUpAddPath,
    PopUpAddTag,
    PopUpCloneTag,
    PopUpDataBrowserCurrentSelection,
    PopUpMultipleSort,
    PopUpProperties,
    PopUpRemoveScan,
    PopUpRemoveTag,
    PopUpSelectFilter,
    PopUpShowHistory,
)

logger = logging.getLogger(__name__)


class DataBrowser(QWidget):
    """
    Widget that manages and displays the contents of the **Data Browser** tab.

    The Data Browser provides an interface for viewing, filtering, tagging,
    and sending documents to the pipeline manager. It integrates tools for
    advanced search, tag management, and visual inspection of loaded data.

    .. Methods:
        - add_tag_infos: Add the tag after add tag pop-up
        - add_tag_pop_up: Display the add tag pop-up
        - clone_tag_infos: Clone the tag after the clone tag pop-up
        - connect_actions: Connect actions method to views
        - connect_mini_viewer: Display the selected documents in the viewer
        - connect_toolbar: Connect toolbar views to methods
        - count_table_pop_up: Open the count table
        - create_layout: Create the layout of the data browser
        - create_toolbar_view: Create the toolbar views
        - move_splitter: Check if the viewer's splitter is at its lowest
                         position
        - open_filter: Open a project filter that has already been saved
        - open_filter_infos: Apply the current filter
        - remove_tag_infos: Remove user tags after the pop-up
        - remove_tag_pop_up: Display the pop-up to remove user tags
        - reset_search_bar: Reset the rapid search bar
        - search_str: Search a string in the table and updates the
                      visualized documents
        - send_documents_to_pipeline: Send the current list of scans to the
                                      Pipeline Manager
        - show_clone_tag_popup: Display the clone tag pop-up
        - toggle_advanced_search: Toggle the visibility of the advanced search
                                  interface
        - update_database: Update the database in the software

    """

    def __init__(self, project, main_window):
        """
        Initialization of the data_browser class.

        :param project: Current project in the software
        :param main_window: Main window of the software
        """
        super().__init__()
        # Store references
        self.project = project
        self.main_window = main_window
        # Flag (bool) indicating if data has been sent to pipeline
        self.data_sent = False
        # Initialize core components
        # Create and configure menu/toolbar actions
        self.add_tag_action = QAction("Add tag", self, shortcut="Ctrl+A")
        self.clone_tag_action = QAction("Clone tag", self)
        self.remove_tag_action = QAction("Remove tag", self, shortcut="Ctrl+R")
        self.save_filter_action = QAction("Save current filter", self)
        self.open_filter_action = QAction(
            "Open filter", self, shortcut="Ctrl+F"
        )
        # Initialize core MIA functional components
        # Quick search functionality
        self.search_bar = RapidSearch(self)
        # Compact data viewer component
        self.viewer = MiniViewer(self.project)
        # Advanced search interface
        self.advanced_search = AdvancedSearch(self.project, self)
        # Create and configure UI widgets
        # Labels and clickable elements
        self.addRowLabel = ClickableLabel()
        # Frames for organization
        self.frame_table_data = QFrame(self)
        self.frame_visualization = QFrame(self)
        self.frame_advanced_search = QFrame(self)
        self.frame_test = QFrame()
        # Buttons
        self.send_documents_to_pipeline_button = QPushButton(
            "Send documents to the Pipeline Manager"
        )
        self.advanced_search_button = QPushButton()
        self.visualized_tags_button = QPushButton()
        self.count_table_button = QPushButton()
        self.button_cross = QToolButton()
        # Layout components
        self.splitter_vertical = QSplitter(Qt.Vertical)
        self.menu_toolbar = QToolBar()
        # Create and configure the main data table

        with self.project.database.data() as database_data:
            shown_tags = database_data.get_shown_tags()

        # Main data table display
        self.table_data = TableDataBrowser(
            self.project, self, shown_tags, True, True
        )
        self.table_data.setObjectName("table_data")
        # Setup layout and connections
        self.create_toolbar_view()
        self.create_layout()
        # Image viewer updated
        self.connect_toolbar()
        self.connect_actions()
        self.connect_mini_viewer()

    def add_tag_infos(
        self,
        new_tag_name,
        new_default_value,
        tag_type,
        new_tag_description,
        new_tag_unit,
    ):
        """
        Add a new tag to both current and initial database collections.

        This method creates a new tag field in the database schema and
        populates it with default values for all existing scans. The operation
        is tracked in the project's undo/redo history.

        :param new_tag_name (str): Name of the new tag to create
        :param new_default_value: Default value to assign to all existing scans
        :param tag_type (str): Data type of the tag
                               (e.g., FIELD_TYPE_STRING, FIELD_TYPE_FLOAT)
        :param new_tag_description (str): Human-readable description of the tag
        :param new_tag_unit (str): Unit of measurement for the tag value

        Note:
            - Marks the project as having unsaved modifications
            - Adds the operation to the undo history
            - Updates the UI table with the new column
        """
        # Import table_to_database only here to prevent circular import issue
        from populse_mia.utils import table_to_database

        # Prepare field configuration (DRY principle)
        field_config = {
            "field_name": new_tag_name,
            "field_type": tag_type,
            "description": new_tag_description,
            "visibility": True,
            "origin": TAG_ORIGIN_USER,
            "unit": new_tag_unit,
            "default_value": new_default_value,
        }
        values = []
        converted_default = table_to_database(new_default_value, tag_type)

        # Add field to database schema for both collections
        with self.project.database.schema() as database_schema:

            for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                database_schema.add_field(
                    {**field_config, "collection_name": collection}
                )

        # Populate existing scans with default values
        with self.project.database.data(write=True) as database_data:
            scans = database_data.get_document(
                collection_name=COLLECTION_CURRENT
            )

            if scans:  # Only mark as modified if there are scans to update
                self.project.unsavedModifications = True

            for scan in scans:
                filename = scan[TAG_FILENAME]
                update_dict = {new_tag_name: converted_default}

                # Update both collections
                for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                    database_data.set_value(
                        collection_name=collection,
                        primary_key=filename,
                        values_dict=update_dict,
                    )
                # Track for history
                values.append(
                    [
                        filename,
                        new_tag_name,
                        converted_default,  # current_value
                        converted_default,  # initial_value
                    ]
                )

        # Update undo/redo history
        self.project.undos.append(
            [
                "add_tag",
                new_tag_name,
                tag_type,
                new_tag_unit,
                new_default_value,
                new_tag_description,
                values,
            ]
        )
        self.project.redos.clear()
        # Update UI table
        column_index = self.table_data.get_index_insertion(new_tag_name)
        self.table_data.add_column(column_index, new_tag_name)

    def add_tag_pop_up(self):
        """
        Display a popup window for adding a new tag to the project.

        This method initializes and shows a `PopUpAddTag` dialog, allowing the
        user to add a new tag to the current project. The popup is modal and
        tied to the current project context.
        """
        self.pop_up_add_tag = PopUpAddTag(self, self.project)
        self.pop_up_add_tag.show()

    def clone_tag_infos(self, tag_to_clone, new_tag_name):
        """
        Clone a tag and its associated data, creating a new tag with the same
        attributes and values.

        This method clones the specified tag, including its schema and data,
        into a new tag. The new tag is added to both the current and initial
        collections, and all existing values for the original tag are copied
        to the new tag. The operation is recorded in the project's undo
        history.

        :param tag_to_clone (str): Name of the tag to clone
        :param new_tag_name (str): Name of the new tag to create

         Notes:
            - The new tag is added to the database schema and data for both
              COLLECTION_CURRENT amd COLLECTION_INITIAL collections.
            - The project's unsaved modifications flag is set to True.
            - The operation is recorded in the project's undo history.
        """

        # Fetch the attributes of the tag to clone from both collections
        with self.project.database.data() as database_data:
            tag_cloned_curr = database_data.get_field_attributes(
                COLLECTION_CURRENT, tag_to_clone
            )
            tag_cloned_init = database_data.get_field_attributes(
                COLLECTION_INITIAL, tag_to_clone
            )

        # Add the new tag to the schema for both collections
        with self.project.database.schema() as database_schema:

            for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                tag_cloned = (
                    tag_cloned_curr
                    if collection == COLLECTION_CURRENT
                    else tag_cloned_init
                )
                database_schema.add_field(
                    {
                        "collection_name": collection,
                        "field_name": new_tag_name,
                        "field_type": tag_cloned["field_type"],
                        "description": tag_cloned["description"],
                        "visibility": True,
                        "origin": TAG_ORIGIN_USER,
                        "unit": tag_cloned["unit"],
                        "default_value": tag_cloned["default_value"],
                    }
                )

        self.project.unsavedModifications = True
        # Clone the values for each scan in the current collection
        values = []

        with self.project.database.data(write=True) as database_data:

            for scan in database_data.get_document(
                collection_name=COLLECTION_CURRENT
            ):
                # If the tag to clone has a value, we add this value with the
                # new tag name in the Database
                filename = scan[TAG_FILENAME]

                for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                    cloned_value = database_data.get_value(
                        collection_name=collection,
                        primary_key=filename,
                        field=tag_to_clone,
                    )

                    if cloned_value is not None:
                        database_data.set_value(
                            collection_name=collection,
                            primary_key=filename,
                            values_dict={new_tag_name: cloned_value},
                        )
                        values.append([filename, new_tag_name, cloned_value])

        # Record the operation in the project's undo history
        history_maker = [
            "add_tag",
            new_tag_name,
            tag_cloned_curr["field_type"],
            tag_cloned_curr["unit"],
            tag_cloned_curr["default_value"],
            tag_cloned_curr["description"],
            values,
        ]
        self.project.undos.append(history_maker)
        self.project.redos.clear()
        # Add the new tag to the table
        column = self.table_data.get_index_insertion(new_tag_name)
        self.table_data.add_column(column, new_tag_name)

    def connect_actions(self):
        """
        Connect UI actions to their corresponding methods.

        Binds each action's triggered signal to the appropriate slot method,
        enabling interactive functionality for tag management and filter
        operations.
        """
        self.add_tag_action.triggered.connect(self.add_tag_pop_up)
        self.clone_tag_action.triggered.connect(self.show_clone_tag_popup)
        self.remove_tag_action.triggered.connect(self.remove_tag_pop_up)
        self.save_filter_action.triggered.connect(
            lambda: self.project.save_current_filter(
                self.advanced_search.get_filters(False)
            )
        )
        self.open_filter_action.triggered.connect(self.open_filter)

    def connect_mini_viewer(self):
        """Display the selected documents in the viewer."""

        if self.splitter_vertical.sizes()[1] == (
            self.splitter_vertical.minimumHeight()
        ):
            self.viewer.setHidden(True)

        else:
            self.viewer.setHidden(False)
            items = self.table_data.selectedItems()
            full_names = []

            for item in items:
                row = item.row()
                full_name = self.table_data.item(row, 0).text()

                if full_name.endswith(".nii"):

                    if not Path(full_name).is_file():
                        full_name = os.path.relpath(
                            os.path.join(self.project.folder, full_name)
                        )

                    else:
                        full_name = os.path.join(os.sep, full_name)

                    if full_name not in full_names:
                        full_names.append(full_name)

            self.viewer.verify_slices(full_names)

    def connect_toolbar(self):
        """Connect methods to toolbar."""
        self.search_bar.textChanged.connect(self.search_str)
        self.button_cross.clicked.connect(self.reset_search_bar)
        self.advanced_search_button.clicked.connect(
            self.toggle_advanced_search
        )
        self.count_table_button.clicked.connect(self.count_table_pop_up)
        self.visualized_tags_button.clicked.connect(
            lambda: self.table_data.visualized_tags_pop_up()
        )

    def count_table_pop_up(self):
        """Open the count table pop-up."""
        self.count_table_pop_up = CountTable(self.project)
        self.count_table_pop_up.show()

    def create_layout(self):
        """Create the layouts of the tab."""
        self.frame_table_data.setFrameShape(QFrame.StyledPanel)
        self.frame_table_data.setFrameShadow(QFrame.Raised)
        self.frame_table_data.setObjectName("frame_table_data")
        vbox_table = QVBoxLayout()
        vbox_table.addWidget(self.table_data)
        # Add path button under the table
        hbox_layout = QHBoxLayout()
        sources_images_dir = Config().getSourceImageDir()
        self.addRowLabel.setObjectName("plus")
        add_row_picture = QPixmap(
            os.path.relpath(os.path.join(sources_images_dir, "green_plus.png"))
        )
        add_row_picture = add_row_picture.scaledToHeight(20)
        self.addRowLabel.setPixmap(add_row_picture)
        self.addRowLabel.setFixedWidth(20)
        self.addRowLabel.setToolTip(
            "Add data without using the MRI converter tool (File>Import)"
        )
        self.addRowLabel.clicked.connect(self.table_data.add_path)
        hbox_layout.addWidget(self.addRowLabel)
        hbox_layout.addStretch(1)
        self.send_documents_to_pipeline_button.clicked.connect(
            self.send_documents_to_pipeline
        )
        hbox_layout.addWidget(self.send_documents_to_pipeline_button)
        vbox_table.addLayout(hbox_layout)
        self.frame_table_data.setLayout(vbox_table)
        # Visualization:
        # Visualization frame, label and text edit (bot.0tom left of the
        # screen in the application)
        self.frame_visualization.setFrameShape(QFrame.StyledPanel)
        self.frame_visualization.setFrameShadow(QFrame.Raised)
        self.frame_visualization.setObjectName("frame_5")
        self.viewer.setObjectName("viewer")
        self.viewer.adjustSize()
        hbox_viewer = QHBoxLayout()
        hbox_viewer.addWidget(self.viewer)
        self.frame_visualization.setLayout(hbox_viewer)
        # Advanced search:
        self.frame_advanced_search.setFrameShape(QFrame.StyledPanel)
        self.frame_advanced_search.setFrameShadow(QFrame.Raised)
        self.frame_advanced_search.setObjectName("frame_search")
        self.frame_advanced_search.setHidden(True)
        layout_search = QGridLayout()
        layout_search.addWidget(self.advanced_search)
        self.frame_advanced_search.setLayout(layout_search)
        # Splitter and layout:
        self.splitter_vertical.addWidget(self.frame_advanced_search)
        self.splitter_vertical.addWidget(self.frame_table_data)
        self.splitter_vertical.addWidget(self.frame_visualization)
        self.splitter_vertical.splitterMoved.connect(self.move_splitter)
        vbox_splitter = QVBoxLayout(self)
        vbox_splitter.addWidget(self.menu_toolbar)
        vbox_splitter.addWidget(self.splitter_vertical)
        self.setLayout(vbox_splitter)

    def create_toolbar_view(self):
        """Create the toolbar menu at the top of the tab"""
        tags_tool_button = QToolButton()
        tags_tool_button.setText("Tags")
        tags_tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        tags_menu = QMenu()
        tags_menu.addAction(self.add_tag_action)
        tags_menu.addAction(self.clone_tag_action)
        tags_menu.addAction(self.remove_tag_action)
        tags_tool_button.setMenu(tags_menu)
        filters_tool_button = QToolButton()
        filters_tool_button.setText("Filters")
        filters_tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        filters_menu = QMenu()
        filters_menu.addAction(self.save_filter_action)
        filters_menu.addAction(self.open_filter_action)
        filters_tool_button.setMenu(filters_menu)
        sources_images_dir = Config().getSourceImageDir()
        self.button_cross.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.button_cross.setIcon(
            QIcon(os.path.join(sources_images_dir, "gray_cross.png"))
        )
        search_bar_layout = QHBoxLayout()
        search_bar_layout.setSpacing(0)
        search_bar_layout.addWidget(self.search_bar)
        search_bar_layout.addWidget(self.button_cross)
        self.advanced_search_button.setText("Advanced search")
        self.frame_test.setLayout(search_bar_layout)
        self.visualized_tags_button.setText("Visualized tags")
        self.count_table_button.setText("Count table")
        self.menu_toolbar.addWidget(tags_tool_button)
        self.menu_toolbar.addSeparator()
        self.menu_toolbar.addWidget(filters_tool_button)
        self.menu_toolbar.addSeparator()
        self.menu_toolbar.addWidget(self.frame_test)
        self.menu_toolbar.addSeparator()
        self.menu_toolbar.addWidget(self.advanced_search_button)
        self.menu_toolbar.addSeparator()
        self.menu_toolbar.addWidget(self.visualized_tags_button)
        self.menu_toolbar.addSeparator()
        self.menu_toolbar.addWidget(self.count_table_button)

    def move_splitter(self):
        """
        Connect the mini viewer if the splitter is not at its minimum
        position.

        Checks whether the bottom pane of the vertical splitter is at its
        minimum height. If it's larger than the minimum, connects the mini
        viewer.
        """
        bottom_pane_height = self.splitter_vertical.sizes()[1]
        minimum_height = self.splitter_vertical.minimumHeight()

        if bottom_pane_height == minimum_height:
            return

        self.connect_mini_viewer()

    def open_filter(self):
        """
        Display a dialog for selecting and opening a saved project filter.

        Creates and shows a PopUpSelectFilter dialog, allowing the user to
        choose from previously saved filters associated with the current
        project. The dialog is stored as an instance attribute to maintain
        a reference during its lifetime.
        """
        self.popUp = PopUpSelectFilter(self.project, self)
        self.popUp.show()

    def open_filter_infos(self):
        """
        Apply the current project filter to the data table.

        Opens the advanced search interface if the filter contains exclusion
        criteria (nots), updates the search bar text, and refreshes the
        visualized scans to match the filtered document collection.

        The method:
            - Retrieves documents from the current collection
            - Updates scans_to_visualize and scans_to_search
            - Applies the filter's search bar text
            - Shows advanced search interface if exclusion filters exist
        """

        filter_to_apply = self.project.currentFilter
        # We open the advanced search + search_bar
        old_scans = self.table_data.scans_to_visualize

        # Retrieve documents from the current collection
        with self.project.database.data() as database_data:
            documents = database_data.get_document_names(COLLECTION_CURRENT)

        self.table_data.scans_to_visualize = documents
        self.table_data.scans_to_search = documents
        self.table_data.update_visualized_rows(old_scans)
        # Apply search bar filter text
        self.search_bar.setText(filter_to_apply.search_bar)

        # Show advanced search interface if exclusion filters exist

        if filter_to_apply.nots:
            self.frame_advanced_search.setHidden(False)
            self.advanced_search.scans_list = (
                self.table_data.scans_to_visualize
            )
            self.advanced_search.show_search()
            self.advanced_search.apply_filter(filter_to_apply)

    def remove_tag_infos(self, tag_names_to_remove):
        """
        Remove specified tags from the database and update the UI.

        This method removes tags from both the current and initial
        collections, preserving tag attributes and values in the undo history.
        The table display is updated to reflect the changes.

        :param tag_names_to_remove: Iterable of tag names (str) to remove from
                                    the database and table display.

        Side Effects:
            - Marks project as having unsaved modifications
            - Adds removal operation to undo history
            - Clears redo history
            - Removes columns from table display
            - Temporarily disconnects and reconnects table selection signal
        """
        # Temporarily disable selection change signals during update
        self.table_data.itemSelectionChanged.disconnect()

        try:

            # Prepare history entry for undo functionality
            with self.project.database.data() as database_data:

                # Collect attributes for tags being removed
                tags_removed = []

                for tag in tag_names_to_remove:
                    self.project.unsavedModifications = True
                    tag_attrib = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag
                    )
                    tags_removed.append([tag_attrib])

                # Collect current and initial values for all scans and tags
                values_removed = []
                scans = database_data.get_document_names(COLLECTION_CURRENT)

                for tag in tag_names_to_remove:

                    for scan in scans:
                        current_value = database_data.get_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            field=tag,
                        )
                        initial_value = database_data.get_value(
                            collection_name=COLLECTION_INITIAL,
                            primary_key=scan,
                            field=tag,
                        )

                        # Only store if at least one value exists
                        if (
                            current_value is not None
                            or initial_value is not None
                        ):
                            values_removed.append(
                                [scan, tag, current_value, initial_value]
                            )

            history_entry = ["remove_tags", tags_removed, values_removed]
            self.project.undos.append(history_entry)
            self.project.redos.clear()

            # Remove tags from database schema and table columns
            with self.project.database.schema() as database_schema:

                for tag in tag_names_to_remove:
                    database_schema.remove_field(COLLECTION_CURRENT, tag)
                    database_schema.remove_field(COLLECTION_INITIAL, tag)
                    self.table_data.removeColumn(
                        self.table_data.get_tag_column(tag)
                    )

            # Update UI state
            self.table_data.update_selection()

        finally:
            # Ensure signal is reconnected even if an error occurs
            self.table_data.itemSelectionChanged.connect(
                self.table_data.selection_changed
            )

    def remove_tag_pop_up(self):
        """
        Display a modal dialog for removing user tags from the project.

        Creates and shows a PopUpRemoveTag instance, allowing the user to
        select and remove tags associated with the current project.
        """
        self.pop_up_remove_tag = PopUpRemoveTag(self, self.project)
        self.pop_up_remove_tag.show()

    def reset_search_bar(self):
        """
        Clear the search bar input field.

        This method resets the search bar to an empty state by clearing
        any existing text content.
        """
        self.search_bar.setText("")

    def search_str(self, str_search):
        """
        Search and filter documents in the table based on a search string.

        Updates the table's visualized documents based on the search criteria.
        An empty string shows all searchable scans. The special value
        NOT_DEFINED_VALUE filters for documents with undefined field values.

        :param str_search: The search string to filter documents. Empty string
                           returns all searchable scans. NOT_DEFINED_VALUE
                           returns scans with undefined values.
        """
        old_scan_list = self.table_data.scans_to_visualize

        # Handle empty search - return all searchable scans
        if not str_search:
            filtered_scans = self.table_data.scans_to_search

        else:

            with self.project.database.data() as database_data:
                shown_tags = database_data.get_shown_tags()

                # Prepare filter based on search type
                if str_search == NOT_DEFINED_VALUE:
                    filter_criteria = (
                        self.search_bar.prepare_not_defined_filter(shown_tags)
                    )

                else:
                    filter_criteria = self.search_bar.prepare_filter(
                        str_search,
                        shown_tags,
                        self.table_data.scans_to_search,
                    )

                # Apply filter and extract filenames
                filtered_documents = database_data.filter_documents(
                    COLLECTION_CURRENT, filter_criteria
                )
                filtered_scans = [
                    scan[TAG_FILENAME] for scan in filtered_documents
                ]

        # Update table state
        self.table_data.scans_to_visualize = filtered_scans
        self.table_data.update_visualized_rows(old_scan_list)
        self.project.currentFilter.search_bar = str_search

    def send_documents_to_pipeline(self):
        """
        Display a popup dialog for sending filtered scans to the Pipeline
        Manager.

        Retrieves the currently filtered scans from the table data and
        presents them in a selection popup, allowing the user to confirm
        which scans to send to the pipeline.

        The popup is shown modally and references the main window as its
        parent.
        """
        current_scans = self.table_data.get_current_filter()
        # Displays a popup with the list of scans
        self.show_selection = PopUpDataBrowserCurrentSelection(
            self.project, self, current_scans, self.main_window
        )
        self.show_selection.show()

    def show_clone_tag_popup(self):
        """
        Display a popup dialog for cloning a tag.

        This method initializes and shows a popup dialog (`PopUpCloneTag`)
        to allow the user to clone a tag within the current project context.

        The popup is stored as an instance variable for later reference if
        needed.
        """
        self.pop_up_clone_tag = PopUpCloneTag(self, self.project)
        self.pop_up_clone_tag.show()

    def toggle_advanced_search(self):
        """
        Toggle the visibility of the advanced search interface.

        If the advanced search is hidden, it resets and displays the search
        interface, updating the scans list to the current visualized scans.
        If the advanced search is visible, it hides the interface, resets the
        search state, and restores the original scans list to the data browser.

        This method ensures the UI and data state are synchronized with the
        visibility of the advanced search.
        """

        if self.frame_advanced_search.isHidden():
            # Display the advanced search interface and reset its state
            self.advanced_search.scans_list = (
                self.table_data.scans_to_visualize
            )
            self.frame_advanced_search.setHidden(False)
            self.advanced_search.show_search()

        else:
            # Hide the advanced search interface and restore the original
            # scans list
            old_scans_list = self.table_data.scans_to_visualize
            self.frame_advanced_search.setHidden(True)
            self.advanced_search.rows = []
            self.table_data.scans_to_visualize = (
                self.advanced_search.scans_list
            )

            with self.project.database.data() as database_data:
                self.table_data.scans_to_search = (
                    database_data.get_document_names(COLLECTION_CURRENT)
                )

            # Reset the current filter
            self.project.currentFilter.nots = []
            self.project.currentFilter.values = []
            self.project.currentFilter.fields = []
            self.project.currentFilter.links = []
            self.project.currentFilter.conditions = []
            self.table_data.update_visualized_rows(old_scans_list)

    def update_database(self, database):
        """
        Update the project database and reset UI state.

        This method propagates the database instance to all components that
        need it and resets UI elements to their default state. It's called
        during project lifecycle events (new, open, save as).

        :param database: The new Database instance to use across the
                         application.
        """

        # Propagate database to all dependent components
        for component in (
            self,
            self.table_data,
            self.viewer,
            self.advanced_search,
        ):
            component.project = database

        # Reset UI state for new project
        self.frame_advanced_search.setHidden(True)


class DateFormatDelegate(QItemDelegate):
    """
    A custom delegate for handling date editing in table views.

    This delegate provides a QDateEdit widget for editing date values in table
    cells, with dates formatted as DD/MM/YYYY. It replaces the default text
    editor with a calendar-based date picker for improved user experience and
    data validation.

    .. Methods:
        - createEditor: Create and return a QDateEdit widget for editing dates
    """

    def __init__(self, parent=None):
        """
        Initialize the DateFormatDelegate.

        :param parent: Optional parent QObject. Defaults to None.
        """
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """
        Create and return a QDateEdit widget for editing dates.

        This method is called by the view when a cell needs to be edited.
        It creates a date editor with DD/MM/YYYY format.

        :param parent: The parent widget for the editor.
        :param option: Style options for rendering the item.
        :param index: The model index of the item being edited.

        :return (QDateEdit): A configured date editor widget.
        """
        editor = QDateEdit(parent)
        editor.setDisplayFormat("dd/MM/yyyy")
        # Enable calendar popup for better user experience with a visual
        # calendar picker
        editor.setCalendarPopup(True)
        return editor


class DateTimeFormatDelegate(QItemDelegate):
    """
    Custom delegate for displaying and editing datetime values in table views.

    This delegate provides a QDateTimeEdit widget for editing datetime cells,
    formatted as DD/MM/YYYY HH:MM:SS.mmm (day/month/year with milliseconds).

    .. Methods:
        - createEditor: Create and return a QDateTimeEdit widget for editing
                        datetimes
    """

    DATETIME_FORMAT = "dd/MM/yyyy hh:mm:ss.zzz"

    def __init__(self, parent=None):
        """
        Initialize the datetime delegate.

        :param parent: Optional parent QWidget. Defaults to None.
        """
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """
         Create and configure a datetime editor widget.

        :param parent: Parent widget for the editor.
        :param option: Style options for the item.
        :param index: Model index of the item being edited.

        :return (QDateTimeEdit): Configured datetime editor widget.
        """
        editor = QDateTimeEdit(parent)
        editor.setDisplayFormat(self.DATETIME_FORMAT)
        return editor


class NumberFormatDelegate(QItemDelegate):
    """
    Delegate for handling numeric input in table cells.

    The number of decimal places is automatically inferred from the
    existing cell value, ensuring consistent formatting of numeric inputs.

    .. Methods:
        - createEditor: Create and return a QDoubleSpinBox widget for editing
                        numbers
    """

    def __init__(self, parent=None):
        """
        Initialize the NumberFormatDelegate.

        :param parent (QWidget): The parent widget. Defaults to None.
        """
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """
        Create and configure a QDoubleSpinBox editor for numeric input.

        The number of decimal places is determined by examining the current
        cell value.

        :param parent: Parent widget for the editor.
        :param option: Style options for the item.
        :paramindex: Model index of the item being edited.

        :return (QDoubleSpinBox): A spin box editor configured with the
                                  appropriate decimal precision.
        """

        editor = QDoubleSpinBox(parent)
        editor.setMaximum(1e10)
        # Determine decimal places from the current value
        data = index.data(Qt.EditRole)
        # Extract the number of decimal places from a numeric string
        text = str(data) if data is not None else ""
        decimal_places = len(text.split(".")[-1]) if "." in text else 0
        editor.setDecimals(decimal_places)
        return editor


class TableDataBrowser(QTableWidget):
    """Table widget that displays the documents contained in the database and
    their associated tags.

    .. Methods:
        - _safe_disconnect: Safely disconnect the itemChanged signal
        - _safe_reconnect: Safely reconnect the itemChanged signal
        - add_column: Add a column to the table
        - add_columns: Add columns to the table
        - add_path: Call a pop-up to add any document to the project
        - add_rows: Insert rows if they are not already in the table
        - clear_cell: Clear the selected cells
        - context_menu_table: Create the context menu of the table
        - delete_from_brick: Delete a document from its brick id
        - display_file: Tries to display a file in the user's preferred
                        application
        - display_unreset_values: Display an error message when trying to
                                  reset user tags
        - edit_table_data_values: Change values in DataBrowser
        - fill_cells_update_table: Initialize and fills the cells of the table
        - fill_headers: Initialize and fill the headers of the table
        - get_current_filter: Get the current data browser selection
        - get_index_insertion: Get index insertion of a new column
        - get_scan_row: Return the row index of the scan
        - get_tag_column: Return the column index of the tag
        - mouseReleaseEvent: Called when clicking released on cells
        - multiple_sort_infos: Sort the table according to the tags specify
                               in list_tags
        - multiple_sort_pop_up: Display the multiple sort pop-up
        - on_cell_changed: Changes the background color and the value of
                           cells when edited by the user
        - remove_scan: Remove documents from table and project
        - reset_cell: Reset the selected cells to their original values
        - reset_column: Reset the selected columns to their original values
        - reset_row: Reset the selected rows to their original values
        - section_moved: Called when the columns of the data_browser are moved
        - select_all_column: Called when single clicking on the column header
                             to select the whole column
        - select_all_columns: Called from context menu to select the columns
        - selection_changed: Called when the selection is changed
        - show_brick_history: Show brick history pop-up
        - sort_column: Sort the current column
        - sort_updated: Called when the button advanced search is called
        - update_colors: Update the background of all the cells
        - update_selection: Called after searches to update the selection
        - update_table: Fill the table with the project's data
        - update_visualized_columns: Update the visualized tags
        - update_visualized_rows: Update the list of documents (scans) in
                                  the table
        - visualized_tags_pop_up: Display the visualized tags pop-up
    """

    def __init__(
        self,
        project,
        data_browser,
        tags_to_display,
        update_values,
        activate_selection,
        link_viewer=True,
    ):
        """
        Initialize the data table widget with project data and browser
        context.

        :param project (Project): The current project instance containing data
                                  and configuration.
        :param data_browser (DataBrowser): Parent DataBrowser widget that
                                           contains this table.
        :param tags_to_display (list[str]): List of metadata tags to show as
                                            table columns.
        :param update_values (bool): If True, enables cell editing;
                                     if False, table is read-only.
        :param activate_selection (bool): True to enable the selection
                                          feature, False otherwise.
        :param link_viewer(bool): If True, links table selection to external
                                  viewer widget. Defaults to True.

        Notes:
            - Column sorting and reordering are enabled by default
              (except first column).
            - Extended selection mode is used unless ``activate_selection``
              is falsy.
            - A custom context menu is available only when both
              ``activate_selection`` and ``link_viewer`` are True.
        """
        super().__init__()
        # Store instance attributes
        self.project = project
        self.data_browser = data_browser
        self.tags_to_display = tags_to_display
        self.update_values = update_values
        self.activate_selection = activate_selection
        self.link_viewer = link_viewer
        self.bricks = {}
        # Configure table behavior
        # Configure selection mode based on activate_selection setting
        self.setSelectionMode(
            QAbstractItemView.ExtendedSelection
            if self.activate_selection
            else QAbstractItemView.NoSelection
        )
        # Configure header behavior
        horizontal_header = self.horizontalHeader()
        # Allows to move the columns (except the first column name)
        horizontal_header.setSectionsMovable(True)
        # Allows the automatic sort
        # self.setSortingEnabled(True)
        self.setSortingEnabled(False)
        self.verticalHeader().setMinimumSectionSize(30)

        # Disable editing if update_values is False
        if not self.update_values:
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Set up context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # Connect Qt signals to their respective slot handlers
        # Only connect context menu handler when selection is active and
        # linked to viewer
        if self.activate_selection and self.link_viewer:
            self.customContextMenuRequested.connect(self.context_menu_table)

        # Item changes
        self.itemChanged.connect(self.on_cell_changed)

        # Selection changes (only when selection is active)
        if self.activate_selection:
            self.itemSelectionChanged.connect(self.selection_changed)

        # Header interactions
        horizontal_header.sortIndicatorChanged.connect(self.sort_updated)
        horizontal_header.sectionDoubleClicked.connect(self.select_all_column)
        horizontal_header.sectionMoved.connect(self.section_moved)
        # Initialize table content
        self.update_table(True)

    def _safe_disconnect(self, signal, slot):
        """
        Disconnect a Qt signal from a slot if connected.

        Attempts to disconnect ``signal`` from ``slot`` and silently ignores
        the error raised when the connection does not exist. This makes the
        operation idempotent and safe to call multiple times.

        :param signal: The Qt signal to disconnect from.
        :param slot: The slot (callable) previously connected to the signal.
        """

        try:
            signal.disconnect(slot)

        except TypeError:
            # Raised by Qt when the signal/slot connection does not exist
            pass

    def _safe_reconnect(self, signal, slot):
        """
        Reconnect a Qt signal to a slot, ensuring a single connection.

        First disconnects ``signal`` from ``slot`` (if connected) to avoid
        duplicate connections, then connects them. This guarantees that the
        slot is connected exactly once.

        :param signal: The Qt signal to (re)connect.
        :param slot: The slot (callable) to connect to the signal.
        """
        self._safe_disconnect(signal, slot)
        signal.connect(slot)

    def add_column(self, column, tag):
        """
        Add a new column to the table with the specified tag.

        Inserts a column at the given index, configures its header with
        metadata from the database, sets the appropriate delegate based on
        field type, and populates cells with current values from the database.

        :param column (int): Zero-based index where the column should be
                             inserted.
        :param tag (str): Tag name identifying the field to add from the
                          database.

        Note:
            Temporarily disconnects item change signals during insertion to
            prevent unwanted event triggers, then reconnects them after
            completion.
        """
        # Import locally to avoid circular dependency
        from populse_mia.utils import set_item_data

        # Safely disconnect signals
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:
            # Insert column and configure header
            self.insertColumn(column)
            header_item = QTableWidgetItem()
            self.setHorizontalHeaderItem(column, header_item)

            with self.project.database.data() as database_data:
                tag_attrib = database_data.get_field_attributes(
                    COLLECTION_CURRENT, tag
                )
                field_type = tag_attrib["field_type"]
                # Configure header with tag metadata
                header_item.setText(tag)
                header_item.setToolTip(
                    f"Description: {tag_attrib['description']}\n"
                    f"Unit: {tag_attrib['unit']}\n"
                    f"Type: {field_type}"
                )
                # Map field types to their corresponding delegates
                delegate_map = {
                    FIELD_TYPE_FLOAT: NumberFormatDelegate,
                    FIELD_TYPE_DATETIME: DateTimeFormatDelegate,
                    FIELD_TYPE_DATE: DateFormatDelegate,
                    FIELD_TYPE_TIME: TimeFormatDelegate,
                }
                # Set appropriate delegate for column based on field type
                delegate_class = delegate_map.get(field_type)
                delegate = delegate_class(self) if delegate_class else None
                self.setItemDelegateForColumn(column, delegate)

                # Populate column cells with values from database
                for row in range(self.rowCount()):
                    item = QTableWidgetItem()
                    self.setItem(row, column, item)
                    scan = self.item(row, 0).text()
                    cur_value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan,
                        field=tag,
                    )

                    if cur_value is not None:
                        set_item_data(item, cur_value, field_type)

                    else:
                        # Style undefined values with italic bold font
                        set_item_data(
                            item, NOT_DEFINED_VALUE, FIELD_TYPE_STRING
                        )
                        font = item.font()
                        font.setItalic(True)
                        font.setBold(True)
                        item.setFont(font)

            # Update UI state
            self.resizeColumnsToContents()
            self.update_selection()
            self.update_colors()

        finally:

            # Reconnect signals
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def add_columns(self):
        """
        Add and update table columns based on database fields.

         This method synchronizes the table's columns with the current database
         schema by:
             - Adding columns for new database fields that don't exist in the
               table
             - Populating new columns with values from the database
             - Removing columns that no longer exist in the database
             - Applying appropriate formatting delegates based on field types
             - Maintaining column visibility settings

         The method temporarily disconnects item change signals during
         operation to prevent unwanted events, then reconnects them after
         completion.

         Note:
             - The TAG_FILENAME column is always placed first
             - Columns are sorted alphabetically (except TAG_FILENAME)
             - System tags (TAG_CHECKSUM, TAG_HISTORY) are excluded
             - Undefined values are displayed in italic bold text
        """
        # Import locally to prevent circular dependency
        from populse_mia.utils import set_item_data

        # Safely disconnect signals
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:

            with self.project.database.data() as database_data:
                # Prepare tag list: exclude system tags, sort, and place
                # filename first
                tags = set(database_data.get_field_names(COLLECTION_CURRENT))
                tags -= {TAG_CHECKSUM, TAG_HISTORY}
                tags = [TAG_FILENAME] + sorted(tags - {TAG_FILENAME})
                visible_tags = database_data.get_shown_tags()

                # Add missing columns
                for tag in tags:

                    if self.get_tag_column(tag) is not None:
                        continue

                    column_index = self.get_index_insertion(tag)
                    self.insertColumn(column_index)

                    # Set up column header
                    header_item = QTableWidgetItem(tag)
                    self.setHorizontalHeaderItem(column_index, header_item)
                    tag_attrib = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag
                    )

                    if tag_attrib:
                        from populse_mia.utils import type_name

                        field_type = tag_attrib["field_type"]
                        tooltip = (
                            f"Description: {tag_attrib['description']}\n"
                            f"Unit: {tag_attrib['unit']}\n"
                            f"Type: {type_name(field_type)}"
                        )
                        header_item.setToolTip(tooltip)
                        # Apply field-type specific delegate
                        delegate_map = {
                            FIELD_TYPE_FLOAT: NumberFormatDelegate,
                            FIELD_TYPE_DATETIME: DateTimeFormatDelegate,
                            FIELD_TYPE_DATE: DateFormatDelegate,
                            FIELD_TYPE_TIME: TimeFormatDelegate,
                        }

                        delegate_class = delegate_map.get(field_type)

                        if delegate_class:
                            self.setItemDelegateForColumn(
                                column_index, delegate_class(self)
                            )

                    # Set visibility
                    self.setColumnHidden(column_index, tag not in visible_tags)

                    # Populate column with data
                    for row in range(self.rowCount()):
                        item = QTableWidgetItem()
                        self.setItem(row, column_index, item)

                        scan = self.item(row, 0).text()
                        value = database_data.get_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            field=tag,
                        )

                        if value is not None:
                            set_item_data(
                                item, value, tag_attrib["field_type"]
                            )

                        else:
                            # Style undefined values distinctly
                            set_item_data(
                                item, NOT_DEFINED_VALUE, FIELD_TYPE_STRING
                            )
                            font = item.font()
                            font.setItalic(True)
                            font.setBold(True)
                            item.setFont(font)

                # Remove obsolete columns
                current_fields = set(
                    database_data.get_field_names(COLLECTION_CURRENT)
                )
                current_fields.add(TAG_FILENAME)

                # Collect columns to remove (iterate in reverse to avoid index
                # shifting)
                for column in reversed(range(self.columnCount())):
                    tag_name = self.horizontalHeaderItem(column).text()

                    if tag_name not in current_fields:
                        self.removeColumn(column)

            # Update UI
            self.resizeColumnsToContents()
            self.update_selection()
            self.update_colors()

        finally:

            # Reconnect signals
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def add_path(self):
        """
        Open a dialog to add documents to the current project.

        Creates and displays a PopUpAddPath dialog that allows users to select
        and add document paths to the project's data browser.
        """
        self.pop_up_add_path = PopUpAddPath(self.project, self.data_browser)
        self.pop_up_add_path.show()

    def add_rows(self, rows):
        """
        Insert rows into the table if they don't already exist.

        This method adds new scans to the table, populating each column with
        data from the database. It displays a progress dialog during the
        operation and handles special cases like the TAG_BRICKS column with
        custom widgets.

        :param rows: An iterable of scan identifiers to be added to the table.

        Note:
            - Duplicate scans (already present in the table) are automatically
              skipped
            - Sorting is temporarily disabled during the insertion process
            - The first column (name) is set as non-editable
            - TAG_BRICKS columns receive custom button widgets for interaction
        """

        # Import set_item_data here to prevent circular import issue
        from populse_mia.utils import set_item_data

        # Temporarily disable sorting and disconnect signals
        self.setSortingEnabled(False)
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:
            # Initialize and configure progress dialog
            cells_number = len(rows) * self.columnCount()
            self.progress = QProgressDialog(
                "Please wait while the paths are being added...",
                None,
                0,
                cells_number,
            )
            self.progress.setMinimumDuration(0)
            self.progress.setValue(0)
            self.progress.setMinimumWidth(350)  # For mac OS
            self.progress.setWindowTitle("Adding the paths")
            self.progress.setWindowFlags(
                Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint
            )
            self.progress.setModal(True)
            self.progress.setAttribute(Qt.WA_DeleteOnClose, True)
            self.progress.show()
            self.setVisible(False)
            # Add rows with database context
            idx = 0

            with self.project.database.data() as database_data:

                for scan in rows:

                    # Skip if scan already exists in table
                    if self.get_scan_row(scan) is not None:
                        continue

                    row_index = self.rowCount()
                    self.insertRow(row_index)

                    # Populate columns for the new row
                    for column_index in range(self.columnCount()):
                        idx += 1
                        self.progress.setValue(idx)
                        QApplication.processEvents()
                        tag = self.horizontalHeaderItem(column_index).text()
                        item = QTableWidgetItem()

                        if column_index == 0:
                            # First column: name tag (non-editable)
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            set_item_data(item, scan, FIELD_TYPE_STRING)

                        else:
                            # Retrieve value from database
                            cur_value = database_data.get_value(
                                collection_name=COLLECTION_CURRENT,
                                primary_key=scan,
                                field=tag,
                            )

                            if cur_value is not None:

                                if tag == TAG_BRICKS:
                                    # Tag bricks, display list with buttons
                                    widget = QWidget()
                                    widget.moveToThread(
                                        QApplication.instance().thread()
                                    )
                                    layout = QVBoxLayout()
                                    brick_uuid = cur_value[-1]
                                    brick_name = database_data.get_value(
                                        collection_name=COLLECTION_BRICK,
                                        primary_key=brick_uuid,
                                        field=BRICK_NAME,
                                    )
                                    brick_name_button = QPushButton(brick_name)
                                    brick_name_button.setFocusPolicy(
                                        Qt.NoFocus
                                    )
                                    brick_name_button.moveToThread(
                                        QApplication.instance().thread()
                                    )
                                    self.bricks[brick_name_button] = brick_uuid

                                    if TAG_FILENAME in scan:
                                        brick_name_button.clicked.connect(
                                            partial(
                                                self.show_brick_history,
                                                scan[TAG_FILENAME],
                                            )
                                        )

                                    layout.addWidget(brick_name_button)
                                    widget.setLayout(layout)
                                    self.setCellWidget(
                                        row_index, column_index, widget
                                    )

                                else:
                                    # Standard cell with database value
                                    field_type = (
                                        database_data.get_field_attributes(
                                            COLLECTION_CURRENT, tag
                                        )["field_type"]
                                    )
                                    set_item_data(item, cur_value, field_type)

                            else:
                                # Handle undefined values

                                if tag == TAG_BRICKS:
                                    set_item_data(item, "", FIELD_TYPE_STRING)
                                    # bricks not editable
                                    item.setFlags(
                                        item.flags() & ~Qt.ItemIsEditable
                                    )

                                else:
                                    set_item_data(
                                        item,
                                        NOT_DEFINED_VALUE,
                                        FIELD_TYPE_STRING,
                                    )
                                    font = item.font()
                                    font.setItalic(True)
                                    font.setBold(True)
                                    item.setFont(font)

                        self.setItem(row_index, column_index, item)

            # Restore table state
            self.resizeColumnsToContents()
            self.resizeRowsToContents()
            # Selection updated
            self.update_selection()
            self.update_colors()

        finally:

            # Reconnect signals
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)
            # Clean up
            self.progress.close()
            self.setVisible(True)

    def clear_cell(self):
        """
        Clear values from selected cells in the table.

        This method removes data from the currently selected cells in the
        database and updates the UI to reflect the cleared state. The
        operation is recorded in the project's undo history for potential
        reversal.

        The method performs the following actions for each selected cell:
            - Retrieves the current value from the database
            - Removes the value from the database
            - Updates the cell's visual appearance (italic + bold)
            - Records the change for undo/redo functionality

        Side Effects:
            - Modifies database values in COLLECTION_CURRENT
            - Updates table cell formatting
            - Appends operation to project.undos
            - Clears project.redos
        """
        # Import here to prevent circular dependency
        from populse_mia.utils import set_item_data

        # Track modifications for undo/redo functionality
        modified_values = []

        with self.project.database.data(write=True) as database_data:

            for cell_index in self.selectedIndexes():
                # Extract cell coordinates and identifiers
                row, col = cell_index.row(), cell_index.column()
                tag_name = self.horizontalHeaderItem(col).text()
                scan_name = self.item(row, 0).text()
                # Retrieve current value before clearing
                current_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan_name,
                    field=tag_name,
                )
                # Record change for history (scan, tag, old_value, new_value)
                modified_values.append(
                    [scan_name, tag_name, current_value, None]
                )
                # Clear value from database
                database_data.remove_value(
                    COLLECTION_CURRENT, scan_name, tag_name
                )
                # Update cell appearance to indicate cleared state
                cell_item = self.item(row, col)
                set_item_data(cell_item, NOT_DEFINED_VALUE, FIELD_TYPE_STRING)
                # Apply italic and bold formatting to cleared cells
                font = cell_item.font()
                font.setItalic(True)
                font.setBold(True)
                cell_item.setFont(font)

        # Register operation in undo history
        self.project.undos.append(["modified_values", modified_values])
        self.project.redos.clear()

    def context_menu_table(self, position):
        """
        Create and display the context menu for the table, and perform
        the corresponding action based on the user's selection.

        :param position (QPoint): The mouse cursor position relative to the
                                  widget.
        """

        def _confirm_action(text: str, callback: callable) -> None:
            """
            Display a warning message box with an OK/Cancel choice and connect
            the OK button to a callback function.

            The dialog shows a warning icon and the provided message. If the
            user confirms the action by clicking OK, the specified callback is
            invoked. Cancel simply closes the dialog without side effects.

            :param text (str): The warning message text to display in the
                                dialog.
            :param callback (callable): The function to execute if the user
                                        clicks OK.
            """
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning")
            msg.setText(text)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok_button = msg.button(QMessageBox.Ok)
            ok_button.clicked.connect(callback)
            msg.exec()

        def _do_add_document():
            """
            Safely add a new document to the table without triggering the
            ``itemChanged`` signal.

            This helper temporarily disconnects the ``itemChanged`` signal from
            ``on_cell_changed`` to prevent unwanted callbacks while adding a
            new document. After that, it calls ``add_path()`` to perform the
            actual addition.
            """
            self._safe_reconnect(self.itemChanged, self.on_cell_changed)
            self.add_path()
            self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        # -- Build menu actions ---------------------------------
        confirm_actions = {
            "Reset cell(s)": (
                "You are about to reset cells.",
                self.reset_cell,
            ),
            "Reset column(s)": (
                "You are about to reset columns.",
                self.reset_column,
            ),
            "Reset row(s)": ("You are about to reset rows.", self.reset_row),
            "Clear cell(s)": (
                "You are about to clear cells.",
                self.clear_cell,
            ),
            "Remove document(s)": (
                "You are about to remove a scan from the project.\n\n"
                "Be careful! This action is definitive and cannot be undone "
                "(the data will be completely deleted).",
                self.remove_scan,
            ),
        }
        direct_actions = {
            "Add document": _do_add_document,
            "Sort column": lambda: self.sort_column(0),
            "Sort column (descending)": lambda: self.sort_column(1),
            "Visualized tags": self.visualized_tags_pop_up,
            "Select column(s)": self.select_all_columns,
            "Multiple sort": self.multiple_sort_pop_up,
            "Send documents to the Pipeline Manager": (
                self.data_browser.send_documents_to_pipeline
            ),
            "Tries to read a file": self.display_file,
        }
        # -- Execute --------------------------------------------
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        try:
            menu = QMenu(self)
            action_objects = {}

            for label, (text, callback) in confirm_actions.items():
                action = menu.addAction(label)
                action_objects[action] = (
                    lambda t=text, cb=callback: _confirm_action(t, cb)
                )

            for label, callback in direct_actions.items():
                action = menu.addAction(label)
                action_objects[action] = callback

            selected_action = menu.exec_(self.mapToGlobal(position))

            if selected_action in action_objects:
                action_objects[selected_action]()

            self.update_colors()

        finally:
            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def delete_from_brick(self, brick_id):
        """
        Delete a brick and its associated documents from the database.

        This method cleans up the database when a pipeline (composed of
        multiple bricks) is initialized but not executed before another
        pipeline is started or the software is closed. It removes the brick
        and any orphaned output documents that are not used as inputs
        elsewhere.

        :param brick_id (str): The unique identifier of the brick to be
                               deleted.
        """

        with self.project.database.data(write=True) as database_data:
            # Fetch the brick document
            brick_doc = database_data.get_document(
                collection_name=COLLECTION_BRICK, primary_keys=brick_id
            )

            if not brick_doc:
                return

            # Extract all input and output document IDs
            def extract_document_ids(data: dict) -> set[str]:
                """
                Extracts all string values from a nested dictionary structure.

                This function traverses the values of the input dictionary.
                If a value is:
                    - a string: it is added to the resulting set of
                                document IDs.
                    - a list: its elements are recursively traversed and
                              processed. Non-string, non-list values are
                              ignored.

                :param data (dict): Dictionary that may contain nested strings
                                    or lists as values.

                :returns (set[str]): A set containing all unique string values
                                     found within the dictionary.
                """
                document_ids = set()
                stack = list(data.values())

                while stack:
                    value = stack.pop(0)

                    if isinstance(value, str):
                        document_ids.add(value)

                    elif isinstance(value, list):
                        stack.extend(value)

                return document_ids

            inputs = extract_document_ids(brick_doc[0][BRICK_INPUTS])
            outputs = extract_document_ids(brick_doc[0][BRICK_OUTPUTS])

            # Remove orphaned outputs
            for output in outputs:

                if not output or output in inputs:
                    continue

                relative_path = os.path.relpath(output, self.project.folder)
                scan_object = database_data.get_document(
                    collection_name=COLLECTION_CURRENT,
                    primary_keys=relative_path,
                    fields=[TAG_FILENAME, TAG_BRICKS],
                )

                if not scan_object:
                    continue

                bricks = scan_object[0][TAG_BRICKS]

                if bricks and brick_id in bricks:
                    bricks = [brick for brick in bricks if brick != brick_id]

                if not bricks:
                    row = self.get_scan_row(relative_path)

                    if row is not None:
                        self.removeRow(row)
                        database_data.remove_document(
                            COLLECTION_CURRENT, relative_path
                        )

                        try:
                            database_data.remove_document(
                                COLLECTION_INITIAL, relative_path
                            )

                        except KeyError:
                            pass

                else:
                    database_data.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=relative_path,
                        values_dict={TAG_BRICKS: bricks},
                    )

            # Remove the brick itself
            database_data.remove_document(COLLECTION_BRICK, brick_id)

        self.resizeColumnsToContents()

    def display_file(self):
        """
        Open the selected file(s) in the user's default application.

        Iterates over all selected items in the view, resolves their absolute
        paths, and opens each file using the platform's default application.

        Supported platforms: Linux, macOS, and Windows.
        """

        for index in self.selectedIndexes():
            scan_path = self.item(index.row(), 0).text()
            full_path = os.path.abspath(
                os.path.join(self.project.folder, scan_path)
            )

            # Platform-specific file opening logic
            if platform.system() == "Linux":
                subprocess.Popen(
                    ["xdg-open", full_path], start_new_session=True
                )

            # FIXME: test the following part of the code for windows and macos!
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", full_path])

            elif platform.system() == "Windows":
                subprocess.Popen(["start", full_path], shell=True)

            else:
                raise NotImplementedError(
                    f"Unsupported platform: {platform.system()}"
                )

    def display_unreset_values(self):
        """
        Displays a warning dialog listing values that cannot be reset.

        This method shows a QMessageBox warning when certain values (such as
        user tags, FileName, or undefined cells) cannot be reset because they
        lack a raw value. The dialog includes a descriptive message and an OK
        button for dismissal.
        """
        warning_dialog = QMessageBox()
        warning_dialog.setIcon(QMessageBox.Warning)
        warning_dialog.setWindowTitle("Reset Warning")
        warning_dialog.setText("Some values cannot be reset.")
        warning_dialog.setInformativeText(
            "Some values were not reset because they lack a raw value.\nIt is "
            "the case for the user tags, FileName and Undefined cells."
        )
        warning_dialog.setStandardButtons(QMessageBox.Ok)
        warning_dialog.buttonClicked.connect(warning_dialog.close)
        warning_dialog.exec_()

    def edit_table_data_values(self):
        """
        Edit and update selected cell values in the DataBrowser table.

        This method handles the selection of cells, validation of list
        lengths, and updating of values in both the table and the database.
        It supports list-type fields and ensures data consistency across
        selections.

        Steps:
            1. Collects selected cells and their metadata
               (coordinates, types, lengths, etc.).
            2. Validates list lengths for compatibility.
            3. Opens a dialog for value modification if valid.
            4. Updates the table and database, and records changes for
               undo/redo history.

        Note:
            - Exits early if the selected tag is 'TAG_BRICKS' or if the field
              type is not a list.
            - Disconnects and reconnects the `itemChanged` signal to prevent
              recursive updates.
        """

        # import set_item_data only here to prevent circular import issue
        from populse_mia.utils import set_item_data

        self.setMouseTracking(False)
        self.coordinates = []  # Coordinates of selected cells
        self.old_database_values = []  # Old database values
        self.old_table_values = []  # Old table values
        self.types = set()  # Unique types
        lengths = set()  # Unique lengths
        self.scans_list = []  # List of table scans
        self.tags = []  # List of table tags

        try:

            with self.project.database.data() as database_data:

                for item in self.selectedItems():
                    column, row = item.column(), item.row()
                    self.coordinates.append([row, column])
                    tag_name = self.horizontalHeaderItem(column).text()
                    tag_attrib = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag_name
                    )
                    tag_type = tag_attrib["field_type"]
                    scan_name = self.item(row, 0).text()

                    if tag_name == TAG_BRICKS:
                        self.setMouseTracking(True)
                        return

                    # Scan, tag, type added
                    self.tags.append(tag_name)
                    self.scans_list.append(scan_name)
                    self.types.add(tag_type)

                    if get_origin(tag_type) is not list:
                        self.setMouseTracking(True)
                        return

                    # Fetch and store old values
                    database_value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan_name,
                        field=tag_name,
                    )
                    self.old_database_values.append(database_value)
                    table_value = item.data(Qt.EditRole)

                    try:
                        table_value = ast.literal_eval(table_value)

                    except (ValueError, SyntaxError):
                        table_value = None

                    self.old_table_values.append(table_value)

                    # Store length if valid
                    try:
                        lengths.add(len(database_value))

                    except TypeError:
                        lengths.add(None)

            # Error if lists of different lengths
            lengths = [x for x in lengths if x is not None]

            if not lengths:
                lengths = [1]

            if len(lengths) > 1:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Incompatible list lengths")
                msg.setInformativeText("The lists can't have several lengths")
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                self.setMouseTracking(True)
                return

            if not self.old_table_values:
                self.setMouseTracking(True)
                return

            # Prepare initial value for dialog
            value = (
                [0] * lengths[0]
                if len(self.coordinates) > 1
                else self.old_table_values[0]
            )

            if value is None:
                value = [0]

            # Open dialog for value modification
            self.popup = ModifyTable(
                self.project,
                value,
                list(self.types),
                self.scans_list,
                self.tags,
            )

            if self.popup.exec_():
                self.popup.deleteLater()
                del self.popup

            # Record changes for history
            history_maker = ["modified_values", []]
            self._safe_disconnect(self.itemChanged, self.on_cell_changed)

            with self.project.database.data() as database_data:

                for i, (scan, tag) in enumerate(
                    zip(self.scans_list, self.tags)
                ):
                    new_item = QTableWidgetItem()
                    old_value = self.old_database_values[i]
                    new_cur_value = (
                        database_data.get_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            field=tag,
                        )
                        or NOT_DEFINED_VALUE
                    )
                    history_maker[1].append(
                        [scan, tag, old_value, new_cur_value]
                    )
                    set_item_data(
                        new_item,
                        new_cur_value,
                        database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag
                        )["field_type"],
                    )
                    self.setItem(
                        self.coordinates[i][0],
                        self.coordinates[i][1],
                        new_item,
                    )

            # For history
            self.project.undos.append(history_maker)
            self.project.redos.clear()
            self.update_colors()
            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

        except Exception as e:
            logger.warning(e)

        finally:
            self.setMouseTracking(True)
            self.resizeColumnsToContents()
            self.resizeRowsToContents()

    def fill_cells_update_table(self):
        """
        Initialize and populate table cells with scan data from the database.

        This method performs the following operations:
            1. Creates a progress dialog to track cell population
            2. Retrieves scan documents matching scans_to_visualize from the
               database
            3. Populates each cell with appropriate data based on column type
            4. Handles special cases (name column, bricks column)
            5. Applies saved sorting preferences
            6. Resizes rows and columns to fit content

        Special column handling:
            - Column 0 (name): Read-only, always displays as string
            - Bricks column: Displays clickable buttons for brick history
            - Other columns: Editable, type-specific formatting

        Notes:
            - Displays a modal progress dialog during population
            - Temporarily hides the table during updates for performance
            - Connects cell change signals after population completes
        """
        # Lazy import to prevent circular dependency
        from populse_mia.utils import set_item_data

        # Initialize progress dialog
        cells_count = len(self.scans_to_visualize) * len(
            self.horizontalHeader()
        )
        self.progress = QProgressDialog(
            "Please wait while the cells are being filled...",
            None,
            0,
            cells_count,
        )
        self.progress.setMinimumDuration(0)
        self.progress.setValue(0)
        self.progress.setMinimumWidth(350)  # For mac OS
        self.progress.setWindowTitle("Filling the cells")
        self.progress.setWindowFlags(
            Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        )
        self.progress.setModal(True)
        self.progress.setAttribute(Qt.WA_DeleteOnClose, True)
        self.progress.show()
        self.setVisible(False)
        cell_index = 0
        # Disconnect signals
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:

            with self.project.database.data() as database_data:
                primary_key = database_data.get_primary_key_name(
                    COLLECTION_CURRENT
                )

                # Fetch scans from database
                if self.scans_to_visualize:
                    escaped_scans = [
                        scan.replace("\\", "\\\\").replace('"', '\\"')
                        for scan in self.scans_to_visualize
                    ]
                    joined_scans = ", ".join(
                        f'"{scan}"' for scan in escaped_scans
                    )
                    query = f"{primary_key} IN [{joined_scans}]"
                    scans = database_data.filter_documents(
                        COLLECTION_CURRENT, query
                    )

                else:
                    scans = []

                # Extract column tags and their types
                tags = [
                    self.horizontalHeaderItem(col).text()
                    for col in range(len(self.horizontalHeader()))
                ]
                field_names = database_data.get_field_names(COLLECTION_CURRENT)
                tag_type_map = {
                    field_name: (
                        database_data.get_field_attributes(
                            COLLECTION_CURRENT, field_name
                        )
                        or {}
                    ).get("field_type", str)
                    for field_name in field_names
                }
                tag_types = [tag_type_map[tag] for tag in tags]

                # Populate table cells
                for row, scan in enumerate(scans):

                    for column, tag in enumerate(tags):
                        cell_index += 1
                        self.progress.setValue(cell_index)
                        QApplication.processEvents()
                        item = QTableWidgetItem()

                        if column == 0:
                            # Name column: read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            set_item_data(item, scan[tag], FIELD_TYPE_STRING)

                        else:
                            current_value = scan[tag]
                            col_type = tag_types[column]

                            if current_value:

                                if tag != TAG_BRICKS:
                                    set_item_data(
                                        item, current_value, col_type
                                    )

                                else:
                                    # Bricks column: create widget with button
                                    widget = QWidget()
                                    widget.moveToThread(
                                        QApplication.instance().thread()
                                    )
                                    layout = QVBoxLayout()

                                    brick_uuid = current_value[-1]
                                    brick_name = database_data.get_value(
                                        collection_name=COLLECTION_BRICK,
                                        primary_key=brick_uuid,
                                        field=BRICK_NAME,
                                    )

                                    if brick_name:
                                        button = QPushButton(brick_name)
                                        button.setFocusPolicy(Qt.NoFocus)
                                        button.moveToThread(
                                            QApplication.instance().thread()
                                        )
                                        self.bricks[button] = brick_uuid
                                        button.clicked.connect(
                                            partial(
                                                self.show_brick_history,
                                                scan[TAG_FILENAME],
                                            )
                                        )
                                        layout.addWidget(button)

                                    widget.setLayout(layout)
                                    self.setCellWidget(row, column, widget)

                            else:

                                # Handle undefined values
                                if tag != TAG_BRICKS:
                                    set_item_data(
                                        item,
                                        NOT_DEFINED_VALUE,
                                        FIELD_TYPE_STRING,
                                    )
                                    font = item.font()
                                    font.setItalic(True)
                                    font.setBold(True)
                                    item.setFont(font)

                                else:
                                    # No brick: clear widget and mark
                                    # non-editable
                                    self.setCellWidget(row, column, None)
                                    set_item_data(item, "", FIELD_TYPE_STRING)
                                    item.setFlags(
                                        item.flags() & ~Qt.ItemIsEditable
                                    )

                        self.setItem(row, column, item)

            # Apply saved sorting preferences
            # self.setSortingEnabled(True)
            self.setSortingEnabled(False)
            tag_to_sort = self.project.getSortedTag()
            column_to_sort = self.get_tag_column(tag_to_sort)
            sort_order = self.project.getSortOrder()

            if column_to_sort is not None:
                self.horizontalHeader().setSortIndicator(
                    column_to_sort, sort_order
                )

            else:
                self.horizontalHeader().setSortIndicator(0, 0)

            self.resizeRowsToContents()
            self.resizeColumnsToContents()

        finally:
            self.progress.close()
            self.setVisible(True)

            # Reconnect signals
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def fill_headers(self, take_tags_to_update=False):
        """
        Initialize and populate table headers with field metadata.

        Sets up table columns based on database fields, configuring each with:
            - Appropriate tooltips showing description, unit, and type
            - Specialized delegates for numeric and temporal data types
            - Visibility based on display settings or field attributes

        :param take_tags_to_update: If True, use tags_to_display for
                                    visibility. If False, use field visibility
                                    attributes. Defaults to False.
        """

        # Get field names and prepare sorted list with FileName first
        with self.project.database.data() as database_data:
            tags = database_data.get_field_names(COLLECTION_CURRENT)

        # Remove internal fields and sort, keeping TAG_FILENAME at position 0
        for internal_tag in (TAG_CHECKSUM, TAG_FILENAME, TAG_HISTORY):
            tags.remove(internal_tag)

        tags = [TAG_FILENAME] + sorted(tags)
        self.setColumnCount(len(tags))
        # Mapping of field types to their corresponding delegates
        DELEGATE_MAP = {
            FIELD_TYPE_FLOAT: NumberFormatDelegate,
            FIELD_TYPE_DATETIME: DateTimeFormatDelegate,
            FIELD_TYPE_DATE: DateFormatDelegate,
            FIELD_TYPE_TIME: TimeFormatDelegate,
        }

        with self.project.database.data() as database_data:

            for column, tag_name in enumerate(tags):
                item = QTableWidgetItem(tag_name)
                tag_attrib = database_data.get_field_attributes(
                    COLLECTION_CURRENT, tag_name
                )

                if tag_attrib:
                    # Set tooltip with field metadata
                    from populse_mia.utils import type_name

                    item.setToolTip(
                        f"Description: {tag_attrib['description']}\n"
                        f"Unit: {tag_attrib['unit']}\n"
                        f"Type: {type_name(tag_attrib['field_type'])}"
                    )
                    # Apply specialized delegate based on field type
                    delegate_class = DELEGATE_MAP.get(tag_attrib["field_type"])

                    if delegate_class:
                        self.setItemDelegateForColumn(
                            column, delegate_class(self)
                        )

                    # Determine column visibility
                    is_visible = (
                        tag_name in self.tags_to_display
                        if take_tags_to_update
                        else tag_attrib["visibility"]
                    )
                    self.setColumnHidden(column, not is_visible)

                self.setHorizontalHeaderItem(column, item)

    def get_current_filter(self):
        """
        Get the current data browser selection.

        Returns the list of selected scan paths if a selection is active,
        otherwise returns all visible scan paths in the data browser.

        :return (list): List of scan paths from either the current selection
                        or all visible scans in the data browser.
        """

        if self.activate_selection and self.scans:
            return [scan[0] for scan in self.scans]

        return self.scans_to_visualize

    def get_index_insertion(self, to_insert):
        """
        Find the insertion index for a new column to maintain alphabetical
        order.

        Uses binary search to efficiently locate the correct position for
        inserting a column header while preserving the existing alphabetical
        sort order.

        :param to_insert (str): The column header text to insert.

        :return (int): The column index where the new column should be
                       inserted. Returns columnCount() if it should be
                       appended at the end.

        Note: Assumes that column 0 is reserved (TAG_FILENAME must always be
              the first tag on the left) and start the search from column 1.
        """
        # Extract column headers starting from index 1
        headers = [
            self.horizontalHeaderItem(col).text()
            for col in range(1, self.columnCount())
        ]
        # Find insertion point using binary search
        insertion_index = bisect.bisect_left(headers, to_insert)

        # Adjust for skipped column 0
        return insertion_index + 1

    def get_scan_row(self, scan):
        """
        Find the row index for a given scan filename.

        :param scan: The scan filename to search for.

        :return(int): The zero-based row index if the scan is found, None
                      otherwise.

        """

        return next(
            (
                row
                for row in range(self.rowCount())
                if self.item(row, 0).text() == scan
            ),
            None,
        )

    def get_tag_column(self, tag):
        """
        Find the column index for a given tag name.

        Searches through the table's horizontal headers to locate the column
        corresponding to the specified tag.

        :param tag (str): The name of the tag to search for.

        :return (int): The zero-based column index if the tag is found,
                       None otherwise.
        """

        for column in range(self.columnCount()):

            if (
                item := self.horizontalHeaderItem(column)
            ) and item.text() == tag:
                return column

        return None

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release event and update table data.

        This method is called when a mouse button is released over the widget.
        It delegates to the parent class handler and then updates the table
        data values.

        :param event (QMouseEvent): The mouse event containing information
                                    about the button released, position, and
                                    modifiers.
        """
        super().mouseReleaseEvent(event)
        self.edit_table_data_values()

    def multiple_sort_infos(self, list_tags, order):
        """
        Sort table rows by multiple tag values.

        Sorts the visualized scans based on the values of specified tags, then
        reorganizes the table rows to reflect the new order. Handles both
        regular items and special brick widgets during the reordering.

        :param list_tags(list): List of tag names to sort by (primary to
                                secondary).
        :param order (str): Sort direction, either "Ascending" or "Descending".

        Note:
            Temporarily disables item change signals during sorting to prevent
            triggering update handlers. The sort is stable and preserves the
            relative order of items with equal sort keys.
        """
        # Import locally to avoid circular dependency
        from populse_mia.utils import set_item_data

        def _clear_cell(row, column, item):
            """
            Clears the specified cell and sets an optional non-editable item.

            :param row (int): The row index of the cell to clear.
            :param column (int): The column index of the cell to clear.
            :param item (QTableWidgetItem) The item to set in the cleared cell.
                                           If None, the cell remains empty.
            """
            self.setCellWidget(row, column, None)

            if item:
                set_item_data(item, "", FIELD_TYPE_STRING)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row, column, item)

        def _create_brick_widget(
            row,
            column,
            scan,
            database_data,
            old_widget,
            item,
            clicked_scan=None,
        ):
            """
            Create and set a brick widget for the specified table cell.

            The brick name is fetched from the database and displayed as a
            clickable button. Clicking the button shows the brick's history.
            Existing brick references are updated if necessary.

            :param row (int): Row index of the cell to fill.
            :param column (int): Column index of the cell to fill.
            :param scan (str): Primary key of the scan linked to the brick.
            :param db (Database): Active database connection.
            :param old_widget (QWidget): Existing widget previously in the
                                         same cell (if any).
            :param item (QTableWidgetItem): The table item for this cell.
            :param clicked_scan (str): The scan ID to use when connecting the
                                       brick button’s clicked signal. If None,
                                       defaults to `scan`.
            """
            app_thread = QApplication.instance().thread()
            widget = QWidget()
            widget.moveToThread(app_thread)
            layout = QVBoxLayout(widget)
            cur_val = database_data.get_value(
                collection_name=COLLECTION_CURRENT,
                primary_key=scan,
                field=TAG_BRICKS,
            )

            if not cur_val:
                _clear_cell(row, column, item)
                return

            brick_uuid = cur_val[0]
            brick_name = database_data.get_value(
                collection_name=COLLECTION_BRICK,
                primary_key=brick_uuid,
                field=BRICK_NAME,
            )

            if not brick_name:
                _clear_cell(row, column, item)
                return

            brick_name_button = QPushButton(brick_name)
            brick_name_button.setFocusPolicy(Qt.NoFocus)
            brick_name_button.moveToThread(app_thread)
            # Replace the old brick reference if needed
            old_button = (
                old_widget.findChild(QPushButton) if old_widget else None
            )

            for key, value in list(self.bricks.items()):

                if value == brick_uuid and key == old_button:
                    del self.bricks[key]
                    self.bricks[brick_name_button] = brick_uuid
                    break

            # Use the appropriate scan for the clicked signal
            target_scan = clicked_scan or scan
            brick_name_button.clicked.connect(
                partial(self.show_brick_history, target_scan)
            )
            layout.addWidget(brick_name_button)
            self.setCellWidget(row, column, widget)
            self.setItem(row, column, item)

        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        try:

            with self.project.database.data() as db:
                # Fetch tag field attributes
                tag_attributes = [
                    db.get_field_attributes(COLLECTION_CURRENT, tag_name)
                    for tag_name in list_tags
                ]
                # Build sort keys for each scan
                sort_keys = []

                for scan in self.scans_to_visualize:
                    key = []

                    for tag in tag_attributes:
                        field_name = tag["index"].split("|")[1]
                        value = db.get_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            field=field_name,
                        )
                        key.append(
                            str(value)
                            if value is not None
                            else NOT_DEFINED_VALUE
                        )

                    sort_keys.append(key)

                # Sort scans by the computed keys
                reverse = order == "Descending"
                self.scans_to_visualize = [
                    scan
                    for _, scan in sorted(
                        zip(sort_keys, self.scans_to_visualize),
                        reverse=reverse,
                    )
                ]
                # Reorder table rows to match sorted scans
                self.setSortingEnabled(False)

                for row, scan in enumerate(self.scans_to_visualize):
                    old_row = self.get_scan_row(scan)

                    if old_row == row:
                        continue

                    # Swap all columns between current_row and target_row
                    for column in range(self.columnCount()):
                        header_text = self.horizontalHeaderItem(column).text()

                        if header_text == TAG_BRICKS:
                            # Handle brick widget cells
                            widget_to_move = self.cellWidget(old_row, column)
                            item_to_move = self.takeItem(old_row, column)
                            widget_wrong_row = self.cellWidget(row, column)
                            item_wrong_row = self.takeItem(row, column)

                            # Move widget_to_move to row
                            if widget_to_move:
                                _create_brick_widget(
                                    row,
                                    column,
                                    scan,
                                    db,
                                    widget_to_move,
                                    item_to_move,
                                )

                            else:
                                _clear_cell(row, column, item_to_move)

                            # widget_wrong_row to old_row
                            if widget_wrong_row:
                                old_scan = self.item(old_row, 0).text()
                                _create_brick_widget(
                                    old_row,
                                    column,
                                    old_scan,
                                    db,
                                    widget_wrong_row,
                                    item_wrong_row,
                                    clicked_scan=old_scan,
                                )

                            else:
                                _clear_cell(old_row, column, item_wrong_row)

                        else:
                            item_to_move = self.takeItem(old_row, column)
                            item_wrong_row = self.takeItem(row, column)
                            self.setItem(row, column, item_to_move)
                            self.setItem(old_row, column, item_wrong_row)

        finally:
            # Re-enable sorting and reconnect signals
            self.horizontalHeader().setSortIndicator(-1, 0)
            # self.setSortingEnabled(True)
            self.setSortingEnabled(False)
            self._safe_reconnect(self.itemChanged, self.on_cell_changed)
            self.resizeRowsToContents()
            self.resizeColumnsToContents()

    def multiple_sort_pop_up(self):
        """
        Display the multiple sort configuration dialog.

        Creates and shows a modal dialog that allows users to configure
        multiple sorting criteria for the current project data.

        Note:
            The dialog instance is stored in `self.pop_up`.
        """
        self.pop_up = PopUpMultipleSort(self.project, self)
        self.pop_up.show()

    def on_cell_changed(self, item_origin):
        """
        Update cell values and appearance when edited by the user.

        This method handles both single and multi-cell selection, validating
        type compatibility across all selected cells before applying changes.
        It performs the following operations:
            1. Validates that all selected cells have compatible types
            2. Verifies the new value matches the expected type(s)
            3. Updates the database with validated values
            4. Maintains undo/redo history for all modifications
            5. Refreshes cell colors and formatting

        Special handling:
        - PatientName: Removes spaces (used for subfolder naming in
                       calculations)
        - TAG_BRICKS/TAG_FILENAME: Read-only fields, changes are rejected
        - List types: Prevents mixed type selections but allows homogeneous
                      lists

        :param item_origin: QTableWidgetItem from which the edit originated

        Side effects:
            - Modifies database values for selected cells
            - Updates cell appearance (colors, fonts)
            - Adds entry to project undo history
            - Clears redo history
            - Resizes columns to fit content
        """
        # Import locally to prevent circular dependency
        from populse_mia.utils import (
            check_value_type,
            set_item_data,
            table_to_database,
        )

        def _show_error_and_revert(
            title, message, selected_items, database_data
        ):
            """
            Display error dialog and revert selected cells to their original
            values.

            :param title: Dialog title text
            :param message: Dialog message text
            :param selected_items: List of QTableWidgetItem objects to revert
            :param database_data: Database context for retrieving original
                                  values
            """
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(title)
            msg.setInformativeText(message)
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()

            # Revert all selected cells to their database values
            for item in selected_items:
                row = item.row()
                col = item.column()
                scan_path = self.item(row, 0).text()
                tag_name = self.horizontalHeaderItem(col).text()
                old_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan_path,
                    field=tag_name,
                )
                field_type = database_data.get_field_attributes(
                    COLLECTION_CURRENT, tag_name
                )["field_type"]
                set_item_data(
                    item,
                    old_value if old_value is not None else "*Not Defined*",
                    field_type,
                )

        # Temporarily disconnect to prevent recursive calls during updates
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:

            new_value = item_origin.data(Qt.EditRole)
            selected_items = self.selectedItems()

            with self.project.database.data(write=True) as database_data:
                # Collect unique field types from all selected cells
                cells_types = []

                # For each item selected, we check the validity of the types
                for item in selected_items:
                    col = item.column()
                    tag_name = self.horizontalHeaderItem(col).text()

                    # Remove spaces from PatientName (used for subfolder
                    # naming)
                    if tag_name == "PatientName":
                        new_value = new_value.replace(" ", "")

                    # Read-only fields - reject changes immediately
                    if tag_name in (TAG_BRICKS, TAG_FILENAME):
                        self.update_colors()
                        return

                    tag_attrib = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag_name
                    )
                    tag_type = tag_attrib["field_type"]

                    if tag_type not in cells_types:
                        cells_types.append(tag_type)

                # Define all list types known in data_manager
                list_types = {
                    FIELD_TYPE_LIST_DATE,
                    FIELD_TYPE_LIST_DATETIME,
                    FIELD_TYPE_LIST_TIME,
                    FIELD_TYPE_LIST_INTEGER,
                    FIELD_TYPE_LIST_STRING,
                    FIELD_TYPE_LIST_FLOAT,
                    FIELD_TYPE_LIST_BOOLEAN,
                    FIELD_TYPE_LIST_JSON,
                }
                has_list_type = bool(set(cells_types) & list_types)

                # Error: Mixed types including list types
                if has_list_type and len(cells_types) > 1:
                    _show_error_and_revert(
                        "Incompatible types",
                        f"The following types in the selection are not "
                        f"compatible: {cells_types}",
                        selected_items,
                        database_data,
                    )
                    return

                # Skip validation for homogeneous list types
                if has_list_type:
                    return

                # Validate value compatibility with all selected cell types
                type_problem = next(
                    (
                        cell_type
                        for cell_type in cells_types
                        if not check_value_type(new_value, cell_type)
                    ),
                    None,
                )

                if type_problem:
                    _show_error_and_revert(
                        "Invalid value",
                        f"The value {new_value} is invalid with the "
                        f"type {type_problem}",
                        selected_items,
                        database_data,
                    )
                    return

                # All validations passed - update database and cells
                modified_values = []

                for item in selected_items:
                    row = item.row()
                    col = item.column()
                    scan_path = self.item(row, 0).text()
                    tag_name = self.horizontalHeaderItem(col).text()

                    # Skip filename tag (read-only)
                    if tag_name == TAG_FILENAME:
                        continue

                    field_type = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag_name
                    )["field_type"]
                    database_value = table_to_database(new_value, field_type)
                    old_value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan_path,
                        field=tag_name,
                    )
                    # Record change for history (whether updating or adding)
                    modified_values.append(
                        [scan_path, tag_name, old_value, database_value]
                    )
                    # Update database
                    database_data.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan_path,
                        values_dict={tag_name: database_value},
                    )

                    # Reset font if this was a previously undefined cell
                    if old_value is None:
                        font = item.font()
                        font.setItalic(False)
                        font.setBold(False)
                        item.setFont(font)

                    # Update cell display
                    set_item_data(item, new_value, field_type)

                # Record in undo history
                if modified_values:
                    self.project.undos.append(
                        ["modified_values", modified_values]
                    )
                    self.project.redos.clear()
                    self.resizeColumnsToContents()

        finally:

            # Reconnect signals
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self.update_colors()
            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def remove_scan(self):
        """
        Remove selected scans from the database and file system.

        This method handles the removal of scan documents from both the
        current and initial collections in the project database. It performs
        the following:
            - Prompts user for confirmation if scans are in the active scan
              list
            - Preserves modification history for removed scan values
            - Deletes associated files (.nii and .json) from the file system
            - Updates the UI table to reflect removals

        The removal process can be cancelled by the user when prompted. If
        multiple scans are selected, the user can choose to apply their
        decision to all remaining scans.

        Side effects:
            - Modifies database by removing documents from COLLECTION_CURRENT
              and COLLECTION_INITIAL
            - Deletes scan files from the project folder
            - Updates UI table rows and marks project as having unsaved
              modifications
        """
        # Safely disconnect signals
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        try:
            selected_points = self.selectedIndexes()

            if not selected_points:
                return

            scans_removed = []
            values_removed = []
            scan_list = (
                self.data_browser.main_window.pipeline_manager.scan_list
            )
            # Track user preferences across multiple deletions
            suppress_dialog = False
            user_cancelled = False

            with self.project.database.data(write=True) as database_data:

                for point in selected_points:
                    scan_path = self.item(point.row(), 0).text()
                    scan_object = database_data.get_document(
                        collection_name=COLLECTION_CURRENT,
                        primary_keys=scan_path,
                    )

                    if not scan_object:
                        continue

                    # Confirm removal if scan is in active pipeline
                    is_in_pipeline = (
                        scan_path in scan_list and self.data_browser.data_sent
                    )

                    if is_in_pipeline:

                        if not suppress_dialog:
                            popup = PopUpRemoveScan(
                                scan_path, len(selected_points)
                            )
                            popup.exec()
                            user_cancelled = popup.stop
                            suppress_dialog = popup.repeat

                        if user_cancelled:
                            continue

                    # Preserve modification history for all fields except
                    # filename
                    for tag in database_data.get_field_names(
                        COLLECTION_CURRENT
                    ):

                        if tag == TAG_FILENAME:
                            continue

                        current_value = database_data.get_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan_path,
                            field=tag,
                        )
                        initial_value = database_data.get_value(
                            collection_name=COLLECTION_INITIAL,
                            primary_key=scan_path,
                            field=tag,
                        )

                        # Only archive if at least one value exists
                        if (
                            current_value is not None
                            or initial_value is not None
                        ):
                            values_removed.append(
                                [
                                    scan_path,
                                    tag,
                                    current_value,
                                    initial_value,
                                ]
                            )

                    # Remove from database collections
                    self.scans_to_visualize.remove(scan_path)
                    database_data.remove_document(
                        COLLECTION_CURRENT, scan_path
                    )
                    database_data.remove_document(
                        COLLECTION_INITIAL, scan_path
                    )
                    # Remove associated files from file system
                    full_scan_path = os.path.join(
                        self.project.folder, scan_path
                    )
                    files_to_remove = [full_scan_path]

                    # Include associated JSON for NIfTI files
                    if scan_path.endswith(".nii"):
                        files_to_remove.append(full_scan_path[:-4] + ".json")

                    for file_path in files_to_remove:

                        if os.path.isfile(file_path):
                            os.remove(file_path)

                    scans_removed.append(scan_object[0])

            # Update UI table
            for scan in scans_removed:
                scan_name = scan[TAG_FILENAME]
                self.removeRow(self.get_scan_row(scan_name))

            if scans_removed:
                self.project.unsavedModifications = True
                self.resizeColumnsToContents()

        finally:
            # Safely disconnect signals
            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def reset_cell(self):
        """
        Reset selected cells to their original values from the initial
        collection.

        This method restores the values of all selected cells to their
        original state by retrieving values from COLLECTION_INITIAL and
        updating COLLECTION_CURRENT. If any cells lack initial values
        (e.g., user-created tags), a warning is displayed. The operation is
        recorded in the project history for undo/redo functionality.

        Side effects:
            - Updates database values in COLLECTION_CURRENT
            - Updates table cell display values
            - Appends operation to project.undos
            - Clears project.redos
            - May display a warning dialog for unreset values
            - Resizes table columns to fit content
        """
        # Import set_item_data locally to prevent circular import
        from populse_mia.utils import set_item_data

        points = self.selectedIndexes()

        if not points:
            return

        modified_values = []
        # To know if some values do not have raw values (user tags)
        has_unreset_values = False

        with self.project.database.data(write=True) as database_data:

            for point in points:
                row, col = point.row(), point.column()
                tag_name = self.horizontalHeaderItem(col).text()
                # We get the FileName of the scan from the first row
                scan_name = self.item(row, 0).text()

                current_value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan_name,
                    field=tag_name,
                )

                initial_value = database_data.get_value(
                    collection_name=COLLECTION_INITIAL,
                    primary_key=scan_name,
                    field=tag_name,
                )

                if initial_value is None:
                    has_unreset_values = True
                    continue

                try:
                    database_data.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan_name,
                        values_dict={tag_name: initial_value},
                    )

                    field_type = database_data.get_field_attributes(
                        COLLECTION_CURRENT, tag_name
                    )["field_type"]

                    set_item_data(
                        self.item(row, col), initial_value, field_type
                    )

                    modified_values.append(
                        [scan_name, tag_name, current_value, initial_value]
                    )

                except ValueError:
                    has_unreset_values = True

        # Record operation in history for undo/redo
        if modified_values:
            self.project.undos.append(["modified_values", modified_values])
            self.project.redos.clear()

        # Warning message if unreset values
        if has_unreset_values:
            self.display_unreset_values()

        self.resizeColumnsToContents()

    def reset_column(self):
        """
        Reset selected columns to their original values.

        Restores values in selected cells to their initial state from the
        database. If a cell's initial value doesn't exist (e.g., user-added
        tags), it cannot be reset and a warning will be displayed.

        The operation is recorded in the project's undo history. Any existing
        redo history is cleared after this operation.

        Side effects:
            - Updates database values in COLLECTION_CURRENT
            - Updates table cell displays
            - Appends to project.undos
            - Clears project.redos
            - Resizes columns to fit content
            - May display warning dialog for unreset values
        """
        # Import locally to prevent circular import
        from populse_mia.utils import set_item_data

        modified_values = []
        # To know if some values do not have raw values (user tags)
        has_unreset_values = False
        selected_points = self.selectedIndexes()

        if not selected_points:
            return

        with self.project.database.data(write=True) as database_data:

            for point in selected_points:
                col = point.column()
                tag_name = self.horizontalHeaderItem(col).text()
                field_type = database_data.get_field_attributes(
                    COLLECTION_CURRENT, tag_name
                )["field_type"]

                for row in range(len(self.scans_to_visualize)):
                    scan = self.item(row, 0).text()
                    initial_value = database_data.get_value(
                        collection_name=COLLECTION_INITIAL,
                        primary_key=scan,
                        field=tag_name,
                    )

                    if initial_value is None:
                        has_unreset_values = True
                        continue

                    current_value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan,
                        field=tag_name,
                    )

                    try:
                        database_data.set_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            values_dict={tag_name: initial_value},
                        )
                        set_item_data(
                            self.item(row, col),
                            initial_value,
                            field_type,
                        )
                        modified_values.append(
                            [scan, tag_name, current_value, initial_value]
                        )

                    except ValueError:
                        has_unreset_values = True

        # Record operation in undo history
        self.project.undos.append(["modified_values", modified_values])
        self.project.redos.clear()

        if has_unreset_values:
            self.display_unreset_values()

        self.resizeColumnsToContents()

    def reset_row(self):
        """
        Reset selected cells to their original values from the initial
        collection.

        Restores the values of all cells in selected rows to their initial
        state by copying values from COLLECTION_INITIAL to COLLECTION_CURRENT.
        Only cells with available initial values are reset. User-defined tags
        without initial values are skipped and trigger a warning dialog.

        The operation is recorded in the project's undo/redo history, allowing
        users to revert the reset if needed. After resetting, columns are
        automatically resized to fit their contents.

        Side Effects:
            - Updates database values in COLLECTION_CURRENT
            - Updates table cell display values
            - Appends operation to project.undos
            - Clears project.redos
            - Shows warning dialog if any values couldn't be reset
            - Resizes table columns
        """
        # Import here to prevent circular dependency
        from populse_mia.utils import set_item_data

        # Early return if nothing selected
        selected_indices = self.selectedIndexes()

        if not selected_indices:
            return

        # Track modifications for undo history
        modified_values = []
        # To know if some values do not have raw values (user tags)
        has_unreset_values = False
        # Get unique rows from selection
        selected_rows = {index.row() for index in selected_indices}

        with self.project.database.data(write=True) as database_data:

            for row in selected_rows:
                # FileName is always first column
                scan_name = self.item(row, 0).text()

                for column in range(len(self.horizontalHeader())):
                    # We get the tag name from the header
                    tag = self.horizontalHeaderItem(column).text()
                    # Fetch current and initial values
                    current_value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan_name,
                        field=tag,
                    )
                    initial_value = database_data.get_value(
                        collection_name=COLLECTION_INITIAL,
                        primary_key=scan_name,
                        field=tag,
                    )

                    # Skip if no initial value exists (e.g., user-defined tags)
                    if initial_value is None:
                        has_unreset_values = True
                        continue

                    # Attempt to reset the value
                    try:
                        database_data.set_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan_name,
                            values_dict={tag: initial_value},
                        )
                        # Update table cell display
                        field_type = database_data.get_field_attributes(
                            COLLECTION_CURRENT, tag
                        )["field_type"]
                        set_item_data(
                            self.item(row, column), initial_value, field_type
                        )
                        # Record change for history
                        modified_values.append(
                            [scan_name, tag, current_value, initial_value]
                        )

                    except ValueError:
                        has_unreset_values = True

        # Record operation in undo history
        if modified_values:
            self.project.undos.append(["modified_values", modified_values])
            self.project.redos.clear()

        # Notify user if some values couldn't be reset
        if has_unreset_values:
            self.display_unreset_values()

        self.resizeColumnsToContents()

    def section_moved(self, logical_index, old_index, new_index):
        """
        Handle section movement to keep the FileName column fixed at
        position 0.

        This slot is triggered when a user attempts to reorder table columns.
        It ensures the FileName column (logical index 0) always remains at the
        leftmost visual position, regardless of user drag-and-drop actions.

        :param logical_index: The logical index of the moved column (unused).
        :param old_index: The previous visual position of the column (unused).
        :param new_index: The new visual position of the column (unused).

        Note:
            Parameters are required by the Qt signal signature but not used in
            the implementation. Uses a guard flag to prevent recursive calls
            when programmatically repositioning the FileName column.
        """

        # Prevent recursive calls when we programmatically move sections
        if getattr(self, "_ignore_section_move", False):
            return

        self._ignore_section_move = True

        try:
            header = self.horizontalHeader()
            file_name_visual_index = header.visualIndex(0)

            # If FileName column has moved, restore it to position 0
            if file_name_visual_index != 0:
                header.moveSection(file_name_visual_index, 0)
                self.update_selection()
                self.update()

        finally:
            self._ignore_section_move = False

    def select_all_column(self, col):
        """
        Select all cells in a column when its header is double-clicked.

        This method clears any existing selection before selecting the entire
        column, ensuring only the specified column is highlighted.

        :param col (int): The zero-based index of the column to select.
        """
        self.clearSelection()
        self.selectColumn(col)

    def select_all_columns(self):
        """
        Select all columns containing currently selected cells.

        Expands the current cell selection to include entire columns. If cells
        from multiple columns are selected, all corresponding columns will be
        selected. This method is typically invoked from the context menu.

        Note:
            Temporarily switches selection mode to MultiSelection during
            operation, then restores ExtendedSelection mode.
        """
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        # Get unique column indices from selected cells
        selected_columns = {index.column() for index in self.selectedIndexes()}
        self.clearSelection()

        # Select each unique column
        for col in selected_columns:
            self.selectColumn(col)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def selection_changed(self):
        """
        Update the tab view when the table selection changes.

        Rebuilds the internal scans list based on currently selected items,
        grouping tag names by scan name. If link_viewer is enabled, updates
        the connected mini viewer display.

        Side effects:
            - Clears and repopulates self.scans with [scan_name, [tag_names]]
              pairs
            - Calls data_browser.connect_mini_viewer() if self.link_viewer
              is True
        """
        # Disconnect signals
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:
            # Rebuild scans list from selected items
            self.scans.clear()
            scan_dict = {}

            for point in self.selectedItems():
                scan_name = self.item(point.row(), 0).text()
                tag_name = self.horizontalHeaderItem(point.column()).text()
                # Group tags by scan name using a dictionary
                scan_dict.setdefault(scan_name, []).append(tag_name)

            # Convert dictionary to list format
            self.scans.extend(
                [scan_name, tags] for scan_name, tags in scan_dict.items()
            )

            # Update image viewer if linked
            if self.link_viewer:
                self.data_browser.connect_mini_viewer()

        finally:

            # Reconnect signals
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def show_brick_history(self, scan):
        """
        Display a popup window showing the history of a brick.

        This method retrieves the brick UUID associated with the triggering
        sender, creates a history popup dialog, and displays it to the user.

        :param scan: The scan data to display in the history popup.

        Note:
            The sender (typically a UI widget) must be registered in
            self.bricks to retrieve the corresponding brick UUID.
        """
        brick_uuid = self.bricks[self.sender()]
        self.brick_history_popup = PopUpShowHistory(
            project=self.project,
            brick_uuid=brick_uuid,
            scan=scan,
            databrowser=self.data_browser,
            main_window=self.data_browser.main_window,
        )
        self.brick_history_popup.show()

    def sort_column(self, order):
        """
        Sort the currently selected column.

        :param order (Qt.SortOrder or int): Sort order to apply.
            - Qt.AscendingOrder (0): Sort from lowest to highest
            - Qt.DescendingOrder (1): Sort from highest to lowest

        Note:
            Temporarily disconnects signals during sorting to prevent
            unwanted side effects, then reconnects them afterward.
        """
        current_item = self.currentItem()

        if current_item is None:
            return

        self._safe_reconnect(self.itemChanged, self.on_cell_changed)

        try:
            self.horizontalHeader().setSortIndicator(
                current_item.column(), order
            )

        finally:
            self._safe_disconnect(self.itemChanged, self.on_cell_changed)

    def sort_updated(self, column, order):
        """
        Update project state and apply sorting to the table.

        Temporarily disconnects signals, updates the project's sort
        configuration, applies the sort to table items, refreshes visual
        elements, and reconnects signals.

        :param column: The column index to sort by. Use -1 to indicate no
                       sorting.
        :param order: The sort order (Qt.AscendingOrder or Qt.DescendingOrder).

        Note:
            This method is a no-op when column is -1, allowing safe calls with
            invalid column indices.
        """

        if column == -1:
            return

        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        try:
            self.project.setSortOrder(int(order))
            self.project.setSortedTag(self.horizontalHeaderItem(column).text())
            self.sortItems(column, order)
            self.update_colors()
            self.resizeRowsToContents()

        finally:
            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def update_colors(self):
        """
        Update cell background colors based on data state and visibility.

        Colors indicate:
            - White/Grey: Unmodified builtin tags (alternating for visible
                          rows)
            - Cyan/Blue: Modified builtin tags (alternating for visible rows)
            - Pink/Red: User-defined tags or null values (alternating for
                        visible rows)

        Note: This method assumes the itemChanged signal is disconnected.
        Automatically saves modifications if auto-save is enabled.
        """

        # itemChanged signal is always disconnected when calling this method
        # Extract headers and scan identifiers
        tags = [
            self.horizontalHeaderItem(col).text()
            for col in range(self.columnCount())
        ]
        scans = [
            self.item(row, 0).text() if self.item(row, 0) else None
            for row in range(self.rowCount())
        ]

        # Fetch database documents and field metadata
        with self.project.database.data() as database_data:
            primary_key = database_data.get_primary_key_name(
                COLLECTION_CURRENT
            )

            if scans:
                escaped_scans = [
                    scan.replace("\\", "\\\\")
                    for scan in self.scans_to_visualize
                ]
                joined_scans = ", ".join(f'"{scan}"' for scan in escaped_scans)
                req = f"{primary_key} IN [{joined_scans}]"
                documents_curr = database_data.filter_documents(
                    COLLECTION_CURRENT, req
                )
                documents_init = database_data.filter_documents(
                    COLLECTION_INITIAL, req
                )

            else:
                documents_curr = []
                documents_init = []

            fields = {
                field_name: database_data.get_field_attributes(
                    COLLECTION_CURRENT, field_name
                )
                for field_name in database_data.get_field_names(
                    COLLECTION_CURRENT
                )
            }

        # Build lookup tables for efficient access
        table_scans = {
            self.item(row, 0).text(): row for row in range(self.rowCount())
        }
        table_tags = {
            self.horizontalHeaderItem(column).text(): column
            for column in range(self.columnCount())
        }
        column_indices = [table_tags[tag] for tag in tags]
        # Precompute even/odd status for visible rows
        row_parity = []
        is_even = True

        for row in range(self.rowCount()):
            row_parity.append(is_even)

            if not self.isRowHidden(row):
                is_even = not is_even

        # Color mapping for different states
        COLORS = {
            ("white", True): (255, 255, 255),  # White
            ("white", False): (230, 230, 230),  # Grey
            ("modified", True): (200, 230, 245),  # Cyan
            ("modified", False): (150, 215, 230),  # Blue
            ("user_or_null", True): (245, 215, 215),  # Pink
            ("user_or_null", False): (245, 175, 175),  # Red
        }

        # Update cell colors
        for scan_curr, scan_init in zip(documents_curr, documents_init):

            try:
                row = table_scans[scan_curr[tags[0]]]

            except KeyError:
                break

            except Exception:
                logger.warning(
                    "Unexpected exception while updating DataBrowser colors. "
                    "Display may be in degraded state.",
                    exc_info=True,
                )
                break

            if self.isRowHidden(row):
                continue

            is_even = row_parity[row]

            for column, tag in zip(column_indices, tags):

                if self.isColumnHidden(column):
                    continue

                item = self.item(row, column)

                # Determine the appropriate color key for a cell
                # First column always uses default white/grey
                if column == 0:
                    color_key = ("white", is_even)

                # Null values get user_or_null coloring
                elif scan_curr[tag] is None:
                    color_key = ("user_or_null", is_even)

                # Builtin tags: check if modified
                elif fields[tag]["origin"] == TAG_ORIGIN_BUILTIN:

                    if scan_curr[tag] != scan_init[tag]:
                        color_key = ("modified", is_even)

                    else:
                        color_key = ("white", is_even)

                # User-defined tags
                else:
                    color_key = ("user_or_null", is_even)

                color = QColor(*COLORS[color_key])
                item.setData(Qt.BackgroundRole, QVariant(color))

        # Auto-save if enabled
        config = Config()

        if config.isAutoSave():
            self.project.saveModifications()

    def update_selection(self):
        """
        Update table selection based on current scan results.

        Clears existing selection and selects cells corresponding to tags
        found in the current scan results. For each scan, selects the cells at
        the intersection of the scan's row and its associated tag columns.
        """
        # Selection updated
        self.clearSelection()

        for scan_id, tags in self.scans:
            row = self.get_scan_row(scan_id)

            if row is None:
                continue

            for tag in tags:
                column = self.get_tag_column(tag)

                if column is not None:
                    self.item(row, column).setSelected(True)

    def update_table(self, take_tags_to_update=False):
        """
        Refresh the table with current project data.

        Completely resets and repopulates the table when switching projects.
        This involves clearing selections, fetching current scan documents,
        refilling headers and cells, resizing columns/rows, and updating
        the visual appearance.

        :param take_tags_to_update: If True, updates tags during the header
                                    fill operation. Defaults to False.

        Side Effects:
            - Clears current table selection
            - Resets scans_to_visualize and scans_to_search attributes
            - Clears selected scans list if selection is active
            - Disconnects and reconnects table signals
            - Modifies table dimensions and visual styling
        """
        self.setSortingEnabled(False)
        self.clearSelection()  # Selection cleared when switching project

        # Fetch current scans from database
        with self.project.database.data() as database_data:
            self.scans_to_visualize = database_data.get_document_names(
                COLLECTION_CURRENT
            )

        self.scans_to_search = list(self.scans_to_visualize)

        # Reset selected scans if selection mode is active
        if self.activate_selection:
            self.scans = []

        # Update table structure with signals temporarily disconnected
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:
            self.setRowCount(len(self.scans_to_visualize))
            # Sort visual management
            self.fill_headers(take_tags_to_update)
            # Cells filled
            self.fill_cells_update_table()
            # Adjust dimensions and styling
            self.resizeColumnsToContents()
            self.resizeRowsToContents()
            self.update_colors()

        finally:

            # Ensure signals are reconnected even if an error occurs
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def update_visualized_columns(self, old_tags, showed):
        """
        Update column visibility based on tag selection changes.

        Synchronizes the table's visible columns with the provided tag list
        by:
            - Hiding columns for tags that are no longer displayed
            - Showing columns for newly displayed tags
            - Updating advanced search dropdowns if the search panel is open
            - Refreshing column sizing and colors

        :param old_tags (list): Previously visualized tags.
        :param showed (list): Tags to currently display in the table.
        """
        # Disconnect signals
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:
            # Convert to sets for efficient difference operations
            old_set, new_set = set(old_tags), set(showed)

            # Hide columns for removed tags
            for tag in old_set - new_set:
                self.setColumnHidden(self.get_tag_column(tag), True)

            # Show columns for added/visible tags
            for tag in new_set:
                self.setColumnHidden(self.get_tag_column(tag), False)

            if not (
                hasattr(self.data_browser, "frame_advanced_search")
                and not self.data_browser.frame_advanced_search.isHidden()
            ):
                return

            # Update advanced search dropdowns if visible
            for row in self.data_browser.advanced_search.rows:
                fields = row[2]
                fields.clear()
                fields.addItems(showed)
                fields.model().sort(0)
                fields.addItem("All visualized tags")

            # Refresh table appearance
            self.resizeColumnsToContents()
            self.update_colors()

        finally:

            # Restore selection handling
            if self.activate_selection:
                self.update_selection()
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def update_visualized_rows(self, old_scans):
        """
        Update table row visibility based on current scan visualization state.

        Temporarily disconnects selection signals, hides rows for scans no
        longer in the visualization list, shows rows for newly visualized
        scans, and updates the table appearance.

        :param old_scans: Collection of scans from the previous state, used to
                          determine which rows need to be hidden.
        """
        # Disconnect signals
        self._safe_disconnect(self.itemChanged, self.on_cell_changed)

        if self.activate_selection:
            self._safe_disconnect(
                self.itemSelectionChanged, self.selection_changed
            )

        try:
            # Hide rows for scans removed from visualization
            old_scan_set = set(old_scans)
            current_scan_set = set(self.scans_to_visualize)

            for scan in old_scan_set - current_scan_set:

                if (row := self.get_scan_row(scan)) is not None:
                    self.setRowHidden(row, True)

            # Show rows for scans added to visualization
            for scan in current_scan_set:

                if (row := self.get_scan_row(scan)) is not None:
                    self.setRowHidden(row, False)

            # Update table appearance
            self.resizeColumnsToContents()

            # Update selection and colors
            if self.activate_selection:
                self.update_selection()

            self.update_colors()

        finally:

            # Re-enable selection change signals
            if self.activate_selection:
                self._safe_reconnect(
                    self.itemSelectionChanged, self.selection_changed
                )

            self._safe_reconnect(self.itemChanged, self.on_cell_changed)

    def visualized_tags_pop_up(self):
        """
        Display a modal dialog for configuring visualized tag columns.

        Opens a properties popup showing currently visible tags and allowing
        the user to modify which tags are displayed in the data browser. The
        popup is sized to 50% of screen width and 80% of screen height.
        """

        with self.project.database.data() as database_data:
            # Old list of columns
            current_tags = database_data.get_shown_tags()

        self.pop_up = PopUpProperties(
            self.project, self.data_browser, current_tags
        )
        self.pop_up.tab_widget.setCurrentIndex(0)
        # Size popup relative to screen dimensions
        screen = QApplication.instance().desktop().screenGeometry()
        popup_width = int(screen.width() * 0.5)
        popup_height = int(screen.height() * 0.8)
        self.pop_up.resize(popup_width, popup_height)
        self.pop_up.show()


class TimeFormatDelegate(QItemDelegate):
    """
    Delegate for handling time data display and editing in table views.

    This delegate creates a QTimeEdit widget with millisecond precision
    (hh:mm:ss.zzz format) for editing time values in a TableDataBrowser.

    .. Methods:
        - createEditor: Create and return a QDateEdit widget for editing times
    """

    def __init__(self, parent=None):
        """
        Initialize the time format delegate.

        :param parent: Parent QWidget, if any. Defaults to None.
        """
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """
        Create and configure the editor widget for time values.

        :param parent: Parent widget for the editor.
        :param option: Style options for the item (unused, required
                       by Qt API).
        :param index: Model index of the item being edited (unused, required
                      by Qt API).

        :return (QTimeEdit): Configured time editor widget with
                             hh:mm:ss.zzz format.
        """
        editor = QTimeEdit(parent)
        editor.setDisplayFormat("hh:mm:ss.zzz")
        return editor
