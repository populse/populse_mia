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

from populse_mia.data_manager.project import COLLECTION_CURRENT, TAG_FILENAME
from populse_mia.software_properties import Config

# MIA imports
from populse_mia.user_interface.pipeline_manager.process_mia import ProcessMIA
from populse_mia.user_interface.pop_ups import (
    ClickableLabel,
    PopUpSelectIteration,
    PopUpSelectTagCountTable,
)


class IterationTable(QWidget):
    """Widget that handles pipeline iteration.

    .. Methods:
        - add_tag: adds a tag to visualize in the iteration table
        - emit_iteration_table_updated: emits a signal when the iteration
                                        scans have been updated
        - fill_values: fill values_list depending on the visualized tags
        - filter_values: select the tag values used for the iteration
        - refresh_layout: updates the layout of the widget
        - remove_tag: removes a tag to visualize in the iteration table
        - select_iterated_tag: opens a pop-up to let the user select on which
                               tag to iterate
        - select_visualized_tag: opens a pop-up to let the user select which
                                 tag to visualize in the iteration table
        - update_iterated_tag: updates the widget
        - update_table: updates the iteration table
        - update_selected_tag: updates the selected tag for current pipeline
                               manager tab

    """

    iteration_table_updated = pyqtSignal(list, list)

    def __init__(self, project, scan_list, main_window):
        """
        Initialization of the IterationTable widget.

        :param project: current project in the software
        :param scan_list: list of the selected database files
        :param main_window: software's main_window
        """

        QWidget.__init__(self)

        # Necessary for using MIA bricks
        ProcessMIA.project = project

        self.project = project

        if not scan_list:
            self.scan_list = self.project.session.get_documents_names(
                COLLECTION_CURRENT
            )
        else:
            self.scan_list = scan_list

        self.main_window = main_window

        # values_list will contain the different values of each selected tag
        self.values_list = [[], []]
        self.all_tag_values = []

        # Checkbox to choose to iterate the pipeline or not
        self.check_box_iterate = QCheckBox("Iterate pipeline")
        self.check_box_iterate.stateChanged.connect(
            self.emit_iteration_table_updated
        )

        # Label "Iterate over:"
        self.label_iterate = QLabel("Iterate over:")

        # Label that displays the name of the selected tag
        self.iterated_tag_label = QLabel("Select a tag")

        # Push button to select the tag to iterate
        self.iterated_tag_push_button = QPushButton("Select")
        self.iterated_tag_push_button.clicked.connect(
            self.select_iteration_tag
        )

        # QComboBox
        self.combo_box = QComboBox()
        self.combo_box.currentIndexChanged.connect(self.update_table)

        # filter
        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.filter_values)

        # QTableWidget
        self.iteration_table = QTableWidget()

        # Label tag
        self.label_tags = QLabel("Tags to visualize:")

        # Each push button will allow the user to visualize a tag in
        # the iteration browser
        push_button_tag_1 = QPushButton()
        push_button_tag_1.setText("SequenceName")
        push_button_tag_1.clicked.connect(
            lambda: self.select_visualized_tag(0)
        )

        push_button_tag_2 = QPushButton()
        push_button_tag_2.setText("AcquisitionDate")
        push_button_tag_2.clicked.connect(
            lambda: self.select_visualized_tag(1)
        )

        # The list of all the push buttons
        # (the user can add as many as he or she wants)
        self.push_buttons = []
        self.push_buttons.insert(0, push_button_tag_1)
        self.push_buttons.insert(1, push_button_tag_2)

        # Labels to add/remove a tag (a push button)
        self.add_tag_label = ClickableLabel()
        self.add_tag_label.setObjectName("plus")
        sources_images_dir = Config().getSourceImageDir()
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

        # Layout
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)
        self.refresh_layout()

    def add_tag(self):
        """Add a tag to visualize in the iteration table.

        Used only for tests
        """

        idx = len(self.push_buttons)
        push_button = QPushButton()
        push_button.setText("Tag n°" + str(len(self.push_buttons) + 1))
        push_button.clicked.connect(lambda: self.select_visualized_tag(idx))
        self.push_buttons.insert(len(self.push_buttons), push_button)
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
        Fill values_list depending on the visualized tags

        :param idx: Index of the tag
        """
        tag_name = self.push_buttons[idx].text()
        values = []
        for scan in self.project.session.get_documents_names(
            COLLECTION_CURRENT
        ):
            current_value = self.project.session.get_value(
                COLLECTION_CURRENT, scan, tag_name
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

    def filter_values(self):
        """Select the tag values used for the iteration"""

        # fmt: off
        iterated_tag = (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor().iterated_tag
        )
        tag_values = (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor().all_tag_values_list
        )
        # fmt: on

        ui_iteration = PopUpSelectIteration(iterated_tag, tag_values)

        if ui_iteration.exec_():
            tag_values_list = [
                t.replace("&", "") for t in ui_iteration.final_values
            ]
            # fmt: off
            (
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor
            )().tag_values_list = tag_values_list
            # fmt: on

            self.combo_box.clear()
            self.combo_box.addItems(tag_values_list)
            self.update_table()

    def refresh_layout(self):
        """Update the layout of the widget.

        Called in widget's initialization and when a tag push button
        is added or removed.
        """

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

        self.v_layout.addLayout(top_layout)
        self.v_layout.addWidget(self.iteration_table)

        self.h_box = QHBoxLayout()
        self.h_box.setSpacing(10)
        self.h_box.addWidget(self.label_tags)

        for tag_label in self.push_buttons:
            self.h_box.addWidget(tag_label)

        self.h_box.addWidget(self.add_tag_label)
        self.h_box.addWidget(self.remove_tag_label)
        self.h_box.addStretch(1)

        self.v_layout.addLayout(self.h_box)

    def remove_tag(self):
        """Remove a tag to visualize in the iteration table."""
        if len(self.push_buttons) >= 1:
            push_button = self.push_buttons[-1]
            push_button.deleteLater()
            push_button = None
            del self.push_buttons[-1]
            del self.values_list[-1]
            self.refresh_layout()
            self.update_table()

    def select_iteration_tag(self):
        """Open a pop-up to let the user select on which tag to iterate."""

        # fmt: off
        ui_select = PopUpSelectTagCountTable(
            self.project,
            self.project.session.get_fields_names(COLLECTION_CURRENT),
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor().iterated_tag,
        )
        # fmt: on

        if ui_select.exec_():
            # fmt: off
            if (
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor().iterated_tag is None
                and ui_select.selected_tag is None
            ):
                # fmt: on
                pass

            else:
                (self.main_window.pipeline_manager.pipelineEditorTabs.
                 get_current_editor)().iterated_tag = ui_select.selected_tag

                # Retrieve tag values
                self.update_selected_tag(ui_select.selected_tag)

    def select_visualized_tag(self, idx):
        """Open a pop-up to let the user select which tag to visualize in the
        iteration table.

        :param idx: index of the clicked push button
        """

        popUp = PopUpSelectTagCountTable(
            self.project,
            self.project.session.get_fields_names(COLLECTION_CURRENT),
            self.push_buttons[idx].text(),
        )
        if popUp.exec_() and popUp.selected_tag is not None:
            self.push_buttons[idx].setText(popUp.selected_tag)
            self.fill_values(idx)
            self.update_table()

    def update_iterated_tag(self, tag_name=None):
        """
        Update the widget when the iterated tag is modified.

        :param tag_name: name of the iterated tag
        """

        if len(self.main_window.pipeline_manager.scan_list) > 0:
            self.scan_list = self.main_window.pipeline_manager.scan_list
        else:
            self.scan_list = self.project.session.get_documents_names(
                COLLECTION_CURRENT
            )

        self.combo_box.clear()
        if tag_name is None:
            self.iterated_tag_push_button.setText("Select")
            self.iterated_tag_label.setText("Select a tag")
            self.iteration_table.clear()
            self.iteration_table.setColumnCount(len(self.push_buttons))
        else:
            self.iterated_tag_push_button.setText(tag_name)
            self.iterated_tag_label.setText(tag_name + ":")

            # duplicate the values list to have the initial, unfiltered, one
            # fmt: off
            self.all_tag_values = list(
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor().all_tag_values_list
            )
            self.combo_box.addItems(
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor().tag_values_list
            )
            # fmt: on
            self.update_table()

    def update_table(self):
        """
        Update the iteration table.

        """

        # Updating the scan list
        if not self.scan_list:
            self.scan_list = self.project.session.get_documents_names(
                COLLECTION_CURRENT
            )

        # Clearing the table and preparing its columns
        self.iteration_table.clear()
        self.iteration_table.setColumnCount(len(self.push_buttons))

        # fmt: off
        if (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor().iterated_tag
            is not None
        ):
            # fmt: on
            # Headers
            for idx in range(len(self.push_buttons)):
                # FIXME should not use GUI text values !!
                header_name = self.push_buttons[idx].text().replace("&", "")
                if header_name not in self.project.session.get_fields_names(
                    COLLECTION_CURRENT
                ):
                    print(f"{header_name} not in the project's tags")
                    return

                item = QTableWidgetItem()
                item.setText(header_name)
                self.iteration_table.setHorizontalHeaderItem(idx, item)

            # Searching the database scans that correspond to
            # iterated tag value
            # fmt: off
            filter_query = (
                "({"
                + str(
                    self.main_window.pipeline_manager.pipelineEditorTabs.
                    get_current_editor().iterated_tag
                )
                + "} "
                + "=="
                + ' "'
                + str(self.combo_box.currentText()).replace("&", "")
                + '")'
            )
            # fmt: on
            scans_list = self.project.session.filter_documents(
                COLLECTION_CURRENT, filter_query
            )
            scans_res = [
                getattr(document, TAG_FILENAME) for document in scans_list
            ]

            # Taking the intersection between the found database scans and the
            # user selection in the data_browser
            self.iteration_scans = list(
                set(scans_res).intersection(self.scan_list)
            )
            self.iteration_table.setRowCount(len(self.iteration_scans))

            # Filling the table cells
            row = -1
            for scan_name in self.iteration_scans:
                row += 1
                for idx in range(len(self.push_buttons)):
                    tag_name = self.push_buttons[idx].text().replace("&", "")

                    item = QTableWidgetItem()
                    item.setText(
                        str(
                            self.project.session.get_value(
                                COLLECTION_CURRENT, scan_name, tag_name
                            )
                        )
                    )
                    self.iteration_table.setItem(row, idx, item)

            all_iterations_scans = []

            # fmt: off
            for (
                tag_value
            ) in (
                self.main_window.pipeline_manager.pipelineEditorTabs.
                get_current_editor().tag_values_list
            ):
                # Searching the database scans that correspond to
                # iterated tag value
                filter_query = (
                    "({"
                    + str(
                        self.main_window.pipeline_manager.pipelineEditorTabs.
                        get_current_editor().iterated_tag
                    )
                    + "} "
                    + "=="
                    + ' "'
                    + str(tag_value)
                    + '")'
                )
                # fmt: on
                scans_list = self.project.session.filter_documents(
                    COLLECTION_CURRENT, filter_query
                )
                scans_res = [
                    getattr(document, TAG_FILENAME) for document in scans_list
                ]
                all_iterations_scans.append(
                    list(set(scans_res).intersection(self.scan_list))
                )
            self.all_iterations_scans = all_iterations_scans
            # self.scans = True

            # This will change the scans list in the current
            # Pipeline Manager tab
            self.iteration_table_updated.emit(
                self.iteration_scans, self.all_iterations_scans
            )

    def update_selected_tag(self, selected_tag):
        """Update the list of values corresponding to the selected tag

        :param selected_tag: the selected tag
        """

        tag_values_list = []
        scans_names = self.project.session.get_documents_names(
            COLLECTION_CURRENT
        )

        if not self.scan_list:
            self.scan_list = scans_names

        scans_names = list(set(scans_names).intersection(self.scan_list))

        for scan_name in scans_names:
            tag_value = self.project.session.get_value(
                COLLECTION_CURRENT, scan_name, selected_tag
            )

            if str(tag_value) not in tag_values_list:
                tag_values_list.append(str(tag_value))

        # fmt: off
        (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor
        )().tag_values_list = tag_values_list

        (
            self.main_window.pipeline_manager.pipelineEditorTabs.
            get_current_editor
        )().all_tag_values_list = tag_values_list
        # fmt: on
        self.update_iterated_tag(selected_tag)
