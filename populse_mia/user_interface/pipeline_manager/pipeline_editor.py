"""
Module that executes the actions in the pipeline manager menu and allows
to graphically modify a pipeline.


Contains:

    Class:
        - PipelineEditor
        - PipelineEditorTabs

    Function:
        - find_filename
        - get_path
        - save_pipeline
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
from pathlib import Path

import yaml

# Capsul imports
from capsul.api import (
    Node,
    PipelineNode,
    Process,
    Switch,
    get_process_instance,
)
from capsul.attributes.completion_engine import ProcessCompletionEngine
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
    """
    Graphical editor for creating, editing, and managing pipelines.

    This view provides interactive tools to build pipeline graphs, connect
    nodes and plugs, edit node properties, and track modifications. It also
    handles persistence (save/export) and undo/redo history management.

    .. Methods:
        - _del_link: Deletes a link.
        - _export_plug: Export a plug to a pipeline global input or output.
        - _release_grab_link: Method called when a link is released.
        - _remove_plug: Removes a plug.
        - add_link: Add a link between two nodes.
        - add_named_process: Adds a process to the pipeline.
        - check_modifications: Checks if the nodes of the pipeline have been
                               modified.
        - del_node: Deletes a node.
        - export_node_plugs: Exports all the plugs of a node.
        - get_current_filename: Returns the relative path the pipeline was
                                last saved to. Empty if never saved.
        - save_pipeline: Saves the pipeline.
        - update_history: Updates the history for undos and redos/
        - update_node_name: Updates a node name.
        - update_plug_value: Updates a plug value.
    """

    # The signal emitted when the pipeline is saved
    pipeline_saved = QtCore.pyqtSignal(str)
    # The signal emitted when the pipeline is modified
    pipeline_modified = QtCore.pyqtSignal(PipelineDeveloperView)

    def __init__(self, project, main_window):
        """
        Initialize the PipelineEditor for visual pipeline development.

        Sets up the pipeline editor with project context and initializes
        undo/redo functionality.

        :param project: The current project instance containing pipeline data
                        and configuration.
        :parm main_window: The main application window instance for UI
                           integration.
        """
        super().__init__(
            pipeline=None,
            allow_open_controller=True,
            show_sub_pipelines=True,
            enable_edition=True,
        )
        engine = Config.get_capsul_engine()
        self.scene.pipeline.set_study_config(engine.study_config)
        self.project = project
        self.main_window = main_window
        # Initialize undo/redo stacks
        self.undos = []
        self.redos = []
        self.userlevel = Config().get_user_level()

    def _del_link(self, link=None, from_undo=False, from_redo=False):
        """
        Delete a link between two pipeline nodes.

        Removes a connection between a source node's output plug and a
        destination node's input plug, updates the pipeline state, and
        records the action in history.

        :param link: Link specification string in the format
                     "source_node.output_plug->dest_node.input_plug".If None,
                     uses the current link stored in self._current_link.
        :param from_undo: Whether this deletion is being performed as part of
                          an undo operation. Affects history recording.
        :param from_redo: Whether this deletion is being performed as part of
                          a redo operation. Affects history recording.

        Side Effects:
            - Updates self._current_link to the deleted link
            - Modifies self._current_link_def with link component references
            - Calls parent class's _del_link() to perform actual deletion
            - Records action in history unless from undo/redo
        """
        # Use provided link or fall back to current link
        link = link or self._current_link
        self._current_link = link
        # Parse link into its components
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
        # Extract destination details from the source plug's first link
        (
            dest_node_name,
            _,
            dest_node,
            dest_plug,
            weak_link,
        ) = list(
            source_plug.links_to
        )[0]
        # Determine if both plugs are active
        active = source_plug.activated and dest_plug.activated
        # Store link definition for potential restoration
        self._current_link_def = (
            source_node,
            source_plug,
            dest_node,
            dest_plug,
        )
        # Perform the actual deletion via parent class
        super()._del_link()
        # Record action in history
        history_maker = [
            "delete_link",
            (source_node_name, source_plug_name),
            (dest_node_name, dest_plug_name),
            active,
            weak_link,
        ]
        self.update_history(history_maker, from_undo, from_redo)
        # Provide user feedback
        self.main_window.statusBar().showMessage(
            f"Link {link} has been deleted."
        )

    def _export_plug(
        self,
        pipeline_parameter=None,
        optional=None,
        weak_link=None,
        from_undo=False,
        from_redo=False,
        temp_plug_name=None,
        multi_export=False,
    ):
        """
        Export a plug to a pipeline global input or output.

        This method exports a node plug to the pipeline level, making it
        accessible as a pipeline parameter. It handles name conflicts, creates
        appropriate links, and maintains operation history for undo/redo
        functionality.

        :param pipeline_parameter (str): Name for the exported pipeline
                                         parameter. If None, prompts user for
                                         a name via dialog. Defaults to None.
        :param optional (bool): Whether the exported plug is optional. If
                                None, derived from dialog checkbox or plug
                                configuration. Defaults to None.
        :param weak_link (bool): Whether to create a weak link (doesn't
                                 enforce execution order). If None, derived
                                 from dialog or defaults to False.
        :param from_undo (bool): True when called during an undo operation.
                                 Used to prevent circular history updates.
                                 Defaults to False.
        :param from_redo (bool): True when called during a redo operation.
                                 Used to prevent circular history updates.
                                 Defaults to False.
        :param temp_plug_name (tuple): A (node_name, plug_name) tuple
                                       specifying the plug to export. If None,
                                       uses self._temp_plug_name. Defaults to
                                       None.
        :param multi_export (bool): True when exporting multiple plugs
                                    simultaneously. Changes return behavior
                                    and error handling. Defaults to False.

        :return (str): When multi_export is True, returns the plug name on
                       success or None on failure. When multi_export is False,
                       returns None after updating the UI and history.

        :raises TraitError: Logged as warning when plug export fails due to
                            trait issues.
        :raises ValueError: Logged as warning when export fails due to invalid
                            values.

        Side Effects:
            - May display dialog boxes for user input
            - Updates pipeline structure and UI
            - Adds entry to operation history (unless from_undo/from_redo)
            - Shows status message in main window
        """
        temp_plug_name = temp_plug_name or self._temp_plug_name

        # Get plug name from user dialog or use provided parameter
        if pipeline_parameter is None:
            dialog = self._PlugEdit()
            dialog.name_line.setText(temp_plug_name[1])
            dialog.optional.setChecked(self._temp_plug.optional)

            if not dialog.exec_():
                return None

            plug_name = str(dialog.name_line.text())
            optional = (
                optional
                if optional is not None
                else dialog.optional.isChecked()
            )
            weak_link = (
                weak_link if weak_link is not None else dialog.weak.isChecked()
            )

        else:
            plug_name = pipeline_parameter
            weak_link = weak_link if weak_link is not None else False

        # Handle name conflicts interactively
        allow_existing_plug = False

        while True:
            existing_plugs = self.scene.pipeline.pipeline_node.plugs

            if plug_name not in existing_plugs:
                break  # Unique plug name → done

            # Ask user if they want to connect to the existing plug
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle(
                "populse_mia - Warning: Duplicate pipeline plug"
            )
            msg_box.setText(
                f"The '{plug_name}' pipeline plug already exists.\n"
                "Do you want to connect to this existing plug?"
            )
            reply = msg_box.question(
                self,
                msg_box.windowTitle(),
                msg_box.text(),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )

            if reply == QMessageBox.Cancel:
                return None

            if reply == QMessageBox.Yes:
                allow_existing_plug = True
                break

            # Otherwise (No), ask for a new name
            new_name, ok = QInputDialog.getText(
                self,
                "Plug name Input Dialog",
                f"The plug '{plug_name}' already exists.\n"
                "Please choose a new name:",
            )

            if not ok or not new_name.strip():
                return None

            plug_name = new_name.strip()

        # Attempt the export
        try:
            self.scene.pipeline.export_parameter(
                temp_plug_name[0],
                temp_plug_name[1],
                plug_name,
                weak_link=weak_link,
                is_optional=optional,
                allow_existing_plug=allow_existing_plug,
            )

        except TraitError:
            logger.warning(
                f"Cannot export {temp_plug_name[0]}.{plug_name} plug."
            )
            return None

        except ValueError as e:
            logger.warning(f"\n{e}")
            return None

        # If multiple exports, only return plug name
        if multi_export:
            return temp_plug_name[1]

        # Update UI and history
        self.scene.update_pipeline()
        self.update_history(
            ["export_plugs", plug_name, temp_plug_name[0]],
            from_undo,
            from_redo,
        )
        self.main_window.statusBar().showMessage(
            f"Plug {plug_name} has been exported."
        )
        return None

    def _release_grab_link(self, event):
        """
        Handle link release event and update pipeline history.

        Called when a user releases a link in the pipeline editor. This method
        extends the parent class behavior by recording the link addition in
        the history and displaying a status message.

        :param event: Mouse event corresponding to the link release.
        """
        # TODO: Is this method still used?

        # Retrieve the created link from parent implementation
        link = super()._release_grab_link(event, ret=True)
        # Record link creation in history for undo/redo functionality
        self.update_history(
            history_maker=["add_link", link], from_undo=False, from_redo=False
        )
        # Provide user feedback
        self.main_window.statusBar().showMessage(
            f"Link {link} has been added."
        )

    def _remove_plug(
        self,
        plug_names=None,
        from_undo=False,
        from_redo=False,
        from_export_plugs=False,
    ):
        """
        Remove one or more plugs from the pipeline.

        This method removes plugs from the pipeline, tracks their connections
        for potential undo/redo operations, and updates the application
        history unless called from an export operation.

        :param plug_names: A tuple (node_name, plug_name) or list of such
                           tuples specifying the plug(s) to remove. If None,
                           uses self._temp_plug_name.
        :param from_undo: Whether this method is being called from an undo
                          operation.
        :param from_redo: Whether this method is being called from a redo
                          operation.
        :param from_export_plugs: Whether this method is being called from an
                                  export plugs undo/redo operation. When True,
                                  history is not updated.

        :note: For each removed plug, stores [plug_info, connected_plugs,
               optional_flag] in the history for potential restoration.
        """
        # Use provided plug names or fall back to instance variable
        plug_names = plug_names or self._temp_plug_name

        # Normalize to list format for uniform processing
        if isinstance(plug_names, tuple):
            plug_names = [plug_names]

        removed_plugs_info = []

        for node_name, plug_name in plug_names:

            # Only process pipeline input/output plugs
            if node_name not in ("inputs", "outputs"):
                continue

            plug = self.scene.pipeline.pipeline_node.plugs[plug_name]
            # Collect all connected plugs for history tracking
            connected_plugs = [
                (link[0], link[1])
                for link in (*plug.links_to, *plug.links_from)
            ]
            # Fix potential "_items" bug by disabling has_items attribute
            pipeline_node = self.scene.pipeline.nodes[""]
            source_trait = pipeline_node.get_trait(plug_name)

            if source_trait.handler.has_items:
                source_trait.handler.has_items = False

            # Remove the plug and update pipeline
            self.scene.pipeline.remove_trait(plug_name)
            self.scene.update_pipeline()

            # Store removal information for history
            removed_plugs_info.append(
                [(node_name, plug_name), connected_plugs, plug.optional]
            )

            # Update history and status bar (unless called from export
            # operation)
            if not from_export_plugs and removed_plugs_info:
                self.update_history(
                    ["remove_plug", removed_plugs_info], from_undo, from_redo
                )

                # Display appropriate status message
                if len(removed_plugs_info) == 1:
                    plug_name = removed_plugs_info[0][0][1]
                    message = f"'{plug_name}' plug has been removed."

                else:
                    plug_names_str = tuple(
                        info[0][1] for info in removed_plugs_info
                    )
                    message = f"{plug_names_str} plugs have been removed."

                self.main_window.statusBar().showMessage(message)

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
        """
        Add a link between two nodes in the pipeline.

        Creates a connection between a source node's output plug and a
        destination node's input plug. The link is represented as
        "node.plug->node.plug" format and added to the pipeline scene.

        :param source: A tuple of (node_name, plug_name) for the source
                       connection.
        :param dest: A tuple of (node_name, plug_name) for the destination
                     connection.
        :param active: Whether the link is currently active/enabled.
        :param weak: Whether the link is a weak reference that doesn't enforce
                     strict execution dependencies.
        :param from_undo: Whether this action originates from an undo
                          operation. Defaults to False.
        :param from_redo: Whether this action originates from a redo
                          operation. Defaults to False.
        :param allow_export: Whether to allow this link in exported pipelines.
                             Defaults to False.

        Side Effects:
            - Adds the link to the pipeline scene
            - Updates the pipeline visualization
            - Records the action in history (unless from undo/redo)
            - Displays a status message in the main window
        """
        # Create link representation in "node.plug->node.plug" format
        link = f"{'.'.join(source)}->{'.'.join(dest)}"
        # Add link to pipeline and refresh visualization
        self.scene.pipeline.add_link(link, allow_export=allow_export)
        self.scene.update_pipeline()
        # Record action in history for undo/redo functionality
        self.update_history(["add_link", link], from_undo, from_redo)
        # Provide user feedback
        self.main_window.statusBar().showMessage(
            f"Link {link} has been added."
        )

    def add_named_process(
        self,
        class_process,
        node_name=None,
        from_undo=False,
        from_redo=False,
        links=None,
    ):
        """
        Add a process to the pipeline with optional link restoration.

        This method adds a named process to the pipeline and configures it
        according to project settings. It also handles link restoration when
        the action is part of an undo/redo operation.

        :param class_process (str): The name of the process class to
                                    instantiate.
        :param node_name (str): Custom name for the node. If None, the name is
                                derived from the process's context_name or
                                name attribute. Defaults to None.
        :param from_undo (bool): Whether this action is part of an undo
                                 operation. Defaults to False.
        :param from_redo (bool): Whether this action is part of a redo
                                 operation. Defaults to False.
        :param links (list): List of link tuples to restore, where each tuple
                             contains (source, dest, active, weak). Used
                             during undo/redo operations. Defaults to None.

        Side Effects:
            - Adds process to the pipeline
            - Configures project settings if applicable
            - Restores links if provided
            - Updates history for undo/redo
            - Updates UI status bar and buttons
        """

        if links is None:
            links = []

        # Add the process via parent class
        process = super().add_named_process(class_process, node_name)

        # Determine node name from process if not provided
        if node_name is None:
            context_name = getattr(process, "context_name", process.name)
            node_name = context_name.split(".")[-1]

        # Configure project if process requires it
        if getattr(process, "use_project", False):
            process.project = self.project

        # Set SPM script file user level for process and nested process
        if hasattr(process, "_spm_script_file"):
            process.trait("_spm_script_file").userlevel = 1

        if hasattr(process, "process") and hasattr(
            process.process, "_spm_script_file"
        ):
            process.process.trait("_spm_script_file").userlevel = 1

        # Restore links if this is part of an undo operation
        for source, dest, active, weak in links:
            # Add link to scene
            self.scene.add_link(source, dest, active, weak)
            # Create string representation of link
            link_string = "->".join([".".join(source), ".".join(dest)])
            # Add link to pipeline
            self.scene.pipeline.add_link(link_string)

        # Update pipeline once after all links are restored
        if links:
            self.scene.update_pipeline()

        # Update history for undo/redo functionality
        history_maker = ["add_process", node_name]

        if not from_undo:
            history_maker.append(class_process)

        self.update_history(history_maker, from_undo, from_redo)
        # Update UI
        self.main_window.statusBar().showMessage(
            f"Node {node_name} has been added."
        )
        self.main_window.pipeline_manager.update_user_buttons_states()

    def check_modifications(self):
        """
        Check and update pipeline nodes that have been modified.

        This method iterates through all pipeline nodes and detects if the
        underlying process definition has changed (added/removed
        inputs/outputs).

        When changes are detected, it:
            - Recreates the node with the updated process definition
            - Preserves the node's position in the scene
            - Attempts to restore compatible links
            - Removes incompatible links and notifies the user

        Side Effects:
            Modifies self.scene.gnodes, self.scene.glinks, and pipeline.nodes.
            Displays a warning dialog if any links are removed.
        """
        # Import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        pipeline = self.scene.pipeline
        config = Config()
        # List to store the removed links
        removed_links = []

        # Load process configuration once for all nodes
        config_path = os.path.join(
            config.get_properties_path(), "properties", "process_config.yml"
        )

        try:
            with open(config_path) as stream:
                if verCmp(yaml.__version__, "5.1", "sup"):
                    process_config = yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    process_config = yaml.load(stream)

        except yaml.YAMLError as exc:
            logger.warning(f"Failed to load process config: {exc}")
            process_config = {}

        for node_name, node in pipeline.nodes.items():

            # Skip if the node is a pipeline node
            if not (node_name and isinstance(node, PipelineNode)):
                continue

            sub_pipeline_process = node.process
            sub_pipeline_name = sub_pipeline_process.name
            # Finding from where comes from the pipeline
            package = sub_pipeline_process.__module__.split(".", 1)[0]

            # Determine search paths based on package
            if package == "mia_processes":
                paths_list = [
                    os.path.dirname(sys.modules["mia_processes"].__path__[0])
                ]

            else:
                paths_list = process_config.get("Paths", [])

            # Locate and load the saved process
            # get_path returns a list that is the package path
            # to the sub_pipeline file
            sub_pipeline_list = get_path(
                sub_pipeline_name,
                process_config.get("Packages", {}),
                None,
                package,
            )
            sub_pipeline_name = sub_pipeline_list.pop()
            # Finding the real sub-pipeline filename
            sub_pipeline_filename = find_filename(
                paths_list, sub_pipeline_list, sub_pipeline_name
            )
            saved_process = get_process_instance(sub_pipeline_filename)
            # Compare process signatures using set operations
            current_inputs = set(sub_pipeline_process.get_inputs().keys())
            current_outputs = set(sub_pipeline_process.get_outputs().keys())
            saved_inputs = set(saved_process.get_inputs().keys())
            saved_outputs = set(saved_process.get_outputs().keys())
            new_inputs = saved_inputs - current_inputs
            new_outputs = saved_outputs - current_outputs
            removed_inputs = current_inputs - saved_inputs
            removed_outputs = current_outputs - saved_outputs

            if not (
                new_inputs or new_outputs or removed_inputs or removed_outputs
            ):
                continue

            # Remove all links connected to this node
            links_to_restore = [
                (link, glink)
                for link, glink in self.scene.glinks.items()
                if link[0][0] == node_name or link[1][0] == node_name
            ]

            for link, glink in links_to_restore:
                self.scene.removeItem(glink)
                del self.scene.glinks[link]

            # Create and configure new node
            new_node = saved_process.pipeline_node
            new_node.name = node_name
            new_node.pipeline = pipeline
            saved_process.parent_pipeline = weak_proxy(pipeline)
            pipeline.nodes[node_name] = new_node
            # Create new graphical node and preserve position
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
            gnode.setPos(self.scene.pos.get(node_name))
            # Replace old node with new one
            self.scene.removeItem(self.scene.gnodes[node_name])
            del self.scene.gnodes[node_name]
            self.scene.gnodes[node_name] = gnode
            self.scene.addItem(gnode)

            # Attempt to restore compatible links
            for link, _ in links_to_restore:
                source, dest = link[0], link[1]

                # Normalize special nodes (inputs/outputs)
                if source[0] == "inputs":
                    source = ("", source[1])
                if dest[0] == "outputs":
                    dest = ("", dest[1])

                # Create link representation
                pipeline_link = f"{'.'.join(source)}->{'.'.join(dest)}"

                # Skip if connected plug was removed
                if (dest[0] == node_name and dest[1] in removed_inputs) or (
                    source[0] == node_name and source[1] in removed_outputs
                ):
                    removed_links.append(pipeline_link)
                    continue

                # Restore valid link
                self.scene.pipeline.add_link(pipeline_link)
                self.scene.add_link(source, dest, active=True, weak=False)

            self.scene.update_pipeline()

        # Notify user if any links were removed
        if removed_links:
            dialog_text = (
                f"Pipeline {node_name} has been updated.\nRemoved links:"
            )

            for removed_link in removed_links:
                dialog_text += f"\n{removed_link}"

            pop_up = QtWidgets.QMessageBox()
            pop_up.setIcon(QtWidgets.QMessageBox.Warning)
            pop_up.setText(dialog_text)
            pop_up.setWindowTitle("Warning: Links Removed During Update")
            pop_up.setStandardButtons(QtWidgets.QMessageBox.Ok)
            pop_up.exec_()

    def del_node(self, node_name=None, from_undo=False, from_redo=False):
        """
        Deletes a node from the pipeline and updates the GUI and history
        accordingly.

        :param node_name (str): The name of the node to delete. If not
                                provided, the currently selected node is used.
        :param from_undo (bool): True if the deletion was triggered by an undo
                                 operation.
        :param from_redo (bool): True if the deletion was triggered by a redo
                                 operation.
        """
        pipeline = self.scene.pipeline
        node_name = node_name or self.current_node_name
        # Determine the node and whether to invert input/output logic
        invert_io = node_name in ("inputs", "outputs")
        node = (
            pipeline.pipeline_node if invert_io else pipeline.nodes[node_name]
        )
        # Collect all links related to this node
        links = []

        for plug_name, plug in node.plugs.items():
            connected_links = (
                plug.links_to
                if (plug.output or (invert_io and not plug.output))
                else plug.links_from
            )

            for link in connected_links:
                (
                    linked_node_name,
                    _,
                    linked_node,
                    linked_plug,
                    weak_link,
                ) = link
                active = plug.activated
                # Find the plug name in the linked node
                linked_plug_name = next(
                    (
                        n
                        for n, p in linked_node.plugs.items()
                        if p == linked_plug
                    ),
                    None,
                )

                # Build the link structure:
                # [
                #     (src_node, src_plug),
                #     (dst_node, dst_plug),
                #     active,
                #     weak_link
                # ]
                if plug.output or (invert_io and not plug.output):
                    link_to_add = [
                        (node_name, plug_name),
                        (linked_node_name, linked_plug_name),
                        active,
                        weak_link,
                    ]

                else:
                    link_to_add = [
                        (linked_node_name, linked_plug_name),
                        (node_name, plug_name),
                        active,
                        weak_link,
                    ]
                links.append(link_to_add)

        # Call parent method to perform the actual deletion
        super().del_node(node_name)
        # Update history and GUI
        process = node.process if isinstance(node, ProcessNode) else node
        history_entry = ["delete_process", node_name, process, links]
        self.update_history(history_entry, from_undo, from_redo)
        self.main_window.statusBar().showMessage(
            f"Node {node_name} has been deleted."
        )

        # Refresh parameter display for all remaining nodes
        for name, node in pipeline.nodes.items():

            if name:
                process = (
                    node.process if isinstance(node, ProcessNode) else node
                )
                self.main_window.pipeline_manager.displayNodeParameters(
                    name, process
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
        """
        Export plugs (parameters) from a pipeline node to make them available
        externally.

        This method identifies and exports node plugs that meet the specified
        criteria (input/output type, optional status, unlinked status) and are
        not in the pipeline's exclusion list.

        :param node_name: Name of the node whose plugs should be exported.
        :param inputs: Whether to export input plugs. Defaults to True.
        :param outputs: Whether to export output plugs. Defaults to True.
        :param optional: Whether to include optional plugs in the export.
                         Defaults to False.
        :param from_undo: Whether this call originates from an undo operation.
                          Defaults to False.
        :param from_redo: Whether this call originates from a redo operation.
                          Defaults to False.

        :note:
            - Only unlinked plugs are exported (outputs without links_to,
              inputs without links_from)
            - Certain system plugs are automatically excluded
              (nodes_activation, selection_changed, etc.)
            - The operation is recorded in the history for undo/redo support
        """
        # System plugs that should never be exported
        EXCLUDED_PLUGS = frozenset(
            {
                "nodes_activation",
                "selection_changed",
                "output_directory",
                "use_mcr",
                "paths",
                "matlab_cmd",
                "mfile",
                "spm_script_file",
            }
        )
        pipeline = self.scene.pipeline
        node = pipeline.nodes[node_name]
        # Collect exportable plugs
        exported_plugs = []

        for param_name, plug in node.plugs.items():

            # Skip system plugs
            if param_name in EXCLUDED_PLUGS:
                continue

            # Skip plugs in the do-not-export list
            if (node_name, param_name) in pipeline.do_not_export:
                continue

            # Check if plug meets export criteria
            is_unlinked_output = outputs and plug.output and not plug.links_to
            is_unlinked_input = (
                inputs and not plug.output and not plug.links_from
            )
            is_optional_allowed = (
                optional or not node.get_trait(param_name).optional
            )

            if (
                is_unlinked_output or is_unlinked_input
            ) and is_optional_allowed:
                exported_name = self._export_plug(
                    param_name,
                    temp_plug_name=(node_name, param_name),
                    multi_export=True,
                )

                if exported_name:  # Only add non-None values
                    exported_plugs.append(exported_name)

        # Update pipeline state
        self.scene.update_pipeline()
        # Record in history for undo/redo
        history_entry = ["export_plugs", exported_plugs, node_name]
        self.update_history(history_entry, from_undo, from_redo)
        # Notify user
        plug_list_str = (
            ", ".join(exported_plugs) if exported_plugs else "No plugs"
        )
        self.main_window.statusBar().showMessage(
            f"{plug_list_str} exported from node '{node_name}'."
        )

    def get_current_filename(self):
        """
        Return the relative path to the last saved pipeline file.

        Returns the relative path from the current working directory to the
        file where this pipeline was most recently saved. If the pipeline has
        never been saved, returns an empty string.

        :return (str): Relative path to the pipeline file, or empty string if
                       never saved.
        """
        filename = getattr(self, "_pipeline_filename", None)

        return os.path.relpath(filename) if filename else ""

    def save_pipeline(self, filename=None):
        """
        Save the pipeline to a Python file.

        This method saves the current pipeline configuration to a file. If no
        filename is provided, it prompts the user with a file dialog. The
        method performs validation to ensure the filename is valid (doesn't
        start with a digit, has .py extension) and checks user permissions.

        :param filename (str): Path where the pipeline should be saved. If
                               None, a file dialog will be shown. Defaults to
                               None.

        :return (str): The absolute path of the saved pipeline file,
                       or None if:
                - The pipeline is empty (fewer than 2 nodes)
                - The user cancelled the save dialog
                - The filename is invalid
                - The user lacks permission to overwrite an existing file

        :note:
            - pipeline_saved: Signal emitted with the filename when save is
                              successful.
        """

        def _show_warning(title, message):
            """
            Display a warning message box to the user.

            :param title (str): The title displayed in the warning dialog
                                window.
            :param message (str): The message text shown inside the warning
                                  dialog box.
            """
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec()

        self.check_modifications()

        # Don't save empty pipelines
        if len(self.scene.pipeline.nodes) < 2:
            logger.info("Pipeline not saved: it is empty")
            return None

        config = Config()
        pipeline = self.scene.pipeline

        # Determine filename through dialog if not provided or if it's in
        # mia_processes (prohibition on modifying the mia_processes library)
        if (not filename) or (
            Path("mia_processes") / "mia_processes" in Path(filename).parents
        ):
            folder = (
                Path(config.get_properties_path())
                / "processes"
                / "User_processes"
            )
            folder.mkdir(parents=True, exist_ok=True)
            # Ensure __init__.py exists
            (folder / "__init__.py").touch(exist_ok=True)
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                None,
                "Save the pipeline",
                str(folder),
                "Compatible files (*.py);; All (*)",
            )

            if not filename:  # User cancelled
                return None

            path = Path(filename)

            # Check if filename starts with a digit
            if path.stem[0].isdigit():
                _show_warning(
                    "Invalid Pipeline Name",
                    "Python module names cannot start with a digit. "
                    "Please choose a different name.",
                )
                return None

            # Normalize to lowercase
            filename = str(path.parent / path.name.lower())
            path = Path(filename)

            # Handle file extension
            if not path.suffix:
                filename = f"{filename}.py"

            elif path.suffix != ".py":
                _show_warning(
                    "Extension Changed",
                    f"The pipeline will be saved with a '.py' extension "
                    f"instead of '{path.suffix}'.",
                )
                filename = f"{path.with_suffix('').as_posix()}.py"

            # Check overwrite permissions
            if Path(filename).exists() and config.get_user_mode():
                _show_warning(
                    "Permission Denied",
                    "This file already exists and you do not have "
                    "permission to overwrite it.",
                )
                return None

        # Prepare and save pipeline with position and dimension data
        posdict = {
            key: (value.x(), value.y())
            for key, value in self.scene.pos.items()
        }
        dimdict = {
            key: (value[0], value[1]) for key, value in self.scene.dim.items()
        }
        pipeline.node_dimension = dimdict
        old_pos = pipeline.node_position
        pipeline.node_position = posdict

        try:
            save_pipeline(pipeline, filename)
            self._pipeline_filename = str(filename)
            self.pipeline_saved.emit(filename)
            return filename

        finally:
            # Restore original position
            pipeline.node_position = old_pos

    def update_history(self, history_maker, from_undo, from_redo):
        """
        Update the undo/redo history after a pipeline action.

        Manages the undo and redo stacks based on the action performed. When
        an action is undone, it's moved to the redo stack. When a new action
        is performed (not from undo/redo), it's added to the undo stack and
        complementary redo entries are cleaned up to maintain consistency.

        :param history_maker: A list describing the action, where
                              history_maker[0] is the action type
                              (e.g., 'add_process', 'delete_process',
                              'update_node_name') and history_maker[1] is
                              typically the affected node identifier.
        :param from_undo (bool): Whether this update stems from an undo
                                 operation. Defaults to False.
        :param from_redo (bool): Whether this update stems from a redo
                                 operation. Defaults to False.

        :note:
            - 'update_node_name' actions are not added to the undo stack
            - Complementary actions (add/delete for the same process) are
              removed from the redo stack when a new action occurs
            - pipeline_modified: Signal emitted indicating the pipeline has
              been modified.
        """

        if from_undo:
            self.redos.append(history_maker)

        else:
            self.undos.append(history_maker)

            # If the action was not triggered by a redo, adjust the redo list
            if not from_redo:
                action_map = {
                    "add_process": "delete_process",
                    "delete_process": "add_process",
                }
                action_type = history_maker[0]
                to_redo = action_map.get(action_type)

                # "update_node_name" actions remove the last undo entry
                if action_type == "update_node_name":
                    self.undos.pop()

                if to_redo:
                    self.redos = [
                        item
                        for item in self.redos
                        if not (
                            item[0] == to_redo and item[1] == history_maker[1]
                        )
                    ]

        self.pipeline_modified.emit(self)

    def update_node_name(
        self,
        old_node,
        old_node_name,
        new_node_name,
        from_undo=False,
        from_redo=False,
    ):
        """
        Update a node's name in the pipeline, preserving all connections.

        This method renames a node by:
        1. Temporarily removing all links connected to the node
        2. Renaming the node in the pipeline
        3. Restoring all links with the updated node name
        4. Recording the action in the history for undo/redo support

        :param old_node: The node object to rename.
        :param old_node_name: The current name of the node.
        :param new_node_name: The desired new name for the node.
        :param from_undo: Whether this action is being performed as part of an
                          undo operation. Defaults to False.
        :param from_redo: Whether this action is being performed as part of a
                          redo operation. Defaults to False.

        Side Effects:
            - Updates the pipeline's node registry
            - Removes and recreates all links connected to the node
            - Updates pipeline activation states
            - Records action in history
            - Displays status message to user
        """
        pipeline = self.scene.pipeline
        # Collect all links connected to this node before removal
        links_to_restore = []

        for source_param, source_plug in old_node.plugs.items():

            # Collect outgoing links (this node -> other nodes)
            for dest_node_name, dest_param, *_ in source_plug.links_to.copy():
                link_spec = (
                    f"{old_node_name}.{source_param}->"
                    f"{dest_node_name}.{dest_param}"
                )
                pipeline.remove_link(link_spec)
                links_to_restore.append(
                    ("outgoing", source_param, dest_node_name, dest_param)
                )

            # Collect incoming links (other nodes -> this node)
            for (
                dest_node_name,
                dest_param,
                *_,
            ) in source_plug.links_from.copy():
                link_spec = (
                    f"{dest_node_name}.{dest_param}->"
                    f"{old_node_name}.{source_param}"
                )
                pipeline.remove_link(link_spec)
                links_to_restore.append(
                    ("incoming", source_param, dest_node_name, dest_param)
                )

        # Rename the node in the pipeline
        pipeline.nodes[new_node_name] = pipeline.nodes.pop(old_node_name)

        # Restore all links with the new node name
        for (
            direction,
            source_param,
            dest_node_name,
            dest_param,
        ) in links_to_restore:

            if direction == "outgoing":
                link_spec = (
                    f"{new_node_name}.{source_param}->"
                    f"{dest_node_name}.{dest_param}"
                )

            else:  # incoming
                link_spec = (
                    f"{dest_node_name}.{dest_param}->"
                    f"{new_node_name}.{source_param}"
                )

            pipeline.add_link(link_spec)

        # Update pipeline state
        pipeline.update_nodes_and_plugs_activation()
        # Record action in history for undo/redo
        history_entry = [
            "update_node_name",
            pipeline.nodes[new_node_name],
            new_node_name,
            old_node_name,
        ]
        self.update_history(history_entry, from_undo, from_redo)
        # Notify user
        self.main_window.statusBar().showMessage(
            f"Node '{old_node_name}' renamed to '{new_node_name}'."
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
        """
        Update a node's plug value and record the change in history.

        Updates the specified plug on the given node with a new value. The
        update is recorded in the history for undo/redo operations unless it's
        already part of an undo/redo action.

        :param node_name: The name of the node containing the plug.
        :param  new_value: The new value to assign to the plug. Will be cast
                           to value_type unless from_undo or from_redo is True.
        :param plug_name: The name of the plug to update.
        :param value_type: The type constructor to apply to new_value
                           (e.g., int, float, str). Ignored when from_undo or
                           from_redo is True.
        :param from_undo: If True, indicates this update is from an undo
                          operation. Defaults to False.
        :param from_redo: If True, indicates this update is from a redo
                          operation. Defaults to False.

        Side Effects:
            - Updates the plug value in the pipeline
            - Records the change in history (unless from undo/redo)
            - Displays a status message in the main window
            - Pops from the undo stack if from undo/redo
        """
        node = self.scene.pipeline.nodes[node_name]
        old_value = node.get_plug_value(plug_name)
        # Skip type conversion for undo/redo - value is already correctly typed
        value_to_set = (
            new_value if (from_undo or from_redo) else value_type(new_value)
        )
        node.set_plug_value(plug_name, value_to_set)

        # Remove from undo stack if this is an undo/redo operation
        if from_undo or from_redo:
            self.undos.pop()

        # Record in history
        history_maker = [
            "update_plug_value",
            node_name,
            old_value,
            plug_name,
            value_type,
        ]
        self.update_history(history_maker, from_undo, from_redo)
        # User feedback
        self.main_window.statusBar().showMessage(
            f"Plug '{plug_name}' of node '{node_name}' changed "
            f"to '{new_value}'"
        )


class PipelineEditorTabs(QtWidgets.QTabWidget):
    """
    Tab widget for managing multiple pipeline editors.

    This widget provides a tabbed interface for creating, editing, and
    managing multiple pipeline configurations. Each tab contains a
    PipelineEditor instance with its own undo/redo history.

    .. Signals:
        pipeline_saved (str): Emitted when a pipeline is saved, passes
                              filename.
        node_clicked (str, Node): Emitted when a node is clicked in any editor.
        process_clicked (str, Process): Emitted when a process is clicked.
        switch_clicked (str, Switch): Emitted when a switch is clicked.

    .. Methods:
        - check_modifications: Check if the nodes of the current pipeline have
                               been modified.
        - close_tab: Close the selected tab and editor.
        - emit_node_clicked: Emit a signal when a node is clicked.
        - emit_pipeline_saved: Emit a signal when a pipeline is saved.
        - emit_switch_clicked: Emit a signal when a switch is clicked.
        - export_to_db_scans: Export the input of a filter to 'database_scans'.
        - get_capsul_engine: Configure and return a CapsulEngine for the
                             current pipeline.
        - get_current_editor: Return the instance of the current editor.
        - get_current_filename: Return the file name of the current pipeline.
        - get_current_pipeline: Return the instance of the current pipeline.
        - get_current_tab_name: Return the tab title of the current editor.
        - get_editor_by_file_name: Return the editor associated with the given
                                   pipeline filename.
        - get_editor_by_index: Retrieve an editor widget by its tab index.
        - get_editor_by_tab_name: Retrieve the editor instance associated with
                                  a specific tab name.
        - get_filename_by_index: get the pipeline filename from its index in
                                 the editors.
        - get_index_by_editor: Find the tab index for a given editor widget.
        - get_index_by_filename: Get the index of the editor corresponding to
                                 the given pipeline filename.
        - get_index_by_tab_name: Get the index of the editor corresponding to
                                 the given tab name.
        - get_tab_name_by_index: Get the tab title from its index in the
                                 editors.
        - has_pipeline_nodes: Check if any of the pipelines in the editor tabs
                              have pipeline nodes.
        - load_pipeline: Load a new pipeline.
        - load_pipeline_parameters: Load parameters to the pipeline of the
                                    current editor.
        - new_tab: Create a new tab and a new editor.
        - open_filter: Open a filter widget.
        - open_sub_pipeline: Open a sub-pipeline in a new tab.
        - reset_pipeline: Reset the pipeline of the current editor.
        - save_pipeline: Save the pipeline of the current editor.
        - save_pipeline_parameters: Save the pipeline parameters of the
                                    current editor.
        - set_current_editor_by_editor: Set the specified editor as the
                                        currently active editor.
        - set_current_editor_by_file_name: Activate the editor tab containing
                                           the specified file.
        - set_current_editor_by_tab_name: Activate the editor tab with the
                                          specified name.
        - set_tab_index: Activate the tab at the specified index and update
                         the current node.
        - update_iteration_checkbox: Update the iteration checkbox state based
                                     on pipeline node names.
        - update_current_node: Update the node parameters display for the
                               current pipeline.
        - update_history: Update undo/redo history of an editor.
        - update_pipeline_editors: Update the pipeline editors after changes
                                   to the specified editor.
        - update_scans_list: Update the list of database scans in every editor.
    """

    pipeline_saved = QtCore.pyqtSignal(str)
    node_clicked = QtCore.pyqtSignal(str, Node)
    process_clicked = QtCore.pyqtSignal(str, Process)
    switch_clicked = QtCore.pyqtSignal(str, Switch)

    def __init__(self, project, scan_list, main_window):
        """
        Initialize the pipeline editor tabs.

        :param project: Current project instance in the software.
        :param scan_list: List of selected database files.
        :param main_window: Main application window reference.
        """
        super().__init__()
        self.project = project
        self.main_window = main_window
        self.scan_list = scan_list
        self.undos = {}
        self.redos = {}
        self.previousIndex = 0
        # Configure the visual styling of the tab widget.
        self.setStyleSheet(
            "QTabBar {"
            "    font-size: 12pt;"
            "    font-family: Arial;"
            "    text-align: center;"
            "    color: black;"
            "}"
        )
        self.setTabsClosable(True)
        # Create and configure the default pipeline editor.
        p_e = PipelineEditor(self.project, self.main_window)
        p_e.initialized = False
        p_e.iterated = False
        p_e.iterated_tag = None
        p_e.tag_values_list = []
        p_e.all_tag_values_list = []
        p_e.all_tag_values_list = []
        p_e.node_parameters = {}
        p_e.node_parameters_tmp = {}
        # Connect signals from a pipeline editor to this widget's handlers.
        p_e.node_clicked.connect(self.emit_node_clicked)
        p_e.process_clicked.connect(self.emit_node_clicked)
        p_e.switch_clicked.connect(self.emit_switch_clicked)
        p_e.pipeline_saved.connect(self.emit_pipeline_saved)
        p_e.pipeline_modified.connect(self.update_pipeline_editors)
        p_e.edit_sub_pipeline.connect(self.open_sub_pipeline)
        p_e.open_filter.connect(self.open_filter)
        p_e.export_to_db_scans.connect(self.export_to_db_scans)
        # Setting a default editor called "New Pipeline"
        self.addTab(p_e, "New Pipeline")
        self.undos[p_e] = []
        self.redos[p_e] = []
        # Create and configure the '+' button for adding new tabs.
        add_button = QtWidgets.QToolButton()
        add_button.setText("+")
        add_button.clicked.connect(self.new_tab)
        placeholder_label = QtWidgets.QLabel('Add tabs by pressing "+"')
        self.addTab(placeholder_label, "")
        self.setTabEnabled(1, False)
        self.tabBar().setTabButton(1, QtWidgets.QTabBar.RightSide, add_button)
        # Connect internal widget signals to their handlers.
        self.tabCloseRequested.connect(self.close_tab)
        self.tabBarClicked.connect(self.check_modifications)
        self.currentChanged.connect(self.update_current_node)
        # Initialize the CAPSUL engine configuration.
        self.get_capsul_engine()

    def check_modifications(self, current_index):
        """
        Check if nodes in the current pipeline have been modified.

        Validates modifications when switching between pipeline tabs. Skips
        validation for the special "add new pipeline" tab (last position).

        :param current_index: The index of the tab being switched to.

        :note: The last tab ('+' button) may not have a widget, which is
               handled gracefully by catching AttributeError.
        """

        if current_index == self.previousIndex:
            return

        self.previousIndex = current_index

        try:
            self.widget(current_index).check_modifications()

        except AttributeError:
            # Last tab ('+' button) has no widget to check
            pass

    def close_tab(self, idx):
        """
        Close a tab and its associated editor, prompting to save if modified.

        Removes the specified tab and cleans up its undo/redo history. If the
        tab contains unsaved changes (indicated by " *" suffix), prompts the
        user to save before closing. If all tabs are closed, creates a new
        default pipeline.

        :param idx: index of the tab to close
        """
        filename = os.path.basename(self.get_filename_by_index(idx))
        editor = self.get_editor_by_index(idx)

        # Check if pipeline has unsaved modifications
        if self.tabText(idx).endswith(" *"):
            self.pop_up_close = PopUpClosePipeline(filename)
            self.pop_up_close.save_as_signal.connect(self.save_pipeline)
            self.pop_up_close.exec()
            can_exit = self.pop_up_close.can_exit()

        else:
            can_exit = True

        if not can_exit:
            return

        # Clean up undo/redo history
        self.undos.pop(editor, None)
        self.redos.pop(editor, None)

        # Adjust current tab if necessary
        if idx == self.currentIndex():
            self.set_tab_index(max(0, self.currentIndex() - 1))

        self.removeTab(idx)

        # Create a new default pipeline if all tabs are closed
        if self.count() == 1:
            p_e = PipelineEditor(self.project, self.main_window)
            # Connect signals
            p_e.node_clicked.connect(self.emit_node_clicked)
            p_e.process_clicked.connect(self.emit_node_clicked)
            p_e.switch_clicked.connect(self.emit_switch_clicked)
            p_e.pipeline_saved.connect(self.emit_pipeline_saved)
            p_e.pipeline_modified.connect(self.update_pipeline_editors)
            p_e.edit_sub_pipeline.connect(self.open_sub_pipeline)
            p_e.open_filter.connect(self.open_filter)
            p_e.export_to_db_scans.connect(self.export_to_db_scans)
            # Initialize editor state
            p_e.initialized = False
            p_e.iterated = False
            p_e.iterated_tag = None
            p_e.tag_values_list = []
            p_e.all_tag_values_list = []
            p_e.node_parameters = {}
            p_e.node_parameters_tmp = {}
            # # Add the new tab
            self.insertTab(0, p_e, "New Pipeline")
            self.set_tab_index(0)
            self.undos[p_e] = []
            self.redos[p_e] = []
            self.get_capsul_engine()

        # Update pipeline display (last node settings)
        *_, (node_name, node_obj) = self.get_current_pipeline().nodes.items()
        process = getattr(node_obj, "process", node_obj)
        self.main_window.pipeline_manager.displayNodeParameters(
            node_name, process
        )
        self.update_iteration_checkbox()

    def emit_node_clicked(self, node_name, process):
        """
        Emit the appropriate signal when a node is clicked.

        Emits either `process_clicked` or `node_clicked` signal depending on
        whether the process parameter is a Process instance.

        :param node_name: The name of the clicked node.
        :param process: The process associated with the node. If this is a
                        Process instance, emits `process_clicked`; otherwise
                        emits `node_clicked`.
        """
        signal = (
            self.process_clicked
            if isinstance(process, Process)
            else self.node_clicked
        )
        signal.emit(node_name, process)

    def emit_pipeline_saved(self, filename):
        """
        Update the current tab title and emit the *pipeline_saved* signal.

        :param filename: Path to the saved pipeline file.
        """
        self.setTabText(self.currentIndex(), Path(filename).name)
        self.pipeline_saved.emit(filename)

    def emit_switch_clicked(self, node_name, switch):
        """
        Emit a signal when a switch is toggled.

        :param node_name: The name of the node whose switch was clicked.
        :param switch:  The Switch associated with the node.

        :Emits: switch_clicked: Signal containing the node name and the Switch.
        """
        self.switch_clicked.emit(node_name, switch)

    def export_to_db_scans(self, node_name):
        """
        Export the input of a filter to "database_scans" plug.

        If database_scans already exists as a pipeline parameter, creates a
        link from database_scans to the node's input. Otherwise, exports the
        node's input parameter as database_scans at the pipeline level.

        :param node_name: Name of the node whose input should be exported.

        :note: This method automatically updates the editor scene after
               modification.
        """
        pipeline = self.get_current_pipeline()

        if "database_scans" in pipeline.user_traits():
            pipeline.add_link(f"database_scans->{node_name}.input")

        else:
            pipeline.export_parameter(
                node_name, "input", pipeline_parameter="database_scans"
            )

        self.get_current_editor().scene.update_pipeline()

    def get_capsul_engine(self):
        """
        Configure and return a CapsulEngine for the current pipeline.

        Retrieves a CapsulEngine instance from the MIA configuration and sets
        up the study configuration with project-specific directories. If the
        current pipeline has completion attributes, they are preserved during
        the engine setup process.

        :returns (CapsulEngine): Configured engine instance with study
                                 directories set to the project's raw_data
                                 and derived_data folders.

        :note: This method temporarily saves and restores completion engine
               attributes to prevent loss of configuration when switching
               between pipelines.
        """
        # save completion attributes for the current pipeline (other pipelines
        # will lose their values)
        pipeline = self.get_current_pipeline()
        completion = getattr(pipeline, "completion_engine", None)
        att_values = (
            completion.get_attribute_values().export_to_dict()
            if completion
            else None
        )
        # Configure engine with project directories
        engine = Config.get_capsul_engine()
        study_config = engine.study_config
        project_data_path = Path(self.project.folder).resolve() / "data"
        study_config.input_directory = str(project_data_path / "raw_data")
        study_config.output_directory = str(project_data_path / "derived_data")

        # Restore completion attributes if they existed
        if att_values is not None:
            completion = ProcessCompletionEngine.get_completion_engine(
                pipeline
            )

            if completion:
                completion.get_attribute_values().import_from_dict(att_values)

        return engine

    def get_current_editor(self):
        """
        Return the editor corresponding to the currently selected tab.

        :return: Editor instance for the active tab.
        """
        return self.get_editor_by_index(self.currentIndex())

    def get_current_filename(self):
        """
        Return the relative path of the file last saved in the current editor.

        If the pipeline has never been saved, the current tab title is
        returned.

        :return: The filename for the current editor.
        """
        return self.get_filename_by_index(self.currentIndex())

    def get_current_pipeline(self):
        """
        Return the pipeline associated with the current editor.

        Returns None if no editor or scene is available.

        :return: The pipeline for the current editor
        """
        editor = self.get_current_editor()
        return editor.scene.pipeline if editor and editor.scene else None

    def get_current_tab_name(self):
        """
        Return the name of the currently selected tab.

        Trailing "*" and "&" characters are stripped.

        :return: The current tab name.
        """
        return self.get_tab_name_by_index(self.currentIndex())

    def get_editor_by_file_name(self, file_name):
        """
        Return the editor associated with the given pipeline filename.

        The filename corresponds to the last saved location of the pipeline.

        :param file_name: Name of the file the pipeline was last saved to.

        :return: The editor corresponding to the file name.
        """
        return self.get_editor_by_index(self.get_index_by_filename(file_name))

    def get_editor_by_index(self, idx):
        """
        Retrieve an editor widget by its tab index.

        :param idx: Zero-based index of the editor tab, or None if not found.

        :return: The editor widget at the specified index, or None if idx is
                 None or if the index corresponds to the "add tab" button
                 (last tab) or if index out of range.

        :note: The last tab position is reserved for the "add tab" button and
               does not contain an editor widget.
        """

        if idx is not None and 0 <= idx < self.count() - 1:
            return self.widget(idx)

        return None

    def get_editor_by_tab_name(self, tab_name):
        """
        Retrieve the editor instance associated with a specific tab name.

        :param tab_name (str): The name of the tab to search for.

        :return: The editor instance corresponding to the specified tab name,
                 or None if the tab is not found.

        :raises:
            - ValueError: If tab_name is empty or None.
            - KeyError: If no tab exists with the given name.
        """
        tab_index = self.get_index_by_tab_name(tab_name)

        return self.get_editor_by_index(tab_index)

    def get_filename_by_index(self, idx):
        """
        Get the filename for the pipeline at the specified editor index.

        Returns the relative path to the file where the pipeline was last
        saved. If the pipeline has never been saved, returns the tab title
        instead.

        :param idx: The zero-based index of the editor tab.

        :return: str or None. The filename or tab title if the editor exists,
                 None if no editor exists at the given index.
        """
        editor = self.get_editor_by_index(idx)

        return editor.get_current_filename() if editor is not None else None

    def get_index_by_editor(self, editor):
        """
        Find the tab index for a given editor widget.

        :param editor: The pipeline editor widget to locate.

        :return: The zero-based index of the editor's tab, or None if not
                 found.

        :note: Searches all tabs except the last one (count() - 1).
        """

        return next(
            (
                idx
                for idx in range(self.count() - 1)
                if self.get_editor_by_index(idx) == editor
            ),
            None,
        )

    def get_index_by_filename(self, filename):
        """
        Get the index of the first tab with the specified filename.

        :param filename (str): The pipeline filename to search for. Can be an
                               absolute or relative path; will be normalized
                               to relative.

        :return (int): The zero-based index of the matching tab, or None
                       if no match is found.

        :note: Filenames are internally stored as relative paths for
               consistency. Only searches up to count() - 1 to exclude special
               tabs if any.
        """

        if not filename:
            return None

        # Normalize to relative path for consistent comparison
        filename = os.path.relpath(filename)

        return next(
            (
                idx
                for idx in range(self.count() - 1)
                if self.get_filename_by_index(idx) == filename
            ),
            None,
        )

    def get_index_by_tab_name(self, tab_name):
        """
        Find the index of a tab by its name.

        Searches through all tabs (excluding the last one) to find a tab
        matching the given name.

        :param tab_name (str): The name of the tab to locate.

        :return (int): The zero-based index of the matching tab, or None if no
                       match is found.
        """

        return next(
            (
                idx
                for idx in range(self.count() - 1)
                if self.get_tab_name_by_index(idx) == tab_name
            ),
            None,
        )

    def get_tab_name_by_index(self, idx):
        """
        Get the clean tab name at the specified index.

        Retrieves the tab text at the given index and removes formatting
        characters:
            - Qt keyboard shortcut indicators (ampersands)
            - Unsaved file indicators (trailing " *")

        :param idx: Zero-based index of the tab.

        :return (str): The cleaned tab name, or None if the index is invalid
                       or corresponds to the "add tab" button (last position).
        """

        # Last tab position is reserved for the "add tab" button
        if not 0 <= idx < self.count() - 1:
            return None

        # Get raw tab text and remove Qt keyboard shortcut indicator
        tab_name = self.tabText(idx).replace("&", "", 1)

        # Remove trailing unsaved indicator if present
        return tab_name.removesuffix(" *")

    def has_pipeline_nodes(self):
        """
        Check if any pipeline in the editor tabs contains nodes.

        Iterates through all tab widgets and checks if any pipeline editor
        contains nodes by examining the presence of plugs in the pipeline's
        root node.

        :return (bool): True if at least one pipeline contains nodes,
                        False otherwise.
        """

        return any(
            hasattr(widget := self.widget(idx), "scene")
            and widget.scene.pipeline.nodes[""].plugs
            for idx in range(self.count())
        )

    def load_pipeline(self, filename=None):
        """
        Load a pipeline into the editor.

        Opens a pipeline file in a new or existing tab. If the pipeline is
        already open, switches to that tab. If the current tab is not empty,
        creates a new tab for the pipeline.

        :param filename (str): Path to the pipeline file to load. If None,
                               prompts the user to select a file. Defaults to
                               None.

        :return (None): Returns early on success, or cleans up and returns on
                        failure.

        :note: This method is also called from `open_sub_pipeline` with a
               filename.

        """
        current_editor = self.get_current_editor()
        current_tab_not_empty = len(current_editor.scene.pipeline.nodes) > 1
        new_tab_opened = False
        working_index = None

        # Prompt for filename if not provided
        if filename is None:

            # Open new tab if the current PipelineEditor is not empty
            if current_tab_not_empty:
                self.new_tab()
                working_index = self.currentIndex()
                new_tab_opened = True

            filename = current_editor.load_pipeline("", False)
            self.get_capsul_engine()

        if not filename:

            # User cancelled or no file selected
            if new_tab_opened:
                self.close_tab(working_index)

            return

        # Switch to tab if pipeline already open
        existing_tab = self.get_index_by_filename(filename)

        if existing_tab is not None:
            self.set_tab_index(existing_tab)
            return

        # Create new tab if needed
        if current_tab_not_empty and not new_tab_opened:
            self.new_tab()
            new_tab_opened = True

        working_index = self.currentIndex()
        editor = self.get_editor_by_index(working_index)
        # Load the pipeline
        loaded_filename = editor.load_pipeline(filename)
        self.get_capsul_engine()

        if loaded_filename:
            # Success - update UI
            self.setTabText(working_index, os.path.basename(loaded_filename))
            self.update_scans_list()
            self.main_window.pipeline_manager.run_pipeline_action.setDisabled(
                False
            )
            return

        # Loading failed - clean up
        if new_tab_opened:
            self.close_tab(working_index)

    def load_pipeline_parameters(self):
        """
        Load pipeline parameters for the current editor.

        Opens a file dialog in the user's home directory to select a JSON
        file containing pipeline configuration parameters, then loads those
        parameters into the currently active editor's pipeline.
        """
        self.get_current_editor().load_pipeline_parameters(Path.home())

    def new_tab(self):
        """
        Create and initialize a new pipeline editor tab.

        Creates a new PipelineEditor instance, connects all necessary signals,
        initializes its state, generates a unique tab name, and makes it the
        current tab. The new tab is inserted at the last tab position.

        The tab name follows the pattern "New Pipeline {n}" where n is the
        first available index from 1 to 49.
        """
        # Create and configure new editor
        editor = PipelineEditor(self.project, self.main_window)
        # Connect signals
        signal_mappings = {
            "node_clicked": self.emit_node_clicked,
            "process_clicked": self.emit_node_clicked,
            "switch_clicked": self.emit_switch_clicked,
            "pipeline_saved": self.emit_pipeline_saved,
            "pipeline_modified": self.update_pipeline_editors,
            "edit_sub_pipeline": self.open_sub_pipeline,
            "open_filter": self.open_filter,
            "export_to_db_scans": self.export_to_db_scans,
        }

        for signal_name, slot in signal_mappings.items():
            getattr(editor, signal_name).connect(slot)

        # Initialize state
        editor.initialized = False
        editor.iterated = False
        editor.iterated_tag = None
        editor.tag_values_list = []
        editor.node_parameters = {}
        editor.node_parameters_tmp = {}
        # Generate unique tab name
        tab_name = None

        for idx in range(1, 50):
            name = f"New Pipeline {idx}"

            if not self.get_index_by_tab_name(name):
                tab_name = name
                break

        if tab_name is None:
            logger.info(
                "Maximum number of tabs (50) reached in Pipeline Editor"
            )
            return

        # Initialize undo/redo stacks
        self.undos[editor] = []
        self.redos[editor] = []
        # Insert tab at the last position and switch to it
        insertion_index = self.count() - 1
        self.insertTab(insertion_index, editor, tab_name)
        self.set_tab_index(insertion_index)
        # Finalize setup
        self.get_capsul_engine()
        self.update_iteration_checkbox()

    def open_filter(self, node_name):
        """
        Open a filter widget for the specified pipeline node.

        Creates and displays a FilterWidget instance for filtering data
        associated with the given node in the current pipeline.

        :param node_name: The name of the node to apply filters to.
        """
        node = self.get_current_pipeline().nodes[node_name]
        self.filter_widget = FilterWidget(
            project=self.project,
            node_name=node_name,
            node=node,
            main_window=self.main_window,
        )
        self.filter_widget.show()

    def open_sub_pipeline(self, sub_pipeline):
        """
        Open a sub-pipeline in a new tab.

        This method locates and loads a sub-pipeline by:
            1. Reading the process configuration to find package paths
            2. Determining the pipeline's source package (mia_processes or
               custom)
            3. Resolving the full filesystem path to the pipeline file
            4. Loading the pipeline in a new tab

        :param sub_pipeline: The pipeline object to open. Must have a 'name'
                             attribute and '__module__' attribute for package
                             resolution.
        """
        # Import locally to prevent circular dependencies
        from populse_mia.utils import verCmp

        # Load process configuration
        config = Config()
        config_path = os.path.join(
            config.get_properties_path(), "properties", "process_config.yml"
        )

        try:

            with open(config_path) as stream:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    process_config = yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    process_config = yaml.load(stream)

        except yaml.YAMLError as exc:
            logger.warning(f"Failed to load process configuration: {exc}")
            process_config = {}

        # Determine pipeline source package
        package_name = sub_pipeline.__module__.split(".", 1)[0]

        if package_name == "mia_processes":
            search_paths = [
                os.path.dirname(sys.modules["mia_processes"].__path__[0])
            ]

        else:
            search_paths = process_config.get("Paths", [])

        # Resolve pipeline path
        pipeline_path_components = get_path(
            sub_pipeline.name,
            process_config.get("Packages"),
            None,
            package_name,
        )
        pipeline_name = pipeline_path_components.pop()
        # Locate and load the pipeline file
        pipeline_file = find_filename(
            search_paths, pipeline_path_components, pipeline_name
        )
        self.load_pipeline(pipeline_file)

    def reset_pipeline(self):
        """
        Reset and refresh the currently active editor's pipeline display.

        This triggers an asynchronous update of the pipeline view after a
        short delay (20ms). The update strategy depends on the editor's view
        mode:
            - Logical view: Displays logical representations of nodes, plugs,
                            and links
            - Normal view: Displays standard representations of nodes, plugs,
                           and links

        :note: The update is performed asynchronously via a single-shot timer
               to allow the UI thread to remain responsive.

        """
        self.get_current_editor()._reset_pipeline()

    def save_pipeline(self, new_file_name=None):
        """
        Save the current pipeline to a file.

        Performs either a "Save" or "Save As" operation depending on whether
        a filename is provided. Updates the tab text and emits a signal upon
        successful save.

        :param new_file_name (str): Target filename for the pipeline. If None,
                                    triggers a "Save As" dialog. Defaults to
                                    None.

        :return (str or None): The basename of the saved file if successful,
                               None otherwise.

        Side Effects:
            - Updates the current tab text with the new filename
            - Emits pipeline_saved signal (only for explicit saves)
            - Modifies the editor's _pipeline_filename attribute
        """
        editor = self.get_current_editor()

        # Handle "Save As" action
        if new_file_name is None:
            new_file_name = editor.save_pipeline()

            if not new_file_name:
                return None

            basename = os.path.basename(new_file_name)
            current_basename = os.path.basename(self.get_current_filename())

            if basename != current_basename:
                self.setTabText(self.currentIndex(), basename)

            return basename

        # Handle explicit save with provided filename
        pipeline = self.get_current_pipeline()
        scene = editor.scene
        # Extract node positions, handling both QPointF objects and tuples
        posdict = {}

        for key, value in scene.pos.items():

            try:
                posdict[key] = (value.x(), value.y())

            except AttributeError:
                posdict[key] = (value[0], value[1])

        # Extract node dimensions
        dimdict = {
            key: (value[0], value[1]) for key, value in scene.dim.items()
        }
        # Update pipeline with current scene data
        pipeline.node_dimension = dimdict
        old_pos = pipeline.node_position
        pipeline.node_position = posdict
        # Save to file
        save_pipeline(pipeline, new_file_name)
        # Update editor state
        editor._pipeline_filename = str(new_file_name)
        pipeline.node_position = old_pos
        # Notify and update UI
        basename = os.path.basename(new_file_name)
        self.pipeline_saved.emit(new_file_name)
        self.setTabText(self.currentIndex(), basename)

        return basename

    def save_pipeline_parameters(self):
        """
        Save pipeline parameters from the currently active editor.

        Delegates the save operation to the current editor's save method.
        """
        self.get_current_editor().save_pipeline_parameters()

    def set_current_editor_by_editor(self, editor):
        """
        Set the specified editor as the currently active editor.

        Activates the tab containing the given editor by switching to its
        index.

        :param editor: The editor instance to make active. Must be an editor
                       that exists within one of the managed tabs.
        """
        self.set_tab_index(self.get_index_by_editor(editor))

    def set_current_editor_by_file_name(self, file_name):
        """
        Activate the editor tab containing the specified file.

        Sets the active editor tab to the one associated with the given file
        name, typically used when reopening a previously saved pipeline.

        :parame file_name: The name of the file whose editor tab should be
                           activated.
        """
        self.set_tab_index(self.get_index_by_filename(file_name))

    def set_current_editor_by_tab_name(self, tab_name):
        """
        Activate the editor tab with the specified name.

        :param tab_name: The display name of the tab to activate.
        """

        if (index := self.get_index_by_tab_name(tab_name)) is not None:
            self.set_tab_index(index)

        else:
            logger.warning(f"No tab found with name: {tab_name}")

    def set_tab_index(self, index):
        """
        Activate the tab at the specified index and update the current node.

        Sets the active tab, stores it as the previous index for navigation
        history, and updates the current node state for the newly active
        editor.

        :param index: The zero-based index of the tab to activate.
        """
        self.setCurrentIndex(index)
        self.previousIndex = index
        self.update_current_node()

    def update_iteration_checkbox(self):
        """
        Update the iteration checkbox state based on pipeline node names.

        Sets the iteration checkbox to checked if any pipeline node has
        'iterated_' in its key name, otherwise sets it to unchecked. If no
        valid pipeline exists or the pipeline lacks nodes, the checkbox is
        unchecked.
        """
        pipeline = self.get_current_pipeline()
        checkbox = (
            self.main_window.pipeline_manager.iterationTable.check_box_iterate
        )

        # Default to unchecked if pipeline is invalid or has no nodes
        if not pipeline or not hasattr(pipeline, "nodes"):
            checkbox.setCheckState(Qt.Qt.Unchecked)
            return

        # Check if any node key contains 'iterated_'
        has_iteration = any(
            "iterated_" in key for key in pipeline.nodes.sortedKeys
        )
        checkbox.setCheckState(
            Qt.Qt.Checked if has_iteration else Qt.Qt.Unchecked
        )

    def update_current_node(self):
        """Update the node parameters display for the current pipeline.

        Refreshes the UI to display parameters for all nodes in the current
        pipeline, updates user button states, iteration checkbox, and iterated
        tag display.
        """
        pipeline = self.get_current_pipeline()
        pipeline_manager = self.main_window.pipeline_manager

        # Display parameters for all nodes in the pipeline
        if pipeline and hasattr(pipeline, "nodes"):

            for node_name, node in pipeline.nodes.items():
                pipeline_manager.displayNodeParameters(node_name, node.process)

        # Update UI state
        pipeline_manager.update_user_buttons_states()
        self.update_iteration_checkbox()
        # Update iterated tag if an editor is active
        current_editor = self.get_current_editor()

        if current_editor:
            pipeline_manager.iterationTable.update_iterated_tag(
                current_editor.iterated_tag
            )

    def update_history(self, editor):
        """
        Update the undo/redo history for the specified editor.

        Saves the editor's current undo and redo stacks and marks the active
        tab as modified by appending an asterisk to its title if not already
        present.

        :param editor: The editor instance whose history should be saved.

        :note: This method assumes the editor is in the currently active tab.
        """
        self.undos[editor] = editor.undos
        self.redos[editor] = editor.redos
        current_tab_name = self.get_current_tab_name()

        if not current_tab_name.endswith(" *"):
            self.setTabText(self.currentIndex(), f"{current_tab_name} *")

    def update_pipeline_editors(self, editor):
        """
        Update the pipeline editors after changes to the specified editor.

        Synchronizes the editor's undo/redo history and refreshes the scans
        list to reflect any modifications made in the pipeline editor.

        :param editor: The editor instance that was modified.
        """
        self.update_history(editor)
        self.update_scans_list()

    def update_scans_list(self):
        """
        Update the list of database scans in every pipeline editor.

        Iterates through all editor tabs (excluding the last tab, reserved for
        the "add tab" button) and updates the database_scans attribute for
        each pipeline that supports it. Also refreshes the iteration checkbox
        state after updating.

        :note: Silently continues if updating a pipeline fails, logging the
               error without interrupting the update process for remaining
               pipelines.
        """

        for i in range(self.count() - 1):
            pipeline = self.widget(i).scene.pipeline

            if not pipeline.trait("database_scans"):
                continue

            try:
                pipeline.database_scans = self.scan_list

            except Exception as e:
                logger.warning(
                    f"Failed to update database_scans for "
                    f"pipeline at index {i}: {e}",
                    exc_info=True,
                )

        self.update_iteration_checkbox()


def find_filename(paths_list, packages_list, file_name):
    """
    Locate a pipeline file within configured paths.

    Searches for a file with the given name (with .py or .xml extension) by
    traversing through base paths combined with package subdirectories.
    Performs case-insensitive matching to handle filesystem sensitivity issues.

    :param paths_list: Base directory paths from process_config.yml
    :param packages_list: Ordered list of package subdirectories to traverse
    :param file_name: Base name of the sub-pipeline file (without extension)

    :return: Absolute path to the matched file, or None if not found
    """
    extensions = (".py", ".xml")

    for base_path in paths_list:
        # Build the target directory path
        target_dir = Path(base_path).joinpath(*packages_list)

        if not target_dir.is_dir():
            continue

        # Search for matching files with case-insensitive comparison
        for file_path in target_dir.iterdir():

            if not file_path.is_file():
                continue

            stem_lower = file_path.stem.lower()
            suffix_lower = file_path.suffix.lower()

            if stem_lower == file_name.lower() and suffix_lower in extensions:
                return str(file_path)

    return None


def get_path(name, dictionary, prev_paths=None, pckg=None):
    """
    Recursively search for a module name inside a nested dictionary structure
    and return its full path as a list of keys.

    The tree is assumed to be a mapping where:
        - Intermediate nodes are dictionaries (packages),
        - Leaf nodes are strings (module names).

    :param name (str): Name of the module to locate in the tree.
    :param dictionary (dict): The nested dictionary representing the tree
                              structure.
    :param prev_paths (list[str]): The accumulated path leading to the current
                                   dictionary. If None, a new path list is
                                   created.
    :param pckg (str): If provided, navigation starts inside that package name.

    :return (list[str]): A list of keys representing the path to the module, or
                         None if the module is not found.
    """

    # Initialize accumulated path
    if prev_paths is None:
        prev_paths = []

        if pckg is not None:
            prev_paths.append(pckg)
            dictionary = dictionary.get(pckg, {})

    # Copy because new_paths will be mutated
    new_paths = prev_paths.copy()

    for key, value in dictionary.items():

        # Leaf: module name
        if isinstance(value, str):

            if key == name:
                return new_paths + [key]

            continue

        # Branch: subpackage
        new_paths.append(key)
        result = get_path(name, value, new_paths)

        if result is not None:
            return result

        # Reset new_paths when going back up
        new_paths = prev_paths.copy()

    # Not found in this branch
    return None


def save_pipeline(pipeline, filename):
    """
    Save a pipeline to a file in the appropriate format.

    Automatically detects the output format based on the file extension.
    Supported formats are Python source (.py) and XML (.xml). If no
    recognized extension is provided, defaults to Python format.

    :param pipeline: The pipeline object to serialize and save.
    :param filename: Path to the output file. The extension determines
                     the output format (.py or .xml).

    :note: Unrecognized extensions will default to Python source format (.py)

    Examples:
        >>> save_pipeline(my_pipeline, "model.py")
        >>> save_pipeline(my_pipeline, "config.xml")
        >>> save_pipeline(my_pipeline, "output")  # Defaults to .py format
    """
    FORMATS = {
        ".py": save_py_pipeline,
        ".xml": save_xml_pipeline,
    }

    suffix = Path(filename).suffix.lower()
    writer = FORMATS.get(suffix, save_py_pipeline)
    writer(pipeline, filename)


def values(d):
    """
    Extract all values from a dictionary as a list.

    :param d (dict): The dictionary to extract values from.

    :return (list): A list containing all values from the dictionary.
    """
    return list(d.values())
