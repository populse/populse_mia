"""
Populse_mia data viewer GUI interface (in the "Data Viewer" tab).

Contains:
    Class:
        - DataViewerTab

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import importlib
import logging
import os

from soma.qt_gui.qt_backend import Qt

logger = logging.getLogger(__name__)


class DataViewerTab(Qt.QWidget):
    """
    A flexible and extensible widget for managing data viewers in a GUI
    application.

    This widget provides a dynamic interface for loading and switching between
    different data viewers. Key features include:
    - Automatic discovery of viewers in the data_viewer directory
    - Graceful handling of viewer import failures
    - Ability to dynamically add new viewers
    - Centralized document and project management across viewers

    .. Methods:
        - activate_viewer: Activates viewer which was selected
                           in the combobox.
        - change_viewer: Switches to viewer selected in the combobox.
        - clear: Clears all loaded viewers before closing Mia.
        - closeEvent: Clears and closes all events before closing Mia.
        - current_viewer: Return current viewer (selected viewer in combobox).
        - load_viewer: Load a viewer.
        - set_documents: Shares project with documents to all viewers.
    """

    def __init__(self, main_window):
        """
        Initialize the DataViewerTab with a reference to the main window.

        :param main_window (Qt.QMainWindow): The main application window
                                             providing context and potential
                                             shared resources.
        """
        super().__init__()
        # Initialize state tracking attributes
        self.docs = []
        self.project = []
        self.viewers_loaded = {}
        self.viewer_current = {}
        # Set up main layout
        self.main_window = main_window
        self.lay = Qt.QVBoxLayout()
        self.setLayout(self.lay)
        # Create viewer selection interface
        hlay = Qt.QHBoxLayout()
        self.lay.addLayout(hlay)
        hlay.addWidget(Qt.QLabel("use viewer:"))
        # Combobox will contain the viewers if they are available
        self.viewers_combo = Qt.QComboBox()
        self.viewers_combo.setMinimumWidth(150)
        hlay.addWidget(self.viewers_combo)
        hlay.addStretch(1)
        # Connect viewer selection to change handler
        self.viewers_combo.currentIndexChanged.connect(self.change_viewer)

    def activate_viewer(self, viewer_name):
        """
        Activate a specific viewer by name.

        :param viewer_name (str): Name of the viewer to activate.
        """

        if self.viewer_current and list(self.viewer_current)[0] == viewer_name:
            return

        logger.info(f"- Activate viewer: {viewer_name}")
        viewer = self.viewers_loaded.get(viewer_name)

        if viewer:
            self.stacks.setCurrentWidget(viewer)
            self.viewer_current.clear()
            self.viewer_current[viewer_name] = viewer

    def change_viewer(self):
        """
        Handle viewer change event triggered by the combobox.

        Retrieves the selected viewer, activates it, and ensures
        that the current project and documents are set.
        """
        viewer_name = self.viewers_combo.currentText().lower()
        self.activate_viewer(viewer_name)
        self.set_documents(self.project, self.docs)

    def clear(self):
        """
        Clean up and close all loaded viewers.

        Called before closing the application to ensure
        proper resource management.
        """

        for viewer in list(self.viewers_loaded):
            self.viewers_loaded[viewer].close()
            del self.viewers_loaded[viewer]

    def closeEvent(self, event):
        """
        Override close event to ensure proper cleanup.

        :param event (QCloseEvent): Close event triggered by the window system.
        """
        self.clear()
        super().closeEvent(event)

    def current_viewer(self):
        """
        Retrieve the name of the currently active viewer.

        :return (str): Name of the current viewer, either from the current
                       viewer tracking or the combobox selection.
        """
        return (
            list(self.viewer_current)[0]
            if self.viewer_current
            else self.viewers_combo.currentText().lower()
        )

    def load_viewer(self, viewer_name=None):
        """
        Dynamically load viewers from the data_viewer directory.

        Attempts to import and initialize viewers, handling
        import failures gracefully.

        :param viewer_name (str): Specific viewer to load. If None, discovers
                                  all viewers.
        """
        # Determine viewers to load
        script_dir = os.path.dirname(__file__)
        detected_viewers = (
            [viewer_name]
            if viewer_name
            else [
                p
                for p in os.listdir(script_dir)
                if (
                    os.path.isdir(os.path.abspath(os.path.join(script_dir, p)))
                    and p != "__pycache__"
                )
            ]
        )

        # Create stacked layout only if no viewers have been loaded yet
        if not self.viewers_loaded:
            self.stacks = Qt.QStackedLayout()
            self.lay.addLayout(self.stacks)

        init_global_handlers = True

        # Load detected viewers
        for name in detected_viewers:

            if name not in self.viewers_loaded:

                try:
                    viewer_module = importlib.import_module(
                        f"{__name__.rsplit('.', 1)[0]}.{name}"
                    )
                    viewer = viewer_module.MiaViewer(init_global_handlers)
                    self.viewers_loaded[name] = viewer
                    self.stacks.addWidget(viewer)
                    self.viewers_combo.addItem(name)

                    # Update global handlers flag
                    if viewer.anaviewer._global_handlers_initialized:
                        init_global_handlers = False

                except Exception:
                    logger.warning(
                        f"{name} viewer is not available or not working...!",
                        exc_info=True,
                    )

    def set_documents(self, project, documents):
        """
        Distribute project and document information to the current viewer.

        :param project: The entire project context.
        :param documents (list): List of document/image objects in the project.
        """
        if self.viewer_current:
            current_viewer_name = list(self.viewer_current)[0]
            self.viewer_current[current_viewer_name].set_documents(
                project, documents
            )
            # Update local project and document tracking
            self.project = project
            self.docs = documents
