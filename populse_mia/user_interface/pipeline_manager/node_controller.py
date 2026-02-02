"""
Pipeline Node Management and Filtering Module

This module provides a collection of Qt-based widgets and controllers for
managing pipeline nodes, filtering database entries, and assigning values to
node plugs in a data processing workflow. It is designed to integrate with a
pipeline editor, enabling users to:

    - View and edit node parameters, including inputs, outputs, and attributes.
    - Filter and select database entries (e.g., scans, files) for assignment
      to pipeline nodes.
    - Apply advanced search and tag-based filtering to refine selections.
    - Handle undo/redo operations for parameter changes and node renaming.
    - Manage subprocesses and context names for hierarchical pipelines.

The module is built on top of Qt and Capsul, leveraging custom widgets like
`AttributedProcessWidget` and `TableDataBrowser` to provide a user-friendly
interface for complex pipeline interactions.

:Contains:

    Class:
        - PlugFilter (must be declared before AttributesFilter)
        - AttributesFilter
        - CapsulNodeController
        - FilterWidget
        - NodeController

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
from functools import partial

import sip

# capsul imports
from capsul.attributes.completion_engine import ProcessCompletionEngine
from capsul.pipeline.pipeline_nodes import PipelineNode
from capsul.pipeline.process_iteration import ProcessIteration
from capsul.qt_gui.widgets.attributed_process_widget import (
    AttributedProcessWidget,
)

# PyQt5 imports
from PyQt5 import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# soma-base imports
from soma.controller import trait_ids
from traits.api import TraitError, Undefined

from populse_mia.data_manager import (
    BRICK_OUTPUTS,
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    NOT_DEFINED_VALUE,
    TAG_FILENAME,
)

# Populse_MIA imports
from populse_mia.data_manager.filter import Filter
from populse_mia.software_properties import Config
from populse_mia.user_interface.data_browser.advanced_search import (
    AdvancedSearch,
)
from populse_mia.user_interface.data_browser.data_browser import (
    TableDataBrowser,
)
from populse_mia.user_interface.data_browser.rapid_search import RapidSearch
from populse_mia.user_interface.pipeline_manager.process_mia import ProcessMIA
from populse_mia.user_interface.pop_ups import (
    PopUpSelectTagCountTable,
    PopUpVisualizedTags,
)

from . import type_editors

logger = logging.getLogger(__name__)


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


class AttributesFilter(PlugFilter):
    """
    A specialized widget for filtering database entries and collecting their
    attributes.

    This widget extends `PlugFilter` to provide a user-friendly interface for
    filtering files using both rapid and advanced search tools. It allows
    users to:
        - Filter database entries based on customizable criteria.
        - Select specific rows or use the entire filtered dataset.
        - Collect attributes from the selected or filtered entries.
        - Emit the collected attributes as a structured dictionary for further
          processing.

    The collected attributes are organized into a dictionary where each key
    represents an attribute name, and the corresponding value is a list of all
    values for that attribute across the selected or filtered entries.

    .. Methods:
        - ok_clicked: Closes the widget and emits the collected attributes. If
                      rows are selected, only those rows' attributes are
                      collected; otherwise, attributes are collected from all
                      entries matching the current filter.
    """

    # Signal emitted when the user validates the selection. The signal carries
    # a dictionary mapping attribute names to lists of values extracted from
    # the database.
    attributes_selected = pyqtSignal(dict)

    def ok_clicked(self):
        """
        Close the widget and emit the collected attributes.

        If rows are selected in the table, attributes are collected only from
        those rows. Otherwise, attributes are collected from all entries
        matching the current filter. The resulting attributes are grouped by
        field name and emitted via the ``attributes_selected`` signal.
        """
        self.close()
        attributes = {}
        selected_indexes = self.table_data.selectedIndexes()

        with self.project.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)

            if selected_indexes:
                # Collect scan names from selected rows
                scan_names = {
                    self.table_data.item(index.row(), 0).text()
                    for index in selected_indexes
                }

            else:
                # Collect scan names from the current filter
                scan_names = self.table_data.get_current_filter()

            for scan_name in scan_names:

                for field in field_names:
                    value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan_name,
                        field=field,
                    )
                    attributes.setdefault(field, []).append(value)

        self.attributes_selected.emit(attributes)


# Node controller V2 style
class CapsulNodeController(QWidget):
    """
    A PyQt widget for managing and editing pipeline node parameters using
    Capsul's AttributedProcessWidget.

    This controller provides a user interface for interacting with pipeline
    nodes, enabling users to:
        - View and modify node parameters using Capsul's
          AttributedProcessWidget.
        - Rename nodes and update the pipeline accordingly.
        - Filter and manage node attributes.
        - Handle undo/redo operations for parameter changes.
        - Recursively rename subprocesses and adjust context names.

    The widget is designed to integrate with a pipeline editor, providing
    real-time updates and synchronization between the UI and the underlying
    pipeline state.

    .. Methods:
        - display_parameters: Displays the parameters of the selected node and
                              configures the UI.
        - filter_attributes: Opens a dialog for filtering node attributes.
        - release_process: Cleans up process notifications and signals.
        - rename_subprocesses: Recursively renames subprocesses and updates
                               context names.
        - static_release: Removes trait change notifications from a process.
        - parameters_changed: Handles parameter value changes and emits a
                              signal.
        - update_attributes_from_filter: Applies selected attributes from the
                                         filter widget.
        - update_node_name: Renames the selected node and updates the pipeline.
        - update_parameters: Placeholder for backward compatibility (no
                             operation).
    """

    # Signal emitted when a node or parameter value is changed. Used for
    # undo/redo functionality.
    value_changed = pyqtSignal(list)

    def __init__(self, project, scan_list, pipeline_manager_tab, main_window):
        """
        Initialize the node controller.

        :param project: Current project instance.
        :param scan_list: List of available scans.
        :param pipeline_manager_tab: Parent pipeline manager tab.
        :parammain_window: Main application window.
        """
        super().__init__()
        self.project = project
        self.scan_list = scan_list
        self.main_window = main_window
        self.node_name = ""
        self.visibles_tags = []
        self.pipeline = (
            pipeline_manager_tab.pipelineEditorTabs.get_current_pipeline()
        )
        # Set up the user interface layout
        v_box_final = QVBoxLayout()
        self.setLayout(v_box_final)
        self.process_widget = None
        # Node name editor
        hlayout = QHBoxLayout()
        label_node_name = QLabel("Node name:")
        self.line_edit_node_name = QLineEdit()
        hlayout.addWidget(label_node_name)
        hlayout.addWidget(self.line_edit_node_name)
        v_box_final.addLayout(hlayout)

    def display_parameters(self, node_name, process, pipeline):
        """
        Display the parameters of the selected node.

        Creates and displays widgets for all node parameters, including line
        edits, labels, and control buttons. Handles special cases for pipeline
        inputs/outputs nodes.

        :param node_name (str): Name of the node to display.
        :param process: Process instance associated with the node.
        :param pipeline: Current pipeline containing the node.
        """
        self.node_name = node_name
        self.pipeline = pipeline

        # Configure the node name editor based on whether it's editable
        if self.node_name not in ("inputs", "outputs"):
            self.line_edit_node_name.setText(self.node_name)
            self.line_edit_node_name.setReadOnly(False)
            self.line_edit_node_name.returnPressed.connect(
                self.update_node_name
            )

        else:
            self.line_edit_node_name.setText("Pipeline inputs/outputs")
            self.line_edit_node_name.setReadOnly(True)

        # Remove and clean up the existing process widget
        if self.process_widget:
            self.static_release(
                self.process_widget.attributed_process, self.parameters_changed
            )
            self.process_widget.deleteLater()
            self.process_widget = None

        # Get connected inputs to disable their filter buttons
        node = pipeline.nodes.get(node_name)

        if node is None:
            connected_inputs = set()

        else:
            connected_inputs = {
                plug_name
                for plug_name, plug in node.plugs.items()
                if not plug.output and plug.links_from
            }

        # Create the attributed process widget
        self.process = process
        ProcessCompletionEngine.get_completion_engine(process)
        userlevel = Config().get_user_level()
        self.process_widget = AttributedProcessWidget(
            process,
            override_control_types={
                "File": type_editors.PopulseFileControlWidget,
                "Directory": type_editors.PopulseDirectoryControlWidget,
                "List_File": (
                    type_editors.PopulseOffscreenListFileControlWidget
                ),
                "Undefined": type_editors.PopulseUndefinedControlWidget,
            },
            separate_outputs=True,
            user_data={
                "project": self.project,
                "scan_list": self.scan_list,
                "main_window": self.main_window,
                "node_controller": self,
                "connected_inputs": connected_inputs,
            },
            scroll=False,
            userlevel=userlevel,
        )

        # Add filter button if the process has user attributes
        if hasattr(process, "completion_engine"):
            compl = process.completion_engine
            atts = compl.get_attribute_values()

            if len(atts.user_traits()) != 0:
                btn = QPushButton("Filter")
                btn.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)
                btn.clicked.connect(self.filter_attributes)
                self.process_widget.attrib_widget.layout().insertWidget(0, btn)

        # Add widget to layout and connect signals
        self.layout().addWidget(self.process_widget)
        self.process.on_trait_change(self.parameters_changed, dispatch="ui")

    def filter_attributes(self):
        """
        Display the attributes filter dialog.

        Opens a popup widget that allows users to filter and select attributes
        for the current process node.
        """
        self.pop_up = AttributesFilter(
            self.project,
            self.scan_list,
            self.process,
            self.node_name,
            "attributes",
            self,
            self.main_window,
        )
        self.pop_up.show()
        self.pop_up.attributes_selected.connect(
            self.update_attributes_from_filter
        )

    def release_process(self):
        """
        Clean up process notifications and signals.
        """

        if hasattr(self, "process"):
            self.process.on_trait_change(self.parameters_changed, remove=True)

        try:

            if not sip.isdeleted(self):
                self.value_changed.disconnect()

        except TypeError:
            pass  # Signal was not connected

    def rename_subprocesses(self, node, parent_node_name):
        """
        Recursively rename subprocesses within the pipeline, adjusting the
        context name.

        This method checks if the process is part of a pipeline and modifies
        its context name accordingly. If the process name contains a
        hierarchy of at least three levels, the context name is updated with
        the parent node name and the remaining parts of the context name. If
        the process is a pipeline node, the method is called recursively for
        each subprocess.

        :param node: The current node being processed.
        :param parent_node_name (str): The name of the parent node to be
                                       included in the context name.
        """
        # Get the context name or process name and split by "."
        context_name = getattr(
            node.process, "context_name", node.process.name
        ).split(".")

        # Check if the process belongs to a pipeline
        if context_name[0] == "Pipeline":

            # If the context name has more than two parts, update the context
            # name
            if len(context_name) >= 3:
                node.process.context_name = (
                    f"Pipeline.{parent_node_name}."
                    f"{'.'.join(context_name[2:])}"
                )

            else:
                node.process.context_name = f"Pipeline.{parent_node_name}"

        else:
            # If not part of a pipeline, just set the context name to the
            # parent node name
            node.process.context_name = parent_node_name

        # Recursively rename subprocesses for pipeline nodes
        if isinstance(node, PipelineNode):

            for name, subnode in node.process.nodes.items():

                if name:
                    self.rename_subprocesses(subnode, parent_node_name)

    @staticmethod
    def static_release(process, param_changed):
        """
        Remove trait change notification from process.

        :param process: Process instance to remove notification from.
        :param param_changed: Callback function to remove.

        """
        process.on_trait_change(param_changed, remove=True)

    def parameters_changed(self, _, plug_name, old_value, new_value):
        """
        Handle parameter value changes and emit signal.

        :param _: Unused parameter (object instance).
        :param plug_name (str): Name of the changed parameter.
        :param old_value: Previous parameter value.
        :param new_value: New parameter value.
        """
        plug_type = type(new_value)
        self.value_changed.emit(
            [
                "plug_value",
                self.node_name,
                old_value,
                plug_name,
                plug_type,
                new_value,
            ]
        )

    def update_attributes_from_filter(self, attributes):
        """
        Apply selected attributes from the filter widget.

        Updates the process completion engine attributes based on user
        selection from the filter dialog. Shows a warning if no matching
        attributes are found.

        :param attributes (dict): Dictionary of attribute names and values to
                                  apply.
        """
        compl = self.process.completion_engine
        atts = compl.get_attribute_values()
        num_set = 0

        for name, value in attributes.items():

            if not atts.trait(name):
                continue

            # Handle list vs scalar attributes
            if isinstance(getattr(atts, name), list):
                setattr(atts, name, value)

            else:
                setattr(atts, name, value[0])

            num_set += 1

        # Handle list vs scalar attributes
        if num_set == 0 and attributes:
            mbox_icon = QMessageBox.Information
            mbox_title = "Unmatching tags / attributes"
            mbox_text = (
                "The selected data tags do not match the expected "
                "attributes set for process parameters completion"
            )
            mbox = QMessageBox(mbox_icon, mbox_title, mbox_text)
            Qt.QTimer.singleShot(2000, mbox.accept)
            mbox.exec()

    def update_node_name(
        self,
        new_node_name=None,
        old_node_name=None,
        from_undo=False,
        from_redo=False,
    ):
        """
        Change the name of the selected node and update the pipeline.

        Renames the node in the pipeline dictionary and updates all associated
        links. For iterated processes, ensures the name starts
        with "iterated_".

        :param new_node_name (str): New name for the node. If None (when this
                                    method is not called from an undo/redo),
                                    reads from the line edit widget.
        :param old_node_name (str): Current node name. If None (when this
                                    method is not called from an undo/redo),
                                    uses self.node_name.
        :param from_undo (bool): True if this action is from an undo operation.
        :param from_redo (bool): True ifthis action is from a redo operation.
        """
        new_node_name = new_node_name or self.line_edit_node_name.text()
        old_node_name = old_node_name or self.node_name

        # Handle iterated process naming convention
        if isinstance(self.process, ProcessIteration):

            if not new_node_name.startswith("iterated_"):
                new_node_name = f"iterated_{new_node_name}"
                self.line_edit_node_name.setText(new_node_name)

        # Check for name conflicts
        if new_node_name in self.pipeline.nodes:
            logger.info(
                f"Cannot rename node '{old_node_name}' to '{new_node_name}': "
                f"node '{new_node_name}' already exists"
            )
            return

        # Perform rename
        self.pipeline.rename_node(old_node_name, new_node_name)
        self.rename_subprocesses(
            self.pipeline.nodes[new_node_name], new_node_name
        )
        # Update internal state
        self.node_name = new_node_name
        self.pipeline.update_nodes_and_plugs_activation()
        # Emit change signal
        self.value_changed.emit(
            [
                "node_name",
                self.pipeline.nodes[new_node_name],
                new_node_name,
                old_node_name,
            ]
        )
        # Update history
        history_maker = ["update_node_name"]

        if not from_undo:
            history_maker.extend(
                [
                    self.pipeline.nodes[new_node_name],
                    new_node_name,
                    old_node_name,
                ]
            )

        # fmt: off
        editor = (
            self.main_window.pipeline_manager.pipelineEditorTabs
            .get_current_editor()
        )
        # fmt: on
        editor.update_history(history_maker, from_undo, from_redo)

        # Display status message
        self.main_window.statusBar().showMessage(
            f"Brick name '{old_node_name} changed to '{new_node_name}'."
        )

    def update_parameters(self, process=None):
        """
        Update parameter values.

        This method is maintained for backward compatibility but does nothing,
        as the controller widget already reacts to process parameter changes.

        :param process: Process instance (unused).
        """
        pass


class FilterWidget(QWidget):
    """
    A PyQt widget for filtering and selecting files in a pipeline's
    Input_Filter process.

    This widget provides a user-friendly interface for filtering database files
    using both rapid and advanced search functionalities. It allows users to:
        - Browse and select files from the project database.
        - Perform rapid searches using a text-based search bar.
        - Apply advanced filters using a customizable search interface.
        - Visualize and update tags associated with the files.
        - Save the configured filter to the process for further use in the
          pipeline.

    The widget is designed to integrate seamlessly with the pipeline editor,
    providing real-time feedback and updates as filters are applied.

    .. Methods:
        - layout_view: Configures and initializes the main widget layout,
                       including search bars, data tables, and action buttons.
        - ok_clicked: Applies the configured filter to the process and closes
                      the widget.
        - reset_search_bar: Resets the search interface to its default state,
                            clearing all filters.
        - search_str: Filters and updates the displayed scans based on the
                      provided search string.
        - update_tag_to_filter: Opens a dialog for selecting tags to filter and
                                updates the filter button text.
        - update_tags: Updates the list of visualized tags through a user
                       dialog and refreshes the table view.
    """

    def __init__(self, project, node_name, node, main_window):
        """
        Initialize the Filter Widget for pipeline node filtering.

        :param project: Current project instance containing database and
                        configuration.
        :param node_name: Display name of the filter node.
        :param node: Input_Filter node instance containing the filter process.
        :param main_window: Parent main window for UI hierarchy.
        """
        super().__init__(None)
        self.setWindowTitle(f"Filter - {node_name}")
        self.project = project
        self.node = node
        self.process = node.process
        self.main_window = main_window

        # Retrieve visible tags from database
        with self.project.database.data() as database_data:
            self.visible_tags = database_data.get_shown_tags()

        # Build scan list from node input
        self.scan_list = (
            [
                os.path.relpath(scan, self.project.folder)
                for scan in self.process.input
            ]
            if self.process.input and self.process.input is not Undefined
            else []
        )
        # Initialize table data browser with filtered scans
        self.table_data = TableDataBrowser(
            self.project, self, self.visible_tags, False, False
        )
        # Configure table data browser to display only filtered scans
        all_scans = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.scan_list
        self.table_data.scans_to_search = self.scan_list
        self.table_data.update_visualized_rows(all_scans)
        # Initialize search components with existing filter
        filter_to_apply = self.node.process.filter
        # Rapid search setup
        self.rapid_search = RapidSearch(self)

        if filter_to_apply.search_bar:
            self.rapid_search.setText(filter_to_apply.search_bar)

        self.rapid_search.textChanged.connect(self.search_str)
        # Advanced search setup
        self.advanced_search = AdvancedSearch(
            self.project,
            self,
            self.scan_list,
            self.visible_tags,
            from_pipeline=True,
        )
        self.advanced_search.show_search()
        self.advanced_search.apply_filter(filter_to_apply)
        # Initialize UI components
        self.button_cross = QToolButton()
        self.push_button_tag_filter = QPushButton(TAG_FILENAME)
        self.layout_view()

    def layout_view(self):
        """
        Configure and initialize the main widget layout.

        Sets up a vertical layout containing:
            - Search bar with reset button
            - Advanced search widget
            - Data table
            - Action buttons (visualize tags, filter, OK, Cancel)

        The window is sized to 60% width and 80% height of the screen
        resolution.
        """
        # Configure search reset button
        sources_images_dir = Config().getSourceImageDir()
        self.button_cross.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.button_cross.setIcon(
            QIcon(os.path.join(sources_images_dir, "gray_cross.png"))
        )
        self.button_cross.clicked.connect(self.reset_search_bar)
        # Create search bar layout
        search_bar_layout = QHBoxLayout()
        search_bar_layout.addWidget(self.rapid_search)
        search_bar_layout.addWidget(self.button_cross)
        # Create and configure action buttons
        push_button_tags = QPushButton("Visualized tags")
        push_button_tags.clicked.connect(self.update_tags)
        self.push_button_tag_filter.clicked.connect(self.update_tag_to_filter)
        push_button_ok = QPushButton("OK")
        push_button_ok.clicked.connect(self.ok_clicked)
        push_button_cancel = QPushButton("Cancel")
        push_button_cancel.clicked.connect(self.close)
        # Create bottom button layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(push_button_tags)
        buttons_layout.addWidget(self.push_button_tag_filter)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(push_button_ok)
        buttons_layout.addWidget(push_button_cancel)
        # Assemble main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(search_bar_layout)
        main_layout.addWidget(self.advanced_search)
        main_layout.addWidget(self.table_data)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        # Set window size as percentage of screen resolution
        screen_resolution = QApplication.instance().desktop().screenGeometry()
        self.setMinimumWidth(round(screen_resolution.width() * 0.6))
        self.setMinimumHeight(round(screen_resolution.height() * 0.8))

    def ok_clicked(self):
        """
        Apply the configured filter to the process and close the dialog.

        Collects filter parameters from the advanced search interface and rapid
        search text field, creates a Filter object, and applies it to the
        process if it's a ProcessMIA instance. The dialog is then closed
        regardless of process type.
        """

        if not isinstance(self.process, ProcessMIA):
            self.close()
            return

        (
            fields,
            conditions,
            values,
            links,
            nots,
        ) = self.advanced_search.get_filters(False)
        filter_object = Filter(
            None,
            nots,
            values,
            fields,
            links,
            conditions,
            self.rapid_search.text(),
        )
        self.process.filter = filter_object
        self.close()

    def reset_search_bar(self):
        """
        Reset search interface to default state.

        Clears the rapid search text field, resets advanced search rows, and
        restores the table to display all available scans. The table is
        updated efficiently by tracking the previous visualization state.

        Side effects:
            - Clears rapid_search text field
            - Resets advanced_search rows to empty list
            - Updates advanced_search display
            - Restores table_data to show all scans from scan_list
        """
        # Clear search inputs
        self.rapid_search.setText("")
        self.advanced_search.rows = []
        self.advanced_search.show_search()
        # Restore full scan list and update table
        previous_scans = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.scan_list
        self.table_data.scans_to_search = self.scan_list
        self.table_data.update_visualized_rows(previous_scans)

    def search_str(self, str_search):
        """
        Filter and update the displayed scans based on a search string.

        Performs a rapid search to filter scans in the browser view. An empty
        search string displays all available scans. Special handling is
        provided for undefined values and custom search filters.

        :param str_search: Search query string. Use empty string to show all
                           scans, or NOT_DEFINED_VALUE constant to filter scans
                           with undefined fields.

        Side Effects:
            - Updates self.table_data.scans_to_visualize with filtered results
            - Updates self.advanced_search.scans_list with filtered results
            - Triggers table row update via
              self.table_data.update_visualized_rows()
        """

        old_scan_list = self.table_data.scans_to_visualize

        # Return all scans if search is empty
        if not str_search:
            return_list = self.table_data.scans_to_search

        else:

            with self.project.database.data() as database_data:
                shown_tags = database_data.get_shown_tags()

                # Build appropriate filter based on search type
                if str_search == NOT_DEFINED_VALUE:
                    scan_filter = self.prepare_not_defined_filter(shown_tags)

                else:
                    scan_filter = self.rapid_search.prepare_filter(
                        str_search,
                        shown_tags,
                        old_scan_list,
                    )

                # Execute filter and extract filenames
                scans = database_data.filter_documents(
                    COLLECTION_CURRENT, scan_filter
                )
                return_list = [scan[TAG_FILENAME] for scan in scans]

        # Update display lists
        self.table_data.scans_to_visualize = return_list
        self.advanced_search.scans_list = return_list
        # Refresh table rows
        self.table_data.update_visualized_rows(old_scan_list)

    def update_tag_to_filter(self):
        """
        Display a tag selection dialog and update the filter button text.

        Opens a popup dialog allowing the user to select from visible project
        tags. If a tag is selected (dialog accepted), updates the filter
        button's text to reflect the chosen tag.
        """
        pop_up = PopUpSelectTagCountTable(
            self.project, self.visible_tags, self.push_button_tag_filter.text()
        )

        if pop_up.exec_():
            self.push_button_tag_filter.setText(pop_up.selected_tag)

    def update_tags(self):
        """
        Update the list of visualized tags through a user dialog.

        Opens a modal dialog that allows users to select which tags should be
        displayed in the table view. Upon confirmation, the method:
            - Updates table columns to show only selected tags
            - Refreshes advanced search field options
            - Ensures TAG_FILENAME is always included in visible tags

        The dialog is automatically cleaned up after use, whether the user
        confirms or cancels the operation.
        """

        # Clean up any existing dialog
        if hasattr(self, "dialog") and self.dialog:
            self.dialog.deleteLater()
            self.dialog = None

        # Create and configure dialog
        self.dialog = QDialog()
        self.dialog.setMinimumSize(600, 600)
        # Set up dialog content
        visualized_tags = PopUpVisualizedTags(self.project, self.visible_tags)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.dialog.accept)
        buttons.rejected.connect(self.dialog.reject)
        # Build layout
        layout = QVBoxLayout()
        layout.addWidget(visualized_tags)
        layout.addWidget(buttons)
        self.dialog.setLayout(layout)

        # Show dialog and process result
        if self.dialog.exec():
            # Apply the selected tag visibility changes to table and
            # search fields
            new_visibilities = [
                visualized_tags.list_widget_selected_tags.item(i).text()
                for i in range(
                    visualized_tags.list_widget_selected_tags.count()
                )
            ]

            # Ensure TAG_FILENAME is always included
            if TAG_FILENAME not in new_visibilities:
                new_visibilities.append(TAG_FILENAME)

            # Update table columns
            self.table_data.update_visualized_columns(
                self.visible_tags, new_visibilities
            )
            # Resize columns to fit content
            self.table_data.resizeColumnsToContents()
            self.visible_tags = new_visibilities

            # Update advanced search fields
            for row in self.advanced_search.rows:
                fields = row[2]
                fields.clear()
                fields.addItems(new_visibilities)
                fields.model().sort(0)
                fields.addItem("All visualized tags")

        # Clean up the dialog reference at the end
        if hasattr(self, "dialog") and self.dialog:
            self.dialog.deleteLater()
            self.dialog = None


# Node controller V1 style
class NodeController(QWidget):
    """
    A PyQt widget for managing and editing the input/output values and
    parameters of a pipeline node.

    This controller provides a user interface to interact with pipeline nodes,
    allowing users to:
        - View and edit node names and parameters
        - Filter and update plug values
        - Handle undo/redo operations for parameter changes
        - Manage subprocesses and context names

    The widget is designed to integrate with a pipeline editor, providing
    real-time updates and synchronization between the UI and the underlying
    pipeline state.

    .. Methods:
        - clearLayout: Clears and deletes all items from a widget's layout,
                       including nested layouts.
        - display_filter: Displays a filter dialog for a plug.
        - display_parameters: Renders the parameters UI for a selected node.
        - get_index_from_plug_name: Returns the index of a plug label in the
                                    UI.
        - update_node_name: Updates the name of the selected node in the
                            pipeline.
        - rename_subprocesses: Recursively updates context names for
                               subprocesses.
        - update_parameters: Synchronizes UI parameter values with the process
                             traits.
        - update_plug_value: Updates a plug value.
        - update_plug_value_from_filter: Updates a plug value from filter
                                         results.
        - release_process: Placeholder for process release logic (to be
                           overridden by subclasses).

    """

    value_changed = pyqtSignal(list)

    def __init__(self, project, scan_list, pipeline_manager_tab, main_window):
        """
        Initialize the node controller widget.

        This controller manages the interaction between the current project,
        the selected scans, and the active pipeline within the pipeline manager
        interface.

        :param project: The current project instance.
        :param scan_list: lThe list of selected database files (scans).
        :param pipeline_manager_tab: The parent pipeline manager tab widget.
        :param main_window: The main application window.
        """
        super().__init__(pipeline_manager_tab)
        # Core context
        self.project = project
        self.scan_list = scan_list
        self.main_window = main_window
        # Pipeline state
        self.node_name = ""
        self.pipeline = (
            pipeline_manager_tab.pipelineEditorTabs.get_current_pipeline()
        )
        # Layouts
        self.v_box_final = QVBoxLayout()
        self.h_box_node_name = QHBoxLayout()

    def clearLayout(self, widget):
        """
        Remove and delete all items from a widget's layout.

        This method recursively clears the layout attached to the given widget:
            - QWidget items are detached from their parent.
            - Nested layouts are emptied and scheduled for deletion.
            - The layout itself is deleted once cleared.

        :param widget (QtWidgets.QWidget): The widget whose layout should be
                                           cleared.
        """
        layout = widget.layout()

        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)

            if item.widget() is not None:
                item.widget().setParent(None)

            elif item.layout() is not None:

                # Recursively clear nested layouts
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)

                    if sub_item.widget() is not None:
                        sub_item.widget().setParent(None)

                item.layout().deleteLater()

        sip.delete(layout)

    def display_filter(self, node_name, plug_name, parameters, process):
        """
        Display an interactive filter widget for modifying plug values.

        Creates and shows a PlugFilter dialog that allows users to filter and
        modify the value of a specific plug. The dialog's value changes are
        automatically propagated back to update the plug through a signal
        connection.

        :param node_name: The name of the pipeline node containing the plug.
        :param plug_name: The name of the plug to filter.
        :param parameters: A tuple containing (plug_index, pipeline_instance,
                           plug_value_type) that provides context for the plug
                           being filtered.
        :param process: The process instance associated with the node.

        Note:
            The created PlugFilter is stored in self.pop_up and remains
            accessible until another filter is displayed or the instance is
            destroyed.
        """
        self.pop_up = PlugFilter(
            project=self.project,
            scans_list=self.scan_list,
            process=process,
            node_name=node_name,
            plug_name=plug_name,
            node_controller=self,
            main_window=self.main_window,
        )
        self.pop_up.show()
        # Connect the filter's value changes to the plug update handler
        self.pop_up.plug_value_changed.connect(
            partial(self.update_plug_value_from_filter, plug_name, parameters)
        )

    def display_parameters(self, node_name, process, pipeline):
        """
        Display and configure parameters for the selected pipeline node.

        Creates an interactive interface showing the node's input and output
        parameters with editable fields. For pipeline global inputs (except
        'database_scans'), adds filter buttons for File/List_File/Any trait
        types.

        Special handling:
            - 'inputs'/'outputs' nodes: Name field is read-only, displays
                                        "Pipeline inputs/outputs"
            - Other nodes: Name field is editable and updates on Enter
            - Parameters with userlevel > 0 are hidden from the interface

        :param node_name: Identifier for the node being displayed
        :param process: Node's process object containing traits and their
                        values
        :param pipeline: Parent pipeline instance containing this node

        Side effects:
            - Clears and rebuilds the widget layout
            - Updates node_parameters_tmp in the current pipeline editor
            - Enables the run_pipeline_action
        """
        self.node_name = node_name
        self.current_process = process
        self.pipeline = pipeline
        self.line_edit_input = []
        self.labels_input = []
        self.line_edit_output = []
        self.labels_output = []

        # Clear existing layout
        if self.children():
            self.clearLayout(self)

        self.v_box_final = QVBoxLayout()
        # Node name section
        label_node_name = QLabel("Node name:")
        self.line_edit_node_name = QLineEdit()

        # The pipeline global inputs and outputs node name cannot be modified
        if self.node_name in ("inputs", "outputs"):
            self.line_edit_node_name.setText("Pipeline inputs/outputs")
            self.line_edit_node_name.setReadOnly(True)

        else:
            self.line_edit_node_name.setText(self.node_name)
            self.line_edit_node_name.returnPressed.connect(
                self.update_node_name
            )

        self.h_box_node_name = QHBoxLayout()
        self.h_box_node_name.addWidget(label_node_name)
        self.h_box_node_name.addWidget(self.line_edit_node_name)
        # Input parameters section
        self.button_group_inputs = QGroupBox("Inputs")
        self.v_box_inputs = QVBoxLayout()

        for name, trait in process.user_traits().items():

            if name == "nodes_activation" or (
                trait.userlevel and trait.userlevel > 0
            ):
                continue

            if not trait.output:
                idx = len(self.line_edit_input)
                # Create label and get value
                label_input = QLabel(str(name))
                self.labels_input.append(label_input)

                try:
                    value = getattr(process, name)

                except TraitError:
                    value = Undefined

                # Create input field
                line_edit = QLineEdit(str(value))
                line_edit.returnPressed.connect(
                    partial(
                        self.update_plug_value,
                        "in",
                        name,
                        pipeline,
                        type(value),
                    )
                )
                self.line_edit_input.append(line_edit)
                # Assemble row
                h_box = QHBoxLayout()
                h_box.addWidget(label_input)
                h_box.addWidget(line_edit)

                # Add filter button for eligible pipeline inputs (except if
                # the input is "database_scans" which means that the scans
                # will be filtered with InputFilter)
                if self.node_name == "inputs" and name != "database_scans":
                    trait_type = trait_ids(process.trait(name))

                    if any(
                        t in trait_type for t in ["File", "List_File", "Any"]
                    ):
                        parameters = (idx, pipeline, type(value))
                        push_button = QPushButton("Filter")
                        push_button.clicked.connect(
                            partial(
                                self.display_filter,
                                self.node_name,
                                name,
                                parameters,
                                process,
                            )
                        )
                        h_box.addWidget(push_button)

                self.v_box_inputs.addLayout(h_box)

        self.button_group_inputs.setLayout(self.v_box_inputs)
        # Output parameters section
        self.button_group_outputs = QGroupBox("Outputs")
        self.v_box_outputs = QVBoxLayout()

        for name, trait in process.traits(output=True).items():

            if trait.userlevel and trait.userlevel > 0:
                continue

            idx = len(self.line_edit_output)
            # Create label and get value
            label_output = QLabel(str(name))
            self.labels_output.append(label_output)
            value = getattr(process, name)
            # Create input field
            line_edit = QLineEdit(str(value))
            line_edit.returnPressed.connect(
                partial(
                    self.update_plug_value, "out", name, pipeline, type(value)
                )
            )
            self.line_edit_output.append(line_edit)
            # Assemble row
            h_box = QHBoxLayout()
            h_box.addWidget(label_output)
            h_box.addWidget(line_edit)
            self.v_box_outputs.addLayout(h_box)

        self.button_group_outputs.setLayout(self.v_box_outputs)
        # Assemble final layout
        self.v_box_final.addLayout(self.h_box_node_name)
        self.v_box_final.addWidget(self.button_group_inputs)
        self.v_box_final.addWidget(self.button_group_outputs)
        self.setLayout(self.v_box_final)
        # Update editor state
        # fmt: off
        current_editor = (
            self.main_window
                .pipeline_manager
                .pipelineEditorTabs
                .get_current_editor()
        )
        # fmt: on
        current_editor.node_parameters_tmp[node_name] = {
            "inputs": [line_edit.text() for line_edit in self.line_edit_input],
            "outputs": [
                line_edit.text() for line_edit in self.line_edit_output
            ],
        }
        current_editor.node_parameters_tmp.pop("outputs", None)

    def get_index_from_plug_name(self, plug_name, in_or_out):
        """
        Get the index of a plug by its name.

        :param plug_name (str): The name of the plug to find.
        :param in_or_out (str): Direction of the plug ; "in" for input,
                                "out" for output.

        :return: The zero-based index of the plug if found, None otherwise.
        """
        labels = self.labels_input if in_or_out == "in" else self.labels_output

        return next(
            (
                idx
                for idx, label in enumerate(labels)
                if label.text() == plug_name
            ),
            None,
        )

    def update_node_name(self, new_node_name=None):
        """
        Update the name of the currently selected node in the pipeline.

        Renames a node in the pipeline dictionary, preserving all its
        properties and connections. If the pipeline contains a
        ProcessIteration, ensures the name is prefixed with 'iterated_'.

        :param new_node_name: The new name for the node. If None, retrieves the
                              name from the UI line edit widget. Is not None
                              only when this method is called from an
                              "undo/redo")

        :Emits: value_changed: Signal with node rename details for undo/redo
                               tracking.

        Note:
            Does nothing if the new name already exists in the pipeline.
        """
        old_node_name = self.node_name
        new_node_name = new_node_name or self.line_edit_node_name.text()

        # Ensure ProcessIteration nodes have the correct prefix
        if isinstance(
            self.pipeline.list_process_in_pipeline[0], ProcessIteration
        ):

            if not new_node_name.startswith("iterated_"):
                new_node_name = f"iterated_{new_node_name}"
                self.line_edit_node_name.setText(new_node_name)

        # Check for name conflicts
        if new_node_name in self.pipeline.nodes:
            logger.info(
                f"Node name '{new_node_name}' already exists in pipeline"
            )
            return

        # Perform the rename
        self.pipeline.rename_node(old_node_name, new_node_name)
        renamed_node = self.pipeline.nodes[new_node_name]
        self.rename_subprocesses(renamed_node, new_node_name)
        # Update local state and emit change signal
        self.node_name = new_node_name
        # For undo/redo
        self.value_changed.emit(
            ["node_name", renamed_node, new_node_name, old_node_name]
        )
        self.main_window.statusBar().showMessage(
            f"Brick name '{old_node_name}' has been "
            f"changed to '{new_node_name}'."
        )

    def rename_subprocesses(self, node, parent_node_name):
        """
        Recursively update context names for a node and its subprocesses.

        This method updates the `context_name` attribute throughout a node
        hierarchy, ensuring consistent naming based on the parent context. For
        pipeline processes, it preserves the hierarchical structure while
        incorporating the parent node name.

        The context name follows these rules:
        - Pipeline processes:"Pipeline.{parent_node_name}.{additional_parts}"
        - Non-pipeline processes: "{parent_node_name}"
        - Nested subprocesses are updated recursively

        :param node (Node): The node whose context name will be updated, along
                            with all its subprocesses.
        :param parent_node_name (str): The parent node's name to incorporate
                                       into the context naming hierarchy.
        """
        # Get the current context name, falling back to process name if not set
        context_name = getattr(node.process, "context_name", node.process.name)
        context_parts = context_name.split(".")

        # Update context name based on whether it's a pipeline process
        if context_parts[0] == "Pipeline":
            # Preserve nested structure beyond the parent level
            additional_parts = (
                context_parts[2:] if len(context_parts) >= 3 else []
            )
            node.process.context_name = ".".join(
                ["Pipeline", parent_node_name, *additional_parts]
            )

        else:
            node.process.context_name = parent_node_name

        # Recursively update all subprocesses in pipeline nodes
        if isinstance(node, PipelineNode):

            for name, subnode in node.process.nodes.items():

                if name:  # Skip empty names
                    self.rename_subprocesses(subnode, parent_node_name)

    def update_parameters(self, process=None):
        """
        Update parameter values in the UI from the process traits.

        Synchronizes input and output line edit widgets with the current values
        of the process traits. If no process is provided, uses the current
        process if available. The 'nodes_activation' trait is ignored.
        Undefined trait values are handled gracefully.

        :param process: Optional process node whose parameters should be
                        displayed. If None, uses self.current_process.
        """

        # Resolve process
        if process is None:
            process = getattr(self, "current_process", None)

            if process is None:
                # No node has been clicked, no need to update the widget
                return

        # Update input parameter widgets
        idx = 0

        for name, trait in process.user_traits().items():

            if name == "nodes_activation" or trait.output:
                continue

            if idx >= len(self.line_edit_input):
                break

            try:
                value = getattr(process, name)

            except TraitError:
                value = Undefined

            self.line_edit_input[idx].setText(str(value))
            idx += 1

        # Update output parameter widgets
        idx = 0

        for name, trait in process.traits(output=True).items():

            if idx >= len(self.line_edit_output):
                break

            value = getattr(process, name)
            self.line_edit_output[idx].setText(str(value))
            idx += 1

    def update_plug_value(
        self, in_or_out, plug_name, pipeline, value_type, new_value=None
    ):
        """
        Update the value of a node plug and propagate changes through the
        pipeline.

        The new value is either explicitly provided (typically during
        undo/redo) or read from the corresponding line edit widget and
        evaluated. If the update fails, the previous value is restored in the
        UI and a warning dialog is shown.

        :param in_or_out (str): Direction of the plug - "in" for input plugs,
                                "out" for output plugs.
        :param plug_name (str): Name of the plug to update.
        :param pipeline: The current pipeline instance.
        :param value_type (type): Expected type of the plug value.
        :param new_value (optional): New value for the plug. If None, reads
                                     from the line edit widget (is None except
                                     when this method is called from an
                                     undo/redo)

        Side Effects:
            - Updates the plug value in the pipeline node
            - Updates the corresponding line edit widget text
            - Triggers pipeline node and plug activation updates
            - Emits value_changed signal for undo/redo tracking
            - Displays status message in the main window
            - Shows error dialog on TraitError or OSError

        Note:
            The method uses eval() to parse string input, which handles
            lists, dicts, and other Python literals. Special handling is
            included for '<undefined>' values in dictionaries, which are
            converted to Undefined objects.
        """
        index = self.get_index_from_plug_name(plug_name, in_or_out)

        # Read and evaluate the value from the UI if not explicitly provided
        if new_value is None:

            if in_or_out == "in":
                new_value = self.line_edit_input[index].text()

            elif in_or_out == "out":
                new_value = self.line_edit_output[index].text()

            else:
                new_value = None

            try:
                new_value = eval(new_value)

            # Handle "<undefined>" textual values that break eval()
            # See FIXME below.
            except SyntaxError:
                new_value = new_value.replace("<undefined>", "'<undefined>'")

                try:
                    new_value = eval(new_value)

                except Exception:
                    logger.warning(
                        f"Problem reading the {plug_name} value", exc_info=True
                    )

            except NameError:
                # Keep the original value if evaluation fails due to undefined
                # names
                pass

            except Exception:
                logger.warning(
                    f"Problem reading the {plug_name} value", exc_info=True
                )

            if value_type not in (float, int, str, list):
                value_type = str

        node_name = (
            "" if self.node_name in ("inputs", "outputs") else self.node_name
        )
        node = pipeline.nodes[node_name]
        old_value = node.get_plug_value(plug_name)

        try:

            # Convert '<undefined>' strings to Undefined objects in
            # dictionaries
            # FIXME: This should be expanded to handle all data types, not
            #        just dicts
            if isinstance(new_value, dict):
                new_value = {
                    k: Undefined if v == "<undefined>" else v
                    for k, v in new_value.items()
                }

            node.set_plug_value(plug_name, new_value)

        except (TraitError, OSError) as err:
            msg = QMessageBox()
            msg.setText(str(err))
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(err.__class__.__name__)
            msg.exec_()

            if in_or_out == "in":
                self.line_edit_input[index].setText(str(old_value))

            elif in_or_out == "out":
                self.line_edit_output[index].setText(str(old_value))

            return

        # Propagate the change through the pipeline
        pipeline.update_nodes_and_plugs_activation()

        if in_or_out == "in":
            self.line_edit_input[index].setText(str(new_value))

        elif in_or_out == "out":
            self.line_edit_output[index].setText(str(new_value))

        # Emit undo/redo information
        self.value_changed.emit(
            [
                "plug_value",
                self.node_name,
                old_value,
                plug_name,
                value_type,
                new_value,
            ]
        )
        self.main_window.statusBar().showMessage(
            f"Plug '{plug_name}' of brick '{node_name}' has "
            f"been changed to '{new_value}'."
        )

    def update_plug_value_from_filter(
        self, plug_name, parameters, filter_res_list
    ):
        """
        Update a plug's value based on filtered results.

        Automatically unwraps single-item lists for convenience, setting the
        plug value to the item itself rather than a list containing one item.

        :param plug_name: Name of the plug to update.
        :param parameters: Tuple of (plug_index, pipeline_instance,
                           value_type).
        :param filter_res_list: Filtered file list to set as the plug value.

        Note:
            - Empty lists are preserved as empty lists
            - Single-item lists are unwrapped to the item itself
            - Multi-item lists are kept as lists
        """
        _, pipeline, value_type = parameters

        # Unwrap single-item lists; preserve empty and multi-item lists
        match len(filter_res_list):

            case 0:
                res = []

            case 1:
                res = filter_res_list[0]

            case _:
                res = filter_res_list

        self.update_plug_value("in", plug_name, pipeline, value_type, res)

    def release_process(self):
        """
        Release the process from notification tracking.

        This method is intended to be overridden by subclasses that need
        to implement process release logic. The base implementation is a no-op.

        Note:
            Currently only implemented in CapsuleNodeController.
        """
        pass
