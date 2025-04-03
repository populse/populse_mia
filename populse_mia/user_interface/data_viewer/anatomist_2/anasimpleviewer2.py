"""
This the anasimpleviewer2 module, a module derived from pyanatomist's
anasimpleviewer module
(brainvisa/anatomist-gpl/pyanatomist/python/anatomist/simpleviewer/
anasimpleviewer.py)

This module is a viewer for 2D/3D images, and is used in Mia.
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
import sys
import time

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

logger = logging.getLogger(__name__)
anatomist_available = True

try:
    import anatomist.direct.api as ana

except ImportError:
    anatomist_available = False
    logger.warning(
        "Anatomist seems not to be installed. The data_viewer anatomist "
        "and anatomist_2 will not work..."
    )

try:
    #  The following imports have to be made after the qApp.startingUp() test
    #  since they do instantiate Anatomist for registry to work.
    from anatomist.cpp.simplecontrols import (
        Simple2DControl,
        registerSimpleControls,
    )
except ImportError:

    if anatomist_available:
        logger.warning(
            "Anatomist seems not to be installed. The data_viewer anatomist "
            "and anatomist_2 will not work..."
        )

# Determine whether we are using Qt4 or Qt5, and hack a little bit accordingly
# the boolean qt4 global variable will tell it for later usage
qt_backend.set_qt_backend(compatible_qt5=True)


class LeftSimple3DControl(Simple2DControl):
    """
    Control for 3D navigation using the left mouse button.

    This control is particularly useful for touch devices where
    rotation can be achieved by pressing and holding the left mouse button.
    """

    def __init__(self, prio=25, name="LeftSimple3DControl"):
        """
        Initializes the LeftSimple3DControl instance.

        :param prio (int): The priority level for the control
                           (default is 25).
        :param name (str): The name of the control
                           (default is "LeftSimple3DControl").
        """
        super().__init__(prio, name)

    def eventAutoSubscription(self, pool):
        """
        Auto-subscribes to mouse and keyboard events relevant for 3D
        controls.

        This method sets up event subscriptions for mouse button actions
        and keyboard shortcuts to control the trackball actions.

        :param pool: The event pool to which the subscriptions will be made.
        """
        key = QtCore.Qt
        NoModifier = key.NoModifier
        ControlModifier = key.ControlModifier
        super().eventAutoSubscription(pool)
        # Subscribes to left button mouse events for continuous trackball
        # movement
        self.mouseLongEventUnsubscribe(key.LeftButton, NoModifier)
        self.mouseLongEventSubscribe(
            key.LeftButton,
            NoModifier,
            pool.action("ContinuousTrackball").beginTrackball,
            pool.action("ContinuousTrackball").moveTrackball,
            pool.action("ContinuousTrackball").endTrackball,
            True,
        )
        # Subscribes to space key press for starting or stopping the trackball
        self.keyPressEventSubscribe(
            key.Key_Space,
            ControlModifier,
            pool.action("ContinuousTrackball").startOrStop,
        )
        # Subscribes to middle mouse button for executing link actions
        self.mousePressButtonEventSubscribe(
            key.MiddleButton, NoModifier, pool.action("LinkAction").execLink
        )


class VolRenderControl(LeftSimple3DControl):
    """
    Control for volume rendering navigation using the middle mouse button.

    This control allows users to rotate the cut slice of the volume
    rendering by holding down the middle mouse button.
    """

    def __init__(self, prio=25, name="VolRenderControl"):
        """
        Initializes the VolRenderControl instance.

        :param prio (int): The priority level for the control
                           (default is 25).
        :param name (str): The name of the control
                           (default is "VolRenderControl").
        """
        super().__init__(prio, name)

    def eventAutoSubscription(self, pool):
        """
        Auto-subscribes to mouse events for cut slice rotation.

        This method overrides the base class behavior to subscribe to
        events triggered by the middle mouse button for controlling the
        track cut action.

        :param pool: The event pool to which the subscriptions will be made.
        """
        super().eventAutoSubscription(pool)
        # Unsubscribe from any previous middle button long events
        self.mouseLongEventUnsubscribe(Qt.Qt.MiddleButton, Qt.Qt.NoModifier)
        # Subscribe to middle button long events for track cut actions
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
    AnaSimpleViewer is a simple viewer application and widget.

    It can be used via the "anasimpleviewer.py" command or included as a
    library module in a custom widget.

    The viewer contains an object list and four 3D views (anatomist windows).
    Objects loaded are added to all views and can be toggled using the "add"
    and "remove" buttons.

    This class handles methods for menu/actions callbacks and utility
    functions for loading/viewing objects, as well as for removal and
    deletion.

    Note: The class inherits from QObject but is not a QWidget. The widget can
    be accessed through the `awidget` attribute of the instance.

    Additionally, some global Anatomist config variables may be set within
    AnaSimpleViewer, initiated optionally via the `init_global_handlers`
    method called by the constructor unless `init_global_handlers` is set
    to False.
    """

    _global_handlers_initialized = False

    def __init__(self, init_global_handlers=None):
        """
         Initializes the AnaSimpleViewer2 instance.

        :param init_global_handlers (bool): Determines if global handlers
                                            should be initialized (default
                                            is True).
        """
        super().__init__()
        a = ana.Anatomist("-b")

        if init_global_handlers:
            self.init_global_handlers()

        # Load UI file for dataviewer anasimpleviewer_2
        uifile = "mainwindow.ui"
        current_dir = os.getcwd()
        mainwindowdir = os.path.dirname(__file__)
        os.chdir(mainwindowdir)
        awin = loadUi(os.path.join(mainwindowdir, uifile))
        os.chdir(current_dir)
        self.awidget = awin
        # Initialization for popup, GUI action callbacks, etc.
        self.newWindow = NewWindowViewer()
        self.setup_gui_connections(awin)
        self._vrenabled = False
        self.meshes2d = {}
        self.setup_anatomist(a)
        # Other initialization
        self.initialize_components(awin)
        self.setup_color_palette_and_slider()

    def setup_gui_connections(self, awin):
        """
        Connects GUI actions to their respective callbacks.

        :param awin (Qt.QWidget): The main window widget to connect
                                  actions to.
        """
        # Connect actions to their slots
        awin.findChild(QtCore.QObject, "actionTimeRunning").triggered.connect(
            self.automaticRunning
        )
        awin.findChild(QtCore.QObject, "fileOpenAction").triggered.connect(
            self.fileOpen
        )
        awin.findChild(QtCore.QObject, "fileExitAction").triggered.connect(
            self.closeAll
        )
        awin.findChild(QtCore.QObject, "editAddAction").triggered.connect(
            self.editAdd
        )
        awin.findChild(QtCore.QObject, "editRemoveAction").triggered.connect(
            self.editRemove
        )
        awin.findChild(QtCore.QObject, "editDeleteAction").triggered.connect(
            self.editDelete
        )
        awin.findChild(
            QtCore.QObject, "viewEnable_Volume_RenderingAction"
        ).toggled.connect(self.enableVolumeRendering)
        awin.findChild(
            QtCore.QObject, "viewOpen_Anatomist_main_window"
        ).triggered.connect(self.open_anatomist_main_window)

        # Set validators and connect coordinate edits to change event
        for coord in ["X", "Y", "Z", "T"]:
            le = awin.findChild(QtCore.QObject, f"coord{coord}Edit")
            le.setValidator(Qt.QDoubleValidator(le))
            le.editingFinished.connect(self.coordsChanged)

        del le
        # Set context menu for objects list
        objects_list = awin.findChild(QtCore.QObject, "objectslist")
        objects_list.setContextMenuPolicy(Qt.Qt.CustomContextMenu)
        objects_list.customContextMenuRequested.connect(self.popup_objects)
        # Set drag and drop events
        awin.dropEvent = lambda awin, event: self.dropEvent(awin, event)
        awin.dragEnterEvent = lambda awin, event: self.dragEnterEvent(
            awin, event
        )
        awin.setAcceptDrops(True)

    def setup_anatomist(self, a):
        """
        Registers the Anatomist controls and options.

        :param a: The Anatomist instance.
        """
        # Register the function on the cursor notifier of anatomist.
        # It will be called when the user clicks on a window.
        a.onCursorNotifier.add(self.clickHandler)
        # viewWindow: parent widget for anatomist windows
        self.viewWindow = self.awidget.findChild(QtCore.QObject, "windows")

    def initialize_components(self, awin):
        """
        Initializes the component attributes and user interface.

        :param awin: The main window widget.
        """
        self.viewgridlay = Qt.QHBoxLayout(self.viewWindow)
        self.combobox = Qt.QComboBox()
        self.slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.fdialog = None
        self.awindows = []
        self.aobjects = []
        self.files = []
        self.displayedObjects = []
        # Initializing additional attributes
        self.fusion2d = []
        self.volrender = None
        self.control_3d_type = "LeftSimple3DControl"
        # Populate available palettes and connect buttons
        self.available_palettes = [
            "B-W_LINEAR",
            "Yellow-red",
            "RAINBOW",
            "Yellow-Red-White-Blue-Green",
            "blue-red-bright-dark",
        ]
        self.viewButtons = [
            awin.findChild(QtCore.QObject, "actionAxial"),
            awin.findChild(QtCore.QObject, "actionSagittal"),
            awin.findChild(QtCore.QObject, "actionCoronal"),
            awin.findChild(QtCore.QObject, "action3D"),
        ]

        for action in self.viewButtons:
            action.triggered.connect(self.newDisplay)

        awin.findChild(
            QtCore.QObject, "objectslist"
        ).itemSelectionChanged.connect(self.disableButtons)

    def setup_color_palette_and_slider(self):
        """
        Sets up the color palette dropdown and opacity slider in the toolbar.
        """
        self.setComboBox()
        self.setSlider()
        self.combobox.currentIndexChanged.connect(self.newPalette)
        self.slider.valueChanged.connect(self.changeOpacity)

    def init_global_handlers(self):
        """
        Set some global controls/settings in Anatomist application object.
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
            a.config()["windowSizeFactor"] = 1.0
            a.config()["commonScannerBasedReferential"] = 1
            # Register controls
            cm = ana.cpp.ControlManager.instance()
            cm.addControl("QAGLWidget3D", "", "Simple2DControl")
            cm.addControl("QAGLWidget3D", "", "LeftSimple3DControl")
            cm.addControl("QAGLWidget3D", "", "VolRenderControl")
            logger.info("Controls registered.")
            del cm
            a.setGraphParams(label_attribute="label")
            AnaSimpleViewer2._global_handlers_initialized = True

    def setComboBox(self):
        """
        Inserts a drop-down menu in the toolbar containing available color
        palettes. The default color palettes are in self.available_palettes.
        """
        toolBar = self.awidget.findChild(QtCore.QObject, "toolBar")
        actionAutoRunning = self.awidget.findChild(
            QtCore.QObject, "actionTimeRunning"
        )
        label = QLabel("Palette: ")
        label.setToolTip("Change color palette of selected object")

        for palette in self.available_palettes:
            self.combobox.addItem(palette)

        toolBar.insertWidget(actionAutoRunning, label)
        toolBar.insertWidget(actionAutoRunning, self.combobox)
        sources_images_dir = Config().getSourceImageDir()

        for i, palette in enumerate(self.available_palettes):
            icon = QIcon(os.path.join(sources_images_dir, palette))
            self.combobox.setItemIcon(i, icon)

        size = PyQt5.QtCore.QSize(200, 15)
        self.combobox.setIconSize(size)

    def setSlider(self):
        """
        Inserts an opacity slider in the toolbar.
        Minimum value is 0 and maximum value is 100.
        """
        toolBar = self.awidget.findChild(QtCore.QObject, "toolBar")
        actionAutoRunning = self.awidget.findChild(
            QtCore.QObject, "actionTimeRunning"
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
        Changes the opacity of the selected object based on the slider value.

        Changes the mixing rate between objects when multiple ones are
        displayed.
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
        Sets the chosen color palette in the toolbar drop-down menu to the
        selected object.
        """
        color = self.combobox.currentText()

        if self.selectedObjects():
            self.selectedObjects()[0].setPalette(palette=color)

    def setColorPalette(self):
        """
        Checks color palette of a selected object, displays it in the toolbar
        drop-down menu and adds it if it isn't already stored in
        self.available_palettes.

        If corresponding palette image exists it is added, otherwise only
        the name of the palette appears.
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
        Changes the configuration based on user settings.

        :param config (str): "neuro" or "radio".
        """
        a = ana.Anatomist("-b")
        a.config()["axialConvention"] = config
        self.newDisplay()

    def changeRef(self):
        """
        Changes the referential and reloads objects.

        ref : Boolean
        0 : World coordinates
        1 : Image referential
        """
        self.deleteObjects(self.aobjects)
        self.loadObject(self.files, config_changed=True)

    def clickHandler(self, eventName, params):
        """
        Callback for linked cursor. In volume rendering mode, it syncs the
        VR slice to the linked cursor and updates the volume values view.

        :param eventName (str): The name of the event (unused)
        :param params (dict): Parameters related to the event,
                              including position and window.
        """
        a = ana.Anatomist("-b")
        pos = params["position"]
        win = params["window"]
        wref = win.getReferential()
        # Display coords in MNI referential (preferably)
        tr = a.getTransformation(wref, a.mniTemplateRef)
        pos2 = tr.transform(pos[:3]) if tr else pos
        self.awidget.findChild(QtCore.QObject, "coordXEdit").setText(
            f"{pos2[0]:8.3f}"
        )
        self.awidget.findChild(QtCore.QObject, "coordYEdit").setText(
            f"{pos2[1]:8.3f}"
        )
        self.awidget.findChild(QtCore.QObject, "coordZEdit").setText(
            f"{pos2[2]:8.3f}"
        )
        t = self.awidget.findChild(QtCore.QObject, "coordTEdit")
        t.setText(f"{pos[3] if len(pos) >= 4 else 0:8.3f}")
        # Display volumes values at the given position
        self.updateVolumeValues(win, a, pos)

        # Update volume rendering when it is enabled
        if self._vrenabled and self.volrender:
            self.updateRendering(win, a, pos)

    def updateVolumeValues(self, win, a, pos):
        """
        Updates the volume values displayed based on the cursor position.

        :param win: The current window instance for transformations.
        :param a: The Anatomist instance for transformation.
        :param pos: The current position of the cursor.
        """
        valbox = self.awidget.findChild(QtCore.QObject, "volumesBox")
        valbox.clear()
        valbox.setColumnCount(2)
        valbox.setHorizontalHeaderLabels(["Volume:", "Value:"])

        if len(self.fusion2d) > 1:
            valbox.setRowCount(len(self.fusion2d) - 1)
            valbox.setVerticalHeaderLabels([""] * (len(self.fusion2d) - 1))

        for i, obj in enumerate(self.fusion2d[1:], start=0):
            aimsv = ana.cpp.AObjectConverter.aims(obj)
            oref = obj.getReferential()
            tr = a.getTransformation(win.getReferential(), oref)
            pos2 = tr.transform(pos[:3]) if tr else pos[:3]
            vs = obj.voxelSize()
            pos2 = [int(round(x / y)) for x, y in zip(pos2, vs)]
            newItem = Qt.QTableWidgetItem(obj.name)
            valbox.setItem(i, 0, newItem)

            # Check bounds
            if all(
                0 <= p < size
                for p, size in zip(
                    pos2 + [pos[3]],
                    [
                        aimsv.getSizeX(),
                        aimsv.getSizeY(),
                        aimsv.getSizeZ(),
                        aimsv.getSizeT(),
                    ],
                )
            ):
                txt = str(aimsv.value(*pos2))

            else:
                txt = ""

            newitem = Qt.QTableWidgetItem(txt)
            valbox.setItem(i, 1, newitem)

        valbox.resizeColumnsToContents()

    def updateRendering(self, win, a, pos):
        """
        Updates volume rendering based on the current cursor position.

        :param win: The current window instance.
        :param a: The Anatomist instance.
        :param pos: The current cursor position.
        """
        clip = self.volrender[0]
        t = a.getTransformation(win.getReferential(), clip.getReferential())

        if t:
            pos = t.transform(pos[:3])

        clip.setOffset(pos[:3])
        clip.notifyObservers()

    def automaticRunning(self):
        """
        Enables the automatic running of functional images.
        The frame rate can be changed in preferences by the user.
        """
        a = ana.Anatomist("-b")
        objects = []
        im_sec = float(Config().getViewerFramerate())
        frame_rate = 1 / im_sec
        t = self.awidget.findChild(QtCore.QObject, "coordTEdit")
        sources_images_dir = Config().getSourceImageDir()
        pauseIcon = QIcon(os.path.join(sources_images_dir, "pause.png"))
        playIcon = QIcon(os.path.join(sources_images_dir, "play.png"))

        for obj in self.displayedObjects:
            objects.append(ana.cpp.AObjectConverter.aims(obj).getSizeT())

        if objects:
            nb_images = max(objects)

        else:
            return

        list_im = list(range(nb_images))
        coord_x_edit = self.awidget.findChild(QtCore.QObject, "coordXEdit")
        coord_y_edit = self.awidget.findChild(QtCore.QObject, "coordYEdit")
        coord_z_edit = self.awidget.findChild(QtCore.QObject, "coordZEdit")
        pos = [
            float(coord_x_edit.text()),
            float(coord_y_edit.text()),
            float(coord_z_edit.text()),
        ]
        i = int(
            float(self.awidget.findChild(QtCore.QObject, "coordTEdit").text())
        )

        if i == nb_images - 1:
            i = 0

        playAction = self.awidget.findChild(
            QtCore.QObject, "actionTimeRunning"
        )

        while playAction.isChecked() and i < len(list_im):
            start_time = time.time()
            playAction.setIcon(pauseIcon)
            t.setText(f"{list_im[i]:8.3f}")
            a.execute(
                "LinkedCursor",
                window=self.awindows[0],
                position=pos[:3] + [list_im[i]],
            )
            PyQt5.QtWidgets.QApplication.processEvents()
            running_time = time.time() - start_time

            # If iteration takes to much time we don't want to
            # make it sleep any longer (happens when fusion of images).
            if running_time < frame_rate:
                time.sleep(frame_rate - running_time)

            i += 1

        playAction.setIcon(playIcon)

    def createWindow(self, wintype="Axial"):
        """
        Opens a new window in the windows grid layout.

        The new window will be set in MNI referential (except 3D for the
        moment, due to a problem with rendering volumes in direct
        reference) and assigned the custom control without menus/toolbars.

        :param wintype (str): The type of window to create
                              ("Axial", "Sagittal", "Coronal" or "3D").
        """
        a = ana.Anatomist("-b")
        w = a.createWindow(wintype, no_decoration=True, options={"hidden": 1})
        w.setAcceptDrops(False)
        x, y = 0, 0
        i = 0

        if not hasattr(self, "_winlayouts"):
            self._winlayouts = [[0, 0], [0, 0]]

        else:

            for y in (0, 1):

                for x in (0, 1):
                    i += 1

                    if not self._winlayouts[x][y]:
                        break

                else:
                    continue

                break

        self.viewgridlay.addWidget(w.getInternalRep())
        self._winlayouts[x][y] = 1
        # Keep it in anasimpleviewer list of windows
        self.awindows.append(w)

        # Set custom control
        if wintype == "3D":
            a.execute("SetControl", windows=[w], control=self.control_3d_type)

        else:
            a.execute("SetControl", windows=[w], control="Simple2DControl")
            a.assignReferential(a.mniTemplateRef, w)

            # Force redrawing in MNI orientation
            # (there should be a better way to do so...)
            if wintype == "Axial":
                w.muteAxial()
                logger.info(f"MUTEAXIAL {w.muteAxial}")

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
        Creates windows that will contain the specified views.

        This method sets a predefined camera angle for the 3D view and
        checks the appropriate view buttons upon creation.

        :param views (list[str]): A list of strings specifying the view types
                                  to create. Acceptable values include
                                  "axial", "sagittal", "coronal", and "3D".
        """

        for view in views:
            self.createWindow(view)

            if view == "3D":
                # Set a specific camera angle for the 3D view
                a = ana.Anatomist("-b")
                a.execute(
                    "Camera",
                    windows=[self.awindows[-1]],
                    view_quaternion=[0.404603, 0.143829, 0.316813, 0.845718],
                )

        # Sets view buttons checked for the initial display
        if views == ["Axial", "Sagittal", "Coronal"]:
            counter = 0

            for counter, view in enumerate(views):
                self.viewButtons[counter].setChecked(True)

    def deleteTotalWindow(self):
        """
        Clears all existing windows and fusions to prepare for a new display.

        This method removes all windows from the grid layout and clears
        the 2D fusion objects. It ensures that no residual elements
        affect the new display setup.
        """
        self.awindows.clear()
        self.fusion2d.clear()

        # Safely delete widgets from the layout in reverse order
        for index in reversed(range(self.viewgridlay.count())):
            item = self.viewgridlay.itemAt(index)

            if item and item.widget() is not None:  # Ensure the widget exists
                item.widget().deleteLater()

    def getViewsToDisplay(self):
        """
        Determines which views need to be displayed based on the state of the
        view buttons.

        :return (list[str]): The views to be displayed. Possible values are
                             "Axial", "Sagittal", "Coronal", and "3D".
        """
        view_labels = ["Axial", "Sagittal", "Coronal", "3D"]
        views = [
            label
            for button, label in zip(self.viewButtons, view_labels)
            if button.isChecked()
        ]

        return views

    def viewReferential(self, obj):
        """
        Centers the view on the specified object and sets the referential.

        :param obj: The object to visualize. The object's bounding box is used
                    to determine the center position for visualization.
        """
        a = ana.Anatomist("-b")
        bb = obj.boundingbox()
        position = (aims.Point3df(bb[1][:3]) - bb[0][:3]) / 2.0
        wrefs = [w.getReferential() for w in self.awindows]
        srefs = {r.uuid() for r in wrefs}

        if len(srefs) != 1:

            # Not all windows in the same reference
            if aims.StandardReferentials.mniTemplateReferentialID() in srefs:
                wref_id = aims.StandardReferentials.mniTemplateReferentialID()
                wref = next(r for r in wrefs if r.uuid() == wref_id)

            elif aims.StandardReferentials.acPcReferentialID() in srefs:
                wref = a.centralReferential()

            elif (
                aims.StandardReferentials.commonScannerBasedReferentialID()
                in srefs
            ):
                wref_id = (
                    aims.StandardReferentials.commonScannerBasedReferentialID()
                )
                wref = next(r for r in wrefs if r.uuid() == wref_id)

            else:
                wref = wrefs[0]

            for w in self.awindows:
                w.setReferential(wref)

        else:
            wref = wrefs[0]

        t = a.getTransformation(obj.getReferential(), wref)

        if not t and obj.getReferential() != wref:
            # Attempt to link to a scanner-based reference
            # and connect it to MNI
            wref_id = (
                aims.StandardReferentials.commonScannerBasedReferentialID()
            )
            sbref = next(
                (r for r in a.getReferentials() if r.uuid() == wref_id), None
            )

            if sbref:
                t2 = a.getTransformation(obj.getReferential(), sbref)

                if t2:
                    a.execute(
                        "LoadTransformation",
                        origin=sbref,
                        destination=a.mniTemplateRef,
                        matrix=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                    )

                else:
                    # Assume the object is in the central referential
                    a.execute(
                        "LoadTransformation",
                        origin=obj.getReferential(),
                        destination=a.centralRef,
                        matrix=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                    )
                t = a.getTransformation(
                    obj.getReferential(), self.awindows[0].getReferential()
                )

        if t:
            position = t.transform(position)

        a.execute("LinkedCursor", window=self.awindows[0], position=position)

        for w in self.awindows:
            w.focusView()

    def checkviews(self):
        """
        Prevents closing the last opened view.

        This method checks how many view buttons are enabled. If only one
        view button is checked, it disables that button to prevent closing
        the last view. Otherwise, all buttons remain enabled.
        """
        nb_views_checked = sum(
            button.isChecked() for button in self.viewButtons
        )

        # Disable the checked button if only one is checked;
        # enable all otherwise
        for button in self.viewButtons:
            button.setEnabled(nb_views_checked != 1 or not button.isChecked())

    def newDisplay(self):
        """
        Performs a new display of windows, objects, and views.

        This method checks the state of view buttons, deletes any existing
        windows and displayed objects, initializes new views based on the
        state of the view buttons, and adds existing objects to the new
        display.
        """
        self.checkviews()
        self.deleteTotalWindow()
        views = self.getViewsToDisplay()
        self.createTotalWindow(views)

        # Add displayed objects to the new windows
        # and set their reference views
        for obj in self.displayedObjects:
            self.addObject(obj)
            self.viewReferential(obj)

    def loadObject(self, files, config_changed=None):
        """
        Loads objects from the specified files and prepares them for display.

        This method displays only the first loaded object. Subsequent objects
        are added to the object list but not displayed. If an object has
        already been imported, a warning message is shown.

        :param files (list[str]): A list of file names to load objects from.
        :param config_changed (bool): Indicates whether the configuration has
                                      changed. If True, the method will return
                                      early if an object has already been
                                      imported.
        """
        a = ana.Anatomist("-b")
        a.config()["setAutomaticReferential"] = Config().get_referential()
        a.config()["axialConvention"] = Config().getViewerConfig()

        # Progress indication
        loading_window = Qt.QWidget()
        loading_window.setWindowTitle("Loading Data")
        loading_window.move(800, 500)
        loading_window.resize(300, 50)
        loading_window.show()

        for i, fname in enumerate(files):

            if fname not in self.files:
                self.files.append(fname)

            objectlist = self.awidget.findChild(QtCore.QObject, "objectslist")

            # Check if the object has already been imported
            if any(
                os.path.basename(fname) == objectlist.item(w).text()
                for w in range(objectlist.count())
            ):

                if config_changed is True:
                    return

                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.setText(
                    "Some of your objects have already been imported."
                )
                msgBox.setWindowTitle("Warning")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
                return

            obj = a.loadObject(fname)

            if obj:

                if i == 0:
                    self.registerObject(obj)

                else:
                    objectlist.addItem(obj.name)
                    # Keep it in the global list
                    self.aobjects.append(obj)
                    self.colorBackgroundList()

                    if obj.objectType == "VOLUME":
                        # Check for adequate colormaps for volumes
                        hints = colormaphints.checkVolume(
                            ana.cpp.AObjectConverter.aims(obj)
                        )
                        obj.attributed()["colormaphints"] = hints

    @QtCore.Slot("anatomist::AObject *", "const std::string &")
    def objectLoaded(self, obj, filename):
        """
        Handles the event when an object is loaded.

        This method registers the loaded object with the Anatomist application
        and manages processing execution state.

        :param obj (AObject): The loaded object to be registered.
        :param filename (str): The name of the file from which the object
                               was loaded (unused).
        """
        a = ana.Anatomist("-b")

        if not obj:
            return

        loaded_object = a.AObject(a, obj)
        loaded_object.releaseAppRef()
        processor = a.theProcessor()
        reset_proc_exec = not processor.execWhileIdle()

        if reset_proc_exec:
            # Allow recursive command execution to ensure proper function
            processor.allowExecWhileIdle(True)

        self.registerObject(loaded_object)

        if reset_proc_exec:
            # Restore the previous state for recursive execution
            processor.allowExecWhileIdle(False)

    def registerObject(self, obj, views=None):
        """
        Registers an object in the AnaSimpleViewer's object list and
        displays it.

        :param obj: The object to register and display.
        :param views (list[str]): A list of view types to create if windows do
                                  not already exist.
        """
        ojectlist = self.awidget.findChild(QtCore.QObject, "objectslist")
        ojectlist.addItem(obj.name)
        # Keep track of the object globally
        self.aobjects.append(obj)
        self.displayedObjects.append(obj)
        self.colorBackgroundList()

        # Check for volume-specific color maps
        if obj.objectType == "VOLUME":
            # Volume are checked for possible adequate colormaps
            # prints the header of volume ana.cpp.AObjectConverter.aims(obj)
            hints = colormaphints.checkVolume(
                ana.cpp.AObjectConverter.aims(obj)
            )
            obj.attributed()["colormaphints"] = hints

        bb = obj.boundingbox()

        if not bb:
            # Not a viewable object
            return

        # Create the 4 windows if they don't exist
        if not self.awindows:
            self.createTotalWindow(views or ["Axial", "Sagittal", "Coronal"])

        # Display the object in the views
        self.addObject(obj)
        # Center the cursor on the object (workaround for a bug in Anatomist)
        self.viewReferential(obj)

    def _displayVolume(self, obj, opts=None):
        """
        Displays a volume or Fusion2D object in all available windows.

        If volume rendering is enabled, 3D views will display a clipped
        volume rendering of the object.

        :param obj (AObject): The volume or Fusion2D object to display.
        :param opts (dict): Additional options for rendering.
        """

        if opts is None:
            opts = {}

        a = ana.Anatomist("-b")

        if self._vrenabled:
            # Filter windows based on subtypes
            volume_wins = [x for x in self.awindows if x.subtype() != 0]

            if volume_wins:
                a.addObjects(obj, volume_wins, **opts)

            # Check for 2D windows
            slice_wins = [x for x in self.awindows if x.subtype() == 0]

            if not slice_wins:
                return

            vr = a.fusionObjects([obj], method="VolumeRenderingFusionMethod")
            vr.releaseAppRef()
            clip = a.fusionObjects([vr], method="FusionClipMethod")
            clip.releaseAppRef()
            self.volrender = [clip, vr]
            a.addObjects(clip, slice_wins, **opts)

        else:
            a.addObjects(obj, self.awindows, **opts)

    def addVolume(self, obj, opts=None):
        """
        Displays a volume in all windows.

        If multiple volumes are displayed, a Fusion2D will be created to
        wrap them all. If volume rendering is enabled, 3D views will display
        a clipped volume rendering of either the single volume (if only one
        is present) or the 2D fusion.

        :param obj: The volume object to be displayed.
        :param opts (dict): Additional options for rendering.
        """

        if opts is None:
            opts = {}

        a = ana.Anatomist("-b")

        if obj in self.fusion2d:
            return

        # Remove any previous volume rendering if it exists
        if self.volrender:
            a.deleteObjects(self.volrender)
            self.volrender = None

        # Handle single and multiple volume cases
        if not self.fusion2d:
            # Initial setup with the first object
            self.fusion2d = [None, obj]

        else:
            # Fusion of multiple objects
            fusobjs = self.fusion2d[1:] + [obj]
            f2d = a.fusionObjects(fusobjs, method="Fusion2DMethod")
            f2d.releaseAppRef()

            if self.fusion2d[0] is not None:
                # Remove the previous fusion
                a.deleteObjects(self.fusion2d[0])

            else:
                a.removeObjects(self.fusion2d[1], self.awindows)

            self.fusion2d = [f2d] + fusobjs
            # Use the newly created Fusion2D object
            obj = f2d

        # Assign color maps based on object type
        if obj.objectType == "VOLUME":

            if "volume_contents_likelihoods" in obj.attributed():
                cmap = colormaphints.chooseColormaps(
                    (obj.attributed()["colormaphints"],)
                )
                obj.setPalette(cmap[0])

        else:
            hints = [x.attributed()["colormaphints"] for x in obj.children]
            children = [
                x
                for x, y in zip(obj.children, hints)
                if "volume_contents_likelihoods" in y
            ]
            hints = [x for x in hints if "volume_contents_likelihoods" in x]
            cmaps = colormaphints.chooseColormaps(hints)

            for child, cmap in zip(children, cmaps):
                child.setPalette(cmap)

        # Call a lower-level function for display and volume rendering
        self._displayVolume(obj, opts)

    def removeVolume(self, obj, opts=None):
        """
        Hides a volume from the views.

        This method removes the specified volume object from the display.
        If multiple volumes are associated with the Fusion2D, it updates
        the Fusion2D object accordingly. If volume rendering is enabled,
        it also handles the cleanup of the rendered objects.

        :param obj: The volume object to be removed.
        :param opts (dict): Additional options for rendering.
        """

        if opts is None:
            opts = {}

        a = ana.Anatomist("-b")

        if obj in self.fusion2d:

            # Remove previous volume rendering if it exists
            if self.volrender:
                a.deleteObjects(self.volrender)
                self.volrender = None

            # Create list of objects excluding the one to remove
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

            # Update the fusion2d list based on remaining objects
            if not fusobjs:
                self.fusion2d = []

            else:
                self.fusion2d = [f2d] + fusobjs

            # Determine the object to display next
            if f2d:
                obj = f2d

            elif len(fusobjs) == 1:
                obj = fusobjs[0]

            else:
                # Exit if no valid object is left to display
                return

            self._displayVolume(obj, opts)

    def get_new_mesh2d_color(self):
        """
        Retrieves a new color for a 2D mesh that has not been used yet.

        This method checks the predefined list of colors and returns the first
        color that is not currently in use by any of the 2D meshes. If all
        colors have been used, it returns a color based on the total count
        of existing 2D meshes.

        :return tuple[float, float, float, float]: The RGBA color.
        """
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
            (1.0, 0.5, 1.0, 1.0),
        ]
        used_colors = {col for _, col in self.meshes2d.values()}

        for color in colors:

            if color not in used_colors:
                return color

        # If all colors have been used, return a color based
        # on the existing count.
        return colors[len(self.meshes2d) % len(colors)]

    def addMesh(self, obj):
        """
        Adds a 2D mesh representation of a volume object to the viewer.

        This method creates a 2D mesh from the given object and assigns a
        unique color. It then displays the mesh in the appropriate 2D windows
        and the original object in the 3D windows.

        :param obj: The volume object from which to create the mesh.
        """
        a = ana.Anatomist("-b")
        # Create a 2D mesh from the object's internal representation
        mesh2d = a.fusionObjects(
            [obj.getInternalRep()], method="Fusion2DMeshMethod"
        )
        # Get a new color for the mesh
        color = self.get_new_mesh2d_color()
        self.meshes2d[obj.getInternalRep()] = (mesh2d, color)
        # Set the color for the mesh material
        mesh2d.setMaterial(diffuse=color)
        mesh2d.releaseAppRef()
        windows_2d = [
            w
            for w in self.awindows
            if w.subtype()
            in (w.AXIAL_WINDOW, w.CORONAL_WINDOW, w.SAGITTAL_WINDOW)
        ]
        windows_3d = [w for w in self.awindows if w not in windows_2d]
        # Add the mesh to the 2D windows and the object to the 3D windows
        a.addObjects(mesh2d, windows_2d)
        a.addObjects(obj, windows_3d)

    def removeMesh(self, obj):
        """
        Removes the specified mesh and its associated object from the viewer.

        This method locates the mesh associated with the provided object,
        removes both the object and its mesh from the displayed windows,
        and updates the internal structures accordingly.

        :param obj: The volume object whose mesh is to be removed.
        """
        a = ana.Anatomist("-b")
        internal_rep = obj.getInternalRep()

        if internal_rep in self.meshes2d:
            mesh2d, _ = self.meshes2d[internal_rep]
            # Remove the object and its mesh from the displayed windows
            a.removeObjects([obj, mesh2d], self.awindows)
            del self.meshes2d[internal_rep]

    def disableButtons(self):
        """
        Disables the add and remove buttons based on the selected object's
        display status.

        This method checks the currently displayed objects and the selected
        item in the objects list. It disables the add button if an item is
        selected and currently displayed, and enables the remove button.
        If no object is urrently displayed or selected, it enables the
        add button.
        """
        self.setColorPalette()
        displayed_ob_names = [obj.name for obj in self.displayedObjects]
        selected_items = self.awidget.findChild(
            QtCore.QObject, "objectslist"
        ).selectedItems()
        # Determine the state of the buttons based on the selection
        add_button = self.awidget.findChild(QtCore.QObject, "editAddAction")
        remove_button = self.awidget.findChild(
            QtCore.QObject, "editRemoveAction"
        )

        if not self.displayedObjects or not selected_items:
            add_button.setEnabled(True)
            remove_button.setEnabled(False)

        else:
            selected_text = selected_items[0].text()
            is_displayed = selected_text in displayed_ob_names
            add_button.setEnabled(not is_displayed)
            remove_button.setEnabled(is_displayed)

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
                logger.info(f"{fname}")
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

        logger.info("Exiting Ana2 viewer.")
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
