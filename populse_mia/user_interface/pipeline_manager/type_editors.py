# -*- coding: utf-8 -*-
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

import six
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
    """Control to enter a file.

    :Contains:
        :Method:
            - create_widget: method to create the file widget
            - filter_clicked: display a filter widget
            - update_plug_value_from_filter: update the plug value from
              a filter result
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
        """Method to create the file widget.

        Parameters
        ----------
        parent: QWidget (mandatory)
            the parent widget
        control_name: str (mandatory)
            the name of the control we want to create
        control_value: str (mandatory)
            the default control value
        trait: Tait (mandatory)
            the trait associated to the control
        label_class: Qt widget class (optional, default: None)
            the label widget will be an instance of this class. Its constructor
            will be called using 2 arguments: the label string and the parent
            widget.

        Returns
        -------
        out: 2-uplet
            a two element tuple of the form (control widget: QWidget with two
            elements, a QLineEdit in the 'path' parameter and a browse button
            in the 'browse' parameter, associated label: QLabel)
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
        if user_data is None:
            user_data = {}
        widget.user_data = user_data  # regular File does not store data

        layout = widget.layout()

        project = user_data.get("project")
        scan_list = user_data.get("scan_list")
        connected_inputs = user_data.get("connected_inputs", set())

        def is_number(x):
            """Check if x is a number.

            Parameters
            ----------
            x: the name of the control we want to create (str)

            Returns
            -------
            out: bool
            True if the control name is a number,
            False otherwise
            """

            try:
                int(x)
                return True

            except ValueError:
                return False

        # files in a list don't get a Filter button.
        if (
            project
            and scan_list
            and not trait.output
            and control_name not in connected_inputs
            and not is_number(control_name)
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
            node_name = getattr(parent.controller, "name", None)
            if node_name is None:
                node_name = parent.controller.__class__.__name__
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
        """Display a filter widget.

        :param node_name: name of the node
        :param plug_name: name of the plug
        """
        # this import is not at the beginning of the file to avoid a cyclic
        # import issue.
        # fmt: off
        # isort: off
        from populse_mia.user_interface.pipeline_manager.\
            node_controller import PlugFilter
        # isort: on
        # fmt: on

        project = widget.user_data.get("project")
        scan_list = widget.user_data.get("scan_list")
        main_window = widget.user_data.get("main_window")
        node_controller = widget.user_data.get("node_controller")
        widget.pop_up = PlugFilter(
            project,
            scan_list,
            None,  # (process)
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
        """Update the plug value from a filter result.

        :param plug_name: name of the plug
        :param filter_res_list: list of the filtered files
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
                    "The '{0}' parameter must by a filename, "
                    "but a value of {1} <class 'list'> was "
                    "specified.".format(plug_name, filter_res_list)
                )
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setWindowTitle("TraitError")
                msg.exec_()
                res = traits.Undefined

        # Set the selected file path to the path sub control
        widget.path.set_value(six.text_type(res))


class PopulseDirectoryControlWidget(DirectoryControlWidget):
    """Control to enter a Directory.

    :Contains:
        :Method:
            - create_widget: method to create the file widget
            - filter_clicked: display a filter widget
            - update_plug_value_from_filter: update the plug value from
              a filter result

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
        """Method to create the directory widget."""

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
        """Display a filter widget.

        :param node_name: name of the node
        :param plug_name: name of the plug
        """
        # this import is not at the beginning of the file to avoid a cyclic
        # import issue.
        # fmt: off
        # isort: off
        from populse_mia.user_interface.pipeline_manager.\
            node_controller import PlugFilter
        # fmt: on
        # isort: on

        project = widget.user_data.get("project")
        scan_list = widget.user_data.get("scan_list")
        main_window = widget.user_data.get("main_window")
        node_controller = widget.user_data.get("node_controller")
        widget.pop_up = PlugFilter(
            project,
            scan_list,
            None,  # (process)
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
        """Update the plug value from a filter result.

        :param plug_name: name of the plug
        :param filter_res_list: list of the filtered files
        """
        # If the list contains only one element, setting
        # this element as the plug value
        len_list = len(filter_res_list)
        if len_list >= 1:
            res = six.text_type(filter_res_list[0])
            if not os.path.isdir(res):
                res = os.path.dirname(res)
        else:
            res = traits.Undefined

        # Set the selected file path to the path sub control
        widget.path.setText(six.text_type(res))


class PopulseOffscreenListFileControlWidget(OffscreenListFileControlWidget):
    """Control to enter a list of files.

    :Contains:
        :Method:
            - create_widget: method to create the list of files widget
            - filter_clicked: display a filter widget
            - update_plug_value_from_filter: update the plug value from
              a filter result

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
        """Method to create the list of files widget.

        Parameters
        ----------
        parent: QWidget (mandatory)
            the parent widget
        control_name: str (mandatory)
            the name of the control we want to create
        control_value: list of items (mandatory)
            the default control value
        trait: Tait (mandatory)
            the trait associated to the control
        label_class: Qt widget class (optional, default: None)
            the label widget will be an instance of this class. Its constructor
            will be called using 2 arguments: the label string and the parent
            widget.

        Returns
        -------
        out: 2-uplet
            a two element tuple of the form (control widget: ,
            associated labels: (a label QLabel, the tools QWidget))
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
            node_name = getattr(parent.controller, "name", None)
            if node_name is None:
                node_name = parent.controller.__class__.__name__
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
        """Display a filter widget.

        :param node_name: name of the node
        :param plug_name: name of the plug
        """
        # this import is not at the beginning of the file to avoid a cyclic
        # import issue.
        # fmt: off
        # isort: off
        from populse_mia.user_interface.pipeline_manager.\
            node_controller import PlugFilter
        # isort: on
        # fmt: on

        project = widget.user_data.get("project")
        scan_list = widget.user_data.get("scan_list")
        main_window = widget.user_data.get("main_window")
        node_controller = widget.user_data.get("node_controller")
        widget.pop_up = PlugFilter(
            project,
            scan_list,
            None,  # (process)
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
        """Update the plug value from a filter result.

        :param plug_name: name of the plug
        :param filter_res_list: list of the filtered files
        """
        controller = widget.parent().controller

        try:
            setattr(controller, plug_name, filter_res_list)

        except Exception as e:
            print(e)


# controller_widget.ControllerWidget._defined_controls['File'] \
# = PopulseFileControlWidget
# controller_widget.ControllerWidget._defined_controls['Directory'] \
# = PopulseDirectoryControlWidget


class PopulseUndefinedControlWidget(object):
    """Control for Undefined value."""

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """Method to check if the new control value is correct.

        Parameters
        ----------
        control_instance: QWidget (mandatory)
            the control widget we want to validate

        Returns
        -------
        out: bool
            True if the control value is Undefined,
            False otherwise
        """

        # Get the control current value
        control_text = control_instance.text()

        is_valid = False

        if control_text in [
            "<undefined>",
            "<style>background-color: gray; "
            "text-color: red;</style><undefined>",
        ]:
            is_valid = True

        return is_valid

    @classmethod
    def check(cls, control_instance):
        """Check if a controller widget control is filled correctly.

        Parameters
        ----------
        cls: StrControlWidget (mandatory)
            a StrControlWidget control
        control_instance: QLineEdit (mandatory)
            the control widget we want to validate
        """

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
        """Method to create the Undefined widget.

        Parameters
        ----------
        parent: QWidget (mandatory)
            the parent widget
        control_name: str (mandatory)
            the name of the control we want to create
        control_value: str (mandatory)
            the default control value
        trait: Tait (mandatory)
            the trait associated to the control
        label_class: Qt widget class (optional, default: None)
            the label widget will be an instance of this class. Its constructor
            will be called using 2 arguments: the label string and the parent
            widget.

        Returns
        -------
        out: 2-uplet
            a two element tuple of the form (control widget: QLineEdit,
            associated label: QLabel)
        """

        # Create the widget
        widget = Qt.QLabel(
            "<style>background-color: gray; text-color: red;</style>"
            + str(traits.Undefined),
            parent,
        )

        # Create the label associated with the string widget
        control_label = control_name
        if label_class is None:
            label_class = QtGui.QLabel
        if control_label is not None:
            label = label_class(control_label, parent)
        else:
            label = None

        return (widget, label)

    @staticmethod
    def update_controller(
        controller_widget,
        control_name,
        control_instance,
        reset_invalid_value,
        *args,
        **kwargs
    ):
        """Update one element of the controller.

        At the end the controller trait value with the name 'control_name'
        will match the controller widget user parameters defined in
        'control_instance'.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """

        # Update the controller only if the control is valid
        if PopulseUndefinedControlWidget.is_valid(control_instance):
            # Define the control value
            new_trait_value = traits.Undefined
            setattr(
                controller_widget.controller, control_name, new_trait_value
            )
            logger.debug(
                "'PopulseUndefinedControlWidget' associated controller trait "
                "'{0}' has been updated with value '{1}'.".format(
                    control_name, new_trait_value
                )
            )
        elif reset_invalid_value:
            # invalid, reset GUI to older value
            old_trait_value = getattr(
                controller_widget.controller, control_name
            )
            control_instance.setText(old_trait_value)

    @staticmethod
    def update_controller_widget(
        controller_widget, control_name, control_instance
    ):
        """Update one element of the controller widget.

        At the end the controller widget user editable parameter with the
        name 'control_name' will match the controller trait value with the same
        name.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """

        # Define the trait value
        new_controller_value = str(traits.Undefined)

        # Set the trait
        control_instance.setText(new_controller_value)
        logger.debug(
            "'PopulseUndefinedControlWidget' has been updated "
            "with value '{0}'.".format(new_controller_value)
        )
        # Set the controller trait value
        PopulseUndefinedControlWidget.update_controller(
            controller_widget, control_name, control_instance, True
        )

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """Connect a 'Str' or 'String' controller trait and a
        'StrControlWidget' controller widget control.

        Parameters
        ----------
        cls: StrControlWidget (mandatory)
            a StrControlWidget control
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str (mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller

        """

        pass

    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """Disconnect a 'Str' or 'String' controller trait and a
        'StrControlWidget' controller widget control.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """

        pass
