"""
Define the Mia logger.

The soma control classes are overloaded for the needs of Mia.
"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

# isort: off

import logging
import os
import traits.api as traits
from functools import partial

# isort: on

# soma import
from soma.qt_gui.controls.Directory import DirectoryControlWidget
from soma.qt_gui.controls.File import FileControlWidget
from soma.qt_gui.controls.List_File_offscreen import (
    OffscreenListFileControlWidget,
)
from soma.qt_gui.qt_backend import Qt, QtGui, QtWidgets
from soma.utils.weak_proxy import weak_proxy

# populse_mia import
from populse_mia.user_interface.pipeline_manager.plug_filter import PlugFilter

__all__ = [
    "PopulseFileControlWidget",
    "PopulseDirectoryControlWidget",
    "PopulseOffscreenListFileControlWidget",
    "PopulseUndefinedControlWidget",
]

logger = logging.getLogger(__name__)


class PopulseFileControlWidget(FileControlWidget):
    """
    Widget control for selecting a file.

    Provides methods to create a file selection widget, display a filter
    dialog, and update plug values based on filter results.

    Contains:
        Methods:
            - create_widget: Method to create the file widget.
            - filter_clicked: Display a filter widget.
            - update_plug_value_from_filter: Update the plug value from
              a filter result.
    """

    @staticmethod
    def create_widget(
        parent,
        control_name,
        control_value,
        trait,
        label_class=None,
        user_data=None,
    ):
        """
        Creates a file selection widget.

        :param parent: The parent widget.
        :type parent: soma.qt_gui.controller_widget.ControllerWidget
        :param control_name: The name of the control to create.
        :type control_name: str
        :param control_value: The default control value.
        :type control_value: str
        :param trait: The trait associated with the control.
        :type trait: traits.ctrait.CTrait
        :param label_class: Custom label widget class.
        :type label_class: QWidget
        :param user_data: Additional user data.
        :type user_data: dict

        :return: A tuple containing the created widget and its associated
         label. The widget includes a QLineEdit ('path') and a browse button
         ('browse').
        :rtype: Tuple[QWidget, QLabel]

        Contains:
            Inner functions:
                - _is_number: Checks if a value is a number.

        """
        # Create the widget that will be used to select a file
        widget, label = FileControlWidget.create_widget(
            parent,
            control_name,
            control_value,
            trait,
            label_class=label_class,
            user_data=user_data,
        )
        user_data = user_data or {}
        # regular File does not store data
        widget.user_data = user_data
        layout = widget.layout()
        project = user_data.get("project")
        scan_list = user_data.get("scan_list")
        connected_inputs = user_data.get("connected_inputs", set())

        def _is_number(value):
            """
            Checks if a value is a number.

            :param value: The value to check.
            :type value: str

            :return: True if the value is a number, False otherwise.
            :rtype: bool
            """

            try:
                int(value)
                return True

            except ValueError:
                return False

        # files in a list don't get a Filter button.
        if (
            project
            and scan_list
            and not trait.output
            and control_name not in connected_inputs
            and not _is_number(control_name)
        ):
            # Create a browse button
            button = Qt.QPushButton("Filter", widget)
            button.setObjectName("filter_button")
            button.setStyleSheet(
                "QPushButton#filter_button "
                "{padding: 2px 10px 2px 10px; margin: 0px;}"
            )
            layout.addWidget(button)
            widget.filter_b = button
            # Set a callback on the browse button
            control_class = parent.get_control_class(trait)
            node_name = getattr(
                parent.controller, "name", parent.controller.__class__.__name__
            )
            browse_hook = partial(
                control_class.filter_clicked,
                weak_proxy(widget),
                node_name,
                control_name,
            )
            widget.filter_b.clicked.connect(browse_hook)

        return (widget, label)

    @staticmethod
    def filter_clicked(widget, node_name, plug_name):
        """
        Display a filter widget.

        :param widget: The parent widget.
        :type widget: QWidget
        :param node_name: The name of the node.
        :type node_name: str
        :param plug_name: The name of the plug.
        :type plug_name: str
        """
        project = widget.user_data.get("project")
        scan_list = widget.user_data.get("scan_list")
        main_window = widget.user_data.get("main_window")
        node_controller = widget.user_data.get("node_controller")
        widget.pop_up = PlugFilter(
            project,
            scan_list,
            None,
            node_name,
            plug_name,
            node_controller,
            main_window,
        )
        widget.pop_up.setWindowModality(Qt.Qt.WindowModal)
        widget.pop_up.show()
        widget.pop_up.plug_value_changed.connect(
            partial(
                PopulseFileControlWidget.update_plug_value_from_filter,
                widget,
                plug_name,
            )
        )

    @staticmethod
    def update_plug_value_from_filter(widget, plug_name, filter_res_list):
        """
        Updates the plug value based on a filter result.

        :param widget: The parent widget.
        :type widget: QWidget
        :param plug_name: The name of the plug.
        :type plug_name: str
        :param filter_res_list: List of filtered file paths.
        :type filter_res_list: List[str]
        """
        # If the list contains only one element, setting
        # this element as the plug value
        len_list = len(filter_res_list)

        if len_list == 1:
            res = filter_res_list[0]

        else:
            res = traits.Undefined

            if len_list > 1:
                msg = QtWidgets.QMessageBox()
                msg.setText(
                    f"The '{plug_name}' parameter must by a filename, "
                    f"but received {filter_res_list}."
                )
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setWindowTitle("TraitError")
                msg.exec_()

        # Set the selected file path to the path sub control
        widget.path.set_value(str(res))


class PopulseDirectoryControlWidget(DirectoryControlWidget):
    """
    Widget for selecting a directory.

    Contains:
        Methods:
            - create_widget: Creates the directory selection widget.
            - filter_clicked: Displays a filtering widget.
            - update_plug_value_from_filter: Updates the plug value based on
              the filter result.
    """

    @staticmethod
    def create_widget(
        parent,
        control_name,
        control_value,
        trait,
        label_class=None,
        user_data=None,
    ):
        """
        Creates and returns a directory selection widget.

        :param parent: The parent widget.
        :type parent: soma.qt_gui.controller_widget.ControllerWidget
        :param control_name: The name of the control.
        :type control_name: str
        :param control_value: The initial value of the control.
        :type control_value: any
        :param trait: The trait associated with the control.
        :type trait: traits.ctrait.CTrait
        :param label_class: The label class (optional).
        :type label_class: QWidget
        :param user_data: User data associated with the widget.
        :type user_data: dict

        :return: The directory selection widget.
        :rtype: QWidget
        """

        return PopulseFileControlWidget.create_widget(
            parent,
            control_name,
            control_value,
            trait,
            label_class=label_class,
            user_data=user_data,
        )

    @staticmethod
    def filter_clicked(widget, node_name, plug_name):
        """
        Displays a filter widget for selecting a directory.

        :param widget: The calling widget.
        :type widget: QWidget
        :param node_name: The name of the node.
        :type node_name: str
        :param plug_name: The name of the associated plug.
        :type plug_name: str
        """
        project = widget.user_data.get("project")
        scan_list = widget.user_data.get("scan_list")
        main_window = widget.user_data.get("main_window")
        node_controller = widget.user_data.get("node_controller")
        widget.pop_up = PlugFilter(
            project,
            scan_list,
            None,
            node_name,
            plug_name,
            node_controller,
            main_window,
        )
        widget.pop_up.show()
        widget.pop_up.plug_value_changed.connect(
            partial(
                PopulseDirectoryControlWidget.update_plug_value_from_filter,
                widget,
                plug_name,
            )
        )

    @staticmethod
    def update_plug_value_from_filter(widget, plug_name, filter_res_list):
        """
        Updates the plug value based on the filter result.

        If multiple elements are returned, the first one is selected.
        If the selected element is not a directory, its parent directory
        is used.

        :param widget: The widget being updated.
        :type widget: QWidget
        :param plug_name: The name of the associated plug.
        :type plug_name: str
        :param filter_res_list: The list of filtered files.
        :type filter_res_list: (list[str]
        """

        if filter_res_list:
            res = str(filter_res_list[0])
            res = res if os.path.isdir(res) else os.path.dirname(res)

        else:
            res = traits.Undefined

        # Set the selected file path to the path sub control
        widget.path.setText(str(res))


class PopulseOffscreenListFileControlWidget(OffscreenListFileControlWidget):
    """
    A control widget for entering a list of files.

    Contains:
        Methods:
            - create_widget: Creates the list of files widget.
            - filter_clicked: Displays a filter widget.
            - update_plug_value_from_filter: Updates the plug value based on
              the filter result.
    """

    @staticmethod
    def create_widget(
        parent,
        control_name,
        control_value,
        trait,
        label_class=None,
        user_data=None,
    ):
        """
        Creates and returns a file list control widget with an optional
        filter button.


        :param parent: The parent widget.
        :type parent: soma.qt_gui.controller_widget.ControllerWidget
        :param control_name: The name of the control.
        :type control_name: str
        :param control_value: The default control value.
        :type control_value: list
        :param trait: The trait associated with the control.
        :type trait: traits.ctrait.CTrait
        :param label_class: A Qt widget class for the label.
        :type label_class: PyQt5.QtWidgets.QLabel
        :param user_data: Additional data, including project, scan list, and
         connected inputs.
         :type user_data: dict

        :return: A tuple (QLabel, QWidget).
        :rtype: tuple[QLabel, QWidget)]
        """
        widget, label = OffscreenListFileControlWidget.create_widget(
            parent,
            control_name,
            control_value,
            trait,
            label_class=label_class,
            user_data=user_data,
        )
        layout = widget.layout()
        project = user_data.get("project")
        scan_list = user_data.get("scan_list")
        connected_inputs = user_data.get("connected_inputs", set())

        if (
            project
            and scan_list
            and not trait.output
            and control_name not in connected_inputs
        ):
            # Create a browse button
            button = Qt.QPushButton("Filter", widget)
            button.setObjectName("filter_button")
            button.setStyleSheet(
                "QPushButton#filter_button "
                "{padding: 2px 10px 2px 10px; margin: 0px;}"
            )
            layout.addWidget(button)
            widget.filter_b = button

            # Set a callback on the browse button
            control_class = parent.get_control_class(trait)
            node_name = getattr(
                parent.controller, "name", parent.controller.__class__.__name__
            )

            browse_hook = partial(
                control_class.filter_clicked,
                weak_proxy(widget),
                node_name,
                control_name,
            )
            # parameters, process)
            widget.filter_b.clicked.connect(browse_hook)

        return (widget, label)

    @staticmethod
    def filter_clicked(widget, node_name, plug_name):
        """
        Displays a filter widget for selecting files.

        :param widget: The file control widget.
        :type widget: QWidget
        :param node_name: The name of the node.
        :type node_name: str
        :param plug_name: The name of the plug.
        :type plug_name: str
        """
        project = widget.user_data.get("project")
        scan_list = widget.user_data.get("scan_list")
        main_window = widget.user_data.get("main_window")
        node_controller = widget.user_data.get("node_controller")
        widget.pop_up = PlugFilter(
            project,
            scan_list,
            None,
            node_name,
            plug_name,
            node_controller,
            main_window,
        )
        widget.pop_up.show()
        # fmt: off
        widget.pop_up.plug_value_changed.connect(
            partial(
                (
                    PopulseOffscreenListFileControlWidget.
                    update_plug_value_from_filter
                ),
                widget,
                plug_name,
            )
        )
        # fmt: on

    @staticmethod
    def update_plug_value_from_filter(widget, plug_name, filter_res_list):
        """
        Updates the plug value based on the filter results.

        :param widget: The file control widget.
        :type widget: widget
        :param plug_name: The name of the plug.
        :type plug_name: str
        :param filter_res_list: The filtered file list.
        :type filter_res_list: list

        """
        controller = widget.parent().controller

        try:
            setattr(controller, plug_name, filter_res_list)

        except Exception as exc:
            logger.warning(
                "Failed to update plug '%s' from filter results: %s",
                plug_name,
                exc,
            )


class PopulseUndefinedControlWidget:
    """
    Widget control for handling Undefined trait values in a Qt interface.

    This class provides methods to create, validate, and update Qt widgets
    that represent undefined values in a controller-based UI framework.

    Contains:
        Methods:
            - check: Check if a controller widget control is filled correctly.
            - connect: Connect a 'Str' or 'String' controller trait and a
              'StrControlWidget' controller widget control.
            - create_widget: Method to create the Undefined widget.
            - disconnect: Disconnect a 'Str' or 'String' controller trait and
              a 'StrControlWidget' controller widget control.
            - is_valid: Method to check if the new control value is correct.
            - update_controller: Update one element of the controller.
            - update_controller_widget: Update one element of the controller
              widget.
    """

    # Class constants
    UNDEFINED_TEXT = "<undefined>"
    STYLED_UNDEFINED_TEXT = (
        "<style>background-color: gray; text-color: red;</style>" "<undefined>"
    )
    VALID_REPRESENTATIONS = [UNDEFINED_TEXT, STYLED_UNDEFINED_TEXT]

    @classmethod
    def check(cls, control_instance):
        """
        Check if a controller widget control is filled correctly.

        This method is a placeholder in this implementation.

        :param cls:  A StrControlWidget control.
        :type cls: StrControlWidget
        :param control_instance: The control widget to check.
        :type control_instance: QLineEdit
        """
        # Implementation can be added here if needed
        pass

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """
        Connect a 'Str' or 'String' controller trait and a 'StrControlWidget'
        controller widget control.

        This method is a placeholder in this implementation.

        :param cls: A StrControlWidget control.
        :type cls: StrControlWidget
        :param controller_widget: The controller widget containing the
         controller.
        :type controller_widget: ControllerWidget
        :param control_name: The name of the control to connect.
        :type control_name: str
        :param control_instance: The widget instance to connect.
        :type control_instance: QWidget
        """
        # Signal connections can be added here if needed
        pass

    @staticmethod
    def create_widget(
        parent,
        control_name,
        control_value,
        trait,
        label_class=None,
        user_data=None,
    ):
        """
        Create a widget for displaying Undefined values in the UI.

        This method creates a read-only QLabel widget that displays a styled
        representation of undefined/null values, along with an optional label.

        :param parent: The parent widget that will contain the created widgets.
        :type parent: QWidget
        :param control_name: The name/text for the label widget. If None,
         no label is created.
        :type control_name: str
        :param control_value: The undefined value to display (currently unused
         in implementation).
        :type control_value: str
        :param trait: The trait object associated with this control (currently
         unused in implementation).
        :type trait:  traits.ctrait.CTrait
        :param label_class: The Qt widget class to use for creating the label.
         Defaults to QtGui.QLabel if None.
        :type label_class: QtGui.QLabel
        :param user_data: Additional user-defined data (currently unused in
         implementation).
        :type user_data: dict

        :return: (tuple): A tuple containing:

            - control_widget: A QLabel displaying the styled undefined value
              text.
            - label_widget: The associated label widget, or None if
              control_name is None.
        :rtype: tuple.
        """
        # Create widget with styled representation of Undefined
        widget = Qt.QLabel(
            PopulseUndefinedControlWidget.STYLED_UNDEFINED_TEXT, parent
        )
        # Create and return the label
        if label_class is None:
            label_class = QtGui.QLabel

        if control_name is not None:
            label = label_class(control_name, parent)

        else:
            label = None

        return (widget, label)

    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """
        Disconnect a 'Str' or 'String' controller trait and a
        'StrControlWidget' controller widget control.

        This method is a placeholder in this implementation.

        :param controller_widget: The controller widget containing the
         controller.
        :type controller_widget: ControllerWidget
        :param control_name: The name of the control to disconnect.
        :type control_name: str
        :param control_instance: The widget instance to disconnect.
        :type control_instance: QWidget
        """
        # Signal disconnections can be added here if needed
        pass

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """
        Validate if the control contains an Undefined value representation.

        :param args: Additional positional arguments, unused and kept for
         interface compatibility.
        :param kwargs: Additional keyword arguments, unused and kept for
         interface compatibility.
        :param control_instance: The control widget to validate.
        :type control_instance: QWidget

        :return: True if the control value is Undefined, False otherwise.
        :rtype: bool
        """

        # Get the control current value
        control_text = control_instance.text()
        return control_text in (
            PopulseUndefinedControlWidget.VALID_REPRESENTATIONS
        )

    @staticmethod
    def update_controller(
        controller_widget,
        control_name,
        control_instance,
        reset_invalid_value,
        *args,
        **kwargs,
    ):
        """
        Update the controller with the widget's value if valid.

        At the end the controller trait value with the name 'control_name'
        will match the controller widget user parameters defined in
        'control_instance'.

        :param args: Additional positional arguments, unused and kept for
         interface compatibility.
        :param kwargs: Additional keyword arguments, unused and kept for
         interface compatibility.
        :param controller_widget: The controller widget containing the
         controller to update.
        :type controller_widget: ControllerWidget
        :param control_name: The name of the control to synchronize with the
         controller.
        :type control_name: str
        :param control_instance: The widget instance to synchronize with the
         controller.
        :type control_instance: QWidget
        :param reset_invalid_value: (bool) If True and the value is invalid,
         reset the widget to the controller's value.
        :type reset_invalid_value: bool
        """

        # Update the controller only if the control is valid
        if PopulseUndefinedControlWidget.is_valid(control_instance):
            # Set controller's trait to Undefined
            new_trait_value = traits.Undefined
            setattr(
                controller_widget.controller, control_name, new_trait_value
            )
            # For debugging purposes, log the update action
            # logger.info(
            #     f"'PopulseUndefinedControlWidget' associated controller "
            #     f"trait '{control_name}' has been updated with "
            #     f"value '{new_trait_value}'."
            # )

        elif reset_invalid_value:
            # Invalid value, reset GUI to the previous value
            old_trait_value = getattr(
                controller_widget.controller, control_name
            )
            control_instance.setText(old_trait_value)

    @staticmethod
    def update_controller_widget(
        controller_widget, control_name, control_instance
    ):
        """
        Update the widget to reflect the controller's value.

        At the end the controller widget user editable parameter with the name
        'control_name' will match the controller trait value with the same
        name.

        :param controller_widget: The controller widget containing the
         controller.
        :type controller_widget: ControllerWidget
        :param control_name: The name of the control to synchronize.
        :type control_name: str
        :param control_instance: The widget instance to update.
        :type control_instance: QWidget
        """
        # Set the widget text to represent Undefined
        new_controller_value = str(traits.Undefined)
        control_instance.setText(new_controller_value)
        # For debugging purposes, log the update action
        # logger.info(
        #     f"'PopulseUndefinedControlWidget' has been updated "
        #     f"with value '{new_controller_value}'."
        # )
        # Update the controller to ensure consistency
        PopulseUndefinedControlWidget.update_controller(
            controller_widget, control_name, control_instance, True
        )
