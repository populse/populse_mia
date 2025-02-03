"""This module is dedicated to pipeline history."""

import os.path as osp

import traits.api as traits
from capsul.api import Pipeline, Process  # , capsul_engine

from populse_mia.data_manager.project import (
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


class ProtoProcess:
    """
    Lightweight convenience class, stores a brick database entry, plus
    additional info (used)
    """

    def __init__(self, brick=None):
        self.brick = brick
        self.used = False


def data_history_pipeline(filename, project):
    """
    Get the complete "useful" history of a file in the database, as a "fake
    pipeline".

    The pipeline contains fake processes (unspecialized, direct Process
    instances), with all parameters (all being of type Any). The pipeline has
    connections, and gets all upstream ancestors of the file, so it contains
    all processing used to produce the latest version of the file (it may have
    been modified several time during the processing), and gets as inputs all
    input files which were used to produce the final data.

    Processing bricks which are not used, probably part of earlier runs which
    have been orphaned because the data file has been overwritten, are not
    listed in this history.
    """

    procs, links = get_data_history_processes(filename, project)

    if procs:
        pipeline = Pipeline()
        for proc in procs.values():
            if proc.used:
                pproc = brick_to_process(proc.brick, project)
                proc.process = pproc
                name = pproc.name
                if name in pipeline.nodes:
                    name = "{}_{}".format(name, pproc.uuid.replace("-", "_"))
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
                    # already taken as an output: export under another name
                    done = False
                    n = 0
                    while not done:
                        src2 = "%s_%d" % (src, n)
                        if src2 not in pipeline.traits():
                            pipeline.export_parameter(
                                link[2].process.node_name, link[3], src2
                            )
                            src = None
                            done = True
                        elif not pipeline.trait(src2).output:
                            src = src2
                            done = True
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
                    # already taken as an input: export under another name
                    done = False
                    n = 0
                    while not done:
                        dst2 = "%s_%d" % (dst, n)
                        if dst2 not in pipeline.traits():
                            pipeline.export_parameter(
                                link[0].process.node_name, link[1], dst2
                            )
                            dst = None
                            done = True
                        elif pipeline.trait(dst2).output:
                            dst = dst2
                            done = True
                        n += 1
            else:
                dst = f"{link[2].process.node_name}.{link[3]}"
            if src is not None and dst is not None:
                try:
                    pipeline.add_link(f"{src}->{dst}")
                except ValueError as e:
                    print(e)

        return pipeline

    else:
        return None


def get_data_history_bricks(filename, project):
    """
    Get the complete "useful" history of a file in the database, as a set of
    bricks.

    This is just a fileterd version of :func:`get_data_history_processes` (like
    :func:`data_history_pipeline` in another shape), which only returns the set
    of brick elements actually used in the "useful" history of the data.
    """

    procs, links = get_data_history_processes(filename, project)
    bricks = {proc.brick for proc in procs.values() if proc.used}
    return bricks


def get_data_history(filename, project):
    """
    Get the processing history for the given data file. Based on
    :func:`get_data_history_processes`.

    The history dict contains several elements:

    - `parent_files`: set of other data used (directly or indirectly) to
      produce the data.
    - `processes`: processing bricks set from each ancestor data which
      lead to the given one. Elements are process (brick) UUIDs.

    Returns
    -------
    history: dict
    """
    procs, links = get_data_history_processes(filename, project)

    # parse input files

    parent_files = set()
    for proc in procs.values():
        if not proc.used:
            continue
        for value in proc.brick[BRICK_INPUTS].values():
            filenames = get_filenames_in_value(
                value, project, allow_temp=False
            )
            parent_files.update(filenames)

    bricks = {proc.brick[BRICK_ID] for proc in procs.values() if proc.used}
    history = {"processes": bricks, "parent_files": parent_files}

    return history


def get_data_history_processes(filename, project):
    """
    Get the complete "useful" history of a file in the database.

    The function outputs a dict of processes (:class:`ProtoProcess` instances)
    and a set of links between them. :func:`data_history_pipeline` is a
    higher-level function which is using this one, then converts its outputs
    into a :class:`~capsul.pipeline.pipeline.Pipeline` instance to represent
    the data history.

    The processes output by this function may include extra processes that are
    looked during history search, but finally not used. They are not filtered
    out, but they are distinguished with their ``used`` attribute: those
    actually used have it set to True.

    Processing bricks which are not used, probably part of earlier runs which
    have been orphaned because the data file has been overwritten, are either
    not listed in this history, or have their ``used`` property set to False.

    Returns
    -------
    procs: dict
        {uuid: ProtoProcess instance}
    links: set
        {(src_protoprocess, src_plug_name, dst_protoprocess, dst_plug_name)}.
        Links from/to the 'exterior" are also given: in this
        case src_protoprocess or dst_protoprocess is None.
    """

    # session = project.session

    procs = {}
    links = set()
    new_procs = get_direct_proc_ancestors(filename, project, procs)
    done_procs = set()

    # keep only the latest to begin with
    later_date = None
    keep_procs = {}
    for uuid, proc in new_procs.items():
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
            print("drop earlier run:", proc.brick[BRICK_NAME], uuid)

    todo = list(keep_procs.values())

    while todo:
        proc = todo.pop(0)
        if proc in done_procs:
            continue
        done_procs.add(proc)
        proc.used = True

        print(
            "-- ancestors for:",
            proc.brick[BRICK_ID],
            proc.brick[BRICK_NAME],
            proc.brick[BRICK_EXEC_TIME],
        )
        values_w_files = {}
        for name, value in proc.brick[BRICK_INPUTS].items():
            filenames = get_filenames_in_value(value, project)
            # record inputs referencing files in the DB
            if filenames:
                print(name, "will be parsed.")
                values_w_files[name] = (value, filenames)

        for name, (value, filenames) in values_w_files.items():
            for nfilename in filenames:
                if nfilename == "<temp>":
                    print("temp file used -- history is broken")
                    prev_procs, prev_links = get_proc_ancestors_via_tmp(
                        proc, project, procs
                    )
                    links.update(prev_links)

                    n_procs = [
                        pproc
                        for pproc in prev_procs.values()
                        if pproc not in done_procs
                    ]
                    todo += n_procs
                else:
                    prev_procs = get_direct_proc_ancestors(
                        nfilename,
                        project,
                        procs,
                        before_exec_time=proc.brick[BRICK_EXEC_TIME],
                        org_proc=proc,
                    )

                    n_procs = [
                        pproc
                        for pproc in prev_procs.values()
                        if pproc not in done_procs
                    ]
                    todo += n_procs

                    # connect outputs of prev_procs which are identical to
                    print("look for value", value, "in", prev_procs.keys())
                    for pproc in prev_procs.values():
                        print("- in", pproc.brick[BRICK_NAME])
                        for pname, pval in pproc.brick[BRICK_OUTPUTS].items():
                            if pval == value or data_in_value(
                                pval, nfilename, project
                            ):
                                links.add((pproc, pname, proc, name))

                if len(prev_procs) == 0 or prev_procs == {
                    proc.brick[BRICK_ID]: proc
                }:
                    # the param has no previous processing or just the current
                    # self-modifing process: connect it to main inputs
                    links.add((None, name, proc, name))

    for proc in keep_procs.values():
        for name, value in proc.brick[BRICK_OUTPUTS].items():
            if data_in_value(value, filename, project):
                links.add((proc, name, None, name))

    print(
        "history of:",
        filename,
        ":",
        len([p for p in procs.values() if p.used]),
        "processes, ",
        len(links),
        "links",
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
    Retrieve processing bricks which are referenced in the direct filename
    history. It can get the latest before a given execution time. As exec time
    is ambiguous (several processes may have finished at exactly the same
    time), several processes may be kept for a given exec time.

    The "origin" process, if given, is excluded from this exec time filtering
    (as we are looking for the one preceding it), but still included in the
    ancestors list.

    This function manipulates processing bricks as :class:`ProtoProcess`
    instances, a light wrapper for a brick database entry.

    Parameters
    ----------
    filename: str
        data filename to inspect
    project: Project instance
        used to access database
    procs: dict
        process dict, {uuid: ProtoProcess instance}, the dict is populated when
        bricks are retrieved from the database.
    before_exec_time: datetime instance (optional)
        if it is specified, only processing bricks not newer than this time are
        used.
    only_latest: bool (optional, default: True)
        if True, only the latest processes retrieved from the history are kept.
        If ``before_exec_time`` is also used, then it is the latest before this
        time.
    org_proc: ProtoProcess instance (optional)
        if filename is the output of a process, we can specify it here in order
        to exclude it from the time filtering (otherwise only this process will
        likely remain).

    Returns
    -------
    procs: dict
        {brick uuid: ProtoProcess instance}
    """

    session = project.session
    bricks = session.get_value(COLLECTION_CURRENT, filename, TAG_BRICKS)
    print("bricks for:", filename, ":", bricks)

    new_procs = {}
    # new_links = set()

    if bricks is not None:
        for brick in bricks:
            if brick not in procs:
                proc = get_history_brick_process(
                    brick, project, before_exec_time=before_exec_time
                )
                if proc is None:
                    continue

                procs[brick] = proc
                new_procs[brick] = proc
            else:
                proc = procs[brick]
                if (
                    before_exec_time
                    and proc.brick[BRICK_EXEC_TIME] > before_exec_time
                ):
                    continue
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
                print("drop earlier run:", proc.brick[BRICK_NAME])
        if org_proc and org_proc.brick[BRICK_ID] in new_procs:
            # set back origin process, if it's in the list
            keep_procs[org_proc.brick[BRICK_ID]] = org_proc
    else:
        keep_procs = new_procs

    return keep_procs


def get_proc_ancestors_via_tmp(proc, project, procs):
    """
    Normally an internal function used in :func:`get_data_history_processes`
    and :func:`data_history_pipeline`: it is not meant to be part of a public
    API.

    Try to get upstream process(es) for proc, connected via a temp value
    ("<temp>").

    For this, try to match processes in the output files history bricks.

    Bricks are looked for, first in the process input files direct histories.
    If no matching process is found, then the full database bricks history is
    searched, which may be much slower for large databases.

    The matching is made by the "<temp>" filename and processing time, thus
    is error-prone, especially if searching the whole bricks database.

    ``proc`` should be a :class:`ProtoProcess` instance

    Returns
    -------
    new_procs: dict
        {uuid: ProtoProcess instance}
    links: set
        {(src_protoprocess, src_plug_name, dst_protoprocess, dst_plug_name)}.
        Pipeline link from/to the pipeline main plugs are also given: in this
        case src_protoprocess or dst_protoprocess is None.
    """

    new_procs = {}
    links = set()
    dlink = None
    tmp_filename = "<temp>"

    def _get_tmp_param(proc):
        """Blabla"""

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
            if proc.brick[BRICK_ID] in hprocs:
                # exclude the current proc
                del hprocs[proc.brick[BRICK_ID]]
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
                if len(new_procs) != 0:
                    break
            # if found, should we still process other filenames ?

    if len(new_procs) == 0:
        # not found in data history: search the entire bricks histories
        session = project.session
        print("temp history not found from output filenames...")

        # print('test bricks older than:', proc.exec_time)
        # filtering for date <= doesn't seem to work as I expect...
        # bricks = session.filter_documents(
        # COLLECTION_BRICK, '{%s} <= "%s"' % (BRICK_EXEC_TIME, proc.exec_time))
        candidates = {}
        bricks = session.get_documents(COLLECTION_BRICK)
        for brick in bricks:
            # if brick
            if brick[BRICK_EXEC] != "Done":
                continue
            if brick[BRICK_EXEC_TIME] > proc.brick[BRICK_EXEC_TIME]:
                continue
            # print('try brick:', brick[BRICK_NAME])
            outputs = brick[BRICK_OUTPUTS]
            for name, value in outputs.items():
                if data_in_value(value, tmp_filename, project):
                    candidates.setdefault(brick[BRICK_EXEC_TIME], []).append(
                        (brick, name)
                    )
                    # print('CANDIDATE.')
                    break
        for exec_time in sorted(candidates, reverse=True):
            for brick, name in candidates[exec_time]:
                brick_id = brick[BRICK_ID]
                hproc = procs.get(brick_id)
                if hproc is None:
                    hproc = get_history_brick_process(brick_id, project)
                    procs[brick_id] = hproc
                new_procs[brick_id] = hproc
                if dlink is None:
                    dlink = _get_tmp_param(proc)
                links.add((hproc, name, dlink[0], dlink[1]))
                print("found:", hproc.brick[BRICK_NAME], name)
                break
            break

    return new_procs, links


def find_procs_with_output(procs, filename, project):
    """
    Find in the given process list if the given filename is part of
    its outputs.

    Parameters
    ----------
    procs: iterable
        process in the list is a :class:`ProtoProcess` instance
    filename: str
        a file name
    project: :class:`~populse_mia.data_manager.project.Project` instance
        used only to get the database folder (base directory for data)

    Returns
    -------
    sprocs: dict
        exec_time: [(process, param_name), ...]
    """

    sprocs = {}
    for proc in procs:
        for name, value in proc.brick[BRICK_OUTPUTS].items():
            if data_in_value(value, filename, project):
                sprocs.setdefault(proc.brick[BRICK_EXEC_TIME], []).append(
                    (proc, name)
                )
    return sprocs


def data_in_value(value, filename, project):
    """
    Looks if the given filename is part of the given value. The value may ba a
    list, a tuple, or a dict, and may include several layers, which are parsed.

    The input filename may be the temp value "<temp>", or a filename in its
    "short" version (relative path to the project database data directory).
    """

    if isinstance(value, str):
        if filename != "<temp>":
            proj_dir = osp.join(osp.abspath(osp.normpath(project.folder)), "")
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


def is_data_entry(filename, project, allow_temp=True):
    """
    Checks if the input filename is a database entry. The return value is
    either the relative path to the database data directory, or "<temp>" if
    filename is this value and allow_temp is True (which is the default), or
    None if it is not in the database.
    """

    if allow_temp and filename == "<temp>":
        return filename

    proj_dir = osp.join(osp.abspath(osp.normpath(project.folder)), "")

    if not filename.startswith(proj_dir):
        return None

    # fmt: off
    filename = filename[len(proj_dir):]
    # fmt: on

    if project.session.has_document(COLLECTION_CURRENT, filename):
        return filename

    return None


def get_filenames_in_value(value, project, allow_temp=True):
    """
    Parses ``value``, which may be an imbrication of lists, tuples and dicts,
    and gets all filenames referenced in it. Only filenames which are database
    entries are kept, and the "<temp>" value if ``allow_temp`` is True (which
    is the default). Other non-indexed filenames are considered to be read-only
    static data (such as templates, atlases or other software-related data),
    and are not retained.
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
    Get a brick from its uuid in the database, and return it as a
    :class:`ProtoProcess` instance.

    A brick that has not been executed (its exec status is not ``"Done"``), or
    if it is newer than ``before_exec_time`` if this parameter is given, is
    discarded.

    If discarded (or nor found in the database), the return value is None.
    """

    session = project.session
    binfo = session.get_document(COLLECTION_BRICK, brick_id)
    if binfo is None:
        return None
    exec_status = binfo[BRICK_EXEC]
    if exec_status != "Done":
        return None
    exec_time = binfo[BRICK_EXEC_TIME]
    print(brick_id, "exec_time:", exec_time, ", before:", before_exec_time)
    if before_exec_time and exec_time > before_exec_time:
        # ignore later runs
        return None
    print(brick_id, ":", binfo[BRICK_NAME])

    proc = ProtoProcess(binfo)

    return proc


def brick_to_process(brick, project):
    """
    Converts a brick database entry (document) into a "fake process": a
    :class:`̀~capsul.process.process.Process` direct instance (not subclassed)
    which cannot do any actual processing, but which represents its parameters
    with values (traits and values). The process gets a ``name`` and an
    ``uuid`` from the brick, and also an ``exec_time``.
    """

    if isinstance(brick, str):
        # brick is an id
        session = project.session
        brick = session.get_document(COLLECTION_BRICK, brick)
    if brick is None:
        return None

    inputs = brick[BRICK_INPUTS]
    outputs = brick[BRICK_OUTPUTS]

    proc = Process()
    proc.name = brick[BRICK_NAME].split(".")[-1]
    proc.uuid = brick[BRICK_ID]
    proc.exec_time = brick[BRICK_EXEC_TIME]

    for name, value in inputs.items():
        proc.add_trait(name, traits.Any(output=False, optional=True))
        setattr(proc, name, value)

    for name, value in outputs.items():
        proc.add_trait(name, traits.Any(output=True, optional=True))
        setattr(proc, name, value)

    return proc
