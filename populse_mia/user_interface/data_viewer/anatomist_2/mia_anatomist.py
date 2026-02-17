"""
Mia data viewer implementation based on
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

import logging
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

logger = logging.getLogger(__name__)


class MiaViewer(DataViewer):
    """
    A PyQt-based viewer using PyAnatomist.

    This class implements a DataViewer interface and provides functionality
    to visualize and interact with medical imaging data through the PyAnatomist
    visualization library.

    :class:`MIA data viewer
           <populse_mia.user_interface.data_viewer.data_viewer.DataViewer>`
           implementation based on
           `PyAnatomist <http://brainvisa.info/pyanatomist/sphinx/index.html>`_

    .. Methods:
        - _add_dialog_buttons: Add action buttons to the filter dialog.
        - _apply_preferences: Apply the settings from the preferences dialog.
        - _create_preferences_dialog: Create the preferences dialog.
        - _process_selected_documents: Process user's document selection.
        - _setup_search_interface: Set up the search bar and related UI
                                   elements.
        - _setup_ui: Set up the user interface components and connect signals.
        - close: Exit
        - display_files: Load objects in files and display.
        - displayed_files: Get the list of displayed files.
        - filter_documents: Filter documents already loaded in the Databrowser.
        - preferences: Preferences for the dataviewer.
        - remove_files: Delete the given objects given by their file names.
        - reset_search_bar: Reset the rapid search bar.
        - screenshot: The screenshot of mia_anatomist_2.
        - search_str: Update the *Not Defined*" values in visualised documents.
        - set_documents: Initialise current documents in the viewer.

    """

    # Class-level tracker for Anatomist viewers
    _mia_viewers_count = 0

    def __init__(self, init_global_handlers=None):
        """
        Initialize the Mia viewer widget.

        :param init_global_handlers: Handlers to initialize the PyAnatomist
                                     viewer
        """
        super().__init__()
        self.anaviewer = AnaSimpleViewer2(init_global_handlers)
        # Track the total number of active viewers to manage PyAnatomist's
        # lifecycle
        type(self)._mia_viewers_count += 1
        # Set up UI and connect actions
        self._setup_ui()
        self.project = None
        self.documents = []
        self.displayed = []
        self.table_data = []

    def _add_dialog_buttons(self, dialog, layout):
        """
        Add action buttons to the filter dialog.

        :param dialog: Parent dialog.
        :param layout: Layout to add buttons to.
        """
        hlay = Qt.QHBoxLayout()
        layout.addLayout(hlay)
        # Import button
        ok = Qt.QPushButton("Import")
        ok.clicked.connect(dialog.accept)
        ok.setDefault(True)
        hlay.addWidget(ok)
        # Cancel button
        cancel = Qt.QPushButton("Cancel")
        cancel.clicked.connect(dialog.reject)
        hlay.addWidget(cancel)
        hlay.addStretch(1)

    def _apply_preferences(self, dialog):
        """
        Apply the settings from the preferences dialog.

        :param dialog: Preferences dialog containing the user selections.
        """
        # Get new values
        new_config = dialog.config_box.currentText().lower()
        new_ref = dialog.ref_box.currentIndex()
        new_framerate = dialog.slider.value()
        # Get current values for comparison
        current_config = Config().getViewerConfig()
        current_ref = Config().get_referential()
        # Save new values
        Config().setViewerFramerate(new_framerate)
        Config().setViewerConfig(new_config)
        Config().set_referential(new_ref)

        # Apply changes that require viewer update
        if new_config != current_config:
            self.anaviewer.changeConfig(new_config)

        if new_ref != current_ref:
            self.anaviewer.changeRef()

    def _create_preferences_dialog(
        self, current_framerate, current_config, current_ref
    ):
        """
        Create the preferences dialog with all settings controls.

        :param current_framerate: Current animation frame rate.
        :param current_config: Current display configuration (neuro/radio).
        :param current_ref: Current referential setting.

        :return (QDialog): Configured preferences dialog.
        """
        dialog = Qt.QDialog()
        dialog.setWindowTitle("Preferences")
        dialog.resize(600, 400)
        layout = Qt.QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        dialog.setLayout(layout)
        # Configuration selection (Neuro/Radio)
        config_layout = QHBoxLayout()
        config_layout.addWidget(Qt.QLabel("Configuration: "))
        dialog.config_box = Qt.QComboBox()
        dialog.config_box.addItems(["Neuro", "Radio"])

        if current_config == "radio":
            dialog.config_box.setCurrentIndex(1)

        config_layout.addWidget(dialog.config_box)
        layout.addLayout(config_layout)
        # Frame rate slider
        frame_rate_layout = QHBoxLayout()
        frame_rate_layout.addWidget(Qt.QLabel("Automatic time image display:"))
        frame_rate_layout.addWidget(Qt.QLabel("slow"))
        dialog.slider = Qt.QSlider(Qt.Qt.Horizontal)
        dialog.slider.setRange(1, 100)
        dialog.slider.setValue(int(current_framerate))
        dialog.slider.setMinimumSize(QtCore.QSize(180, 15))
        frame_rate_layout.addWidget(dialog.slider)
        frame_rate_layout.addWidget(Qt.QLabel("fast"))
        frame_rate_layout.insertSpacing(1, 200)
        layout.addLayout(frame_rate_layout)
        # Referential selection
        ref_layout = QHBoxLayout()
        ref_layout.addWidget(Qt.QLabel("Referential: "))
        dialog.ref_box = Qt.QComboBox()
        dialog.ref_box.addItems(["World Coordinates", "Image referential"])
        dialog.ref_box.setCurrentIndex(int(current_ref))
        ref_layout.addWidget(dialog.ref_box)
        layout.addLayout(ref_layout)
        layout.addStretch(1)
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        save_button = Qt.QPushButton("Save")
        save_button.clicked.connect(dialog.accept)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)

        cancel_button = Qt.QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        return dialog

    def _process_selected_documents(self):
        """Process user's document selection and display the selected files."""
        points = self.table_data.selectedIndexes()
        selected_files = []

        with self.project.database.data() as database_data:

            for point in points:
                row = point.row()
                # Get the filename of the scan from the first column
                scan_name = self.table_data.item(row, 0).text()
                filepath = database_data.get_value(
                    COLLECTION_CURRENT, scan_name, TAG_FILENAME
                )
                # Convert to absolute path
                filepath = os.path.abspath(
                    os.path.join(self.project.folder, filepath)
                )
                selected_files.append(filepath)

            if selected_files:
                self.display_files(selected_files)

    def _setup_search_interface(self, dialog, layout):
        """
        Set up the search bar and related UI elements.

        :param dialog: Parent dialog for the search interface.
        :param layout: Layout to add search components to.
        """
        # Title label
        title = Qt.QLabel("Search by FileName: ")
        layout.addWidget(title)
        # Search bar with clear button
        search_bar_layout = QHBoxLayout()
        # Search text field
        self.search_bar = RapidSearch(dialog)
        self.search_bar.textChanged.connect(self.search_str)
        search_bar_layout.addWidget(self.search_bar)
        search_bar_layout.addSpacing(3)
        # Clear button
        sources_images_dir = Config().getSourceImageDir()
        button_cross = QToolButton()
        button_cross.setStyleSheet("background-color:rgb(255, 255, 255);")
        button_cross.setIcon(
            QIcon(os.path.join(sources_images_dir, "gray_cross.png"))
        )
        button_cross.clicked.connect(self.reset_search_bar)
        search_bar_layout.addWidget(button_cross)
        # Add to main layout
        layout.addLayout(search_bar_layout)
        layout.addSpacing(8)

    def _setup_ui(self):
        """Set up the user interface components and connect signals."""
        # Get references to PyAnatomist widget actions
        awidget = self.anaviewer.awidget
        filter_action = awidget.findChild(QtCore.QObject, "filterAction")
        preferences_action = awidget.findChild(
            QtCore.QObject, "actionPreferences"
        )
        screenshot_action = awidget.findChild(
            QtCore.QObject, "actionprint_view"
        )
        # Connect actions to methods
        filter_action.triggered.connect(self.filter_documents)
        preferences_action.triggered.connect(self.preferences)
        screenshot_action.triggered.connect(self.screenshot)
        # Layout setup
        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        # Make PyAnatomist widget expand to fill available space
        self.anaviewer.awidget.setSizePolicy(
            Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding
        )
        layout.addWidget(self.anaviewer.awidget)

    def close(self):
        """
        Close the viewer and properly clean up PyAnatomist resources.

        If this is the last MIA viewer instance, closes PyAnatomist entirely.
        """
        # NOTE: super().close() is intentionally NOT called here.
        # DataViewer.close() would call clear() → remove_files() →
        # anaviewer.deleteObjectsFromFiles() → Anatomist.getObjects(),
        # which crashes because the Anatomist singleton is already destroyed
        # at this point. This is a known bug in Anatomist: its API does not
        # guard against calls made after the singleton has been destroyed.
        # closeAll(True) handles the equivalent C++ cleanup directly and
        # safely.
        # super().close()
        # Decrement viewer count
        type(self)._mia_viewers_count -= 1
        last_viewer = type(self)._mia_viewers_count == 0

        try:

            if last_viewer:
                # Last viewer: close all C++ objects
                # self.anaviewer.remove_files()

                # Guard: only call closeAll if Anatomist singleton is still
                # alive
                # try:
                #
                #     import anatomist.api as anatomist
                #
                #     a = anatomist.Anatomist()
                #
                #     # Check the singleton is still functional
                #     if a is not None and a.anatomistinstance is not None:
                #         self.anaviewer.closeAll(True)
                #
                # except Exception:
                #     # Singleton already gone, skip closeAll silently
                #     pass
                #
                # self.anaviewer = None
                self.anaviewer.closeAll(True)
                self.anaviewer = None

            else:
                self.anaviewer.setParent(None)
                self.anaviewer.deleteLater()
                self.anaviewer = None

        except Exception:
            logger.warning("Anatomist close failed", exc_info=True)

    def display_files(self, files):
        """
        Load and display the specified files in the viewer.

        :param files (list): List of file paths to display.
        """
        self.displayed.extend(files)
        self.anaviewer.loadObject(files)

    def displayed_files(self):
        """
        Get the list of currently displayed files.

        :return (list): File paths currently displayed in the viewer.
        """
        return self.displayed

    def filter_documents(self):
        """
        Open a dialog to filter and select documents to display.

        Allows searching and filtering documents loaded in the Databrowser
        and importing selected ones into the viewer.
        """
        dialog = Qt.QDialog()
        dialog.setWindowTitle("Filter documents")
        dialog.resize(1150, 500)
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)
        # Set up search interface
        self._setup_search_interface(dialog, layout)

        with self.project.database.data() as database_data:
            # Create data browser table
            self.table_data = TableDataBrowser(
                self.project,
                self,
                database_data.get_shown_tags(),
                False,
                True,
                link_viewer=False,
            )

        layout.addWidget(self.table_data)
        # Add action buttons
        self._add_dialog_buttons(dialog, layout)
        # Reducing the list of scans to selection
        all_scans = self.table_data.scans_to_visualize
        self.table_data.scans_to_visualize = self.documents
        self.table_data.scans_to_search = self.documents
        self.table_data.update_visualized_rows(all_scans)

        # Show dialog and process results
        if dialog.exec_() == Qt.QDialog.Accepted:
            self._process_selected_documents()

    def preferences(self):
        """
        Open the preferences dialog to configure viewer settings.

        Allows configuring display mode (Neuro/Radio), animation speed,
        and coordinate system referential.
        """
        # Get initial config:
        current_framerate = Config().getViewerFramerate()
        current_config = Config().getViewerConfig()
        current_ref = Config().get_referential()
        # Create dialog
        dialog = self._create_preferences_dialog(
            current_framerate, current_config, current_ref
        )

        # Show dialog and process results
        if dialog.exec_() == Qt.QDialog.Accepted:
            self._apply_preferences(dialog)

    def remove_files(self, files):
        """
         Remove specified files from the viewer.

        :param files (list): List of file paths to remove from display.
        """
        self.anaviewer.deleteObjectsFromFiles(files)
        self.displayed = [doc for doc in self.displayed if doc not in files]

    def reset_search_bar(self):
        """Clear the search bar text."""
        self.search_bar.setText("")

    def screenshot(self):
        """
        Take a screenshot of the current viewer state.

        Currently displays a "Not yet implemented" message.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Not yet implemented!")
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(msg.close)
        msg.exec()

    def search_str(self, search_term):
        """
        Search for documents matching the given term and update the view.

        Handles special case for NOT_DEFINED_VALUE as well as normal text
        search. Updates the table to show only matching documents.

        :param search_term (str): Text to search for in documents
        """

        old_scan_list = self.table_data.scans_to_visualize
        matching_documents = []

        if not search_term:
            # Show all documents when search is empty
            matching_documents = self.table_data.scans_to_search

        else:

            with self.project.database.data() as database_data:

                # Create appropriate filter based on search term
                if search_term == NOT_DEFINED_VALUE:
                    # Special case for undefined values
                    filter_query = self.search_bar.prepare_not_defined_filter(
                        database_data.get_shown_tags()
                    )

                # Scans matching the search
                else:
                    filter_query = self.search_bar.prepare_filter(
                        search_term,
                        database_data.get_shown_tags(),
                        self.table_data.scans_to_search,
                    )

                # Get matching documents from database
                matching_docs = database_data.filter_documents(
                    COLLECTION_CURRENT, filter_query
                )

            # Creating the list of scans
            matching_documents = [doc[TAG_FILENAME] for doc in matching_docs]

        # Update table with matching documents
        self.table_data.scans_to_visualize = matching_documents
        # Rows updated
        self.table_data.update_visualized_rows(old_scan_list)
        # Save current search in project
        self.project.currentFilter.search_bar = search_term

    def set_documents(self, project, documents):
        """
        Initialize the viewer with a set of documents from a project.

        :param project: Project containing the documents.
        :param documents (list): List of document filenames to make available.
        """

        if self.project is not project:
            self.clear()

        self.project = project
        self.documents = documents
