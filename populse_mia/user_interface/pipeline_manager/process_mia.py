"""
Module for managing and running processes within the Populse_mia framework.

This module provides specialized classes and methods to handle the execution
and completion of processes within the Populse_mia framework. It includes
functionalities for managing process attributes, handling database
interactions, and ensuring proper inheritance of metadata tags.
The module supports various process types, including those from
mia_processes, Nipype, and Capsul.

:Contains:
    :Class:
        - MIAProcessCompletionEngine
        - MIAProcessCompletionEngineFactory
        - ProcessMIA


"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# Other imports
import logging
import os
import uuid

import nibabel as nib
import numpy as np
import traits.api as traits

# Capsul imports
from capsul.api import Pipeline, Process, capsul_engine
from capsul.attributes.completion_engine import (
    ProcessCompletionEngine,
    ProcessCompletionEngineFactory,
)
from capsul.attributes.completion_engine_factory import (
    BuiltinProcessCompletionEngineFactory,
)
from capsul.pipeline.pipeline_nodes import ProcessNode
from capsul.pipeline.process_iteration import ProcessIteration
from capsul.process.process import NipypeProcess

# nipype imports
from nipype.interfaces.base import File, InputMultiObject, traits_extension

# Soma-base import
from soma.controller.trait_utils import relax_exists_constraint
from soma.utils.weak_proxy import get_ref

# Populse_MIA imports
from populse_mia.data_manager import (
    COLLECTION_CURRENT,
    COLLECTION_INITIAL,
    TAG_BRICKS,
    TAG_CHECKSUM,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_TYPE,
)
from populse_mia.software_properties import Config

logger = logging.getLogger(__name__)


class MIAProcessCompletionEngine(ProcessCompletionEngine):
    """
    A specialized completion engine for all processes within the Populse_mia
    context.

    This engine handles both PopulseMIA processes and NipypeProcess instances
    with special consideration for their unique requirements:

    - PopulseMIA processes use their `list_outputs` method to generate outputs
      based on input parameters, primarily using filename patterns rather
      than attributes.

    - NipypeProcess instances have their MATLAB/SPM settings configured from
      the application configuration.

    The engine also manages project-specific parameters including "project"
    and "output_directory" when available in the study configuration.

    The completion system is augmented with Mia database integration, where
    attributes from input parameters (called "tags" in Mia) are added to the
    completion attributes.

    This engine tracks completed processes in the correct order, enabling
    other operations to be performed in the same sequence later.

    :Contains:
        :Method:
            - _complete_mia_process: Complete parameters for Mia-specific
                                     processes.
            - _complete_standard_process: Complete parameters for standard
                                          (non-Mia) processes.
            - complete_attributes_with_database: Augments the Capsul
                                                 completion system attributes
                                                 associated with a process.
            - complete_nipype_common: Set Nipype parameters for SPM.
            - complete_parameters: Completes file parameters from
                                   given inputs parameters.
            - complete_parameters_mia: Completion for :class:`ProcessMIA`
                                       instances.
            - get_attribute_values: Get attribute values from the fallback
                                    engine.
            - get_path_completion_engine: Get the path completion engine from
                                          the fallback engine.
            - get_project: Get the project associated with the process
            - path_attributes: Get path attributes from the fallback engine.
            - remove_switch_observe: Reimplemented since it is expects
                                     in switches completion engine.

    """

    def __init__(self, process, name, fallback_engine):
        """
        Initialize the Mia process completion engine.

        :param process: The process instance to be completed.
        :param name (str): The name of the process.
        :param fallback_engine: The fallback engine to use when MIA-specific
                                completion is not applicable.
        """
        super().__init__(process, name)
        self.fallback_engine = fallback_engine
        self.completion_progress = 0.0
        self.completion_progress_total = 0.0

    def _complete_standard_process(
        self, process, process_inputs, complete_iterations
    ):
        """
        Complete parameters for standard (non-Mia) processes.

        :param process: The process to complete.
        :param process_inputs (dict): Parameters to set on the process.
        :param complete_iterations (bool): Whether to complete iteration
                                           nodes.
        """

        # Determine node name for logging
        if not isinstance(process, Pipeline):
            context_name = getattr(process, "context_name", process.name)

            if context_name.split(".")[0] == "Pipeline":
                node_name = ".".join(context_name.split(".")[1:])

            else:
                node_name = context_name

            # Log the node type
            if isinstance(process, NipypeProcess):
                interface_path = ".".join(
                    [
                        process._nipype_interface.__module__,
                        process._nipype_interface.__class__.__name__,
                    ]
                )
                logger.info(
                    f"\n. {node_name} ({interface_path}) nipype brick ..."
                )

            else:
                process_path = ".".join(
                    [process.__module__, process.__class__.__name__]
                )
                logger.info(
                    f"\n. {node_name} ({process_path}) regular brick ..."
                )

        # Use fallback engine to complete parameters
        self.fallback_engine.complete_parameters(
            process_inputs, complete_iterations=complete_iterations
        )
        # Update progress tracking
        self.completion_progress = self.fallback_engine.completion_progress
        self.completion_progress_total = (
            self.fallback_engine.completion_progress_total
        )
        # Handle tag inheritance
        # Import here to avoid circular imports
        # isort: off
        from populse_mia.user_interface.pipeline_manager import (
            pipeline_manager_tab,
        )

        # isort: on

        PipelineManagerTab = pipeline_manager_tab.PipelineManagerTab
        auto_inheritance_dict = PipelineManagerTab.update_auto_inheritance(
            process
        )
        # auto_inheritance_dict (dict) object format:
        # - if there is no ambiguity :
        #    key: value of the output file (str)
        #    value: value of the input file (str)
        # - if ambiguous :
        #    key: output plug value (string)
        #    value: a dictionary: with key / value corresponding to each
        #           possible input file
        #           => key: name of the input plug
        #              value: value of the input plug

        if auto_inheritance_dict is not None:

            # Ensure project is set
            if not hasattr(process, "project"):

                if hasattr(process, "get_study_config"):
                    study_config = process.get_study_config()
                    project = getattr(study_config, "project", None)

                    if project is not None:
                        process.project = project

            # Apply tag inheritance if project is available
            if hasattr(process, "project"):

                for out_file in auto_inheritance_dict:
                    ProcessMIA.tags_inheritance(
                        process,
                        auto_inheritance_dict[out_file],
                        out_file,
                        node_name,
                    )

    def _complete_mia_process(
        self, process, process_inputs, complete_iterations
    ):
        """
        Complete parameters for Mia-specific processes.

        :param process: The Mia process to complete.
        :param process_inputs (dict): Parameters to set on the process.
        :param complete_iterations (bool): Whether to complete iteration
                                           nodes.
        """
        # Here the process is a ProcessMIA instance. Use the specific
        # method.
        # Determine node name for logging
        name = getattr(self.process, "context_name", self.process.name)

        if name.split(".")[0] == "Pipeline":
            node_name = ".".join(name.split(".")[1:])

        else:
            node_name = name

        # Log the node type
        process_path = ".".join(
            [process.__module__, process.__class__.__name__]
        )
        logger.info(f"\n. {node_name} ({process_path}) Mia brick ...")
        # Complete parameters using MIA-specific method
        self.complete_parameters_mia(
            process_inputs, iteration=complete_iterations
        )
        self.completion_progress = self.completion_progress_total

        # Check if initialization succeeded
        if getattr(process, "init_result", None) is False:
            return

        # Handle tag inheritance
        if (
            not hasattr(process, "inheritance_dict")
            or not process.inheritance_dict
        ):
            # The tags_inheritance() function has not been implemented in
            # the brick, so we are using auto-inheritance.
            # We're only importing PipelineManagerTab now, to avoid a
            # circular import issue
            # isort: off
            from populse_mia.user_interface.pipeline_manager import (
                pipeline_manager_tab,
            )

            # isort: on

            PipelineManagerTab = pipeline_manager_tab.PipelineManagerTab
            auto_inheritance_dict = PipelineManagerTab.update_auto_inheritance(
                process
            )
            # auto_inheritance_dict (dict) object format:
            # - if there is no ambiguity :
            #    key: value of the output file (str)
            #    value: value of the input file (str)
            # - if ambiguous :
            #    key: output plug value (string)
            #    value: a dictionary: with key / value corresponding to
            #           each possible input file
            #           => key: name of the input plug
            #              value: value of the input plug

            if auto_inheritance_dict is not None:

                # Ensure project is set
                if not hasattr(process, "project"):

                    if hasattr(process, "get_study_config"):
                        study_config = process.get_study_config()
                        project = getattr(study_config, "project", None)

                        if project is not None:
                            process.project = project

                # Apply tag inheritance if project is available
                if hasattr(process, "project"):

                    for out_file in auto_inheritance_dict:
                        ProcessMIA.tags_inheritance(
                            process,
                            auto_inheritance_dict[out_file],
                            out_file,
                            node_name,
                        )

        # We must keep a copy of inheritance dict, since it changes
        # at each iteration and is not included in workflow.
        # TODO: A better solution would be to save for each
        #       node the inheritance between plugs and not between
        #       filenames (that changes over iteration).
        # Record completion for later indexation
        project = self.get_project(process)

        if project is not None:

            # Record completion order to perform 2nd pass tags recording
            # and indexation
            if not hasattr(project, "node_inheritance_history"):
                project.node_inheritance_history = {}

            node = self.process

            if isinstance(node, Pipeline):
                node = node.pipeline_node

            # Store inheritance dict for this node
            if node_name not in project.node_inheritance_history:
                project.node_inheritance_history[node_name] = []

            if hasattr(node, "inheritance_dict"):
                project.node_inheritance_history[node_name].append(
                    node.inheritance_dict
                )

    def complete_attributes_with_database(self, process_inputs=None):
        """
        Augment the completion attributes with values from the Mia database.

        Queries the database for attributes associated with input parameters
        and adds them to the completion attributes if matches are found.

        :param process_inputs (dict): Parameters to be set on the process.
        :return: The augmented attributes collection.
        """
        process_inputs = process_inputs or {}
        # Get attributes from the fallback engine
        attributes = self.fallback_engine.get_attribute_values()
        process = self.process

        if isinstance(process, ProcessNode):
            process = process.process

        if not isinstance(process, Process) or not hasattr(
            process, "get_study_config"
        ):
            return attributes

        study_config = process.get_study_config()
        project = getattr(study_config, "project", None)

        if not project:
            return attributes

        with project.database.data() as database_data:
            # Get fields that match attributes traits
            fields = database_data.get_field_names(COLLECTION_CURRENT)
            pfields = [field for field in fields if attributes.trait(field)]

            if not pfields:
                return attributes

            # Get project directory path
            proj_dir = os.path.join(
                os.path.abspath(os.path.realpath(project.folder)), ""
            )
            proj_dir_len = len(proj_dir)

            for param, par_value in process.get_inputs().items():
                # update value from given forced input
                par_value = process_inputs.get(param, par_value)
                par_values = (
                    par_value if isinstance(par_value, list) else [par_value]
                )
                # Initialize field values lists
                field_values = [[] for _ in pfields]

                for value in par_values:

                    if not isinstance(value, str):
                        continue

                    abs_path = os.path.abspath(os.path.realpath(value))

                    if not abs_path.startswith(proj_dir):
                        continue

                    # Get relative path from project root
                    rel_value = abs_path[proj_dir_len:]
                    # Query document from database
                    document = database_data.get_document(
                        collection_name=COLLECTION_CURRENT,
                        primary_keys=rel_value,
                        fields=pfields,
                    )

                    if document:

                        for field_val_list, doc_value in zip(
                            field_values, document
                        ):
                            field_val_list.append(
                                doc_value if doc_value is not None else ""
                            )

                    else:

                        # Mark as None if not found in database
                        for field_val_list in field_values:
                            field_val_list.append(None)

                # Temporarily block attributes change notification in order to
                # avoid triggering another completion while we are already in
                # this process.
                was_fallback_ongoing = self.fallback_engine.completion_ongoing
                was_self_ongoing = self.completion_ongoing
                self.fallback_engine.completion_ongoing = True
                self.completion_ongoing = True

                # Update attributes if valid values found
                if field_values[0] and not all(
                    all(x is None for x in y) for y in field_values
                ):

                    for field, values in zip(pfields, field_values):
                        setattr(
                            attributes,
                            field,
                            (
                                values
                                if isinstance(par_value, list)
                                else values[0]
                            ),
                        )

                # Restore notification state
                self.fallback_engine.completion_ongoing = was_fallback_ongoing
                self.completion_ongoing = was_self_ongoing

        return attributes

    @staticmethod
    def complete_nipype_common(process, output_dir=True):
        """
        Configure Nipype/SPM parameters for a process.

        Sets MATLAB/SPM paths, commands, and project-specific parameters
        based on the configuration.

        :param process: The process to configure.
        :param output_dir (bool): If False, the output_directory attribute
                                  value is not initialised.
        """

        # Test for matlab launch
        if process.trait("use_mcr"):
            config = Config()

            if config.get_use_spm_standalone():
                process.use_mcr = True
                process.paths = config.get_spm_standalone_path().split()
                process.matlab_cmd = config.get_matlab_command()

            elif config.get_use_spm():
                process.use_mcr = False
                process.paths = config.get_spm_path().split()
                process.matlab_cmd = config.get_matlab_command()

        # Set project attribute if available
        study_config = process.get_study_config()
        project = getattr(study_config, "project", None)

        if not project:
            return

        process.project = project
        # Set output directory if needed

        if process.trait("output_directory"):
            out_dir = os.path.abspath(
                os.path.join(project.folder, "data", "derived_data")
            )

        else:
            logger.warning(
                f"The output_directory trait does not exist for the "
                f"{process.context_name} process!"
            )
            out_dir = None

        if output_dir and out_dir is not None:

            # Ensure this output_directory exists since it is not
            # actually an output but an input, and thus it is supposed
            # to exist in Capsul.
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            process.output_directory = out_dir

        # Handle SPM-specific configuration
        is_spm = (
            hasattr(process, "_nipype_interface_name")
            and process._nipype_interface_name == "spm"
        ) or (
            hasattr(process, "process")
            and hasattr(process.process, "_nipype_interface_name")
            and process.process._nipype_interface_name == "spm"
        )

        if is_spm:
            # Configure SPM script file
            tname = None
            tmap = getattr(process, "_nipype_trait_mapping", {})
            tname = tmap.get("_spm_script_file", "_spm_script_file")
            # FIXME: I don't understand why the _spm_script_file is in a
            #       mia_processes process (normally it should be in
            #       process.process!).
            if process.trait(tname):
                process.trait(tname).userlevel = 1

            if hasattr(process, "process") and process.process.trait(tname):
                process.process.trait(tname).userlevel = 1

            if process.trait("spm_script_file"):
                tname = "spm_script_file"

            if tname:

                # Get interface script file
                if hasattr(process, "_nipype_interface"):
                    iscript = process._nipype_interface.mlab.inputs.script_file

                elif hasattr(process, "process") and hasattr(
                    process.process, "_nipype_interface"
                ):
                    # ProcessMIA with a NipypeProcess inside
                    # fmt: off
                    iscript = (
                        process.process._nipype_interface.mlab.inputs.
                        script_file
                    )
                    # fmt: on

                else:
                    iscript = f"{process.name}.m"

                # Generate unique script file name

                process.uuid = str(uuid.uuid4())
                script_name = (
                    f"{os.path.basename(iscript)[:-2]}_" f"{process.uuid}.m"
                )
                script_path = os.path.abspath(
                    os.path.join(project.folder, "scripts", script_name)
                )
                setattr(process, tname, script_path)

            process.mfile = True

    def complete_parameters(
        self, process_inputs=None, complete_iterations=True
    ):
        """
        Complete process parameters based on input values.

        This method handles both standard Capsul processes and Mia-specific
        processes, applying the appropriate completion strategy for each.

        :param process_inputs (dict): Parameters to be set on the process.
                                      May include regular parameters and
                                      completion attributes (under
                                      'capsul_attributes' key).
        :param complete_iterations (bool): If False, iteration nodes in
                                           pipelines will not complete their
                                           parameters. This prevents
                                           modification of the input pipeline
                                           and avoids redundant iterations
                                           completion that will be done again
                                           during workflow building.
        """
        process_inputs = process_inputs or {}
        # Update progress tracking
        self.completion_progress = self.fallback_engine.completion_progress
        self.completion_progress_total = (
            self.fallback_engine.completion_progress_total
        )
        # Handle database attributes
        self.complete_attributes_with_database(process_inputs)
        process = get_ref(self.process)

        if isinstance(process, ProcessNode):
            process = process.process

        # Handle Nipype/ProcessMIA special cases
        if isinstance(process, (NipypeProcess, ProcessMIA)):
            self.complete_nipype_common(process)

        # Process completion based on type
        if not isinstance(process, ProcessMIA):
            # Standard process completion
            self._complete_standard_process(
                process, process_inputs, complete_iterations
            )

        else:
            # Mia-specific process completion
            self._complete_mia_process(
                process, process_inputs, complete_iterations
            )

    def complete_parameters_mia(
        self, process_inputs=None, iteration=False, verbose=False
    ):
        """
        Complete parameters for ProcessMIA instances.

        Uses the ProcessMIA.list_outputs method to generate output parameters
        based on input values and sets the inheritance_dict for data
        indexation.

        :param process_inputs (dict): Parameters to set on the process.
        :param iteration (bool): Whether this completion is for an iteration
                                 node.
        :param verbose (bool): If true, makes the method verbose
        """
        process_inputs = process_inputs or {}
        # Set input parameters
        self.set_parameters(process_inputs)
        # Get process and plugs information
        node = get_ref(self.process)
        process = node
        is_plugged = None

        if isinstance(node, ProcessNode):
            process = node.process
            # Identify which parameters are connected to other nodes
            is_plugged = {
                key: (bool(plug.links_to) or bool(plug.links_from))
                for key, plug in node.plugs.items()
            }

        process.init_result = None

        try:
            # Get outputs from the process
            initResult_dict = process.list_outputs(
                is_plugged=is_plugged, iteration=iteration
            )

        except Exception:
            logger.warning("Error during initialisation ...!", exc_info=True)
            initResult_dict = {}

        # Check if initialization was successful
        if not initResult_dict:
            process.init_result = False
            return  # the process is not really configured

        outputs = initResult_dict.get("outputs", {})

        if not outputs:
            process.init_result = False
            return  # the process is not really configured

        # Set output parameters
        for parameter, value in outputs.items():

            # Skip special parameters
            if parameter == "notInDb" or process.is_parameter_protected(
                parameter
            ):
                # Special non-param or set manually:
                continue

            try:
                setattr(process, parameter, value)

            except Exception:

                if verbose:
                    logger.warning(
                        f"Issue with {parameter} and {repr(value)}",
                        exc_info=True,
                    )

    def get_attribute_values(self):
        """
        Get attribute values from the fallback engine.

        :return: The attribute values collection.
        """
        return self.fallback_engine.get_attribute_values()

    def get_path_completion_engine(self):
        """
        Get the path completion engine from the fallback engine.

        :return: The path completion engine.
        """
        return self.fallback_engine.get_path_completion_engine()

    @staticmethod
    def get_project(process):
        """
        Get the project associated with a process.

        :param process: The process to get the project for.

        :return: The associated project or None if not found.

        """

        if isinstance(process, ProcessNode):
            process = process.process

        if hasattr(process, "get_study_config"):
            study_config = process.get_study_config()
            return getattr(study_config, "project", None)

        return None

    def path_attributes(self, filename, parameter=None):
        """
        Get path attributes from the fallback engine.

        :param filename (str): The filename to get attributes for.
        :param parameter (str): The parameter name associated with the
                                filename.

        :return: The path attributes.
        """
        return self.fallback_engine.path_attributes(filename, parameter)

    def remove_switch_observer(self, observer=None):
        """
        Remove a switch observer from the fallback engine.

        :param observer: The observer to remove.

        :return: The result from the fallback engine.

        """
        return self.fallback_engine.remove_switch_observer(observer)


class MIAProcessCompletionEngineFactory(ProcessCompletionEngineFactory):
    """
    Specialization of the ProcessCompletionEngineFactory for the Populse Mia
    context.

    This factory is identified by ``factory_id = "mia_completion"`` and is
    activated in a :class:`~capsul.study_config.study_config.StudyConfig`
    instance by setting the following 2 parameters:

        study_config.attributes_schema_paths += [
            'populse_mia.user_interface.pipeline_manager.process_mia'
        ]
        study_config.process_completion = 'mia_completion'


    Once activated, the completion system is applied to all processes,
    distinguishing between MIA and Nipype processes. For standard processes,
    additional database operations are performed before invoking the underlying
    completion system (such as FOM or others).

    :Contains:
        :Method:
            - get_completion_engine: get a ProcessCompletionEngine instance for
              a given process/node

    """

    factory_id = "mia_completion"

    def get_completion_engine(self, process, name=None):
        """
        Retrieves a `ProcessCompletionEngine` instance for the given process
        or node.

        :param process (Process or Node): The process or node for which to get
                                          the completion engine.
        :param name (str, optional): An optional name for the completion
                                     engine.

        :return (ProcessCompletionEngine): A completion engine instance
                                           associated with the process.
        """

        if hasattr(process, "completion_engine"):
            return process.completion_engine

        engine_factory = None

        if hasattr(process, "get_study_config"):
            study_config = process.get_study_config()
            engine = study_config.engine

            if "capsul.engine.module.attributes" in engine._loaded_modules:

                try:
                    # TODO: Define a method to store this!
                    former_factory = "builtin"
                    engine_factory = engine._modules_data["attributes"][
                        "attributes_factory"
                    ].get("process_completion", former_factory)

                except ValueError:
                    pass  # Not found

        if engine_factory is None:
            engine_factory = BuiltinProcessCompletionEngineFactory()

        fallback = engine_factory.get_completion_engine(process, name=name)
        # Handle process iteration
        in_process = (
            process.process if isinstance(process, ProcessNode) else process
        )

        if isinstance(in_process, ProcessIteration):
            # iteration nodes must follow their own way
            return fallback

        return MIAProcessCompletionEngine(process, name, fallback)


class ProcessMIA(Process):
    """
    Extends the Capsul Process class to customize execution for Mia bricks.

    This class provides specialized methods for Mia bricks, including process
    initialization, output handling, and trait management.

    .. Methods:
        - _add_field_to_collections: Add a new field to the specified
                                     collection in the database.
        - _add_or_modify_tags: Add new tags or modify existing tag values in
                               the database.
        - _all_values_identical: Checks if all dictionaries have identical
                                 content
        - _after_run_process: Try to recover the output values, when the
                              calculation has been delegated to a process in
                              ProcessMIA.
        - _find_plug_for_output:  Find the plug name associated with the given
                                  output file.
        - _get_relative_path: Converts an absolute file path to a relative
                              path based on the project folder.
        - _remove_tags: Remove specified tags from value dictionaries and the
                        database.
        - _resolve_inheritance_ambiguity: Resolves ambiguity when multiple
                                          input files could provide tags.
        - _run_process: call the run_process_mia method in the ProcessMIA
                        subclass.
        - _save_tag_values: Save tag values to the database.
        - init_default_traits: Automatically initialise necessary parameters
                               for nipype or capsul.
        - init_process: Instantiation of the process attribute given a
                        process identifier.
        - list_outputs: Override the outputs of the process.
        - load_nii: Return the header and the data of a nibabel image object.
        - make_initResult: Make the final dictionary for outputs,
                           inheritance and requirement from the
                           initialisation of a brick.
        - relax_nipype_exists_constraints: Relax the exists constraint of
                                           the process.inputs traits.
        - requirements: Capsul Process.requirements() implementation using
                        MIA's ProcessMIA.requirement attribute.
        - run_process_mia: Implements specific runs for ProcessMia
                           subclasses.
        - tags_inheritance: create tags for data.

    """

    # Class attributes used for the inheritance dictionary
    ignore_node = False
    ignore = {}
    key = {}

    def __init__(self, *args, **kwargs):
        """
        Initializes the process instance with default attributes.

        :param args (tuple): Positional arguments passed to the parent class.
        :param kwargs (dict): Keyword arguments passed to the parent class
        """
        super().__init__(*args, **kwargs)
        self.requirement = None
        self.outputs = {}
        self.inheritance_dict = {}
        self.init_result = None

    def _add_field_to_collections(self, database_schema, collection, tag_def):
        """
        Add a new field to the specified collection in the database.

        :param database_schema: The database schema context used for modifying
                                collections.
        :param collection (str): The name of the collection to which the field
                                 should be added.
        :param tag_def (dict): Dictionary containing the field definition with
                               the following keys:
                               - 'name' (str): The name of the field.
                               - 'field_type' (str): The type of the field.
                               - 'description' (str): A description of the
                                                      field.
                               - 'visibility' (str): The visibility status of
                                                     the field.
                               - 'origin' (str): The origin of the field.
                               - 'unit' (str): The unit associated with the
                                               field.
                               - 'default_value' (Any): The default value of
                                                        the field.
        """
        field_config = {
            "field_name": tag_def["name"],
            "field_type": tag_def["field_type"],
            "description": tag_def["description"],
            "visibility": tag_def["visibility"],
            "origin": tag_def["origin"],
            "unit": tag_def["unit"],
            "default_value": tag_def["default_value"],
        }
        # Add to the collection
        database_schema.add_field(
            {"collection_name": collection, **field_config}
        )

    def _add_or_modify_tags(
        self, own_tags, current_values, initial_values, field_names
    ):
        """
        Add new tags or modify existing tag values in the current and initial
        collections.

        :param own_tags (list[dict]): List of tags to be added or modified,
                                      where each tag is a dictionary with
                                      'name', 'value', 'description', etc.,
                                      keys.
        :param current_values (dict): Dictionary storing the current tag
                                      values.
        :param initial_values (dict): Dictionary storing the initial tag
                                      values.
        :param field_names (set[str]): Set of field names that exist in the
                                       database schema.
        """

        with self.project.database.schema() as database_schema:

            with database_schema.data() as database_data:

                for tag_to_add in own_tags:

                    # Ensure tag exists in the database schema
                    if tag_to_add["name"] not in field_names:
                        self._add_field_to_collections(
                            database_schema, COLLECTION_CURRENT, tag_to_add
                        )

                    if tag_to_add["name"] not in (
                        database_data.get_field_names
                    )(COLLECTION_INITIAL):
                        self._add_field_to_collections(
                            database_schema, COLLECTION_INITIAL, tag_to_add
                        )

                    # Set tag values
                    current_values[tag_to_add["name"]] = tag_to_add["value"]
                    initial_values[tag_to_add["name"]] = tag_to_add["value"]

    def _all_values_identical(self, values_dict):
        """
        Checks if all dictionaries in `values_dict` have identical content.

        :param values_dict (dict): A dictionary where each value is expected
                                   to be comparable to the others.

        :return (bool): True if all values in `values_dict` are identical or
                         if the dictionary is empty, otherwise False.
        """

        if not values_dict:
            return True

        first = None

        for values in values_dict.values():

            if first is None:
                first = values

            elif values != first:
                return False

        return True

    def _after_run_process(self, run_process_result):
        """
        Retrieve output values when the process is a NipypeProcess.

        :param run_process_result: The result of the process execution.
                                   (unused)
        """

        if hasattr(self, "process") and isinstance(
            self.process, NipypeProcess
        ):

            for mia_output in self.user_traits():
                wrapped_output = self.trait(mia_output).nipype_process_name

                if wrapped_output:
                    new_value = getattr(self.process, wrapped_output, None)

                    if (
                        new_value
                        and getattr(self, mia_output, None) != new_value
                    ):
                        setattr(self, mia_output, new_value)

    def _find_plug_for_output(self, out_file):
        """
        Find the plug name associated with the given output file.

        :param out_file (str): The output file to search for in user traits.

        :return (str | None): The name of the plug (trait) if found,
                               otherwise None.
        """

        for trait_name in self.user_traits():

            try:

                if out_file in getattr(self, trait_name, "___nothing___"):
                    return trait_name

            except Exception:
                pass

        return None

    def _get_relative_path(self, file_path, base_dir):
        """
        Converts an absolute file path to a relative path based on the
        project folder.

        :param file_path (str): The absolute path of the file.
        :param base_dir (str): The base directory to make the path relative to.

        :return (str): The relative file path.

        """
        rel_path = file_path.replace(base_dir, "")

        if rel_path and rel_path[0] in {os.sep, os.altsep}:
            rel_path = rel_path[1:]

        return rel_path

    def _remove_tags(self, tags2del, current_values, initial_values, out_file):
        """
        Remove specified tags from value dictionaries and the database.

        :param tags2del (list[str]): List of tag names to be removed.
        :param current_values (dict): Dictionary storing the current tag
                                      values.
        :param initial_values (dict): Dictionary storing the initial tag
                                      values.
        :param out_file (str): The output file associated with the tags being
                               removed.
        """

        for tag_to_del in tags2del:
            current_values.pop(tag_to_del, None)
            initial_values.pop(tag_to_del, None)

        # If tag_to_del is only in out_file, remove it from database
        relative_path = out_file.split(self.project.getName() + os.sep, 1)[-1]

        with self.project.database.data() as database_data:

            for tag in tags2del:

                for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):

                    try:
                        database_data.remove_value(
                            collection, relative_path, tag
                        )

                    except ValueError:
                        # Collection, field, or document may not exist — ignore
                        pass

    def _resolve_inheritance_ambiguity(
        self,
        all_current_values,
        all_initial_values,
        in_files,
        node_name,
        plug_name,
        out_file,
    ):
        """
        Resolves ambiguity when multiple input files could provide tags.

        This method applies a series of resolution strategies in order:
        1. If all input files have identical tag values, the first input is
           selected.
        2. If a previously stored selection rule exists, it is used.
        3. If neither condition applies, the user is prompted to manually
           resolve the ambiguity, and their decision is stored for future use.

        :param all_current_values (dict): A dictionary containing the current
                                          values for each possible input file.
        :param all_initial_values (dict): A dictionary containing the initial
                                          values for each possible input file.
        :param in_files (dict): A mapping of input file indices to their
                                corresponding file paths.
        :param node_name (str): The name of the processing node.
        :param plug_name (str | None): The name of the plug (trait) causing
                                       the ambiguity.
        :param out_file (str): The output file for which inheritance needs to
                               be resolved.
        """
        # Check if all inputs have identical tag values
        if self._all_values_identical(
            all_current_values
        ) and self._all_values_identical(all_initial_values):
            # All values equal, no ambiguity - select first input
            k, v = next(iter(all_current_values.items()))
            all_current_values.clear()
            all_current_values[k] = v
            k, v = next(iter(all_initial_values.items()))
            all_initial_values.clear()
            all_initial_values[k] = v
            self.inheritance_dict[out_file]["parent"] = in_files[k]
            return

        # Try to use previously stored selection rules
        if node_name in ProcessMIA.key:
            param = ProcessMIA.key[node_name]
            value = in_files[param]
            value_param = all_current_values.get(param)
            all_current_values.clear()

            if value_param is not None:
                all_current_values[param] = value_param

            value_param = all_initial_values.get(param)
            all_initial_values.clear()

            if value_param is not None:
                all_initial_values[param] = value_param

            self.inheritance_dict[out_file]["parent"] = value
            return

        elif (
            plug_name is not None
            and f"{node_name}{plug_name}" in ProcessMIA.key
        ):
            param = ProcessMIA.key[f"{node_name}{plug_name}"]
            value = in_files[param]
            value_param = all_current_values.get(param)
            all_current_values.clear()

            if value_param is not None:
                all_current_values[param] = value_param

            value_param = all_initial_values.get(param)
            all_initial_values.clear()

            if value_param is not None:
                all_initial_values[param] = value_param

            self.inheritance_dict[out_file]["parent"] = value
            return

        # No resolution strategy worked, prompt user
        # FIXME: There is a GUI dialog here, involving user
        #        interaction. This should probably be avoided here in
        #        a processing loop. Some pipelines, especially with
        #        iterations, may ask many many questions to users.
        #        These should be worked on earlier.
        logger.info(
            f"Ambiguity in tag inheritance for: {node_name} - "
            f"{plug_name} - {out_file}"
        )
        # We're only importing PopUpInheritanceDict now, to avoid a
        # circular import issue
        from populse_mia.user_interface.pop_ups import PopUpInheritanceDict

        pop_up = PopUpInheritanceDict(
            in_files,
            node_name,
            plug_name,
            False,
        )
        pop_up.exec()
        ProcessMIA.ignore_node = pop_up.everything

        if pop_up.ignore:
            self.inheritance_dict = {}

            if pop_up.all is True:
                ProcessMIA.ignore[node_name] = True

            else:
                ProcessMIA.ignore[f"{node_name}{plug_name}"] = True

        else:
            value = pop_up.value

            if pop_up.all is True:
                ProcessMIA.key[node_name] = pop_up.key

            else:
                ProcessMIA.key[f"{node_name}{plug_name}"] = pop_up.key

            self.inheritance_dict[out_file]["parent"] = value
            value = all_current_values.get(pop_up.key)
            all_current_values.clear()

            if value is not None:
                all_current_values[pop_up.key] = value

            value = all_initial_values.get(pop_up.key)
            all_initial_values.clear()

            if value is not None:
                all_initial_values[pop_up.key] = value

    def _run_process(self):
        """Execute the specific run method for ProcessMIA subclasses."""
        self.run_process_mia()

    def _save_tag_values(self, rel_out_file, current_values, initial_values):
        """
        Save tag values to the CURRENT and INITIAL database collections.

        :param rel_out_file (str): The relative path of the output file used
                                   as the document's primary key.
        :param current_values (dict): Dictionary containing the current tag
                                      values to be saved.
        :param initial_values (dict): Dictionary containing the initial tag
                                      values to be saved.
        """

        with self.project.database.data(write=True) as database_data:

            if current_values:

                # Ensure document exists in CURRENT collection
                if not database_data.has_document(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=rel_out_file,
                ):
                    database_data.add_document(
                        COLLECTION_CURRENT, rel_out_file
                    )

                # Update values
                database_data.set_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=rel_out_file,
                    values_dict=current_values,
                )

            if initial_values:

                # Ensure document exists in INITIAL collection
                if not database_data.has_document(
                    collection_name=COLLECTION_INITIAL,
                    primary_key=rel_out_file,
                ):
                    database_data.add_document(
                        COLLECTION_INITIAL, rel_out_file
                    )

                # Update values
                database_data.set_value(
                    collection_name=COLLECTION_INITIAL,
                    primary_key=rel_out_file,
                    values_dict=initial_values,
                )

    def init_default_traits(self):
        """
        Initialize required traits for Nipype or Capsul processes.
        """

        if "output_directory" not in self.user_traits():
            self.add_trait(
                "output_directory",
                traits.Directory(output=False, optional=True, userlevel=1),
            )

        if self.requirement and "spm" in self.requirement:
            required_traits = {
                "use_mcr": traits.Bool(optional=True, userlevel=1),
                "paths": InputMultiObject(
                    traits.Directory(), optional=True, userlevel=1
                ),
                "matlab_cmd": traits_extension.Str(optional=True, userlevel=1),
                "mfile": traits.Bool(optional=True, userlevel=1),
                "spm_script_file": File(
                    output=True,
                    optional=True,
                    input_filename=True,
                    userlevel=1,
                    desc="Path to the generated SPM Matlab script.",
                ),
            }

            for name, trait in required_traits.items():

                if name not in self.user_traits():
                    self.add_trait(name, trait)

    def init_process(self, int_name):
        """
        Instantiate the process attribute given a process identifier.

        :param int_name (str): A process identifier used to fetch the
                               process instance.
        """
        ce = (
            self.study_config.engine
            if getattr(self, "study_config", None)
            else capsul_engine()
        )
        self.process = ce.get_process_instance(int_name)

    def list_outputs(self):
        """Reset and override process outputs."""
        self.relax_nipype_exists_constraints()
        self.outputs.clear()
        self.inheritance_dict.clear()

    def load_nii(self, file_path, scaled=True, matlab_like=False):
        """
        Load a NIfTI image and return its header and data, optionally
        adjusting for MATLAB conventions.

        MATLAB and Python (in particular NumPy) treat the order of dimensions
        and the origin of the coordinate system differently. MATLAB uses main
        column order (also known as Fortran order). NumPy (and Python in
        general) uses the order of the main rows (C order). For a 3D array
        data(x, y, z) in MATLAB, the equivalent in NumPy is data[y, x, z].
        MATLAB and NumPy also handle the origin of the coordinate system
        differently:
        MATLAB's coordinate system starts with the origin in the lower
        left-hand corner (as in traditional matrix mathematics).
        NumPy's coordinate system starts with the origin in the top left-hand
        corner.
        When taking matlab_like=True as argument, the numpy matrix is
        rearranged to follow MATLAB conventions.
        Using scaled=False generates a raw unscaled data matrix (as in MATLAB
        with `header = loadnifti(fnii)` and `header.reco.data`).

        :param file_path (str): The path to a NIfTI file.
        :param scaled (bool): If True the data is scaled.
        :param matlab_like (bool): If True the data is rearranged to match the
                                   order of the dimensions and the origin of
                                   the coordinate system in Matlab.
        """
        img = nib.load(file_path)
        header = img.header
        data = img.get_fdata() if scaled else img.dataobj.get_unscaled()

        if matlab_like:
            # TODO: Should transpose for ndim>4 cases be implemented?
            # fmt: off
            axes = (1, 0, 2, 3)[:data.ndim]
            # fmt: on
            data = np.transpose(data, axes)
            data = np.flip(data, axis=0)

        return header, data

    def make_initResult(self):
        """Generate the initialization result dictionary."""
        data = {
            "requirement": self.requirement,
            "inheritance_dict": self.inheritance_dict,
            "outputs": self.outputs,
        }

        if not all(data.values()):
            missing = [k for k, v in data.items() if not v]
            context_name = getattr(self, "context_name", self.name)
            logger.warning(
                f"Issues detected during "
                f"{context_name.rsplit('.', 1)[-1]}"
                f" initialization:"
            )

            for issue in missing:
                logger.warning(f"- {issue} attribute is missing...")

        if self.outputs and "spm" in (self.requirement or []):
            self.outputs["notInDb"] = ["spm_script_file"]

        return {
            "requirement": self.requirement,
            "outputs": self.outputs,
            "inheritance_dict": self.inheritance_dict,
        }

    def relax_nipype_exists_constraints(self):
        """Relax the 'exists' constraint of the process.inputs traits."""

        if hasattr(self, "process") and hasattr(self.process, "inputs"):

            for trait in self.process.inputs.traits().values():
                relax_exists_constraint(trait)

    def requirements(self):
        """
        Return the process requirements using MIA's requirement attribute.
        """

        if self.requirement:
            return {req: "any" for req in self.requirement}

        return {}

    def run_process_mia(self):
        """
        Execute a customized run for ProcessMIA subclasses.
        """
        if self.output_directory and hasattr(self, "process"):
            self.process.output_directory = self.output_directory

        if self.requirement and "spm" in self.requirement:
            attributes = ["use_mcr", "paths", "matlab_cmd", "mfile"]

            for attr in attributes:

                if getattr(self, attr, None):
                    setattr(self.process, attr, getattr(self, attr))

            if getattr(self, "spm_script_file", None):
                self.process._spm_script_file = self.spm_script_file

    def tags_inheritance(
        self,
        in_file,
        out_file,
        node_name=None,
        own_tags=None,
        tags2del=None,
    ):
        """
        Inherit and manage data tags from input file(s) to an output file.

        This method handles the inheritance of metadata tags from one or
        more input files to an output file. It also allows adding new tags,
        modifying existing ones, or deleting unwanted tags in the process.

        Notes:
        This method performs inheritance in two ways:
        1. Immediate inheritance during process execution
        2. Deferred inheritance by storing inheritance information for later
           use during workflow generation (addresses issue #290, #310)

        In ambiguous cases (multiple input files), the method will either:
        - Use previously stored inheritance rules
        - Prompt the user for a decision if no rule exists
        - Auto-resolve if all inputs have identical tag values

        :param in_file (str or dict): Source of tag inheritance. Either:
                                      - A string representing a single input
                                        file path (unambiguous case)
                                      - A dictionary mapping plug names to
                                        corresponding input file paths
                                        (ambiguous case)
        :param out_file (str): Path of the output file that will inherit the
                               tags.
        :param node_name (str): Name of the processing node in the workflow.
        :param own_tags (list of dict): Tags to be added or modified. Each
                                        dictionary must contain:
                                        - "name": Tag identifier
                                        - "field_type": Data type of the tag
                                        - "description": Human-readable
                                                         description
                                        - "visibility": Boolean or visibility
                                                        level
                                        - "origin": Source of the tag
                                        - "unit": Unit of measurement
                                                  (if applicable)
                                        - "default_value": Default value
                                        - "value": Current value to set
        :param tags2del (list of str): Tags to be deleted from the output
                                       file.
        """

        # 1- We want out_file to inherit all the tags from in_file.
        # FIXME: We're trying to do the inheritance now. However, as in_file
        #        may not have inherited any tags yet (in the case of a
        #        non-mia_processes brick, for example, etc.), the same
        #        inheritance operation will also be performed at the end of
        #        the workflow generation (inheritance must be possible in all
        #        cases after workflow generation, see #290 and #310 and
        #        populse/mia_processes#39). This is sub-optimal, but until the
        #        #290 fix, it's the best solution we're using.

        # Initialize inheritance dictionary if it doesn't exist
        if not hasattr(self, "inheritance_dict"):
            self.inheritance_dict = {}

        # Store inheritance information for post-workflow processing
        self.inheritance_dict[out_file] = {
            "own_tags": own_tags,
            "tags2del": tags2del,
        }
        # Find the plug name associated with this output file
        plug_name = self._find_plug_for_output(out_file)
        # Tags that should never be inherited
        excluded_tags = {
            TAG_TYPE,
            TAG_BRICKS,
            TAG_CHECKSUM,
            TAG_FILENAME,
            TAG_HISTORY,
        }

        # Normalize input file format
        if isinstance(in_file, str):
            in_files = {None: in_file}
            # Store parent for inheritance at workflow completion
            self.inheritance_dict[out_file]["parent"] = in_file

        elif isinstance(in_file, dict):
            # Ambiguous case - multiple potential parents
            # self.inheritance_dict will be defined later
            in_files = in_file

        else:
            raise TypeError("in_file must be either a string or dictionary")

        # Prepare paths for database operations
        db_dir = os.path.abspath(os.path.normpath(self.project.folder))

        with self.project.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)
            rel_out_file = self._get_relative_path(out_file, db_dir)
            # Collect tag values from all input files
            all_current_values = {}
            all_initial_values = {}

            # Get all tags values for inputs
            for param, parent_file in in_files.items():
                rel_in_file = self._get_relative_path(
                    os.path.abspath(os.path.normpath(parent_file)), db_dir
                )

                # Skip self-reference case (output is one of the inputs)
                if rel_in_file == rel_out_file:
                    all_current_values = {}
                    all_initial_values = {}
                    current_values = {}
                    initial_values = {}
                    break

                # Get current tag values for this input
                current_doc = database_data.get_document(
                    collection_name=COLLECTION_CURRENT,
                    primary_keys=rel_in_file,
                )

                if current_doc:
                    # Extract relevant fields from CURRENT collection
                    current_values = {
                        field: current_doc[0][field]
                        for field in field_names
                        if field not in excluded_tags
                    }
                    # Get matching INITIAL values if available
                    initial_doc = database_data.get_document(
                        collection_name=COLLECTION_INITIAL,
                        primary_keys=rel_in_file,
                    )
                    # Tags in COLLECTION_CURRENT for in_file
                    # FIXME: If initial_doc is None, do we want a message in
                    #        stdout like the one below (currently a message is
                    #        only visible in stdout if the document is not in
                    #        the CURRENT collection)?
                    initial_values = (
                        {
                            field: initial_doc[0][field]
                            for field in current_values
                        }
                        if initial_doc
                        else {}
                    )
                    all_current_values[param] = current_values
                    all_initial_values[param] = initial_values

                else:
                    logger.warning(
                        f"{self.context_name} brick initialization warning: "
                        f"{parent_file} has no tags registered yet. "
                        f"Therefore, {out_file} cannot inherit its tags. "
                        f"This may cause subsequent initialization issues..."
                    )
                    initial_values = {}
                    current_values = {}

        # Resolve ambiguous parent selection if needed
        if (
            not ProcessMIA.ignore_node
            and len(all_current_values) >= 2
            and (node_name not in ProcessMIA.ignore)
            and (f"{node_name}{plug_name}" not in ProcessMIA.ignore)
        ):
            self._resolve_inheritance_ambiguity(
                all_current_values,
                all_initial_values,
                in_files,
                node_name,
                plug_name,
                out_file,
            )

        # Extract final values after ambiguity resolution:
        # From here if we still have several tags sets, we do not assign them
        # at all. Otherwise, set them.
        if len(all_current_values) == 1:
            initial_values.update(next(iter(all_initial_values.values())))
            current_values.update(next(iter(all_current_values.values())))

        # Apply custom tag modifications
        if own_tags:
            self._add_or_modify_tags(
                own_tags, current_values, initial_values, field_names
            )

        # Remove specified tags
        if tags2del:
            self._remove_tags(
                tags2del, current_values, initial_values, out_file
            )

        # Save updated tag values to database
        self._save_tag_values(rel_out_file, current_values, initial_values)
