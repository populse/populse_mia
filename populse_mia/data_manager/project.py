"""Module that handle the projects and their database.

:Contains:
    :Class:
        - Project

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import glob
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

import yaml
from capsul.api import Pipeline
from capsul.pipeline import pipeline_tools
from capsul.pipeline.pipeline_nodes import PipelineNode, ProcessNode

# Populse_mia imports
from populse_mia.data_manager import (
    BRICK_EXEC,
    BRICK_EXEC_TIME,
    BRICK_ID,
    BRICK_INIT,
    BRICK_INIT_TIME,
    BRICK_INPUTS,
    BRICK_NAME,
    BRICK_OUTPUTS,
    CLINICAL_TAGS,
    COLLECTION_BRICK,
    COLLECTION_CURRENT,
    COLLECTION_HISTORY,
    COLLECTION_INITIAL,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_INTEGER,
    FIELD_TYPE_JSON,
    FIELD_TYPE_LIST_STRING,
    FIELD_TYPE_STRING,
    HISTORY_BRICKS,
    HISTORY_ID,
    HISTORY_PIPELINE,
    NOT_DEFINED_VALUE,
    TAG_BRICKS,
    TAG_CHECKSUM,
    TAG_EXP_TYPE,
    TAG_FILENAME,
    TAG_HISTORY,
    TAG_ORIGIN_BUILTIN,
    TAG_ORIGIN_USER,
    TAG_TYPE,
)
from populse_mia.data_manager.database_mia import DatabaseMIA
from populse_mia.data_manager.filter import Filter

# Populse_MIA imports
from populse_mia.software_properties import Config

logger = logging.getLogger(__name__)


class Project:
    """Class that handles projects and their associated database.

    :param project_root_folder: project's path
    :param new_project: project's object

    .. Methods:
        - add_clinical_tags: add the clinical tags to the project
        - cleanup_orphan_bricks: remove orphan bricks from the database
        - cleanup_orphan_history: remove orphan bricks from the database
        - cleanup_orphan_nonexisting_files: Remove orphan files which do not
                                            exist from the database
        - del_clinical_tags: remove clinical tags to the project
        - files_in_project: return file / directory names within the
                            project folder
        - finished_bricks: retrieves a dictionary of finished bricks from
                           workflows
        - get_data_history: get the processing history for the given data file
        - getDate: return the date of creation of the project
        - get_finished_bricks_in_pipeline: retrieves a dictionary of finished
                                           bricks from a given pipeline
        - get_finished_bricks_in_workflows: retrieves a dictionary of finished
                                            bricks from a workflow
        - getFilter: return a Filter object
        - getFilterName: input box to get the name of the filter to save
        - getName: return the name of the project
        - get_orphan_bricks: identifies orphan bricks and their associated
                             weak files
        - get_orphan_history: identifies orphan history entries
        - get_orphan_nonexisting_files: get orphan files which do not exist
                                        from the database
        - getSortedTag: return the sorted tag of the project
        - getSortOrder: return the sort order of the project
        - hasUnsavedModifications: return if the project has unsaved
                                   modifications or not
        - init_filters: initialize the filters at project opening
        - loadProperties: load the properties file
        - redo: redo the last action made by the user on the project
        - reput_values: re-put the value objects in the database
        - saveConfig: save the changes in the properties file
        - save_current_filter: save the current filter
        - saveModifications: save the pending operations of the project
                             (actions still not saved)
        - setCurrentFilter: set the current filter of the project
        - setDate: set the date of the project
        - setName: set the name of the project
        - setSortedTag: set the sorted tag of the project
        - setSortOrder: set the sort order of the project
        - undo: undo the last action made by the user on the project
        - unsavedModifications: Modify the window title depending
                                of whether the project has unsaved
                                modifications or not.
        - unsaveModifications: unsaves the pending operations of the project
        - update_db_for_paths: update the history and brick tables with a new
                               project file
    """

    def __init__(self, project_root_folder, new_project):
        """Initialization of the project class.

        :param project_root_folder: project's path
        :param new_project: project's object
        """

        if project_root_folder is None:
            self.isTempProject = True
            self.folder = tempfile.mkdtemp(prefix="temp_mia_project")

        else:
            self.isTempProject = False
            self.folder = project_root_folder

        # Checks that the project is not already opened
        config = Config()
        opened_projects = config.get_opened_projects()

        if self.folder not in opened_projects:
            opened_projects.append(self.folder)
            config.set_opened_projects(opened_projects)

        else:
            raise OSError(
                f"The project at {self.folder} is already opened "
                f"in another instance of the software."
            )

        db_folder = os.path.join(self.folder, "database")
        os.makedirs(db_folder, exist_ok=True)
        file_path = os.path.join(db_folder, "mia.db")

        with open(file_path, "a"):
            os.utime(file_path, None)

        db_path = f"sqlite://{file_path}"
        self.database = DatabaseMIA(db_path)

        if new_project:
            os.makedirs(self.folder, exist_ok=True)
            os.makedirs(os.path.join(self.folder, "database"), exist_ok=True)
            os.makedirs(os.path.join(self.folder, "filters"), exist_ok=True)
            os.makedirs(os.path.join(self.folder, "data"), exist_ok=True)
            os.makedirs(
                os.path.join(self.folder, "data", "raw_data"), exist_ok=True
            )
            os.makedirs(
                os.path.join(self.folder, "data", "derived_data"),
                exist_ok=True,
            )
            os.makedirs(
                os.path.join(self.folder, "data", "downloaded_data"),
                exist_ok=True,
            )
            # Properties file created
            os.mkdir(os.path.join(self.folder, "properties"))

            if self.isTempProject:
                name = "Unnamed project"

            else:
                name = os.path.basename(self.folder)

            properties = dict(
                name=name,
                date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                sorted_tag=TAG_FILENAME,
                sort_order=0,
            )

            with open(
                os.path.join(self.folder, "properties", "properties.yml"),
                "w",
                encoding="utf8",
            ) as propertyfile:
                yaml.dump(
                    properties,
                    propertyfile,
                    default_flow_style=False,
                    allow_unicode=True,
                )

            with self.database.schema() as database_schema:
                database_schema.add_field_attributes_collection()
                # Adding current and initial collections
                database_schema.add_collection(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=TAG_FILENAME,
                    visibility=True,
                    origin=TAG_ORIGIN_BUILTIN,
                    unit=None,
                    default_value=None,
                )
                database_schema.add_collection(
                    collection_name=COLLECTION_INITIAL,
                    primary_key=TAG_FILENAME,
                    visibility=True,
                    origin=TAG_ORIGIN_BUILTIN,
                    unit=None,
                    default_value=None,
                )
                database_schema.add_collection(
                    collection_name=COLLECTION_BRICK,
                    primary_key=BRICK_ID,
                    visibility=False,
                    origin=TAG_ORIGIN_BUILTIN,
                    unit=None,
                    default_value=None,
                )
                database_schema.add_collection(
                    collection_name=COLLECTION_HISTORY,
                    primary_key=HISTORY_ID,
                    visibility=False,
                    origin=TAG_ORIGIN_BUILTIN,
                    unit=None,
                    default_value=None,
                )
                # Tags manually added
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_CURRENT,
                        "field_name": TAG_CHECKSUM,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Path checksum",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                # TODO: Maybe remove checksum tag from populse_mia initial
                #       table?
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_INITIAL,
                        "field_name": TAG_CHECKSUM,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Path checksum",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_CURRENT,
                        "field_name": TAG_TYPE,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Path type",
                        "visibility": True,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_INITIAL,
                        "field_name": TAG_TYPE,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Path type",
                        "visibility": True,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_CURRENT,
                        "field_name": TAG_EXP_TYPE,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Path exp type",
                        "visibility": True,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_INITIAL,
                        "field_name": TAG_EXP_TYPE,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Path exp type",
                        "visibility": True,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_CURRENT,
                        "field_name": TAG_BRICKS,
                        "field_type": FIELD_TYPE_LIST_STRING,
                        "description": "Path bricks",
                        "visibility": True,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_INITIAL,
                        "field_name": TAG_BRICKS,
                        "field_type": FIELD_TYPE_LIST_STRING,
                        "description": "Path bricks",
                        "visibility": True,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_CURRENT,
                        "field_name": TAG_HISTORY,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "History uuid",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_INITIAL,
                        "field_name": TAG_HISTORY,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "History uuid",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_BRICK,
                        "field_name": BRICK_NAME,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Brick name",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_BRICK,
                        "field_name": BRICK_INPUTS,
                        "field_type": FIELD_TYPE_JSON,
                        "description": "Brick input(s)",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_BRICK,
                        "field_name": BRICK_OUTPUTS,
                        "field_type": FIELD_TYPE_JSON,
                        "description": "Brick output(s)",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_BRICK,
                        "field_name": BRICK_INIT,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Brick init status",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_BRICK,
                        "field_name": BRICK_INIT_TIME,
                        "field_type": FIELD_TYPE_DATETIME,
                        "description": "Brick init time",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_BRICK,
                        "field_name": BRICK_EXEC,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Brick exec status",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_BRICK,
                        "field_name": BRICK_EXEC_TIME,
                        "field_type": FIELD_TYPE_DATETIME,
                        "description": "Brick exec time",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_HISTORY,
                        "field_name": HISTORY_PIPELINE,
                        "field_type": FIELD_TYPE_STRING,
                        "description": "Pipeline XML",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )
                database_schema.add_field(
                    {
                        "collection_name": COLLECTION_HISTORY,
                        "field_name": HISTORY_BRICKS,
                        "field_type": FIELD_TYPE_LIST_STRING,
                        "description": "Bricks list",
                        "visibility": False,
                        "origin": TAG_ORIGIN_BUILTIN,
                        "unit": None,
                        "default_value": None,
                    }
                )

                # Adding default tags for the clinical mode
                if config.get_use_clinical() is True:

                    for clinical_tag in CLINICAL_TAGS:

                        if clinical_tag == "Age":
                            field_type = FIELD_TYPE_INTEGER

                        else:
                            field_type = FIELD_TYPE_STRING

                        database_schema.add_field(
                            {
                                "collection_name": COLLECTION_CURRENT,
                                "field_name": clinical_tag,
                                "field_type": field_type,
                                "description": CLINICAL_TAGS[clinical_tag],
                                "visibility": True,
                                "origin": TAG_ORIGIN_BUILTIN,
                                "unit": None,
                                "default_value": None,
                            }
                        )
                        database_schema.add_field(
                            {
                                "collection_name": COLLECTION_INITIAL,
                                "field_name": clinical_tag,
                                "field_type": field_type,
                                "description": CLINICAL_TAGS[clinical_tag],
                                "visibility": True,
                                "origin": TAG_ORIGIN_BUILTIN,
                                "unit": None,
                                "default_value": None,
                            }
                        )

        self.properties = self.loadProperties()
        self._unsavedModifications = False
        self.undos = []
        self.redos = []
        self.init_filters()

    def add_clinical_tags(self):
        """Add new clinical tags to the project.

        :return: list of clinical tags that were added.
        """
        return_tags = []

        with self.database.schema() as database_schema:

            with database_schema.data() as database_data:
                field_names = database_data.get_field_names(COLLECTION_CURRENT)

                for clinical_tag in CLINICAL_TAGS:

                    if clinical_tag not in field_names:

                        if clinical_tag == "Age":
                            field_type = FIELD_TYPE_INTEGER

                        else:
                            field_type = FIELD_TYPE_STRING

                        database_schema.add_field(
                            {
                                "collection_name": COLLECTION_CURRENT,
                                "field_name": clinical_tag,
                                "field_type": field_type,
                                "description": CLINICAL_TAGS[clinical_tag],
                                "visibility": True,
                                "origin": TAG_ORIGIN_BUILTIN,
                                "unit": None,
                                "default_value": None,
                            }
                        )
                        database_schema.add_field(
                            {
                                "collection_name": COLLECTION_INITIAL,
                                "field_name": clinical_tag,
                                "field_type": field_type,
                                "description": CLINICAL_TAGS[clinical_tag],
                                "visibility": True,
                                "origin": TAG_ORIGIN_BUILTIN,
                                "unit": None,
                                "default_value": None,
                            }
                        )

                        # This step is redundant and could be removed, because
                        # after creating a field (just above), it seems to me
                        # that the default value is already None!
                        for scan in database_data.get_document(
                            collection_name=COLLECTION_CURRENT
                        ):
                            database_data.set_value(
                                collection_name=COLLECTION_CURRENT,
                                primary_key=scan[TAG_FILENAME],
                                values_dict={clinical_tag: None},
                            )
                            database_data.set_value(
                                collection_name=COLLECTION_INITIAL,
                                primary_key=scan[TAG_FILENAME],
                                values_dict={clinical_tag: None},
                            )

                        return_tags.append(clinical_tag)

        return return_tags

    def cleanup_orphan_bricks(self, bricks=None):
        """
        Remove orphan bricks and their associated files from the database.

        This method performs the following cleanup operations:
        1. Removes obsolete brick documents from the brick collection
        2. Removes orphaned file documents from both current and initial
           collections
        3. Deletes the corresponding physical files from the filesystem

        :param bricks (str): list of brick IDs to check for orphans.
                             If None, checks all bricks in the database.
        """
        obsolete_bricks, orphan_files = self.get_orphan_bricks(bricks)
        logger.info(f"Identified obsolete bricks: {obsolete_bricks}")

        with self.database.data(write=True) as database_data:

            for brick in obsolete_bricks:
                logger.info(f"Removing obsolete brick: {brick}")

                try:
                    database_data.remove_document(COLLECTION_BRICK, brick)

                except KeyError:
                    pass  # malformed database, the brick doesn't exist

            for file_path in orphan_files:
                logger.info(f"Removing orphan file: {file_path}")

                try:
                    database_data.remove_document(
                        COLLECTION_CURRENT, file_path
                    )
                    database_data.remove_document(
                        COLLECTION_INITIAL, file_path
                    )

                except KeyError:
                    pass  # malformed database, the file doesn't exist

                # Remove physical file if it exists
                full_path = os.path.join(self.folder, file_path)

                if os.path.exists(full_path):
                    os.unlink(full_path)

    def cleanup_orphan_history(self):
        """
        Remove orphan histories, their associated bricks, and files from
        the database.

        This method performs three cleanup operations:
        1. Removes obsolete history documents from the history collection
        2. Removes orphaned brick documents from the brick collection
        3. Removes orphaned file documents from both current and initial
           collections, along with their corresponding physical files
        """
        (obsolete_histories, obsolete_bricks, orphan_files) = (
            self.get_orphan_history()
        )
        logger.info(f"Orphan histories: {obsolete_histories}")
        logger.info(f"Orphan bricks: {obsolete_bricks}")

        with self.database.data(write=True) as database_data:

            for hist in obsolete_histories:
                logger.info(f"Removing obsolete history: {hist}")

                try:
                    database_data.remove_document(
                        collection_name=COLLECTION_HISTORY, primary_key=hist
                    )

                except KeyError:
                    pass  # malformed database, the brick doesn't exist

            for brick in obsolete_bricks:
                logger.info(f"Removing obsolete brick: {brick}")

                try:
                    database_data.remove_document(
                        collection_name=COLLECTION_BRICK, primary_key=brick
                    )

                except KeyError:
                    pass  # malformed database, the brick doesn't exist

            for file_path in orphan_files:
                logger.info(f"Removing orphan file: {file_path}")

                for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):

                    try:
                        database_data.remove_document(
                            collection_name=collection, primary_key=file_path
                        )

                    except KeyError:
                        pass  # malformed database, the file doesn't exist

                full_path = os.path.join(self.folder, file_path)

                if os.path.exists(full_path):
                    os.unlink(full_path)

    def cleanup_orphan_nonexisting_files(self):
        """
        Remove database entries for files that no longer exist in the
        filesystem.

        This method:
        1. Identifies files referenced in the database that are missing
           from disk
        2. Removes their entries from both current and initial collections
        3. Ensures any remaining physical files are deleted (defensive
           cleanup)
        """
        orphan_files = self.get_orphan_nonexisting_files()

        with self.database.data(write=True) as database_data:

            for file_path in orphan_files:
                logger.info(f"Removing orphan file: {file_path}")

                for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):

                    try:
                        database_data.remove_document(collection, file_path)

                    except KeyError:
                        pass  # malformed database, the file doesn't exist

                full_path = os.path.join(self.folder, file_path)

                if os.path.exists(full_path):
                    os.unlink(full_path)

    def del_clinical_tags(self):
        """
        Remove clinical tags from the project's current and initial
        collections.

        Iterates through predefined clinical tags and removes them from both
        collections if they exist in the current collection's field names.

        :return (list): Clinical tags that were successfully removed.
        """
        removed_tags = []

        with self.database.data() as database_data:
            field_names = database_data.get_field_names(COLLECTION_CURRENT)

        with self.database.schema() as database_schema:

            for clinical_tag in CLINICAL_TAGS:

                if clinical_tag in field_names:

                    for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                        database_schema.remove_field(collection, clinical_tag)

                    removed_tags.append(clinical_tag)

        return removed_tags

    def files_in_project(self, files):
        """
        Extract file/directory names from input that are within the project
        folder.

        Recursively processes the input to find all file paths, handling
        nested data structures. Only paths within the project directory are
        included.

        :param files: Input that may contain file paths. Can be:
                      - str: A single file path
                      - list/tuple/set: Collection of file paths or
                        nested structures
                      - dict: Only values are processed, keys are ignored

        :return (set): Relative file paths that exist within the project
                       folder, with paths normalized and made relative to the
                       project directory
        """
        project_dir = os.path.join(
            os.path.abspath(os.path.normpath(self.folder)),
            "",  # Ensures trailing slash
        )
        dir_length = len(project_dir)
        found_paths = set()
        to_process = [files]

        while to_process:
            current = to_process.pop(0)

            # Handle collections
            if isinstance(current, (list, tuple, set)):
                to_process.extend(current)
                continue

            # Handle dictionaries
            if isinstance(current, dict):
                to_process.extend(current.values())
                continue

            # Skip non-string values
            if not isinstance(current, str):
                continue

            # Normalize path and check if it's within project directory
            abs_path = os.path.abspath(os.path.normpath(current))

            if abs_path.startswith(project_dir):
                found_paths.add(abs_path[dir_length:])

        return found_paths

    def finished_bricks(self, engine, pipeline=None, include_done=False):
        """
        Retrieve and process finished bricks from workflows and pipelines.

        This method:
        1. Gets finished bricks from workflows and optionally a specific
           pipeline
        2. Filters them based on their presence in the MIA database
        3. Updates brick metadata with execution status and outputs
        4. Collects all output files that are within the project directory

        :param engine: Engine instance for retrieving finished bricks
        :param pipeline: Optional pipeline object to filter specific bricks
        :param include_done: If True, includes all bricks regardless of
                             execution status. If False, only includes
                             "Not Done" bricks.

        :return (dict): Dictionary containing:
                  - 'bricks': Dict mapping brick IDs to their metadata
                  - 'outputs': Set of output file paths relative to project
                               directory

        :Contains:
            :Private function:
                - _update_dict: Merge two dictionaries by updating the first
                                with the second
                - _collect_outputs: Recursively collects file paths from
                                    output values that are within the project
                                    directory.
        """

        def _update_dict(d1, d2):
            """
            Merge two dictionaries by updating the first with the second.

            :param d1 (dict): The dictionary to be updated.
            :param d2 (dict): The dictionary containing new key-value pairs
                              to merge into `d1`.

            :return (dict): The updated dictionary (`d1`) after merging
                            with `d2`.

            """
            d1.update(d2)
            return d1

        def _collect_outputs(value, base_path, base_len):
            """
            Recursively collects file paths from output values that are
            within the project directory.

            :param value: Output value to process (can be str, list,
                          set, tuple)
            :param base_path (str): Base project directory path
            :param base_len (int): Length of base path string for relative
                                   path calculation

            :return (set[str]): A set of collected file paths, relative to
                                the project directory.
            """
            outputs = set()
            to_process = [value]

            while to_process:
                current = to_process.pop(0)

                if isinstance(current, (list, set, tuple)):
                    to_process.extend(current)
                    continue

                if not isinstance(current, str):
                    continue

                path = Path(current).absolute().as_posix()

                if path.startswith(base_path):  # and Path(path).exists():
                    outputs.add(path[base_len:])

            return outputs

        # Get bricks from workflows and pipeline
        bricks = self.get_finished_bricks_in_workflows(engine)

        if pipeline:
            pipeline_bricks = self.get_finished_bricks_in_pipeline(pipeline)
            pipeline_bricks.update(bricks)
            bricks = pipeline_bricks

        # Filter and update bricks from database
        with self.database.data() as database_data:
            docs = database_data.get_document(
                collection_name=COLLECTION_BRICK,
                primary_keys=list(bricks),
                fields=[BRICK_ID, BRICK_EXEC, BRICK_OUTPUTS],
            )

        docs = {
            doc[BRICK_ID]: {
                "brick_exec": doc[BRICK_EXEC],
                "outputs": doc[BRICK_OUTPUTS],
            }
            for doc in docs
            if include_done or doc[BRICK_EXEC] == "Not Done"
        }
        # Merge brick metadata
        bricks = {
            brick_id: _update_dict(value, docs[brick_id])
            for brick_id, value in bricks.items()
            if brick_id in docs
        }
        # Collect all output files
        project_dir = Path(self.folder).absolute().as_posix() + os.sep
        dir_len = len(project_dir)
        all_outputs = set()

        # Process outputs from all bricks
        for brick_desc in bricks.values():
            out_data = brick_desc["outputs"]

            if out_data:

                for output in out_data.values():
                    all_outputs.update(
                        _collect_outputs(output, project_dir, dir_len)
                    )

        return {"bricks": bricks, "outputs": all_outputs}

    def get_data_history(self, path):
        """
        Get the processing history for the given data file.

        The history dict contains several elements:
        - `parent_files`: set of other data used (directly or indirectly) to
                          produce the data.
        - `processes`: processing bricks set from each ancestor data which
                       lead to the given one. Elements are process
                       (brick) UUIDs.

        :param path: Path to the data file
        :return: history (dict)
        """

        from . import data_history_inspect

        return data_history_inspect.get_data_history(path, self)

    def getDate(self):
        """Return the date of creation of the project.

        :return (str): The date of creation of the project if it's not
                       Unnamed project, otherwise empty string
        """

        return self.properties["date"]

    def get_finished_bricks_in_pipeline(self, pipeline):
        """
        Retrieves a dictionary of finished processes (bricks) from a given
        pipeline, including nested pipelines, if any.

        :param pipeline (Pipeline or Process): The pipeline or single process
                                               to analyze. If a single
                                               process is provided, it will
                                               be treated as a minimal
                                               pipeline.

        :return (dict): A dictionary where keys are process UUIDs (brick IDs)
                        and values are dictionaries containing the associated
                        process instances.

        """

        if not isinstance(pipeline, Pipeline):
            # it's a single process...
            procs = {}
            brid = getattr(pipeline, "uuid", None)

            if brid is not None:
                procs[brid] = {"process": pipeline}

            return procs

        # Get initial enabled nodes
        nodes_list = [
            n
            for n in pipeline.nodes.items()
            if n[0] != ""
            and pipeline_tools.is_node_enabled(pipeline, n[0], n[1])
        ]

        all_nodes = list(nodes_list)

        while nodes_list:
            node_name, node = nodes_list.pop(0)

            if hasattr(node, "process") and isinstance(node, PipelineNode):
                process = node.process
                new_nodes = [
                    n
                    for n in process.nodes.items()
                    if n[0] != ""
                    and pipeline_tools.is_node_enabled(process, n[0], n[1])
                ]
                nodes_list.extend(new_nodes)
                all_nodes.extend(new_nodes)

        # Collect process UUIDs into result dictionary
        procs = {}

        for node_name, node in all_nodes:

            if isinstance(node, ProcessNode):
                process = node.process
                brid = getattr(process, "uuid", None)

                if brid is not None:
                    procs[brid] = {"process": process}

        return procs

    def get_finished_bricks_in_workflows(self, engine):
        """
        Retrieves a dictionary of finished bricks (jobs) from Soma-Workflow
        workflows.

        :param engine (object): The engine instance used to interact with the
                                study configuration and Soma-Workflow module.

        :return (dict): A dictionary where keys are brick IDs (UUIDs) and
                        values are dictionaries containing metadata about
                        each finished job, including:
                        - `workflow`: The workflow ID in which the job is
                                      contained.
                        - `job`: The Soma-Workflow job instance.
                        - `job_id`: The ID of the job in Soma-Workflow.
                        - `swf_status`: The status information for the job in
                                        Soma-Workflow.
        """
        # import soma_workflow.client as swclient
        # from soma_workflow import constants

        swm = engine.study_config.modules["SomaWorkflowConfig"]
        swm.connect_resource(engine.connected_to())
        controller = swm.get_workflow_controller()
        jobs = {}

        for wf_id in controller.workflows():
            wf_st = controller.workflow_elements_status(wf_id)
            finished_jobs = {}

            for job_st in wf_st[0]:
                job_id = job_st[0]

                if job_st[1] != "done" or job_st[3][0] != "finished_regularly":
                    continue

                finished_jobs[job_id] = job_st

            if not finished_jobs:
                continue

            wf = controller.workflow(wf_id)

            for job in wf.jobs:
                brid = getattr(job, "uuid", None)

                if not brid:
                    continue

                # get engine job
                ejob = wf.job_mapping[job]
                job_id = ejob.job_id
                status = finished_jobs.get(job_id, None)

                if not status:
                    continue

                jobs[brid] = {
                    "workflow": wf_id,
                    "job": job,
                    "job_id": job_id,
                    "swf_status": status,
                }

        return jobs

    def getFilter(self, target_filter):
        """Return a Filter object from its name.

        :param target_filter (str): Filter name

        :return (Filter): Filter object corresponding to the given name or
                          None if not found
        """
        return next(
            (obj for obj in self.filters if obj.name == target_filter), None
        )

    def getFilterName(self):
        """
        Input box to type the name of the filter to save.

        :return (str): Return the name typed by the user or None if
                       cancelled
        """

        from PyQt5.QtWidgets import QInputDialog, QLineEdit

        text, ok_pressed = QInputDialog.getText(
            None, "Save a filter", "Filter name: ", QLineEdit.Normal, ""
        )

        if ok_pressed and text != "":
            return text

        # Explicitly return None if dialog was cancelled or empty text
        return None

    def getName(self):
        """Return the name of the project.

        :return (str): The name of the project if it's not Unnamed
                       project, otherwise empty string
        """

        return self.properties["name"]

    def get_orphan_bricks(self, bricks=None):
        """
        Identifies orphan bricks and their associated weak files.

        :param bricks (list or set): A list or set of brick IDs to filter the
                                     search. If None, all bricks in the
                                     database are considered. Defaults to None.

        :return (tuple): A tuple containing two sets:
                    - `orphan` (set): Brick IDs considered orphaned, meaning
                                      they have no valid or existing outputs
                                      linked to the current database.
                    - `orphan_weak_files` (set): Paths to weak files associated
                                                 with orphaned bricks, such as
                                                 script files or files that no
                                                 longer exist.
        """
        orphan = set()
        orphan_weak_files = set()
        used_bricks = set()

        if bricks is not None and not isinstance(bricks, list):
            bricks = list(bricks)

        with self.database.data() as database_data:
            brick_docs = database_data.get_document(
                collection_name=COLLECTION_BRICK,
                primary_keys=bricks,
                fields=[BRICK_ID, BRICK_OUTPUTS],
            )

        proj_dir = os.path.join(
            os.path.abspath(os.path.normpath(self.folder)), ""
        )
        lp = len(proj_dir)

        for brick in brick_docs:
            brid = brick[BRICK_ID]

            if brid is None:
                continue

            if brick[BRICK_OUTPUTS] is None:
                orphan.add(brid)
                continue

            todo = list(brick[BRICK_OUTPUTS].values())
            values = set()

            while todo:
                value = todo.pop(0)

                if isinstance(value, (list, set, tuple)):
                    todo += value

                elif isinstance(value, str):
                    path = os.path.abspath(os.path.normpath(value))

                    if path.startswith(proj_dir):
                        value = path[lp:]

                    values.add(value)

            with self.database.data() as database_data:
                docs = database_data.get_document(
                    collection_name=COLLECTION_CURRENT,
                    primary_keys=list(values),
                    fields=[TAG_FILENAME, TAG_BRICKS],
                )

            used = False
            orphan_files = set()

            for doc in docs:

                if doc[TAG_BRICKS] and brid in doc[TAG_BRICKS]:

                    if doc[TAG_FILENAME].startswith(
                        "scripts/"
                    ) or not os.path.exists(
                        os.path.join(self.folder, doc[TAG_FILENAME])
                    ):
                        # script files are "weak" and should not prevent
                        # brick deletion. Non-existing files can be
                        # cleared too.
                        orphan_files.add(doc[TAG_FILENAME])
                        continue

                    used = True
                    used_bricks.add(brid)
                    break

            if not used:
                orphan.add(brid)
                orphan_weak_files.update(orphan_files)

        if bricks:
            orphan.update(brid for brid in bricks if brid not in used_bricks)

        return (orphan, orphan_weak_files)

    def get_orphan_history(self):
        """
        Identifies orphaned history entries, their associated orphan bricks,
        and weak files.

        :return (tuple): A tuple containing three sets:
            - `orphan_hist` (set): IDs of history entries that are no longer
                                   linked to any current document in the
                                   database.
            - `orphan_bricks` (set): IDs of bricks associated with orphaned
                                     history entries.
            - `orphan_weak_files` (set): Paths to weak files (e.g., script
                                         files or non-existent files) linked
                                         to orphaned history entries.
        """
        orphan_hist = set()
        orphan_bricks = set()
        orphan_weak_files = set()
        used_hist = set()

        with self.database.data() as database_data:
            hist_docs = database_data.get_document(
                collection_name=COLLECTION_HISTORY,
                fields=[HISTORY_ID, HISTORY_BRICKS],
            )

            proj_dir = os.path.join(
                os.path.abspath(os.path.normpath(self.folder)), ""
            )
            lp = len(proj_dir)

            for hist in hist_docs:
                hist_id = hist[HISTORY_ID]

                if hist_id is None:
                    continue

                if hist[HISTORY_BRICKS]:
                    orphan_hist.add(hist_id)
                    continue

                values = set()

                for brid in hist[HISTORY_BRICKS]:
                    brick_doc = database_data.get_value(
                        collection_name=COLLECTION_BRICK,
                        primary_key=brid,
                        field=BRICK_OUTPUTS,
                    )
                    todo = list(brick_doc.values()) if brick_doc else []

                    while todo:
                        value = todo.pop(0)

                        if isinstance(value, (list, set, tuple)):
                            todo.extend(value)

                        elif isinstance(value, str):
                            path = os.path.abspath(os.path.normpath(value))

                            if path.startswith(proj_dir):
                                values.add(path[lp:])

                docs = database_data.get_document(
                    collection_name=COLLECTION_CURRENT,
                    primary_keys=list(values),
                    fields=[TAG_FILENAME, TAG_HISTORY],
                )
                used = False
                orphan_files = set()

                for doc in docs:

                    if doc[TAG_HISTORY] and hist_id == doc[TAG_HISTORY]:

                        if doc[TAG_FILENAME].startswith(
                            "scripts/"
                        ) or not os.path.exists(
                            os.path.join(self.folder, doc[TAG_FILENAME])
                        ):
                            # script files are "weak" and should not prevent
                            # brick deletion. Non-existing files can be
                            # cleared too.
                            orphan_files.add(doc[TAG_FILENAME])
                            continue

                        used = True
                        used_hist.add(hist_id)
                        break

                if not used:
                    orphan_hist.add(hist_id)
                    orphan_bricks.update(hist[HISTORY_BRICKS])
                    orphan_weak_files.update(orphan_files)

        return orphan_hist, orphan_bricks, orphan_weak_files

    def get_orphan_nonexisting_files(self):
        """
        Retrieves orphaned files listed in the database that no longer exist
        on the filesystem.

        :return (set): A set of filenames from the database that are not
                       found on the filesystem and are not associated with
                       existing bricks.
        """

        with self.database.data() as database_data:
            docs = database_data.get_document(
                collection_name=COLLECTION_CURRENT,
                fields=[TAG_FILENAME, TAG_BRICKS],
            )
            orphan = set()

            for doc in docs:

                if doc[TAG_BRICKS]:
                    bricks = database_data.get_document(
                        collection_name=COLLECTION_BRICK,
                        primary_keys=doc[TAG_BRICKS],
                        fields=[BRICK_ID],
                    )

                    if bricks:
                        continue

                file_path = os.path.join(self.folder, doc[TAG_FILENAME])

                if not os.path.exists(file_path):
                    orphan.add(doc[TAG_FILENAME])

        return orphan

    def getSortedTag(self):
        """Return the sorted tag of the project.

        :return (str): Sorted tag of the project if it's not Unnamed
                       project, otherwise empty string
        """

        return self.properties["sorted_tag"]

    def getSortOrder(self):
        """Return the sort order of the project.

        :return (str): Sort order of the project if it's not Unnamed
                       project, otherwise empty string
        """

        return self.properties["sort_order"]

    def hasUnsavedModifications(self):
        """Return if the project has unsaved modifications or not.

        :return (bool): True if the project has pending modifications,
                        False otherwise
        """

        return self.unsavedModifications

    def init_filters(self):
        """
         Initializes project filters by loading them from stored JSON files.

        This method sets the `currentFilter` to a default empty filter and
        populates the `filters` list with `Filter` objects created
        """

        self.currentFilter = Filter(None, [], [], [], [], [], "")
        self.filters = []
        filters_folder = os.path.join(self.folder, "filters")

        for filename in glob.glob(os.path.join(filters_folder, "*")):
            filter_name, extension = os.path.splitext(
                os.path.basename(filename)
            )

            # Make sure this gets closed automatically
            # as soon as we are done reading
            with open(filename) as f:
                data = json.load(f)

            self.filters.append(
                Filter(
                    filter_name,
                    data.get("nots", []),
                    data.get("values", []),
                    data.get("fields", []),
                    data.get("links", []),
                    data.get("conditions", []),
                    data.get("search_bar_text", ""),
                )
            )

    def loadProperties(self):
        """
        Loads the project properties from the 'properties.yml' file.

        This method reads the project's YAML properties file and returns
        its contents as a Python dictionary.

        :return (dict): A dictionary containing the project properties if
                        successfully loaded, or None if an error occurs.
        """

        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        properties_path = os.path.join(
            self.folder, "properties", "properties.yml"
        )

        with open(properties_path) as stream:

            try:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    return yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    return yaml.load(stream)

            except yaml.YAMLError as exc:
                logger.warning(
                    f"Error loading YAML properties "
                    f"from {properties_path}: {exc}"
                )
                return None

    def redo(self, table):
        """
        Redo the last action made by the user on the project.

        :param table (QTableWidget): The table on which to apply the
                                     modifications.

        Actions that can be redone:
            - add_tag
            - remove_tags
            - add_scans
            - modified_values
            - modified_visibilities

        :raises (ValueError): If an unknown action type is encountered.
        """
        # To avoid circular imports
        from populse_mia.utils import set_item_data

        if not self.redos:
            return  # No action to redo

        to_redo = self.redos.pop()
        self.undos.append(to_redo)
        self.unsavedModifications = True
        # We pop the redo action in the undo stack
        # The first element of the list is the type of action made by
        # the user (add_tag, remove_tags, add_scans, remove_scans,
        # or modified_values)
        action = to_redo[0]

        if action == "add_tag":
            # For adding the tag, we need the tag name,
            # and all its attributes
            (
                tag_name,
                tag_type,
                tag_unit,
                tag_default_value,
                tag_description,
                values,
            ) = to_redo[1:]

            with self.database.schema() as database_schema:

                # Adding the tag
                for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                    database_schema.add_field(
                        {
                            "collection_name": collection,
                            "field_name": tag_name,
                            "field_type": tag_type,
                            "description": tag_description,
                            "visibility": True,
                            "origin": TAG_ORIGIN_USER,
                            "unit": tag_unit,
                            "default_value": tag_default_value,
                        }
                    )

            with self.database.data(write=True) as database_data:

                # Adding all the values associated
                for value in values:
                    (
                        primary_key,
                        field_name,
                        current_value,
                        initial_value,
                    ) = value
                    database_data.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=primary_key,
                        values_dict={field_name: current_value},
                    )
                    database_data.set_value(
                        collection_name=COLLECTION_INITIAL,
                        primary_key=primary_key,
                        values_dict={field_name: initial_value},
                    )

            column = table.get_index_insertion(tag_name)
            table.add_column(column, tag_name)

        elif action == "remove_tags":
            # To remove the tags, we need the names
            # The second element is a list of the removed
            # tags (Tag class)
            tags_removed = to_redo[1]

            with self.database.schema() as database_schema:

                for tag in tags_removed:
                    # We reput each tag in the tag list, keeping
                    # all the tags params
                    tag_name = tag[0]["index"].split("|")[-1]
                    database_schema.remove_field(COLLECTION_CURRENT, tag_name)
                    database_schema.remove_field(COLLECTION_INITIAL, tag_name)
                    column_to_remove = table.get_tag_column(tag_name)
                    table.removeColumn(column_to_remove)

        elif action == "add_scans":
            # To add the scans, we need the FileNames and the values
            # associated to the scans
            # The second element is a list of the scans to add
            scans_added, values_added = to_redo[1], to_redo[2]

            with self.database.data(write=True) as database_data:

                # We add all the scans
                for scan in scans_added:
                    # We remove each scan added
                    database_data.add_document(COLLECTION_CURRENT, scan)
                    database_data.add_document(COLLECTION_INITIAL, scan)
                    table.scans_to_visualize.append(scan)

                # We add all the values.
                # The third element is a list of the values to add
                for value in values_added:
                    (
                        primary_key,
                        field_name,
                        current_value,
                        initial_value,
                    ) = value
                    database_data.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=primary_key,
                        values_dict={field_name: current_value},
                    )
                    database_data.set_value(
                        collection_name=COLLECTION_INITIAL,
                        primary_key=primary_key,
                        values_dict={field_name: initial_value},
                    )

                table.add_rows(
                    database_data.get_document_names(COLLECTION_CURRENT)
                )

        elif action == "modified_values":
            # Not working?
            # To modify the values, we need the cells,
            # and the updated values

            # The second element is a list of modified values
            # (reset or value changed)
            modified_values = to_redo[1]
            table.itemChanged.disconnect()

            with self.database.data(write=True) as database_data:

                for scan, tag, old_value, new_value in modified_values:
                    # Each modified value is a list of 3 elements:
                    # scan, tag, old_value and new_value
                    item = table.item(
                        table.get_scan_row(scan), table.get_tag_column(tag)
                    )

                    if old_value is None:
                        # Font reput to normal in case it was a not
                        # defined cell
                        font = item.font()
                        font.setItalic(False)
                        font.setBold(False)
                        item.setFont(font)

                    database_data.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan,
                        values_dict={tag: new_value},
                    )

                    if new_value is None:
                        font = item.font()
                        font.setItalic(True)
                        font.setBold(True)
                        item.setFont(font)
                        set_item_data(
                            item, NOT_DEFINED_VALUE, FIELD_TYPE_STRING
                        )

                    else:
                        set_item_data(
                            item,
                            new_value,
                            database_data.get_field_attributes(
                                COLLECTION_CURRENT, tag
                            )["field_type"],
                        )

            table.update_colors()
            table.itemChanged.connect(table.change_cell_color)

        elif action == "modified_visibilities":
            # To revert the modifications of the visualized tags

            with self.database.data(write=True) as database_data:
                # Old list of columns
                old_tags = database_data.get_shown_tags()
                # List of the tags shown before the modification
                # (Tag objects)
                showed_tags = to_redo[2]
                database_data.set_shown_tags(showed_tags)

            # Columns updated
            table.update_visualized_columns(old_tags, showed_tags)

    def reput_values(self, values):
        """
        Re-put the value objects in the database.

        :param values (list): List of Value objects
        """

        with self.database.data(write=True) as database_data:

            for valueToReput in values:
                primary_key, tag, current_value, initial_value = valueToReput
                # We reput each value, exactly the same as it was before
                database_data.set_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=primary_key,
                    values_dict={tag: current_value},
                )
                database_data.set_value(
                    collection_name=COLLECTION_INITIAL,
                    primary_key=primary_key,
                    values_dict={tag: initial_value},
                )

    def saveConfig(self):
        """Save the changes in the properties file."""

        properties_path = os.path.join(
            self.folder, "properties", "properties.yml"
        )

        with open(properties_path, "w", encoding="utf8") as configfile:
            yaml.dump(
                self.properties,
                configfile,
                default_flow_style=False,
                allow_unicode=True,
            )

    def save_current_filter(self, custom_filters):
        """Save the current filter.

        :param custom_filters: The customized filter
        """

        from PyQt5.QtWidgets import QMessageBox

        (fields, conditions, values, links, nots) = custom_filters
        self.currentFilter.fields = fields
        self.currentFilter.conditions = conditions
        self.currentFilter.values = values
        self.currentFilter.links = links
        self.currentFilter.nots = nots
        # Getting the path
        filters_path = os.path.join(self.folder, "filters")

        # Filters folder created if it does not already exists
        if not os.path.exists(filters_path):
            os.mkdir(filters_path)

        filter_name = self.getFilterName()

        # We save the filter only if we have a filter name from
        # populse_mia.e popup
        if filter_name is not None:
            file_path = os.path.join(filters_path, f"{filter_name}.json")

            if os.path.exists(file_path):
                # Filter already exists
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("The filter already exists in the project")
                msg.setInformativeText(
                    f"The project already has a filter named {filter_name}"
                )
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()

            else:

                # Json filter file written
                with open(file_path, "w") as outfile:
                    new_filter = Filter(
                        filter_name,
                        self.currentFilter.nots,
                        self.currentFilter.values,
                        self.currentFilter.fields,
                        self.currentFilter.links,
                        self.currentFilter.conditions,
                        self.currentFilter.search_bar,
                    )

                    json.dump(new_filter.json_format(), outfile)
                    self.filters.append(new_filter)

    def saveModifications(self):
        """
        Save the pending operations of the project (actions still not saved).
        """
        self.saveConfig()
        self.unsavedModifications = False

    def setCurrentFilter(self, new_filter):
        """Set the current filter of the project.

        :param new_filter: New Filter object
        """
        self.currentFilter = new_filter

    def setDate(self, date):
        """Set the date of the project.

        :param date: New date of the project
        """
        self.properties["date"] = date

    def setName(self, name):
        """
        Set the name of the project if it's not Unnamed project, otherwise
        does nothing.

        :param name (str): New name of the project
        """
        self.properties["name"] = name

    def setSortedTag(self, tag):
        """Set the sorted tag of the project.

        :param tag: New sorted tag of the project
        """
        old_tag = self.properties["sorted_tag"]

        if old_tag != tag:
            self.properties["sorted_tag"] = tag
            self.unsavedModifications = True

    def setSortOrder(self, order):
        """Set the sort order of the project.

        :param order: New sort order of the project (ascending or descending)
        """
        old_order = self.properties["sort_order"]
        self.properties["sort_order"] = order

        if old_order != order:
            self.unsavedModifications = True

    def undo(self, table):
        """Undo the last action made by the user on the project.

        :param table: Table on which to apply the modifications

        Actions that can be undone:
            - add_tag
            - remove_tags
            - add_scans
            - modified_values
            - modified_visibilities
        """

        # To avoid circular imports
        from populse_mia.utils import set_item_data

        # Ensure there is an action to undo
        if not self.undos:
            return

        to_undo = self.undos.pop()
        # We pop the undo action in the redo stack
        self.redos.append(to_undo)
        # The first element of the list is the type of action made by the
        # user (add_tag, remove_tags, add_scans, remove_scans, or
        # modified_values)
        action = to_undo[0]
        self.unsavedModifications = True

        if action == "add_tag":
            # For removing the tag added, we just have to memorize
            # the tag name, and remove it
            tag_to_remove = to_undo[1]

            with self.database.schema() as database_schema:
                database_schema.remove_field(COLLECTION_CURRENT, tag_to_remove)
                database_schema.remove_field(COLLECTION_INITIAL, tag_to_remove)

            column_to_remove = table.get_tag_column(tag_to_remove)
            table.removeColumn(column_to_remove)

        elif action == "remove_tags":
            # To reput the removed tags, we need to reput the
            # tag in the tag list, and all the tags values associated
            # to this tag. The second element is a list of the
            # removed tags([Tag row, origin, unit, default_value]).
            # The third element is a list of tags values (Value class)
            tags_removed = to_undo[1]
            values_removed = to_undo[2]

            for tag in tags_removed:
                tag_to_reput = tag[0]

                with self.database.schema() as database_schema:

                    for collection in (
                        COLLECTION_CURRENT,
                        COLLECTION_INITIAL,
                    ):
                        database_schema.add_field(
                            {
                                "collection_name": collection,
                                "field_name": tag_to_reput["index"].split("|")[
                                    -1
                                ],
                                "field_type": tag_to_reput["field_type"],
                                "description": tag_to_reput["description"],
                                "visibility": tag_to_reput["visibility"],
                                "origin": tag_to_reput["origin"],
                                "unit": tag_to_reput["unit"],
                                "default_value": tag_to_reput["default_value"],
                            }
                        )

                column = table.get_index_insertion(
                    tag_to_reput["index"].split("|")[-1]
                )
                table.add_column(column, tag_to_reput["index"].split("|")[-1])

            self.reput_values(values_removed)

        elif action == "add_scans":
            # To remove added scans, we just need their file name
            # The second element is a list of added scans to remove
            scans_added = to_undo[1]

            with self.database.data(write=True) as database_data:

                for scan in scans_added:
                    # We remove each scan added
                    database_data.remove_document(COLLECTION_CURRENT, scan)
                    database_data.remove_document(COLLECTION_INITIAL, scan)
                    table.removeRow(table.get_scan_row(scan))
                    table.scans_to_visualize.remove(scan)

            table.itemChanged.disconnect()
            table.update_colors()
            table.itemChanged.connect(table.change_cell_color)

        elif action == "modified_values":
            # To revert a value changed in the databrowser,
            # we need two things:
            # the cell (scan and tag, and the old value)
            # The second element is a list of modified values (reset,
            # or value changed)
            modified_values = to_undo[1]
            table.itemChanged.disconnect()

            with self.database.data(write=True) as database_data:

                for scan, tag, old_value, new_value in modified_values:
                    item = table.item(
                        table.get_scan_row(scan), table.get_tag_column(tag)
                    )

                    if old_value is None:
                        # If the cell was not defined before, we reput it
                        database_data.remove_value(
                            COLLECTION_CURRENT, scan, tag
                        )
                        database_data.remove_value(
                            COLLECTION_INITIAL, scan, tag
                        )
                        set_item_data(
                            item, NOT_DEFINED_VALUE, FIELD_TYPE_STRING
                        )
                        font = item.font()
                        font.setItalic(True)
                        font.setBold(True)
                        item.setFont(font)

                    else:
                        # If the cell was there before,
                        # we just set it to the old value
                        database_data.set_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            values_dict={tag: old_value},
                        )
                        set_item_data(
                            item,
                            old_value,
                            database_data.get_field_attributes(
                                COLLECTION_CURRENT, tag
                            )["field_type"],
                        )

                        # If the new value is None,
                        # the not defined font must be removed
                        if new_value is None:
                            font = item.font()
                            font.setItalic(False)
                            font.setBold(False)
                            item.setFont(font)

            table.update_colors()
            table.itemChanged.connect(table.change_cell_color)

        elif action == "modified_visibilities":
            # To revert the modifications of the visualized tags

            with self.database.data(write=True) as database_data:
                # Old list of columns
                old_tags = database_data.get_shown_tags()
                # List of the tags visible before the modification
                # (Tag objects)
                visible_tags = to_undo[1]
                database_data.set_shown_tags(visible_tags)

            # Columns updated
            table.update_visualized_columns(old_tags, visible_tags)

    @property
    def unsavedModifications(self):
        """Getter for _unsavedModifications."""
        return self._unsavedModifications

    @unsavedModifications.setter
    def unsavedModifications(self, value):
        """Modify the window title depending of whether the project has
           unsaved modifications or not.

        :param value: boolean
        """
        self._unsavedModifications = value

        try:
            from PyQt5.QtCore import QCoreApplication

            app = QCoreApplication.instance()

            if self._unsavedModifications:

                if app.title()[-1] != "*":
                    app.set_title(app.title() + "*")

            else:

                if app.title()[-1] == "*":
                    app.set_title(app.title()[:-1])

        except ImportError:
            # PyQt is not here ? never mind for what we are doing here.
            pass

    def unsaveModifications(self):
        """
        Unsave the pending operations of the project.
        """
        self.unsavedModifications = False

    def update_db_for_paths(self, new_path=None):
        """Update database paths when renaming or loading a project.

        This method updates path references in the database when a project is
        renamed or loaded from a different location. It scans the `HISTORY`
        and `BRICK` collections to identify the old project path, then
        systematically replaces it with the new path.

        The method looks for the old path in brick input/output fields and
        history pipeline XML data. If the old path contains
        'data/derived_data', the method uses the portion before this segment
        as the base path.

        :param new_path (str): The new project path. If not provided,
                               the current project folder path is used.

        :Contains:
            :Private method:
                - _update_json_data: Helper method to update paths in JSON
                                     data structures
        """

        def _update_json_data(
            collection, doc_id, field, data, old_path, new_path
        ):
            """
            Helper method to update paths in JSON data structures.

            Serializes the data to JSON, performs string replacement, then
            deserializes and updates the database.

            :param collection (str): Database collection name
            :param doc_id (str): Document ID
            :param field (str): Field name to update
            :param data (dict): The data structure to process
            :param old_path (str): Old path to replace
            :param new_path (str): New path to use
            """

            try:
                data_string = json.dumps(data)
                new_data_string = data_string.replace(old_path, new_path)
                new_data = json.loads(new_data_string)

                database_data.set_value(
                    collection_name=collection,
                    primary_key=doc_id,
                    values_dict={field: new_data},
                )

            except (TypeError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to update {field} for {doc_id}: {e}")

        with self.database.data(write=True) as database_data:
            history_docs = database_data.get_document(
                collection_name=COLLECTION_HISTORY
            )

            if not history_docs:
                # The project has no calculation history: There is nothing
                #  to do and no message to print.
                return

            old_path = None
            current_project_path = (
                os.path.abspath(self.folder) if new_path is None else new_path
            )

            # Process each history document
            for hist_doc in history_docs:

                if not hist_doc or not hist_doc.get(HISTORY_ID):
                    continue

                hist_id = hist_doc[HISTORY_ID]
                brick_ids = hist_doc.get(HISTORY_BRICKS, []) or []

                # Process each brick ID in this history
                for brick_id in brick_ids:

                    if not brick_id:
                        continue

                    # Get brick inputs
                    inputs = database_data.get_value(
                        collection_name=COLLECTION_BRICK,
                        primary_key=brick_id,
                        field=BRICK_INPUTS,
                    )

                    if not inputs:
                        continue

                    # Determine old path from first valid brick input
                    if old_path is None and "output_directory" in inputs:
                        old_path = inputs["output_directory"]

                        # If path contains data/derived_data, use portion
                        # before it
                        if old_path:
                            base_path, _, _ = old_path.partition(
                                os.path.join("data", "derived_data")
                            )
                            old_path = (
                                base_path
                                if base_path != old_path
                                else old_path
                            )

                    # If we've found the old_path, update this brick's data
                    if old_path:
                        # Update inputs
                        _update_json_data(
                            collection=COLLECTION_BRICK,
                            doc_id=brick_id,
                            field=BRICK_INPUTS,
                            data=inputs,
                            old_path=old_path,
                            new_path=current_project_path,
                        )
                        # Update outputs
                        outputs = database_data.get_value(
                            collection_name=COLLECTION_BRICK,
                            primary_key=brick_id,
                            field=BRICK_OUTPUTS,
                        )

                        if outputs:
                            _update_json_data(
                                collection=COLLECTION_BRICK,
                                doc_id=brick_id,
                                field=BRICK_OUTPUTS,
                                data=outputs,
                                old_path=old_path,
                                new_path=current_project_path,
                            )

                # Update history pipeline XML if needed
                if old_path and hist_id:
                    old_pipeline_xml = database_data.get_value(
                        collection_name=COLLECTION_HISTORY,
                        primary_key=hist_id,
                        field=HISTORY_PIPELINE,
                    )

                    if old_pipeline_xml:
                        new_pipeline_xml = old_pipeline_xml.replace(
                            old_path, current_project_path
                        )
                        database_data.set_value(
                            collection_name=COLLECTION_HISTORY,
                            primary_key=hist_id,
                            values_dict={HISTORY_PIPELINE: new_pipeline_xml},
                        )

            # Handle results
            if old_path is None:
                logger.warning(
                    "Updating the paths in the database when renaming the "
                    "project: No changes in the HISTORY and BRICK "
                    "collections are made because the output_directory has "
                    "not been found. The renamed project may be corrupted...!"
                )

            else:
                logger.info(
                    f"Updating the paths in the database when renaming "
                    f"the project: Changing {old_path} with "
                    f"{current_project_path}...!"
                )
