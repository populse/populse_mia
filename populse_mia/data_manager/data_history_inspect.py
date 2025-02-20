"""
This module is dedicated to pipeline history.

:Contains:
    :Class:
        - ProtoProcess: A lightweight convenience class that stores a brick
                        database entry along with additional usage information.

    :Functions:
        - brick_to_process:  Convert a brick database entry into a
                             'fake process'.
        - data_history_pipeline: Retrieves the complete processing history of
                                 a file in the database.
        - data_in_value: Determine if the specified filename is present within
                         the given value.
        - find_procs_with_output: Identify processes that have the specified
                                  filename as part of their outputs.
        - get_data_history: Retrieves the processing history for a given data
                            file
        - get_data_history_bricks: Retrieves the complete "useful" history of
                                   a file in the database.

        - get_data_history_processes: Retrieves the complete "useful"
                                      processing history of a file in the
                                      database.
        - get_direct_proc_ancestors: Retrieve processing bricks referenced in
                                     the direct filename history.
        - get_filenames_in_value: Extract filenames from a nested structure of
                                  lists, tuples, and dictionaries.
        - get_history_brick_process: Retrieve a brick from the database and
                                     return it as `ProtoProcess` instance.
        - get_proc_ancestors_via_tmp: Retrieve upstream processes connected
                                      via a temporary value ("<temp>").
        - is_data_entry: Determine if the given filename is a valid database
                         entry.
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import logging
import os.path as osp

import traits.api as traits
from capsul.api import Pipeline, Process  # , capsul_engine

from populse_mia.data_manager import (
    BRICK_EXEC,
    BRICK_EXEC_TIME,
    BRICK_ID,
    BRICK_INPUTS,
    BRICK_NAME,
    BRICK_OUTPUTS,
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    TAG_BRICKS,
)

logger = logging.getLogger(__name__)


class ProtoProcess:
    """
    A lightweight convenience class that stores a brick database entry along
    with additional usage information.

    :param brick: The brick database entry to store. Defaults
                             to None.
    """

    def __init__(self, brick=None):
        self.brick = brick
        self.used = False


def brick_to_process(brick, project):
    """
    Convert a brick database entry into a 'fake process'.

    This function transforms a brick database entry into a `Process` instance
    that represents its parameters and values. The process gets a `name`,
    `uuid`, and `exec_time` from the brick. This "fake process" cannot perform
    actual processing but serves as a representation of the brick's traits and
    values.

    :param brick (dict or str): The brick database entry to convert. If a
                                string is provided, it is treated as the
                                brick's unique ID, and the corresponding brick
                                document is retrieved from the project's
                                database.
    :param project (object): The project object providing access to the
                             database and its documents.

    :returns (Process or None): A `Process` instance representing the brick's
                                parameters and values. Returns `None` if the
                                brick is not found.
    """

    if isinstance(brick, str):

        # If brick is an ID, retrieve the corresponding document
        with project.database.data() as database_data:
            brick = database_data.get_document(
                collection_name=COLLECTION_BRICK, primary_keys=brick
            )

    if not brick:
        return None

    brick_data = brick[0]
    inputs = brick_data[BRICK_INPUTS]
    outputs = brick_data[BRICK_OUTPUTS]
    proc = Process()
    proc.name = brick_data[BRICK_NAME].split(".")[-1]
    proc.uuid = brick_data[BRICK_ID]
    proc.exec_time = brick_data[BRICK_EXEC_TIME]

    for name, value in inputs.items():
        proc.add_trait(name, traits.Any(output=False, optional=True))
        setattr(proc, name, value)

    for name, value in outputs.items():
        proc.add_trait(name, traits.Any(output=True, optional=True))
        setattr(proc, name, value)

    return proc


def data_history_pipeline(filename, project):
    """
    Retrieves the complete processing history of a file in the database,
    formatted as a "fake pipeline".

    The generated pipeline consists of unspecialized (fake) processes,
    each representing a processing step with all parameters of type `Any`.
    The pipeline includes connections and traces all upstream ancestors
    of the file, capturing the entire processing path leading to the
    latest version of the file.

    If the file was modified multiple times, the pipeline reflects only
    the relevant processing steps that contributed to the final output.
    Orphaned processing steps from overwritten versions are omitted.

    :param filename (str): The name of the file whose processing history is
                           being retrieved.
    :param project (Project): The project object containing the database
                              and relevant details.

    :returns (Pipeline | None): A `Pipeline` object representing the
                                processing history, or `None` if no relevant
                                history is found.
    """
    procs, links = get_data_history_processes(filename, project)

    if not procs:
        return None

    pipeline = Pipeline()

    for proc in procs.values():

        if proc.used:
            pproc = brick_to_process(proc.brick, project)
            proc.process = pproc
            name = pproc.name

            if name in pipeline.nodes:
                name = f"{name}_{pproc.uuid.replace('-', '_')}"

            pproc.node_name = name
            pipeline.add_process(name, pproc)

    for link in links:

        if link[0] is None:
            src = link[1]

            if src not in pipeline.traits():
                pipeline.export_parameter(
                    link[2].process.node_name, link[3], src
                )
                src = None

            elif pipeline.trait(src).output:
                # Rename output if already taken
                n = 0

                while True:
                    src2 = f"{src}_{n}"

                    if src2 not in pipeline.traits():
                        pipeline.export_parameter(
                            link[2].process.node_name, link[3], src2
                        )
                        src = None
                        break

                    elif not pipeline.trait(src2).output:
                        src = src2
                        break

                    n += 1

        else:
            src = f"{link[0].process.node_name}.{link[1]}"

        if link[2] is None:
            dst = link[3]

            if dst not in pipeline.traits():
                pipeline.export_parameter(
                    link[0].process.node_name, link[1], dst
                )
                dst = None

            elif not pipeline.trait(dst).output:
                # Rename input if already taken
                n = 0

                while True:
                    dst2 = f"{dst}_{n}"

                    if dst2 not in pipeline.traits():
                        pipeline.export_parameter(
                            link[0].process.node_name, link[1], dst2
                        )
                        dst = None
                        break

                    elif pipeline.trait(dst2).output:
                        dst = dst2
                        break

                    n += 1

        else:
            dst = f"{link[2].process.node_name}.{link[3]}"

        if src is not None and dst is not None:

            try:
                pipeline.add_link(f"{src}->{dst}")

            except ValueError as e:
                logger.warning(e)

    return pipeline


def data_in_value(value, filename, project):
    """
    Determine if the specified filename is present within the given value.

    This function recursively searches through the `value`, which can be a
    string, list, tuple, or dictionary, to check if it contains the specified
    filename. The filename can be a special placeholder "<temp>" or a "short"
    filename, which is a relative path within the project's database data
    directory.

    :param value (str, list, tuple, or dict): The data structure to search.
                                              It can be:
        - A string representing a file path.
        - A list or tuple containing multiple file paths.
        - A dictionary where file paths are stored as values.
    :param filename (str): The filename to search for. It can be:
        - The special placeholder "<temp>" indicating a temporary value.
        - A relative file path to the project database data directory.
    :param project (object): The project object containing the project's
                             folder path as an attribute (`project.folder`).

    :returns (bool): True if the filename is found in the value,
                     False otherwise.
    """

    if isinstance(value, str):

        if filename != "<temp>":
            proj_dir = osp.abspath(osp.normpath(project.folder))
            filename = osp.join(proj_dir, filename)

        return value == filename

    if isinstance(value, (list, tuple)):

        for val in value:

            if data_in_value(val, filename, project):
                return True

        return False

    if hasattr(value, "values"):

        for val in value.values():

            if data_in_value(val, filename, project):
                return True

    return False


def find_procs_with_output(procs, filename, project):
    """
     Identify processes in the given list that have the specified filename as
     part of their outputs.

    This function searches through a list of processes to determine which ones
    have the specified filename in their output values. The results are
    organized by execution time.

    :param procs (iterable of ProtoProcess): A collection of `ProtoProcess`
                                             instances to search through.
    :param filename (str): The filename to search for within the processes'
                           outputs.
    :param project (Project): An instance of the project, used to access the
                              database folder.

    :returns (dict): A dictionary where keys are execution times and values
                     are lists of tuples. Each tuple contains a process and
                     the parameter name associated with the filename.
                     Format: `{exec_time: [(process, param_name), ...]}`.
    """

    sprocs = {}

    for proc in procs:

        for name, value in proc.brick[BRICK_OUTPUTS].items():

            if data_in_value(value, filename, project):
                sprocs.setdefault(proc.brick[BRICK_EXEC_TIME], []).append(
                    (proc, name)
                )

    return sprocs


def get_data_history(filename, project):
    """
    Retrieves the processing history for a given data file, based on
    :func:`get_data_history_processes`.

    The returned dictionary contains:

    - `"parent_files"`: A set of filenames representing data (direct or
                        indirect) used to produce the given file.
    - `"processes"`: A set of UUIDs of processing bricks that contributed
                     to the file's creation.

    :param filename (str): The name of the file whose processing history is
                           being retrieved.
    :param project (Project): The project object containing the database and
                              relevant details.

    :returns (dict): A dictionary with the following keys:
                     - `"processes"` (set): A set of UUIDs representing the
                                            processing bricks involved.
                     - `"parent_files"` (set): A set of filenames that were
                                               used to produce the data.
    """
    procs, _ = get_data_history_processes(filename, project)
    # Collect parent files (input dependencies)
    parent_files = set()

    for proc in procs.values():

        if proc.used:

            for value in proc.brick[BRICK_INPUTS].values():
                parent_files.update(
                    get_filenames_in_value(value, project, allow_temp=False)
                )

    # Collect process (brick) UUIDs
    bricks = {proc.brick[BRICK_ID] for proc in procs.values() if proc.used}
    return {"processes": bricks, "parent_files": parent_files}


def get_data_history_bricks(filename, project):
    """
    Retrieves the complete "useful" history of a file in the database as a set
    of processing bricks.

    This function is a filtered version of :func:`get_data_history_processes`,
    similar to :func:`data_history_pipeline`, but instead of constructing a
    pipeline, it returns only the set of brick elements that were actually
    used in the relevant processing history of the file.

    :param filename (str): The name of the file whose processing history is
                           being retrieved.
    :param project (Project): The project object containing the database and
                              relevant details.

    :returns (set): A set of brick elements representing the "useful"
                    processing steps that contributed to the final version of
                    the given data file.
    """
    procs, _ = get_data_history_processes(filename, project)
    return {proc.brick for proc in procs.values() if proc.used}


def get_data_history_processes(filename, project):
    """
    Retrieves the complete "useful" processing history of a file in the
    database.

    This function returns:
    - A dictionary of processes (:class:`ProtoProcess` instances), where
      keys are process UUIDs.
    - A set of links between these processes, forming the processing graph.

    Unlike :func:`data_history_pipeline`, which converts the history into a
    :class:`~capsul.pipeline.pipeline.Pipeline`, this function provides a
    lower-level representation. Some processes retrieved during history
    traversal may not be used; they are distinguished by their ``used``
    attribute (set to `True` for relevant processes).

    Processing bricks that are not used (possibly from earlier runs where
    the data file was overwritten) may either be absent from the history
    or have ``used = False``.

    :param filename (str): The name of the file whose processing history is
                           being retrieved.
    :param project (Project): The project object containing the database and
                              relevant details.

    :returns (tuple):
        - `procs` (dict): `{uuid: ProtoProcess instance}` mapping.
        - `links` (set): `{
                            (
                              src_protoprocess,
                              src_plug_name,
                              dst_protoprocess,
                              dst_plug_name
                            )
                          }`.
          External connections are represented with `None` as
          `src_protoprocess` or `dst_protoprocess`.
    """
    procs = {}
    links = set()
    new_procs = get_direct_proc_ancestors(filename, project, procs)
    done_procs = set()
    # Identify the most recent processes
    later_date = None
    keep_procs = {}

    for uuid, proc in new_procs.items():
        date = proc.brick[BRICK_EXEC_TIME]

        if later_date is None or date > later_date:
            later_date = date
            keep_procs = {uuid: proc}

        elif date == later_date:
            # Keep all processes with the same latest execution time
            keep_procs[uuid] = proc

        else:
            logger.info(f"Drop earlier run: {proc.brick[BRICK_NAME]} {uuid}")

    todo = list(keep_procs.values())

    while todo:
        proc = todo.pop(0)

        if proc in done_procs:
            continue

        done_procs.add(proc)
        proc.used = True
        logger.info(
            f"-- ancestors for: {proc.brick[BRICK_ID]} "
            f"{proc.brick[BRICK_NAME]} {proc.brick[BRICK_EXEC_TIME]}"
        )
        values_w_files = {}

        for name, value in proc.brick[BRICK_INPUTS].items():
            filenames = get_filenames_in_value(value, project)

            # Record inputs referencing database files
            if filenames:
                logger.info(f"{filenames} will be parsed.")
                values_w_files[name] = (value, filenames)

        for name, (value, filenames) in values_w_files.items():

            for nfilename in filenames:

                if nfilename == "<temp>":
                    logger.info("Temporary file used -- history is broken")
                    prev_procs, prev_links = get_proc_ancestors_via_tmp(
                        proc, project, procs
                    )
                    links.update(prev_links)
                    todo += [
                        p for p in prev_procs.values() if p not in done_procs
                    ]

                else:
                    prev_procs = get_direct_proc_ancestors(
                        nfilename,
                        project,
                        procs,
                        before_exec_time=proc.brick[BRICK_EXEC_TIME],
                        org_proc=proc,
                    )
                    todo += [
                        p for p in prev_procs.values() if p not in done_procs
                    ]
                    logger.info(
                        f"Looking for value {value} " f"in {prev_procs.keys()}"
                    )

                    for pproc in prev_procs.values():
                        logger.info(f"- in {pproc.brick[BRICK_NAME]}")

                        for pname, pval in pproc.brick[BRICK_OUTPUTS].items():

                            if pval == value or data_in_value(
                                pval, nfilename, project
                            ):
                                links.add((pproc, pname, proc, name))

                if not prev_procs or prev_procs == {
                    proc.brick[BRICK_ID]: proc
                }:
                    # The parameter has no previous processing or is
                    # self-modifying
                    links.add((None, name, proc, name))

    # Connect outputs to external scope if they match the target filename
    for proc in keep_procs.values():

        for name, value in proc.brick[BRICK_OUTPUTS].items():

            if data_in_value(value, filename, project):
                links.add((proc, name, None, name))

    logger.info(
        f"History of {filename}: "
        f"{len([p for p in procs.values() if p.used])} processes, "
        f"{len(links)} links"
    )

    return procs, links


def get_direct_proc_ancestors(
    filename,
    project,
    procs,
    before_exec_time=None,
    only_latest=True,
    org_proc=None,
):
    """
    Retrieve processing bricks referenced in the direct filename history.

    This function identifies the most recent processing steps that generated
    the given filename. If multiple processes share the same execution time,
    they are all retained to account for ambiguity. The function also allows
    filtering by execution time and excluding a specified originating process.

    :param filename (str): The data filename to inspect.
    :param project (Project): The project instance used to access the database.
    :param procs (dict): Dictionary mapping process UUIDs to `ProtoProcess`
                         instances. This dictionary is updated with newly
                         retrieved processes.
    :param before_exec_time (datetime): If specified, only processing bricks
                                        executed before this time are
                                        considered.
    :param only_latest (bool): If True (default), keeps only the latest
                               processes found in the history. If
                               `before_exec_time` is specified, retains only
                               the latest before that time.
    :param org_proc (ProtoProcess): The originating process, which is excluded
                                    from execution time filtering but included
                                    in the ancestor list.

    :returns (dict): A dictionary mapping brick UUIDs to `ProtoProcess`
                     instances.
    """

    with project.database.data() as database_data:
        bricks = database_data.get_value(
            collection_name=COLLECTION_CURRENT,
            primary_key=filename,
            field=TAG_BRICKS,
        )

    logger.info(f"Bricks for: {filename} : {bricks}")
    new_procs = {}
    # new_links = set()

    if bricks:

        for brick in bricks:

            if brick not in procs:
                proc = get_history_brick_process(
                    brick, project, before_exec_time=before_exec_time
                )

                if proc:
                    procs[brick] = proc
                    new_procs[brick] = proc

            else:
                proc = procs[brick]

                if not (
                    before_exec_time
                    and proc.brick[BRICK_EXEC_TIME] > before_exec_time
                ):
                    new_procs[brick] = procs[brick]

    if only_latest:
        # keep last run(s)
        later_date = None
        keep_procs = {}

        for uuid, proc in new_procs.items():

            if org_proc and proc is org_proc:
                # ignore origin proc for date sorting
                continue

            date = proc.brick[BRICK_EXEC_TIME]

            if later_date is None:
                later_date = date
                keep_procs[uuid] = proc

            elif date > later_date:
                later_date = date
                keep_procs = {uuid: proc}

            elif date == later_date:
                # ambiguity: keep all equivalent
                keep_procs[uuid] = proc

            else:
                logger.info(f"Drop earlier run: {proc.brick[BRICK_NAME]}")

        if org_proc and org_proc.brick[BRICK_ID] in new_procs:
            # set back origin process, if it's in the list
            keep_procs[org_proc.brick[BRICK_ID]] = org_proc

    else:
        keep_procs = new_procs

    return keep_procs


def get_filenames_in_value(value, project, allow_temp=True):
    """
    Extract filenames from a nested structure of lists, tuples, and
    dictionaries.

    This function parses the given `value`, which can be a nested combination
    of lists, tuples, and dictionaries, to retrieve all filenames referenced
    within it. Only filenames that are valid database entries or the special
    "<temp>" value (if `allow_temp` is `True`) are retained. Other filenames
    are considered read-only static data and are not included in the results.

    :param value (object): The value to parse. It can be a single string, a
                           list, tuple, dictionary, or a nested combination
                           of these types.
    :param project (object): The project object providing access to the
                             database.
    :param allow_temp (bool, optional): If `True`, includes the temporary
                                        filename "<temp>" in the results.
                                        Defaults to `True`.

    :returns (set): A set of filenames that are valid database entries or the
                    temporary filename "<temp>" (if allowed).
    """

    values = [value]
    filenames = set()

    while values:
        value = values.pop(0)

        if isinstance(value, str):
            nvalue = is_data_entry(value, project, allow_temp=allow_temp)

            if nvalue:
                filenames.add(nvalue)

        elif isinstance(value, (list, tuple)):
            values.extend(value)

        elif hasattr(value, "values"):
            values.extend(value.values())

    return filenames


def get_history_brick_process(brick_id, project, before_exec_time=None):
    """
    Retrieve a brick from the database using its UUID and return it as a
    `ProtoProcess` instance.

    This function fetches a brick from the database using its unique
    identifier (UUID). It returns the brick as a `ProtoProcess` instance if
    the brick has been executed (its execution status is "Done") and, if
    specified, its execution time is not later than `before_exec_time`. If
    the brick does not meet these criteria or is not found in the database,
    the function returns `None`.

    :param brick_id (str): The unique identifier (UUID) of the brick to
                           retrieve.
    :param project (object): The project object providing access to the
                             database.
    :param before_exec_time (str): An execution time filter. If provided,
                                   bricks executed after this timestamp are
                                   discarded.

    :returns (ProtoProcess or None): A `ProtoProcess` instance representing
                                     the brick if it meets the criteria;
                                     otherwise, `None`.
    """

    with project.database.data() as database_data:
        binfo = database_data.get_document(
            collection_name=COLLECTION_BRICK, primary_keys=brick_id
        )

    if not binfo:
        return None

    brick_data = binfo[0]
    exec_status = brick_data[BRICK_EXEC]

    if exec_status != "Done":
        return None

    exec_time = brick_data[BRICK_EXEC_TIME]
    logger.info(
        f"{brick_id} exec_time: {exec_time} before: {before_exec_time}"
    )

    if before_exec_time and exec_time > before_exec_time:
        # Ignore bricks executed after the specified time
        return None

    logger.info(f"{brick_id} : {brick_data[BRICK_NAME]}")
    return ProtoProcess(brick_data)


def get_proc_ancestors_via_tmp(proc, project, procs):
    """
    Retrieve upstream processes connected via a temporary value ("<temp>").

    This function is intended for internal use within
    `get_data_history_processes` and `data_history_pipeline`. It attempts to
    identify upstream processes connected to the given process (`proc`)
    through a temporary filename.

    The function first searches the direct history of the process's output
    files. If no matching process is found, it searches the entire database
    of bricks, which may be slower for large databases. Matching is based on
    the temporary filename and processing time, which can be error-prone.

    :param proc (ProtoProcess): The process whose ancestors need to be
                                determined.
    :param project (object): The project object providing access to the
                             session and other necessary functionalities for
                             processing.
    :param procs (dict): A dictionary of processes, where keys are process IDs
                         and values are `ProtoProcess` instances.

    :returns:
        - new_procs (dict): A dictionary mapping process UUIDs to
                            `ProtoProcess` instances.
        - links (set):
          A set of tuples representing pipeline links in the format
          `(src_protoprocess, src_plug_name, dst_protoprocess, dst_plug_name)`.
          Links from/to the pipeline main plugs are also included, where
          `src_protoprocess` or `dst_protoprocess` may be `None`.

    :Contains:
            :Private function:
                - _get_tmp_param: Identifies a process parameter associated
                                  with a temporary value.
    """
    new_procs = {}
    links = set()
    dlink = None
    tmp_filename = "<temp>"

    def _get_tmp_param(proc):
        """
        Identifies a process parameter associated with a temporary value.

        This helper function searches through the input parameters of
        a process (`proc`) to find one that references a temporary
        filename (`<temp>`) in its value.

        :param proc (ProtoProcess): The process object whose input parameters
                                    are being inspected.

        :returns: A tuple `(proc, param)` where `proc` is the process object
                  and `param` is the name of the parameter referencing
                  `<temp>`. Returns `(None, None)` if no match is found.
        """

        for param, value in proc.brick[BRICK_INPUTS].items():

            if data_in_value(value, tmp_filename, project):
                return (proc, param)

        return (None, None)  # failed...

    # look first from proc outputs history (which is more direct, less error-
    # prone, and a more limited search)
    for name, value in proc.brick[BRICK_OUTPUTS].items():
        filenames = get_filenames_in_value(value, project, allow_temp=False)

        for filename in filenames:
            hprocs = get_direct_proc_ancestors(
                filename,
                project,
                procs,
                before_exec_time=proc.brick[BRICK_EXEC_TIME],
                only_latest=False,
            )
            # Exclude the current process
            hprocs.pop(proc.brick[BRICK_ID], None)
            sprocs = find_procs_with_output(
                hprocs.values(), tmp_filename, project
            )

            for exec_time in sorted(sprocs, reverse=True):

                for hproc, param in sprocs[exec_time]:
                    new_procs[hproc.brick[BRICK_ID]] = hproc

                    if dlink is None:
                        dlink = _get_tmp_param(proc)

                    links.add((hproc, param, dlink[0], dlink[1]))
                    # we have found a link (starting with the older): stop
                    break

                if new_procs:
                    break
            # if found, should we still process other filenames ?

    if not new_procs:
        # Search the entire database of bricks if not found in direct history
        logger.info("Temporary history not found from output filenames...")
        candidates = {}

        with project.database.data() as database_data:
            bricks = database_data.get_document(
                collection_name=COLLECTION_BRICK
            )

        for brick in bricks:

            if (
                brick[BRICK_EXEC] != "Done"
                or brick[BRICK_EXEC_TIME] > proc.brick[BRICK_EXEC_TIME]
            ):
                continue

            for name, value in brick[BRICK_OUTPUTS].items():

                if data_in_value(value, tmp_filename, project):
                    candidates.setdefault(brick[BRICK_EXEC_TIME], []).append(
                        (brick, name)
                    )
                    break

        for exec_time in sorted(candidates, reverse=True):

            for brick, name in candidates[exec_time]:
                brick_id = brick[BRICK_ID]
                hproc = procs.get(brick_id) or get_history_brick_process(
                    brick_id, project
                )
                procs[brick_id] = hproc
                new_procs[brick_id] = hproc

                if dlink is None:
                    dlink = _get_tmp_param(proc)

                links.add((hproc, name, *dlink))
                logger.info(f"found: {hproc.brick[BRICK_NAME]} {name}")
                break

            break

    return new_procs, links


def is_data_entry(filename, project, allow_temp=True):
    """
    Determine if the given filename is a valid database entry within the
    specified project.

    This function checks whether the input filename is either a recognized
    temporary value ("<temp>") or a file located within the project's database
    data directory. If the filename is valid, it returns either the relative
    path to the database data directory or "<temp>" (if allowed). If the file
    is not found in the database, the function returns `None`.

    :param filename (str): The full path or special value "<temp>" to be
                           checked.
    :param project (object): The project object providing access to the
                             database and folder structure.
    :param allow_temp (bool, optional): If `True`, allows the special value
                                        "<temp>" to be considered a valid
                                        entry. Defaults to `True`.

    :returns (str or None):
        - The relative path to the project's database data directory if the
          filename is a valid database entry.
        - "<temp>" if the input is "<temp>" and `allow_temp` is `True`.
        - `None` if the filename is not a valid database entry.
    """

    if allow_temp and filename == "<temp>":
        return filename

    proj_dir = osp.join(osp.abspath(osp.normpath(project.folder)), "")

    if not filename.startswith(proj_dir):
        return None

    # fmt: off
    filename = filename[len(proj_dir):]
    # fmt: on

    with project.database.data() as database_data:

        if database_data.has_document(
            collection_name=COLLECTION_CURRENT, primary_key=filename
        ):
            return filename

    return None
