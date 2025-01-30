# -*- coding: utf-8 -*-

"""
MIA data viewer implementation based on
`Anatomist <http://brainvisa.info/anatomist/user_doc/index.html>`_

Contains:
    Class:
        - MiaViewer
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

from __future__ import absolute_import, print_function

import os

from PyQt5.QtGui import QIcon, QMessageBox
from PyQt5.QtWidgets import QHBoxLayout, QToolButton
from soma.qt_gui.qt_backend import Qt, QtCore

from populse_mia.data_manager import (
    COLLECTION_CURRENT,
    NOT_DEFINED_VALUE,
    TAG_FILENAME,
)
from populse_mia.software_properties import Config
from populse_mia.user_interface.data_browser.data_browser import (
    TableDataBrowser,
)
from populse_mia.user_interface.data_browser.rapid_search import RapidSearch
from populse_mia.user_interface.data_viewer.anatomist_2 import (  # noqa: F401
    resources,
)
from populse_mia.user_interface.data_viewer.anatomist_2.anasimpleviewer2 import (  # noqa: E501
    AnaSimpleViewer2,
)

from ..data_viewer import DataViewer


class MiaViewer(Qt.QWidget, DataViewer):
    """
    :class:`MIA data viewer
           <populse_mia.user_interface.data_viewer.data_viewer.DataViewer>`
           implementation based on
           `PyAnatomist <http://brainvisa.info/pyanatomist/sphinx/index.html>`_

    .. Methods:
        - close: Exit
        - display_files: Load objects in files and display
        - displayed_files: Get the list of displayed files
        - filter_documents: Filter documents already loaded in the Databrowser
        - preferences: Preferences for the dataviewer
        - remove_files: Delete the given objects given by their file names
        - reset_search_bar: Reset the rapid search bar
        - screenshot: The screenshot of mia_anatomist_2
        - search_str: Update the *Not Defined*" values in visualised documents
        - set_documents: Initialise current documents in the viewer

    """

    def __init__(self, init_global_handlers=None):
        """
        Initializes an instance of MiaViewer.

        This sets up the Anatomist-based viewer (`AnaSimpleViewer2`), manages
        the global viewer count (`mia_viewers`), connects UI actions to their
        respective methods, and initializes layout and attributes for handling
        project data.

        :param init_global_handlers: Optional initialization handlers for
                                    `AnaSimpleViewer2`. Defaults to None.
        """
        super(MiaViewer, self).__init__()
        self.anaviewer = AnaSimpleViewer2(init_global_handlers)

        # count global number of viewers using anatomist, in order to close it
        # nicely
        if not hasattr(DataViewer, "mia_viewers"):
            DataViewer.mia_viewers = 0

        DataViewer.mia_viewers += 1

        def findChild(parent, name):
            """
            Finds a child object within a given parent object.

            This is a wrapper around `Qt.QObject.findChild` to simplify
            finding a child object by name within a given parent object.

            :param parent: The parent `QObject` in which to search.
            :param name: The name of the child `QObject` to find.
            :return: The found `QObject` if it exists, otherwise None.
            """
            return Qt.QObject.findChild(parent, Qt.QObject, name)

        awidget = self.anaviewer.awidget
        filter_action = findChild(awidget, "filterAction")
        preferences_action = findChild(awidget, "actionPreferences")
        screenshot_action = findChild(awidget, "actionprint_view")
        filter_action.triggered.connect(self.filter_documents)
        preferences_action.triggered.connect(self.preferences)
        screenshot_action.triggered.connect(self.screenshot)
        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        self.anaviewer.awidget.setSizePolicy(
            Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding
        )
        layout.addWidget(self.anaviewer.awidget)
        self.project = None
        self.documents = []
        self.displayed = []
        self.table_data = []

    def close(self):
        """
        Closes the MiaViewer instance.

        Decrements the global count of active MiaViewer instances. If no more
        instances are open, it ensures that all associated Anatomist viewers
        are properly closed.

        Calls the parent class's `close` method before handling viewer cleanup.
        """
        super(MiaViewer, self).close()
        close_ana = False
        DataViewer.mia_viewers -= 1  # dec count

        if DataViewer.mia_viewers == 0:
            close_ana = True

        self.anaviewer.closeAll(close_ana)

    def display_files(self, files):
        """
        Loads and displays objects from the given file paths.

        Appends the provided files to the list of currently displayed files
        and loads them into the Anatomist viewer.

        :param files: List of file paths to be loaded and displayed.
        """
        self.displayed += files
        self.anaviewer.loadObject(files)

    def displayed_files(self):
        """
        Returns the list of currently displayed files.

        :return: List of file paths that are currently displayed.
        """
        return self.displayed

    def filter_documents(self):
        """
        Opens a dialog to filter and select documents already loaded in the
        Databrowser.

        The dialog allows users to search for documents by filename and refine
        the list of displayed files. The selected files are then imported and
        displayed in the viewer.

        Features:
        - A search bar for filtering by filename.
        - A cancel button to clear the search.
        - A table displaying the filtered documents.
        - Import and cancel buttons to confirm or discard the selection.

        Upon confirmation, the selected files are passed to `display_files()`.
        """
        dialog = Qt.QDialog()
        dialog.setWindowTitle("Filter documents")
        dialog.resize(1150, 500)
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)
        # Some specific filtering
        # QLineEdit for research
        self.search_bar = RapidSearch(dialog)
        self.search_bar.textChanged.connect(self.search_str)
        # Cancel search button
        sources_images_dir = Config().getSourceImageDir()
        button_cross = QToolButton()
        button_cross.setStyleSheet("background-color:rgb(255, 255, 255);")
        button_cross.setIcon(
            QIcon(os.path.join(sources_images_dir, "gray_cross.png"))
        )
        button_cross.clicked.connect(self.reset_search_bar)
        title = Qt.QLabel()
        title.setText("Search by FileName: ")
        layout.addWidget(title)
        search_bar_layout = QHBoxLayout()
        search_bar_layout.addWidget(self.search_bar)
        search_bar_layout.addSpacing(3)
        search_bar_layout.addWidget(button_cross)
        # Add layout to dialogBox
        layout.addLayout(search_bar_layout)
        layout.addSpacing(8)
        self.table_data = TableDataBrowser(
            self.project,
            self,
            self.project.database.get_shown_tags(),
            False,
            True,
            link_viewer=False,
        )
        layout.addWidget(self.table_data)
        hlay = Qt.QHBoxLayout()
        layout.addLayout(hlay)
        ok = Qt.QPushButton("Import")
        hlay.addWidget(ok)
        ok.clicked.connect(dialog.accept)
        ok.setDefault(True)
        cancel = Qt.QPushButton("Cancel")
        hlay.addWidget(cancel)
        cancel.clicked.connect(dialog.reject)
        hlay.addStretch(1)
        # Reducing the list of scans to selection
        all_scans = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.documents
        self.table_data.scans_to_search = self.documents
        self.table_data.update_visualized_rows(all_scans)
        res = dialog.exec_()

        if res == Qt.QDialog.Accepted:
            points = self.table_data.selectedIndexes()
            result_names = []

            for point in points:
                row = point.row()
                # We get the FileName of the scan from the first row
                scan_name = self.table_data.item(row, 0).text()
                value = self.project.database.get_value(
                    collection=COLLECTION_CURRENT,
                    primary_key=scan_name,
                    field=TAG_FILENAME,
                )
                value = os.path.abspath(
                    os.path.join(self.project.folder, value)
                )
                result_names.append(value)

            self.display_files(result_names)

    def preferences(self):
        """
        Opens a preferences dialog for the dataviewer.

        This dialog allows users to modify the following settings:
        - **Viewer Configuration**: Toggle between "Neuro" and "Radio" modes.
        - **Automatic Frame Rate**: Adjust the speed at which images are
                                    displayed.
        - **Referential System**: Choose between "World Coordinates" and
                                  "Image Referential".

        Features:
        - Uses `QComboBox` for selecting configuration and referential options.
        - Includes a `QSlider` for adjusting the automatic frame rate.
        - Provides "Save" and "Cancel" buttons to apply or discard changes.
        - Updates `Config` settings and reloads images when necessary.

        If changes are confirmed:
        - The new settings are saved in `Config`.
        - If the viewer configuration or referential system is modified, the
          viewer updates accordingly.
        """
        # Get initial config:
        im_sec = Config().getViewerFramerate()
        config = Config().getViewerConfig()
        ref = Config().get_referential()
        dialog = Qt.QDialog()
        dialog.setWindowTitle("Preferences")
        dialog.resize(600, 400)
        layout = Qt.QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        dialog.setLayout(layout)
        # Change Neuro/Radio configuration
        config_layout = QHBoxLayout()
        title_config = Qt.QLabel()
        title_config.setText("Configuration: ")
        box = Qt.QComboBox()
        box.addItem("Neuro")
        box.addItem("Radio")
        config_layout.addWidget(title_config)
        config_layout.addWidget(box)

        if config == "radio":
            box.setCurrentIndex(1)

        # set automatic time frame rate
        frame_rate_layout = QHBoxLayout()
        title = Qt.QLabel()
        title.setText("Automatic time image display:")
        slider = Qt.QSlider(Qt.Qt.Horizontal)
        slider.setRange(1, 100)
        slider.setValue(int(im_sec))
        size = QtCore.QSize(180, 15)
        slider.setMinimumSize(size)
        slow_label = Qt.QLabel()
        fast_label = Qt.QLabel()
        slow_label.setText("slow")
        fast_label.setText("fast")
        frame_rate_layout.addWidget(title)
        frame_rate_layout.addWidget(slow_label)
        frame_rate_layout.addWidget(slider)
        frame_rate_layout.addWidget(fast_label)
        frame_rate_layout.insertSpacing(1, 200)
        # Change referential
        ref_layout = QHBoxLayout()
        title_ref = Qt.QLabel()
        title_ref.setText("Referential: ")
        box2 = Qt.QComboBox()
        box2.addItem("World Coordinates")
        box2.addItem("Image referential")
        ref_layout.addWidget(title_ref)
        ref_layout.addWidget(box2)
        box2.setCurrentIndex(int(ref))
        # Set general vertical layout
        layout.addLayout(config_layout)
        layout.addLayout(frame_rate_layout)
        layout.addLayout(ref_layout)
        layout.addStretch(1)
        # Save and cancel buttons
        hlay = Qt.QHBoxLayout()
        layout.addLayout(hlay)
        ok = Qt.QPushButton("Save")
        hlay.addStretch(1)
        hlay.addWidget(ok)
        ok.clicked.connect(dialog.accept)
        ok.setDefault(True)
        cancel = Qt.QPushButton("Cancel")
        hlay.addWidget(cancel)
        cancel.clicked.connect(dialog.reject)
        hlay.addStretch(1)
        res = dialog.exec_()

        if res == Qt.QDialog.Accepted:
            new_config = box.currentText().lower()
            new_ref = box2.currentIndex()
            # Save Config parameters and reload images
            # when config and referential have changed
            Config().setViewerFramerate(slider.value())
            Config().setViewerConfig(new_config)
            Config().set_referential(new_ref)

            if new_config != config:
                self.anaviewer.changeConfig(new_config)

            if new_ref != ref:
                self.anaviewer.changeRef()

    def remove_files(self, files):
        """
        Removes the specified objects from the viewer based on their file
        names.

        This method:
        - Calls `deleteObjectsFromFiles` to remove the objects associated
          with the given file names.
        - Updates the `self.displayed` list to exclude the removed files.

        :param files: List of file paths to be removed from the viewer.
        :type files: list[str]
        """
        self.anaviewer.deleteObjectsFromFiles(files)
        self.files = [doc for doc in self.displayed if doc not in files]

    def reset_search_bar(self):
        """
        Clears the text in the rapid search bar.

        This resets any search query entered by the user.
        """
        self.search_bar.setText("")

    def screenshot(self):
        """
        Displays an information message indicating that the screenshot
        functionality for mia_anatomist_2 is not yet implemented.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Not yet implemented!")
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(msg.close)
        msg.exec()

    def search_str(self, str_search):
        """
        Searches for a given string in the table and updates the list of
        visualized documents based on the search result. It handles both
        normal searches and searches for undefined values.

        :param str_search: The string to search for in the documents. If
                           empty, all documents will be displayed. If the
                           string matches the special value
                           `NOT_DEFINED_VALUE`, it filters for documents with
                           undefined values.
        """

        old_scan_list = self.table_data.scans_to_visualize
        return_list = []

        # Every scan taken if empty search
        if str_search == "":
            return_list = self.table_data.scans_to_search

        else:

            # Scans with at least a not defined value
            if str_search == NOT_DEFINED_VALUE:
                filter = self.search_bar.prepare_not_defined_filter(
                    self.project.database.get_shown_tags()
                )

            # Scans matching the search
            else:
                filter = self.search_bar.prepare_filter(
                    str_search,
                    self.project.database.get_shown_tags(),
                    self.table_data.scans_to_search,
                )

            scans = self.project.database.filter_documents(
                COLLECTION_CURRENT, filter
            )
            # Creating the list of scans
            return_list = [scan[TAG_FILENAME] for scan in scans]

        self.table_data.scans_to_visualize = return_list
        # Rows updated
        self.table_data.update_visualized_rows(old_scan_list)
        self.project.currentFilter.search_bar = str_search

    def set_documents(self, project, documents):
        """
        Initializes the documents to be displayed in the viewer.

        If the current project is different from the provided one, the viewer
        is cleared before setting the new project and documents.

        :param project: The project object to associate with the documents.
        :param documents: A list of document paths or identifiers to display
                          in the viewer.
        """

        if self.project is not project:
            self.clear()

        self.project = project
        self.documents = documents
