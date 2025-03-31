"""Open a new window for a selected object with only one view possible.

Contains:
    Class:
        - NewWindowViewer
"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

import logging
import os

from soma.qt_gui.qt_backend import Qt, QtCore, QtGui
from soma.qt_gui.qt_backend.uic import loadUi

logger = logging.getLogger(__name__)

try:
    import anatomist.direct.api as ana

except ImportError:
    logger.warning(
        "Anatomist seems not to be installed. The data_viewer anatomist "
        "and anatomist_2 will not work..."
    )


class NewWindowViewer(QtGui.QMainWindow):
    """
    Window for displaying a selected object in a single anatomical view.

    This class creates a window that remains on top of other windows and
    allows the user to choose between different anatomical views (axial,
    sagittal, coronal, or 3D) for visualizing the selected object.

    .. Methods:
        - changeDisplay: Changes display on user's demand.
        - disableButton: Manages button availability and whether they should be
                         checked or not depending on which view is displayed.
        - createNewWindow: Opens a new window in the vertical layout.
        - setObject: Store object to display.
        - showPopup: Defines the dimensions of the popup which is a QWidget.
        - close: Close properly objects before exiting Mia.
    """

    def __init__(self):
        """
        Initialize the NewWindowViewer with UI components and event
        connections.
        """
        super().__init__(None, QtCore.Qt.WindowStaysOnTopHint)
        # Load ui file
        uifile = "second_window.ui"
        mainwindowdir = os.path.dirname(__file__)
        awin = loadUi(os.path.join(mainwindowdir, uifile))
        self.window = awin
        self.viewNewWindow = awin.findChild(QtCore.QObject, "windows")
        self.newViewLay = Qt.QHBoxLayout(self.viewNewWindow)
        self.new_awindow = None
        self.object = None
        self.window_index = 0
        self.popup_window = Qt.QWidget()
        self.popup_window.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
        )
        self.popups = []
        self.layout = Qt.QVBoxLayout()
        self.popup_window.setLayout(self.layout)
        self.popup_window.resize(730, 780)
        self.window.setSizePolicy(
            Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding
        )
        # find views viewButtons
        self.viewButtons = [
            awin.findChild(QtCore.QObject, "actionAxial"),
            awin.findChild(QtCore.QObject, "actionSagittal"),
            awin.findChild(QtCore.QObject, "actionCoronal"),
            awin.findChild(QtCore.QObject, "action3D"),
        ]
        self.viewButtons[0].setChecked(True)

        for index, button in enumerate(self.viewButtons):
            button.triggered.connect(
                lambda _, i=index: self.changeDisplay(i, self.object)
            )

    def changeDisplay(self, index, obj):
        """
         Changes the display based on user's selection.

        :param index (int): Index of the view to display
                            (0: Axial, 1: Sagittal, 2: Coronal, 3: 3D).
        :param obj: The object to display.
        """
        a = ana.Anatomist("-b")
        views = ["Axial", "Sagittal", "Coronal", "3D"]
        new_view = views[index]
        self.disableButton(index)
        self.createNewWindow(new_view)
        a.addObjects(obj, self.new_awindow)

    def disableButton(self, index):
        """
        Manages button availability and checked state depending on the
        displayed view.

        :param index (int): Index of the view to enable.
        """

        for i, button in enumerate(self.viewButtons):
            button.setChecked(i == index)

    def createNewWindow(self, wintype="Axial"):
        """
        Opens a new window in the vertical layout.

        :param intype (str): Type of the view to create (default is 'Axial').
        """
        a = ana.Anatomist("-b")
        w = a.createWindow(wintype, no_decoration=True, options={"hidden": 1})
        w.setAcceptDrops(False)
        # Set wanted view button checked and others unchecked
        views = ["Axial", "Sagittal", "Coronal", "3D"]
        index = views.index(wintype)
        self.disableButton(index)

        # Delete object if there is already one at the first position
        if self.newViewLay.itemAt(0):
            self.newViewLay.itemAt(0).widget().deleteLater()

        x, y = 0, 0  # Ensure x and y are always defined

        if not hasattr(self, "_winlayouts"):
            self._winlayouts = [[0, 0], [0, 0]]

        for y in range(2):

            for x in range(2):

                if not self._winlayouts[x][y]:
                    break

            else:
                continue

            break

        self.newViewLay.addWidget(w.getInternalRep())
        self.new_awindow = w
        self._winlayouts[x][y] = 1

        if wintype == "3D":
            a.execute("SetControl", windows=[w], control="LeftSimple3DControl")
            a.execute(
                "Camera",
                windows=[self.new_awindow],
                view_quaternion=[0.404603, 0.143829, 0.316813, 0.845718],
            )
        else:
            a.execute("SetControl", windows=[w], control="Simple2DControl")
            a.assignReferential(a.mniTemplateRef, w)
            # Force redrawing in MNI orientation
            getattr(w, f"mute{wintype}")()

        # Set a black background
        a.execute(
            "WindowConfig",
            windows=[w],
            light={"background": [0.0, 0.0, 0.0, 1.0]},
            view_size=(500, 600),
        )

    def setObject(self, obj):
        """
        Stores the object to be displayed.

        :param obj: The object to display.
        """
        self.object = obj

    def showPopup(self, obj):
        """
         Defines the dimensions of the popup and displays the object.

        QWidget is added to self.popups in order to keep the widget but being
        able to replace the object inside.

        :param obj: The object to display in the popup.
        """
        a = ana.Anatomist("-b")
        self.layout.addWidget(self.window)
        self.popups.append(self.popup_window)
        index = len(self.popups) - 1
        self.popups[index].setWindowTitle(obj.name)
        # Create empty view (Axial, Sagittal,...)
        self.createNewWindow()
        self.setObject(obj)
        # Add object into view
        a.addObjects(obj, self.new_awindow)
        self.popups[index].show()

    def close(self):
        """
        Properly closes objects before exiting.
        """
        self.window.close()
        self.window = None
        self.viewNewWindow = []
        self.newViewLay = None
        self.new_awindow = None
        self.object = []
