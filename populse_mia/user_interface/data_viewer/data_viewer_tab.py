# -*- coding: utf-8 -*-
"""
Populse-MIA data viewer GUI interface, in the "Data Viewer" tab.

Contains:
    Class:
        - DataViewerTab

"""

import importlib
import os
import traceback

from soma.qt_gui.qt_backend import Qt


class DataViewerTab(Qt.QWidget):
    """
    DataViewerTab is the widget in the data viewer tab of Populse-MIA GUI.

    A combobox containing the available viewers will always appear.
    If import of viewers fails, it won't impact the work of Mia itself.
    Viewers are put in Qt.QStackedLayout in order to share a same project.
    A new viewer can be added simply by placing it in the
    data_viewer directory.
    """

    def __init__(self, main_window):
        """The constructor ...

        :param main_window: an instance of the MainWindow class
        """
        super(DataViewerTab, self).__init__()
        self.docs = []
        self.lay = []
        self.project = []
        self.stacks = []
        self.viewers_loaded = {}
        self.viewer_current = {}

        # Display of combobox containing the viewers
        self.main_window = main_window
        self.lay = Qt.QVBoxLayout()
        self.setLayout(self.lay)

        hlay = Qt.QHBoxLayout()
        self.lay.addLayout(hlay)
        hlay.addWidget(Qt.QLabel("use viewer:"))

        # Combobox will contain the viewers if they are available
        self.viewers_combo = Qt.QComboBox()
        self.viewers_combo.setMinimumWidth(150)

        hlay.addWidget(self.viewers_combo)
        hlay.addStretch(1)

        self.viewers_combo.currentIndexChanged.connect(self.change_viewer)

    def activate_viewer(self, viewer_name):
        """Activates viewer viewer_name which was selected
        in the combobox.

        :param viewer_name: a viewer name (a string)
        """
        if self.viewer_current and list(self.viewer_current)[0] == viewer_name:
            return

        print("\n- activate viewer:", viewer_name)
        viewer = self.viewers_loaded[viewer_name]

        if viewer:
            self.stacks.setCurrentWidget(viewer)
            self.viewer_current.clear()
            self.viewer_current[viewer_name] = viewer

    def change_viewer(self):
        """Switches to viewer selected in the combobox
        pass the project from on viewer to the other.
        """
        index = self.viewers_combo.currentIndex()
        viewer_name = self.viewers_combo.itemText(index).lower()
        self.activate_viewer(viewer_name)
        self.set_documents(self.project, self.docs)

    def clear(self):
        """Clears all loaded viewers before closing Mia."""
        for viewer in list(self.viewers_loaded):
            self.viewers_loaded[viewer].close()
            del self.viewers_loaded[viewer]

    def closeEvent(self, event):
        """clears and closes all events before closing Mia."""
        self.clear()
        super().close()

    def current_viewer(self):
        """Return current viewer (selected viewer in combobox)
        used when user changes from BrowserTab or PipelineManagerTab
        to DataViewerTab.

        """
        if not self.viewer_current:
            return self.viewers_combo.currentText().lower()
        else:
            return list(self.viewer_current)[0]

    def load_viewer(self, viewer_name):
        """Available viewers in data_viewer folder are loaded as soon
        as Data Viewer tab is clicked.

        :param viewer_name: string
        """
        if viewer_name:
            detected_viewer = [viewer_name]

        else:
            detected_viewer = [
                p
                for p in os.listdir(os.path.dirname(__file__))
                if os.path.isdir(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), p))
                )
                and p != "__pycache__"
            ]

        if not self.viewers_loaded:
            self.stacks = Qt.QStackedLayout()
            self.lay.addLayout(self.stacks)

        init_global_handlers = True

        # Try import detected viewers
        for viewer_name in detected_viewer:
            if viewer_name not in self.viewers_loaded:
                try:
                    viewer_module = importlib.import_module(
                        "%s.%s" % (__name__.rsplit(".", 1)[0], viewer_name)
                    )
                    self.viewers_loaded[viewer_name] = viewer_module.MiaViewer(
                        init_global_handlers
                    )
                    self.stacks.addWidget(self.viewers_loaded[viewer_name])
                    self.viewers_combo.addItem(viewer_name)
                    # Check if initialization of controls has been done:
                    if self.viewers_loaded[
                        viewer_name
                    ].anaviewer._global_handlers_initialized:
                        init_global_handlers = False

                except Exception as e:
                    print(
                        "\n{0} viewer is not available or not working "
                        "...!\nTraceback:".format(viewer_name)
                    )
                    print(
                        "".join(traceback.format_tb(e.__traceback__)), end=""
                    )
                    print("{0}: {1}\n".format(e.__class__.__name__, e))

    def set_documents(self, project, documents):
        """Shares project with documents to all viewers.

        :param project: whole project
        :param documents: objects (images) contained in the project
        """
        if self.viewer_current:
            self.viewer_current[list(self.viewer_current)[0]].set_documents(
                project, documents
            )
            self.project = project
            self.docs = documents
