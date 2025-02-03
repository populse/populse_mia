#!/usr/bin/env python
"""AnaSimpleViewer2"""

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.


import os
import sys
import time

import numpy as np
import PyQt5
from PyQt5.QtGui import QColor, QIcon, QLabel, QWidget
from PyQt5.QtWidgets import QMessageBox
from soma import aims
from soma.aims import colormaphints
from soma.qt_gui import qt_backend
from soma.qt_gui.qt_backend import Qt, QtCore
from soma.qt_gui.qt_backend.uic import loadUi

from populse_mia.software_properties import Config
from populse_mia.user_interface.data_viewer.anatomist_2.snd_window import (
    NewWindowViewer,
)

try:
    import anatomist.direct.api as ana
except ImportError:
    print(
        "\nAnatomist seems not to be installed. The data_viewer anatomist "
        "and anatomist_2 will not work...\n"
    )
# the following imports have to be made after the qApp.startingUp() test
# since they do instantiate Anatomist for registry to work.
try:
    from anatomist.cpp.simplecontrols import (
        Simple2DControl,
        registerSimpleControls,
    )
except ImportError:
    print(
        "\nAnatomist seems not to be installed. The data_viewer anatomist "
        "and anatomist_2 will not work...\n"
    )
# determine whether we are using Qt4 or Qt5, and hack a little bit accordingly
# the boolean qt4 global variable will tell it for later usage
qt_backend.set_qt_backend(compatible_qt5=True)


class LeftSimple3DControl(Simple2DControl):
    """
    define another control where rotation is with the left mouse button
    (useful for touch devices)
    """

    def __init__(self, prio=25, name="LeftSimple3DControl"):
        """blabla"""
        super().__init__(prio, name)

    def eventAutoSubscription(self, pool):
        """blabla"""
        key = QtCore.Qt
        NoModifier = key.NoModifier
        ControlModifier = key.ControlModifier
        super().eventAutoSubscription(pool)
        self.mouseLongEventUnsubscribe(key.LeftButton, NoModifier)
        self.mouseLongEventSubscribe(
            key.LeftButton,
            NoModifier,
            pool.action("ContinuousTrackball").beginTrackball,
            pool.action("ContinuousTrackball").moveTrackball,
            pool.action("ContinuousTrackball").endTrackball,
            True,
        )
        self.keyPressEventSubscribe(
            key.Key_Space,
            ControlModifier,
            pool.action("ContinuousTrackball").startOrStop,
        )
        self.mousePressButtonEventSubscribe(
            key.MiddleButton, NoModifier, pool.action("LinkAction").execLink
        )


class VolRenderControl(LeftSimple3DControl):
    """
    define another control where cut slice rotation is with the middle mouse
    button
    """

    def __init__(self, prio=25, name="VolRenderControl"):
        """blabla"""
        super().__init__(prio, name)

    def eventAutoSubscription(self, pool):
        """blabla"""
        super().eventAutoSubscription(pool)
        self.mouseLongEventUnsubscribe(Qt.Qt.MiddleButton, Qt.Qt.NoModifier)
        self.mouseLongEventSubscribe(
            Qt.Qt.MiddleButton,
            Qt.Qt.NoModifier,
            pool.action("TrackCutAction").beginTrackball,
            pool.action("TrackCutAction").moveTrackball,
            pool.action("TrackCutAction").endTrackball,
            True,
        )


class AnaSimpleViewer2(Qt.QObject):
    """
    AnaSimpleViewer is a "simple viewer" application and widget, which can be
    used using the "anasimpleviewer.py" command, or included in a custom widget
    as a library module.

    It includes an objects list and 4 3D views (anatomist windows). Objects
    loaded are added in all views, and can be hidden or shown using the "add"
    and "remove" buttons.

    The AnaSimpleViewer class holds methods for menu/actions callbacks, and
    utility functions like load/view objects, remove/delete, etc.

    It is a QObject, but not a QWidget. The widget can be accessed as the
    ``awidget`` attribute in the AnaSimpleViewer instance.

    As it is more intended to be used as a complete application, and it is
    simpler to handle in Anatomist, some global Anatomist config variables and
    controls may be set within AnaSimpleViewer. This is done optionally using
    the :meth:`init_global_handlers` method, which is called by the constructor
    if the argument `init_global_handlers` is not set to False when calling it.
    """

    _global_handlers_initialized = False

    def __init__(self, init_global_handlers=None):
        """blabla"""
        Qt.QObject.__init__(self)

        a = ana.Anatomist("-b")

        if init_global_handlers:
            self.init_global_handlers()

        # ui file for dataviewer anasimpleviewer_2
        uifile = "mainwindow.ui"
        cwd = os.getcwd()
        mainwindowdir = os.path.dirname(__file__)
        os.chdir(mainwindowdir)
        awin = loadUi(os.path.join(mainwindowdir, uifile))
        os.chdir(cwd)
        self.awidget = awin

        # new window popup for objects
        self.newWindow = NewWindowViewer()

        # connect GUI actions callbacks
        def findChild(x, y):
            """blabla"""
            return Qt.QObject.findChild(x, QtCore.QObject, y)

        # findChild(awin,
        #           'actionprint_view').triggered.connect(self.addNewView)
        findChild(awin, "actionTimeRunning").triggered.connect(
            self.automaticRunning
        )
        findChild(awin, "fileOpenAction").triggered.connect(self.fileOpen)
        findChild(awin, "fileExitAction").triggered.connect(self.closeAll)
        findChild(awin, "editAddAction").triggered.connect(self.editAdd)
        findChild(awin, "editRemoveAction").triggered.connect(self.editRemove)
        findChild(awin, "editDeleteAction").triggered.connect(self.editDelete)
        findChild(awin, "viewEnable_Volume_RenderingAction").toggled.connect(
            self.enableVolumeRendering
        )
        findChild(awin, "viewOpen_Anatomist_main_window").triggered.connect(
            self.open_anatomist_main_window
        )
        # manually entered coords
        le = findChild(awin, "coordXEdit")
        le.setValidator(Qt.QDoubleValidator(le))
        le = findChild(awin, "coordYEdit")
        le.setValidator(Qt.QDoubleValidator(le))
        le = findChild(awin, "coordZEdit")
        le.setValidator(Qt.QDoubleValidator(le))
        le = findChild(awin, "coordTEdit")
        le.setValidator(Qt.QDoubleValidator(le))
        del le
        findChild(awin, "coordXEdit").editingFinished.connect(
            self.coordsChanged
        )
        findChild(awin, "coordYEdit").editingFinished.connect(
            self.coordsChanged
        )
        findChild(awin, "coordZEdit").editingFinished.connect(
            self.coordsChanged
        )
        findChild(awin, "coordTEdit").editingFinished.connect(
            self.coordsChanged
        )

        objects_list = findChild(self.awidget, "objectslist")
        objects_list.setContextMenuPolicy(Qt.Qt.CustomContextMenu)
        objects_list.customContextMenuRequested.connect(self.popup_objects)

        awin.dropEvent = lambda awin, event: self.dropEvent(awin, event)
        awin.dragEnterEvent = lambda awin, event: self.dragEnterEvent(
            awin, event
        )
        awin.setAcceptDrops(True)

        self._vrenabled = False
        self.meshes2d = {}
        # register the function on the cursor notifier of anatomist. It will be
        # called when the user clicks on a window
        a.onCursorNotifier.add(self.clickHandler)

        # viewWindow: parent widget for anatomist windows
        self.viewWindow = findChild(awin, "windows")

        self.viewgridlay = Qt.QHBoxLayout(self.viewWindow)
        self.combobox = Qt.QComboBox()
        self.slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.fdialog = None
        self.awindows = []
        self.aobjects = []
        self.fusion2d = []
        self.volrender = None
        self.control_3d_type = "LeftSimple3DControl"
        self.viewButtons = [
            findChild(awin, "actionAxial"),
            findChild(awin, "actionSagittal"),
            findChild(awin, "actionCoronal"),
            findChild(awin, "action3D"),
        ]
        self.displayedObjects = []
        self.files = []
        self.available_palettes = [
            "B-W_LINEAR",
            "Yellow-red",
            "RAINBOW",
            "Yellow-Red-White-Blue-Green",
            "blue-red-bright-dark",
        ]

        for action in self.viewButtons:
            action.triggered.connect(self.newDisplay)
        findChild(awin, "objectslist").itemSelectionChanged.connect(
            self.disableButtons
        )

        self.setComboBox()
        self.setSlider()
        self.combobox.currentIndexChanged.connect(self.newPalette)
        self.slider.valueChanged.connect(self.changeOpacity)

    def init_global_handlers(self):
        """
        Set some global controls / settings in Anatomist application object
        """
        if not AnaSimpleViewer2._global_handlers_initialized:
            registerSimpleControls()
            a = ana.Anatomist("-b")
            iconpath = os.path.join(str(a.anatomistSharedPath()), "icons")
            pix = Qt.QPixmap(os.path.join(iconpath, "simple3Dcontrol.png"))
            ana.cpp.IconDictionary.instance().addIcon(
                "LeftSimple3DControl", pix
            )
            ana.cpp.IconDictionary.instance().addIcon("VolRenderControl", pix)
            del pix, iconpath
            cd = ana.cpp.ControlDictionary.instance()
            cd.addControl("LeftSimple3DControl", LeftSimple3DControl, 25)
            cd.addControl("VolRenderControl", VolRenderControl, 25)

            # tweak: override some user config options
            a.config()["windowSizeFactor"] = 1.0
            a.config()["commonScannerBasedReferential"] = 1

            # register controls
            cm = ana.cpp.ControlManager.instance()
            cm.addControl("QAGLWidget3D", "", "Simple2DControl")
            cm.addControl("QAGLWidget3D", "", "LeftSimple3DControl")
            cm.addControl("QAGLWidget3D", "", "VolRenderControl")
            print("controls registered.")

            del cm

            a.setGraphParams(label_attribute="label")

            AnaSimpleViewer2._global_handlers_initialized = True

    def setComboBox(self):
        """
        Inserts a drop down menu in the toolbar. This menu contains defined
        available color palettes. The default color palettes are in
        self.available_palettes.
        """

        toolBar = Qt.QObject.findChild(self.awidget, QtCore.QObject, "toolBar")
        actionAutoRunning = Qt.QObject.findChild(
            self.awidget, QtCore.QObject, "actionTimeRunning"
        )
        label = QLabel("Palette: ")
        label.setToolTip("Change color palette of selected object")

        for palette in self.available_palettes:
            self.combobox.addItem(palette)

        toolBar.insertWidget(actionAutoRunning, label)
        toolBar.insertWidget(actionAutoRunning, self.combobox)
        sources_images_dir = Config().getSourceImageDir()

        for i in range(len(self.available_palettes)):
            icon = QIcon(
                os.path.join(sources_images_dir, self.available_palettes[i])
            )
            self.combobox.setItemIcon(i, icon)

        size = PyQt5.QtCore.QSize(200, 15)
        self.combobox.setIconSize(size)

    def setSlider(self):
        """
        Inserts opacity slider in the toolbar
        Minimum returned value is 0 and maximum value is 100
        """

        toolBar = Qt.QObject.findChild(self.awidget, QtCore.QObject, "toolBar")
        actionAutoRunning = Qt.QObject.findChild(
            self.awidget, QtCore.QObject, "actionTimeRunning"
        )
        space = QWidget().resize(5, 0)
        label = QLabel("Opacity: ")
        label.setToolTip("Change opacity of selected object")
        size = PyQt5.QtCore.QSize(120, 15)
        self.slider.setMaximumSize(size)
        self.slider.setValue(100)
        toolBar.insertWidget(actionAutoRunning, space)
        toolBar.insertWidget(actionAutoRunning, label)
        toolBar.insertWidget(actionAutoRunning, self.slider)

    def changeOpacity(self):
        """
        Changes opacity of selected object (to be more precise it changes the
        mixing rate between objects when multiple ones are displayed)
        """

        if self.selectedObjects() and len(self.displayedObjects) == 1:
            diffuse_vect = self.selectedObjects()[0].getInfo()["material"][
                "diffuse"
            ]
            self.selectedObjects()[0].setMaterial(
                diffuse=[
                    diffuse_vect[0],
                    diffuse_vect[1],
                    diffuse_vect[2],
                    self.slider.value() / 100,
                ]
            )

        elif self.selectedObjects():
            index = self.displayedObjects.index(self.selectedObjects()[0])
            a = ana.Anatomist("-b")

            if index == 0:
                a.execute(
                    "TexturingParams",
                    objects=self.fusion2d,
                    texture_index=1,
                    rate=self.slider.value() / 100,
                    mode="linear_B_if_A_black",
                )

            else:
                corrected_val = abs(self.slider.value() - 100)
                a.execute(
                    "TexturingParams",
                    objects=self.fusion2d,
                    texture_index=index,
                    rate=corrected_val / 100,
                    mode="linear_A_if_B_black",
                )

    def newPalette(self):
        """
        Sets chosen color palette in the toolbar drop down menu to
        selected object.
        """
        color = self.combobox.currentText()
        if self.selectedObjects():
            self.selectedObjects()[0].setPalette(palette=color)

    def setColorPalette(self):
        """
        Checks color palette of a selected object, displays it in the toolbar
        drop-down menu and adds it if it isn't already stored in
        self.available_palettes. If corresponding palette image exists it is
        added, otherwise only the name of the palette appears.
        """

        color = self.combobox.currentText()

        if self.selectedObjects():
            actual_pal = self.selectedObjects()[0].getInfo()["palette"][
                "palette"
            ]

            if actual_pal != color:
                if actual_pal in self.available_palettes:
                    self.combobox.setCurrentText(actual_pal)

                else:
                    self.combobox.addItem(actual_pal)
                    self.combobox.setCurrentText(actual_pal)
                    self.available_palettes.append(actual_pal)
                    sources_images_dir = Config().getSourceImageDir()
                    index = self.combobox.currentIndex()
                    icon = QIcon(
                        os.path.join(
                            sources_images_dir, self.available_palettes[index]
                        )
                    )
                    self.combobox.setItemIcon(index, icon)

    def changeConfig(self, config):
        """
        change config depending on user settings
        config : string "neuro" or "radio"
        """
        a = ana.Anatomist("-b")
        a.config()["axialConvention"] = config
        self.newDisplay()

    def changeRef(self):
        """
        change referential
        ref : Boolean
        0 : World coordinates
        1 : Image referential
        """
        self.deleteObjects(self.aobjects)
        self.loadObject(self.files, config_changed=True)

    def findChild(x, y):
        """Blabla"""

        return Qt.QObject.findChild(x, QtCore.QObject, y)

    def clickHandler(self, eventName, params):
        """
        Callback for linked cursor. In volume rendering mode, it will sync
        the VR slice to the linked cursor.
        It also updates the volumes values view
        """
        a = ana.Anatomist("-b")
        pos = params["position"]
        win = params["window"]
        wref = win.getReferential()
        # display coords in MNI referential (preferably)
        tr = a.getTransformation(wref, a.mniTemplateRef)
        if tr:
            pos2 = tr.transform(pos[:3])
        else:
            pos2 = pos

        def findChild(x, y):
            """Blabla"""
            return Qt.QObject.findChild(x, QtCore.QObject, y)

        x = findChild(self.awidget, "coordXEdit")
        x.setText("%8.3f" % pos2[0])
        y = findChild(self.awidget, "coordYEdit")
        y.setText("%8.3f" % pos2[1])
        z = findChild(self.awidget, "coordZEdit")
        z.setText("%8.3f" % pos2[2])
        t = findChild(self.awidget, "coordTEdit")
        if len(pos) < 4:
            pos = pos[:3] + [0]
        t.setText("%8.3f" % pos[3])
        # display volumes values at the given position

        valbox = findChild(self.awidget, "volumesBox")
        valbox.clear()
        # (we don't use the same widget type in Qt3 and Qt4)

        valbox.setColumnCount(2)
        valbox.setHorizontalHeaderLabels(["Volume:", "Value:"])
        if len(self.fusion2d) > 1:
            valbox.setRowCount(len(self.fusion2d) - 1)
            valbox.setVerticalHeaderLabels([""] * (len(self.fusion2d) - 1))
        i = 0
        for obj in self.fusion2d[1:]:
            # retrieve volume val'radio'ue in its own coords system
            aimsv = ana.cpp.AObjectConverter.aims(obj)
            oref = obj.getReferential()
            tr = a.getTransformation(wref, oref)
            if tr:
                pos2 = tr.transform(pos[:3])
            else:
                pos2 = pos[:3]
            vs = obj.voxelSize()
            pos2 = [int(round(x / y)) for x, y in zip(pos2, vs)]
            # pos2 in in voxels, in obj coords system
            newItem = Qt.QTableWidgetItem(obj.name)
            valbox.setItem(i, 0, newItem)
            # check bounds
            if (
                pos2[0] >= 0
                and pos2[1] >= 0
                and pos2[2] >= 0
                and pos[3] >= 0
                and pos2[0] < aimsv.getSizeX()
                and pos2[1] < aimsv.getSizeY()
                and pos2[2] < aimsv.getSizeZ()
                and pos[3] < aimsv.getSizeT()
            ):
                txt = str(aimsv.value(*pos2))
            else:
                txt = ""
            newitem = Qt.QTableWidgetItem(txt)
            valbox.setItem(i, 1, newitem)
            i += 1
        valbox.resizeColumnsToContents()

        # update volume rendering when it is enabled
        if self._vrenabled and len(self.volrender) >= 1:
            clip = self.volrender[0]
            t = a.getTransformation(
                win.getReferential(), clip.getReferential()
            )
            if t is not None:
                pos = t.transform(pos[:3])
            clip.setOffset(pos[:3])
            clip.notifyObservers()

    def automaticRunning(self):
        """
        Enable automatic running of functional images
        frame rate can be changed in preferences by the user
        """

        a = ana.Anatomist("-b")
        objects = []
        im_sec = float(Config().getViewerFramerate())
        frame_rate = 1 / im_sec

        def findChild(x, y):
            """Blabla"""

            return Qt.QObject.findChild(x, QtCore.QObject, y)

        t = findChild(self.awidget, "coordTEdit")
        sources_images_dir = Config().getSourceImageDir()
        pauseIcon = QIcon(os.path.join(sources_images_dir, "pause.png"))
        playIcon = QIcon(os.path.join(sources_images_dir, "play.png"))

        for i in range(len(self.displayedObjects)):
            objects.append(
                ana.cpp.AObjectConverter.aims(
                    self.displayedObjects[i]
                ).getSizeT()
            )
        if objects:
            nb_images = np.max(objects)
        else:
            return
        list_im = list(range(0, nb_images))
        pos = [
            float(findChild(self.awidget, "coordXEdit").text()),
            float(findChild(self.awidget, "coordYEdit").text()),
            float(findChild(self.awidget, "coordZEdit").text()),
        ]
        i = int(float(findChild(self.awidget, "coordTEdit").text()))
        if i == nb_images - 1:
            i = 0
        playAction = findChild(self.awidget, "actionTimeRunning")
        while playAction.isChecked() and i < len(list_im):
            start_time = time.time()
            playAction.setIcon(pauseIcon)
            t.setText("%8.3f" % list_im[i])
            a.execute(
                "LinkedCursor",
                window=self.awindows[0],
                position=pos[:3] + [list_im[i]],
            )
            PyQt5.QtWidgets.QApplication.processEvents()
            running_time = time.time() - start_time
            if running_time > frame_rate:
                # If iteration takes to much time we don't want to
                # make it sleep any longer (happens when fusion of images)
                pass
            else:
                time.sleep(frame_rate - running_time)
            i += 1
        playAction.setIcon(playIcon)

    def createWindow(self, wintype="Axial"):
        """
        Opens a new window in the windows grid layout.
        The new window will be set in MNI referential (except 3D for now
        because of a buf in volume rendering in direct referentials), will be
        assigned the custom control, and have no menu/toolbars.
        """
        a = ana.Anatomist("-b")
        w = a.createWindow(wintype, no_decoration=True, options={"hidden": 1})
        w.setAcceptDrops(False)
        # insert in grid layout

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

        # in Qt4, the widget must not have a parent before calling
        # layout.addWidget
        # self.viewgridlay.addWidget(w.getInternalRep(), x, y)
        self.viewgridlay.addWidget(w.getInternalRep())
        # self.viewgridlay.addWidget(w.getInternalRep(), 0, i)
        self._winlayouts[x][y] = 1
        # keep it in anasimpleviewer list of windows
        self.awindows.append(w)
        # set custom control
        if wintype == "3D":
            a.execute("SetControl", windows=[w], control=self.control_3d_type)
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

    def createTotalWindow(self, views):
        """
        Create the windows which will contain the views.

        views : array containing strings "axial", "sagittal", "coronal"
                and/or "3D"
        """

        for i in views:
            self.createWindow(str(i))

            if i == "3D":
                # set a cool angle of view for 3D
                a = ana.Anatomist("-b")
                a.execute(
                    "Camera",
                    windows=[self.awindows[-1]],
                    view_quaternion=[0.404603, 0.143829, 0.316813, 0.845718],
                )

        # Sets view buttons checked for first display
        if views == ["Axial", "Sagittal", "Coronal"]:
            counter = 0

            for i in views:
                self.viewButtons[counter].setChecked(True)
                counter += 1

    def deleteTotalWindow(self):
        """
        Clear windows and fusions in order to enable new display
        """
        self.awindows.clear()
        self.fusion2d.clear()
        for i in reversed(range(self.viewgridlay.count())):
            self.viewgridlay.itemAt(i).widget().deleteLater()

    def getViewsToDisplay(self):
        """
        Check which views must be displayed
        return : array with strings
        """
        views = []
        if self.viewButtons[0].isChecked():
            views.append("Axial")
        if self.viewButtons[1].isChecked():
            views.append("Sagittal")
        if self.viewButtons[2].isChecked():
            views.append("Coronal")
        if self.viewButtons[3].isChecked():
            views.append("3D")
        return views

    def viewReferential(self, object):
        """
        Set referential at the object center to visualize it
        """
        a = ana.Anatomist("-b")
        bb = object.boundingbox()
        position = (aims.Point3df(bb[1][:3]) - bb[0][:3]) / 2.0
        wrefs = [w.getReferential() for w in self.awindows]
        srefs = {r.uuid() for r in wrefs}
        if len(srefs) != 1:
            # not all windows in the same ref
            if aims.StandardReferentials.mniTemplateReferentialID() in srefs:
                wref_id = aims.StandardReferentials.mniTemplateReferentialID()
                wref = [r for r in wrefs if r.uuid() == wref_id][0]
            elif aims.StandardReferentials.acPcReferentialID() in srefs:
                wref = a.centralReferential()
            elif (
                aims.StandardReferentials.commonScannerBasedReferentialID()
                in srefs
            ):
                wref_id = (
                    aims.StandardReferentials.commonScannerBasedReferentialID()
                )
                wref = [r for r in wrefs if r.uuid() == wref_id][0]
            else:
                wref = wrefs[0]
            for w in self.awindows:
                w.setReferential(wref)
        else:
            wref = wrefs[0]

        t = a.getTransformation(object.getReferential(), wref)
        if not t and object.getReferential() != wref:
            # try to find a scanner-based ref and connect it to MNI
            sbref = [
                r
                for r in a.getReferentials()
                if r.uuid()
                == aims.StandardReferentials.commonScannerBasedReferentialID()
            ]
            if sbref:
                sbref = sbref[0]
                t2 = a.getTransformation(object.getReferential(), sbref)
                if t2:
                    a.execute(
                        "LoadTransformation",
                        origin=sbref,
                        destination=a.mniTemplateRef,
                        matrix=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                    )
                else:
                    # otherwise we will assume the object is in the central
                    # referential.
                    a.execute(
                        "LoadTransformation",
                        origin=object.getReferential(),
                        destination=a.centralRef,
                        matrix=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                    )
                t = a.getTransformation(
                    object.getReferential(), self.awindows[0].getReferential()
                )
        if t:
            position = t.transform(position)
        a.execute("LinkedCursor", window=self.awindows[0], position=position)
        for w in self.awindows:
            w.focusView()

    def checkviews(self):
        """
        Prevent from closing the last view opened
        Checks how many views button are enabled and if only one is,
        it disables the button
        """
        nb_views_checked = 0
        for i in range(len(self.viewButtons)):
            if self.viewButtons[i].isChecked():
                nb_views_checked += 1
        if nb_views_checked == 1:
            for i in range(len(self.viewButtons)):
                if self.viewButtons[i].isChecked():
                    self.viewButtons[i].setEnabled(False)
        else:
            for i in range(len(self.viewButtons)):
                self.viewButtons[i].setEnabled(True)

    def newDisplay(self):
        """
        New display of windows, objects and views
        """
        self.checkviews()
        self.deleteTotalWindow()
        views = self.getViewsToDisplay()
        self.createTotalWindow(views)
        for i in range(len(self.displayedObjects)):
            self.addObject(self.displayedObjects[i])
            self.viewReferential(self.displayedObjects[i])

    def loadObject(self, files, config_changed=None):
        """
        Load objects in files and display
        Only the first object of files is displayed, the others are loaded and
        added to objectlist but not displayed
        """
        a = ana.Anatomist("-b")
        a.config()["setAutomaticReferential"] = Config().get_referential()
        a.config()["axialConvention"] = Config().getViewerConfig()

        # Progress indication
        window = Qt.QWidget()
        window.setWindowTitle("Loading data")
        window.move(800, 500)
        window.resize(300, 50)
        window.show()

        i = 0
        for fname in files:
            if fname not in self.files:
                self.files.append(fname)
            objectlist = Qt.QObject.findChild(
                self.awidget, QtCore.QObject, "objectslist"
            )
            # test if object has already been imported
            for w in range(objectlist.count()):
                if os.path.basename(fname) == objectlist.item(w).text():
                    if config_changed is True:
                        return
                    msgBox = QMessageBox()
                    msgBox.setIcon(QMessageBox.Warning)
                    msgBox.setText(
                        "Some of your objects have already been imported"
                    )
                    msgBox.setWindowTitle("Warning")
                    msgBox.setStandardButtons(QMessageBox.Ok)

                    returnValue = msgBox.exec()
                    if returnValue == QMessageBox.Ok:
                        return

            obj = a.loadObject(fname)
            if obj:
                if i == 0:
                    self.registerObject(obj)
                    i += 1
                else:
                    objectlist.addItem(obj.name)
                    # keep it in the global list
                    self.aobjects.append(obj)
                    self.colorBackgroundList()
                    if obj.objectType == "VOLUME":
                        # volume are checked for possible adequate colormaps
                        hints = colormaphints.checkVolume(
                            ana.cpp.AObjectConverter.aims(obj)
                        )
                        obj.attributed()["colormaphints"] = hints
                    i += 1

    @QtCore.Slot("anatomist::AObject *", "const std::string &")
    def objectLoaded(self, obj, filename):
        """Blabla"""

        a = ana.Anatomist("-b")
        if not obj:
            return
        o = a.AObject(a, obj)
        o.releaseAppRef()
        p = a.theProcessor()
        resetProcExec = False
        if not p.execWhileIdle():
            # allow recursive commands execution, otherwise the execute()
            # may not be done right now
            p.allowExecWhileIdle(True)
            resetProcExec = True
        self.registerObject(o)
        if resetProcExec:
            # set back recursive execution to its previous state
            p.allowExecWhileIdle(False)

    def registerObject(self, obj, views=None):
        """
        Register an object in anasimpleviewer objects list, and display it
        """
        ojectlist = Qt.QObject.findChild(
            self.awidget, QtCore.QObject, "objectslist"
        )
        ojectlist.addItem(obj.name)
        # keep it in the global list
        self.aobjects.append(obj)
        self.displayedObjects.append(obj)
        self.colorBackgroundList()

        if obj.objectType == "VOLUME":
            # volume are checked for possible adequate colormaps
            # prints the header of volume ana.cpp.AObjectConverter.aims(obj)
            hints = colormaphints.checkVolume(
                ana.cpp.AObjectConverter.aims(obj)
            )
            obj.attributed()["colormaphints"] = hints

        bb = obj.boundingbox()

        if not bb:
            # not a viewable object
            return

        # create the 4 windows if they don't exist
        if len(self.awindows) == 0:
            if views is None:
                self.createTotalWindow(["Axial", "Sagittal", "Coronal"])

            else:
                self.createTotalWindow(views)

        # view obj in these views
        self.addObject(obj)
        # set the cursor at the center of the object (actually, overcome a bug
        # in anatomist...)
        self.viewReferential(obj)

    def _displayVolume(self, obj, opts={}):
        """
        Display a volume or a Fusion2D in all windows.
        If volume rendering is allowed, 3D views will display a clipped volume
        rendering of the object.
        """
        a = ana.Anatomist("-b")
        if self._vrenabled:
            wins = [x for x in self.awindows if x.subtype() != 0]
            if len(wins) != 0:
                a.addObjects(obj, wins, **opts)
            wins = [x for x in self.awindows if x.subtype() == 0]
            if len(wins) == 0:
                return
            vr = a.fusionObjects([obj], method="VolumeRenderingFusionMethod")
            vr.releaseAppRef()
            clip = a.fusionObjects([vr], method="FusionClipMethod")
            clip.releaseAppRef()
            self.volrender = [clip, vr]
            a.addObjects(clip, wins, **opts)
        else:
            a.addObjects(obj, self.awindows, **opts)

    def addVolume(self, obj, opts={}):
        """
        Display a volume in all windows.
        If several volumes are displayed, a Fusion2D will be built to wrap all
        of them.
        If volume rendering is allowed, 3D views will display a clipped volume
        rendering of either the single volume (if only one is present), or of
        the 2D fusion.
        """
        a = ana.Anatomist("-b")

        if obj in self.fusion2d:
            return

        # hasvr = False
        if self.volrender:
            # delete the previous volume rendering
            a.deleteObjects(self.volrender)
            # hasvr = True
            self.volrender = None

        if len(self.fusion2d) == 0:
            # only one object
            self.fusion2d = [None, obj]

        else:
            # several objects: fusion them
            fusobjs = self.fusion2d[1:] + [obj]
            f2d = a.fusionObjects(fusobjs, method="Fusion2DMethod")
            f2d.releaseAppRef()

            if self.fusion2d[0] is not None:
                # destroy the previous fusion
                a.deleteObjects(self.fusion2d[0])

            else:
                a.removeObjects(self.fusion2d[1], self.awindows)

            self.fusion2d = [f2d] + fusobjs
            # repalette( fusobjs )
            obj = f2d

        if obj.objectType == "VOLUME":
            # choose a good colormap for a single volume
            if "volume_contents_likelihoods" in obj.attributed():
                cmap = colormaphints.chooseColormaps(
                    (obj.attributed()["colormaphints"],)
                )
                obj.setPalette(cmap[0])

        else:
            # choose good colormaps for the current set of volumes
            hints = [x.attributed()["colormaphints"] for x in obj.children]
            children = [
                x
                for x, y in zip(obj.children, hints)
                if "volume_contents_likelihoods" in y
            ]
            hints = [x for x in hints if "volume_contents_likelihoods" in x]
            cmaps = colormaphints.chooseColormaps(hints)

            for x, y in zip(children, cmaps):
                x.setPalette(y)

        # call a lower-level function for display and volume rendering
        self._displayVolume(obj, opts)

    def removeVolume(self, obj, opts={}):
        """
        Hides a volume from views (low-level function: use removeObject)
        """
        a = ana.Anatomist("-b")

        if obj in self.fusion2d:
            # hasvr = False

            if self.volrender:
                a.deleteObjects(self.volrender)
                self.volrender = None
                # hasvr = True

            fusobjs = [o for o in self.fusion2d[1:] if o != obj]

            if len(fusobjs) >= 2:
                f2d = a.fusionObjects(fusobjs, method="Fusion2DMethod")
                f2d.releaseAppRef()

            else:
                f2d = None

            if self.fusion2d[0] is not None:
                a.deleteObjects(self.fusion2d[0])

            else:
                a.removeObjects(self.fusion2d[1], self.awindows)

            if len(fusobjs) == 0:
                self.fusion2d = []

            else:
                self.fusion2d = [f2d] + fusobjs

            # repalette( fusobjs )
            if f2d:
                obj = f2d

            elif len(fusobjs) == 1:
                obj = fusobjs[0]

            else:
                return

            self._displayVolume(obj, opts)

    def get_new_mesh2d_color(self):
        """Blabla"""

        colors = [
            (1.0, 0.3, 0.3, 1.0),
            (0.3, 1.0, 0.3, 1.0),
            (0.3, 0.3, 1.0, 1.0),
            (1.0, 1.0, 0.0, 1.0),
            (0.0, 1.0, 1.0, 1.0),
            (1.0, 0.0, 1.0, 1.0),
            (1.0, 1.0, 1.0, 1.0),
            (1.0, 0.7, 0.0, 1.0),
            (1.0, 0.0, 0.7, 1.0),
            (1.0, 0.7, 0.7, 1.0),
            (0.7, 1.0, 0.0, 1.0),
            (0.0, 1.0, 0.7, 1.0),
            (0.7, 1.0, 0.7, 1.0),
            (0.7, 0.0, 1.0, 1.0),
            (0.0, 0.7, 1.0, 1.0),
            (0.7, 0.7, 1.0, 1.0),
            (1.0, 1.0, 0.5, 1.0),
            (0.5, 1.0, 1.0, 1.0),
            (1, 0.5, 1.0, 1.0),
        ]
        used_cols = {col for obj, col in self.meshes2d.values()}
        for col in colors:
            if col not in used_cols:
                return col
        return len(self.meshes2d) % len(colors)

    def addMesh(self, obj, opts):
        """Blabla"""

        a = ana.Anatomist("-b")
        mesh2d = a.fusionObjects(
            [obj.getInternalRep()], method="Fusion2DMeshMethod"
        )
        color = self.get_new_mesh2d_color()
        self.meshes2d[obj.getInternalRep()] = (mesh2d, color)
        mesh2d.setMaterial(diffuse=color)
        mesh2d.releaseAppRef()
        windows_2d = [
            w
            for w in self.awindows
            if w.subtype()
            in (w.AXIAL_WINDOW, w.CORONAL_WINDOW, w.SAGITTAL_WINDOW)
        ]
        windows_3d = [w for w in self.awindows if w not in windows_2d]
        a.addObjects(mesh2d, windows_2d)
        a.addObjects(obj, windows_3d)

    def removeMesh(self, obj):
        """Blabla"""

        a = ana.Anatomist("-b")
        mesh2d, col = self.meshes2d[obj.getInternalRep()]
        a.removeObjects([obj, mesh2d], self.awindows)
        del self.meshes2d[obj.getInternalRep()]

    def disableButtons(self):
        """
        Disable plus or minus button depending on the selected object's display
        """
        self.setColorPalette()
        displayedObNames = []
        for i in range(len(self.displayedObjects)):
            displayedObNames.append(self.displayedObjects[i].name)
        item = Qt.QObject.findChild(
            self.awidget, QtCore.QObject, "objectslist"
        ).selectedItems()
        # There is always only one selected object
        if self.displayedObjects == [] or item == []:
            Qt.QObject.findChild(
                self.awidget, QtCore.QObject, "editAddAction"
            ).setEnabled(True)
        else:
            if item[0].text() in displayedObNames:
                Qt.QObject.findChild(
                    self.awidget, QtCore.QObject, "editAddAction"
                ).setEnabled(False)
                Qt.QObject.findChild(
                    self.awidget, QtCore.QObject, "editRemoveAction"
                ).setEnabled(True)
            else:
                Qt.QObject.findChild(
                    self.awidget, QtCore.QObject, "editRemoveAction"
                ).setEnabled(False)
                Qt.QObject.findChild(
                    self.awidget, QtCore.QObject, "editAddAction"
                ).setEnabled(True)

    def colorBackgroundList(self):
        """
        Color the background of displayed objects in objectlist and call
        changeIcon to add the right icon
        """
        displayedObNames = []
        for i in range(len(self.displayedObjects)):
            displayedObNames.append(self.displayedObjects[i].name)
        for i in range(len(self.aobjects)):
            item = Qt.QObject.findChild(
                self.awidget, QtCore.QObject, "objectslist"
            ).item(i)
            if item.text() in displayedObNames:
                self.changeIcon(item, i, "check")
                item = Qt.QObject.findChild(
                    self.awidget, QtCore.QObject, "objectslist"
                ).item(i)
                item.setBackground(QColor("#7fc97f"))
            else:
                self.changeIcon(item, i)
                item = Qt.QObject.findChild(
                    self.awidget, QtCore.QObject, "objectslist"
                ).item(i)
                item.setBackground(QColor("transparent"))

    def changeIcon(self, item, i, icon=None):
        """
        Adds empty icon if object is not displayed and check icon if displayed.
        """

        objectlist = Qt.QObject.findChild(
            self.awidget, QtCore.QObject, "objectslist"
        )
        row = objectlist.row(item)
        # remove item from objectlist
        objectlist.takeItem(row)
        object_name = self.aobjects[i].name
        # Add blank icon as spaceItem
        sources_images_dir = Config().getSourceImageDir()
        if icon == "check":
            icon = QIcon(os.path.join(sources_images_dir, "check.png"))
        else:
            icon = QIcon(os.path.join(sources_images_dir, "BLANK_ICON.png"))
        new_item = Qt.QListWidgetItem(icon, object_name)
        # reinsert new item with blank icon
        objectlist.insertItem(row, new_item)

    def addObject(self, obj):
        """
        Display an object in all windows
        """
        a = ana.Anatomist("-b")
        if obj not in self.displayedObjects:
            self.displayedObjects.append(obj)
        self.disableButtons()
        opts = {}
        if obj.objectType == "VOLUME":
            # volumes have a specific function since several volumes have to be
            # fusionned, and a volume rendering may occur
            self.addVolume(obj, opts)
            return
        elif obj.objectType == "SURFACE":
            self.addMesh(obj, opts)
            return
        elif obj.objectType == "GRAPH":
            opts["add_graph_nodes"] = 1

        a.addObjects(obj, self.awindows, **opts)

    def removeObject(self, obj):
        """
        Hides an object from views
        """
        a = ana.Anatomist("-b")
        if obj in self.displayedObjects:
            self.displayedObjects.remove(obj)
        self.disableButtons()
        if obj.objectType == "VOLUME":
            self.removeVolume(obj)
        elif obj.objectType == "SURFACE":
            self.removeMesh(obj)
        else:
            a.removeObjects(obj, self.awindows, remove_children=True)

    def fileOpen(self):
        """
        File browser + load object(s)
        """
        if not self.fdialog:
            self.fdialog = Qt.QFileDialog()
            self.fdialog.setDirectory(os.path.expanduser("~"))
        else:
            fd2 = self.fdialog
            self.fdialog = Qt.QFileDialog()
            self.fdialog.setDirectory(fd2.directory())
            self.fdialog.setHistory(fd2.history())
        self.fdialog.setFileMode(self.fdialog.ExistingFiles)
        self.fdialog.show()
        res = self.fdialog.exec_()
        if res:
            fnames = self.fdialog.selectedFiles()
            files = []
            for fname in fnames:
                print(str(fname))
                files.append(str(fname))
            self.loadObject(files)

    def selectedObjects(self):
        """
        list of objects selected in the list box on the upper left panel
        """
        olist = Qt.QObject.findChild(
            self.awidget, QtCore.QObject, "objectslist"
        )
        sobjs = []
        for o in olist.selectedItems():
            sobjs.append(str(o.text()).strip("\0"))
        return [o for o in self.aobjects if o.name in sobjs]

    def editAdd(self):
        """
        Display selected objects"""
        objs = self.selectedObjects()
        for o in objs:
            self.addObject(o)
        self.colorBackgroundList()

    def editRemove(self):
        """
        Hide selected objects"""
        objs = self.selectedObjects()
        for o in objs:
            self.removeObject(o)
        self.colorBackgroundList()

    def editDelete(self):
        """
        Delete selected objects"""
        objs = self.selectedObjects()
        self.deleteObjects(objs)

    def deleteObjects(self, objs):
        """Delete the given objects"""
        a = ana.Anatomist("-b")
        for o in objs:
            self.removeObject(o)
        olist = Qt.QObject.findChild(
            self.awidget, QtCore.QObject, "objectslist"
        )
        for o in objs:
            olist.takeItem(
                olist.row(olist.findItems(o.name, QtCore.Qt.MatchExactly)[0])
            )
        self.aobjects = [o for o in self.aobjects if o not in objs]
        a.deleteObjects(objs)

    def deleteObjectsFromFiles(self, files):
        """
        Delete the given objects given by their file names
        """
        a = ana.Anatomist("-b")
        objs = [o for o in a.getObjects() if o.filename in files]
        self.deleteObjects(objs)

    def closeAll(self, close_ana=True):
        """Exit"""

        print("Exiting Ana2")
        self.newWindow.close()
        a = ana.Anatomist("-b")
        # remove windows from their parent to prevent them to be brutally
        # deleted by Qt.
        w = None

        for w in self.awindows:
            try:
                w.hide()

            except Exception:
                continue  # window closed by Qt ?

            self.viewgridlay.removeWidget(w.internalRep._get())
            w.setParent(None)

        del w
        self.awindows = []
        self.displayedObjects = []
        self.viewgridlay = None
        self.volrender = None
        self.fusion2d = []
        self.mesh3d = {}
        self.aobjects = []
        self.awidget.close()
        self.awidget = None
        del self.fdialog

        if close_ana:
            a = ana.Anatomist()
            a.close()

    def stopVolumeRendering(self):
        """Disable volume rendering: show a slice instead"""

        a = ana.Anatomist("-b")

        if not self.volrender:
            return

        a.deleteObjects(self.volrender)
        self.volrender = None

        if len(self.fusion2d) != 0:
            if self.fusion2d[0] is not None:
                obj = self.fusion2d[0]

            else:
                obj = self.fusion2d[1]

        wins = [w for w in self.awindows if w.subtype() == 0]
        a.addObjects(obj, wins)
        self.control_3d_type = "LeftSimple3DControl"
        a.execute("SetControl", windows=wins, control=self.control_3d_type)

    def startVolumeRendering(self):
        """Enable volume rendering in 3D views"""
        a = ana.Anatomist("-b")
        if len(self.fusion2d) == 0:
            return
        if self.fusion2d[0] is not None:
            obj = self.fusion2d[0]
        else:
            obj = self.fusion2d[1]
        wins = [x for x in self.awindows if x.subtype() == 0]
        if len(wins) == 0:
            return
        vr = a.fusionObjects([obj], method="VolumeRenderingFusionMethod")
        vr.releaseAppRef()
        clip = a.fusionObjects([vr], method="FusionClipMethod")
        clip.releaseAppRef()
        self.volrender = [clip, vr]
        a.removeObjects(obj, wins)
        a.addObjects(clip, wins)
        self.control_3d_type = "VolRenderControl"
        a.execute("SetControl", windows=wins, control=self.control_3d_type)

    def enableVolumeRendering(self, on):
        """Enable/disable volume rendering in 3D views"""
        self._vrenabled = on
        if self._vrenabled:
            self.startVolumeRendering()
        else:
            self.stopVolumeRendering()

    def open_anatomist_main_window(self):
        """Blabla"""

        a = ana.Anatomist()
        cw = a.getControlWindow()
        a.execute("CreateControlWindow")
        if not cw:
            anacontrolmenu = sys.modules.get("anacontrolmenu")
            if anacontrolmenu:
                anacontrolmenu.add_gui_menus()

    def coordsChanged(self):
        """set the cursor on the position entered in the coords fields"""
        a = ana.Anatomist("-b")
        if len(self.awindows) == 0:
            return

        def findChild(x, y):
            """Blabla"""

            return Qt.QObject.findChild(x, QtCore.QObject, y)

        pos = [
            float(findChild(self.awidget, "coordXEdit").text()),
            float(findChild(self.awidget, "coordYEdit").text()),
            float(findChild(self.awidget, "coordZEdit").text()),
        ]
        # take coords transformation into account
        tr = a.getTransformation(
            a.mniTemplateRef, self.awindows[0].getReferential()
        )
        if tr is not None:
            pos = tr.transform(pos)
        t = float(findChild(self.awidget, "coordTEdit").text())
        a.execute(
            "LinkedCursor", window=self.awindows[0], position=pos[:3] + [t]
        )

    def dragEnterEvent(self, win, event):
        """Blabla"""

        x = ana.cpp.QAObjectDrag.canDecode(
            event
        ) or ana.cpp.QAObjectDrag.canDecodeURI(event)
        if x:
            event.accept()
        else:
            event.reject()

    def dropEvent(self, win, event):
        """Blabla"""

        a = ana.Anatomist("-b")
        o = ana.cpp.set_AObjectPtr()
        if ana.cpp.QAObjectDrag.decode(event, o):
            for obj in o:
                ob = a.AObject(o)
                if ob not in self.aobjects:
                    self.registerObject(ob)
                else:
                    self.addObject(ob)
            event.accept()
            return
        else:
            things = ana.cpp.QAObjectDrag.decodeURI(event)
            if things is not None:
                for obj in things[0]:
                    objnames = [x.fileName() for x in self.aobjects]
                    if obj not in objnames:
                        self.loadObject(obj)
                    else:
                        o = [x for x in self.aobjects if x.fileName() == obj][
                            0
                        ]
                        self.addObject(o)
                # TODO: things[1]: .ana scripts
                event.accept()
                return
        event.reject()

    def popup_objects(self):
        """
        Right-click popup on objects list
        """
        sel = self.selectedObjects()
        if len(sel) == 0:
            return
        t = aims.Tree()
        osel = [o.getInternalRep() for o in sel]
        menu = ana.cpp.OptionMatcher.popupMenu(osel, t)
        prop = menu.addAction("Object properties")
        prop.triggered.connect(self.object_properties)
        new_view = menu.addAction("Open in new view")
        new_view.triggered.connect(lambda: self.addNewView(sel[0]))
        menu.exec_(Qt.QCursor.pos())

    def object_properties(self):
        """
        Display selected objects properties in a browser window
        """
        a = ana.Anatomist("-b")
        if (
            not hasattr(self, "browser")
            or not self.browser
            or self.browser.isNull()
            or not self.browser.isVisible()
        ):
            self.browser = a.createWindow("Browser")
        else:
            self.browser.removeObjects(self.browser.Objects())
        self.browser.addObjects(self.selectedObjects())

    def addNewView(self, object):
        """
        Opens a popup with a view of the object
        Default display is axial view but can be changed
        """
        self.newWindow.showPopup(object)
