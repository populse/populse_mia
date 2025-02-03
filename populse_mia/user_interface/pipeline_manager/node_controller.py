"""Module to handle the node of a pipeline and its plugs.

:Contains:
    :Class:
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

import os
import sys
from functools import partial

import sip

# capsul imports
from capsul.attributes.completion_engine import ProcessCompletionEngine
from capsul.pipeline.pipeline_nodes import PipelineNode
from capsul.pipeline.process_iteration import ProcessIteration
from capsul.qt_gui.widgets.attributed_process_widget import (
    AttributedProcessWidget,
)
from matplotlib.backends.qt_compat import QtWidgets

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

# Populse_MIA imports
from populse_mia.data_manager.filter import Filter
from populse_mia.data_manager.project import (
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    TAG_FILENAME,
)
from populse_mia.software_properties import Config
from populse_mia.user_interface.data_browser.advanced_search import (
    AdvancedSearch,
)
from populse_mia.user_interface.data_browser.data_browser import (
    TableDataBrowser,
    not_defined_value,
)
from populse_mia.user_interface.data_browser.rapid_search import RapidSearch
from populse_mia.user_interface.pipeline_manager.process_mia import ProcessMIA
from populse_mia.user_interface.pop_ups import (
    PopUpSelectTagCountTable,
    PopUpVisualizedTags,
)

from . import type_editors

if sys.version_info[0] >= 3:
    unicode = str

    def values(d):
        """blabla"""

        return list(d.values())

else:

    def values(d):
        """blabla"""

        return d.values()


class PlugFilter(QWidget):
    """Filter widget used on a node plug.

    The widget displays a browser with the selected files of the database,
    a rapid search and an advanced search to filter these files. Once the
    filtering is done, the result (as a list of files) is set to the plug.

    .. Methods:
        - ok_clicked: set the new value to the node plug and closes the widget
        - reset_search_bar: reset the search bar of the rapid search
        - search_str: update the files to display in the browser
        - set_plug_value: emit a signal to set the file names to the node plug
        - update_tag_to_filter: update the tag to Filter
        - update_tags: update the list of visualized tags
    """

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
        Initialization of the PlugFilter widget

        :param project: current project in the software
        :param scans_list: list of database files to filter
        :param process: process instance of the selected node
        :param node_name: name of the current node
        :param plug_name: name of the selected node plug
        :param node_controller: parent node controller
        :param main_window: parent main window
        """
        super().__init__(None)

        from populse_mia.data_manager.project import COLLECTION_CURRENT
        from populse_mia.user_interface.data_browser.rapid_search import (
            RapidSearch,
        )

        self.project = project
        self.node_controller = node_controller
        self.main_window = main_window
        self.process = process
        self.plug_name = plug_name

        # If the filter is saved in the node plug (not the case now)
        # if hasattr(self.process, 'filters'):
        #    if self.plug_name in self.process.filters.keys():
        #         print("Already a filter for {0} plug of {1} process".format(
        #                 self.plug_name, self.process.name))
        #         # TODO: fill the advanced search with the corresponding
        #          filter:orphan:

        # Verifying that the scan names begin not with a "/" or a "\"
        doc_list = []
        for brick in self.main_window.pipeline_manager.brick_list:
            doc = self.project.session.get_document(COLLECTION_BRICK, brick)
            if doc is not None:
                for key in doc["Output(s)"]:
                    if isinstance(doc["Output(s)"][key], str):
                        if doc["Output(s)"][key] != "":
                            doc_delete = os.path.relpath(
                                doc["Output(s)"][key], self.project.folder
                            )
                            doc_list.append(doc_delete)

        if scans_list:
            scans_list_copy = []
            for scan in scans_list:
                scan_no_pfolder = scan.replace(self.project.folder, "")
                if scan_no_pfolder[0] in ["\\", "/"]:
                    scan_no_pfolder = scan_no_pfolder[1:]
                if scan_no_pfolder not in doc_list:
                    scans_list_copy.append(scan_no_pfolder)

            self.scans_list = scans_list_copy

        # If there is no element in scans_list, this means that all the scans
        # of the database needs to be taken into account
        else:
            self.scans_list = self.project.session.get_documents_names(
                COLLECTION_CURRENT
            )

        self.setWindowTitle("Filter - " + node_name + " - " + plug_name)

        # Graphical components
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

        search_bar_layout = QHBoxLayout()

        self.rapid_search = RapidSearch(self)
        self.rapid_search.textChanged.connect(partial(self.search_str))

        sources_images_dir = Config().getSourceImageDir()
        self.button_cross = QToolButton()
        self.button_cross.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.button_cross.setIcon(
            QIcon(os.path.join(sources_images_dir, "gray_cross.png"))
        )
        self.button_cross.clicked.connect(self.reset_search_bar)

        search_bar_layout.addWidget(self.rapid_search)
        search_bar_layout.addWidget(self.button_cross)

        self.advanced_search = AdvancedSearch(
            self.project,
            self,
            self.scans_list,
            self.node_controller.visibles_tags,
            from_pipeline=True,
        )
        self.advanced_search.show_search()

        push_button_tags = QPushButton("Visualized tags")
        push_button_tags.clicked.connect(self.update_tags)

        self.push_button_tag_filter = QPushButton(TAG_FILENAME)
        self.push_button_tag_filter.clicked.connect(self.update_tag_to_filter)

        push_button_ok = QPushButton("OK")
        push_button_ok.clicked.connect(self.ok_clicked)

        push_button_cancel = QPushButton("Cancel")
        push_button_cancel.clicked.connect(self.close)

        # Layout
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

        screen_resolution = QApplication.instance().desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        self.setMinimumWidth(round(0.6 * width))
        self.setMinimumHeight(round(0.8 * height))

    def ok_clicked(self):
        """Set the new value to the node plug and closes the widget."""

        # To use if the filters are set on plugs, which is not the case
        # if isinstance(self.process, ProcessMIA):
        #     (fields, conditions, values, links, nots) =
        #     self.advanced_search.get_filters(False)
        #
        #
        #     plug_filter = Filter(None, nots, values, fields,
        #     links, conditions, "")
        #     self.process.filters[self.plug_name] = plug_filter

        self.set_plug_value()
        self.close()

    def reset_search_bar(self):
        """Reset the search bar of the rapid search."""
        self.rapid_search.setText("")
        self.advanced_search.rows = []
        self.advanced_search.show_search()

        # All rows reput
        old_scan_list = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.scans_list
        self.table_data.scans_to_search = self.scans_list
        self.table_data.update_visualized_rows(old_scan_list)

    def search_str(self, str_search):
        """Update the files to display in the browser.
        :param str_search: string typed in the rapid search
        """
        old_scan_list = self.table_data.scans_to_visualize

        # Every scan taken if empty search
        if str_search == "":
            return_list = self.table_data.scans_to_search
        else:
            # Scans with at least a not defined value
            if str_search == not_defined_value:
                filter = self.prepare_not_defined_filter(
                    self.project.session.get_shown_tags()
                )

            # Scans matching the search
            else:
                filter = self.rapid_search.prepare_filter(
                    str_search,
                    self.project.session.get_shown_tags(),
                    self.table_data.scans_to_search,
                )

            generator = self.project.session.filter_documents(
                COLLECTION_CURRENT, filter
            )

            # Creating the list of scans
            return_list = [getattr(scan, TAG_FILENAME) for scan in generator]

        self.table_data.scans_to_visualize = return_list
        self.advanced_search.scans_list = return_list

        # Rows updated
        self.table_data.update_visualized_rows(old_scan_list)

    def set_plug_value(self):
        """Emit a signal to set the file names to the node plug."""

        result_names = []
        points = self.table_data.selectedIndexes()

        # If the user has selected some items
        if points:
            for point in points:
                row = point.row()
                tag_name = self.push_button_tag_filter.text()
                if tag_name.startswith("&"):
                    tag_name = tag_name[1:]
                # We get the FileName of the scan from the first row
                scan_name = self.table_data.item(row, 0).text()
                value = self.project.session.get_value(
                    COLLECTION_CURRENT, scan_name, tag_name
                )
                if tag_name == TAG_FILENAME:
                    value = os.path.abspath(
                        os.path.join(self.project.folder, value)
                    )
                result_names.append(value)
        else:
            filter = self.table_data.get_current_filter()
            for i in range(len(filter)):
                scan_name = filter[i]
                tag_name = self.push_button_tag_filter.text()
                value = self.project.session.get_value(
                    COLLECTION_CURRENT, scan_name, tag_name
                )
                if tag_name == TAG_FILENAME:
                    value = os.path.abspath(
                        os.path.join(self.project.folder, value)
                    )
                result_names.append(value)

        self.plug_value_changed.emit(result_names)

    def update_tag_to_filter(self):
        """Update the tag to Filter."""

        popUp = PopUpSelectTagCountTable(
            self.project,
            self.node_controller.visibles_tags,
            self.push_button_tag_filter.text(),
        )
        if popUp.exec_():
            self.push_button_tag_filter.setText(popUp.selected_tag)

    def update_tags(self):
        """Update the list of visualized tags."""

        dialog = QDialog()
        visualized_tags = PopUpVisualizedTags(
            self.project, self.node_controller.visibles_tags
        )
        layout = QVBoxLayout()
        layout.addWidget(visualized_tags)
        buttons_layout = QHBoxLayout()
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        buttons_layout.addWidget(buttons)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.show()
        dialog.setMinimumHeight(600)
        dialog.setMinimumWidth(600)
        if dialog.exec():
            new_visibilities = []
            for x in range(visualized_tags.list_widget_selected_tags.count()):
                visible_tag = visualized_tags.list_widget_selected_tags.item(
                    x
                ).text()
                new_visibilities.append(visible_tag)
            new_visibilities.append(TAG_FILENAME)
            self.table_data.update_visualized_columns(
                self.node_controller.visibles_tags, new_visibilities
            )
            self.node_controller.visibles_tags = new_visibilities
            for row in self.advanced_search.rows:
                fields = row[2]
                fields.clear()
                for visible_tag in new_visibilities:
                    fields.addItem(visible_tag)
                fields.model().sort(0)
                fields.addItem("All visualized tags")


class AttributesFilter(PlugFilter):
    """Filter widget used on an attributes set for completion.

    The widget displays a browser with the selected files of the database,
    a rapid search and an advanced search to filter these files. Once the
    filtering is done, the result (as a list of files) is set to the plug.

    .. Methods:
        - ok_clicked: close the widget
    """

    attributes_selected = pyqtSignal(dict)

    def ok_clicked(self):
        """Close the widget"""
        self.close()
        attributes = {}

        points = self.table_data.selectedIndexes()

        # If the user has selected some items
        if points:
            for point in points:
                row = point.row()
                for tag_name in self.project.session.get_fields_names(
                    COLLECTION_CURRENT
                ):
                    # We get the FileName of the scan from the first row
                    scan_name = self.table_data.item(row, 0).text()
                    value = self.project.session.get_value(
                        COLLECTION_CURRENT, scan_name, tag_name
                    )
                    attributes.setdefault(tag_name, []).append(value)
        else:
            filter = self.table_data.get_current_filter()
            for i in range(len(filter)):
                scan_name = filter[i]
                for tag_name in self.project.session.get_fields_names(
                    COLLECTION_CURRENT
                ):
                    value = self.project.session.get_value(
                        COLLECTION_CURRENT, scan_name, tag_name
                    )
                    attributes.setdefault(tag_name, []).append(value)

        self.attributes_selected.emit(attributes)


# Node controller V2 style
class CapsulNodeController(QWidget):
    """
    Implementation of NodeController using Capsul AttributedProcessWidget
    widget.

    .. Methods:
        - display_parameters: display the parameters of the selected node
        - static_release: remove notification
        - release_process: remove notification from process
        - update_parameters: update the parameters values
        - parameters_changed: emit the value_changed signal
        - update_node_name: change the name of the selected node and updates
        the pipeline
        - rename_subprocesses: change the name of a node
        - filter_attributes: display a filter widget
        - update_attributes_from_filter: update attributes from filter widget
    """

    value_changed = pyqtSignal(list)

    def __init__(self, project, scan_list, pipeline_manager_tab, main_window):
        super().__init__()
        self.project = project
        self.scan_list = scan_list
        self.main_window = main_window
        self.node_name = ""
        self.visibles_tags = []
        self.pipeline = (
            pipeline_manager_tab.pipelineEditorTabs.get_current_pipeline()
        )

        # Layouts
        v_box_final = QVBoxLayout()
        self.setLayout(v_box_final)
        self.process_widget = None

        # Node name
        hlayout = QHBoxLayout()
        label_node_name = QLabel()
        label_node_name.setText("Node name:")

        self.line_edit_node_name = QLineEdit()
        hlayout.addWidget(label_node_name)
        hlayout.addWidget(self.line_edit_node_name)
        v_box_final.addLayout(hlayout)

    def display_parameters(self, node_name, process, pipeline):
        """Display the parameters of the selected node.

        The node parameters are read and line labels/line edits/push buttons
        are created for each of them. This methods consists mainly in widget
        and layout organization.

        :param node_name: name of the node
        :param process: process of the node
        :param pipeline: current pipeline
        """
        self.node_name = node_name
        self.pipeline = pipeline

        # The pipeline global inputs and outputs node name cannot be modified
        if self.node_name not in ("inputs", "outputs"):
            self.line_edit_node_name.setText(self.node_name)
            self.line_edit_node_name.setReadOnly(False)
            self.line_edit_node_name.returnPressed.connect(
                self.update_node_name
            )
        else:
            self.line_edit_node_name.setText("Pipeline inputs/outputs")
            self.line_edit_node_name.setReadOnly(True)

        if self.process_widget:
            # item = self.layout().takeAt(1)
            self.static_release(
                self.process_widget.attributed_process, self.parameters_changed
            )
            self.process_widget.deleteLater()
            # del item
            self.process_widget = None

        # get the list of inputs connected from outputs of upstream nodes
        # in order to disable their "filter" file button
        node = pipeline.nodes.get(node_name)
        connected_inputs = set()
        if node is not None:
            for plug_name, plug in node.plugs.items():
                if not plug.output and plug.links_from:
                    connected_inputs.add(plug_name)

        userlevel = Config().get_user_level()
        self.process = process

        # force initializing the completion engine
        ProcessCompletionEngine.get_completion_engine(process)
        # fmt: off
        self.process_widget = AttributedProcessWidget(
            process,
            override_control_types={
                "File": type_editors.PopulseFileControlWidget,
                "Directory": type_editors.PopulseDirectoryControlWidget,
                "List_File": type_editors.
                PopulseOffscreenListFileControlWidget,
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
        # fmt: on

        if hasattr(process, "completion_engine"):
            compl = process.completion_engine
            atts = compl.get_attribute_values()

            if len(atts.user_traits()) != 0:
                btn = QPushButton("Filter")
                btn.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)
                btn.clicked.connect(self.filter_attributes)
                self.process_widget.attrib_widget.layout().insertWidget(0, btn)

        self.layout().addWidget(self.process_widget)
        self.process.on_trait_change(self.parameters_changed, dispatch="ui")
        # this cannot be done in __del__ since the C++ part will be already
        # destroyed by then.
        # However this signal seems never to be emitted, and I don't understand
        # why. So release_process() has to be called manually from the
        # pipeline manager. Sigh.
        # self.process_widget.destroyed.connect(partial(
        #                                             self.static_release,
        #                                             process,
        #                                             self.parameters_changed))

    @staticmethod
    def static_release(process, param_changed):
        """Remove notification"""
        process.on_trait_change(param_changed, remove=True)

    def release_process(self):
        """Remove notification from process"""
        if hasattr(self, "process"):
            self.process.on_trait_change(self.parameters_changed, remove=True)
        try:
            if not sip.isdeleted(self):
                self.value_changed.disconnect()
        except TypeError:
            pass  # it was not connected: OK

    def update_parameters(self, process=None):
        """Update the parameters values.

        Does nothing any longer since the controller widget already reacts to
        changes in the process parameters.

        :param process: process of the node
        """
        pass

    def parameters_changed(self, _, plug_name, old_value, new_value):
        """Emit the value_changed signal."""

        # plug_name_type = type(plug_name)
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

    def update_node_name(
        self,
        new_node_name=None,
        old_node_name=None,
        from_undo=False,
        from_redo=False,
    ):
        """Change the name of the selected node and updates the pipeline.

        Because the nodes are stored in a dictionary, we have to create
        a new node that has the same traits as the selected one and create
        new links that are the same than the selected node.

        :param new_node_name: new node name (is None except when this method
         is called from an undo/redo)
        :param old_node_name: old node name (is None except when this method
         is called from an undo/redo)
        :param from_undo: boolean, True if the action has been made using an
         undo
        :param from_redo: boolean, True if the action has been made using a
         redo
        """
        if not new_node_name:
            new_node_name = self.line_edit_node_name.text()

        if not old_node_name:
            old_node_name = self.node_name

        if isinstance(self.process, ProcessIteration):
            if not new_node_name.startswith("iterated_"):
                new_node_name = "iterated_" + new_node_name
                self.line_edit_node_name.setText(new_node_name)

        if new_node_name in list(self.pipeline.nodes.keys()):
            print(
                "\nUpdate of the node name from '{0}' to '{1}': impossible, "
                "the node '{1}' already exists !".format(
                    old_node_name, new_node_name
                )
            )

        else:
            self.pipeline.rename_node(old_node_name, new_node_name)
            self.rename_subprocesses(
                self.pipeline.nodes[new_node_name], new_node_name
            )

            # Updating the node_name attribute
            self.node_name = new_node_name
            self.pipeline.update_nodes_and_plugs_activation()

            # To undo/redo
            self.value_changed.emit(
                [
                    "node_name",
                    self.pipeline.nodes[new_node_name],
                    new_node_name,
                    old_node_name,
                ]
            )

            # For history
            history_maker = ["update_node_name"]

            if from_undo:
                # TODO: next line is strange!
                history_maker.append

            else:
                history_maker.append(self.pipeline.nodes[new_node_name])
                history_maker.append(new_node_name)
                history_maker.append(old_node_name)
            # fmt:off
            (
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor().update_history
            )(history_maker, from_undo, from_redo)
            # fmt: on

            self.main_window.statusBar().showMessage(
                'Node name "{}" has been changed to "{}".'.format(
                    old_node_name, new_node_name
                )
            )

    def rename_subprocesses(self, node, parent_node_name):
        """Change the name of a node."""

        if (
            getattr(node.process, "context_name", node.process.name).split(
                "."
            )[0]
            == "Pipeline"
        ):
            if (
                len(
                    getattr(
                        node.process, "context_name", node.process.name
                    ).split(".")
                )
                >= 3
            ):
                node.process.context_name = (
                    "Pipeline."
                    + parent_node_name
                    + "."
                    + ".".join(
                        getattr(
                            node.process, "context_name", node.process.name
                        ).split(".")[2:]
                    )
                )
            else:
                node.process.context_name = "Pipeline." + parent_node_name
        else:
            node.process.context_name = parent_node_name

        if isinstance(node, PipelineNode):
            for name, subnode in node.process.nodes.items():
                if name == "":
                    continue
                else:
                    self.rename_subprocesses(subnode, parent_node_name)

    def filter_attributes(self):
        """Display a filter widget."""
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

    def update_attributes_from_filter(self, attributes):
        """Update attributes from filter widget"""
        compl = self.process.completion_engine
        atts = compl.get_attribute_values()
        num_set = 0
        for name, value in attributes.items():
            if atts.trait(name):
                if isinstance(getattr(atts, name), list):
                    setattr(atts, name, value)

                else:
                    setattr(atts, name, value[0])

                num_set += 1

        if num_set == 0 and len(attributes) != 0:
            mbox_icon = QMessageBox.Information
            mbox_title = "Unmatching tags / attributes"
            mbox_text = (
                "The selected data tags do not match the expected "
                "attributes set for process parameters completion"
            )
            mbox = QMessageBox(mbox_icon, mbox_title, mbox_text)
            Qt.QTimer.singleShot(2000, mbox.accept)
            mbox.exec()


class FilterWidget(QWidget):
    """Filter widget used on a Input_Filter process.

    The widget displays a browser with the selected files of the database,
    a rapid search and an advanced search to filter these files. Once the
    filtering is done, the filter is saved in the process.

    .. Methods:
        - layout_view: create the layout
        - ok_clicked: set the filter to the process and closes the widget
        - reset_search_bar: reset the search bar of the rapid search
        - search_str: update the files to display in the browser
        - update_tag_to_filter: update the tag to Filter
        - update_tags: update the list of visualized tags
    """

    def __init__(self, project, node_name, node, main_window):
        """Initialization of the Filter Widget.

        :param project: current project in the software
        :param node_name: name of the current node
        :param node: instance of the corresponding Input_Filter node
        :param main_window: parent main window
        """

        super().__init__(None)

        self.setWindowTitle("Filter - " + node_name)
        self.project = project
        self.visible_tags = self.project.session.get_shown_tags()
        self.node = node
        self.process = node.process
        self.main_window = main_window

        scan_list = []
        # The scan list to filter corresponds to the input of the Input Filter
        if self.process.input and self.process.input is not Undefined:
            for scan in self.process.input:
                path, file_name = os.path.split(scan)
                path, second_folder = os.path.split(path)
                first_folder = os.path.basename(path)
                database_file = os.path.join(
                    first_folder, second_folder, file_name
                )
                scan_list.append(database_file)

        self.scan_list = scan_list

        # Graphical components
        self.table_data = TableDataBrowser(
            self.project, self, self.visible_tags, False, False
        )

        # Reducing the list of scans to selection
        all_scans = self.table_data.scans_to_visualize

        self.table_data.scans_to_visualize = self.scan_list
        self.table_data.scans_to_search = self.scan_list
        self.table_data.update_visualized_rows(all_scans)

        # Filter information
        filter_to_apply = node.process.filter

        # Search
        self.rapid_search = RapidSearch(self)
        if filter_to_apply.search_bar:
            self.rapid_search.setText(filter_to_apply.search_bar)
        self.rapid_search.textChanged.connect(partial(self.search_str))

        self.advanced_search = AdvancedSearch(
            self.project,
            self,
            self.scan_list,
            self.visible_tags,
            from_pipeline=True,
        )
        self.advanced_search.show_search()
        self.advanced_search.apply_filter(filter_to_apply)

        # Initialize Qt objects
        self.button_cross = QToolButton()
        self.push_button_tag_filter = QPushButton(TAG_FILENAME)

        self.layout_view()

    def layout_view(self):
        """Create the layout."""

        sources_images_dir = Config().getSourceImageDir()

        self.button_cross.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.button_cross.setIcon(
            QIcon(os.path.join(sources_images_dir, "gray_cross.png"))
        )
        self.button_cross.clicked.connect(self.reset_search_bar)

        search_bar_layout = QHBoxLayout()
        search_bar_layout.addWidget(self.rapid_search)
        search_bar_layout.addWidget(self.button_cross)

        push_button_tags = QPushButton("Visualized tags")
        push_button_tags.clicked.connect(self.update_tags)

        self.push_button_tag_filter.clicked.connect(self.update_tag_to_filter)

        push_button_ok = QPushButton("OK")
        push_button_ok.clicked.connect(self.ok_clicked)

        push_button_cancel = QPushButton("Cancel")
        push_button_cancel.clicked.connect(self.close)

        # Layout
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

        screen_resolution = QApplication.instance().desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        self.setMinimumWidth(round(0.6 * width))
        self.setMinimumHeight(round(0.8 * height))

    def ok_clicked(self):
        """Set the filter to the process and closes the widget."""
        if isinstance(self.process, ProcessMIA):
            (
                fields,
                conditions,
                values,
                links,
                nots,
            ) = self.advanced_search.get_filters(False)
            filt = Filter(
                None,
                nots,
                values,
                fields,
                links,
                conditions,
                self.rapid_search.text(),
            )
            self.process.filter = filt

        # self.set_output_value()
        self.close()

    def reset_search_bar(self):
        """Reset the search bar of the rapid search."""
        self.rapid_search.setText("")
        self.advanced_search.rows = []
        self.advanced_search.show_search()

        # All rows reput
        old_scan_list = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.scan_list
        self.table_data.scans_to_search = self.scan_list
        self.table_data.update_visualized_rows(old_scan_list)

    def search_str(self, str_search):
        """Update the files to display in the browser.

        :param str_search: string typed in the rapid search
        """

        old_scan_list = self.table_data.scans_to_visualize

        # Every scan taken if empty search
        if str_search == "":
            return_list = self.table_data.scans_to_search
        else:
            # Scans with at least a not defined value
            if str_search == not_defined_value:
                filter = self.prepare_not_defined_filter(
                    self.project.session.get_shown_tags()
                )
            # Scans matching the search
            else:
                filter = self.rapid_search.prepare_filter(
                    str_search,
                    self.project.session.get_shown_tags(),
                    old_scan_list,
                )

            generator = self.project.session.filter_documents(
                COLLECTION_CURRENT, filter
            )

            # Creating the list of scans
            return_list = [getattr(scan, TAG_FILENAME) for scan in generator]

        self.table_data.scans_to_visualize = return_list
        self.advanced_search.scans_list = return_list

        # Rows updated
        self.table_data.update_visualized_rows(old_scan_list)

    #    def set_output_value(self):
    #        """Set the output of the filter to the output of the node."""
    #
    #        result_names = []
    #        filter = self.table_data.get_current_filter()
    #        for i in range(len(filter)):
    #            scan_name = filter[i]
    #            tag_name = self.push_button_tag_filter.text().replace('&', '')
    #            value = self.project.session.get_value(COLLECTION_CURRENT,
    #                                                   scan_name, tag_name)
    #            if tag_name == TAG_FILENAME:
    #                value = os.path.abspath(os.path.join(self.project.folder,
    #                                                     value))
    #            result_names.append(value)
    #
    #        result_files = []
    #        for result_name in result_names:
    #            full_path = os.path.abspath(os.path.join(self.project.folder,
    #                                                     result_name))
    #            result_files.append(full_path)
    #
    #        self.node.set_plug_value("output", result_files)

    def update_tag_to_filter(self):
        """Update the tag to Filter."""

        pop_up = PopUpSelectTagCountTable(
            self.project, self.visible_tags, self.push_button_tag_filter.text()
        )
        if pop_up.exec_():
            self.push_button_tag_filter.setText(pop_up.selected_tag)

    def update_tags(self):
        """Update the list of visualized tags."""

        dialog = QDialog()
        visualized_tags = PopUpVisualizedTags(self.project, self.visible_tags)
        layout = QVBoxLayout()
        layout.addWidget(visualized_tags)
        buttons_layout = QHBoxLayout()
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        buttons_layout.addWidget(buttons)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.show()
        dialog.setMinimumHeight(600)
        dialog.setMinimumWidth(600)
        if dialog.exec():
            new_visibilities = []
            for x in range(visualized_tags.list_widget_selected_tags.count()):
                visible_tag = visualized_tags.list_widget_selected_tags.item(
                    x
                ).text()
                new_visibilities.append(visible_tag)
            new_visibilities.append(TAG_FILENAME)
            self.table_data.update_visualized_columns(
                self.visible_tags, new_visibilities
            )
            # self.node_controller.visibles_tags = new_visibilities
            for row in self.advanced_search.rows:
                fields = row[2]
                fields.clear()
                for visible_tag in new_visibilities:
                    fields.addItem(visible_tag)
                fields.model().sort(0)
                fields.addItem("All visualized tags")


# Node controller V1 style
class NodeController(QWidget):
    """
    Allow to change the input and output values of a pipeline node

    .. Methods:
        - clearLayout: clear the layouts of the widget
        - display_filter: display a filter widget
        - display_parameters: display the parameters of the selected node
        - get_index_from_plug_name: return the index of the plug label.
        - update_node_name: update the name of the selected node
        - rename_subprocesses: change the name of a node
        - update_parameters: update the parameters values
        - update_plug_value: update the value of a node plug
        - update_plug_value_from_filter: update the plug value from a filter
           result
        - release_process: remove notification from process (not implemented)

    """

    value_changed = pyqtSignal(list)

    def __init__(self, project, scan_list, pipeline_manager_tab, main_window):
        """
        Initialization of the Node Controller

        :param project: current project in the software
        :param scan_list: list of the selected database files
        :param pipeline_manager_tab: parent widget
        :param main_window: main window of the software
        """

        super().__init__(pipeline_manager_tab)
        self.project = project
        self.scan_list = scan_list
        self.main_window = main_window
        self.node_name = ""
        self.pipeline = (
            pipeline_manager_tab.pipelineEditorTabs.get_current_pipeline()
        )

        # Layouts
        self.v_box_final = QVBoxLayout()
        self.h_box_node_name = QHBoxLayout()

    def clearLayout(self, layout):
        """Clear the layouts of the widget.

        :param layout: widget with a layout
        """

        for i in reversed(range(len(layout.children()))):
            if type(layout.layout().itemAt(i)) == QtWidgets.QWidgetItem:
                layout.layout().itemAt(i).widget().setParent(None)
            if (
                type(layout.layout().itemAt(i)) == QtWidgets.QHBoxLayout
                or type(layout.layout().itemAt(i)) == QtWidgets.QVBoxLayout
            ):
                layout.layout().itemAt(i).deleteLater()
                for j in reversed(range(len(layout.layout().itemAt(i)))):
                    layout.layout().itemAt(i).itemAt(j).widget().setParent(
                        None
                    )

        if layout.layout() is not None:
            sip.delete(layout.layout())

    def display_filter(self, node_name, plug_name, parameters, process):
        """Display a filter widget.

        :param node_name: name of the node
        :param plug_name: name of the plug
        :param parameters: tuple containing the index of the plug, the current
                           pipeline instance and the type of the plug value
        :param process: process of the node
        """
        self.pop_up = PlugFilter(
            self.project,
            self.scan_list,
            process,
            node_name,
            plug_name,
            self,
            self.main_window,
        )
        self.pop_up.show()
        self.pop_up.plug_value_changed.connect(
            partial(self.update_plug_value_from_filter, plug_name, parameters)
        )

    # def display_parameters(self, node_name: object,
    #                        process: object, pipeline: object) -> object:
    def display_parameters(self, node_name, process, pipeline):
        """Display the parameters of the selected node.

        The node parameters are read and line labels/line edits/push buttons
        are created for each of them. This methods consists mainly in widget
        and layout organization.

        :param node_name: name of the node
        :param process: process of the node
        :param pipeline: current pipeline
        """
        self.node_name = node_name
        self.current_process = process

        self.line_edit_input = []
        self.line_edit_output = []
        self.labels_input = []
        self.labels_output = []

        # Refreshing the layouts
        if len(self.children()) > 0:
            self.clearLayout(self)

        self.v_box_final = QVBoxLayout()

        # Node name
        label_node_name = QLabel()
        label_node_name.setText("Node name:")

        self.line_edit_node_name = QLineEdit()
        self.pipeline = pipeline
        # The pipeline global inputs and outputs node name cannot be modified
        if self.node_name not in ("inputs", "outputs"):
            self.line_edit_node_name.setText(self.node_name)
            self.line_edit_node_name.returnPressed.connect(
                self.update_node_name
            )

        else:
            self.line_edit_node_name.setText("Pipeline inputs/outputs")
            self.line_edit_node_name.setReadOnly(True)

        self.h_box_node_name = QHBoxLayout()
        self.h_box_node_name.addWidget(label_node_name)
        self.h_box_node_name.addWidget(self.line_edit_node_name)

        # Inputs
        self.button_group_inputs = QGroupBox("Inputs")
        self.v_box_inputs = QVBoxLayout()
        idx = 0

        for name, trait in process.user_traits().items():
            if name == "nodes_activation":
                continue

            if trait.userlevel is not None and trait.userlevel > 0:
                continue

            if not trait.output:
                label_input = QLabel()
                label_input.setText(str(name))
                self.labels_input.insert(idx, label_input)
                try:
                    value = getattr(process, name)
                except TraitError:
                    value = Undefined
                trait_type = trait_ids(process.trait(name))

                self.line_edit_input.insert(idx, QLineEdit())
                self.line_edit_input[idx].setText(str(value))
                self.line_edit_input[idx].returnPressed.connect(
                    partial(
                        self.update_plug_value,
                        "in",
                        name,
                        pipeline,
                        type(value),
                    )
                )

                h_box = QHBoxLayout()
                h_box.addWidget(label_input)
                h_box.addWidget(self.line_edit_input[idx])

                # Adding the possibility to filter pipeline global
                # inputs except if the input is "database_scans"
                # which means that the scans will be filtered with InputFilter
                if self.node_name == "inputs" and name != "database_scans":
                    if (
                        "File" in trait_type
                        or "List_File" in trait_type
                        or "Any" in trait_type
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

                idx += 1

        self.button_group_inputs.setLayout(self.v_box_inputs)

        # Outputs
        self.button_group_outputs = QGroupBox("Outputs")
        self.v_box_outputs = QVBoxLayout()
        idx = 0
        for name, trait in process.traits(output=True).items():
            if trait.userlevel is not None and trait.userlevel > 0:
                continue

            label_output = QLabel()
            label_output.setText(str(name))
            self.labels_output.insert(idx, label_output)

            value = getattr(process, name)
            trait_type = trait_ids(process.trait(name))

            self.line_edit_output.insert(idx, QLineEdit())
            self.line_edit_output[idx].setText(str(value))
            self.line_edit_output[idx].returnPressed.connect(
                partial(
                    self.update_plug_value, "out", name, pipeline, type(value)
                )
            )

            h_box = QHBoxLayout()
            h_box.addWidget(label_output)
            h_box.addWidget(self.line_edit_output[idx])

            self.v_box_outputs.addLayout(h_box)

            idx += 1

        self.button_group_outputs.setLayout(self.v_box_outputs)

        self.v_box_final.addLayout(self.h_box_node_name)
        self.v_box_final.addWidget(self.button_group_inputs)
        self.v_box_final.addWidget(self.button_group_outputs)
        # fmt: off
        (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor
        )().node_parameters_tmp[node_name] = {}

        (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor
        )().node_parameters_tmp[node_name]["inputs"] = [
            x.text() for x in self.line_edit_input
        ]

        (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor
        )().node_parameters_tmp[node_name]["outputs"] = [
            x.text() for x in self.line_edit_output
        ]

        if (
            "outputs" in
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor().node_parameters_tmp
        ):
            del (
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor().node_parameters_tmp["outputs"]
            )
        # fmt: on

        # Commented on January, 4th 2020
        # if self.main_window.pipeline_manager.pipelineEditorTabs\
        # .get_current_editor().node_parameters_tmp ==  \
        #         self.main_window.pipeline_manager.pipelineEditorTabs\
        # .get_current_editor().node_parameters and \
        #         self.main_window.pipeline_manager.test_init and \
        #         self.main_window.pipeline_manager.pipelineEditorTabs\
        #                 .get_current_editor().initialized:
        #     self.main_window.pipeline_manager.run_pipeline_action \
        #         .setDisabled(False)
        # else:
        #    self.main_window.pipeline_manager.run_pipeline_action\
        #         .setDisabled(True)
        # if self.main_window.pipeline_manager.iterationTable\
        #         .check_box_iterate.isChecked():
        #     self.main_window.pipeline_manager.run_pipeline_action\
        #         .setDisabled(False)

        self.main_window.pipeline_manager.run_pipeline_action.setDisabled(
            False
        )
        # End - commented on January, 4th 2020

        self.setLayout(self.v_box_final)

    def get_index_from_plug_name(self, plug_name, in_or_out):
        """Return the index of the plug label.

        :param plug_name: name of the plug
        :param in_or_out: "in" if the plug is an input plug, "out" else
        :return: the corresponding index
        """

        if in_or_out == "in":
            for idx, label in enumerate(self.labels_input):
                if label.text() == plug_name:
                    return idx

        else:
            for idx, label in enumerate(self.labels_output):
                if label.text() == plug_name:
                    return idx

    def update_node_name(self, new_node_name=None):
        """Change the name of the selected node and updates the pipeline.

        Because the nodes are stored in a dictionary, we have to create
        a new node that has the same traits as the selected one and create
        new links that are the same than the selected node.

        :param new_node_name: new node name (is None except when this method
                              is called from an undo/redo)
        """
        # Copying the old node
        old_node_name = self.node_name

        if not new_node_name:
            new_node_name = self.line_edit_node_name.text()

        if isinstance(
            self.pipeline.list_process_in_pipeline[0], ProcessIteration
        ):
            if not new_node_name.startswith("iterated_"):
                new_node_name = "iterated_" + new_node_name
                self.line_edit_node_name.setText(new_node_name)

        if new_node_name in list(self.pipeline.nodes.keys()):
            print("Node name already in pipeline")

        else:
            self.pipeline.rename_node(old_node_name, new_node_name)
            self.rename_subprocesses(
                self.pipeline.nodes[new_node_name], new_node_name
            )

            # Updating the node_name attribute
            self.node_name = new_node_name

            # To undo/redo
            self.value_changed.emit(
                [
                    "node_name",
                    self.pipeline.nodes[new_node_name],
                    new_node_name,
                    old_node_name,
                ]
            )

            self.main_window.statusBar().showMessage(
                'Node name "{}" has been changed to "{}".'.format(
                    old_node_name, new_node_name
                )
            )

    def rename_subprocesses(self, node, parent_node_name):
        """Change the name of a node."""

        if (
            getattr(node.process, "context_name", node.process.name).split(
                "."
            )[0]
            == "Pipeline"
        ):
            if (
                len(
                    getattr(
                        node.process, "context_name", node.process.name
                    ).split(".")
                )
                >= 3
            ):
                node.process.context_name = (
                    "Pipeline."
                    + parent_node_name
                    + "."
                    + ".".join(
                        getattr(
                            node.process, "context_name", node.process.name
                        ).split(".")[2:]
                    )
                )
            else:
                node.process.context_name = "Pipeline." + parent_node_name
        else:
            node.process.context_name = parent_node_name

        if isinstance(node, PipelineNode):
            for name, subnode in node.process.nodes.items():
                if name == "":
                    continue
                else:
                    self.rename_subprocesses(subnode, parent_node_name)

    def update_parameters(self, process=None):
        """Update the parameters values.

        :param process: process of the node
        """

        # commented on January, 4th 2020
        # self.main_window.pipeline_manager.run_pipeline_action.setDisabled(
        #                                                                True)

        if process is None:
            try:
                process = self.current_process
            except AttributeError:
                # if no node has been clicked, no need to update the widget
                return

        idx = 0
        for name, trait in process.user_traits().items():
            if name == "nodes_activation":
                continue
            if not trait.output:
                try:
                    value = getattr(process, name)
                except TraitError:
                    value = Undefined
                if idx < len(self.line_edit_input):
                    self.line_edit_input[idx].setText(str(value))
                    idx += 1

        idx = 0

        for name, trait in process.traits(output=True).items():
            value = getattr(process, name)
            if idx < len(self.line_edit_output):
                self.line_edit_output[idx].setText(str(value))
                idx += 1

        # self.main_window.pipeline_manager.pipelineEditorTabs\
        #     .update_current_node()

    def update_plug_value(
        self, in_or_out, plug_name, pipeline, value_type, new_value=None
    ):
        """Update the value of a node plug.

        :param in_or_out: "in" if the plug is an input plug, "out" else
        :param plug_name: name of the plug
        :param pipeline: current pipeline
        :param value_type: type of the plug value
        :param new_value: new value for the plug (is None except when this
                          method is called from an undo/redo)
        """

        index = self.get_index_from_plug_name(plug_name, in_or_out)

        # Reading the value from the plug's line edit
        if not new_value:
            if in_or_out == "in":
                new_value = self.line_edit_input[index].text()

            elif in_or_out == "out":
                new_value = self.line_edit_output[index].text()

            else:
                new_value = None

            try:
                new_value = eval(new_value)

            # We try to handle the undefined value with the eval() function
            # See FixME below.
            except SyntaxError:
                new_value = new_value.replace("<undefined>", "'<undefined>'")

                try:
                    new_value = eval(new_value)

                except Exception as err:
                    print(f"{err.__class__}: {err}.")

            except NameError:
                pass

            except Exception as err:
                print(f"{err.__class__}: {err}.")

            # except NameError:
            #    print("NameError for value {0}".format(new_value))
            # except SyntaxError:
            #    pass
            #    print("SynthaxError for value {0}".format(new_value))

            if value_type not in [float, int, str, list]:
                value_type = str

        if self.node_name in ["inputs", "outputs"]:
            node_name = ""

        else:
            node_name = self.node_name

        old_value = pipeline.nodes[node_name].get_plug_value(plug_name)

        try:
            # FIXME:Since we replace, above, "<undefined>" with "<undefined>"
            # in order to handle syntax error with eval() we should handle
            # all cases here (big job).
            # For the moment we manage only the dictionary
            if isinstance(new_value, dict):
                new_value = {
                    k: Undefined if v == "<undefined>" else v
                    for k, v in new_value.items()
                }
            pipeline.nodes[node_name].set_plug_value(plug_name, new_value)

        except (TraitError, OSError) as err:
            msg = QMessageBox()
            msg.setText(f"{err}")
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(err.__class__.__name__)
            msg.exec_()

            if in_or_out == "in":
                self.line_edit_input[index].setText(str(old_value))
            elif in_or_out == "out":
                self.line_edit_output[index].setText(str(old_value))
            return

        # Update pipeline to "propagate" the node value
        pipeline.update_nodes_and_plugs_activation()

        if in_or_out == "in":
            self.line_edit_input[index].setText(str(new_value))
        elif in_or_out == "out":
            self.line_edit_output[index].setText(str(new_value))

        # To undo/redo
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
            'Plug "{}" of node "{}" has been changed to "{}".'.format(
                plug_name, node_name, new_value
            )
        )

    def update_plug_value_from_filter(
        self, plug_name, parameters, filter_res_list
    ):
        """Update the plug value from a filter result.

        :param plug_name: name of the plug
        :param parameters: tuple containing the index of the plug, the current
                           pipeline instance and the type of the plug value
        :param filter_res_list: list of the filtered files
        """

        pipeline = parameters[1]
        value_type = parameters[2]

        # If the list contains only one element, setting
        # this element as the plug value
        len_list = len(filter_res_list)

        if len_list > 1:
            res = filter_res_list

        elif len_list == 1:
            res = filter_res_list[0]

        else:
            res = []

        self.update_plug_value("in", plug_name, pipeline, value_type, res)

    def release_process(self):
        """
        Remove notification from process
        """
        # only implemented in CapsulNodeController
        pass
