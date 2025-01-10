# -*- coding: utf-8 -*-

"""
MIA data viewer implementation based on `Anatomist
<http://brainvisa.info/anatomist/user_doc/index.html>`_

This module provides the `MiaViewer` class, which integrates the Anatomist
viewer for displaying medical imaging data within the MIA interface. It
extends the functionality of `DataViewer` and uses PyAnatomist for
visualization.

Classes:
    - MiaViewer: The main widget for viewing and interacting with image data.
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

try:
    from anatomist.simpleviewer.anasimpleviewer import AnaSimpleViewer

except ImportError:
    print(
        "\nAnatomist seems not to be installed. The data_viewer anatomist "
        "and anatomist_2 will not work...\n"
    )

from soma.qt_gui.qt_backend import Qt

from populse_mia.data_manager.project import COLLECTION_CURRENT, TAG_FILENAME
from populse_mia.user_interface.data_browser.data_browser import (
    TableDataBrowser,
)

from ..data_viewer import DataViewer


class MiaViewer(Qt.QWidget, DataViewer):
    """
    MIA data viewer widget for visualizing medical imaging data.

    This class is an implementation of the `DataViewer` interface,
    using `PyAnatomist <http://brainvisa.info/pyanatomist/sphinx/index.html>`_
    for image visualization. It provides features to display, filter, and
    manage imaging data within the MIA interface.

    Attributes:
        anaviewer (AnaSimpleViewer): The Anatomist viewer instance.
        project: The associated project object containing metadata.
        documents (list): A list of documents associated with the project.
        displayed (list): A list of files currently displayed in the viewer.
    """

    def __init__(self, init_global_handlers=None):
        """
        Initializes the MiaViewer instance.

        Args:
            init_global_handlers (callable, optional): A callback function
            for initializing global handlers in Anatomist.
        """

        super(MiaViewer, self).__init__()
        self.anaviewer = AnaSimpleViewer(init_global_handlers)

        # count global number of viewers using anatomist, in order to close it
        # nicely
        if not hasattr(DataViewer, "mia_viewers"):
            DataViewer.mia_viewers = 0

        DataViewer.mia_viewers += 1

        def findChild(x, y):
            """
            Finds a child object of the specified parent by name.

            Args:
                x (QObject): The parent object in which to search
                             for the child.
                y (str): The name of the child object to find.

            Returns:
                QObject or None: The child object if found, otherwise None.
            """
            return Qt.QObject.findChild(x, Qt.QObject, y)

        awidget = self.anaviewer.awidget
        toolbar = findChild(awidget, "toolBar")
        open_action = findChild(awidget, "fileOpenAction")
        db_action = Qt.QAction(open_action.icon(), "filter", awidget)
        toolbar.insertAction(open_action, db_action)
        db_action.triggered.connect(self.filter_documents)

        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        self.anaviewer.awidget.setSizePolicy(
            Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding
        )
        layout.addWidget(self.anaviewer.awidget)

        self.project = None
        self.documents = []
        self.displayed = []

    def display_files(self, files):
        """
        Displays the specified files in the Anatomist viewer.

        Args:
            files (list): A list of file paths to be displayed.
        """
        self.displayed += files

        for filename in files:
            self.anaviewer.loadObject(filename)

    def displayed_files(self):
        """
        Retrieves the list of files currently displayed in the viewer.

        Returns:
            list: A list of file paths currently displayed.
        """
        return self.displayed

    def remove_files(self, files):
        """
        Removes the specified files from the viewer.

        Args:
            files (list): A list of file paths to remove from the viewer.
        """
        self.anaviewer.deleteObjectsFromFiles(files)
        self.files = [doc for doc in self.displayed if doc not in files]

    def set_documents(self, project, documents):
        """
        Sets the project and its associated documents for the viewer.

        If a new project is provided, the current viewer is cleared before
        loading the new documents.

        Args:
            project: The project object to associate with the viewer.
            documents (list): A list of documents to manage in the viewer.
        """
        if self.project is not project:
            self.clear()

        self.project = project
        self.documents = documents

    def filter_documents(self):
        """
        Opens a dialog to filter and select documents for display.

        The user can interact with the dialog to filter available documents
        based on metadata, and the selected documents are displayed in the
        viewer.
        """
        dialog = Qt.QDialog()
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)
        table_data = TableDataBrowser(
            self.project,
            self,
            self.project.database.get_shown_tags(),
            False,
            True,
            link_viewer=False,
        )
        layout.addWidget(table_data)
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

        # Reducing the list of scans to selection
        all_scans = table_data.scans_to_visualize
        table_data.scans_to_visualize = self.documents
        table_data.scans_to_search = self.documents
        table_data.update_visualized_rows(all_scans)

        res = dialog.exec_()

        if res == Qt.QDialog.Accepted:
            points = table_data.selectedIndexes()
            result_names = []

            for point in points:
                row = point.row()
                # We get the FileName of the scan from the first row
                scan_name = table_data.item(row, 0).text()
                value = self.project.database.get_value(
                    COLLECTION_CURRENT, scan_name, TAG_FILENAME
                )
                value = os.path.abspath(
                    os.path.join(self.project.folder, value)
                )
                result_names.append(value)

            self.display_files(result_names)

    def close(self):
        """
        Closes the viewer and decrements the global viewer count.

        If no other MiaViewer instances are active, the Anatomist viewer
        is closed completely.
        """
        super(MiaViewer, self).close()
        close_ana = False
        DataViewer.mia_viewers -= 1  # dec count

        if DataViewer.mia_viewers == 0:
            close_ana = True

        self.anaviewer.closeAll(close_ana)
