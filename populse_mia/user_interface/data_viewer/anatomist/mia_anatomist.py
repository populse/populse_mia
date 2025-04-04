"""
Mia data viewer implementation based on `Anatomist
<http://brainvisa.info/anatomist/user_doc/index.html>`_

Contains:
    Class:
        - MiaViewer
"""

#############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
#############################################################################

import logging
import os

from soma.qt_gui.qt_backend import Qt

from populse_mia.data_manager.project import COLLECTION_CURRENT, TAG_FILENAME
from populse_mia.user_interface.data_browser.data_browser import (
    TableDataBrowser,
)

from ..data_viewer import DataViewer

logger = logging.getLogger(__name__)


try:
    from anatomist.simpleviewer.anasimpleviewer import AnaSimpleViewer

except ImportError:
    logger.warning(
        "Anatomist seems not to be installed. The data_viewer anatomist "
        "and anatomist_2 will not work..."
    )


class MiaViewer(Qt.QWidget, DataViewer):
    """
    A data viewer for Mia (Multiparametric Image Analysis) using PyAnatomist.

    This class provides a specialized viewer for displaying and managing
    medical imaging files with additional filtering and visualization
    capabilities.

    :class:`Mia data viewer <populse_mia.user_interface.data_viewer.data_viewer.DataViewer>` # noqa: E501
    implementation based on `PyAnatomist <http://brainvisa.info/pyanatomist/sphinx/index.html>`_  # noqa: E501

    .. Methods:
        - _find_child: Find a child widget by name.
        - _setup_ui: Set up the user interface components for the viewer.
        - display_files: Display the given files in the Anatomist viewer.
        - displayed_files: Get the list of currently displayed files.
        - remove_files: Remove specified files from the viewer.
        - set_documents: Set the current project and documents for the viewer.
        - filter_documents: Open a dialog to filter and select documents for
                            visualization.
        - close: Close the viewer and manage Anatomist viewer resources.

    """

    def __init__(self, init_global_handlers=None):
        """
        Initialize the MiaViewer.

        :param init_global_handlers: Initial global handlers for Anatomist
                                     viewer.
        """
        super().__init__()
        # Initialize Anatomist viewer
        self.anaviewer = AnaSimpleViewer(init_global_handlers)

        # Count global number of viewers using anatomist, in order to close it
        # nicely
        if not hasattr(DataViewer, "mia_viewers"):
            DataViewer.mia_viewers = 0

        DataViewer.mia_viewers += 1
        # Set up UI components
        self._setup_ui()
        # Initialize project-related attributes
        self.project = None
        self.documents = []
        self.disp_find_childlayed = []

    @staticmethod
    def _find_child(parent, name):
        """
        Find a child widget by name.

        :param parent (Qt.QObject): Parent widget to search in.
        :param name (str): Name of the child widget to find.

        :return (Qt.QObject): The found child widget.
        """
        return parent.findChild(Qt.QObject, name)

    def _setup_ui(self):
        """
        Set up the user interface components for the viewer.
        """
        # Find and modify the toolbar
        awidget = self.anaviewer.awidget
        toolbar = self._find_child(awidget, "toolBar")
        open_action = self._find_child(awidget, "fileOpenAction")
        # Add custom filter action
        db_action = Qt.QAction(open_action.icon(), "Filter", awidget)
        toolbar.insertAction(open_action, db_action)
        db_action.triggered.connect(self.filter_documents)
        # Set up layout
        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        # Configure Anatomist widget
        self.anaviewer.awidget.setSizePolicy(
            Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding
        )
        layout.addWidget(self.anaviewer.awidget)

    def display_files(self, files):
        """
        Display the given files in the Anatomist viewer.

        :param files (list): List of file paths to display.
        """
        self.displayed.extend(files)

        for filename in files:
            self.anaviewer.loadObject(filename)

    def displayed_files(self):
        """
        Get the list of currently displayed files.

        :return (List): List of displayed file paths.
        """
        return self.displayed

    def remove_files(self, files):
        """
        Remove specified files from the viewer.

        :param files (list): List of file paths to remove.
        """
        self.anaviewer.deleteObjectsFromFiles(files)
        self.files = [doc for doc in self.displayed if doc not in files]

    def set_documents(self, project, documents):
        """
         Set the current project and documents for the viewer.

        :param project: The project to set.
        :param documents (List): List of documents in the project.
        """

        if self.project is not project:
            self.clear()

        self.project = project
        self.documents = documents

    def filter_documents(self):
        """Open a dialog to filter and select documents for visualization."""
        # Create filter dialog
        dialog = Qt.QDialog()
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)

        with self.project.database.data() as database_data:
            # Create table data browser
            table_data = TableDataBrowser(
                self.project,
                self,
                database_data.get_shown_tags(),
                False,
                True,
                link_viewer=False,
            )

        layout.addWidget(table_data)
        # Add dialog buttons
        hlay = Qt.QHBoxLayout()
        layout.addLayout(hlay)
        ok = Qt.QPushButton("Display")
        hlay.addWidget(ok)
        ok.clicked.connect(dialog.accept)
        ok.setDefault(True)
        cancel = Qt.QPushButton("Cancel")
        hlay.addWidget(cancel)
        cancel.clicked.connect(dialog.reject)
        hlay.addStretch(1)
        # Prepare table data
        all_scans = table_data.scans_to_visualize
        table_data.scans_to_visualize = self.documents
        table_data.scans_to_search = self.documents
        table_data.update_visualized_rows(all_scans)

        # Execute dialog
        if dialog.exec_() == Qt.QDialog.Accepted:
            # Process selected files
            result_names = []

            with self.project.database.data() as database_data:

                for point in table_data.selectedIndexes():
                    row = point.row()
                    # We get the FileName of the scan from the first row
                    scan_name = table_data.item(row, 0).text()
                    value = database_data.get_value(
                        COLLECTION_CURRENT, scan_name, TAG_FILENAME
                    )
                    full_path = os.path.abspath(
                        os.path.join(self.project.folder, value)
                    )
                    result_names.append(full_path)

            self.display_files(result_names)

    def close(self):
        """Close the viewer and manage Anatomist viewer resources."""
        super().close()
        # Decrement viewer count
        DataViewer.mia_viewers -= 1  # dec count
        close_ana = DataViewer.mia_viewers == 0
        self.anaviewer.closeAll(close_ana)
