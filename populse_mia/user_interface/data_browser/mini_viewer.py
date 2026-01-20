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
        - update_visualization: update the config file and the thumbnails
        - verify_slices: verify the number of selected documents

    """

    def __init__(self, project):
        """
        Initialize the MiniViewer with project configuration.

        The MiniViewer provides a thumbnail preview interface for scans,
        initially hidden to maximize space for the data browser.

        :param project: The current project instance containing scan data and
                        project-specific configuration.
        """
        super().__init__()
        self.project = project
        # first_time (bool) is a flag tracking whether this is the first
        # display
        self.first_time = True
        # file_paths (str) is the currently selected file path(s)
        self.file_paths = ""
        # config that allows to read the software preferences
        self.config = Config()
        # max_scans (int) is the maximum number of thumbnails to display for
        # multiple selections
        self.max_scans = self.config.get_max_thumbnails()
        # start hidden to maximize data browser space
        self.setHidden(True)
        # Setup UI components
        self._initialize_components()
        self._create_layouts()
        self._initialize_checkboxes()

    def _create_layouts(self):
        """
        Initialize and configure all layout managers for the MiniViewer widget.

        Creates a hierarchical layout structure with:
            - Horizontal layouts for images, sliders (3D/4D/5D), checkboxes,
              and thumbnails
            - Vertical layouts for main content organization and slider
              grouping
            - Sets the final vertical layout as the widget's root layout

        All layouts are stored as instance attributes for later population
        with widgets.
        """
        # Image display layouts
        self.h_box_images = QHBoxLayout()
        self.h_box_images.setSpacing(10)
        # Main vertical layouts
        self.v_box = QVBoxLayout()
        self.v_box_final = QVBoxLayout()
        # Slider layouts for different dimensions
        self.h_box_slider_3D = QHBoxLayout()
        self.h_box_slider_4D = QHBoxLayout()
        self.h_box_slider_5D = QHBoxLayout()
        self.v_box_sliders = QVBoxLayout()
        # Control layouts
        self.h_box = QHBoxLayout()
        self.h_box_check_box = QHBoxLayout()
        # Thumbnail layouts
        self.v_box_thumb = QVBoxLayout()
        self.h_box_thumb = QHBoxLayout()
        # Set root layout
        self.setLayout(self.v_box_final)

    def _initialize_checkboxes(self):
        """
        Initialize checkboxes for controlling visualization behavior.

        Creates two checkboxes:
            - 'Show all slices': Toggles between displaying all slices or
                                 using cursors
            - 'Chain cursors': Links cursors across multiple selected documents

        Both checkboxes are initialized with their states from the current
        config and connected to their respective event handlers.
        """

        def _create_checkbox(text, checked, callback, tooltip=None):
            """
            Create a configured checkbox with consistent styling.

            :param text: Label text for the checkbox.
            :param checked: Initial checked state.
            :param callback: Function to call when state changes.
            :param tooltip: Optional tooltip text.

            :return: Configured QCheckBox instance.
            """
            checkbox = QCheckBox(text)
            checkbox.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            checkbox.stateChanged.connect(callback)

            if tooltip:
                checkbox.setToolTip(tooltip)

            return checkbox

        # Show all slices checkbox
        self.check_box_slices = _create_checkbox(
            text="Show all slices (no cursors)",
            checked=self.config.getShowAllSlices(),
            callback=self.update_visualization,
        )
        # Chain cursors checkbox
        self.check_box_cursors = _create_checkbox(
            text="Chain cursors",
            checked=self.config.getChainCursors(),
            callback=self.check_box_cursors_state_changed,
            tooltip=(
                "Allows to connect all cursors when selecting "
                "multiple documents"
            ),
        )

    def _initialize_components(self):
        """
        Initialize UI components for the MiniViewer.

        Creates and configures the main UI elements including:
            - Frame containers and scroll area for layout management
            - Slice count control with label and editable line input
            - Orientation label (radiological vs neurological view)
            - Empty collections for dynamic image display elements (sliders,
              labels, images)

        Note: Image-related collections are initialized as empty lists and
              populated dynamically based on the loaded data dimensions.
        """
        # Main container widgets
        self.labels = QWidget()
        self.frame = QFrame()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.frame)
        self.frame_final = QFrame()
        # Slice count controls
        max_slices = self.config.getNbAllSlicesMax()
        self.label_nb_slices = QLabel("Maximum number of slices: ")
        self.line_edit_nb_slices = QLineEdit(str(max_slices))
        self.line_edit_nb_slices.returnPressed.connect(self.update_nb_slices)
        # Orientation label
        orientation = (
            "Radiological" if self.config.isRadioView() else "Neurological"
        )
        self.label_orientation = QLabel(f"{orientation} orientation")
        # Dynamic image display components (populated on data load)
        self.im_2D = []
        self.img = []
        self.imageLabel = []
        self.label_description = []
        # 3D/4D/5D navigation components
        self.slider_3D = []
        self.slider_4D = []
        self.slider_5D = []
        self.txt_slider_3D = []
        self.txt_slider_4D = []
        self.txt_slider_5D = []
        self.label3D = []
        self.label4D = []
        self.label5D = []

    def boxSlider(self, idx):
        """
        Initialize dimensional sliders and value fields for a given index.

        Creates three sliders (3D, 4D, 5D) with their corresponding text
        fields and connects each slider's valueChanged signal to the
        appropriate position update handler.

        :param idx (int): The index position where sliders should be inserted.

        Note: Each slider is connected to changePosValue with dimension
              offsets:
                - 3D slider: dimension 1
                - 4D slider: dimension 2
                - 5D slider: dimension 3
        """
        # Define slider configurations: (slider_list, dimension_offset)
        slider_configs = [
            (self.slider_3D, 1),
            (self.slider_4D, 2),
            (self.slider_5D, 3),
        ]
        # Create and configure sliders
        for slider_list, dimension in slider_configs:
            slider = self.create_slider(0, 0, 0)
            slider.valueChanged.connect(
                partial(self.changePosValue, idx, dimension)
            )
            slider_list.insert(idx, slider)

        # Create corresponding text fields
        for text_field_list in (
            self.txt_slider_3D,
            self.txt_slider_4D,
            self.txt_slider_5D,
        ):
            text_field_list.insert(idx, self.createFieldValue())

    def changePosValue(self, idx, cursor_to_change):
        """
        Synchronize cursor positions across multiple image viewers when chain
        mode is enabled.

        When the "Chain cursors" checkbox is checked, this method propagates
        the cursor value from the modified viewer to all other viewers,
        scaling the value proportionally to account for different cursor
        ranges.

        :param idx (int): Index of the viewer whose cursor was changed.
        :param cursor_to_change (int): Cursor identifier (1=3D, 2=4D, 3=5D).

        Notes:
            - If chain mode is disabled, only updates the image for the given
              index.
            - Boundary values (min/max) are preserved exactly.
            - Intermediate values are scaled linearly to maintain relative
              position.
        """

        # Early return if chain mode is disabled
        if not self.check_box_cursors.isChecked():
            self.navigImage(idx)
            return

        # Map cursor identifier to the appropriate slider array
        cursor_map = {
            1: self.slider_3D,
            2: self.slider_4D,
            3: self.slider_5D,
        }
        cursors = cursor_map[cursor_to_change]
        source_cursor = cursors[idx]
        source_value = source_cursor.value()
        source_min = source_cursor.minimum()
        source_max = source_cursor.maximum()
        num_viewers = min(self.max_scans, len(self.file_paths))

        for idx_loop in range(num_viewers):
            target_cursor = cursors[idx_loop]
            # Temporarily disconnect to prevent recursive updates
            target_cursor.valueChanged.disconnect()

            if idx_loop != idx:
                target_min = target_cursor.minimum()
                target_max = target_cursor.maximum()

                # Explicit boundary handling
                if source_value == source_min:
                    value = target_min

                elif source_value == source_max:
                    value = target_max

                else:
                    # Linear scaling for intermediate values
                    delta_source = source_value - source_min
                    range_source = source_max - source_min
                    range_target = target_max - target_min
                    proportion = delta_source / range_source
                    value = round(proportion * range_target + target_min)

                target_cursor.setValue(value)

            # Update the displayed image
            self.navigImage(idx_loop)
            # Restore the signal connection
            target_cursor.valueChanged.connect(
                partial(self.changePosValue, idx_loop, cursor_to_change)
            )

    def check_box_cursors_state_changed(self):
        """
        Update cursor chaining configuration based on checkbox state.

        Synchronizes the cursor chaining setting in the configuration with the
        current state of the checkbox. When enabled, cursors will be chained
        together across views.
        """
        self.config.setChainCursors(self.check_box_cursors.isChecked())

    def clear(self):
        """
        Clear cached Nibabel image to free memory.

        Removes the internal image reference if it exists, allowing the image
        object to be garbage collected.
        """

        try:
            del self.img

        except AttributeError:
            pass

    def clear_layouts(self):
        """
        Remove all widgets from the final layout.

        This prepares the layout for new content by detaching and deleting
        all existing widgets.
        """

        while self.v_box_final.count():
            item = self.v_box_final.takeAt(0)

            if widget := item.widget():
                widget.deleteLater()

    def createDimensionLabels(self, idx):
        """
        Create and configure dimension labels for the specified index.

        Creates three QLabel widgets (3D, 4D, and 5D) at the given index
        position, configures them with a 9-point font, and sets their text
        labels.

        :param idx: The index position where the labels should be inserted.
        """
        font = QFont()
        font.setPointSize(9)
        # Configuration for each dimension label
        label_configs = [
            (self.label3D, "3D: "),
            (self.label4D, "4D: "),
            (self.label5D, "5D: "),
        ]

        # Create and configure all labels
        for label_list, text in label_configs:
            label = QLabel()
            label.setFont(font)
            label.setText(text)
            label_list.insert(idx, label)

    def createFieldValue(self):
        """
        Create a read-only field for displaying cursor position.

        :return (QLineEdit): A disabled, center-aligned text field with fixed
                             width (65px) and font size (9pt) for displaying
                             coordinate values.
        """
        field_value = QLineEdit()
        field_value.setEnabled(False)
        field_value.setFixedWidth(65)
        field_value.setAlignment(Qt.AlignCenter)
        field_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        font = field_value.font()
        font.setPointSize(9)
        field_value.setFont(font)
        return field_value

    def create_slider(self, minimum=0, maximum=0, position=0):
        """
        Create a horizontal slider widget.

        :param minimum: The minimum value of the slider. Defaults to 0.
        :param maximum: The maximum value of the slider. Defaults to 0.
        :param position: The initial position/value of the slider.
                         Defaults to 0.

        :return QSlider: A configured horizontal slider widget, initially
                         disabled.

        Note:
        The slider is created with strong focus policy and a tick interval of
        1. It starts in a disabled state. With default parameters (min=0,
        max=0), the slider has no range and should be configured before
        enabling.
        """
        slider = QSlider(Qt.Horizontal)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickInterval(1)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(position)
        slider.setEnabled(False)
        return slider

    def displayPosValue(self, idx):
        """
        Update position display for all dimensional sliders at the given index.

        Updates the text labels for 3D, 4D, and 5D sliders to show the current
        position (1-indexed) and maximum value in the format "current / max".

        :param idx: Index of the slider group to update (0-based).
        """

        for slider, text_widget in [
            (self.slider_3D[idx], self.txt_slider_3D[idx]),
            (self.slider_4D[idx], self.txt_slider_4D[idx]),
            (self.slider_5D[idx], self.txt_slider_5D[idx]),
        ]:
            current = slider.value() + 1
            maximum = slider.maximum() + 1
            text_widget.setText(f"{current} / {maximum}")

    def enableSliders(self, idx):
        """
        Enable sliders at the specified index across all dimensions.

        :param idx: Index of the sliders to enable across 3D, 4D, and 5D
                    slider collections.
        """

        for slider_collection in (
            self.slider_3D,
            self.slider_4D,
            self.slider_5D,
        ):
            slider_collection[idx].setEnabled(True)

    def image2DModifications(self, idx, im2D=None):
        """
        Apply display modifications to a 2D image slice.

        Processes an image for optimal display by:
        1. Resizing to standard display dimensions
        2. Rescaling intensities with percentile-based clipping
        3. Converting to appropriate display data type
        4. Applying orientation rotation (radiological/neurological)

        :param idx: Index of the image slice in the internal array
        :param im2D: Optional 2D numpy array to modify. If None, uses
                     self.im_2D[idx]

        Note: When im2D is not provided, the modified image is stored in
              self.im_2D[idx]
        """

        def _resize_image(image, target_size):
            """Resize image with version-aware anti-aliasing handling.

            :param image: 2D numpy array to resize
            :param target_size: Tuple of (height, width) for output dimensions

            :return (numpy.ndarray): Resized image
            """
            resize_kwargs = {"output_shape": target_size, "mode": "constant"}

            # Add anti_aliasing for newer skimage versions
            if version.parse(sk.__version__) >= version.Version("0.14.0"):
                resize_kwargs["anti_aliasing"] = False

            try:
                return resize(image, **resize_kwargs)

            except ValueError:

                # Handle byte order issues
                return resize(image.byteswap().newbyteorder(), **resize_kwargs)

        def _rescale_intensities(image, min_val, max_val, pctl):
            """Rescale image intensities using percentile-based normalization.

            Handles NaN and infinite values gracefully by masking them out
            during percentile calculations.

            :param image: 2D numpy array to rescale (modified in-place)
            :param min_val: Minimum value for output range
            :param max_val: Maximum value for output range
            :param pctl: Percentile for clipping at both ends

            :returns (numpy.ndarray): Rescaled image with values in [min_val,
                                      max_val]
            """
            finite_mask = np.isfinite(image)

            if np.any(finite_mask):  # Only rescale if we have finite values
                # Shift the lower percentile to 0.0
                lower_bound = np.percentile(image[finite_mask], pctl)
                image -= lower_bound
                # Calculate upper percentile after shifting
                im_max = np.percentile(image[finite_mask], 100.0 - pctl)

                if im_max > 0:  # Avoid division by zero
                    # Re-scale to display range
                    image *= (max_val - min_val) / im_max

                # Shift to lower limit of display range
                image += min_val

            # Always clip, regardless of whether rescaling occurred
            # This removes infinite values and enforces display range
            np.clip(image, min_val, max_val, out=image)

            return image

        def _apply_rotation(image):
            """Apply orientation-specific rotation to image.

            :param image: 2D numpy array to rotate

            :return (numpy.ndarray): Rotated image with contiguous memory
                                     layout

            Note:
                Copy is made to ensure contiguous memory (Qt compatibility)
            """

            if self.config.isRadioView():
                # Radiological view
                return np.rot90(image.T, 2).copy()

            else:
                # Neurological view
                return np.rot90(image, 1).copy()

        # Display configuration constants
        DISPLAY_SIZE = (128, 128)
        DISPLAY_TYPE = np.uint8  # Must be an integer data type
        DISPLAY_PCTL = 0.5  # Percentile for intensity clipping
        DISPLAY_MAX = np.iinfo(DISPLAY_TYPE).max
        DISPLAY_MIN = np.iinfo(DISPLAY_TYPE).min
        im2d_provided = im2D is not None

        if im2D is None:
            im2D = self.im_2D[idx]

        # Resize image (before rescaling for performance and accuracy)
        # - it may slightly changes the intensity scale, so re-scaling
        #      should be done after this
        # - rescaling before rotation is slightly faster, specially for
        #      large images (> display_size).
        # - rescaling may alter the occurrence of nan or infinite values
        #      (e.g. an image may become all-nan), anti_aliasing keyword is
        #      defined in skimage since version 0.14.0
        im2D = _resize_image(im2D, DISPLAY_SIZE)
        # Rescale intensities while handling NaN and infinite values
        im2D = _rescale_intensities(
            im2D, DISPLAY_MIN, DISPLAY_MAX, DISPLAY_PCTL
        )
        # Convert to display data type (NaNs become 0)
        im2D = im2D.astype(DISPLAY_TYPE)
        # Apply orientation rotation and ensure contiguous memory layout
        im2D = _apply_rotation(im2D)

        # Return or store the result
        if im2d_provided:
            return im2D

        else:
            self.im_2D[idx] = im2D
            return None

    def image_to_pixmap(self, im, i):
        """
        Convert an N-dimensional NIfTI image to a 2D Qt pixmap.

        Extracts a 2D slice from multi-dimensional medical imaging data and
        converts it to a Qt pixmap for display. The extraction strategy
        depends on dimensionality:

        - 3D images: Extract slice at index i along the z-axis
        - 4D images: Extract middle z-slice from the 3D volume at time index i
        - 5D images: Extract middle z-slice from the 3D volume at time index 1
                     of the 4D volume at the 5th dimension index i

        :param im: NIfTI image object with a dataobj attribute
        :param i: Index for slice/volume selection along the outermost
                  variable dimension

        :return (QPixmap): Qt pixmap ready for display, or pixmap from empty
                           array if dimensionality is unsupported
        """
        ndim = len(im.shape)

        # Dispatch to appropriate extraction method based on dimensionality
        if ndim == 3:
            # 3D case, each slice is displayed
            im_2D = np.asarray(im.dataobj)[:, :, i].copy()

        elif ndim == 4:
            # 4D case, each middle slice of the 3D dimension is displayed
            # for each time in the 4D dimension
            im_3D = np.asarray(im.dataobj)[:, :, :, i].copy()
            im_2D = im_3D[:, :, im_3D.shape[2] // 2]

        elif ndim == 5:
            # 5D case, each first time of the 4D dimension and its middle
            # slice of the 3D dimension is displayed
            im_4D = np.asarray(im.dataobj)[:, :, :, :, i].copy()
            im_3D = im_4D[:, :, :, 1]
            im_2D = im_3D[:, :, im_3D.shape[2] // 2]

        else:
            im_2D = np.array([0])

        # Apply display-specific transformations
        im_2D = self.image2DModifications(0, im_2D)
        # Convert to Qt pixmap
        h, w = im_2D.shape
        im_Qt = QImage(im_2D.data, w, h, QImage.Format_Indexed8)

        return QPixmap.fromImage(im_Qt)

    def indexImage(self, idx):
        """
        Update the displayed 2D image slice and adjust slider ranges according
        to the dimensionality of the selected image.

        The current values of the 3D, 4D, and 5D sliders are used to extract
        the corresponding slice from the image data. Sliders that exceed the
        image dimensionality are reset to a maximum value of 0.

        :param idx: Index of the selected image
        """
        # Reading the image data
        img = self.img[idx]
        data = np.asarray(img.dataobj)
        shape = img.shape
        ndim = img.ndim

        # Getting the sliders value
        sl3D = self.slider_3D[idx].value()
        sl4D = self.slider_4D[idx].value()
        sl5D = self.slider_5D[idx].value()

        # Depending on the dimension, define the displayed 2D slice and
        # modify the maximum value of the cursors.
        if ndim == 3:
            self.im_2D.insert(idx, data[:, :, sl3D].copy())
            self.slider_3D[idx].setMaximum(shape[2] - 1)
            self.slider_4D[idx].setMaximum(0)
            self.slider_5D[idx].setMaximum(0)

        elif ndim == 4:
            self.im_2D.insert(idx, data[:, :, sl3D, sl4D].copy())
            self.slider_3D[idx].setMaximum(shape[2] - 1)
            self.slider_4D[idx].setMaximum(shape[3] - 1)
            self.slider_5D[idx].setMaximum(0)

        elif ndim == 5:
            self.im_2D.insert(idx, data[:, :, sl3D, sl4D, sl5D].copy())
            self.slider_3D[idx].setMaximum(shape[2] - 1)
            self.slider_4D[idx].setMaximum(shape[3] - 1)
            self.slider_5D[idx].setMaximum(shape[4] - 1)

    def mem_release(self):
        """
        Release memory by clearing all internal lists holding images, sliders,
        labels, and related UI elements.

        This method empties the existing lists in place (without
        reassigning them) to ensure that all references are removed
        and memory can be reclaimed.
        """

        for attr in (
            "im_2D",
            "slider_3D",
            "slider_4D",
            "slider_5D",
            "txt_slider_3D",
            "txt_slider_4D",
            "txt_slider_5D",
            "label3D",
            "label4D",
            "label5D",
            "imageLabel",
            "img",
            "label_description",
        ):
            getattr(self, attr).clear()

    def navigImage(self, idx):
        """
        Display the 2D image corresponding to the given index.

        This method updates the navigation state, applies image-specific
        modifications, converts the image to a Qt pixmap, and displays it in
        the associated label.

        :param idx (int): Index of the image to display
        """
        # Update navigation and position
        self.indexImage(idx)
        self.displayPosValue(idx)
        # Apply image-specific modifications
        self.image2DModifications(idx)
        # Convert the NumPy array to a QPixmap and display it
        height, width = self.im_2D[idx].shape
        qimage = QImage(
            self.im_2D[idx].data,
            width,
            height,
            QImage.Format_Indexed8,
        )
        self.imageLabel[idx].setPixmap(QPixmap.fromImage(qimage))

    def openTagsPopUp(self):
        """
        Open a modal dialog allowing the user to select the tag used as the
        thumbnail legend.

        If the dialog is accepted, slice verification is triggered for the
        current file paths.

        Notes:
        The dialog instance is stored on ``self.popUp`` to allow access from
        unit tests.
        """
        self.popUp = PopUpSelectTag(self.project)
        self.popUp.setWindowTitle("Select the image viewer tag")

        if self.popUp.exec_():
            self.verify_slices(self.file_paths)

    def setThumbnail(self, file_path_db, idx):
        """
        Set the thumbnail description label for a given image index.

        Retrieves the value of the configured thumbnail tag from the database
        and displays it under the image frame. If the value is not defined,
        a default placeholder is used. The tooltip shows the tag name.

        :param file_path_db (str): Path of selected image in database
                                   format (ex. data/raw_data/mymri.nii')
        :param idx (int): Index of the image in the UI.
        """

        with self.project.database.data() as database_data:

            # Looking for the tag value to display as a legend of the
            # thumbnail
            if file_path_db in database_data.get_document_names(
                COLLECTION_CURRENT
            ):
                value = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=file_path_db,
                    field=self.config.getThumbnailTag(),
                )
                # fmt: off
                display_text = (
                    str(value)[:self.nb_char_max]
                    if value is not None
                    else NOT_DEFINED_VALUE[:self.nb_char_max]
                )
                # fmt: on
                self.label_description[idx].setText(display_text)
                self.label_description[idx].setToolTip(
                    self.config.getThumbnailTag()
                )

    def show_slices(self, file_paths):
        """
        Display thumbnail previews of neuroimaging files with interactive
        controls.

        Creates a thumbnail viewer showing either cursor-controlled slices or
        multiple slices from the selected neuroimaging files. On first call,
        makes the MiniViewer visible. Does nothing if the viewer is hidden by
        the user.

        The viewer supports two display modes:
        - Cursor mode (default): Shows one slice per image with interactive
          3D/4D/5D sliders
        - All slices mode: Displays multiple consecutive slices from each image

        :param file_paths: List of paths to neuroimaging files (NIfTI format)
                           to display. Invalid or non-existent files are
                           automatically filtered out with warnings.

        Side effects:
            - Modifies self.file_paths by removing invalid entries
            - Updates self.img list with loaded image objects
            - Creates and configures numerous Qt widgets for the thumbnail
              display
            - Logs warnings for files that cannot be loaded or displayed

        Note:
            Maximum thumbnails displayed is controlled by
            self.config.get_max_thumbnails() in cursor mode, and by
            self.line_edit_nb_slices.text() in all slices mode.
        """

        # Show viewer on first call
        if self.first_time:
            self.setHidden(False)
            self.first_time = False

        # Skip processing if viewer is hidden
        if self.isHidden():
            return

        # Initialize state
        self.file_paths = file_paths
        self.do_nothing = [False] * len(file_paths)
        self.max_scans = self.config.get_max_thumbnails()
        self.nb_char_max = 60  # Limiting the legend of the thumbnails
        self.setMinimumHeight(220)
        self.clear_layouts()
        self.frame = QFrame(self)
        self.frame_final = QFrame(self)
        font = QFont()
        font.setPointSize(9)

        # Load neuroimaging files and populate self.img list, filtering
        # invalid files
        for idx, file_path in enumerate(self.file_paths.copy()):
            chk = False

            try:
                chk = nib.as_closest_canonical(nib.load(file_path, mmap=False))

            except nib.filebasedimages.ImageFileError:
                logger.warning(
                    f"MiniViewer: Error while trying to display "
                    f"{os.path.abspath(file_path)} image",
                    exc_info=True,
                )
                self.file_paths.remove(file_path)

            except FileNotFoundError:
                logger.warning(
                    f"MiniViewer: File "
                    f"{os.path.abspath(file_path)} does not exist"
                )
                self.file_paths.remove(file_path)

            # Only validate data if image loaded successfully
            if chk is not False:

                try:
                    np.asarray(chk.dataobj)

                except Exception:
                    logger.warning(
                        f"MiniViewer: Error while trying to display "
                        f"{os.path.abspath(file_path)} image",
                        exc_info=True,
                    )
                    self.file_paths.remove(file_path)

                else:
                    self.img.insert(idx, chk)

        # Render appropriate display mode
        if self.check_box_slices.checkState() == Qt.Unchecked:
            # Render thumbnails in cursor mode with interactive sliders.
            self.h_box_thumb = QHBoxLayout()

            # idx represents the index of the selected image
            for idx in range(min(self.max_scans, len(self.file_paths))):

                if not self.do_nothing[idx]:
                    # Setup sliders and controls
                    self.boxSlider(idx)
                    self.enableSliders(idx)
                    self.createDimensionLabels(idx)
                    # Getting the sliders value and reading the image data
                    self.indexImage(idx)
                    # Modifying pixels to display the image correctly
                    self.image2DModifications(idx)

                self.displayPosValue(idx)
                # Create thumbnail image
                w, h = self.im_2D[idx].shape
                im_Qt = QImage(
                    self.im_2D[idx].data, w, h, QImage.Format_Indexed8
                )
                pixm = QPixmap.fromImage(im_Qt)
                # Setup image label
                file_path_base_name = os.path.basename(self.file_paths[idx])
                # imageLabel is the label where the image is displayed
                # (as a pixmap)
                self.imageLabel.insert(idx, QLabel(self))
                self.imageLabel[idx].setPixmap(pixm)
                self.imageLabel[idx].setToolTip(file_path_base_name)
                # Setup description label
                self.label_description.insert(idx, ClickableLabel())
                self.label_description[idx].setFont(font)
                self.label_description[idx].clicked.connect(self.openTagsPopUp)
                # Looking for the tag value to display as a legend of the
                # thumbnail
                file_path_rel = os.path.relpath(
                    self.file_paths[idx], self.project.folder
                )
                self.setThumbnail(file_path_rel, idx)
                # Build slider layouts
                slider_layouts = [
                    (
                        self.label3D[idx],
                        self.txt_slider_3D[idx],
                        self.slider_3D[idx],
                    ),
                    (
                        self.label4D[idx],
                        self.txt_slider_4D[idx],
                        self.slider_4D[idx],
                    ),
                    (
                        self.label5D[idx],
                        self.txt_slider_5D[idx],
                        self.slider_5D[idx],
                    ),
                ]
                v_box_sliders = QVBoxLayout()

                for label, txt, slider in slider_layouts:
                    h_box = QHBoxLayout()
                    h_box.addWidget(label)
                    h_box.addWidget(txt)
                    h_box.addWidget(slider)
                    v_box_sliders.addLayout(h_box)

                # Combine image and sliders
                h_box = QHBoxLayout()
                h_box.addWidget(self.imageLabel[idx])
                h_box.addLayout(v_box_sliders)
                # Add description
                v_box_thumb = QVBoxLayout()
                v_box_thumb.addLayout(h_box)
                v_box_thumb.addWidget(self.label_description[idx])
                # Layout that will contain all the thumbnails
                self.h_box_thumb.addLayout(v_box_thumb)

            self.frame.setLayout(self.h_box_thumb)

        else:
            # Render thumbnails showing all slices from each image
            h_box_images = QHBoxLayout()
            h_box_images.setSpacing(10)
            v_box_scans = QVBoxLayout()

            # idx represents the index of the selected image
            for idx, file_path in enumerate(self.file_paths):
                file_path_rel = os.path.relpath(file_path, self.project.folder)
                # Setup description label
                self.label_description.insert(idx, ClickableLabel())
                self.label_description[idx].setFont(font)
                self.label_description[idx].clicked.connect(self.openTagsPopUp)
                # Looking for the tag value to display as a legend of the
                # thumbnail
                self.setThumbnail(file_path_rel, idx)

                if self.do_nothing[idx]:
                    continue

                # Determine slice parameters based on dimensions
                shape_len = len(self.img[idx].shape)

                # Depending of the dimension of the image, the legend of each
                # image and the number of images to display will change
                if shape_len == 3:
                    nb_slices, txt = self.img[idx].shape[2], "Slice n°"

                elif shape_len == 4:
                    nb_slices, txt = self.img[idx].shape[3], "Time n°"

                elif shape_len == 5:
                    nb_slices, txt = self.img[idx].shape[4], "Study n°"

                else:
                    continue

                # Limiting the number of images to the number chosen by the
                # user
                max_slices = min(
                    nb_slices, int(self.line_edit_nb_slices.text())
                )

                # Create slice thumbnails
                for i in range(max_slices):
                    pixm = self.image_to_pixmap(self.img[idx], i)
                    # label corresponds to the label where one image is
                    # displayed
                    label = QLabel(self)
                    label.setPixmap(pixm)
                    label.setToolTip(os.path.basename(file_path))
                    # Legend of the image (depends on the number of dimensions)
                    label_info = QLabel(f"{txt}{i + 1}")
                    label_info.setFont(font)
                    label_info.setAlignment(QtCore.Qt.AlignCenter)
                    v_box = QVBoxLayout()
                    v_box.addWidget(label)
                    v_box.addWidget(label_info)
                    # This layout allows to chain each image
                    h_box_images.addLayout(v_box)

                v_box_scans.addLayout(h_box_images)
                v_box_scans.addWidget(self.label_description[idx])

            self.frame.setLayout(v_box_scans)

        # Setup scroll area and control checkboxes for the thumbnail viewer
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.frame)
        h_box_check_box = QHBoxLayout()

        if self.check_box_slices.isChecked():
            h_box_check_box.addStretch(1)
            h_box_check_box.addWidget(self.label_orientation)
            h_box_check_box.addStretch(1)
            self.label_nb_slices.setHidden(False)
            self.line_edit_nb_slices.setHidden(False)
            h_box_check_box.addWidget(self.label_nb_slices)
            h_box_check_box.addWidget(self.line_edit_nb_slices)
            self.check_box_cursors.setHidden(True)

        else:
            self.check_box_cursors.setHidden(False)
            h_box_check_box.addWidget(self.check_box_cursors)
            h_box_check_box.addStretch(1)
            h_box_check_box.addWidget(self.label_orientation)
            h_box_check_box.addStretch(1)
            self.label_nb_slices.setHidden(True)
            self.line_edit_nb_slices.setHidden(True)

        h_box_check_box.addWidget(self.check_box_slices)
        self.v_box_final.addLayout(h_box_check_box)
        self.v_box_final.addWidget(self.scroll_area)

    def update_nb_slices(self):
        """
        Update slice configuration and refresh thumbnails.

        Triggered when the user modifies the number of slices to visualize.
        Updates the configuration with the new slice count and re-validates
        the current file paths to regenerate thumbnails accordingly.

        Notes:
        The slice count is retrieved from the UI line edit widget and applied
        to all loaded files.
        """
        nb_slices = self.line_edit_nb_slices.text()
        self.config.setNbAllSlicesMax(nb_slices)
        self.verify_slices(self.file_paths)

    def update_visualization(self):
        """
        Update visualization settings and refresh thumbnails.

        Synchronizes the slice visualization preference (show all slices
        vs. single slice) based on the checkbox state, updates the
        configuration, and regenerates thumbnails
        for the current file paths.

        This method is triggered when the user toggles the "show all slices"
        checkbox.
        """
        self.config.setShowAllSlices(self.check_box_slices.isChecked())
        self.verify_slices(self.file_paths)

    def verify_slices(self, file_paths):
        """
        Update slice display settings based on the number of selected files.

        When multiple files are selected, the "Show all slices" checkbox is
        disabled and unchecked to prevent viewing slices from multiple files
        simultaneously. For single file selection, the checkbox remains
        enabled.

        :param file_paths: List or collection of selected document file paths.
        """
        # Refresh configuration and release memory
        self.config = Config()
        self.mem_release()
        # Disable slice checkbox for multiple files
        is_multiple_files = len(file_paths) > 1

        if is_multiple_files:
            self.config.setShowAllSlices(False)
            self.check_box_slices.setCheckState(Qt.Unchecked)

        self.check_box_slices.setCheckable(not is_multiple_files)
        # Update slice display
        self.show_slices(file_paths)
        # Set orientation label based on view mode
        orientation_text = (
            "Radiological orientation"
            if self.config.isRadioView()
            else "Neurological orientation"
        )
        self.label_orientation.setText(orientation_text)
