"""
Define the Mia logger.

The soma control classes are overloaded for the needs of Mia.

:Contains:
    :Class:
        - PopulseFileControlWidget
        - PopulseDirectoryControlWidget
        - PopulseOffscreenListFileControlWidget
        - PopulseUndefinedControlWidget

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
from functools import partial

import traits.api as traits
from soma.qt_gui.controls.Directory import DirectoryControlWidget
from soma.qt_gui.controls.File import FileControlWidget
from soma.qt_gui.controls.List_File_offscreen import (
    OffscreenListFileControlWidget,
)
from soma.qt_gui.qt_backend import Qt, QtGui, QtWidgets
from soma.utils.weak_proxy import weak_proxy

logger = logging.getLogger(__name__)


class PopulseFileControlWidget(FileControlWidget):
    """
    Widget control for selecting a file.

    Provides methods to create a file selection widget, display a filter
    dialog, and update plug values based on filter results.

    :Contains:
        :Method:
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

        :param parent (QWidget): The parent widget.
        :param control_name (str): The name of the control to create.
        :param control_value (str): The default control value.
        :param trait (Trait): The trait associated with the control.
        :param label_class (Optional[Type[QWidget]]): Custom label widget
                                                      class.
        :param user_data (Optional[dict]): Additional user data.

        :return (Tuple[QWidget, QLabel]):
            A tuple containing the created widget and its associated label.
            The widget includes a QLineEdit ('path') and a browse
            button ('browse').
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

            :param value (str): The value to check.

            :return (bool): True if the value is a number, False otherwise.
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

        :param widget (QWidget): The parent widget.
        :param node_name (str): The name of the node.
        :param plug_name (str): The name of the plug.
        """
        # This import is not at the beginning of the file to avoid a cyclic
        # import issue.
        from .node_controller import PlugFilter

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

        :param widget (QWidget): The parent widget.
        :param plug_name (str): The name of the plug.
        :param filter_res_list (List[str]): List of filtered file paths.
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

    :Contains:
        :Method:
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

        :param parent (QWidget): The parent widget.
        :param control_name (str): The name of the control.
        :param control_value (Any): The initial value of the control.
        :param trait (Any): The trait associated with the control.
        :param label_class (Optional[Any]): The label class (optional).
        :param user_data (Optional[dict]): User data associated with
                                           the widget.

        :return (QWidget): The directory selection widget.
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

        :param widget (QWidget): The calling widget.
        :param node_name (str): The name of the node.
        :param plug_name (str): The name of the associated plug.
        """
        # this import is not at the beginning of the file to avoid a cyclic
        # import issue.
        from .node_controller import PlugFilter

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

        :param widget (QWidget): The widget being updated.
        :param plug_name (str): The name of the associated plug.
        :param filter_res_list (list[str]): The list of filtered files.
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

    :Contains:
        :Method:
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


        :param parent (QWidget): The parent widget.
        :param control_name (str): The name of the control.
        :param control_value (list): The default control value.
        :param trait (Trait): The trait associated with the control.
        :param label_class (type): A Qt widget class for the label.
        :param user_data (dict): Additional data, including project,
                                 scan list, and connected inputs.

        :return (tuple): A tuple (control widget, (QLabel, QWidget)).
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

        :param widget (QWidget): The file control widget.
        :param node_name (str): The name of the node.
        :param plug_name (str): The name of the plug.
        """
        # this import is not at the beginning of the file to avoid a cyclic
        # import issue.
        from .node_controller import PlugFilter

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

        :param widget (QWidget): The file control widget.
        :param plug_name (str): The name of the plug.
        :param filter_res_list (list): The filtered file list.

        """
        controller = widget.parent().controller

        try:
            setattr(controller, plug_name, filter_res_list)

        except Exception as e:
            logger.warning(e)


class PopulseUndefinedControlWidget:
    """
    Widget control for handling Undefined trait values in a Qt interface.

    This class provides methods to create, validate, and update Qt widgets
    that represent undefined values in a controller-based UI framework.


    :Contains:
        :Method:

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

        :param cls (StrControlWidget): A StrControlWidget control.
        :param control_instance (QLineEdit): The control widget to check.
        """
        # Implementation can be added here if needed
        pass

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """
        Connect a 'Str' or 'String' controller trait and a 'StrControlWidget'
        controller widget control.

        This method is a placeholder in this implementation.

        :param cls (StrControlWidget): A StrControlWidget control.
        :param controller_widget (ControllerWidget): The controller widget
                                                     containing the controller.
        :param control_name (str): The name of the control to connect.
        :param control_instance (QWidget): The widget instance to connect
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

        :param parent (QWidget): The parent widget that will contain the
                                 created widgets.
        :param control_name (str): The name/text for the label widget.
                                   If None, no label is created.
        :param control_value: The undefined value to display (currently
                              unused in implementation).
        :param trait: trait: The trait object associated with this control
                             (currently unused in implementation).
        :param label_class: The Qt widget class to use for creating the label.
                            Defaults to QtGui.QLabel if None.
        :param user_data: Additional user-defined data (currently unused in
                          implementation).

        :return (tuple): A tuple containing:
            - control_widget: A QLabel displaying the styled undefined value
                              text
            - label_widget: The associated label widget, or None if
                            control_name is None
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

        :param controller_widget (ControllerWidget): The controller widget
                                                     containing the controller.
        :param control_name (str): The name of the control to disconnect
        :param control_instance (QWidget): The widget instance to disconnect
        """
        # Signal disconnections can be added here if needed
        pass

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """
        Validate if the control contains an Undefined value representation.

        *args, **kwargs : Additional arguments. Not used, kept for
                          interface compatibility.

        :param control_instance (QWidget): The control widget to validate.

        :return (bool): True if the control value is Undefined, False
                         otherwise
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

        *args, **kwargs : Additional arguments. Not used, kept for
                          interface compatibility.

        :param controller_widget (ControllerWidget): The controller widget
                                                     containing the controller
                                                     to update
        :param control_name (str): The name of the control to synchronize
                                    with the controller
        :param  control_instance (QWidget): The widget instance to synchronize
                                            with the controller
        :param reset_invalid_value (bool): If True and the value is invalid,
                                           reset the widget to the
                                           controller's value
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

        At the end the controller widget user editable parameter with the
        name 'control_name' will match the controller trait value with the
        same name.

        :param controller_widget (ControllerWidget): The controller widget
                                                     containing the controller.
        :param control_name (str): The name of the control to synchronize.
        :param control_instance (QWidget): The widget instance to update.
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
