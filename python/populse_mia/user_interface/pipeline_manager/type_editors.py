from soma.qt_gui.controls.File import FileControlWidget
from soma.qt_gui.controls.Directory import DirectoryControlWidget
from soma.qt_gui.controls.List_File_offscreen \
    import OffscreenListFileControlWidget
from soma.qt_gui import controller_widget
from soma.qt_gui.qt_backend import Qt
from functools import partial
from soma.utils.weak_proxy import weak_proxy
import traits.api as traits
import six


class PopulseFileControlWidget(FileControlWidget):

    @staticmethod
    def create_widget(parent, control_name, control_value, trait,
                      label_class=None, user_data=None):
        """ Method to create the file widget.

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
            parent, control_name, control_value, trait,
            label_class=label_class, user_data=user_data)
        if user_data is None:
            user_data = {}
        widget.user_data = user_data  # regular File does not store data

        layout = widget.layout()

        project = user_data.get('project')
        scan_list = user_data.get('scan_list')
        main_window = user_data.get('main_window')
        if project and scan_list:
            # Create a browse button
            button = Qt.QPushButton("Filter", widget)
            button.setObjectName('filter_button')
            button.setStyleSheet('QPushButton#filter_button '
                                '{padding: 2px 10px 2px 10px; margin: 0px;}')
            layout.addWidget(button)
            widget.filter_b = button

            # Set a callback on the browse button
            control_class = parent.get_control_class(trait)
            node_name = getattr(parent.controller, 'name', None)
            if node_name is None:
                node_name = parent.controller.__class__.__name__
            browse_hook = partial(
                control_class.filter_clicked, weak_proxy(widget), node_name,
                control_name)
                                    #parameters, process)
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
        from populse_mia.user_interface.pipeline_manager.node_controller \
            import PlugFilter

        project = widget.user_data.get('project')
        scan_list = widget.user_data.get('scan_list')
        main_window = widget.user_data.get('main_window')
        node_controller = widget.user_data.get('node_controller')
        widget.pop_up = PlugFilter(project, scan_list, None, #(process)
                                   node_name, plug_name, node_controller,
                                   main_window)
        widget.pop_up.setWindowModality(Qt.Qt.WindowModal)
        widget.pop_up.show()
        widget.pop_up.plug_value_changed.connect(
            partial(PopulseFileControlWidget.update_plug_value_from_filter,
                    widget, plug_name))

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
            res = filter_res_list[0]
        else:
            res = traits.Undefined

        # Set the selected file path to the path sub control
        widget.path.set_value(six.text_type(res))


class PopulseDirectoryControlWidget(DirectoryControlWidget):

    @staticmethod
    def create_widget(parent, control_name, control_value, trait,
                      label_class=None, user_data=None):
        return PopulseFileControlWidget.create_widget(
            parent, control_name, control_value, trait,
            label_class=label_class, user_data=user_data)

    @staticmethod
    def filter_clicked(widget, node_name, plug_name):
        """Display a filter widget.

        :param node_name: name of the node
        :param plug_name: name of the plug
        """
        # this import is not at the beginning of the file to avoid a cyclic
        # import issue.
        from populse_mia.user_interface.pipeline_manager.node_controller \
            import PlugFilter

        project = widget.user_data.get('project')
        scan_list = widget.user_data.get('scan_list')
        main_window = widget.user_data.get('main_window')
        node_controller = widget.user_data.get('node_controller')
        widget.pop_up = PlugFilter(project, scan_list, None, #(process)
                                   node_name, plug_name, node_controller,
                                   main_window)
        widget.pop_up.show()
        widget.pop_up.plug_value_changed.connect(
            partial(
                PopulseDirectoryControlWidget.update_plug_value_from_filter,
                widget, plug_name))

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

    @staticmethod
    def create_widget(parent, control_name, control_value, trait,
                      label_class=None, user_data=None):
        """ Method to create the list widget.

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
            parent, control_name, control_value, trait,
            label_class=label_class, user_data=user_data)

        layout = widget.layout()

        project = user_data.get('project')
        scan_list = user_data.get('scan_list')
        main_window = user_data.get('main_window')
        if project and scan_list:
            # Create a browse button
            button = Qt.QPushButton("Filter", widget)
            button.setObjectName('filter_button')
            button.setStyleSheet('QPushButton#filter_button '
                                '{padding: 2px 10px 2px 10px; margin: 0px;}')
            layout.addWidget(button)
            widget.filter_b = button

            # Set a callback on the browse button
            control_class = parent.get_control_class(trait)
            node_name = getattr(parent.controller, 'name', None)
            if node_name is None:
                node_name = parent.controller.__class__.__name__
            browse_hook = partial(
                control_class.filter_clicked, weak_proxy(widget), node_name,
                control_name)
                                    #parameters, process)
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
        from populse_mia.user_interface.pipeline_manager.node_controller \
            import PlugFilter

        project = widget.user_data.get('project')
        scan_list = widget.user_data.get('scan_list')
        main_window = widget.user_data.get('main_window')
        node_controller = widget.user_data.get('node_controller')
        widget.pop_up = PlugFilter(project, scan_list, None, #(process)
                                   node_name, plug_name, node_controller,
                                   main_window)
        widget.pop_up.show()
        widget.pop_up.plug_value_changed.connect(
            partial(
                PopulseOffscreenListFileControlWidget.update_plug_value_from_filter,
                widget, plug_name))

    @staticmethod
    def update_plug_value_from_filter(widget, plug_name, filter_res_list):
        """Update the plug value from a filter result.

        :param plug_name: name of the plug
        :param filter_res_list: list of the filtered files
        """
        controller = widget.parent().controller
        setattr(controller, plug_name, filter_res_list)



#controller_widget.ControllerWidget._defined_controls['File'] \
    #= PopulseFileControlWidget
#controller_widget.ControllerWidget._defined_controls['Directory'] \
    #= PopulseDirectoryControlWidget


