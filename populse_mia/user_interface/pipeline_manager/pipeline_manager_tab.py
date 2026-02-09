"""
Module to define pipeline manager tab appearance, settings and methods.

Contains:
    Class:
        - PipelineManagerTab
        - RunProgress
        - RunWorker
        - StatusWidget
    Function:
        - protected_logging

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# Other imports
import contextlib
import copy
import datetime
import functools
import importlib
import io
import json
import logging
import math
import os
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

# Soma_workflow import
import soma_workflow.constants as swconstants
import traits.api as traits

# Capsul imports
from capsul.api import (
    NipypeProcess,
    Pipeline,
    PipelineNode,
    Process,
    ProcessNode,
    get_process_instance,
)
from capsul.attributes.completion_engine import ProcessCompletionEngine
from capsul.engine import WorkflowExecutionError
from capsul.pipeline import pipeline_tools
from capsul.pipeline.pipeline_workflow import workflow_from_pipeline
from capsul.pipeline.process_iteration import ProcessIteration
from matplotlib.backends.qt_compat import QtWidgets

# PyQt5 imports
from PyQt5 import Qt, QtCore
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QMovie
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

# Soma_base import
from soma.controller.trait_utils import is_file_trait
from soma.qt_gui.qtThread import QtThreadCall
from traits.api import TraitListObject, Undefined

# Populse_mia imports
from populse_mia.data_manager import (
    BRICK_EXEC,
    BRICK_EXEC_TIME,
    BRICK_INIT,
    BRICK_INIT_TIME,
    BRICK_INPUTS,
    BRICK_NAME,
    BRICK_OUTPUTS,
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    COLLECTION_HISTORY,
    COLLECTION_INITIAL,
    HISTORY_BRICKS,
    HISTORY_PIPELINE,
    TAG_BRICKS,
    TAG_CHECKSUM,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_TYPE,
    TYPE_MAT,
    TYPE_NII,
    TYPE_TXT,
    TYPE_UNKNOWN,
)
from populse_mia.software_properties import Config
from populse_mia.user_interface.pipeline_manager.iteration_table import (
    IterationTable,
)
from populse_mia.user_interface.pipeline_manager.node_controller import (
    CapsulNodeController,
    NodeController,
)
from populse_mia.user_interface.pipeline_manager.pipeline_editor import (
    PipelineEditorTabs,
)
from populse_mia.user_interface.pipeline_manager.process_library import (
    ProcessLibraryWidget,
)
from populse_mia.user_interface.pipeline_manager.process_mia import ProcessMIA
from populse_mia.user_interface.pop_ups import PopUpInheritanceDict

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def protected_logging():
    """
    Context manager that preserves logging configuration across soma-workflow
    interference.

    This context manager creates a snapshot of all logger configurations
    before execution and intelligently restores them afterwards. It preserves
    any new handlers or filters that were added during execution while
    ensuring original configurations are restored.

    The protection covers:
        - All named loggers in the logger hierarchy
        - The root logger
        - Handler and filter lists (with intelligent merging)
        - Logger levels, disabled state, and propagation settings

    Usage:
        with protected_logging():
            # Code that might interfere with logging
            some_workflow_operation()
            # Any new handlers/filters added here are preserved
    """
    # Create a comprehensive backup of the logging state
    loggers_backup = {}

    # Backup all named loggers
    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        loggers_backup[name] = {
            "handlers": list(logger.handlers),  # copy handler list
            "filters": list(logger.filters),  # copy filters
            "level": logger.level,
            "disabled": logger.disabled,
            "propagate": logger.propagate,
        }

    # Backup root logger separately
    root = logging.getLogger()
    loggers_backup["root"] = {
        "handlers": list(root.handlers),
        "filters": list(root.filters),
        "level": root.level,
        "disabled": root.disabled,
        "propagate": root.propagate,
    }

    try:
        yield

    finally:

        # Restore configs but merge handlers/filters
        for name, config in loggers_backup.items():

            logger = (
                logging.getLogger()
                if name == "root"
                else logging.getLogger(name)
            )

            # Merge handlers: keep existing, re-add missing originals
            existing_handlers = {id(h): h for h in logger.handlers}

            for h in config["handlers"]:

                if id(h) not in existing_handlers:
                    logger.addHandler(h)

            # Merge filters the same way
            existing_filters = {id(f): f for f in logger.filters}

            for f in config["filters"]:

                if id(f) not in existing_filters:
                    logger.addFilter(f)

            # Restore scalar properties
            logger.setLevel(config["level"])
            logger.disabled = config["disabled"]
            logger.propagate = config["propagate"]


class PipelineManagerTab(QWidget):
    """
    Widget that handles the Pipeline Manager tab.

    .. Methods:
        - _register_node_io_in_database: Register node input and output values
                                         in the database
        - _set_anim_frame: Callback that updates the pipeline status action
                           icon
        - _should_register_plug: Determine if a plug should be registered
        - add_plug_value_to_database: Add the plug value to the database
        - ask_iterated_pipeline_plugs: Display a config dialog for pipeline
                                       plug iteration and database connections
        - build_iterated_pipeline: Build a new pipeline with an iteration node
        - check_requirements: Return the configuration of a pipeline as
                              required
        - cleanup_older_init: Remove non-existent entries from the databrowser
        - complete_pipeline_parameters: Complete pipeline parameters
        - controller_value_changed: Update history when a pipeline node is
                                    changed
        - displayNodeParameters: Display the node controller when a node is
                                 clicked
        - finish_execution: Handle pipeline execution completion and update UI
                            state
        - garbage_collect: Clean up obsolete data and maintain database
                           consistency
        - get_capsul_engine: Retrieve and configure a Capsul engine from the
                             pipeline editor
        - get_pipeline_or_process: Get the pipeline or its single unconnected
                                   process node
        - get_missing_mandatory_parameters: Check on missing parameters for
                                            each job
        - initialize: Clean previous initialization then initialize the current
                      pipeline
        - init_pipeline: Initialize the current pipeline of the pipeline
                         editor
        - layout_view : Initialize layout for the pipeline manager
        - loadParameters: Load pipeline parameters to the current pipeline of
                          the pipeline editor
        - loadPipeline: Load a pipeline to the pipeline editor
        - postprocess_pipeline_execution: Operations to be performed after a
                                          run has been completed
        - redo: Redo the last undone action on the current pipeline editor
        - register_completion_attributes: Register completion attributes for a
                                          given pipeline in the project
                                          database
        - remove_progress: Remove and clean up the progress widget
        - runPipeline: Run the current pipeline of the pipeline editor
        - saveParameters: Save the pipeline parameters of the the current
                          pipeline of the pipeline editor
        - savePipeline: Save the current pipeline of the pipeline editor
        - save_pipeline_as: Save the current pipeline of the pipeline editor
                            under another name
        - show_status: Display the execution status window with runtime
                       information.
        - stop_execution: Interrupt pipeline execution gracefully
        - undo: Undo the last action made on the current pipeline editor
        - update_auto_inheritance: Get database tags for output parameters
        - update_inheritance: Update the inheritance dictionary for a process
                              node in a pipeline execution
        - update_node_list: Update the list of nodes in workflow
        - updateProcessLibrary: Update the library of processes when a
                                pipeline is saved
        - update_project: Update the project attribute of several objects
        - update_scans_list: Update the user-selected list of scans
        - update_user_buttons_states: Update the visibility of
                                      initialize / run / save actions
                                      according to the pipeline state
        - update_user_mode: Update the visibility of widgets / actions
                            depending of the chosen mode

    """

    item_library_clicked = pyqtSignal(str)

    def __init__(self, project, scan_list, main_window):
        """
        Initialize the Pipeline Manager tab.

        The Pipeline Manager provides a comprehensive interface for creating,
        editing, and executing data processing pipelines. It integrates
        process libraries, pipeline editors, node controllers, and iteration
        tables to manage complex data analysis workflows.

        :param project: The current project instance containing database and
                        configuration
        :param scan_list: List of selected database files to process. If None
                          or empty, defaults to all documents in the current
                          collection
        :param main_window: Main application window instance for UI integration
        """
        super().__init__()
        # Initialize core attributes
        self.project = project
        self.main_window = main_window
        self.inheritance_dict = None
        self.workflow = None
        # Initialize state flags
        self.init_clicked = False
        self.test_init = False
        self.ignore_node = False
        self.enable_progress_bar = False
        # Initialize collections
        self.brick_list = []
        self.node_list = []
        # This list is the list of scans contained in the iteration table.
        # If it is empty, the scan list in the Pipeline Manager is the scan
        # list from the data_browser
        self.iteration_table_scans_list = []
        self.key = {}
        self.ignore = {}
        # Configure node controller based on version
        config = Config()
        node_controller_class = (
            CapsulNodeController
            if not config.isControlV1()
            else NodeController
        )
        # Set up MIA processing project reference
        ProcessMIA.project = project

        # Initialize the scan list from database or provided list
        with self.project.database.data() as database_data:
            self.scan_list = (
                scan_list
                if scan_list
                else database_data.get_document_names(COLLECTION_CURRENT)
            )

        # Initialize main UI components
        self.processLibrary = ProcessLibraryWidget(self.main_window)
        self.pipelineEditorTabs = PipelineEditorTabs(
            self.project, self.scan_list, self.main_window
        )
        # Iteration table
        self.iterationTable = IterationTable(
            self.project, self.scan_list, self.main_window
        )
        # Layout components
        self.verticalLayout = QVBoxLayout(self)
        # Initialize toolbar
        self.menu_toolbar = QToolBar()
        self.tags_menu = QMenu()
        self.tags_tool_button = QtWidgets.QToolButton()
        self.scrollArea = QScrollArea()
        # Initialize Qt layout
        self.hLayout = QHBoxLayout()
        self.splitterRight = QSplitter(Qt.Qt.Vertical)
        self.splitter0 = QSplitter(Qt.Qt.Vertical)
        self.splitter1 = QSplitter(Qt.Qt.Horizontal)
        # Initialize and configure the node controller
        self.nodeController = node_controller_class(
            self.project, self.scan_list, self, self.main_window
        )

        with self.project.database.data() as database_data:
            self.nodeController.visibles_tags = database_data.get_shown_tags()

        # Setup actions and toolbar
        sources_images_dir = config.getSourceImageDir()
        # Pipeline management actions
        self.load_pipeline_action = QAction("Load pipeline", self)
        self.load_pipeline_action.triggered.connect(self.loadPipeline)
        self.save_pipeline_action = QAction("Save pipeline", self)
        self.save_pipeline_action.triggered.connect(self.savePipeline)
        self.save_pipeline_as_action = QAction("Save pipeline as", self)
        self.save_pipeline_as_action.triggered.connect(self.save_pipeline_as)
        # Parameter management actions
        self.load_pipeline_parameters_action = QAction(
            "Load pipeline parameters", self
        )
        self.load_pipeline_parameters_action.triggered.connect(
            self.loadParameters
        )
        self.save_pipeline_parameters_action = QAction(
            "Save pipeline parameters", self
        )
        self.save_pipeline_parameters_action.triggered.connect(
            self.saveParameters
        )
        # Execution actions
        self.run_pipeline_action = QAction(
            QIcon(os.path.join(sources_images_dir, "run32.png")),
            "Run pipeline",
            self,
        )
        self.run_pipeline_action.triggered.connect(self.runPipeline)
        self.stop_pipeline_action = QAction(
            QIcon(os.path.join(sources_images_dir, "stop32.png")), "Stop", self
        )
        self.stop_pipeline_action.triggered.connect(self.stop_execution)
        self.stop_pipeline_action.setDisabled(True)
        self.show_pipeline_status_action = QAction(
            QIcon(os.path.join(sources_images_dir, "gray_cross.png")),
            "Status",
            self,
        )
        self.show_pipeline_status_action.triggered.connect(self.show_status)
        self.garbage_collect_action = QAction(
            QIcon(os.path.join(sources_images_dir, "garbage_collect.png")),
            "Cleanup",
            self,
        )
        self.garbage_collect_action.triggered.connect(self.garbage_collect)
        self.garbage_collect_action.setToolTip(
            "Cleanup obsolete items in the database (pipeline inits, "
            "obsolete data...). Not needed in normal situations, but useful "
            "after a reconnection (client/server) or application crash."
        )
        # Initialize connection state
        self.startedConnection = None
        # Initialize the layout structure
        self.layout_view()
        # Connect signals
        # Process library signals
        self.processLibrary.process_library.item_library_clicked.connect(
            self.item_library_clicked
        )
        # Pipeline editor signals
        signal_connections = [
            (self.pipelineEditorTabs.node_clicked, self.displayNodeParameters),
            (
                self.pipelineEditorTabs.process_clicked,
                self.displayNodeParameters,
            ),
            (
                self.pipelineEditorTabs.switch_clicked,
                self.displayNodeParameters,
            ),
            (
                self.pipelineEditorTabs.pipeline_saved,
                self.updateProcessLibrary,
            ),
        ]

        for signal, slot in signal_connections:
            signal.connect(slot)

        # Iteration table signals
        self.iterationTable.iteration_table_updated.connect(
            self.update_scans_list
        )
        # To undo/redo
        self.nodeController.value_changed.connect(
            self.controller_value_changed
        )

    def _register_node_io_in_database(
        self, job, node, pipeline_name="", history_id=""
    ):
        """
        Register node input and output values in the database.

        This method processes the inputs and outputs of a given node,
        associates them with a job, and updates the database with the
        appropriate values. It handles leaf processes, user-defined traits,
        and completion attributes, ensuring that initialization data is
        recorded correctly.

        :param job: Job object containing parameter values and unique
                    identifier (UUID).
        :param node: Node instance (Process, Pipeline, or custom node) to
                     register.
        :param pipeline_name (str, optional): Name of the containing pipeline,
                                              if any.
        :param history_id (str, optional): Database history entry identifier.
                                           Defaults to an empty string.

        Note:
            Pipeline and PipelineNode instances are skipped as only leaf
            processes produce meaningful output data.

        """

        def _serialize_for_json(item):
            """
            Serialize objects to JSON-compatible format.

            Handles special types like Undefined values, temporary paths,
            datetime objects, and sets for safe JSON storage.

            :param item: The object to be serialized.

            :return: JSON-serializable representation of the item.

            :raises TypeError: If item type cannot be serialized.
            """

            import soma_workflow.client as swc

            # Handle special cases
            if item in (Undefined, [Undefined]):
                return "<undefined>"

            if isinstance(item, swc.TemporaryPath):
                return "<temp>"

            if isinstance(item, datetime.datetime):
                return str(item)

            if isinstance(item, set):
                return list(item)

            raise TypeError(f"Cannot serialize object of type {type(item)}")

        # Skip pipeline nodes as they don't produce direct output
        if isinstance(node, (PipelineNode, Pipeline)):
            # only leaf processes produce output data
            return

        # Extract the actual process
        process = node.process if isinstance(node, ProcessNode) else node

        if isinstance(process, Process):
            inputs = process.get_inputs()
            outputs = process.get_outputs()

            # Handle ProcessMIA/Process_Mia specific outputs
            if hasattr(process, "list_outputs") and hasattr(
                process, "outputs"
            ):
                outputs.update(process.outputs)

        else:
            # Handle custom nodes with user-defined traits
            user_traits = node.user_traits()
            outputs = {
                param: node.get_plug_value(param)
                for param, trait in user_traits.items()
                if trait.output
            }
            inputs = {
                param: node.get_plug_value(param)
                for param, trait in user_traits.items()
                if not trait.output
            }

        # Update I/O values from job parameters
        def _update_values_from_job(values_dict: dict) -> None:
            """
            Update values dictionary with job parameters.

            :param values_dict: Dictionary of input or output values to
                                update.
            """

            for key in values_dict:
                if key not in job.param_dict:
                    continue

                job_value = job.param_dict[key]

                if isinstance(job_value, list):

                    for i, value in enumerate(job_value):

                        if i < len(values_dict[key]):
                            values_dict[key][i] = value

                else:
                    values_dict[key] = job_value

        _update_values_from_job(inputs)
        _update_values_from_job(outputs)

        # Get completion attributes
        attributes = {}
        completion = ProcessCompletionEngine.get_completion_engine(node)

        if completion:
            attributes = completion.get_attribute_values().export_to_dict()

        # Serialize I/O values for database storage
        def _serialize_dict_values(data_dict: dict) -> dict:
            """
            Serialize all values in a dictionary for JSON compatibility.

            :param data_dict: Dictionary with values to serialize.
            """
            serialized = {}

            for key, value in data_dict.items():

                try:
                    # Use JSON roundtrip to ensure serialization works
                    json_str = json.dumps(value, default=_serialize_for_json)
                    serialized[key] = json.loads(json_str)

                except (TypeError, ValueError) as e:
                    # Log warning and skip problematic values
                    logger.warning(f"Warning: Could not serialize {key}: {e}")
                    serialized[key] = "<serialization_error>"

            return serialized

        serialized_inputs = _serialize_dict_values(inputs)
        serialized_outputs = _serialize_dict_values(outputs)

        # Register output values in database
        node_name = node.name
        # Updating the database with output values obtained from
        # initialisation. If a plug name is in outputs['notInDb'], then
        # the corresponding output value is not added to the database.
        excluded_outputs = set(serialized_outputs.get("notInDb", []))

        for plug_name, plug_value in serialized_outputs.items():

            # Skip if not a valid process trait or has high user level
            if not self._should_register_plug(process, plug_name):
                continue

            # Skip undefined values and excluded outputs
            if plug_value == "<undefined>" or plug_name in excluded_outputs:
                continue

            # Construct full node name
            full_name = (
                f"{pipeline_name}.{node_name}" if pipeline_name else node_name
            )

            # Register plug value in database
            trait = process.trait(plug_name)
            self.add_plug_value_to_database(
                p_value=plug_value,
                brick_id=job.uuid,
                history_id=history_id,
                node_name=node_name,
                plug_name=plug_name,
                full_name=full_name,
                job=job,
                trait=trait,
                inputs=serialized_inputs,
                attributes=attributes,
            )

        with self.project.database.data(write=True) as database_data:
            # Update brick initialization state in database.
            database_data.set_value(
                collection_name=COLLECTION_BRICK,
                primary_key=job.uuid,
                values_dict={
                    BRICK_INPUTS: serialized_inputs,
                    BRICK_OUTPUTS: serialized_outputs,
                    BRICK_INIT: "Done",
                },
            )

    def _set_anim_frame(self):
        """
        Update the pipeline status action icon with the current animation
        frame.

        This method serves as a callback that synchronizes the animated movie's
        current frame with the status action's icon, creating a smooth animated
        icon effect in the UI.

        Note:
        This method is typically connected to QMovie's frameChanged signal
        to automatically update the icon as the animation progresses.
        """
        current_pixmap = self._mmovie.currentPixmap()
        self.show_pipeline_status_action.setIcon(QIcon(current_pixmap))

    def _should_register_plug(self, process, plug_name: str) -> bool:
        """
        Determine if a plug should be registered in the database.

        :param process: Process instance
        :param plug_name (str): Name of the plug to check

        :return: True if plug should be registered, False otherwise
        """

        if plug_name not in process.traits():
            return False

        trait = process.trait(plug_name)

        return trait.userlevel is None or trait.userlevel <= 0

    def add_plug_value_to_database(
        self,
        p_value,
        brick_id,
        history_id,
        node_name,
        plug_name,
        full_name,
        job,
        trait,
        inputs,
        attributes,
    ):
        """
        Add plug value(s) to the database with proper metadata and
        inheritance.

        This method handles adding file-based plug values to a project
        database, managing inheritance of metadata tags from input files,
        and resolving ambiguities when multiple parent files exist.

        :param p_value: The plug value - either a single file path (str) or
                        list of file paths. Can also be special values like
                        "<undefined>" or Undefined.
        :param brick_id (str): UUID of the brick in the database.
        :param history_id (str): UUID of the processing history in the
                                 database.
        :param node_name (str): Name of the processing node.
        :param plug_name (str): Name of the specific plug/parameter.
        :param full_name (str): Full hierarchical name including parent
                                bricks. Equals node_name if no parent exists.
        :param job (Job): Job object containing the plug, may have
                          inheritance dictionaries.
        :param trait (Trait): Handler for the plug trait or sub-trait for list
                              elements. Used to validate value types (file vs
                              non-file).
        :param inputs (dict): Input parameter values for the process/node.
        :param attributes (dict): Completion engine attributes to be applied
                                  to all outputs.

        Notes:
            - Recursively processes list values by calling itself on each
              element
            - Only processes file-type traits within the project folder
            - Handles tag inheritance from parent files using inheritance_dict
              and auto_inheritance_dict from the job
            - May prompt user to resolve ambiguous inheritance scenarios
            - Automatically determines file types based on extensions
            - Updates both CURRENT and INITIAL database collections

        :raises: May raise database-related exceptions during document
                 operations.
        """

        # Recursive case: list of values
        if isinstance(p_value, (list, TraitListObject)):
            inner_trait = trait.handler.inner_traits()[0]

            for index, element in enumerate(p_value):
                distributed = {}

                for key, value in attributes.items():

                    if isinstance(value, list) and value:
                        # Use element at index, or last element if index
                        # exceeds length
                        distributed[key] = (
                            value[index] if index < len(value) else value[-1]
                        )

                    else:
                        distributed[key] = value

                self.add_plug_value_to_database(
                    p_value=element,
                    brick_id=brick_id,
                    history_id=history_id,
                    node_name=node_name,
                    plug_name=plug_name,
                    full_name=full_name,
                    job=job,
                    trait=inner_trait,
                    inputs=inputs,
                    attributes=distributed,
                )

            return

        # Skip non-file values or undefined values
        invalid_values = ("<undefined>", Undefined, [Undefined])

        if (
            not is_file_trait(trait, allow_dir=True)
            or p_value in invalid_values
        ):
            return

        # Process file path and validate it's within project
        p_val = Path(p_value).resolve()
        project_folder = Path(self.project.folder).resolve()

        if not p_val.is_relative_to(project_folder):
            # file name is outside the project folder: don't index it in the
            # database
            logger.info(
                "Path %s is outside the project folder: "
                "don't index it in the database!",
                p_val,
            )
            return

        # Fit p_value to the database's syntax
        processed_path = str(p_val.relative_to(project_folder))

        # If the file name is already in the database,
        # no exception is raised, but the user is warned
        with self.project.database.schema() as schema:

            with schema.data() as database_data:
                already_exists = database_data.has_document(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=processed_path,
                )

                if already_exists:
                    logger.info("Path %s already in database!", processed_path)

                else:
                    database_data.add_document(
                        COLLECTION_CURRENT, processed_path
                    )
                    database_data.add_document(
                        COLLECTION_INITIAL, processed_path
                    )

                # Determine file type based on extension
                name = (
                    processed_path[:-3]
                    if processed_path.endswith(".gz")
                    else processed_path
                )
                ext = os.path.splitext(name)[1]

                type_mapping = {
                    (".nii", ".mnc", ".ima", ".img"): TYPE_NII,
                    (".mat",): TYPE_MAT,
                    (".txt",): TYPE_TXT,
                }
                file_type = TYPE_UNKNOWN

                for extensions, p_type in type_mapping.items():

                    if ext in extensions:
                        file_type = p_type

                # Determine from which value the output should inherit its
                # database tags. Each process may have an "inheritance_dict"
                # prepared using list_outputs() during completion, if this
                # method is available. If it is not present, or if the
                # parameter value is not found there, we can refer to the
                # "auto_inheritance_dict," which automatically maps outputs
                # to inputs. If there is no ambiguity, we can proceed with
                # automatic processing.
                # Get inheritance dictionaries from job
                inheritance_dict = getattr(job, "inheritance_dict", {})
                auto_inheritance_dict = getattr(
                    job, "auto_inheritance_dict", {}
                )
                parent_files, own_tags, tags2del = (
                    inheritance_dict.get(p_value),
                    None,
                    None,
                )
                # The inheritance_dict and auto_inheritance_dict dictionaries
                # can take several forms.
                # inheritance_dict:
                # Keys are output filenames (str).
                # Values may be:
                # - an input filename: get the tags from it (deprecated)
                # - or a dict
                #   {   'own_tags': list of dict of additional / updated tags
                #       'tags2del': list of tags (str) whose value will be
                #                   deleted
                #       'parent': input_filename, (optional)
                #   }
                # auto_inheritance_dict:
                # - if there is no ambiguity :
                #    key: value of the output file (string)
                #    value: value of the input file (string)
                # - if ambiguous :
                #    key: output plug value (string)
                #    value: a dict: with key / value corresponding to each
                #                   possible input file
                #               => key: name of the input plug
                #               => value: value of the input plug
                # Handle different formats of inheritance_dict values
                if isinstance(parent_files, dict):
                    own_tags = parent_files.get("own_tags")
                    tags2del = parent_files.get("tags2del")
                    parent = parent_files.get("parent")
                    parent_files = (
                        {None: parent} if parent is not None else None
                    )

                elif isinstance(parent_files, str):
                    parent_files = {None: parent_files}

                # Fall back to auto_inheritance_dict if needed
                if parent_files is None:
                    auto_parent = auto_inheritance_dict.get(p_value, {})
                    parent_files = (
                        {None: auto_parent}
                        if isinstance(auto_parent, str)
                        else auto_parent
                    )

                field_names = database_data.get_field_names(COLLECTION_CURRENT)
                all_cvalues, all_ivalues = {}, {}

                # get all tags values for inputs
                for param, parent_file in (parent_files or {}).items():
                    parent_val = Path(parent_file).resolve()

                    try:
                        rel_path = str(parent_val.relative_to(project_folder))

                    except ValueError:
                        # parent_file is outside the project folder
                        continue

                    if rel_path == processed_path:
                        # output is one of the inputs: OK nothing to be done.
                        all_cvalues, all_ivalues = {}, {}
                        break

                    current_doc = database_data.get_document(
                        collection_name=COLLECTION_CURRENT,
                        primary_keys=rel_path,
                    )

                    if not current_doc:
                        continue

                    banished_tags = {
                        TAG_TYPE,
                        TAG_BRICKS,
                        TAG_CHECKSUM,
                        TAG_FILENAME,
                        TAG_HISTORY,
                    }
                    cvalues = {
                        field: current_doc[0][field]
                        for field in field_names
                        if field not in banished_tags
                    }
                    initial_doc = database_data.get_document(
                        collection_name=COLLECTION_INITIAL,
                        primary_keys=rel_path,
                    )
                    ivalues = {
                        field: initial_doc[0][field] for field in cvalues
                    }
                    all_cvalues[param] = cvalues
                    all_ivalues[param] = ivalues

                # If there are several possible inputs: there is more work
                if (
                    not self.ignore_node
                    and len(all_cvalues) > 1
                    and (node_name not in self.ignore)
                    and (f"{node_name}.{plug_name}" not in self.ignore)
                ):
                    # If all inputs have the same tags set: then pick either
                    # of them, they are all the same, there is no ambiguity
                    eq = all(
                        cv == next(iter(all_cvalues.values()))
                        for cv in list(all_cvalues.values())[1:]
                    )
                    eq &= (
                        all(
                            iv == next(iter(all_ivalues.values()))
                            for iv in list(all_ivalues.values())[1:]
                        )
                        if eq
                        else False
                    )

                    if eq:
                        # all values equal, no ambiguity
                        all_cvalues = {
                            k: v for k, v in [next(iter(all_cvalues.items()))]
                        }
                        all_ivalues = {
                            k: v for k, v in [next(iter(all_ivalues.items()))]
                        }

                    else:
                        # ambiguous inputs -> output
                        # ask the user, or use previously setup answers.

                        # FIXME: There is a GUI dialog here, involving user
                        #        interaction. This should probably be avoided
                        #        here in a processing loop. Some pipelines,
                        #        especially with iterations, may ask many
                        #        many questions to users. These should be
                        #        worked on earlier.

                        if node_name in self.key:
                            param = self.key[node_name]
                            value = parent_files[param]
                            inheritance_dict[p_value] = value
                            all_cvalues = {param: all_cvalues[param]}
                            all_ivalues = {param: all_ivalues[param]}

                        elif f"{node_name}.{plug_name}" in self.key:
                            param = self.key[f"{node_name}.{plug_name}"]
                            value = parent_files[param]
                            inheritance_dict[p_value] = value
                            all_cvalues = {param: all_cvalues[param]}
                            all_ivalues = {param: all_ivalues[param]}

                        elif not attributes and not already_exists:
                            # If there are attributes from completion, use
                            # them without asking.
                            # Using %s defers string formatting until needed.
                            # (better than f-string for logger)
                            logger.info(
                                "no attributes for: %s %s %s %s",
                                node_name,
                                plug_name,
                                full_name,
                                p_value,
                            )
                            # fmt: off
                            pop_up = PopUpInheritanceDict(
                                parent_files,
                                full_name,
                                plug_name,
                                (
                                    self.iterationTable.check_box_iterate
                                    .isChecked()
                                ),
                            )
                            # fmt: on
                            pop_up.exec()
                            self.ignore_node = pop_up.everything

                            if pop_up.ignore:
                                inheritance_dict = None

                                if pop_up.all is True:
                                    self.ignore[node_name] = True

                                else:
                                    self.ignore[f"{node_name}.{plug_name}"] = (
                                        True
                                    )

                            else:
                                value = pop_up.value

                                if pop_up.all is True:
                                    self.key[node_name] = pop_up.key

                                else:
                                    self.key[f"{node_name}.{plug_name}"] = (
                                        pop_up.key
                                    )

                                inheritance_dict[p_value] = value
                                all_cvalues = {
                                    pop_up.key: all_cvalues[pop_up.key]
                                }
                                all_ivalues = {
                                    pop_up.key: all_ivalues[pop_up.key]
                                }

                cvalues = {
                    TAG_TYPE: file_type,
                    TAG_BRICKS: [brick_id],
                    TAG_HISTORY: history_id,
                }
                ivalues = dict(cvalues)

                # from here if we still have several tags sets,
                # we do not assign them at all. Otherwise, set them.

                # Adding inherited tags
                if len(all_cvalues) == 1:
                    ivalues.update(next(iter(all_ivalues.values())))
                    cvalues.update(next(iter(all_cvalues.values())))

                # use also completion attributes values
                cvalues.update(
                    {k: v for k, v in attributes.items() if k in field_names}
                )
                ivalues.update(
                    {k: v for k, v in attributes.items() if k in field_names}
                )

                if own_tags:

                    # own_tags may insert new fields in the database
                    for tag_to_add in own_tags:

                        for coll in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                            field_names = database_data.get_field_names(coll)

                            if tag_to_add["name"] not in field_names:
                                schema.add_field(
                                    {
                                        "collection_name": coll,
                                        "field_name": tag_to_add["name"],
                                        "field_type": tag_to_add["field_type"],
                                        "description": (
                                            tag_to_add["description"]
                                        ),
                                        "visibility": tag_to_add["visibility"],
                                        "origin": tag_to_add["origin"],
                                        "unit": tag_to_add["unit"],
                                        "default_value": (
                                            tag_to_add["default_value"]
                                        ),
                                    }
                                )

                        cvalues[tag_to_add["name"]] = tag_to_add["value"]
                        ivalues[tag_to_add["name"]] = tag_to_add["value"]

                # Apply changes to DB
                database_data.set_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=processed_path,
                    values_dict=cvalues,
                )
                database_data.set_value(
                    collection_name=COLLECTION_INITIAL,
                    primary_key=processed_path,
                    values_dict=ivalues,
                )

                if tags2del:

                    for tag_to_del in tags2del:

                        for coll in (COLLECTION_CURRENT, COLLECTION_INITIAL):

                            try:
                                database_data.remove_value(
                                    coll, processed_path, tag_to_del
                                )

                            except KeyError:
                                # The collection does not exist
                                # or the field does not exist
                                # or the document does not exist
                                pass

    def ask_iterated_pipeline_plugs(self, pipeline):
        """
        Display a configuration dialog for pipeline plug iteration and
        database connections.

        This method opens an interactive dialog that allows users to
        configure how pipeline plugs (inputs and outputs) should be handled
        during execution. Users can specify:

        - Which plugs should be iterated over during pipeline execution
        - Which input plugs should be connected to database filters
        - Interactive dependency management (database connection requires
          iteration)

        The dialog presents a grid layout with checkboxes for each available
        plug:
            - Iteration checkbox: Mark plug for iteration during execution
            - Database checkbox: Connect input plug to database filter
              (inputs only)

        Behavioral constraints:
            - Database connection automatically enables iteration
            - Disabling iteration automatically disables database connection
            - Only file-compatible plugs can connect to database filters
            - Certain system plugs are excluded from configuration

        :param pipeline: Pipeline object containing plugs to be configured

        :return:
            Optional[Tuple[List[str], List[str]]]: A tuple containing:
                - iterated_plugs: List of plug names marked for iteration
                - database_plugs: List of plug names connected to database
            None if the user cancels the dialog.
        """

        # System plugs that should not be configurable
        FORBIDDEN_PLUGS: set[str] = {
            "nodes_activation",
            "selection_changed",
            "pipeline_steps",
            "visible_groups",
        }

        def is_database_compatible(process, plug: str) -> bool:
            """
            Check if a pipeline plug is compatible with a database filter.

            This helper function verifies whether a plug can be connected to
            a database filter based on its trait type.

            :param process: The process or pipeline containing the plug.
            :param plug (str): The name of the plug to check.

            :return (bool): True if the plug is compatible with a database
                            filter, False otherwise.
            """

            try:
                return is_file_trait(process.trait(plug))

            except (AttributeError, KeyError):
                return False

        def on_iteration_toggled(
            param_buttons: list[list], param_idx: int, checked: bool
        ):
            """
            Handle iteration checkbox toggle events.

            When iteration is disabled, automatically disable database
            connection since database connection requires iteration.

            :param param_buttons (list): List of parameter button
                                         configurations.
            :param param_idx (int): Index of the plug in the parameter list.
            :param checked (bool): The current state of the iteration
                                   checkbox.
            """

            db_checkbox = param_buttons[param_idx][2]

            if not checked and db_checkbox is not None:
                db_checkbox.setChecked(False)

        def on_database_toggled(
            param_buttons: list[list], param_idx: int, checked: bool
        ):
            """
            Handle database checkbox toggle events.

            When database connection is enabled, automatically enable
            iteration since database connection requires iteration.

            Args:
                param_buttons (list): List of parameter button configurations.
                param_idx (int): Index of the plug in the parameter list.
                checked (bool): The current state of the database checkbox.
            """

            if checked:
                param_buttons[param_idx][1].setChecked(True)

        def create_dialog_layout() -> (
            tuple[Qt.QDialog, Qt.QGridLayout, list[list]]
        ):
            """
            Create and configure the main dialog window for pipeline
            configuration.

            This function builds a dialog with:
                - A scrollable parameter configuration section inside a group
                  box.
                - A grid layout for parameter input/output controls.
                - Standard OK/Cancel dialog buttons.

            :return (Tuple[Qt.QDialog, Qt.QGridLayout, List[List]]):
                A tuple containing:
                    - dialog (Qt.QDialog): The configured pipeline
                                           configuration dialog.
                    - param_grid (Qt.QGridLayout): The grid layout used to
                                                   arrange parameter widgets.
                    - param_buttons (List[List]): Two lists (inputs and
                                                  outputs) for storing
                                                  parameter-related button
                                                  widgets.
            """
            dialog = Qt.QDialog()
            dialog.setWindowTitle("Pipeline Iteration Configuration")

            # Create main layout structure
            main_layout = Qt.QVBoxLayout()

            # Parameter configuration section
            param_group = Qt.QGroupBox("Iterate over parameters:")
            param_layout = Qt.QVBoxLayout()
            param_layout.setContentsMargins(0, 0, 0, 0)

            # Scrollable area for parameters
            scroll_area = Qt.QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameStyle(scroll_area.NoFrame)
            scroll_area.setViewportMargins(0, 0, 0, 0)

            # Grid layout for parameter controls
            grid_widget = Qt.QWidget()
            param_grid = Qt.QGridLayout()
            grid_widget.setLayout(param_grid)
            scroll_area.setWidget(grid_widget)

            param_layout.addWidget(scroll_area)
            param_group.setLayout(param_layout)
            main_layout.addWidget(param_group)

            # Dialog buttons
            button_box = Qt.QDialogButtonBox(
                Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            main_layout.addWidget(button_box)

            dialog.setLayout(main_layout)

            # Setup grid headers
            param_grid.addWidget(Qt.QLabel("iter. / database:"), 0, 0, 1, 3)
            param_grid.addWidget(Qt.QLabel("iter.:"), 0, 3, 1, 2)
            param_grid.setColumnStretch(2, 1)
            param_grid.setColumnStretch(4, 1)
            param_grid.setRowStretch(0, 0)

            # [[], []]: param_buttons for [inputs, outputs]
            return dialog, param_grid, [[], []]

        def add_parameter_controls(
            grid: Qt.QGridLayout,
            plugs: list[str],
            param_type: int,
            param_buttons: list[list],
            has_database_option: bool,
        ):
            """
            Add iteration and optional database controls for plugs into the
            grid layout.

            This function creates checkboxes and labels for each plug,
            positions them in the provided grid layout, and stores references
            to the controls in `param_buttons` for later retrieval.

            :param grid (Qt.QGridLayout): The layout where parameter controls
                                          are added.
            :param plugs (list[str]): The list of plug names to create
                                      controls for.
            :param param_type (int): Indicator for the plug type:
                                     - 0: inputs
                                     - 1: outputs
            :param param_buttons (list[list]): A nested list that stores
                                               references to the created
                                               controls, organized by plug
                                               type.
            :param has_database_option (bool): Whether to include a database
                                               checkbox next to each plug.
            """
            filtered_plugs = [
                plug for plug in plugs if plug not in FORBIDDEN_PLUGS
            ]

            for row_idx, plug_name in enumerate(filtered_plugs):
                # Create checkboxes
                iter_checkbox = Qt.QCheckBox()
                iter_checkbox.setChecked(True)  # Default enabled
                db_checkbox = None

                if has_database_option:
                    db_checkbox = Qt.QCheckBox()

                    if not is_database_compatible(pipeline, plug_name):
                        db_checkbox.setEnabled(False)

                # Connect event handlers
                iter_checkbox.toggled.connect(
                    functools.partial(
                        on_iteration_toggled,
                        param_buttons[param_type],
                        row_idx,
                    )
                )

                if db_checkbox:
                    db_checkbox.toggled.connect(
                        functools.partial(
                            on_database_toggled,
                            param_buttons[param_type],
                            row_idx,
                        )
                    )

                # Position controls in grid
                col_base = param_type * 3
                grid.addWidget(iter_checkbox, row_idx + 1, col_base)

                if db_checkbox:
                    grid.addWidget(db_checkbox, row_idx + 1, col_base + 1)

                label_col = 2 if param_type == 0 else 4
                grid.addWidget(Qt.QLabel(plug_name), row_idx + 1, label_col)
                # Store references for later retrieval
                param_buttons[param_type].append(
                    [plug_name, iter_checkbox, db_checkbox]
                )

        def extract_results(
            param_buttons: list[list],
        ) -> tuple[list[str], list[str]]:
            """
            Extract the final plug configuration from the dialog controls.

            This function inspects the checkboxes stored in `param_buttons` to
            determine which plugs are selected for iteration and which are
            linked to the database option.

            :param param_buttons (list[list]): A nested list of plug
                                               configurations, where each
                                               entry is of the form:
                [plug_name (str), iter_checkbox (Qt.QCheckBox),
                db_checkbox (Optional[Qt.QCheckBox])].

            :return (tuple[list[str], list[str]]): A tuple containing:
                - iterated_plugs (list[str]): Names of plugs selected for
                                              iteration.
                - database_plugs (list[str]): Names of plugs with the database
                                              option enabled.
            """
            all_controls = param_buttons[0] + param_buttons[1]

            iterated_plugs = [
                config[0] for config in all_controls if config[1].isChecked()
            ]

            database_plugs = [
                config[0]
                for config in all_controls
                if config[2] is not None and config[2].isChecked()
            ]

            return iterated_plugs, database_plugs

        # Main execution flow
        dialog, param_grid, param_buttons = create_dialog_layout()

        # Get pipeline parameters
        try:
            inputs = list(pipeline.get_inputs().keys())
            outputs = list(pipeline.get_outputs().keys())

        except AttributeError as e:
            raise AttributeError(f"Pipeline missing required methods: {e}")

        add_parameter_controls(
            param_grid, inputs, 0, param_buttons, has_database_option=True
        )
        add_parameter_controls(
            param_grid, outputs, 1, param_buttons, has_database_option=False
        )

        # Set grid stretch for proper layout
        max_param_count = max(
            len([p for p in inputs if p not in FORBIDDEN_PLUGS]),
            len([p for p in outputs if p not in FORBIDDEN_PLUGS]),
        )
        if max_param_count > 0:
            param_grid.setRowStretch(max_param_count, 1)

        # Show dialog and return results
        if dialog.exec_() != dialog.Accepted:
            return None

        return extract_results(param_buttons)

    def build_iterated_pipeline(self):
        """
        Build an iteration pipeline wrapper around the current pipeline.

        This method creates a new pipeline that iterates over the current
        pipeline, allowing batch processing of multiple datasets. The
        process involves:

        1. Interactive selection of plugs to iterate over and database
           connections
        2. Preprocessing of list-type plugs with ReduceNode to handle
           nested lists
        3. Creation of an iterative pipeline using the CAPSUL engine
        4. Addition of Input_Filter nodes for database-connected plugs
        5. Proper linking of database_scans parameter across all filters

        The method handles both single processes and full pipelines,
        converting single processes into single-node pipelines when necessary.

        :return: Pipeline or None: The new iteration pipeline if successful,
                 None if aborted

        :raises ValueError: If Input_Filter process cannot be found in the
                            library.

        Notes:
            - Modifies pipeline completion settings for database plugs
            - Sets the editor's iterated flag to True upon successful
              completion
            - Handles context name parsing for proper iteration naming
        """
        pipeline = self.get_pipeline_or_process()
        engine = self.get_capsul_engine()

        # Determine iteration and pipeline names
        if hasattr(pipeline, "context_name"):
            context_parts = pipeline.context_name.split(".")
            iteration_name = (
                ".".join(context_parts[1:])
                if context_parts[0] == "Pipeline"
                else pipeline.context_name
            )

        else:
            iteration_name = "Pipeline"

        pipeline_name = "Iteration_pipeline"

        # Get user-selected plugs for iteration and database connection
        iteration_data = self.ask_iterated_pipeline_plugs(pipeline)

        if iteration_data is None:
            return None  # User aborted

        iterated_plugs, database_plugs = iteration_data

        # Fix unconnected inner nodes if needed
        if hasattr(pipeline, "parent_pipeline") and pipeline.parent_pipeline:
            pipeline.parent_pipeline = None

            if hasattr(pipeline, "update_nodes_and_plugs_activation"):
                # only if it is a pipeline - a single node does not have it
                pipeline.update_nodes_and_plugs_activation()

        # Process database plugs
        for plug in database_plugs:
            trait = pipeline.trait(plug)
            trait.forbid_completion = True

            # Propagate non-completion status to linked plugs
            if hasattr(pipeline, "pipeline_node"):

                # (TODO: needs something better)
                for link in pipeline.pipeline_node.plugs[plug].links_to:
                    link[2].get_trait(link[1]).forbid_completion = True

            # Convert single process to pipeline if necessary
            if not isinstance(pipeline, Pipeline):
                new_pipeline = Pipeline()
                new_pipeline.set_study_config(pipeline.study_config)

                # Determine node name from context
                context_name = getattr(pipeline, "context_name", pipeline.name)
                context_parts = context_name.split(".")
                old_node_name = (
                    ".".join(context_parts[1:])
                    if context_parts[0] == "Pipeline"
                    else context_name
                )
                new_pipeline.add_process(old_node_name, pipeline)
                new_pipeline.autoexport_nodes_parameters(include_optional=True)
                pipeline = new_pipeline
                iteration_name = old_node_name

            # Add ReduceNode for list-type traits to prevent nested lists
            if isinstance(trait.trait_type, traits.List):
                node_name = f"un_list_{plug}"
                reduce_node = pipeline.add_custom_node(
                    node_name,
                    "capsul.pipeline.custom_nodes.reduce_node.ReduceNode",
                    parameters={"input_types": ["File"]},
                )
                reduce_node.lengths = [1]

                # Redirect existing connections through the ReduceNode
                existing_links = list(
                    pipeline.pipeline_node.plugs[plug].links_to
                )

                for link in existing_links:
                    pipeline.add_link(
                        f"{node_name}.outputs->{link[0]}.{link[1]}"
                    )

                # Replace pipeline plug with ReduceNode input export
                old_traits = list(pipeline.user_traits().keys())
                pipeline.remove_trait(plug)
                pipeline.export_parameter(
                    node_name, "input_0", pipeline_parameter=plug
                )
                pipeline.trait(plug).forbid_completion = True
                pipeline.reorder_traits(old_traits)

        # Create the iteration pipeline
        iteration_name = f"iterated_{iteration_name}"
        it_pipeline = engine.get_iteration_pipeline(
            pipeline_name,
            iteration_name,
            pipeline,
            iterative_plugs=iterated_plugs,
            do_not_export=database_plugs,
            make_optional=None,
        )
        # Add Input_Filter nodes for database-connected plugs
        input_filter_success = True

        for plug in database_plugs:

            try:
                input_filter = engine.get_process_instance(
                    "mia_processes.bricks.tools.Input_Filter"
                )
                input_filter.pipmantab = self

            except ValueError:
                input_filter_success = False
                logger.warning("Input filter not found in library.")
                break

            # Add to pipeline and connect to iteration node
            node_name = f"{plug}_filter"
            it_pipeline.add_process(node_name, input_filter)
            it_pipeline.add_link(
                f"{node_name}.output->{iteration_name}.{plug}"
            )

            # Handle database_scans connection - link existing
            # or create new parameter
            if "database_scans" in it_pipeline.user_traits():
                it_pipeline.add_link(f"database_scans->{node_name}.input")

            else:
                old_traits = list(it_pipeline.user_traits().keys())
                it_pipeline.export_parameter(
                    node_name, "input", pipeline_parameter="database_scans"
                )
                it_pipeline.reorder_traits(["database_scans"] + old_traits)

        # Set iteration flag if all filters were added successfully
        if input_filter_success:
            self.pipelineEditorTabs.get_current_editor().iterated = True

        return it_pipeline

    def check_requirements(self, environment="global"):
        """
        Check and return the configuration of a pipeline based on its
        requirements.

        This method iterates through the nodes in the pipeline, gathers their
        requirements, and determines the appropriate configuration for each
        node in the specified environment. It uses the settings from the study
        configuration engine to select configurations that match the
        requirements.

        :param environment (str): The target environment for checking
                                  configurations. Defaults to "global".

        :return (dict): A dictionary mapping each pipeline node to its
                        selected configuration.
        """

        return {
            node: (
                node.get_study_config().engine.settings.select_configurations(
                    environment,
                    uses=node.requirements(),
                )
            )
            for node in self.node_list
        }

    def cleanup_older_init(self):
        """
        Clean up data browser state and remove orphaned files.

        This method performs the following cleanup operations:
            1. Removes non-existent entries from the data browser for
               each brick
            2. Cleans up orphaned non-existing files from the project
            3. Clears the brick and node lists
            4. Updates the data browser table display

        Note:
        The table update is performed asynchronously using QtThreadCall
        to ensure UI responsiveness.
        """

        # Process each brick and remove non-existent entries
        for brick in self.brick_list:
            logger.info("Cleaning up brick: %s", brick)
            self.main_window.data_browser.table_data.delete_from_brick(brick)

        # Clean up project-level orphaned files
        self.project.cleanup_orphan_nonexisting_files()
        # Clear internal state lists
        self.brick_list.clear()
        self.node_list.clear()
        # Update UI asynchronously
        QtThreadCall().push(
            self.main_window.data_browser.table_data.update_table
        )

    def complete_pipeline_parameters(self, pipeline=None):
        """
        Complete pipeline parameters using Capsul's completion engine.

        This method utilizes Capsul's completion engine to automatically
        populate the parameters of a pipeline based on a set of attributes.
        These attributes can be retrieved from an associated database. If no
        pipeline is specified, the current pipeline or process is used.

        :param pipeline (Pipeline): The pipeline object to be completed.
                                    If not provided, the method
                                    retrieves the current pipeline
                                    or process.

        Notes:
        The completion process relies on Capsul's ProcessCompletionEngine
        to automatically determine appropriate parameter values.
        """
        pipeline = pipeline or self.get_pipeline_or_process()

        completion = ProcessCompletionEngine.get_completion_engine(pipeline)

        if completion:
            completion.complete_parameters()

    def controller_value_changed(self, signal_list):
        """
        Update history when a node or plug value changes.

        This method processes change signals from the pipeline editor and
        maintains an undo history for user actions. It handles two types
        of changes:
            - Node name updates: Updates the node name and refreshes the
                                 pipeline view while preserving the current
                                 view state.
            - Plug value updates: Records parameter changes while filtering
                                  out protected parameters, empty values, and
                                  system-generated changes to avoid cluttering
                                  the undo history.

        :param signal_list: A list containing change information with the
                            first element being the change type ("node_name"
                            or "plug_value"), followed by context-specific
                            data:
            - For "node_name": ["node_name", ProcessNode_object,
                                new_node_name, old_node_name]
            - For "plug_value": ["plug_value", node_name, old_value,
                                 plug_name, plug_type, new_value]]
        """

        if not signal_list:
            return

        # Constants for filtering
        protected_parameters = {
            "protected_parameters",
            "protected_parameters_items",
            "selection_changed",
            "trait_added",
            "user_traits_changed",
        }
        filtered_plug_types = {"inputs", "outputs"}
        change_type = signal_list.pop(0)

        if change_type == "node_name":
            # Create history entry for node name change
            history_entry = ["update_node_name", *signal_list]
            # Refresh pipeline view while preserving current state
            pipeline = self.pipelineEditorTabs.get_current_pipeline()
            editor = self.pipelineEditorTabs.get_current_editor()
            # Preserve current view state
            current_rect = editor.sceneRect()
            current_transform = editor.transform()
            # Update pipeline and restore view state
            editor.set_pipeline(pipeline)
            editor.setSceneRect(current_rect)
            editor.setTransform(current_transform)

        elif change_type == "plug_value":

            # Validate signal data length
            if len(signal_list) < 5:
                return

            (
                _,
                old_value,
                plug_name,
                _,
                new_value,
            ) = signal_list[:5]

            # Filter out changes we don't want to track
            if (
                plug_name in protected_parameters
                or old_value == ""
                or (old_value == [] and new_value is Undefined)
            ):
                return

            # Clean signal data by filtering out unwanted plug types
            cleaned_signal_list = [
                (
                    ""
                    if isinstance(element, str)
                    and element in filtered_plug_types
                    else element
                )
                for element in signal_list
            ]

            history_entry = ["update_plug_value", *cleaned_signal_list]

        else:
            # Unknown change type, skip processing
            return

        # Add entry to undo history
        current_editor = self.pipelineEditorTabs.get_current_editor()
        self.pipelineEditorTabs.undos[current_editor].append(history_entry)

    def displayNodeParameters(self, node_name, process):
        """
        Display the node controller interface for the specified node.

        This method configures and shows the node parameter interface when
        a user clicks on a node in the pipeline editor. It updates the scroll
        area widget to display the node controller with the current pipeline
        context.

        :param node_name: The name/identifier of the selected node.
        :param process: The process instance associated with the selected
                        node.
        """
        current_pipeline = self.pipelineEditorTabs.get_current_pipeline()
        self.nodeController.display_parameters(
            node_name, process, current_pipeline
        )
        self.scrollArea.setWidget(self.nodeController)

    def finish_execution(self):
        """
        Handle pipeline execution completion and update UI state.

        This callback is invoked after a pipeline execution completes,
        whether successfully or with errors. The method performs comprehensive
        cleanup and user feedback operations:

        - Disables pipeline control actions during cleanup
        - Disconnects progress worker signals to prevent memory leaks
        - Checks execution status and handles
          WorkflowExecutionError/RuntimeError
        - Updates status bar with clear success/failure messages
        - Sets appropriate visual status icon (green checkmark or red cross)
        - Cleans up progress indicators and re-enables pipeline actions
        - Updates node controller parameters for next execution

        The method ensures proper cleanup regardless of execution outcome and
        provides comprehensive user feedback through status messages and
        visual indicators.

        :raises:
            WorkflowExecutionError: When pipeline execution fails
            RuntimeError: When execution is aborted before running
        """

        from soma_workflow import constants as swconstants

        self.stop_pipeline_action.setEnabled(False)
        worker = self.progress.worker
        status = worker.status
        worker.finished.disconnect(self.finish_execution)
        self.last_status = status
        # Check execution status and handle errors
        execution_successful = True

        try:
            engine = self.last_run_pipeline.get_study_config().engine

            if worker.exec_id is None:
                raise RuntimeError("Execution aborted before running")

            engine.raise_for_status(status, worker.exec_id)
            self.last_run_log = None

        except (WorkflowExecutionError, RuntimeError) as exc:
            execution_successful = False
            error_message = str(exc)
            self.last_run_log = error_message
            logger.warning(
                "Pipeline execution failed with exception: %s", error_message
            )

        # Update status bar with clear messaging
        pipeline_name = self.last_pipeline_name
        status_bar = self.main_window.statusBar()

        if execution_successful:
            status_bar.showMessage(
                f"'{pipeline_name}' pipeline completed successfully!"
            )

        else:
            status_bar.showMessage(
                f"'{pipeline_name}' pipeline execution failed!"
            )

        # Set appropriate status icon
        icon_filename = (
            "green_v.png"
            if status == swconstants.WORKFLOW_DONE
            else "red_cross32.png"
        )
        config = Config()
        sources_images_dir = Path(config.getSourceImageDir())
        icon_path = sources_images_dir / icon_filename
        self.show_pipeline_status_action.setIcon(QIcon(str(icon_path)))
        # Cleanup progress indicators and re-enable actions
        self._mmovie.stop()
        del self._mmovie
        Qt.QTimer.singleShot(100, self.remove_progress)
        # Re-enable pipeline actions for next execution
        self.nodeController.update_parameters()
        self.run_pipeline_action.setDisabled(False)
        self.garbage_collect_action.setDisabled(False)
        self.test_init = False

    def garbage_collect(self):
        """
        Clean up obsolete data and maintain database consistency.

        This method performs comprehensive cleanup operations including:
            - Processing finished pipeline executions with error protection
            - Removing orphaned files and historical data entries
            - Refreshing the data browser table display
            - Resetting pipeline editor initialization state if applicable
            - Updating UI button states to reflect current system status

        The cleanup operations ensure the application remains performant
        and maintains data integrity across user sessions.
        """

        # Process pipeline execution with logger protection
        with protected_logging():
            self.postprocess_pipeline_execution()

        # Clean up orphaned project data
        self.project.cleanup_orphan_nonexisting_files()
        self.project.cleanup_orphan_history()
        # Refresh UI components
        self.main_window.data_browser.table_data.update_table()
        current_editor = self.pipelineEditorTabs.get_current_editor()

        if (
            hasattr(current_editor, "initialized")
            and current_editor.initialized
        ):
            current_editor.initialized = False

        self.update_user_buttons_states()

    def get_capsul_engine(self):
        """
        Retrieve and configure a Capsul engine from the pipeline editor.

        This method obtains a CapsulEngine object from the current
        pipeline editor tabs and configures it using the Mia configuration
        settings.

        :return (CapsulEngine): A configured Capsul engine instance ready for
                                pipeline execution, with settings applied from
                                the Mia config object.
        """
        return self.pipelineEditorTabs.get_capsul_engine()

    def get_pipeline_or_process(self, pipeline=None):
        """
        Get the pipeline or its single unconnected process node.

        When a pipeline contains only one process node with no connections,
        this method returns the process directly instead of the pipeline
        wrapper. This simplifies GUI workflows where single processes can
        act as pipelines.

        :param pipeline (Pipeline): Optional pipeline to evaluate. If None,
                                    uses the currently selected pipeline from
                                    the editor GUI.

        :return (Pipeline | Process): The process node if pipeline contains a
                                      single unconnected process, otherwise
                                      the pipeline itself.
        """

        if pipeline is None:
            current_editor = self.pipelineEditorTabs.get_current_editor()
            pipeline = current_editor.scene.pipeline

        # Check if pipeline has only root node + one process node with no
        # connections
        if len(pipeline.nodes) == 2 and len(pipeline.pipeline_node.plugs) == 0:

            # Find and return the process node (skip empty names)
            process_nodes = [
                node
                for name, node in pipeline.nodes.items()
                if name and isinstance(node, ProcessNode)
            ]

            if process_nodes:
                return process_nodes[0].process

        return pipeline

    def get_missing_mandatory_parameters(self):
        """
        Find missing mandatory parameters across all pipeline nodes.

        Checks each node in the pipeline for missing mandatory parameters,
        accounting for workflow job parameter overrides and temporary values.

        :return (list[str]): Parameter names that are missing, formatted as
                             either 'parameter_name' for pipeline root or
                             'node.parameter_name' for other nodes.

        Note:
            Parameters with non-null values in the workflow job dictionary
            are not considered missing, even if undefined at the node level.
        """
        missing_mandatory_param = []

        for node in self.node_list:
            # Extract display name, handling Pipeline prefix
            node_name = getattr(node, "context_name", node.name)

            if node_name.split(".")[0] == "Pipeline":
                node_name = ".".join(node_name.split(".")[1:])

            # Find workflow job for this node (cached per node)
            job = None

            for param in node.get_missing_mandatory_parameters():

                # Lazy load job only when needed
                if job is None:
                    matching_jobs = [
                        j
                        for j in self.workflow.jobs
                        if hasattr(j, "process") and j.process() is node
                    ]
                    job = matching_jobs[0] if matching_jobs else False

                # Skip parameters with values in workflow
                if job:
                    value = job.param_dict.get(param)

                    if value not in (None, Undefined, []):
                        # gets a non-null value in the workflow
                        continue

                # Format parameter name based on node type
                current_pipeline = (
                    self.pipelineEditorTabs.get_current_pipeline()
                )

                if node is current_pipeline.pipeline_node:
                    param_name = param

                else:
                    param_name = f"{node_name}.{param}"

                missing_mandatory_param.append(param_name)

        return missing_mandatory_param

    def initialize(self):
        """
        Initialize the pipeline after cleaning up any previous initialization.

        This method performs the following operations:
            1. Sets a wait cursor to indicate processing
            2. Cleans up any previous initialization if needed
            3. Resets internal state variables
            4. Attempts to initialize the pipeline
            5. Updates the UI with the results
            6. Restores the normal cursor

        The method handles initialization errors gracefully by logging
        warnings and updating the status bar with error messages.

        Side Effects:
            - Modifies cursor appearance during execution
            - Updates pipeline editor tabs and node parameters
            - May display error messages in the status bar
            - Sets self.init_clicked to True upon completion
        """
        app = QApplication.instance()
        app.setOverrideCursor(QCursor(Qt.Qt.WaitCursor))

        try:

            # Clean up previous initialization if this isn't the first run
            if self.init_clicked:
                self.cleanup_older_init()

            # Reset internal state
            self.ignore_node = False
            self.key = {}
            self.ignore = {}

            # Attempt pipeline initialization
            try:
                self.test_init = self.init_pipeline()

            except Exception:
                # Get pipeline name for error reporting
                filename = self.pipelineEditorTabs.get_current_filename()
                pipeline_name = os.path.basename(filename)

                if not pipeline_name:
                    # Fallback: get first non-empty node name
                    pipeline = self.pipelineEditorTabs.get_current_pipeline()
                    non_empty_nodes = [name for name in pipeline.nodes if name]
                    # TODO: This is suboptimal if multiple nodes exist!
                    #       Ex. a pipeline with two nodes: A and B consructed
                    #       just before to launch init_pipeline: in this case
                    #       we will always get A as pipeline name...
                    pipeline_name = (
                        non_empty_nodes[0]
                        if len(non_empty_nodes) == 1
                        else "Unknown"
                    )

                pipeline_name = pipeline_name.removesuffix(".py")

                logger.warning(
                    f"Error during initialization of "
                    f"the '{pipeline_name}' pipeline",
                    exc_info=True,
                )
                self.test_init = False
                error_message = (
                    f'Pipeline "{pipeline_name}" was '
                    f"not initialized successfully."
                )
                self.main_window.statusBar().showMessage(error_message)

            # Update UI state
            self.pipelineEditorTabs.update_current_node()
            # Deep copy node parameters from temporary storage
            current_editor = self.pipelineEditorTabs.get_current_editor()
            current_editor.node_parameters = copy.deepcopy(
                current_editor.node_parameters_tmp
            )
            # Update UI state again after parameter
            # changes (TODO: not sure if needed)
            self.pipelineEditorTabs.update_current_node()

        finally:
            # Always restore cursor and set init_clicked, even if an
            # exception occurs
            self.init_clicked = True
            app.restoreOverrideCursor()

    def init_pipeline(self, pipeline=None, pipeline_name=""):
        """
        Initialize the current pipeline in the pipeline editor.

        This method:
            - Retrieves and configures the pipeline or sub-pipeline.
            - Generates and validates the workflow.
            - Checks requirements (FSL, AFNI, ANTS, Matlab, MRtrix, SPM).
            - Verifies that mandatory inputs/outputs are properly set.
            - Records initialization results in the project database.
            - Updates the status bar and displays warnings when needed.

        :param pipeline (Pipeline, Process): The pipeline or process instance
                                             to initialize. If None, the main
                                             pipeline is retrieved.
        :param pipeline_name (str): The name of the parent pipeline, if
                                    applicable.

        :return (bool): True if the pipeline was successfully initialized,
                        False otherwise.
        """

        def _calculate_duration(t0: float) -> float:
            """
            Calculate the elapsed time since `t0`, rounded to the nearest
            significant digit of the fractional part of the duration.

            :param t0 (float): The starting time.

            :return (float): The elapsed duration since `t0`, rounded to the
                             nearest significant digit.
            """

            try:
                duration = time.time() - t0

                return round(
                    duration,
                    -int(math.floor(math.log10(abs(math.modf(duration)[0]))))
                    + 1,
                )

            except ValueError:
                return time.time() - t0

        def _get_node_name(node) -> str:
            """
            Extracts a node's name, preferring ``context_name`` if available.

            If the node has a ``context_name`` attribute, it will be used;
            otherwise, the node's ``name`` attribute is used. If the resulting
            name starts with ``"Pipeline."``, the prefix is stripped.

            :param node: The node object, expected to have at least a
                         ``name`` attribute, and optionally a ``context_name``
                         attribute.
            :return (str): The extracted node name with any leading
                           ``"Pipeline."`` prefix removed.
            """
            node_name = getattr(node, "context_name", node.name)

            if node_name.split(".")[0] == "Pipeline":
                node_name = ".".join(node_name.split(".")[1:])

            return node_name

        # TODO: It seems pipeline and pipeline_name are always
        #       None and "",respectively

        logger.info("- Pipeline initializing")
        logger.info("  *********************")
        # Initialize timing and state
        start_time = time.time()
        init_result, init_messages = True, []
        QApplication.processEvents()

        # Retrieve main pipeline if not provided
        # TODO: main_pipeline is always True (see TODO above)
        main_pipeline = pipeline is None
        pipeline = pipeline or get_process_instance(
            self.get_pipeline_or_process()
        )
        # Determine pipeline name
        if isinstance(pipeline, Process) and not isinstance(
            pipeline, Pipeline
        ):
            # Special case: single brick
            name = f"{pipeline.name.lower()}_1"
            # FIXME: launching a brick without exporting all plugs could have
            #        side effects?

        else:
            name = pipeline.name

        # Special case: default pipeline with exactly 2 nodes
        if name == "Pipeline" and len(pipeline.nodes) == 2:
            name = next((k for k in pipeline.nodes if k), name)

        else:
            name = "Unknown"

        # Show status message
        self.main_window.statusBar().showMessage(
            f"'{name}' pipeline is getting initialized. Please wait..."
        )
        QApplication.processEvents()
        # complete config for completion
        study_config = pipeline.get_study_config()
        study_config.project = self.project
        self.project.node_inheritance_history = {}
        init_messages = []

        # Generate workflow from pipeline
        try:
            logger.info(
                f"Workflow generation / completion for the "
                f"'{name}' pipeline..."
            )
            self.workflow = workflow_from_pipeline(
                pipeline, check_requirements=False, complete_parameters=True
            )
            logger.info("Workflow done!")

        except Exception as e:
            init_result = False
            traceback_str = "".join(traceback.format_tb(e.__traceback__))
            init_messages.append(
                f"Error when building the workflow for the '{name}' "
                f"pipeline:\n{traceback_str} {e.__class__.__name__}: {e}\n"
            )

        # Fail if workflow is invalid
        if getattr(self.workflow, "jobs", []) == [] or not init_result:
            logger.warning(
                f"'{name}' pipeline was not successfully initialised..."
            )
            duration = _calculate_duration(start_time)
            logger.info(f"Initialisation phase completed in {duration}s!")

            self.msg = QMessageBox()
            self.msg.setWindowTitle("Pipeline initialization warning!")
            self.msg.setText(
                "No bricks were detected when the workflow was "
                "generated...!\nPlease check that the pipeline has "
                "been correctly built and configured (have all the necessary "
                "plugs been exported? have all the input parameters been "
                "set?, etc.)"
            )
            self.msg.setIcon(QMessageBox.Critical)
            yes_button = self.msg.addButton(
                "Open MIA preferences", QMessageBox.YesRole
            )
            self.msg.addButton(QMessageBox.Ok)
            self.msg.exec()

            if self.msg.clickedButton() == yes_button:
                self.main_window.software_preferences_pop_up()
                # fmt: off
                (
                    self.main_window.pop_up_preferences.
                    tab_widget.setCurrentIndex
                )(1)
                # fmt: on

            self.main_window.statusBar().showMessage(
                f"'{name}' pipeline was not initialised successfully..."
            )

            for err_mess in init_messages:
                logger.warning("%s", err_mess)

            return False

        if self.workflow is not None:
            # retrieve node list
            self.update_node_list(brick=pipeline)
            # check missing mandatory parameters
            missing_mandat_param = self.get_missing_mandatory_parameters()
            # check requirements
            requirements = self.check_requirements()

        else:
            missing_mandat_param = []
            requirements = {}

        if missing_mandat_param:
            mes = "\n    - ".join(missing_mandat_param)
            mssg = (
                f"Missing mandatory parameters in '{name}' pipeline:\n    - "
                f"{mes}\n"
            )
            init_messages.append(mssg)
            init_result = False

        if not requirements:
            pipeline.check_requirements(message_list=[])
            logger.warning("\nPipeline requirements are not met:\n%s")
            logger.warning(
                "\nCurrent configuration:\n%s",
                study_config.engine.settings.export_config_dict("global"),
            )

            req_messages = [
                "Please see the standard output for more information.\n"
            ]

        else:
            # FIXME: Would it be better to write a general method for
            #        testing all modules (currently each module test is
            #        hard coded below)?
            # FIXME: Are these tests compatible with remote run?
            # FIXME: Make a requirement check for FreeSurfer:
            req_messages = []

            for req_node, reqs in requirements.items():
                node_name = _get_node_name(req_node)

                # Safely get the "uses" dictionary
                uses = reqs.get("capsul_engine", {}).get("uses", {})

                if not uses:
                    continue  # Skip if no "uses" section

                # TODO: # --- FreeSurfer ---

                # --- AFNI ---
                if uses.get("capsul.engine.module.afni") is not None:

                    if not reqs.get("capsul.engine.module.afni", {}).get(
                        "directory", False
                    ):
                        req_messages.append(
                            f"The {node_name} requires AFNI but it "
                            f"seems AFNI is not configured in "
                            f"Mia preferences."
                        )

                # --- ANTS ---
                if uses.get("capsul.engine.module.ants") is not None:

                    if not reqs.get("capsul.engine.module.ants", {}).get(
                        "directory", False
                    ):
                        req_messages.append(
                            f"The {node_name} requires ANTS but it "
                            f"seems ANTS is not configured in "
                            f"Mia preferences."
                        )

                # --- FSL ---
                if uses.get("capsul.engine.module.fsl") is not None:

                    if not reqs.get("capsul.engine.module.fsl", {}).get(
                        "directory", False
                    ):
                        req_messages.append(
                            f"The {node_name} requires FSL but it "
                            f"seems FSL is not configured in Mia preferences."
                        )

                # --- MRtrix ---
                if uses.get("capsul.engine.module.mrtrix") is not None:

                    if not reqs.get("capsul.engine.module.mrtrix", {}).get(
                        "directory", False
                    ):
                        req_messages.append(
                            f"The {node_name} requires MRtrix but it "
                            f"seems MRtrix is not configured in "
                            f"Mia preferences."
                        )

                # --- Matlab ---
                if uses.get("capsul.engine.module.matlab") is not None:
                    matlab_config = reqs.get("capsul.engine.module.matlab", {})

                    if Config().get_use_spm() and not matlab_config.get(
                        "executable", False
                    ):
                        req_messages.append(
                            f"The {node_name} requires Matlab but it "
                            f"seems Matlab is not configured in "
                            "Mia preferences."
                        )
                    if (
                        Config().get_use_spm_standalone()
                        and not matlab_config.get("mcr_directory", False)
                    ):
                        req_messages.append(
                            f"The {node_name} requires Matlab MCR but it "
                            f"seems Matlab MCR is not configured in "
                            f"Mia preferences."
                        )

                # --- SPM ---
                if uses.get("capsul.engine.module.spm") is not None:

                    if "capsul.engine.module.spm" in reqs:
                        spm_config = reqs["capsul.engine.module.spm"]

                        if not spm_config.get("directory", False):
                            req_messages.append(
                                f"The {node_name} requires SPM but it "
                                f"seems SPM is not configured in "
                                f"Mia preferences."
                            )

                        elif spm_config.get("standalone", False):

                            if not Config().get_use_matlab_standalone():
                                req_messages.append(
                                    f"The {node_name} requires SPM but "
                                    f"it seems that in Mia preferences, SPM "
                                    f"has been configured as standalone "
                                    f"while Matlab MCR is not configured."
                                )

                        else:
                            # Check for matlab executable using .get()
                            if not reqs.get(
                                "capsul.engine.module.matlab", {}
                            ).get("executable", False):
                                req_messages.append(
                                    f"The {node_name} requires SPM but it "
                                    f"seems that in Mia preferences, SPM has "
                                    f"been configured as non-standalone while "
                                    f"Matlab with license is not configured."
                                )
                    else:
                        req_messages.append(
                            f"The {node_name} requires SPM but it seems "
                            f"SPM is not configured in Mia preferences."
                        )

        if req_messages:
            init_result = False
            mes = "\n    - ".join(req_messages)
            mssg = (
                f"The pipeline requirements are not met for '{name}' "
                f"pipeline:\n    - {mes}\n"
            )
            init_messages.append(mssg)

        # Check that completion for output parameters is fine (for each job)
        missing_mandat_out_param = []
        missing_all_out_param = []

        if self.workflow:

            for job in self.workflow.jobs:

                if hasattr(job, "process"):
                    node = job.process()
                    node_name = _get_node_name(node)
                    # All output plugs (except spm_script_file),
                    # optional or not:
                    output_names = [
                        trait_name
                        for trait_name in node.traits(output=True)
                        if trait_name
                        not in ("spm_script_file", "_spm_script_file")
                    ]
                    # If none of the outputs have a value, there is a problem.
                    # Checked only for ProcessMIA bricks because it seems that
                    # for some nipype processes the output parameters are only
                    # generated at runtime (for example:
                    # nipype.interfaces.utility.base.Rename).
                    if not any(
                        output_name in job.param_dict
                        for output_name in output_names
                    ) and isinstance(node, ProcessMIA):
                        missing_all_out_param.append(node_name)

                    # All output plugs (except spm_script_file), not optional
                    output_names = [
                        trait_name
                        for trait_name in output_names
                        if not node.trait(trait_name).optional
                    ]

                    # If a non-optional output has no value, there's issue
                    if not all(
                        output_name in job.param_dict
                        for output_name in output_names
                    ):
                        missing_mandat_out_param.append(node_name)

                    if getattr(node, "init_result", None) is False:
                        init_result = False
                        init_messages.append(
                            f"An issue has been detected when initializing "
                            f"the '{node_name}' brick in the '{name}' "
                            f"pipeline.\nThe pipeline cannot be launched "
                            f"under these conditions...\n"
                        )

        if missing_mandat_out_param:
            init_result = False
            mes = "\n    - ".join(missing_mandat_out_param)
            mssg = (
                f"Missing mandatory output parameter(s) for the following "
                f"brick(s) in the '{name}' pipeline:\n    - {mes}\n"
            )
            init_messages.append(mssg)

        if missing_all_out_param:
            init_result = False
            mes = "\n    - ".join(missing_all_out_param)
            mssg = (
                f"None of the output parameters have been completed for the "
                f"following brick(s) in the '{name}' pipeline.\n    - {mes}\n"
                f"Please check the configuration and input parameters for "
                f"these bricks..."
            )
            init_messages.append(mssg)

        if init_result:
            # --- Save pipeline to history and database ---
            history_id = str(uuid.uuid4())

            with self.project.database.data(write=True) as database_data:
                database_data.add_document(COLLECTION_HISTORY, history_id)
                # serialize pipeline
                target_pipeline = (
                    next(
                        proc.process
                        for proc in pipeline.list_process_in_pipeline
                        if isinstance(proc, ProcessIteration)
                    )
                    if pipeline.name == "Iteration_pipeline"
                    else pipeline
                )
                buffer = io.StringIO()
                pipeline_tools.save_pipeline(
                    target_pipeline, buffer, format="xml"
                )
                database_data.set_value(
                    collection_name=COLLECTION_HISTORY,
                    primary_key=history_id,
                    values_dict={HISTORY_PIPELINE: buffer.getvalue()},
                )

            # add process characteristics in the database
            # if init is otherwise OK
            for job in filter(
                lambda job: hasattr(job, "process"), self.workflow.jobs
            ):
                node = job.process()
                process = (
                    node.process if isinstance(node, ProcessNode) else node
                )

                if not hasattr(process, "context_name"):
                    continue

                node_name = process.context_name
                node_name = (
                    ".".join(node_name.split(".")[1:])
                    if node_name.startswith("Pipeline.")
                    else node_name
                )
                self.update_auto_inheritance(node, job)
                self.update_inheritance(job, node)

                # Skip pipeline nodes
                if isinstance(node, (PipelineNode, Pipeline)):
                    continue

                # Generate brick ID
                if not (
                    brick_id := getattr(job, "uuid", None)
                    or getattr(node, "uuid", None)
                ):
                    brick_id = str(uuid.uuid4())

                # set brick_id in process
                job.uuid = brick_id
                self.brick_list.append(brick_id)

                with self.project.database.data(write=True) as database_data:

                    try:
                        database_data.add_document(COLLECTION_BRICK, brick_id)

                    except ValueError:
                        # ID is not unique. It happens in iterations
                        # FIXME: we need a better way to handle UUIDs in
                        #        iterated processes
                        init_result = False
                        init_messages.append(
                            f"Error while setting job uuid on "
                            f"'{node_name}' brick."
                        )

                    database_data.set_value(
                        collection_name=COLLECTION_BRICK,
                        primary_key=brick_id,
                        values_dict={
                            BRICK_NAME: node_name,
                            BRICK_INIT_TIME: (datetime.datetime.now()),
                            BRICK_INIT: "Not Done",
                            BRICK_EXEC: "Not Done",
                        },
                    )

                self._register_node_io_in_database(
                    job, node, pipeline_name, history_id
                )

            # Save brick list to history
            with self.project.database.data(write=True) as database_data:
                database_data.set_value(
                    collection_name=COLLECTION_HISTORY,
                    primary_key=history_id,
                    values_dict={HISTORY_BRICKS: self.brick_list},
                )

        self.register_completion_attributes(pipeline)
        self.project.saveModifications()

        # Updating the node controller
        # Display the updated parameters in right part of
        # the Pipeline Manager (controller)
        if main_pipeline:
            # TODO: Fix the problem of the controller that
            #       keeps the name of the old brick deleted until
            #       a click on the new one. This can cause a Mia
            #       crash during the initialisation, for example.
            node_controller_node_name = (
                ""
                if self.nodeController.node_name in ["inputs", "outputs"]
                else self.nodeController.node_name
            )
            # Determine process for controller
            process = (
                pipeline.nodes[node_controller_node_name].process
                if (
                    isinstance(pipeline, Pipeline)
                    and node_controller_node_name in pipeline.nodes
                )
                else pipeline
            )
            self.nodeController.display_parameters(
                self.nodeController.node_name,
                process,
                self.pipelineEditorTabs.get_current_pipeline(),
            )

            if not init_result:

                # Format error message more elegantly
                if init_messages:
                    details = "\n".join(f"- {msg}" for msg in init_messages)
                    message = (
                        "The pipeline could not be initialized properly:\n"
                        f"{details}"
                    )

                else:
                    message = (
                        "The pipeline could not be initialized correctly, "
                        "for an unknown reason!"
                    )

                lineCnt = message.count("\n")
                self.msg = QMessageBox()
                self.msg.setWindowTitle("Pipeline initialization warning!")

                # Setup message display based on length
                if lineCnt > 10:
                    scroll = QtWidgets.QScrollArea()
                    scroll.setWidgetResizable(True)
                    content = QtWidgets.QWidget()
                    scroll.setWidget(content)
                    layout = QtWidgets.QVBoxLayout(content)
                    label = QtWidgets.QLabel(message)
                    label.setTextInteractionFlags(
                        QtCore.Qt.TextSelectableByMouse
                    )
                    layout.addWidget(label)
                    self.msg.layout().addWidget(
                        scroll, 0, 0, 1, self.msg.layout().columnCount()
                    )
                    self.msg.setStyleSheet(
                        "QScrollArea{min-width:550 px; min-height: 300px}"
                    )

                else:
                    self.msg.setText(message)
                    self.msg.setIcon(QMessageBox.Critical)

                yes_button = self.msg.addButton(
                    "Open MIA preferences", QMessageBox.YesRole
                )
                self.msg.addButton(QMessageBox.Ok)
                self.msg.exec()

                if self.msg.clickedButton() == yes_button:
                    self.main_window.software_preferences_pop_up()
                    # fmt: off
                    (
                        self.main_window.pop_up_preferences.
                        tab_widget.setCurrentIndex
                    )(1)
                    # fmt: on

                self.main_window.statusBar().showMessage(
                    f"'{name}' pipeline was not initialised successfully."
                )
                logger.warning(
                    '\n"%s" pipeline was not successfully initialised.', name
                )
                duration = _calculate_duration(start_time)

            else:

                # Success case - update editors
                for i in range(0, len(self.pipelineEditorTabs) - 1):
                    self.pipelineEditorTabs.get_editor_by_index(
                        i
                    ).initialized = False

                self.pipelineEditorTabs.get_current_editor().initialized = True
                self.main_window.statusBar().showMessage(
                    f"'{name}' pipeline has been successfully initialised."
                )
                logger.info(
                    '\n"%s" pipeline has been successfully initialised.', name
                )
                duration = _calculate_duration(start_time)

        else:
            duration = _calculate_duration(start_time)
            # FIXME: I don't understand when main_pipeline can be False.
            #        So in this case, we are instancing the duration here.

        logger.info(f"Initialisation phase completed in {duration}s!")
        return init_result

    def layout_view(self):
        """
        Initialize the layout and toolbar for the pipeline manager tab.

        This method sets up the main diagram editor window, configures the
        scroll area, builds the toolbar with pipeline actions, and arranges
        widgets in splitters and layouts for the pipeline editor interface.
        """
        # Window setup
        self.setWindowTitle("Diagram editor")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.nodeController)
        # Toolbar setup
        self.tags_menu.addActions(
            [
                self.load_pipeline_action,
                self.save_pipeline_action,
            ]
        )
        editor = self.pipelineEditorTabs.get_current_editor()

        if Config().get_user_mode():
            self.save_pipeline_action.setDisabled(True)
            editor.disable_overwrite = True

        else:
            self.save_pipeline_action.setEnabled(True)
            editor.disable_overwrite = False

        self.tags_menu.addAction(self.save_pipeline_as_action)
        self.tags_menu.addSeparator()
        self.tags_menu.addAction(self.load_pipeline_parameters_action)
        self.tags_menu.addAction(self.save_pipeline_parameters_action)
        self.tags_menu.addSeparator()
        self.tags_menu.addAction(self.run_pipeline_action)
        self.tags_menu.addAction(self.stop_pipeline_action)
        self.tags_menu.addAction(self.show_pipeline_status_action)
        self.tags_menu.addAction(self.garbage_collect_action)
        self.tags_tool_button.setText("Pipeline")
        self.tags_tool_button.setPopupMode(
            QtWidgets.QToolButton.MenuButtonPopup
        )
        self.tags_tool_button.setMenu(self.tags_menu)
        self.menu_toolbar.addActions(
            [
                self.run_pipeline_action,
                self.stop_pipeline_action,
                self.show_pipeline_status_action,
                self.garbage_collect_action,
            ]
        )
        self.menu_toolbar.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        # Layouts
        self.hLayout.addWidget(self.tags_tool_button)
        self.hLayout.addWidget(self.menu_toolbar)
        self.hLayout.addStretch(1)
        self.splitterRight.addWidget(self.iterationTable)
        self.splitterRight.addWidget(self.scrollArea)
        self.splitterRight.setSizes([400, 400])
        self.splitter0.addWidget(self.processLibrary)
        self.splitter1.addWidget(self.splitter0)
        self.splitter1.addWidget(self.pipelineEditorTabs)
        self.splitter1.addWidget(self.splitterRight)
        self.splitter1.setSizes([200, 800, 200])
        self.verticalLayout.addLayout(self.hLayout)
        self.verticalLayout.addWidget(self.splitter1)

    def loadParameters(self):
        """
        Load pipeline parameters into the current pipeline of the editor.

        This method refreshes the pipeline editor by loading the stored
        parameters and then updates the node controller accordingly.
        """
        self.pipelineEditorTabs.load_pipeline_parameters()
        self.nodeController.update_parameters()

    def loadPipeline(self):
        """
        Load a pipeline into the pipeline editor.

        This method initializes the pipeline editor with the selected
        pipeline.
        """
        self.pipelineEditorTabs.load_pipeline()

    def postprocess_pipeline_execution(self, pipeline=None):
        """
        Operations to be performed after a run has been completed.

        It can be called either within the run procedure (the user clicks on
        the "run" button and waits for the results), or after a disconnetion /
        reconnection of the client app: the user clicks on "run" with
        distributed/remote execution activated, then closes the client Mia.
        Processing takes place (possibly remotely) within a soma-workflow
        server. Then the user runs Mia again, and we have to collect the
        outputs of runs which happened (finished) while we were disconnected.

        Such post-processing includes database indexing of output data, and
        should take into account not only the current pipeline, but all past
        runs which have not been postprocessed yet.

        When called with a pipeline argument, it only deals with this one.

        The method can be called from within a worker run thread, thus has to
        be thread-safe.

        :param pipeline (Pipeline): The pipeline to postprocess. If not
                                    provided, the method will use
                                    `self.last_run_pipeline` or fetch the
                                    currently selected pipeline from the
                                    pipeline editor.
        """
        # TODO:
        # Question 1: do we have to postprocess failed runs (pipelines which
        # started and failed) ? Probably yes because they may have produced
        # some results during the first steps, and failed later.

        # Question 2: how to decide which pipelines / runs have to be
        # posptocessed now ? A pipeline may be started, then stopped or could
        # have failed, then be postprocessed. But the user can still restart
        # them in soma-workflow (or maybe Mia one day), thus they should be
        # postprocessed again then.

        # Resolve the pipeline if not provided
        pipeline = pipeline or getattr(self, "last_run_pipeline", None)

        if pipeline is None:
            pipeline = self.pipelineEditorTabs.get_current_pipeline()

        bricks_to_update = self.project.finished_bricks(
            self.get_capsul_engine(), pipeline=pipeline, include_done=False
        ).get("bricks", {})

        # Update brick execution statuses in the database
        with self.project.database.data(write=True) as database_data:

            # set state of bricks: done + exec date
            for brick_id, brick in bricks_to_update.items():
                swf_status = brick.get("swf_status")
                exec_date = (
                    swf_status[4][2] if swf_status else datetime.datetime.now()
                )
                logger.info(
                    f"Setting execution status for brick {brick_id} "
                    f"(executed at: {exec_date})"
                )
                database_data.set_value(
                    collection_name=COLLECTION_BRICK,
                    primary_key=brick_id,
                    values_dict={
                        BRICK_EXEC: "Done",
                        BRICK_EXEC_TIME: exec_date,
                    },
                )

        # Clean up orphaned data and refresh the UI
        self.project.cleanup_orphan_nonexisting_files()
        self.project.cleanup_orphan_history()
        QtThreadCall().push(
            self.main_window.data_browser.table_data.update_table
        )
        self.project.saveModifications()

    def redo(self):
        """
        Redo the last undone action on the current pipeline editor

        Supported redoable actions:
            - add_process
            - delete_process
            - export_plug
            - export_plugs
            - remove_plug
            - update_node_name
            - update_plug_value
            - add_link
            - delete_link
        """
        editor = self.pipelineEditorTabs.get_current_editor()
        redos = self.pipelineEditorTabs.redos[editor]

        # We can redo if we have an action to redo!
        if not redos:
            return

        action, *args = redos.pop()

        if action == "delete_process":
            node_name, class_process, links = args
            editor.add_named_process(
                class_process, node_name, from_redo=True, links=links
            )

        elif action == "add_process":
            (node_name,) = args
            editor.del_node(node_name, from_redo=True)

        elif action == "export_plugs":
            plug_name, _ = args
            editor._remove_plug(
                plug_names=("inputs", plug_name), from_redo=True
            )

        elif action == "remove_plug":
            plug_infos = args[0]
            multi_export = len(plug_infos) > 1
            pip_plug_names = []

            for pip_plug, node_plug, optional in plug_infos:

                if multi_export:
                    pip_plug_names.append(pip_plug[1])

                editor._export_plug(
                    temp_plug_name=node_plug[0],
                    weak_link=False,
                    optional=optional,
                    from_redo=True,
                    pipeline_parameter=pip_plug[1],
                    multi_export=multi_export,
                )

                # Reconnect original plugs
                if pip_plug[0] == "inputs":
                    source, dest = ("", pip_plug[1]), node_plug[0]

                else:
                    source, dest = node_plug[0], ("", pip_plug[1])

                link = f"{'.'.join(source)}->{'.'.join(dest)}"
                editor.scene.pipeline.add_link(link, allow_export=True)
                editor.scene.update_pipeline()

            if multi_export:
                history = ["export_plugs", pip_plug_names, node_plug[0][0]]
                editor.undos.append(history)

        elif action == "update_node_name":
            node, new_name, old_name = args
            editor.update_node_name(node, new_name, old_name, from_redo=True)

        elif action == "update_plug_value":
            node_name, new_value, plug_name, value_type = args
            editor.update_plug_value(
                node_name, new_value, plug_name, value_type, from_redo=True
            )

        elif action == "add_link":
            (link,) = args
            editor._del_link(link, from_redo=True)

        elif action == "delete_link":
            source, dest, active, weak = args
            editor.add_link(source, dest, active, weak, from_redo=True)

        editor.scene.pipeline.update_nodes_and_plugs_activation()
        self.nodeController.update_parameters()

    def register_completion_attributes(self, pipeline):
        """
        Register completion attributes for a given pipeline in the
        project database.

        This method retrieves attribute values from the pipeline's completion
        engine and records them in the project database. Only attributes
        corresponding to existing fields (tags) in the database schema are
        stored. For each pipeline parameter that resolves to a file path
        within the project directory, the attributes are associated with both
        the *current* and *initial* collections.

        :param pipeline (Pipeline): The pipeline whose completion attributes
                                    should be registered. The pipeline must
                                    provide a completion engin capable of
                                    exporting its attributes
        """
        completion = ProcessCompletionEngine.get_completion_engine(pipeline)

        if not completion:
            return

        attributes = completion.get_attribute_values().export_to_dict()

        if not attributes:
            return

        proj_dir = Path(self.project.folder).resolve()

        with self.project.database.data(write=True) as db:
            valid_tags = set(db.get_field_names(COLLECTION_CURRENT))
            attributes = {
                k: v for k, v in attributes.items() if k in valid_tags
            }

            if not attributes:
                return

            for param in pipeline.user_traits():
                value = getattr(pipeline, param)
                queue, rel_paths = [value], []

                while queue:
                    item = queue.pop(0)

                    if isinstance(item, list):
                        queue.extend(item)

                    elif isinstance(item, str):
                        apath = Path(item).resolve()

                        if proj_dir in apath.parents:
                            rel_paths.append(str(apath.relative_to(proj_dir)))

                for rel_path in rel_paths:

                    try:

                        for collection in (
                            COLLECTION_CURRENT,
                            COLLECTION_INITIAL,
                        ):
                            db.set_value(
                                collection_name=collection,
                                primary_key=rel_path,
                                values_dict=attributes,
                            )

                    except ValueError:
                        # Skip outputs that are unused or inactivated
                        continue

    def remove_progress(self):
        """
        Remove and clean up the progress widget.

        Safely removes the progress widget from the UI and frees associated
        resources. This method handles the complete lifecycle cleanup of the
        progress widget, nsuring proper Qt object disposal and memory
        management.

        Note:
            This method is idempotent - it can be safely called multiple times
            without side effects if the progress widget has already been
            removed.
        """

        if not hasattr(self, "progress") or self.progress is None:
            return

        try:
            self.progress.cleanup()
            self.progress.close()

        finally:
            # Ensure cleanup happens even if previous steps fail
            self.progress.deleteLater()
            self.progress = None

    def runPipeline(self):
        """
        Execute the current pipeline in the pipeline editor.

        This method initializes and runs the active pipeline with the
        following steps:
            1. Initializes the pipeline and validates prerequisites
            2. Sets up pipeline metadata and UI state
            3. Configures soma-workflow connection (if enabled)
            4. Starts pipeline execution with progress tracking

        The method handles both local and remote execution via soma-workflow,
        displays progress animation, and manages UI state during execution.
        """

        from soma_workflow import configuration
        from soma_workflow import constants as swconstants
        from soma_workflow.gui.workflowGui import ConnectionDialog

        execution_started = False
        self.run_pipeline_action.setDisabled(True)

        try:
            # Initialize the pipeline
            self.initialize()

            if not self.test_init:
                return

            filename = self.pipelineEditorTabs.get_current_filename()

            if filename:
                pipeline_name = os.path.basename(filename)

            else:
                pipeline = self.pipelineEditorTabs.get_current_pipeline()
                non_empty_nodes = [name for name in pipeline.nodes if name]
                pipeline_name = (
                    non_empty_nodes[0]
                    if len(non_empty_nodes) == 1
                    else "Unknown"
                )

            pipeline_name = pipeline_name.removesuffix(".py")
            # Set pipeline execution metadata
            self.last_run_pipeline = self.get_pipeline_or_process()
            self.last_status = swconstants.WORKFLOW_NOT_STARTED
            self.last_run_log = None
            self.last_pipeline_name = pipeline_name
            # Update UI status
            self.main_window.statusBar().showMessage(
                f"'{pipeline_name}' pipeline is getting run. Please wait."
            )
            QApplication.processEvents()
            # Configure soma-workflow if enabled
            engine = self.get_capsul_engine()
            swf_config = engine.settings.select_configurations(
                "global", {"somaworkflow": 'config_id=="somaworkflow"'}
            )

            if swf_config.get("use", True):
                # Get configuration files and show connection dialog
                config_file = configuration.Configuration.search_config_path()
                resource_list = (
                    configuration.Configuration.get_configured_resources(
                        config_file
                    )
                )
                login_list = configuration.Configuration.get_logins(
                    config_file
                )
                dialog = ConnectionDialog(login_list, resource_list)
                # Pre-select configured resource if available
                selected_resource = swf_config.get("computing_resource")

                if selected_resource and selected_resource in resource_list:
                    dialog.ui.combo_resources.setCurrentText(selected_resource)

                # Show dialog and handle user response
                if dialog.exec_() == 0:  # User cancelled
                    return

                # Reset execution state
                self.ignore = {}
                self.ignore_node = False
                self.key = {}
                self.brick_list = []
                self.init_clicked = False
                # Extract connection details
                resource = dialog.ui.combo_resources.currentText()
                password = dialog.ui.lineEdit_password.text()
                rsa_key = dialog.ui.lineEdit_rsa_password.text()

                # Connect to remote resource if not local
                local_resources = {
                    "",
                    "localhost",
                    configuration.Configuration.get_local_resource_id(),
                }

                if resource not in local_resources:
                    study_config = engine.study_config

                    if "SomaWorkflowConfig" in study_config.modules:
                        # Configure the computing resource
                        # TODO: Not sure this is needed...)
                        study_config.somaworkflow_computing_resource = resource
                        swc = study_config.modules["SomaWorkflowConfig"]
                        swc.set_computing_resource_password(
                            resource, password, rsa_key
                        )

                    logger.info(f"Connecting to resource: {resource}")
                    engine.connect(resource)

            # Setup progress widget and animation
            self.progress = RunProgress(self)
            self.progress.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
            )
            self.hLayout.addWidget(self.progress)
            # Setup rotating brain animation
            config = Config()
            sources_images_dir = config.getSourceImageDir()
            animation_path = os.path.join(
                sources_images_dir, "rotatingBrainVISA.gif"
            )
            self._mmovie = QMovie(animation_path)
            self._mmovie.stop()
            self._mmovie.frameChanged.connect(self._set_anim_frame)
            self._mmovie.start()
            # Update UI state for execution
            execution_started = True
            self.stop_pipeline_action.setEnabled(True)
            self.garbage_collect_action.setDisabled(True)
            # Connect signals and start execution
            self.progress.worker.finished.connect(self.finish_execution)
            self.progress.start()

        except Exception:
            logger.exception("Error while starting pipeline execution")
            raise

        finally:
            # If execution never really started, restore immediately the
            # run_pipeline_action availability
            if not execution_started:
                self.run_pipeline_action.setEnabled(True)

    def saveParameters(self):
        """
        Saves the parameters of the currently active pipeline in the pipeline
        editor.
        """
        self.pipelineEditorTabs.save_pipeline_parameters()

    def savePipeline(self, skip_overwrite_warning: bool = False):
        """
        Save the current pipeline in the pipeline editor.

        This method handles three scenarios:
            1. Save to existing file with overwrite confirmation
               (unless skipped)
            2. Save to existing file without confirmation when warning
               is skipped
            3. Save as new file when no filename exists or file is in
               protected directory

        :param skip_overwrite_warning (bool): If True, skip the overwrite
                                              confirmation dialog when saving
                                              to an existing file. Defaults to
                                              False.

        Side Effects:
            - Updates the main window status bar with save operation messages
            - May display a confirmation dialog for file overwriting
            - Saves the pipeline to disk via pipelineEditorTabs.save_pipeline()

        Note:
            Files in "mia_processes/mia_processes" directory are treated as
            protected and will trigger a "save as" operation regardless of
            other conditions.
        """
        # Initialize status message
        self.main_window.statusBar().showMessage(
            "The pipeline is getting saved. Please wait."
        )
        current_filename = self.pipelineEditorTabs.get_current_filename()
        current_pipeline = self.pipelineEditorTabs.get_current_pipeline()
        pipeline_name = current_pipeline.name

        # Check if file exists and is not in protected directory
        is_existing_file = (
            current_filename
            and os.path.join("mia_processes", "mia_processes")
            not in current_filename
        )

        # Handle existing file save with potential overwrite confirmation
        if is_existing_file:
            should_save = True

            # Show overwrite warning if not skipped
            if not skip_overwrite_warning:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("populse_mia - Save pipeline Warning!")
                msg.setText(
                    f"The following module will be overwritten:\n\n"
                    f"{os.path.abspath(current_filename)}\n\n"
                    f"Do you agree?"
                )
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Abort)
                msg.buttonClicked.connect(msg.close)
                should_save = msg.exec() == QMessageBox.Yes

            # Execute save or show cancellation message
            if should_save:
                pipeline_name = self.pipelineEditorTabs.save_pipeline(
                    new_file_name=current_filename
                )
                self.main_window.statusBar().showMessage(
                    f"The '{pipeline_name}' pipeline has been saved."
                )

            else:
                self.main_window.statusBar().showMessage(
                    f"The '{pipeline_name}' pipeline was not saved."
                )

        # Handle save as new file
        else:
            save_result = self.pipelineEditorTabs.save_pipeline()
            status_message = (
                f"The '{os.path.splitext(save_result)[0].capitalize()}' "
                f"pipeline has been saved."
                if save_result
                else "The pipeline was not saved."
            )
            self.main_window.statusBar().showMessage(status_message)

    def save_pipeline_as(self):
        """
        Save the current pipeline under a new name via 'Save As' dialog.

        This method displays a status message during the save operation and
        provides user feedback based on the save result. The pipeline name in
        the success message is capitalized and stripped of its file extension
        for display.
        """
        status_bar = self.main_window.statusBar()
        # Show progress message
        status_bar.showMessage("The pipeline is getting saved. Please wait.")
        # Attempt to save the pipeline
        save_result = self.pipelineEditorTabs.save_pipeline()

        # Display appropriate status message based on result
        if save_result:
            pipeline_name = Path(save_result).stem.capitalize()
            status_bar.showMessage(
                f"The '{pipeline_name}' pipeline has been saved."
            )

        else:
            status_bar.showMessage("The pipeline was not saved.")

    def show_status(self):
        """
        Display the execution status window with runtime information.

        Opens a new status widget window that shows the last execution run
        details, including runtime statistics, error messages, and other
        diagnostic information. The widget is stored as an instance attribute
        for potential future reference.
        """
        logger.info("Open Execution Status Window")
        self.status_widget = StatusWidget(self)
        self.status_widget.show()

    def stop_execution(self):
        """
        Interrupt pipeline execution gracefully.

        This method signals the pipeline to stop its current execution flow.
        The interruption is handled asynchronously through the progress
        tracker, allowing any in-flight operations to complete safely before
        termination.
        """
        logger.info("Pipeline execution interrupted")
        self.progress.stop_execution()

    def undo(self):
        """
        Undo the last action performed on the current pipeline editor.

        This method reverts the most recent undoable action by popping it
        from the undo stack and performing the inverse operation. The method
        handles all reversible operations in the pipeline editor interface.

        Supported undoable actions:
            - add_process: Remove the added process node
            - delete_process: Restore the deleted process node with its links
            - export_plug/export_plugs: Remove the exported pipeline plug(s)
            - remove_plug: Restore the removed plug(s) and reconnect links
            - update_node_name: Revert node name change
            - update_plug_value: Restore previous plug value
            - add_link: Remove the added connection
            - delete_link: Restore the deleted connection

        The method automatically updates the pipeline state and node
        parameters after performing the undo operation.

        Note:
            Does nothing if no undoable actions are available in the stack.
        """
        current_editor = self.pipelineEditorTabs.get_current_editor()
        undo_stack = self.pipelineEditorTabs.undos[current_editor]

        # Early return if no actions to undo
        if not undo_stack:
            return

        # Pop the most recent action and extract components
        action_data = undo_stack.pop()
        # action_type is the action to undo
        # action_args are the arguments needed to undo the action
        action_type, *action_args = action_data

        # Handle each action type
        if action_type == "add_process":
            node_name = action_args[0]
            current_editor.del_node(node_name, from_undo=True)

        elif action_type == "delete_process":
            node_name, class_name, links = action_args
            current_editor.add_named_process(
                class_name, node_name, from_undo=True, links=links
            )

        elif action_type == "export_plugs":
            parameters, node_name = action_args
            # Ensure parameters is a list for consistent handling
            parameters = (
                [parameters] if isinstance(parameters, str) else parameters
            )
            # Determine plug types and build removal list
            plugs_to_remove = []

            for parameter in parameters:
                is_input = (
                    current_editor.scene.pipeline.nodes[""]
                    .plugs[parameter]
                    .links_to
                )
                plug_type = "inputs" if is_input else "outputs"
                plugs_to_remove.append((plug_type, parameter))

            current_editor._remove_plug(
                plug_names=plugs_to_remove,
                from_undo=True,
                from_export_plugs=False,
            )

        elif action_type == "remove_plug":
            tot_plug_names = action_args[0]
            is_multi_export = len(tot_plug_names) > 1

            if is_multi_export:
                tot_pip_plug_name = []

            for pip_plug_name, node_plug_name, optional in tot_plug_names:

                if is_multi_export:
                    tot_pip_plug_name.append(pip_plug_name[1])

                # Re-export the plug
                current_editor._export_plug(
                    temp_plug_name=node_plug_name[0],
                    weak_link=False,
                    optional=optional,
                    from_undo=True,
                    pipeline_parameter=pip_plug_name[1],
                    multi_export=is_multi_export,
                )

                # Reconnect original links if they existed
                if node_plug_name and pip_plug_name:

                    # Determine source and destination based on plug direction
                    if pip_plug_name[0] == "inputs":
                        source = ("", pip_plug_name[1])
                        dest = node_plug_name[0]

                    else:
                        source = node_plug_name[0]
                        dest = ("", pip_plug_name[1])

                    # Create and add the link
                    link_string = f"{'.'.join(source)}->{'.'.join(dest)}"
                    current_editor.scene.pipeline.add_link(
                        link_string, allow_export=True
                    )

            current_editor.scene.update_pipeline()

            # Handle multi-export history
            if is_multi_export:
                history_entry = [
                    "export_plugs",
                    tot_pip_plug_name,
                    node_plug_name[0][0],
                ]
                current_editor.undos.append(history_entry)

        elif action_type == "update_node_name":
            node, new_node_name, old_node_name = action_args
            current_editor.update_node_name(
                node, new_node_name, old_node_name, from_undo=True
            )

        elif action_type == "update_plug_value":
            node_name, old_value, plug_name, value_type, _ = action_args
            current_editor.update_plug_value(
                node_name, old_value, plug_name, value_type, from_undo=True
            )

        elif action_type == "add_link":
            link = action_args[0]
            current_editor._del_link(link, from_undo=True)

        elif action_type == "delete_link":
            source, dest, active, weak = action_args
            current_editor.add_link(
                source, dest, active, weak, from_undo=True, allow_export=True
            )

        else:
            # Log warning for unknown action types
            logger.warning(f"Warning: Unknown undo action type: {action_type}")
            return

        # Update pipeline state after successful undo operation
        current_editor.scene.pipeline.update_nodes_and_plugs_activation()
        self.nodeController.update_parameters()

    @staticmethod
    def update_auto_inheritance(node, job=None):
        """
        Automatically infer database tags for output parameters from input
        parameters.

        1. **Single input case**: When only one input parameter has a database
           value, all outputs inherit from this input.
        2. **Multiple inputs with same value**: When multiple inputs exist but
            have identical database values, fallback to single input behavior.
        3. **Ambiguous case**: When multiple inputs have different database
           values, track all possible inheritance sources for user resolution.

        The process attribute auto_inheritance_dict is filled with these
        values. It's a dict with the shape::

            {output_filename: <input_spec>}

        `output_filename` is the relative filename in the database

        `<input_spec>` can be:

        * a string: filename
        * a dict::

                {input_param: input_filename}

        `auto_inheritance_dict` is built automatically, and is used as a
        fallback to :class:`ProcessMIA` `inheritance_dict`, built "manually"
        (specialized for each process) in the :meth:`ProcessMIA.list_outputs`
        when the latter does not exist, or does not specify what an output
        inherits from.

        If ambiguities still subsist, the Mia infrastructure will ask the user
        how to solve them, which is not very convenient, and error-prone, thus
        should be avoided.

        :param node: The node (typically a process or process node) whose
                     inputs and outputs are analyzed for tag inheritance.
        :param job: An optional job object containing parameter values to
                    override or populate the node's inputs and outputs.
                    Defaults to None.

        :return (dict or None): Auto-inheritance mapping if successful and no
                                job provided, None if no inheritance can be
                                determined or job is provided (in which case
                                the job object is updated in-place).
        """
        # Extract process from node if needed
        process = node.process if isinstance(node, ProcessNode) else node

        if not isinstance(process, Process) or isinstance(process, Pipeline):
            # Keep only leaf processes that actually produce outputs
            return None

        # Clean up any existing auto_inheritance_dict
        if hasattr(process, "auto_inheritance_dict"):
            del process.auto_inheritance_dict

        # Validate study configuration and project
        study_config = getattr(process, "get_study_config", lambda: None)()

        if not study_config:
            return None

        project = getattr(study_config, "project", None)

        if not project:
            # No databasing, nothing to be done.
            return None

        proj_dir = Path(project.folder).resolve()

        # Extract inputs and outputs
        if isinstance(process, Process):
            inputs = process.get_inputs()
            outputs = process.get_outputs()

            # Handle ProcessMIA specific outputs
            if hasattr(process, "list_outputs") and hasattr(
                process, "outputs"
            ):
                # Normally same as outputs, but it may contain an additional
                # "notInDb" key.
                outputs.update(process.outputs)

        else:
            traits = process.user_traits()
            outputs = {
                param: node.get_plug_value(param)
                for param, trait in traits.items()
                if trait.output
            }
            inputs = {
                param: node.get_plug_value(param)
                for param, trait in traits.items()
                if not trait.output
            }

        # Apply job parameter overrides if provided
        if job:

            for param_dict in [inputs, outputs]:

                for key in list(param_dict.keys()):

                    if key in job.param_dict:
                        job_value = job.param_dict[key]

                        if isinstance(job_value, list) and isinstance(
                            param_dict[key], list
                        ):

                            # Update list elements
                            for i, value in enumerate(job_value):

                                if i < len(param_dict[key]):
                                    param_dict[key][i] = value

                        else:
                            param_dict[key] = job_value

                    elif param_dict[key] is Undefined:
                        # Remove undefined values
                        del param_dict[key]

        else:
            # Remove undefined values
            inputs = {k: v for k, v in inputs.items() if v is not Undefined}
            outputs = {k: v for k, v in outputs.items() if v is not Undefined}

        database_inputs = {}

        with project.database.data() as database_data:

            for key, value in inputs.items():
                trait = process.trait(key)

                if not is_file_trait(trait):
                    continue

                # Handle both single values and lists
                paths = (
                    [value]
                    if isinstance(value, str)
                    else (
                        [v for v in value if isinstance(v, str)]
                        if isinstance(value, list)
                        else []
                    )
                )

                for path in paths:
                    resolved_path = Path(path).resolve()

                    if resolved_path.is_relative_to(proj_dir):
                        relative_path = resolved_path.relative_to(proj_dir)

                        if database_data.has_document(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=str(relative_path),
                        ):
                            # inheritance_dict is using full paths.
                            database_inputs[key] = path
                            break
                            # TODO: What if several path values are valid ?
                            #       Currently we keep only the first element of
                            #       the plug parameters

        if not database_inputs:
            # Zero inputs are registered in the database: We cannot
            # infer outputs tags automatically. OK we leave.
            return None

        elif len(database_inputs) == 1:
            # If the process has a single input with a value in the database,
            # then we can deduce its output database tags/attributes from it.
            inheritance_source = next(iter(database_inputs.values()))

        else:
            # Several inputs are registered in the database: We cannot
            # infer outputs tags automatically too, but we mark the ambiguity
            # to ask the user later
            unique_values = set(database_inputs.values())
            inheritance_source = (
                next(iter(unique_values))
                if len(unique_values) == 1
                else database_inputs
            )

        # Build auto inheritance dictionary
        not_in_db = set(outputs.get("notInDb", []))
        auto_inheritance_dict = {}

        for plug_name, plug_value in outputs.items():

            # Skip special parameters and high-level user parameters
            if (
                plug_name == "notInDb"
                or plug_name in not_in_db
                or (
                    process.trait(plug_name).userlevel is not None
                    and process.trait(plug_name).userlevel > 0
                )
            ):
                continue

            trait = process.trait(plug_name)

            if not trait or not is_file_trait(trait):
                continue

            # Extract all valid file paths from plug value
            # (handles nested lists)
            valid_paths = []
            todo = [plug_value]

            while todo:
                current = todo.pop(0)

                if isinstance(current, list):
                    todo.extend(current)

                elif isinstance(current, str):
                    resolved_path = Path(current).resolve()

                    if resolved_path.is_relative_to(proj_dir):
                        valid_paths.append(current)

            for path in valid_paths:
                auto_inheritance_dict[path] = inheritance_source

        if auto_inheritance_dict:

            if job:
                job.auto_inheritance_dict = auto_inheritance_dict

            else:
                return auto_inheritance_dict

        return None

    def update_inheritance(self, job, node):
        """
        Update the inheritance dictionary for a process node in a pipeline
        execution.

        This method manages metadata inheritance by updating a job's
        inheritance_dict based on the node's execution context and the
        project's inheritance history. The inheritance dictionary defines
        relationships between input and output parameters, enabling
        propagation of database tags and other metadata properties through the
        pipeline.

        The method follows this precedence order:
            1. Project-specific inheritance history (if matching parameters
               are found)
            2. Process-level inheritance dictionary (fallback)

        :param job: Job execution object containing param_dict
                    (parameter name->value mapping) and inheritance_dict
                    (will be updated by this method)
        :param node: Process node being evaluated (ProcessNode or Process
                     object). Used to determine inheritance rules via
                     context_name or name attribute.

        Note: For Pipeline nodes, the method strips the "Pipeline." prefix
              from the context_name to match against inheritance history keys.
        """
        # Extract the effective node name, handling Pipeline prefixes
        context_name = getattr(node, "context_name", node.name)
        node_name = (
            ".".join(context_name.split(".")[1:])
            if context_name.split(".")[0] == "Pipeline"
            else context_name
        )
        # Try to find matching inheritance from project history
        inheritance_dict = {}

        if node_name in self.project.node_inheritance_history:
            param_values = {
                tuple(v) if isinstance(v, list) else v
                for v in job.param_dict.values()
            }

            for inherit_dict in self.project.node_inheritance_history[
                node_name
            ]:

                # Check if any inheritance dict key matches any parameter value
                if param_values & set(inherit_dict.keys()):
                    inheritance_dict = inherit_dict
                    break

        # Fall back to process-level inheritance if no history match found
        if not inheritance_dict:
            process = node.process if hasattr(node, "process") else node
            inheritance_dict = getattr(process, "inheritance_dict", {})

        job.inheritance_dict = inheritance_dict

    def update_node_list(self, brick=None):
        """
        Update the node list with unique nodes from workflow jobs.

        Iterates through all jobs in the current workflow and adds their
        associated process nodes to the node list, ensuring no duplicates.
        Only jobs with a 'process' attribute are considered.

        :param brick: Reserved for future use. Currently unused parameter that
                      could be used for filtering or extending functionality.

        Note:
            This method modifies self.node_list in-place by extending it with
            new unique nodes. Jobs without a 'process' attribute are silently
            skipped.
        """

        # Get nodes from jobs that have a process attribute
        new_nodes = [
            job.process()
            for job in self.workflow.jobs
            if hasattr(job, "process")
        ]
        # Use set difference for efficient duplicate filtering
        existing_nodes = set(self.node_list)
        unique_new_nodes = [
            node for node in new_nodes if node not in existing_nodes
        ]
        # Extend the list with unique new nodes
        self.node_list.extend(unique_new_nodes)

    def updateProcessLibrary(self, filename):
        """
        Update the library of processes when a pipeline is saved.

        This method performs the following operations:
            1. Renames the Pipeline class in the saved file to match the
               filename
            2. Updates the __init__.py file to include the new import
            3. Refreshes the module in sys.modules if it already exists
            4. Adds the module to the process library

        :param filename: Path to the pipeline file that has been saved

        Note:
            Only processes saved in the User_processes directory are added to
            the library.
        """
        filepath = Path(filename)
        module_name = filepath.stem
        class_name = module_name.capitalize()
        # Update class name in the pipeline file using atomic replacement
        temp_file = filepath.with_suffix(filepath.suffix + "_tmp")

        try:

            with (
                open(filepath, encoding="utf-8") as source,
                open(temp_file, "w", encoding="utf-8") as temp,
            ):

                for line in source:
                    line = line.rstrip("\r\n")

                    if line.strip().startswith("class "):
                        line = f"class {class_name}(Pipeline):"

                    temp.write(f"{line}\n")

            temp_file.replace(filepath)

        except Exception:
            temp_file.unlink(missing_ok=True)
            raise

        # Check if file is in User_processes directory
        config = Config()
        user_processes_dir = (
            Path(config.get_properties_path()) / "processes" / "User_processes"
        )

        try:
            filepath.parent.resolve().relative_to(user_processes_dir.resolve())

        except ValueError:
            return  # File not in User_processes directory

        # Update __init__.py with new import if not already present
        init_file = user_processes_dir / "__init__.py"
        import_line = f"from .{module_name} import {class_name}\n"

        try:
            existing_lines = init_file.read_text(encoding="utf-8").splitlines(
                keepends=True
            )

        except FileNotFoundError:
            existing_lines = []

        if import_line not in existing_lines:

            with open(init_file, "a", encoding="utf-8") as f:
                f.write(import_line)

        # Refresh module if it exists in sys.modules
        module_full_name = f"User_processes.{module_name}"

        if module_full_name in sys.modules:
            del sys.modules[module_full_name]
            importlib.import_module("User_processes")

        # Add to system path and update process library
        base_path = str(user_processes_dir.parent)

        if base_path not in sys.path:
            sys.path.insert(0, base_path)

        self.processLibrary.pkg_library.add_package(
            "User_processes", class_name, init_package_tree=True
        )

        if base_path not in self.processLibrary.pkg_library.paths:
            self.processLibrary.pkg_library.paths.append(base_path)

        self.processLibrary.pkg_library.save()

    def update_project(self, project):
        """
        Update the project reference across all relevant components.

        This method propagates the project instance to all components that
        require access to project data, ensuring consistency across the
        application state. It also updates the node controller's visible tags
        from the project database.

        :param project: The current project instance containing application
                        data and database connections.

        Note:
            This method has the side effect of setting ProcessMIA.project as a
            class attribute, which is required for Mia brick functionality.
        """
        # Components that need direct project access
        components_requiring_project = [
            self,
            self.nodeController,
            self.pipelineEditorTabs,
            self.iterationTable,
            ProcessMIA,
        ]

        # Update project reference for all components
        for component in components_requiring_project:
            component.project = project

        # Update visible tags from project database
        with project.database.data() as database_data:
            self.nodeController.visibles_tags = database_data.get_shown_tags()

    def update_scans_list(self, iteration_list, all_iterations_list):
        """
        Update the user-selected list of scans based on iteration settings.

        This method handles the transition between regular and iterated
        pipeline modes, updating the scan list accordingly. When iteration
        mode is enabled, it builds an iterated pipeline and uses the full
        iterations list. When disabled, it extracts the pipeline from the
        iteration node and reverts to the original scan list.

        :param iteration_list: Current list of scans in the iteration table
                               (unused in current implementation)
        :param all_iterations_list: Complete list of all iteration scan lists

        Side Effects:
            - Updates UI button states
            - May modify the current pipeline (switch between regular/iterated)
            - Updates scan lists for both iteration table and pipeline editor
            - May update node parameters display
            - Falls back to database scan list if pipeline scan list is empty
        """
        self.update_user_buttons_states()
        current_editor = self.pipelineEditorTabs.get_current_editor()
        pipeline = self.pipelineEditorTabs.get_current_pipeline()
        # Find iteration node if it exists
        iteration_node_name = None

        if pipeline and hasattr(pipeline, "nodes"):

            for key in pipeline.nodes.sortedKeys:

                if "iterated_" in key:
                    iteration_node_name = key
                    break

        has_iteration = iteration_node_name is not None

        if self.iterationTable.check_box_iterate.isChecked():

            # Enable iteration mode
            if not has_iteration:
                new_pipeline = self.build_iterated_pipeline()

                if new_pipeline is None:
                    # Abort and uncheck the iteration checkbox
                    self.iterationTable.check_box_iterate.setCheckState(
                        Qt.Qt.Unchecked
                    )
                    return

                current_editor.set_pipeline(new_pipeline)
                self.displayNodeParameters("inputs", new_pipeline)

            # Update scan lists for iteration mode
            self.iteration_table_scans_list = all_iterations_list
            self.pipelineEditorTabs.scan_list = [
                scan
                for iteration_list in all_iterations_list
                for scan in iteration_list
            ]

        else:

            # Disable iteration mode
            if has_iteration:
                # Extract the original pipeline from the iteration node
                original_pipeline = pipeline.nodes[
                    iteration_node_name
                ].process.process
                current_editor.set_pipeline(original_pipeline)
                self.displayNodeParameters("inputs", original_pipeline)

            # Reset scan lists to non-iteration mode
            self.iteration_table_scans_list = []
            self.pipelineEditorTabs.scan_list = self.scan_list

        # Fallback to database scan list if needed
        if not self.pipelineEditorTabs.scan_list:

            with self.project.database.data() as database_data:
                self.pipelineEditorTabs.scan_list = (
                    database_data.get_document_names(COLLECTION_CURRENT)
                )

        self.pipelineEditorTabs.update_scans_list()

    def update_user_buttons_states(self, index=-1):
        """
        Update the visibility and state of pipeline-related UI actions.

        Updates the enabled/disabled state of pipeline actions (Run, Save,
        Save As) based on the current pipeline state. The method evaluates
        the pipeline associated with either the specified editor or the
        current active editor.

        Button states updated:
            - Run Pipeline: Disabled when pipeline is empty or None
            - Save Pipeline & Save As: Enabled only when pipeline is not
              iterated

        :param index (int): Index of the specific editor to check. If -1
                            (default), uses the currently active editor.

        Note:
            If the specified editor doesn't exist or has no scene, the
            pipeline is treated as None and buttons are disabled accordingly.
        """

        if index == -1:
            pipeline = self.pipelineEditorTabs.get_current_pipeline()

        else:
            editor = self.pipelineEditorTabs.get_editor_by_index(index)
            pipeline = getattr(
                getattr(editor, "scene", None), "pipeline", None
            )

        # Update run button state based on pipeline content
        has_processes = (
            pipeline is not None and len(pipeline.list_process_in_pipeline) > 0
        )

        if self.test_init is False:
            self.run_pipeline_action.setEnabled(has_processes)

    def update_user_mode(self):
        """
        Update widget/action visibility and functionality based on user mode
        configuration.

        In user mode:
            - Disables pipeline saving (process library unavailable)
            - Disables pipeline overwriting
            - Disables project deletion

        Also synchronizes user level across pipeline editor and node
        controller components.
        """
        config = Config()
        user_mode = config.get_user_mode()
        # Configure actions based on user mode
        actions_enabled = not user_mode
        self.save_pipeline_action.setEnabled(actions_enabled)
        self.main_window.action_delete_project.setEnabled(actions_enabled)
        # Configure current editor
        current_editor = self.pipelineEditorTabs.get_current_editor()
        current_editor.disable_overwrite = user_mode

        # Update user level if changed
        user_level = config.get_user_level()

        if user_level != current_editor.userlevel:
            current_editor.userlevel = user_level

            # Update process widget if it exists
            if self.nodeController.process_widget:
                self.nodeController.process_widget.userlevel = user_level


class RunProgress(QWidget):
    """
    A Qt widget for displaying and managing pipeline execution progress.

    This widget provides a visual progress indicator and manages the lifecycle
    of pipeline execution through a worker thread. It handles user feedback,
    error reporting, and resource cleanup.

    The widget integrates with a PipelineManagerTab to control pipeline
    execution, providing real-time feedback and graceful error handling.

    .. Methods:
        - _determine_completion_message: Analyze execution results and
                                         determine appropriate user message
        - _setup_ui: Set up the user interface for the widget
        - _show_completion_message: Display execution completion message
        - cleanup: Clean up resources and prepare for widget destruction
        - end_progress: Handle completion of pipeline execution and show
                        results
        - start: Starts the worker thread to begin the pipeline execution
                 process
        - stop_execution: Stops the execution of the pipeline by signaling the
                          worker to interrupt

    Notes:
        pipeline_manager (PipelineManagerTab):
            The pipeline manager instance that handles the pipeline operations.
        progressbar (QProgressBar):
            The progress bar widget to show execution progress.
        worker (RunWorker):
            The worker thread that runs the pipeline.
    """

    # UI Constants
    MIN_PROGRESS_WIDTH = 350  # Minimum width for progress bar (for macOS)
    AUTO_CLOSE_DELAY_MS = 2000  # Delay before auto-closing message box

    def __init__(self, pipeline_manager, settings=None):
        """
        Initialize the RunProgress widget with a progress bar and worker
        thread.

        :param pipeline_manager (PipelineManagerTab): A `PipelineManagerTab`
                                                      instance responsible for
                                                      managing the pipeline.
        :param settings (dict): A dictionary of settings to customize pipeline
                                iteration, default is None.
        """
        super().__init__()
        self.pipeline_manager = pipeline_manager
        self._setup_ui()
        self.worker = RunWorker(self.pipeline_manager)
        self.worker.finished.connect(self.end_progress)

    def _determine_completion_message(self):
        """
        Analyze execution results and determine appropriate user message.

        :return: Dictionary containing message box configuration with keys:
                 'icon', 'title', and 'text'.
        """

        if self.worker.exec_id is None:
            return {
                "icon": QMessageBox.Critical,
                "title": "Execution Failed",
                "text": (
                    "Pipeline execution failed to start.\n"
                    "Please check the status report for details."
                ),
            }

        try:
            pipeline = self.pipeline_manager.get_pipeline_or_process()
            engine = pipeline.get_study_config().engine
            engine.raise_for_status(self.worker.status, self.worker.exec_id)

            return {
                "icon": QMessageBox.Information,
                "title": "Execution Successful",
                "text": "Pipeline execution completed successfully.",
            }

        except WorkflowExecutionError as e:
            logger.error(f"Pipeline execution failed: {e}")

            return {
                "icon": QMessageBox.Critical,
                "title": "Execution Failed",
                "text": (
                    "Pipeline execution encountered an error.\n"
                    "Please check the status report for details."
                ),
            }

    def _setup_ui(self) -> None:
        """
        Set up the user interface for the widget.

        This method initializes an indeterminate progress bar with a
        predefined minimum width and places it inside a horizontal
        box layout, which is then assigned to the widget.
        """
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setRange(0, 0)  # Indeterminate progress
        self.progressbar.setValue(0)
        self.progressbar.setMinimumWidth(self.MIN_PROGRESS_WIDTH)
        layout = QHBoxLayout()
        layout.addWidget(self.progressbar)
        self.setLayout(layout)

    def _show_completion_message(self, icon, title, text):
        """
        Display execution completion message with auto-close timer.

        :param icon (QMessageBox.Icon): Message box icon type.
        :param title (str): Dialog window title.
        :param text (str): Message content to display.
        """
        message_box = QMessageBox(icon, title, text, parent=self)
        # Auto-close timer
        close_timer = QTimer()
        close_timer.singleShot(self.AUTO_CLOSE_DELAY_MS, message_box.accept)
        message_box.exec()

    def cleanup(self):
        """
        Clean up resources and prepare for widget destruction.

        Ensures the worker thread completes, disconnects signals,
        and releases resources. Should be called before widget destruction.

        Note:
            This method blocks until the worker thread finishes.
        """
        logger.debug("Cleaning up RunProgress resources...")
        self.worker.wait()
        self.worker.finished.disconnect()
        del self.worker

    def end_progress(self):
        """
        Handle completion of pipeline execution and show results.

        Called automatically when the worker thread finishes. Restores
        the application cursor, evaluates execution status, and displays
        an appropriate message to the user.

        The message dialog automatically closes after a brief delay.
        """
        self.worker.wait()
        QApplication.instance().restoreOverrideCursor()
        message_config = self._determine_completion_message()
        self._show_completion_message(**message_config)

    def start(self):
        """
        Starts the worker thread to begin the pipeline execution process.

        This method initiates the worker thread by calling its `start` method,
        which in turn triggers the execution of the pipeline.
        """
        logger.info("Starting pipeline execution")
        self.worker.start()

    def stop_execution(self):
        """
        Stops the execution of the pipeline by signaling the worker to
        interrupt.

        This method sets the `interrupt_request` flag to `True` within the
        worker thread's lock, which tells the worker to stop its execution.
        The method can be used to cancel the pipeline execution at any point
        during its run.
        """
        logger.info("Requesting pipeline execution cancellation")

        with self.worker.lock:
            self.worker.interrupt_request = True


class RunWorker(QThread):
    """
     Worker thread for executing a pipeline in the background.

    This class runs a pipeline or process using a separate thread to avoid
    blocking the GUI. Execution can be interrupted at any time by setting
    the :attr:`interrupt_request` flag while holding :attr:`lock`.

    .. Methods:
        - _check_interrupt: Check whether an interrupt has been requested
        -  _disable_nipype_copy: Recursively check and disable the copy flag
                                 for Nipype processes in the pipeline.
        - run: Run the pipeline in a background thread
    """

    def __init__(self, pipeline_manager):
        """
        Initialize the worker thread for pipeline execution.

        :param pipeline_manager (PipelineManager): The manager responsible for
                                                   configuring, running, and
                                                   monitoring the pipeline
                                                   execution.
        """
        super().__init__()
        self.pipeline_manager = pipeline_manager
        # Use this lock to modify the worker state from GUI/other thread
        self.lock = threading.RLock()
        self.status = swconstants.WORKFLOW_NOT_STARTED
        # When interrupt_request is set (within a lock session from a
        # different thread), the worker will interrupt execution and leave
        # the thread.
        self.interrupt_request = False
        self.exec_id = None

    def _check_interrupt(self, engine=None) -> bool:
        """
        Check whether an interrupt has been requested.

        If an interrupt is detected, log the event and optionally stop
        the execution engine.

        :param engine (CapsulEngine): Execution engine to interrupt if
                                      running.

        :return (bool): True if an interrupt was requested, False otherwise.
        """

        with self.lock:

            if self.interrupt_request:
                logger.info("*** INTERRUPT ***")

                if engine and self.exec_id:
                    engine.interrupt(self.exec_id)

                return True

        return False

    def _disable_nipype_copy(self, proc):
        """
        Recursively check and disable the copy flag for Nipype processes in
        the pipeline.

        This function traverses the pipeline's nodes and checks if the
        nodes contain a NipypeProcess. If it does, it sets the
        `activate_copy` flag to `False`. The recursion handles nested
        pipelines.

        :param proc: A Pipeline or NipypeProcess instance.
        """

        if isinstance(proc, Pipeline):

            for node_name, node in proc.nodes.items():
                child = getattr(node, "process", None)

                if child is None:
                    continue

                if isinstance(child, Pipeline):

                    # Only recurse for named nodes (not for inputs/outputs
                    # nodes)
                    if node_name != "":
                        self._disable_nipype_copy(child)

                elif isinstance(child, NipypeProcess):
                    child.activate_copy = False

        elif isinstance(proc, NipypeProcess):
            proc.activate_copy = False

    def run(self):
        """
        Run the pipeline in a background thread.

        The method prepares the pipeline, disables unnecessary copy flags
        for Nipype processes, rebuilds workflows when file transfer or path
        translation is required, and starts execution using the Capsul engine.
        The status is monitored until the workflow completes or an interrupt
        is requested.
        """

        if self._check_interrupt():
            return

        pipeline = self.pipeline_manager.get_pipeline_or_process()
        self._disable_nipype_copy(pipeline)

        if self._check_interrupt():
            return

        engine = self.pipeline_manager.get_capsul_engine()

        if self._check_interrupt():
            return

        engine.study_config.reset_process_counter()
        cwd = os.getcwd()
        pipeline = engine.get_process_instance(pipeline)

        if self._check_interrupt():
            return

        logger.info("- Pipeline running")
        logger.info("  ****************")
        workflow = self.pipeline_manager.workflow
        # If we are running with file transfers / translations, then we must
        # rebuild the workflow, because it has not been made with them.
        resource_id = engine.connected_to()
        resource_conf = engine.settings.select_configurations(
            resource_id, {"somaworkflow": 'config_id=="somaworkflow"'}
        ).get("capsul.engine.module.somaworkflow", {})

        if resource_conf.get("transfer_paths") or resource_conf.get(
            "path_translations"
        ):
            logger.info(
                "Rebuilding workflow for file transfers / translations..."
            )
            workflow = workflow_from_pipeline(
                pipeline, complete_parameters=True, environment=resource_id
            )
            logger.info("Running now...")

        try:

            with protected_logging():
                self.exec_id, pipeline = engine.start(
                    pipeline,
                    workflow=workflow,
                    get_pipeline=True,
                )

            while self.status in (
                swconstants.WORKFLOW_NOT_STARTED,
                swconstants.WORKFLOW_IN_PROGRESS,
            ):
                self.status = engine.wait(self.exec_id, 1, pipeline)

                if self._check_interrupt(engine):
                    return

            # Postprocess each node to index outputs, even if workflow failed
            with protected_logging():
                self.pipeline_manager.postprocess_pipeline_execution(pipeline)

        except Exception as e:
            logger.warning(
                f"{pipeline.name} has not run correctly: {e}", exc_info=True
            )

        finally:
            del self.pipeline_manager
            # Restore current working directory in case it has been changed
            os.chdir(cwd)


class StatusWidget(QWidget):
    """
     A widget that displays the current or last pipeline execution status
    along with logs and an optional Soma-Workflow monitoring panel.

    Features:
        - Shows the last known pipeline status (or a default message if
          unavailable).
        - Displays the execution log of the most recent run.
        - Provides a toggleable Soma-Workflow monitoring section.

    .. Methods:
        - toggle_soma_workflow: Show or hide the Soma-Workflow monitoring
                                widget
    """

    def __init__(self, pipeline_manager):
        """
        Initializes the execution status window for monitoring pipeline runs.

        This window displays the latest pipeline execution status, the
        execution log, and provides an optional section for Soma-Workflow
        monitoring. The log is automatically populated from the pipeline
        manager's last recorded run.

        :param pipeline_manager: The pipeline manager instance containing
        """
        super().__init__()
        self.pipeline_manager = pipeline_manager
        # Main layout
        layout = QVBoxLayout(self)
        # Execution log viewer
        self.edit = QtWidgets.QTextBrowser()
        self.edit.setText(getattr(pipeline_manager, "last_run_log", ""))
        # Status box
        status = getattr(
            pipeline_manager, "last_status", "No pipeline execution"
        )
        status_box = QtWidgets.QGroupBox("Status:")
        s_layout = QVBoxLayout(status_box)
        s_layout.addWidget(QtWidgets.QLabel(f"<b>status:</b> {status}"))
        # Soma-Workflow monitoring box
        self.swf_widget = None
        self.swf_box = QtWidgets.QGroupBox("Soma-Workflow monitoring:")
        self.swf_box.setCheckable(True)
        self.swf_box.setChecked(False)
        self.swf_box.toggled.connect(self.toggle_soma_workflow)
        self.swf_box.setLayout(QVBoxLayout())
        # Assemble layout
        layout.addWidget(status_box)
        layout.addWidget(self.swf_box)
        layout.addWidget(QtWidgets.QLabel("Execution log:"))
        layout.addWidget(self.edit)
        # Window setup
        self.resize(600, 800)
        self.setWindowTitle("Execution status")

    def toggle_soma_workflow(self, checked):
        """
        Show or hide the Soma-Workflow monitoring widget.

        If enabled and the widget does not yet exist, it is created and
        added below the status section.

        :param checked (bool): Whether the monitoring panel is enabled.
        """

        if self.swf_widget:
            self.swf_widget.setVisible(checked)
            return

        if checked:
            from soma_workflow.gui.workflowGui import (
                ApplicationModel,
                MainWindow,
            )

            model = ApplicationModel()

            with protected_logging():
                self.swf_widget = MainWindow(
                    model, None, True, None, None, interactive=False
                )

            self.swf_box.layout().addWidget(self.swf_widget)
