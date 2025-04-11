"""
This module provides the `MiniViewer` class, which is a PyQt-based widget
designed for rapid visualization of medical scans. The `MiniViewer` allows
users to view and interact with 3D, 4D, and 5D NIfTI images, providing tools
to navigate through slices and time points.

Key Features:
- Visualize single images per scan with cursors to move in multiple dimensions.
- Display all images of the greater dimension of the scan.
- Support for 3D, 4D, and 5D NIfTI images.
- Configurable display settings, including orientation and slice navigation.
- Integration with project-specific configurations and preferences.

Contains:
    Class:
        - MiniViewer
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
from functools import partial

import nibabel as nib
import numpy as np  # a N-dimensional array object
import skimage as sk

# Populse_MIA imports
from packaging import version
from PyQt5 import QtCore

# PyQt5 imports
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# from scipy.ndimage import rotate  # to work with NumPy arrays
from skimage.transform import resize

from populse_mia.data_manager import COLLECTION_CURRENT, NOT_DEFINED_VALUE
from populse_mia.software_properties import Config
from populse_mia.user_interface.pop_ups import ClickableLabel, PopUpSelectTag

logger = logging.getLogger(__name__)


class MiniViewer(QWidget):
    """
    MiniViewer allows rapid visualization of scans with either a single image
    per scan or all images of the greater dimension of the scan.

    Displayed images depend on their dimension:
    - 3D: Display all slices.
    - 4D: Display the middle slice of the third dimension for each time of the
          fourth dimension.
    - 5D: Display the middle slice of the third dimension for the first time
          of the fourth dimension for each time of the fifth dimension.

    Note:
        - idx corresponds to the index of the displayed image
        - idx in [0, self.max_scans]
        - most of the class's attributes are lists of 0 to self.max_scans
           elements

    .. Methods:
        - __init__: initialise the MiniViewer object.
        - _create_layouts: Create the layouts for the MiniViewer
        - _initialize_checkboxes: Initialize the checkboxes for the MiniViewer
        - _initialize_components: Initialize the components of the MiniViewer

        - boxSlider: create sliders, their connections and thumbnail labels
                     for a selected index
        - changePosValue: change the value of a cursor for the selected index
        - check_box_cursors_state_changed: updates the config file
        - clear: remove the Nibabel images to be able to remove it in the
                 unit tests
        - clear_layouts: clear the final layout
        - createDimensionLabels: create the dimension labels for the
                                 selected index
        - createFieldValue: create a field where will be displayed the
                            position of a cursor
        - create_slider: create a slider
        - displayPosValue: display the position of each cursor for the
                           selected index
        - enableSliders: enable each slider of the selected index
        - image2DModifications: apply modifications to the image to
                                display it correctly
        - image_to_pixmap: create a 2D pixmap from a N-D Nifti image
        - indexImage: update the sliders values depending on the size of
                      the selected image
        - mem_release: reset all object lists to zero in order to
                       preserve memory
        - navigImage: display the 2D image for the selected index
        - openTagsPopUp: opens a pop-up to select the legend of the thumbnails
        - setThumbnail: set the thumbnail tag value under the image frame
        - show_slices: create the thumbnails from the selected file paths
        - update_nb_slices: update the config file and the thumbnails
        - update_visualization_method: update the config file and the
                                       thumbnails
        - verify_slices: verify the number of selected documents

    """

    def __init__(self, project):
        """
        Initialize the MiniViewer object.

        :param project: Current project in the software.
        """
        super().__init__()
        self.project = project
        self.first_time = True
        # The MiniViewer is set hidden to give more space to the data_browser
        self.setHidden(True)
        # Config that allows to read the software preferences
        self.config = Config()
        # When multiple selection, limiting the number of thumbnails to
        # max_scans
        self.max_scans = self.config.get_max_thumbnails()
        self.file_paths = ""
        self._initialize_components()
        self._create_layouts()
        self._initialize_checkboxes()

    def _create_layouts(self):
        """Create the layouts for the MiniViewer."""
        self.h_box_images = QHBoxLayout()
        self.h_box_images.setSpacing(10)
        self.v_box = QVBoxLayout()
        self.v_box_final = QVBoxLayout()
        self.h_box_slider_3D = QHBoxLayout()
        self.h_box_slider_4D = QHBoxLayout()
        self.h_box_slider_5D = QHBoxLayout()
        self.v_box_sliders = QVBoxLayout()
        self.h_box = QHBoxLayout()
        self.h_box_check_box = QHBoxLayout()
        self.v_box_thumb = QVBoxLayout()
        self.h_box_thumb = QHBoxLayout()
        self.setLayout(self.v_box_final)

    def _initialize_checkboxes(self):
        """Initialize the checkboxes for the MiniViewer."""
        self.check_box_slices = QCheckBox("Show all slices (no cursors)")
        self.check_box_slices.setCheckState(
            Qt.Checked if self.config.getShowAllSlices() else Qt.Unchecked
        )
        self.check_box_slices.stateChanged.connect(
            self.update_visualization_method
        )
        self.check_box_cursors = QCheckBox("Chain cursors")
        self.check_box_cursors.setToolTip(
            "Allows to connect all cursors when selecting multiple documents"
        )
        self.check_box_cursors.setCheckState(
            Qt.Checked if self.config.getChainCursors() else Qt.Unchecked
        )
        self.check_box_cursors.stateChanged.connect(
            self.check_box_cursors_state_changed
        )

    def _initialize_components(self):
        """Initialize the components of the MiniViewer."""
        self.labels = QWidget()
        self.frame = QFrame()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.frame)
        self.frame_final = QFrame()
        self.label_nb_slices = QLabel("Maximum number of slices: ")
        self.line_edit_nb_slices = QLineEdit(
            f"{self.config.getNbAllSlicesMax()}"
        )
        self.line_edit_nb_slices.returnPressed.connect(self.update_nb_slices)
        self.label_orientation = QLabel(
            "Radiological orientation"
            if self.config.isRadioView()
            else "Neurological orientation"
        )
        self.im_2D = []
        self.slider_3D = []
        self.slider_4D = []
        self.slider_5D = []
        self.txt_slider_3D = []
        self.txt_slider_4D = []
        self.txt_slider_5D = []
        self.label3D = []
        self.label4D = []
        self.label5D = []
        self.imageLabel = []
        self.img = []
        self.label_description = []

    def boxSlider(self, idx):
        """
        Define horizontal sliders connections and thumbnail labels.

        :param idx (int): The selected index.
        """
        self.slider_3D.insert(idx, self.create_slider(0, 0, 0))
        self.slider_4D.insert(idx, self.create_slider(0, 0, 0))
        self.slider_5D.insert(idx, self.create_slider(0, 0, 0))

        self.slider_3D[idx].valueChanged.connect(
            partial(self.changePosValue, idx, 1)
        )
        self.slider_4D[idx].valueChanged.connect(
            partial(self.changePosValue, idx, 2)
        )
        self.slider_5D[idx].valueChanged.connect(
            partial(self.changePosValue, idx, 3)
        )

        self.txt_slider_3D.insert(idx, self.createFieldValue())
        self.txt_slider_4D.insert(idx, self.createFieldValue())
        self.txt_slider_5D.insert(idx, self.createFieldValue())

    def changePosValue(self, idx, cursor_to_change):
        """
        Change the value of a cursor for the selected index.

        :param idx: the selected index
        :param cursor_to_change: the cursor to change (1, 2 or 3)
        """
        # If the "Chain cursors" mode is not selected, there is nothing to do
        if self.check_box_cursors.checkState() == Qt.Unchecked:
            self.navigImage(idx)
        else:
            # Checking with cursor has been modified
            if cursor_to_change == 1:
                cursor = self.slider_3D
            elif cursor_to_change == 2:
                cursor = self.slider_4D
            else:
                cursor = self.slider_5D

            # Loop on the thumbnails
            for idx_loop in range(min(self.max_scans, len(self.file_paths))):
                # Disconnecting the connection when changing other cursors
                # values
                cursor[idx_loop].valueChanged.disconnect()
                # Do something only when the cursor is not the one that has
                # been changed by the user
                if idx_loop != idx:
                    if cursor[idx].value() == cursor[idx].maximum():
                        value = cursor[idx_loop].maximum()

                    elif cursor[idx].value() == cursor[idx].minimum():
                        value = cursor[idx_loop].minimum()

                    else:
                        # Updating the new value as the value of the cursor
                        # that has been changed by the user
                        value = round(
                            (cursor[idx_loop].maximum() + 1)
                            * (cursor[idx].value() + 1)
                            / max(1, cursor[idx].maximum() + 1)
                        )
                        value = min(cursor[idx_loop].maximum(), value - 1)
                        value = max(0, int(value))
                    cursor[idx_loop].setValue(value)

                # Changing the image to show
                self.navigImage(idx_loop)
                # Reconnecting
                cursor[idx_loop].valueChanged.connect(
                    partial(self.changePosValue, idx_loop, cursor_to_change)
                )

    def check_box_cursors_state_changed(self):
        """
        Update the config file when the state of the checkbox to chain the
        cursors changes.
        """
        self.config.setChainCursors(
            self.check_box_cursors.checkState() == Qt.Checked
        )

    def clear(self):
        """
        Remove the Nibabel images to be able to remove it in the unit tests.
        """

        if hasattr(self, "img"):
            del self.img

    def clear_layouts(self):
        """Clear the final layout."""

        for i in reversed(range(self.v_box_final.count())):
            if self.v_box_final.itemAt(i).widget() is not None:
                self.v_box_final.itemAt(i).widget().setParent(None)

    def createDimensionLabels(self, idx):
        """Create the dimension labels for the selected index.

        :param idx: the selected index
        """
        font = QFont()
        font.setPointSize(9)

        self.label3D.insert(idx, QLabel())
        self.label4D.insert(idx, QLabel())
        self.label5D.insert(idx, QLabel())

        self.label3D[idx].setFont(font)
        self.label4D[idx].setFont(font)
        self.label5D[idx].setFont(font)

        self.label3D[idx].setText("3D: ")
        self.label4D[idx].setText("4D: ")
        self.label5D[idx].setText("5D: ")

    def createFieldValue(self):
        """Create a field where will be displayed the position of a cursor.

        :return: the corresponding field
        """
        fieldValue = QLineEdit()
        fieldValue.setEnabled(False)
        fieldValue.setFixedWidth(65)
        fieldValue.setAlignment(Qt.AlignCenter)
        fieldValue.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        font = QFont()
        font.setPointSize(9)
        fieldValue.setFont(font)
        return fieldValue

    def create_slider(self, maxm=0, minm=0, pos=0):
        """Generate an horizontal slider.

        :param maxm: slider's maximum
        :param minm: slider's minimum
        :param pos: slider's initial value
        :return: the slider object
        """
        slider = QSlider(Qt.Horizontal)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickInterval(1)
        slider.setMaximum(maxm)
        slider.setMinimum(minm)
        slider.setValue(pos)
        slider.setEnabled(False)
        return slider

    def displayPosValue(self, idx):
        """Display the position of each cursor for the selected index.

        :param idx: the selected index
        """
        self.txt_slider_3D[idx].setText(
            f"{self.slider_3D[idx].value() + 1} "
            f"/ {self.slider_3D[idx].maximum() + 1}"
        )
        self.txt_slider_4D[idx].setText(
            f"{self.slider_4D[idx].value() + 1} "
            f"/ {self.slider_4D[idx].maximum() + 1}"
        )
        self.txt_slider_5D[idx].setText(
            f"{self.slider_5D[idx].value() + 1} "
            f"/ {self.slider_5D[idx].maximum() + 1}"
        )

    def enableSliders(self, idx):
        """Enable all the horizontal slider.

        :param idx: the slider's index
        """
        self.slider_3D[idx].setEnabled(True)
        self.slider_4D[idx].setEnabled(True)
        self.slider_5D[idx].setEnabled(True)

    def image2DModifications(self, idx, im2D=None):
        """Apply modifications to display the image correctly.

        :param idx: the selected index
        :param im2D: image to modify
        """

        display_size = (128, 128)
        display_type = np.uint8  # this MUST be an integer data type
        display_pctl = 0.5  # percentile (0.5%) of values to clip at the
        # low and high end of intensities.
        display_max = np.iinfo(display_type).max
        display_min = np.iinfo(display_type).min

        im2d_provided = im2D is not None
        if not im2d_provided:
            im2D = self.im_2D[idx]

        # Resize image first, for three reasons:
        #  1 - it may slightly changes the intensity scale, so re-scaling
        #      should be done after this
        #  2 - rescaling before rotation is slightly faster, specially for
        #      large images (> display_size).
        #  3 - rescaling may alter the occurrence of nan or infinite values
        #      (e.g. an image may become all-nan), anti_aliasing keyword is
        #      defined in skimage since version 0.14.0

        if version.parse(sk.__version__) >= version.Version("0.14.0"):
            try:
                im2D = resize(
                    im2D, display_size, mode="constant", anti_aliasing=False
                )

            except ValueError:
                im2D = resize(
                    im2D.byteswap().newbyteorder(),
                    display_size,
                    mode="constant",
                    anti_aliasing=False,
                )
        else:
            try:
                im2D = resize(im2D, display_size, mode="constant")

            except ValueError:
                im2D = resize(
                    im2D.byteswap().newbyteorder(),
                    display_size,
                    mode="constant",
                )

        # Rescale image while handling Nans and infinite values
        im_mask = np.isfinite(im2D)
        if np.any(im_mask):  # if we have any finite value to work with
            # shift the lower percentile chosen to 0.0
            im2D -= np.percentile(im2D[im_mask], display_pctl)
            # determine max from upper percentile
            im_max = np.percentile(im2D[im_mask], 100.0 - display_pctl)
            if im_max > 0:  # avoid dividing by zero
                # re-scale to display range
                im2D *= (display_max - display_min) / im_max
            # shift lowest value to lower limit of display range
            im2D += display_min

        # clip all values to display range, remove infinite values
        np.clip(im2D, display_min, display_max, im2D)
        # convert to integer display data type. NaNs get converted to 0.
        im2D = im2D.astype(display_type)

        # Rotate. Copy array to avoid negative strides (Qt doesn't handle that)
        if self.config.isRadioView() is True:
            im2D = np.rot90(im2D.T, 2).copy()  # radiological

        else:
            im2D = np.rot90(im2D, 1).copy()  # neurological

        if im2d_provided:
            return im2D
        else:
            self.im_2D[idx] = im2D

    def image_to_pixmap(self, im, i):
        """Create a 2D pixmap from a N-D Nifti image.

        :param im: Nifti image
        :param i: index of the slide
        :return: the corresponding pixmap
        """

        # The image to display depends on the dimension of the image
        # In the 3D case, each slice is displayed
        if len(im.shape) == 3:
            # im_2D = im.get_fdata()[:, :, i].copy()
            im_2D = np.asarray(im.dataobj)[:, :, i].copy()

        # In the 4D case, each middle slice of the 3D dimension is displayed
        # for each time in the 4D dimension
        elif len(im.shape) == 4:
            # im_3D = im.get_fdata()[:, :, :, i].copy()
            im_3D = np.asarray(im.dataobj)[:, :, :, i].copy()
            middle_slice = int(im_3D.shape[2] / 2)
            im_2D = im_3D[:, :, middle_slice]

        # In the 5D case, each first time of the 4D dimension and
        # its middle slice of the 3D dimension is displayed
        elif len(im.shape) == 5:
            # im_4D = im.get_fdata()[:, :, :, :, i].copy()
            im_4D = np.asarray(im.dataobj)[:, :, :, :, i].copy()
            im_3D = im_4D[:, :, :, 1]
            middle_slice = int(im_3D.shape[2] / 2)
            im_2D = im_3D[:, :, middle_slice]

        else:
            im_2D = [0]

        # Making some pixel modification to display the image correctly
        im_2D = self.image2DModifications(0, im_2D)

        w, h = im_2D.shape

        im_Qt = QImage(im_2D.data, w, h, QImage.Format_Indexed8)
        pixm = QPixmap.fromImage(im_Qt)

        return pixm

    def indexImage(self, idx):
        """Update all slider values according to the size of the current image.

        :param idx: the selected index
        """

        # Getting the sliders value
        sl3D = self.slider_3D[idx].value()
        sl4D = self.slider_4D[idx].value()
        sl5D = self.slider_5D[idx].value()

        # Depending on the dimension, reading the image data and
        # changing the cursors maximum
        if len(self.img[idx].shape) == 3:
            self.im_2D.insert(
                idx, np.asarray(self.img[idx].dataobj)[:, :, sl3D].copy()
            )
            self.slider_3D[idx].setMaximum(self.img[idx].shape[2] - 1)
            self.slider_4D[idx].setMaximum(0)
            self.slider_5D[idx].setMaximum(0)

        if len(self.img[idx].shape) == 4:
            self.im_2D.insert(
                idx, np.asarray(self.img[idx].dataobj)[:, :, sl3D, sl4D].copy()
            )
            self.slider_3D[idx].setMaximum(self.img[idx].shape[2] - 1)
            self.slider_4D[idx].setMaximum(self.img[idx].shape[3] - 1)
            self.slider_5D[idx].setMaximum(0)

        if len(self.img[idx].shape) == 5:
            self.im_2D.insert(
                idx,
                np.asarray(self.img[idx].dataobj)[
                    :, :, sl3D, sl4D, sl5D
                ].copy(),
            )
            self.slider_3D[idx].setMaximum(self.img[idx].shape[2] - 1)
            self.slider_4D[idx].setMaximum(self.img[idx].shape[3] - 1)
            self.slider_5D[idx].setMaximum(self.img[idx].shape[4] - 1)

    def mem_release(self):
        """Reset all object lists to zero in order to preserve memory"""

        del self.im_2D[:]
        del self.slider_3D[:]
        del self.slider_4D[:]
        del self.slider_5D[:]
        del self.txt_slider_3D[:]
        del self.txt_slider_4D[:]
        del self.txt_slider_5D[:]
        del self.label3D[:]
        del self.label4D[:]
        del self.label5D[:]
        del self.imageLabel[:]
        del self.img[:]
        del self.label_description[:]

    def navigImage(self, idx):
        """Display the 2D image for the selected index.

        :param idx: the selected index
        """

        self.indexImage(idx)
        self.displayPosValue(idx)

        self.image2DModifications(idx)
        w, h = self.im_2D[idx].shape

        image = QImage(self.im_2D[idx].data, w, h, QImage.Format_Indexed8)
        pixm = QPixmap.fromImage(image)
        self.imageLabel[idx].setPixmap(pixm)

    def openTagsPopUp(self):
        """Open a pop-up to select the legend of the thumbnails."""

        self.popUp = PopUpSelectTag(self.project)
        self.popUp.setWindowTitle("Select the image viewer tag")
        if self.popUp.exec_():
            self.verify_slices(self.file_paths)

    def setThumbnail(self, file_path_base_name, idx):
        """Set the thumbnail tag value under the image frame.

        :param file_path_base_name: basename of the selected path
        :param idx: index of the image
        """

        with self.project.database.data() as database_data:

            # Looking for the tag value to display as a legend of the
            # thumbnail
            for scan in database_data.get_document_names(COLLECTION_CURRENT):
                if scan == file_path_base_name:
                    value = database_data.get_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan,
                        field=self.config.getThumbnailTag(),
                    )
                    if value is not None:
                        self.label_description[idx].setText(
                            str(value)[: self.nb_char_max]
                        )
                    else:
                        self.label_description[idx].setText(
                            NOT_DEFINED_VALUE[: self.nb_char_max]
                        )
                    self.label_description[idx].setToolTip(
                        os.path.basename(self.config.getThumbnailTag())
                    )

    def show_slices(self, file_paths):
        """Creates the thumbnails from the selected file paths.

        :param file_paths: the selected file paths
        """

        # If it's the first time that this function is called, the MiniViewer
        # has to be shown
        if self.first_time:
            self.setHidden(False)
            self.first_time = False

        # If the user has willingly hidden the MiniViewer, the Processes are
        # not made
        if self.isHidden():
            pass
        else:
            self.do_nothing = [False] * len(file_paths)

            self.file_paths = file_paths
            self.max_scans = self.config.get_max_thumbnails()
            self.setMinimumHeight(220)
            self.clear_layouts()
            self.frame = QFrame(self)
            self.frame_final = QFrame(self)

            # Limiting the legend of the thumbnails
            self.nb_char_max = 60

            font = QFont()
            font.setPointSize(9)

            # Reading the images from the file paths
            for idx, file_path in enumerate(self.file_paths.copy()):
                try:
                    chk = nib.as_closest_canonical(
                        nib.load(file_path, mmap=False)
                    )
                    # chk = nib.as_closest_canonical(nib.load(file_path))
                    # chk = nib.load(file_path)

                except nib.filebasedimages.ImageFileError:
                    logger.warning(
                        f"Error while trying to display "
                        f"the {os.path.abspath(file_path)} image ...!",
                        exc_info=True,
                    )
                    self.file_paths.remove(file_path)
                    chk = False

                except FileNotFoundError:
                    logger.warning(
                        f"File {os.path.abspath(file_path)} is "
                        f"not existing..."
                    )
                    self.file_paths.remove(file_path)
                    chk = False

                if chk is not False:
                    try:
                        np.asarray(chk.dataobj)

                    except Exception:
                        logger.warning(
                            f"Error while trying to display "
                            f"the {os.path.abspath(file_path)} image ...!\n",
                            exc_info=True,
                        )
                        self.file_paths.remove(file_path)

                    else:
                        self.img.insert(idx, chk)

            # If we are in the "cursors" display mode
            if self.check_box_slices.checkState() == Qt.Unchecked:
                # Layout to align each thumbnail (image + cursors)
                self.h_box_thumb = QHBoxLayout()

                # idx represents the index of the selected image
                for idx in range(min(self.max_scans, len(self.file_paths))):
                    if not self.do_nothing[idx]:
                        # Creating sliders and labels
                        self.boxSlider(idx)
                        self.enableSliders(idx)
                        self.createDimensionLabels(idx)

                        # Getting the sliders value and reading the image data
                        self.indexImage(idx)

                        # Making some pixel modification to display the image
                        # correctly
                        self.image2DModifications(idx)

                    self.displayPosValue(idx)

                    w, h = self.im_2D[idx].shape

                    im_Qt = QImage(
                        self.im_2D[idx].data, w, h, QImage.Format_Indexed8
                    )
                    pixm = QPixmap.fromImage(im_Qt)

                    file_path_base_name = os.path.basename(
                        self.file_paths[idx]
                    )

                    # imageLabel is the label where the image is displayed
                    # (as a pixmap)
                    self.imageLabel.insert(idx, QLabel(self))
                    self.imageLabel[idx].setPixmap(pixm)
                    self.imageLabel[idx].setToolTip(file_path_base_name)

                    self.label_description.insert(idx, ClickableLabel())
                    self.label_description[idx].setFont(font)
                    self.label_description[idx].clicked.connect(
                        self.openTagsPopUp
                    )

                    # Looking for the tag value to display as a
                    # legend of the thumbnail
                    file_path_base_name = os.path.relpath(
                        self.file_paths[idx], self.project.folder
                    )
                    self.setThumbnail(file_path_base_name, idx)

                    # Layout that corresponds to the 3D dimension
                    self.h_box_slider_3D = QHBoxLayout()
                    self.h_box_slider_3D.addWidget(self.label3D[idx])
                    self.h_box_slider_3D.addWidget(self.txt_slider_3D[idx])
                    self.h_box_slider_3D.addWidget(self.slider_3D[idx])

                    # Layout that corresponds to the 4D dimension
                    self.h_box_slider_4D = QHBoxLayout()
                    self.h_box_slider_4D.addWidget(self.label4D[idx])
                    self.h_box_slider_4D.addWidget(self.txt_slider_4D[idx])
                    self.h_box_slider_4D.addWidget(self.slider_4D[idx])

                    # Layout that corresponds to the 5D dimension
                    self.h_box_slider_5D = QHBoxLayout()
                    self.h_box_slider_5D.addWidget(self.label5D[idx])
                    self.h_box_slider_5D.addWidget(self.txt_slider_5D[idx])
                    self.h_box_slider_5D.addWidget(self.slider_5D[idx])

                    # Layout for the three sliders
                    self.v_box_sliders = QVBoxLayout()
                    self.v_box_sliders.addLayout(self.h_box_slider_3D)
                    self.v_box_sliders.addLayout(self.h_box_slider_4D)
                    self.v_box_sliders.addLayout(self.h_box_slider_5D)

                    # Layout that corresponds to the image + the sliders
                    self.h_box = QHBoxLayout()
                    self.h_box.addWidget(self.imageLabel[idx])
                    self.h_box.addLayout(self.v_box_sliders)

                    # Layout that corresponds to the image and sliders +
                    # the description
                    self.v_box_thumb = QVBoxLayout()
                    self.v_box_thumb.addLayout(self.h_box)
                    self.v_box_thumb.addWidget(self.label_description[idx])

                    # Layout that will contain all the thumbnails
                    self.h_box_thumb.addLayout(self.v_box_thumb)

                self.frame.setLayout(self.h_box_thumb)

            # If we are in the "all slices" display mode
            else:
                self.h_box_images = QHBoxLayout()
                self.h_box_images.setSpacing(10)
                self.v_box_scans = QVBoxLayout()

                # idx represents the index of the selected image
                for idx in range(len(self.file_paths)):
                    file_path_base_name = os.path.relpath(
                        self.file_paths[idx], self.project.folder
                    )

                    self.label_description.insert(idx, ClickableLabel())
                    self.label_description[idx].setFont(font)
                    self.label_description[idx].clicked.connect(
                        self.openTagsPopUp
                    )

                    # Looking for the tag value to display as a legend
                    # of the thumbnail
                    self.setThumbnail(file_path_base_name, idx)

                    # Depending of the dimension of the image,
                    # the legend of each image and the number of images to
                    # display will change
                    if not self.do_nothing[idx]:
                        if len(self.img[idx].shape) == 3:
                            nb_slices = self.img[idx].shape[2]
                            txt = "Slice n°"
                        elif len(self.img[idx].shape) == 4:
                            nb_slices = self.img[idx].shape[3]
                            txt = "Time n°"
                        elif len(self.img[idx].shape) == 5:
                            nb_slices = self.img[idx].shape[4]
                            txt = "Study n°"
                        else:
                            nb_slices = 0

                        # Limiting the number of images to the number
                        # chosen by the user
                        for i in range(
                            min(
                                nb_slices, int(self.line_edit_nb_slices.text())
                            )
                        ):
                            pixm = self.image_to_pixmap(self.img[idx], i)

                            self.v_box = QVBoxLayout()

                            # label corresponds to the label where one image
                            # is displayed
                            label = QLabel(self)
                            label.setPixmap(pixm)
                            label.setToolTip(
                                os.path.basename(self.file_paths[idx])
                            )

                            # Legend of the image (depends on the number
                            # of dimensions)
                            label_info = QLabel()
                            label_info.setFont(font)
                            label_info.setText(f"{txt}{i + 1}")
                            label_info.setAlignment(QtCore.Qt.AlignCenter)

                            self.v_box.addWidget(label)
                            self.v_box.addWidget(label_info)

                            # This layout allows to chain each image
                            self.h_box_images.addLayout(self.v_box)
                        self.v_box_scans.addLayout(self.h_box_images)
                        self.v_box_scans.addWidget(self.label_description[idx])
                self.frame.setLayout(self.v_box_scans)

            # Adding a scroll area if the thumbnails are too large
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidget(self.frame)

            self.h_box_check_box = QHBoxLayout()

            if self.check_box_slices.isChecked():
                self.h_box_check_box.addStretch(1)
                self.h_box_check_box.addWidget(self.label_orientation)
                self.h_box_check_box.addStretch(1)
                self.label_nb_slices.setHidden(False)
                self.line_edit_nb_slices.setHidden(False)
                self.h_box_check_box.addWidget(self.label_nb_slices)
                self.h_box_check_box.addWidget(self.line_edit_nb_slices)
                self.check_box_cursors.setHidden(True)
            else:
                self.check_box_cursors.setHidden(False)
                self.h_box_check_box.addWidget(self.check_box_cursors)
                self.h_box_check_box.addStretch(1)
                self.h_box_check_box.addWidget(self.label_orientation)
                self.h_box_check_box.addStretch(1)
                self.label_nb_slices.setHidden(True)
                self.line_edit_nb_slices.setHidden(True)

            self.h_box_check_box.addWidget(self.check_box_slices)

            self.v_box_final.addLayout(self.h_box_check_box)
            self.v_box_final.addWidget(self.scroll_area)

    def update_nb_slices(self):
        """Update the config file and the thumbnails.

        Called when the number of slices to visualize changes.
        """
        nb_slices = self.line_edit_nb_slices.text()
        self.config.setNbAllSlicesMax(nb_slices)
        self.verify_slices(self.file_paths)

    def update_visualization_method(self):
        """Update the config file and the thumbnails.

        Called when the state of the checkbox to show all slices changes.
        """
        if self.check_box_slices.checkState() == Qt.Checked:
            self.config.setShowAllSlices(True)
        elif self.check_box_slices.checkState() == Qt.Unchecked:
            self.config.setShowAllSlices(False)
        self.verify_slices(self.file_paths)

    def verify_slices(self, file_paths):
        """Make 'Show all slices' checkbox unclickable if len(file_paths) > 1.

        :param file_paths: the selected documents
        """
        # Updating the config
        self.config = Config()
        self.mem_release()

        if len(file_paths) > 1:
            self.config.setShowAllSlices(False)
            self.check_box_slices.setCheckState(Qt.Unchecked)
            self.check_box_slices.setCheckable(False)

        else:
            self.check_box_slices.setCheckable(True)

        self.show_slices(file_paths)

        if self.config.isRadioView() is True:
            self.label_orientation.setText("Radiological orientation")

        else:
            self.label_orientation.setText("Neurological orientation")
