# -*- coding: utf-8 -*-
"""Open a new window for a selected object with only one view possible."""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

import os

try:
    import anatomist.direct.api as ana

except ImportError:
    print(
        "\nAnatomist seems not to be installed. The data_viewer anatomist "
        "and anatomist_2 will not work...\n"
    )

from soma.qt_gui.qt_backend import Qt, QtCore, QtGui
from soma.qt_gui.qt_backend.uic import loadUi


class NewWindowViewer(QtGui.QMainWindow):
    """
    Class defined to open a new window for a selected object with only one
    view possible. The user will be able to choose which view he wants to
    display (axial, sagittal, coronal view or 3D view)
    """

    def __init__(self):
        QtGui.QMainWindow.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)

        # Load ui file
        uifile = "second_window.ui"
        cwd = os.getcwd()
        mainwindowdir = os.path.join(
            cwd, "user_interface/data_viewer/anatomist_2"
        )
        os.chdir(mainwindowdir)
        awin = loadUi(os.path.join(mainwindowdir, uifile))
        os.chdir(cwd)

        # connect GUI actions callbacks
        def findChild(x, y):
            return Qt.QObject.findChild(x, QtCore.QObject, y)

        self.window = awin
        self.viewNewWindow = findChild(awin, "windows")
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
            findChild(awin, "actionAxial"),
            findChild(awin, "actionSagittal"),
            findChild(awin, "actionCoronal"),
            findChild(awin, "action3D"),
        ]
        self.viewButtons[0].setChecked(True)

        self.viewButtons[0].triggered.connect(
            lambda: self.changeDisplay(0, self.object)
        )
        self.viewButtons[1].triggered.connect(
            lambda: self.changeDisplay(1, self.object)
        )
        self.viewButtons[2].triggered.connect(
            lambda: self.changeDisplay(2, self.object)
        )
        self.viewButtons[3].triggered.connect(
            lambda: self.changeDisplay(3, self.object)
        )

    def changeDisplay(self, index, object):
        """
        Changes display on user's demand
        index : int between 0 and 3
        object : object to display
        """
        a = ana.Anatomist("-b")
        views = ["Axial", "Sagittal", "Coronal", "3D"]
        new_view = views[index]
        self.disableButton(index)
        self.createNewWindow(new_view)
        a.addObjects(object, self.new_awindow)

    def disableButton(self, index):
        """
        Manages button availability and whether they should be checked or not
        depending on which view is displayed
        """
        self.viewButtons[index].setChecked(True)
        for i in [0, 1, 2, 3]:
            if i == index:
                pass
            else:
                self.viewButtons[i].setChecked(False)

    def createNewWindow(self, wintype="Axial"):
        """
        Opens a new window in the vertical layout
        Function is nearly the same as createWindow in AnaSimpleViewer2
        Default display each time a new popup opens is 'Axial' view
        """
        a = ana.Anatomist("-b")
        w = a.createWindow(wintype, no_decoration=True, options={"hidden": 1})
        w.setAcceptDrops(False)

        # Set wanted view button checked and others unchecked
        views = ["Axial", "Sagittal", "Coronal", "3D"]
        index = views.index(wintype)
        self.disableButton(index)

        # Delete object if there is already one
        if self.newViewLay.itemAt(0):
            self.newViewLay.itemAt(0).widget().deleteLater()

        x = 0
        y = 0
        i = 0
        if not hasattr(self, "_winlayouts"):
            self._winlayouts = [[0, 0], [0, 0]]
        else:
            freeslot = False
            for y in (0, 1):
                for x in (0, 1):
                    i = i + 1
                    if not self._winlayouts[x][y]:
                        freeslot = True
                        break
                if freeslot:
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
            # force redrawing in MNI orientation
            # (there should be a better way to do so...)
            if wintype == "Axial":
                w.muteAxial()
                print("MUTEAXIAL", w.muteAxial)
            elif wintype == "Coronal":
                w.muteCoronal()
            elif wintype == "Sagittal":
                w.muteSagittal()
            elif wintype == "Oblique":
                w.muteOblique()
        # set a black background
        a.execute(
            "WindowConfig",
            windows=[w],
            light={"background": [0.0, 0.0, 0.0, 1.0]},
            view_size=(500, 600),
        )

    def setObject(self, object):
        """
        Store object to display
        """
        self.object = object

    def showPopup(self, object):
        """
        Defines the dimensions of the popup which is a QWidget
        QWidget is added to self.popups in order to keep the widget
        but beeing able to replace the object inside

        """
        a = ana.Anatomist("-b")
        self.layout.addWidget(self.window)
        self.popups.append(self.popup_window)
        index = len(self.popups) - 1
        self.popups[index].setWindowTitle(object.name)
        # Create empty view (Axial, Sagittal,...)
        self.createNewWindow()
        self.setObject(object)
        # Add object into view
        a.addObjects(object, self.new_awindow)
        self.popups[index].show()

    def close(self):
        """
        Close properly objects before exiting Mia
        """
        self.window.close()
        self.window = None
        self.viewNewWindow = []
        self.newViewLay = None
        self.new_awindow = None
        self.object = []
