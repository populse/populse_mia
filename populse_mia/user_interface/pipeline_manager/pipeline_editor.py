"""
Module that execute the pipeline manager tab menu actions
and allow to edit graphically a pipeline.

Contains:
    Class:
        - PipelineEditor
        - PipelineEditorTabs
    Function:
        - save_pipeline
        - get_path
        - find_filename
        - values

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
import sys

import yaml

# Capsul imports
from capsul.api import (
    Node,
    PipelineNode,
    Process,
    Switch,
    get_process_instance,
)
from capsul.pipeline.pipeline_nodes import ProcessNode
from capsul.pipeline.python_export import save_py_pipeline
from capsul.pipeline.xml import save_xml_pipeline
from capsul.qt_gui.widgets.pipeline_developer_view import (
    NodeGWidget,
    PipelineDeveloperView,
)

# PyQt5 imports
from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox

# soma-base imports
from soma.utils.weak_proxy import weak_proxy
from traits.api import TraitError

from populse_mia.software_properties import Config

# Populse_mia imports
from populse_mia.user_interface.pipeline_manager.node_controller import (
    FilterWidget,
)
from populse_mia.user_interface.pop_ups import PopUpClosePipeline

logger = logging.getLogger(__name__)


class PipelineEditor(PipelineDeveloperView):
    """View to edit a pipeline graphically.

    .. Methods:
        - _del_link: deletes a link
        - _export_plug: export a plug to a pipeline global input or output
        - _release_grab_link: method called when a link is released
        - _remove_plug: removes a plug
        - add_link: add a link between two nodes
        - add_named_process: adds a process to the pipeline
        - check_modifications: checks if the nodes of the pipeline have been
           modified
        - del_node: deletes a node
        - dragEnterEvent: event handler when the mouse enters the widget
        - dragMoveEvent: event handler when the mouse moves in the widget
        - dropEvent: event handler when something is dropped in the widget
        - export_node_plugs: exports all the plugs of a node
        - get_current_filename: returns the relative path the pipeline was
           last saved to. Empty if never saved.
        - save_pipeline: saves the pipeline
        - update_history: updates the history for undos and redos
        - update_node_name: updates a node name
        - update_plug_value: updates a plug value
    """

    # The signal that will be emitted when the pipeline is saved
    pipeline_saved = QtCore.pyqtSignal(str)
    # The signal that will be emitted when the pipeline is modified
    pipeline_modified = QtCore.pyqtSignal(PipelineDeveloperView)

    def __init__(self, project, main_window):
        """Initialization of the PipelineEditor.

        :param project: current project in the software
        :param main_window: current main window
        """
        PipelineDeveloperView.__init__(
            self,
            pipeline=None,
            allow_open_controller=True,
            show_sub_pipelines=True,
            enable_edition=True,
        )
        engine = Config.get_capsul_engine()
        self.scene.pipeline.set_study_config(engine.study_config)
        self.project = project
        self.main_window = main_window
        # Undo/Redo
        self.undos = []
        self.redos = []
        self.userlevel = Config().get_user_level()

    def _del_link(self, link=None, from_undo=False, from_redo=False):
        """Delete a link.

        :param link: string representation of a link
           (e.g. "process1.out->process2.in")
        :param from_undo: boolean, True if the action has been made using an
           undo
        :param from_redo: boolean, True if the action has been made using a
           redo
        """

        if not link:
            link = self._current_link

        else:
            self._current_link = link

        (
            source_node_name,
            source_plug_name,
            source_node,
            source_plug,
            dest_node_name,
            dest_plug_name,
            dest_node,
            dest_plug,
        ) = self.scene.pipeline.parse_link(link)
        (
            dest_node_name,
            dest_parameter,
            dest_node,
            dest_plug,
            weak_link,
        ) = list(source_plug.links_to)[0]
        active = source_plug.activated and dest_plug.activated
        self._current_link_def = (
            source_node,
            source_plug,
            dest_node,
            dest_plug,
        )
        # Calling the original method
        PipelineDeveloperView._del_link(self)
        # For history
        history_maker = [
            "delete_link",
            (source_node_name, source_plug_name),
            (dest_node_name, dest_plug_name),
            active,
            weak_link,
        ]
        self.update_history(history_maker, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Link {link} has been deleted."
        )

    def _export_plug(
        self,
        pipeline_parameter=False,
        optional=None,
        weak_link=None,
        from_undo=False,
        from_redo=False,
        temp_plug_name=None,
        multi_export=False,
    ):
        """Export a plug to a pipeline global input or output.

        :param pipeline_parameter: name of the pipeline input/output
        :param optional: True if the plug is optional
        :param weak_link: True if the link is weak
        :param from_undo: True if this method is called from an undo action
        :param from_redo: True if this method is called from a redo action
        :param temp_plug_name: tuple containing (the name of the node, the
           name of the plug) to export
        :param multi_export: True if this method is called in export plugs case
        """
        # TODO: Bug: the first parameter (here pipeline_parameter) cannot be
        #            None even if we write pipeline_parameter=None in the
        #            line above, it will be False...

        if temp_plug_name is None:
            temp_plug_name = self._temp_plug_name

        if not pipeline_parameter:
            dial = self._PlugEdit()
            dial.name_line.setText(temp_plug_name[1])
            dial.optional.setChecked(self._temp_plug.optional)
            res = dial.exec_()

        else:
            res = True

        if res:
            allow_existing_plug = False
            check_plug = True

            if not pipeline_parameter:
                plug_name = str(dial.name_line.text())

            else:
                plug_name = pipeline_parameter

            while check_plug is True:

                if plug_name in self.scene.pipeline.pipeline_node.plugs:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    title = "populse_mia - Warning: Duplicate pipeline plug"
                    msgtext = (
                        f"The '{plug_name}' pipeline plug already exists, do "
                        f"you want to connect to this existing plug ?"
                    )
                    reply = msg.question(
                        self, title, msgtext, QMessageBox.Yes | QMessageBox.No
                    )

                    if reply == QMessageBox.Yes:
                        allow_existing_plug = True
                        check_plug = False

                    elif reply == QMessageBox.No:
                        new_name, ok = QInputDialog.getText(
                            self,
                            "Plug name Input Dialog",
                            f"The plug {plug_name} already exists, "
                            f"please choose a new name.",
                        )

                        if (
                            ok
                            and new_name
                            and not new_name.isspace()
                            and plug_name != new_name
                        ):
                            plug_name = new_name

                            if (
                                plug_name
                                not in self.scene.pipeline.pipeline_node.plugs
                            ):
                                check_plug = False

                else:
                    allow_existing_plug = False
                    check_plug = False

            pipeline_parameter = plug_name

            if optional is None:

                try:
                    optional = dial.optional.isChecked()

                except UnboundLocalError:
                    pass

            if weak_link is None:

                try:
                    weak_link = dial.weak.isChecked()

                except UnboundLocalError:
                    weak_link = False

            try:
                self.scene.pipeline.export_parameter(
                    temp_plug_name[0],
                    temp_plug_name[1],
                    pipeline_parameter,
                    weak_link=weak_link,
                    is_optional=optional,
                    allow_existing_plug=allow_existing_plug,
                )

            except TraitError:
                logger.warning(
                    f"Cannot export {temp_plug_name[0]}.{plug_name} plug."
                )

                if multi_export:
                    return None

            except ValueError as e:
                logger.warning(f"\n{e}")

                if multi_export:
                    return None

            else:

                # For history
                if multi_export:
                    return temp_plug_name[1]

                else:
                    self.scene.update_pipeline()
                    history_maker = [
                        "export_plugs",
                        plug_name,
                        temp_plug_name[0],
                    ]
                    self.update_history(history_maker, from_undo, from_redo)
                    self.main_window.statusBar().showMessage(
                        f"Plug {plug_name} has been exported."
                    )

    def _release_grab_link(self, event, ret=False):
        """Method called when a link is released.

        :param event: mouse event corresponding to the release
        :param ret: boolean that is set to True in the original method to
           return the link
        """
        # Calling the original method
        link = PipelineDeveloperView._release_grab_link(self, event, ret=True)
        # For history
        history_maker = ["add_link", link]
        self.update_history(history_maker, from_undo=False, from_redo=False)
        self.main_window.statusBar().showMessage(
            f"Link {link} has been added."
        )

    def _remove_plug(
        self,
        _temp_plug_name=None,
        from_undo=False,
        from_redo=False,
        from_export_plugs=False,
    ):
        """Remove a plug

        :param _temp_plug_name: tuple containing (the name of the node,
           the name of the plug) to remove
        :param from_undo: True if this method is called from an undo action
        :param from_redo: True if this method is called from a redo action
        :param from_export_plugs: True if this method is called from a
           "from_export_plugs" undo or redo action
        """
        tot_plug_name = []

        if not _temp_plug_name:
            _temp_plug_name = self._temp_plug_name

        if isinstance(_temp_plug_name, tuple):
            _temp_plug_name = [_temp_plug_name]

        for pip_plug_name in _temp_plug_name:

            if pip_plug_name[0] in ("inputs", "outputs"):
                plug_name = pip_plug_name[1]
                plug = self.scene.pipeline.pipeline_node.plugs[plug_name]
                optional = plug.optional
                # contains the plugs that are connected
                # to the input or output plug
                new_temp_plugs = []

                for link in plug.links_to:
                    temp_plug = (link[0], link[1])
                    new_temp_plugs.append(temp_plug)

                for link in plug.links_from:
                    temp_plug = (link[0], link[1])
                    new_temp_plugs.append(temp_plug)

                # To avoid the "_items" bug: setting the has_items attribute
                # of the trait's handler to False
                node = self.scene.pipeline.nodes[""]
                source_trait = node.get_trait(plug_name)

                if source_trait.handler.has_items:
                    source_trait.handler.has_items = False

                self.scene.pipeline.remove_trait(pip_plug_name[1])
                self.scene.update_pipeline()
                tot_plug_name.append([pip_plug_name, new_temp_plugs, optional])

        # if not from_undo and not from_redo:
        if not from_export_plugs and tot_plug_name:
            # For history
            history_maker = ["remove_plug", tot_plug_name]
            self.update_history(history_maker, from_undo, from_redo)

            if len(tot_plug_name) == 1:
                self.main_window.statusBar().showMessage(
                    f"'{tot_plug_name[0][0][1]}' plug has been removed."
                )

            else:
                self.main_window.statusBar().showMessage(
                    f"{tuple(i[0][1] for i in tot_plug_name)} plugs "
                    f"has been removed."
                )

    def add_link(
        self,
        source,
        dest,
        active,
        weak,
        from_undo=False,
        from_redo=False,
        allow_export=False,
    ):
        """Add a link between two nodes.

        :param source: tuple containing the node and plug source names
        :param dest: tuple containing the node and plug destination names
        :param active: boolean that is True if the link is activated
        :param weak: boolean that is True if the link is weak
        :param from_undo: boolean that is True if the action has been made
           using an undo
        :param from_redo: boolean that is True if the action has been made
           using a redo
        """
        # Writing a string to represent the link
        source_parameters = ".".join(source)
        dest_parameters = ".".join(dest)
        link = "->".join((source_parameters, dest_parameters))
        self.scene.pipeline.add_link(link, allow_export=allow_export)
        self.scene.update_pipeline()
        # For history
        history_maker = ["add_link", link]
        self.update_history(history_maker, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Link {link} has been added."
        )

    def add_named_process(
        self,
        class_process,
        node_name=None,
        from_undo=False,
        from_redo=False,
        links=[],
    ):
        """Add a process to the pipeline.

        :param class_process: process class's name (str)
        :param node_name: name of the corresponding node (using when
          undo/redo) (str)
        :param from_undo: boolean that is True if the action has been made
          using an undo
        :param from_redo: boolean that is True if the action has been made
          using a redo
        :param links: list of links (using when undo/redo)
        """
        process = super().add_named_process(class_process, node_name)

        if node_name is None:
            node_name = getattr(process, "context_name", process.name).split(
                "."
            )[-1]

        if hasattr(process, "use_project") and process.use_project:
            process.project = self.project

        if hasattr(process, "_spm_script_file"):
            process.trait("_spm_script_file").userlevel = 1

        if hasattr(process, "process") and hasattr(
            process.process, "_spm_script_file"
        ):
            process.process.trait("_spm_script_file").userlevel = 1

        # If the process is added from a undo, all the links
        # that were connected to the corresponding node has to be reset
        for link in links:
            source = link[0]
            dest = link[1]
            active = link[2]
            weak = link[3]
            self.scene.add_link(source, dest, active, weak)
            # Writing a string to represent the link
            source_parameters = ".".join(source)
            dest_parameters = ".".join(dest)
            link_to_add = "->".join((source_parameters, dest_parameters))
            self.scene.pipeline.add_link(link_to_add)
            self.scene.update_pipeline()

        # For history
        history_maker = ["add_process"]

        if from_undo:
            # Adding the arguments to make the redo correctly
            history_maker.append(node_name)

        else:
            # Adding the arguments to make the undo correctly
            history_maker.append(node_name)
            history_maker.append(class_process)

        self.update_history(history_maker, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Node {node_name} has been added."
        )
        self.main_window.pipeline_manager.update_user_buttons_states()

    def check_modifications(self):
        """Check if the nodes of the pipeline have been modified."""
        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        pipeline = self.scene.pipeline
        config = Config()
        # List to store the removed links
        removed_links = []

        for node_name, node in pipeline.nodes.items():
            # Only if the node is a pipeline node ?

            if node_name and isinstance(node, PipelineNode):
                sub_pipeline_process = node.process

                # Reading the process configuration file
                with open(
                    os.path.join(
                        config.get_properties_path(),
                        "properties",
                        "process_config.yml",
                    ),
                ) as stream:

                    try:

                        if verCmp(yaml.__version__, "5.1", "sup"):
                            dic = yaml.load(stream, Loader=yaml.FullLoader)

                        else:
                            dic = yaml.load(stream)

                    except yaml.YAMLError as exc:
                        logger.warning(exc)
                        dic = {}

                sub_pipeline_name = sub_pipeline_process.name
                # Finding from where comes from the pipeline
                pckg = sub_pipeline_process.__module__.split(".", 1)[0]

                if pckg == "mia_processes":
                    paths_list = [
                        os.path.dirname(
                            sys.modules["mia_processes"].__path__[0]
                        )
                    ]

                else:
                    paths_list = dic["Paths"]

                # get_path returns a list that is the package path
                # to the sub_pipeline file
                sub_pipeline_list = get_path(
                    sub_pipeline_name, dic["Packages"], None, pckg
                )
                sub_pipeline_name = sub_pipeline_list.pop()
                # Finding the real sub-pipeline filename
                sub_pipeline_filename = find_filename(
                    paths_list, sub_pipeline_list, sub_pipeline_name
                )
                saved_process = get_process_instance(sub_pipeline_filename)
                current_inputs = list(sub_pipeline_process.get_inputs().keys())
                current_outputs = list(
                    sub_pipeline_process.get_outputs().keys()
                )
                saved_inputs = list(saved_process.get_inputs().keys())
                saved_outputs = list(saved_process.get_outputs().keys())
                new_inputs = [
                    item for item in saved_inputs if item not in current_inputs
                ]
                new_outputs = [
                    item
                    for item in saved_outputs
                    if item not in current_outputs
                ]
                removed_inputs = [
                    item for item in current_inputs if item not in saved_inputs
                ]
                removed_outputs = [
                    item
                    for item in current_outputs
                    if item not in saved_outputs
                ]

                if (
                    new_inputs
                    or new_outputs
                    or removed_inputs
                    or removed_outputs
                ):
                    # Checking the links of the node
                    link_to_del = set()

                    for link, glink in self.scene.glinks.items():

                        if link[0][0] == node_name or link[1][0] == node_name:
                            self.scene.removeItem(glink)
                            link_to_del.add((link, glink))

                    for link, glink in link_to_del:
                        del self.scene.glinks[link]

                    # Creating a new node
                    new_node = saved_process.pipeline_node
                    new_node.name = node_name
                    new_node.pipeline = pipeline
                    saved_process.parent_pipeline = weak_proxy(pipeline)
                    pipeline.nodes[node_name] = new_node
                    # Creating a new graphical node
                    gnode = NodeGWidget(
                        node_name,
                        new_node.plugs,
                        pipeline,
                        sub_pipeline=saved_process,
                        process=saved_process,
                        colored_parameters=self.scene.colored_parameters,
                        logical_view=self.scene.logical_view,
                        labels=self.scene.labels,
                    )
                    # Setting the new node to the same position as the
                    # previous one
                    pos = self.scene.pos.get(node_name)
                    gnode.setPos(pos)
                    # Removing the old node
                    self.scene.removeItem(self.scene.gnodes[node_name])
                    del self.scene.gnodes[node_name]
                    # Adding the new node to the scene
                    self.scene.gnodes[node_name] = gnode
                    self.scene.addItem(gnode)

                    for link, glink in link_to_del:
                        source = link[0]
                        dest = link[1]

                        if source[0] == "inputs":
                            link_plug = source[1]
                            source = ("", link_plug)

                        if dest[0] == "outputs":
                            link_plug = dest[1]
                            dest = ("", link_plug)

                        # Writing a string to represent the link
                        source_parameters = ".".join(source)
                        dest_parameters = ".".join(dest)
                        pipeline_link = "->".join(
                            (source_parameters, dest_parameters)
                        )

                        # Checking if a connected plug has been deleting
                        if dest[0] == node_name and dest[1] in removed_inputs:
                            removed_links.append(pipeline_link)
                            continue

                        if (
                            source[0] == node_name
                            and source[1] in removed_outputs
                        ):
                            removed_links.append(pipeline_link)
                            continue

                        # Adding the link
                        self.scene.pipeline.add_link(pipeline_link)
                        self.scene.add_link(source, dest, True, False)

                    self.scene.update_pipeline()

        if removed_links:
            dialog_text = (
                f"Pipeline {node_name} has been updated.\nRemoved links:"
            )

            for removed_link in removed_links:
                dialog_text += f"\n{removed_link}"

            pop_up = QtWidgets.QMessageBox()
            pop_up.setIcon(QtWidgets.QMessageBox.Warning)
            pop_up.setText(dialog_text)
            pop_up.setWindowTitle("Warning: links have been removed")
            pop_up.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )
            pop_up.exec_()

    def del_node(self, node_name=None, from_undo=False, from_redo=False):
        """Delete a node.

        :param node_name: name of the corresponding node (using when undo/redo)
        :param from_undo: boolean, True if the action has been made using an
           undo
        :param from_redo: boolean, True if the action has been made using a
           redo
        """
        pipeline = self.scene.pipeline

        if not node_name:
            node_name = self.current_node_name

        invert_io = False

        if node_name in ("inputs", "outputs"):
            node = pipeline.pipeline_node
            invert_io = True

        else:
            node = pipeline.nodes[node_name]

        # Collecting the links from the node that is being deleted
        links = []

        for plug_name, plug in node.plugs.items():

            if plug.output or (invert_io and not plug.output):

                for link_to in plug.links_to:
                    (
                        dest_node_name,
                        dest_parameter,
                        dest_node,
                        dest_plug,
                        weak_link,
                    ) = link_to
                    active = plug.activated
                    # Looking for the name of dest_plug in dest_node
                    dest_plug_name = None

                    for plug_name_d, plug_d in dest_node.plugs.items():

                        if plug_d == dest_plug:
                            dest_plug_name = plug_name_d
                            break

                    link_to_add = [(node_name, plug_name)]
                    link_to_add.append((dest_node_name, dest_plug_name))
                    link_to_add.append(active)
                    link_to_add.append(weak_link)
                    links.append(link_to_add)

            else:

                for link_from in plug.links_from:
                    (
                        source_node_name,
                        source_parameter,
                        source_node,
                        source_plug,
                        weak_link,
                    ) = link_from
                    active = plug.activated
                    # Looking for the name of source_plug in source_node
                    source_plug_name = None

                    for plug_name_d, plug_d in source_node.plugs.items():

                        if plug_d == source_plug:
                            source_plug_name = plug_name_d
                            break

                    link_to_add = [(source_node_name, source_plug_name)]
                    link_to_add.append((node_name, plug_name))
                    link_to_add.append(active)
                    link_to_add.append(weak_link)
                    links.append(link_to_add)

        # Calling the original method
        super().del_node(node_name)
        # For history
        process = node

        if isinstance(process, ProcessNode):
            process = node.process

        history_maker = ["delete_process", node_name, process, links]
        self.update_history(history_maker, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Node {node_name} has been deleted."
        )

        for node_name, node in pipeline.nodes.items():
            process = node

            if isinstance(process, ProcessNode):
                process = node.process

            if node_name != "":
                self.main_window.pipeline_manager.displayNodeParameters(
                    node_name, process
                )

        self.main_window.pipeline_manager.update_user_buttons_states()

    def export_node_plugs(
        self,
        node_name,
        inputs=True,
        outputs=True,
        optional=False,
        from_undo=False,
        from_redo=False,
    ):
        """Export all the plugs of a node

        :param node_name: node name
        :param inputs: True if the inputs have to be exported
        :param outputs: True if the outputs have to be exported
        :param optional: True if the optional plugs have to be exported
        :param from_undo: True if this method is called from an undo action
        :param from_redo: True if this method is called from a redo action
        """
        pipeline = self.scene.pipeline
        node = pipeline.nodes[node_name]
        parameter_list = []

        for parameter_name, plug in node.plugs.items():

            if parameter_name in (
                "nodes_activation",
                "selection_changed",
                "output_directory",
                "use_mcr",
                "paths",
                "matlab_cmd",
                "mfile",
                "spm_script_file",
            ):
                continue

            if (
                (node_name, parameter_name) not in pipeline.do_not_export
                and (
                    (outputs and plug.output and not plug.links_to)
                    or (inputs and not plug.output and not plug.links_from)
                )
                and (optional or not node.get_trait(parameter_name).optional)
            ):
                p_name = self._export_plug(
                    parameter_name,
                    temp_plug_name=(node_name, parameter_name),
                    multi_export=True,
                )
                parameter_list.append(p_name)

        parameter_list = list(filter(None, parameter_list))
        self.scene.update_pipeline()
        # For history
        history_maker = ["export_plugs", parameter_list, node_name]
        self.update_history(history_maker, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Plugs {str(parameter_list)} have been exported."
        )

    def get_current_filename(self):
        """Return the relative path the pipeline was last saved to.
        Empty if never saved.

        :return: the current pipeline file name
        """

        if hasattr(self, "_pipeline_filename") and self._pipeline_filename:
            return os.path.relpath(self._pipeline_filename)

        else:
            return ""

    def save_pipeline(self, filename=None):
        """Save the pipeline.

        :return: the name of the file where the pipeline was saved
        """
        self.check_modifications()

        if len(self.scene.pipeline.nodes) < 2:
            logger.info(
                "\nThe pipeline hasn't been saved because it is empty ..."
            )
            return None

        config = Config()

        if (
            not filename
            or os.path.join("mia_processes", "mia_processes") in filename
        ):
            pipeline = self.scene.pipeline
            folder = os.path.join(
                config.get_properties_path(), "processes", "User_processes"
            )

            if not os.path.isdir(folder):
                os.mkdir(folder)

            if not os.path.isfile(os.path.join(folder, "__init__.py")):
                with open(os.path.join(folder, "__init__.py"), "w"):
                    pass

            filename = QtWidgets.QFileDialog.getSaveFileName(
                None,
                "Save the pipeline",
                folder,
                "Compatible files (*.py);; All (*)",
            )[0]

            if not filename:  # save widget was cancelled by the user
                return None

            if os.path.basename(filename)[0].isdigit():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("populse_mia - Save pipeline as Warning!")
                msg.setText(
                    "Python does not allow to use a module name "
                    "starting with a number ...!"
                    "please change the name of your pipeline!"
                )
                msg.setStandardButtons(QMessageBox.Close)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                return None

            filename_temp = os.path.split(filename)
            filename = os.path.join(
                filename_temp[0], filename_temp[-1].lower()
            )

            if os.path.splitext(filename)[1] == "":  # which means no extension
                filename += ".py"

            elif os.path.splitext(filename)[1] != ".py":
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText(
                    f"The pipeline will be saved with a '.py' extension "
                    f"instead of {os.path.splitext(filename)[1]}!"
                )
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                filename = f"{os.path.splitext(filename)[0]}.py"

            if os.path.exists(filename) and config.get_user_mode():
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText(
                    "This file already exists, you do not have the "
                    "rights to overwrite it."
                )
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                return None

        if filename:
            posdict = {
                key: (value.x(), value.y())
                for key, value in self.scene.pos.items()
            }
            dimdict = {
                key: (value[0], value[1])
                for key, value in self.scene.dim.items()
            }
            pipeline.node_dimension = dimdict
            old_pos = pipeline.node_position
            pipeline.node_position = posdict
            save_pipeline(pipeline, filename)
            self._pipeline_filename = str(filename)
            pipeline.node_position = old_pos
            self.pipeline_saved.emit(filename)
            return filename

    def update_history(self, history_maker, from_undo, from_redo):
        """Update the history for undos and redos.
        This method is called after each action in the PipelineEditor.

        :param history_maker: list that contains information about what has
            been done
        :param from_undo: boolean that is True if the action has been made
            using an undo
        :param from_redo: boolean that is True if the action has been made
            using a redo
        """

        if from_undo:
            self.redos.append(history_maker)

        else:
            self.undos.append(history_maker)

            # If the action does not comes from an undo or a redo,
            # redos must be updated with care
            if not from_redo:
                to_redo = None

                if history_maker[0] == "add_process":
                    to_redo = "delete_process"

                elif history_maker[0] == "delete_process":
                    to_redo = "add_process"

                elif history_maker[0] == "update_node_name":
                    self.undos.pop()

                for i, item in enumerate(self.redos):
                    if item[0] == to_redo and history_maker[1] == item[1]:
                        self.redos.pop(i)

        self.pipeline_modified.emit(self)

    def update_node_name(
        self,
        old_node,
        old_node_name,
        new_node_name,
        from_undo=False,
        from_redo=False,
    ):
        """Update a node name.

        :param old_node: Node object to change
        :param old_node_name: original name of the node (str)
        :param new_node_name: new name of the node (str)
        :param from_undo: boolean, True if the action has been made using an
           undo
        :param from_redo: boolean, True if the action has been made using a
           redo
        """
        pipeline = self.scene.pipeline
        # Removing links of the selected node and copy the origin/destination
        links_to_copy = []

        for source_parameter, source_plug in old_node.plugs.items():

            for (
                dest_node_name,
                dest_parameter,
                dest_node,
                dest_plug,
                weak_link,
            ) in source_plug.links_to.copy():
                pipeline.remove_link(
                    f"{old_node_name}.{source_parameter}->"
                    f"{dest_node_name}.{dest_parameter}"
                )
                links_to_copy.append(
                    ("to", source_parameter, dest_node_name, dest_parameter)
                )

            for (
                dest_node_name,
                dest_parameter,
                dest_node,
                dest_plug,
                weak_link,
            ) in source_plug.links_from.copy():
                pipeline.remove_link(
                    f"{dest_node_name}.{dest_parameter}->"
                    f"{old_node_name}.{source_parameter}"
                )
                links_to_copy.append(
                    ("from", source_parameter, dest_node_name, dest_parameter)
                )

        # Creating a new node with the new name and deleting the previous one
        pipeline.nodes[new_node_name] = pipeline.nodes[old_node_name]
        del pipeline.nodes[old_node_name]

        # Setting the same links as the original node
        for link in links_to_copy:

            if link[0] == "to":
                pipeline.add_link(
                    f"{new_node_name}.{link[1]}->{link[2]}.{link[3]}"
                )

            elif link[0] == "from":
                pipeline.add_link(
                    f"{link[2]}.{link[3]}->{new_node_name}.{link[1]}"
                )

        # Updating the pipeline
        pipeline.update_nodes_and_plugs_activation()
        # For history
        history_maker = [
            "update_node_name",
            pipeline.nodes[new_node_name],
            new_node_name,
            old_node_name,
        ]
        self.update_history(history_maker, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Node name '{old_node_name}' has been "
            f"changed to '{new_node_name}'."
        )

    def update_plug_value(
        self,
        node_name,
        new_value,
        plug_name,
        value_type,
        from_undo=False,
        from_redo=False,
    ):
        """Update a plug value.

        :param node_name: name of the node (str)
        :param new_value: new value to set to the plug
        :param plug_name: name of the plug to change (str)
        :param value_type: type of the new value
        :param from_undo: boolean, True if the action has been made using an
                          undo
        :param from_redo: boolean, True if the action has been made using a
                          redo
        """
        old_value = self.scene.pipeline.nodes[node_name].get_plug_value(
            plug_name
        )

        if from_undo or from_redo:
            self.scene.pipeline.nodes[node_name].set_plug_value(
                plug_name, new_value
            )

        else:
            self.scene.pipeline.nodes[node_name].set_plug_value(
                plug_name, value_type(new_value)
            )

        if from_undo or from_redo:
            self.undos.pop()

        # For history
        history_maker = [
            "update_plug_value",
            node_name,
            old_value,
            plug_name,
            value_type,
        ]
        self.update_history(history_maker, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Plug '{plug_name}' of node '{node_name}' has been "
            f"changed to '{new_value}'."
        )


class PipelineEditorTabs(QtWidgets.QTabWidget):
    """
    Tab widget that contains pipeline editors.

    .. Methods:
        - check_modifications: check if the nodes of the current pipeline have
          been modified
        - close_tab: close the selected tab and editor
        - emit_node_clicked: emit a signal when a node is clicked
        - emit_pipeline_saved: emit a signal when a pipeline is saved
        - emit_switch_clicked: emit a signal when a switch is clicked
        - export_to_db_scans: export the input of a filter to 'database_scans'
        - get_current_editor: get the instance of the current editor
        - get_current_filename: get the file name of the current pipeline
        - get_current_pipeline: get the instance of the current pipeline
        - get_current_tab_name: get the tab title of the current editor
        - get_filename_by_index: get the pipeline filename from its index in
          the editors
        - get_index_by_filename: get the index of the editor corresponding to
          the given pipeline filename
        - get_index_by_tab_name: get the index of the editor corresponding to
          the given tab name
        - get_tab_name_by_index: get the tab title from its index in the
          editors
        - has_pipeline_nodes: check if any of the pipelines in the editor tabs
          have pipeline nodes
        - load_pipeline: load a new pipeline
        - load_pipeline_parameters: load parameters to the pipeline of the
          current editor
        - new_tab: create a new tab and a new editor
        - open_filter: open a filter widget
        - open_sub_pipeline: open a sub-pipeline in a new tab
        - reset_pipeline: reset the pipeline of the current editor
        - save_pipeline: save the pipeline of the current editor
        - save_pipeline_parameters: save the pipeline parameters of the
          current editor
        - set_current_editor_by_tab_name: set the current editor
        - set_tab_index: set the current tab index and disable the run
          pipeline action
        - update_current_node: update node parameter
        - update_history: update undo/redo history of an editor
        - update_pipeline_editors: update editors
        - update_scans_list: update the list of database scans in every editor
    """

    pipeline_saved = QtCore.pyqtSignal(str)
    node_clicked = QtCore.pyqtSignal(str, Node)
    process_clicked = QtCore.pyqtSignal(str, Process)
    switch_clicked = QtCore.pyqtSignal(str, Switch)

    def __init__(self, project, scan_list, main_window):
        """Initialization of the Pipeline Editor tabs.

        :param project: current project in the software
        :param scan_list: list of the selected database files
        :param main_window: main window of the software
        """
        super().__init__()
        self.project = project
        self.main_window = main_window
        self.setStyleSheet(
            "QTabBar{font-size:12pt;font-family:Arial;"
            "text-align: center;color:black;}"
        )
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.scan_list = scan_list
        self.undos = {}
        self.redos = {}
        p_e = PipelineEditor(self.project, self.main_window)
        p_e.node_clicked.connect(self.emit_node_clicked)
        p_e.process_clicked.connect(self.emit_node_clicked)
        p_e.switch_clicked.connect(self.emit_switch_clicked)
        p_e.pipeline_saved.connect(self.emit_pipeline_saved)
        p_e.pipeline_modified.connect(self.update_pipeline_editors)
        p_e.edit_sub_pipeline.connect(self.open_sub_pipeline)
        p_e.open_filter.connect(self.open_filter)
        p_e.export_to_db_scans.connect(self.export_to_db_scans)
        p_e.initialized = False
        p_e.iterated = False
        p_e.iterated_tag = None
        p_e.tag_values_list = []
        p_e.all_tag_values_list = []
        p_e.all_tag_values_list = []
        p_e.node_parameters = {}
        p_e.node_parameters_tmp = {}
        # Setting a default editor called "New Pipeline"
        self.addTab(p_e, "New Pipeline")
        self.undos[p_e] = []
        self.redos[p_e] = []
        # Tool button to add a tab
        tb = QtWidgets.QToolButton()
        tb.setText("+")
        tb.clicked.connect(self.new_tab)
        self.addTab(QtWidgets.QLabel('Add tabs by pressing "+"'), "")
        self.setTabEnabled(1, False)
        self.tabBar().setTabButton(1, QtWidgets.QTabBar.RightSide, tb)
        # Checking if the pipeline nodes have been modified
        self.tabBarClicked.connect(self.check_modifications)
        self.currentChanged.connect(self.update_current_node)
        self.previousIndex = 0
        # init capsul engine config
        self.get_capsul_engine()

    def check_modifications(self, current_index):
        """Check if the nodes of the current pipeline have been modified.

        :param current_index: index to check
        """
        # If the user click on the last tab (with the '+'),
        # it will throw an AttributeError

        try:

            if current_index != self.previousIndex:
                self.previousIndex = current_index

            self.widget(current_index).check_modifications()

        except AttributeError:
            pass

    def close_tab(self, idx):
        """Close the selected tab and editor.

        :param idx: index of the tab to close
        """
        filename = os.path.basename(self.get_filename_by_index(idx))
        editor = self.get_editor_by_index(idx)

        # If the pipeline has been modified and not saved
        if self.tabText(idx)[-2:] == " *":
            self.pop_up_close = PopUpClosePipeline(filename)
            self.pop_up_close.save_as_signal.connect(self.save_pipeline)
            self.pop_up_close.exec()
            can_exit = self.pop_up_close.can_exit()

            if self.pop_up_close.bool_save_as:

                if idx == self.currentIndex():
                    self.set_tab_index(max(0, self.currentIndex() - 1))

                self.removeTab(idx)
                return

        else:
            can_exit = True

        if not can_exit:
            return

        del self.undos[editor]
        del self.redos[editor]

        if idx == self.currentIndex():
            self.set_tab_index(max(0, self.currentIndex() - 1))

        self.removeTab(idx)

        # If there is no more editor, adding one
        if self.count() == 1:
            p_e = PipelineEditor(self.project, self.main_window)
            p_e.node_clicked.connect(self.emit_node_clicked)
            p_e.process_clicked.connect(self.emit_node_clicked)
            p_e.switch_clicked.connect(self.emit_switch_clicked)
            p_e.pipeline_saved.connect(self.emit_pipeline_saved)
            p_e.pipeline_modified.connect(self.update_pipeline_editors)
            p_e.edit_sub_pipeline.connect(self.open_sub_pipeline)
            p_e.open_filter.connect(self.open_filter)
            p_e.export_to_db_scans.connect(self.export_to_db_scans)
            p_e.initialized = False
            p_e.iterated = False
            p_e.iterated_tag = None
            p_e.tag_values_list = []
            p_e.all_tag_values_list = []
            p_e.node_parameters = {}
            p_e.node_parameters_tmp = {}
            # Setting a default editor called "New Pipeline"
            self.insertTab(0, p_e, "New Pipeline")
            self.set_tab_index(0)
            self.undos[p_e] = []
            self.redos[p_e] = []
            self.get_capsul_engine()

        for node_name, node in self.get_current_pipeline().nodes.items():
            process = getattr(node, "process", node)
            self.main_window.pipeline_manager.displayNodeParameters(
                node_name, process
            )

        self.update_iteration_checkbox()

    def emit_node_clicked(self, node_name, process):
        """Emit a signal when a node is clicked.

        :param node_name: node name
        :param process: process of the corresponding node
        """

        if isinstance(process, Process):
            self.process_clicked.emit(node_name, process)

        else:
            self.node_clicked.emit(node_name, process)

    def emit_pipeline_saved(self, filename):
        """Emit a signal when a pipeline is saved.

        :param filename: file name of the pipeline
        """
        self.setTabText(self.currentIndex(), os.path.basename(filename))
        self.pipeline_saved.emit(filename)

    def emit_switch_clicked(self, node_name, switch):
        """Emit a signal when a switch is clicked.

        :param node_name: node name
        :param switch: process of the corresponding node
        """
        self.switch_clicked.emit(node_name, switch)

    def export_to_db_scans(self, node_name):
        """Export the input of a filter to "database_scans" plug.

        :param node_name: the name of the node from which to export
        """

        # If database_scans is already a pipeline global input, the plug
        # cannot be exported. A link as to be added between database_scans
        # and the input of the filter.
        if (
            "database_scans"
            in self.get_current_pipeline().user_traits().keys()
        ):
            self.get_current_pipeline().add_link(
                f"database_scans->{node_name}.input"
            )

        else:
            self.get_current_pipeline().export_parameter(
                node_name, "input", pipeline_parameter="database_scans"
            )

        self.get_current_editor().scene.update_pipeline()

    def get_capsul_engine(self):
        """
        Get a CapsulEngine object from the edited pipeline, and set it up from
        MIA config object
        """
        # save completion attributes for the current pipeline (other pipelines
        # will lose their values)
        pipeline = self.get_current_pipeline()
        completion = getattr(pipeline, "completion_engine", None)

        if completion:
            att_values = completion.get_attribute_values().export_to_dict()

        engine = Config.get_capsul_engine()
        study_config = engine.study_config
        study_config.input_directory = os.path.join(
            os.path.abspath(self.project.folder), "data", "raw_data"
        )
        study_config.output_directory = os.path.join(
            os.path.abspath(self.project.folder), "data", "derived_data"
        )

        # restore completion attributes
        from capsul.attributes.completion_engine import ProcessCompletionEngine

        if completion:
            completion = ProcessCompletionEngine.get_completion_engine(
                pipeline
            )

            if completion:
                completion.get_attribute_values().import_from_dict(att_values)

        return engine

    def get_current_editor(self):
        """Get the instance of the current editor.

        :return: the current editor
        """
        return self.get_editor_by_index(self.currentIndex())

    def get_current_filename(self):
        """Get the relative path to the file the pipeline in the current editor
        has been last saved to.
        If the pipeline has never been saved, returns the title of the tab.

        :return: the filename of the current editor
        """
        return self.get_filename_by_index(self.currentIndex())

    def get_current_pipeline(self):
        """Get the instance of the current pipeline.

        :return: the pipeline of the current editor
        """
        editor = self.get_current_editor()

        if editor is None or editor.scene is None:
            return None

        return editor.scene.pipeline

    def get_current_tab_name(self):
        """Get the tab name of the editor in the current tab.

        Trailing "*" and ampersand ("&") characters are removed.

        :return: the current tab name
        """
        return self.get_tab_name_by_index(self.currentIndex())

    def get_editor_by_file_name(self, file_name):
        """Get the instance of an editor from its file name.

        :param file_name: name of the file the pipeline was last saved to
        :return: the editor corresponding to the file name
        """
        return self.get_editor_by_index(self.get_index_by_filename(file_name))

    def get_editor_by_index(self, idx):
        """Get the instance of an editor from its index in the editors.

        :param idx: index of the editor
        :return: the editor corresponding to the index
        """

        # last tab has "add tab" button, no editor
        if idx in range(self.count() - 1):
            return self.widget(idx)

    def get_editor_by_tab_name(self, tab_name):
        """Get the instance of an editor from its tab name.

        :param tab_name: name of the tab
        :return: the editor corresponding to the tab name
        """
        return self.get_editor_by_index(self.get_index_by_tab_name(tab_name))

    def get_filename_by_index(self, idx):
        """Get the relative path to the file the pipeline in the editor at the
        given index has been last saved to.
        If the pipeline has never been saved, returns the title of the tab.

        :param idx: index of the editor
        :return: the file name corresponding to the index
        """
        editor = self.get_editor_by_index(idx)

        if editor is not None:
            return editor.get_current_filename()

    def get_index_by_editor(self, editor):
        """Get the index of the editor corresponding to the given editor.

        :param editor: searched pipeline editor
        :return: the index corresponding to the editor
        """

        for idx in range(self.count() - 1):

            if self.get_editor_by_index(idx) == editor:
                return idx

    def get_index_by_filename(self, filename):
        """Get the index of the first editor corresponding to the given
        pipeline filename.

        :param filename: filename of the searched pipeline
        :return: the index corresponding to the file name
        """

        if filename:
            # we always store file names as relative paths
            filename = os.path.relpath(filename)

            for idx in range(self.count() - 1):

                if self.get_filename_by_index(idx) == filename:
                    return idx

    def get_index_by_tab_name(self, tab_name):
        """Get the index of the editor corresponding to the given tab name.

        :param tab_name: name of the tab with the searched pipeline
        :return: the index corresponding to the tab name
        """

        for idx in range(self.count() - 1):

            if self.get_tab_name_by_index(idx) == tab_name:
                return idx

    def get_tab_name_by_index(self, idx):
        """Get the tab name of the editor at the given index.

        Trailing "*" and ampersand ("&") characters are removed.

        :param idx: index of the editor
        :return: the tab name corresponding to the index
        """

        # last tab has "add tab" button, no tab name
        if idx in range(self.count() - 1):
            # remove Qt keyboard shortcut indicator
            tab_name = self.tabText(idx).replace("&", "", 1)

            if tab_name[-2:] == " *":
                tab_name = tab_name[:-2]

            return tab_name

    def has_pipeline_nodes(self):
        """Check if any of the pipelines in the editor tabs have pipeline
        nodes.

        :return: True or False depending on if there are nodes in the editors
        """

        for idx in range(self.count()):
            p_e = self.widget(idx)

            if hasattr(p_e, "scene"):

                # if the widget is a tab editor
                if p_e.scene.pipeline.nodes[""].plugs:
                    return True

        return False

    def load_pipeline(self, filename=None):
        """Load a new pipeline.

        :param filename: not None only when this method is called from
          "open_sub_pipeline"
        """
        current_tab_not_empty = (
            len(self.get_current_editor().scene.pipeline.nodes.keys()) > 1
        )
        new_tab_opened = False

        if filename is None:

            # Open new tab if the current PipelineEditor is not empty
            if current_tab_not_empty:
                # create new tab with new editor and make it current
                self.new_tab()
                working_index = self.currentIndex()
                new_tab_opened = True

            # get only the file name to load
            filename = self.get_current_editor().load_pipeline("", False)
            self.get_capsul_engine()

        if filename:
            # Check if this pipeline is already open
            existing_pipeline_tab = self.get_index_by_filename(filename)

            if existing_pipeline_tab is not None:
                self.set_tab_index(existing_pipeline_tab)

            else:

                # we need to actually load the pipeline
                if current_tab_not_empty and not new_tab_opened:
                    self.new_tab()
                    new_tab_opened = True

                working_index = self.currentIndex()
                editor = self.get_editor_by_index(working_index)
                # actually load the pipeline
                filename = editor.load_pipeline(filename)
                self.get_capsul_engine()

                if filename:
                    self.setTabText(working_index, os.path.basename(filename))
                    self.update_scans_list()
                    # fmt: off
                    (
                        self.main_window.pipeline_manager
                        .run_pipeline_action.setDisabled(False)
                    )
                    # fmt: on
                    return  # success

        # if we're still here, something went wrong. clean up.
        if new_tab_opened:
            self.close_tab(working_index)

    def load_pipeline_parameters(self):
        """Load parameters to the pipeline of the current editor"""
        self.get_current_editor().load_pipeline_parameters(
            os.path.expanduser("~")
        )

    def new_tab(self):
        """Create a new tab and a new editor and makes the new tab current."""
        # Creating a new editor
        p_e = PipelineEditor(self.project, self.main_window)
        p_e.node_clicked.connect(self.emit_node_clicked)
        p_e.process_clicked.connect(self.emit_node_clicked)
        p_e.switch_clicked.connect(self.emit_switch_clicked)
        p_e.pipeline_saved.connect(self.emit_pipeline_saved)
        p_e.pipeline_modified.connect(self.update_pipeline_editors)
        p_e.edit_sub_pipeline.connect(self.open_sub_pipeline)
        p_e.open_filter.connect(self.open_filter)
        p_e.export_to_db_scans.connect(self.export_to_db_scans)
        p_e.initialized = False
        p_e.iterated = False
        p_e.iterated_tag = None
        p_e.tag_values_list = []
        p_e.node_parameters = {}
        p_e.node_parameters_tmp = {}
        # A unique editor name has to be automatically generated
        idx = 1

        while True and idx < 50:
            name = f"New Pipeline {idx}"

            if self.get_index_by_tab_name(name):
                idx += 1
                continue

            else:
                break

        if name is not None:
            self.undos[p_e] = []
            self.redos[p_e] = []

        else:
            logger.info("Too many tabs in the Pipeline Editor")
            return

        self.insertTab(self.count() - 1, p_e, name)
        self.set_tab_index(self.count() - 2)
        self.get_capsul_engine()
        self.update_iteration_checkbox()

    def open_filter(self, node_name):
        """Open a filter widget.

        :param node_name: name of the corresponding node
        """
        node = self.get_current_pipeline().nodes[node_name]
        self.filter_widget = FilterWidget(self.project, node_name, node, self)
        self.filter_widget.show()

    def open_sub_pipeline(self, sub_pipeline):
        """Open a sub-pipeline in a new tab.

        :param sub_pipeline: the pipeline to open
        """
        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        # Reading the process configuration file
        config = Config()

        with open(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            ),
        ) as stream:
            try:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    dic = yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    dic = yaml.load(stream)

            except yaml.YAMLError as exc:
                logger.warning(exc)
                dic = {}

        sub_pipeline_name = sub_pipeline.name
        # Finding from where comes from the pipeline
        pckg = sub_pipeline.__module__.split(".", 1)[0]

        if pckg == "mia_processes":
            paths_list = [
                os.path.dirname(sys.modules["mia_processes"].__path__[0])
            ]

        else:
            paths_list = dic["Paths"]

        # get_path returns a list that is the package path to
        # the sub_pipeline file
        sub_pipeline_list = get_path(
            sub_pipeline_name, dic["Packages"], None, pckg
        )
        sub_pipeline_name = sub_pipeline_list.pop()
        # Finding the real sub-pipeline filename
        sub_pipeline_filename = find_filename(
            paths_list, sub_pipeline_list, sub_pipeline_name
        )
        self.load_pipeline(sub_pipeline_filename)

    def reset_pipeline(self):
        """Reset the pipeline of the current editor."""
        self.get_current_editor()._reset_pipeline()

    def save_pipeline(self, new_file_name=None):
        """Save the pipeline of the current editor."""

        if new_file_name is None:
            # Doing a "Save as" action
            new_file_name = self.get_current_editor().save_pipeline()

            if new_file_name:
                new_file_name = os.path.basename(new_file_name)

            if (
                new_file_name
                and os.path.basename(self.get_current_filename())
                != new_file_name
            ):
                self.setTabText(self.currentIndex(), new_file_name)

            return new_file_name

        else:
            # Saving the current pipeline
            pipeline = self.get_current_pipeline()

            try:
                posdict = {
                    key: (value.x(), value.y())
                    for key, value in (
                        self.get_current_editor().scene.pos
                    ).items()
                }

            except Exception:
                posdict = {
                    key: (value[0], value[1])
                    for key, value in (
                        self.get_current_editor().scene.pos
                    ).items()
                }

            dimdict = {
                key: (value[0], value[1])
                for key, value in (self.get_current_editor().scene.dim).items()
            }
            pipeline.node_dimension = dimdict
            old_pos = pipeline.node_position
            pipeline.node_position = posdict
            save_pipeline(pipeline, new_file_name)
            self.get_current_editor()._pipeline_filename = str(new_file_name)
            pipeline.node_position = old_pos
            self.pipeline_saved.emit(new_file_name)
            self.setTabText(
                self.currentIndex(), os.path.basename(new_file_name)
            )
            return new_file_name

    def save_pipeline_parameters(self):
        """Save the pipeline parameters of the current editor."""
        self.get_current_editor().save_pipeline_parameters()

    def set_current_editor_by_editor(self, editor):
        """Set the current editor.

        :param editor: editor in the tab that should be made current
        """
        self.set_tab_index(self.get_index_by_editor(editor))

    def set_current_editor_by_file_name(self, file_name):
        """Set the current editor from file name.

        :param file_name: name of the file the pipeline was last saved to
        """
        self.set_tab_index(self.get_index_by_filename(file_name))

    def set_current_editor_by_tab_name(self, tab_name):
        """Set the current editor from tab name.

        :param tab_name: name of the tab
        """
        self.set_tab_index(self.get_index_by_tab_name(tab_name))

    def set_tab_index(self, index):
        """Set the current tab index and disable the run pipeline action.

        :param index: index of the editor
        """
        self.setCurrentIndex(index)
        self.previousIndex = index
        self.update_current_node(index)

    def update_iteration_checkbox(self):
        """blabla"""
        pipeline = self.get_current_pipeline()

        if not pipeline or not hasattr(pipeline, "nodes"):
            # fmt: off
            (
                self.main_window.pipeline_manager.iterationTable.
                check_box_iterate.setCheckState
            )(Qt.Qt.Unchecked)
            # fmt: on

        else:
            has_iteration = False

            for key in pipeline.nodes.sortedKeys:

                if "iterated_" in key:
                    has_iteration = True

            if has_iteration:
                # fmt: off
                (
                    self.main_window.pipeline_manager.iterationTable.
                    check_box_iterate.setCheckState
                )(Qt.Qt.Checked)
                # fmt: on

            else:
                # fmt: off
                (
                    self.main_window.pipeline_manager.iterationTable.
                    check_box_iterate.setCheckState
                )(Qt.Qt.Unchecked)
                # fmt: on

    def update_current_node(self, index):
        """Update the node parameters

        :param index: index of the editor
        """

        try:

            for node_name, node in self.get_current_pipeline().nodes.items():
                self.main_window.pipeline_manager.displayNodeParameters(
                    node_name, node.process
                )

        except AttributeError:
            pass

        self.main_window.pipeline_manager.update_user_buttons_states()
        self.update_iteration_checkbox()

        # fmt: off
        if self.get_current_editor():
            (
                self.main_window.pipeline_manager.iterationTable.
                update_iterated_tag
            )(self.get_current_editor().iterated_tag)
        # fmt: on

    def update_history(self, editor):
        """Update undo/redo history of an editor.

        :param editor: editor
        """
        self.undos[editor] = editor.undos
        self.redos[editor] = editor.redos
        self.setTabText(
            self.currentIndex(), f"{self.get_current_tab_name()} *"
        )
        # TODO: make sure the " *" is there

    def update_pipeline_editors(self, editor):
        """Update editor.

        :param editor: editor
        """
        self.update_history(editor)
        self.update_scans_list()

    def update_scans_list(self):
        """Update the list of database scans in every editor."""

        for i in range(self.count() - 1):
            pipeline = self.widget(i).scene.pipeline

            if pipeline.trait("database_scans"):

                try:
                    setattr(pipeline, "database_scans", self.scan_list)

                except Exception:
                    logger.warning("An error occurred", exc_info=True)
                    # but continue...

        self.update_iteration_checkbox()


def find_filename(paths_list, packages_list, file_name):
    """
    Find the corresponding file name in the paths list of process_config.yml.

    :param paths_list: list of all the paths contained in process_config.yml
    :param packages_list: packages path
    :param file_name: name of the sub-pipeline
    :return: name of the corresponding file if it is found, else None
    """
    filenames = [f"{file_name}.py", f"{file_name}.xml"]

    for filename in filenames:

        for path in paths_list:
            new_path = path

            for package in packages_list:
                new_path = os.path.join(new_path, package)

            # Making sure that the filename is found (has some issues
            # with case sensitivity)
            if os.path.isdir(new_path):

                for f in os.listdir(new_path):
                    new_file = os.path.join(new_path, f)

                    if (os.path.isfile(new_file)) and (
                        f.lower() == filename.lower()
                    ):
                        return new_file


def get_path(name, dictionary, prev_paths=None, pckg=None):
    """Return the package path to the selected sub-pipeline.

    :param name: name of the sub-pipeline
    :param dictionary: package tree
    :param prev_paths: paths of the last call of this function
    :param pckg: package root
    :return: the package path of the sub-pipeline if it is found, else None
    """

    if prev_paths is None:
        prev_paths = []

        if pckg is not None:
            prev_paths.append(pckg)
            dictionary = dictionary.get(pckg, {})

    # new_paths is a list containing the packages to the desired module
    new_paths = prev_paths.copy()

    for idx, (key, value) in enumerate(dictionary.items()):
        # If the value is a string, this means
        # that this is a "leaf" of the tree
        # so the key is a module name.

        if isinstance(value, str):

            if key == name:
                new_paths.append(key)
                return new_paths

            else:
                continue

        # Else, this means that the value is still a dictionary,
        # we are still in the tree
        else:
            new_paths.append(key)
            final_res = get_path(name, value, new_paths)

            # final_res is None if the module name has not
            # been found in the tree
            if final_res:
                return final_res

            else:
                new_paths = prev_paths.copy()


def save_pipeline(pipeline, filename):
    """Save the pipeline either in XML or .py source file.

    :param pipeline: the pipeline to save
    :param filename: name of the file where to save the pipeline
    """
    formats = {".py": save_py_pipeline, ".xml": save_xml_pipeline}
    saved = False

    for ext, writer in formats.items():

        if filename.endswith(ext):
            writer(pipeline, filename)
            saved = True
            break

    if not saved:
        # fallback to .py
        save_py_pipeline(pipeline, filename)


def values(d):
    """Return a variable as a list.

    :return (list): A variable as a list.
    """
    return list(d.values())
