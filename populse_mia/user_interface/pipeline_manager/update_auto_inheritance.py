"""
Utility function related to automatic tag inheritance in Mia.

This module provides helper used by the pipeline execution and completion
system to infer database tag inheritance between process inputs and outputs.

The main functionality implemented here analyzes process parameters and
database entries to automatically determine how output files should inherit
metadata (tags) from input files. This mechanism acts as a fallback when a
:class:`ProcessMIA` implementation does not explicitly define its own
`inheritance_dict` in :meth:`ProcessMIA.list_outputs`.

:Contains:
    :Functions:
        - update_auto_inheritance
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################


from pathlib import Path

from capsul.api import (
    Pipeline,
    Process,
    ProcessNode,
)
from soma.controller.trait_utils import is_file_trait
from traits.api import Undefined

from populse_mia.data_manager import COLLECTION_CURRENT


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
        if hasattr(process, "list_outputs") and hasattr(process, "outputs"):
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
