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
        - unsavedModifications(self, value): Modify the window title depending
                                             of whether the project has unsaved
                                             modifications or not.
        - unsaveModifications: unsaves the pending operations of the project
        - update_data_history: cleanup earlier history of given data
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
            # self.folder = os.path.relpath(tempfile.mkdtemp())
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
                "The project at " + str(self.folder) + " is already opened "
                "in another instance "
                "of the software."
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

        :returns: list of clinical tags that were added.
        """
        return_tags = []

        with self.database.schema() as database_schema:

            with database_schema.data() as database_data:

                for clinical_tag in CLINICAL_TAGS:

                    if clinical_tag not in database_data.get_field_names(
                        COLLECTION_CURRENT
                    ):

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

        with self.database.data() as database_data:

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

        with self.database.data() as database_data:

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

        with self.database.data() as database_data:

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

        :returns: List of clinical tags that were successfully removed.
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

        :returns: Set of relative file paths that exist within the project
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

        :returns: Dict containing:
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

            :returns: The updated dictionary (`d1`) after merging with `d2`.

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

            :returns (set[str]): A set of collected file paths, relative to
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
                rimary_keys=list(bricks),
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
          lead to the given one. Elements are process (brick) UUIDs.

        :return: history (dict)
        """

        from . import data_history_inspect

        return data_history_inspect.get_data_history(path, self)

    def getDate(self):
        """Return the date of creation of the project.

        :returns: string of the date of creation of the project if it's not
                  Unnamed project, otherwise empty string
        """

        return self.properties["date"]

    def get_finished_bricks_in_pipeline(self, pipeline):
        """
        Retrieves a dictionary of finished processes (bricks) from a given
        pipeline, including nested pipelines, if any.

        Args:
            pipeline (Pipeline or Process): The pipeline or single process to
                                            analyze. If a single process is
                                            provided, it will be treated as a
                                            minimal pipeline.

        Returns:
            dict: A dictionary where keys are process UUIDs (brick IDs) and
                  values are dictionaries containing the associated process
                  instances.

        """

        if not isinstance(pipeline, Pipeline):
            # it's a single process...
            procs = {}
            brid = getattr(pipeline, "uuid", None)

            if brid is not None:
                procs[brid] = {"process": pipeline}

            return procs

        nodes_list = [
            n
            for n in pipeline.nodes.items()
            if n[0] != ""
            and pipeline_tools.is_node_enabled(pipeline, n[0], n[1])
        ]

        all_nodes = list(nodes_list)

        while nodes_list:
            node_name, node = nodes_list.pop(0)

            if hasattr(node, "process"):
                process = node.process

                if isinstance(node, PipelineNode):
                    new_nodes = [
                        n
                        for n in process.nodes.items()
                        if n[0] != ""
                        and pipeline_tools.is_node_enabled(process, n[0], n[1])
                    ]
                    nodes_list += new_nodes
                    all_nodes += new_nodes

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

        Args:
            engine (object): The engine instance used to interact with the
            study configuration and Soma-Workflow module.

        Returns:
            dict: A dictionary where keys are brick IDs (UUIDs) and values are
                  dictionaries containing metadata about each finished job,
                  including:
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

    def getFilter(self, filter):
        """Return a Filter object from its name.

        :param filter: Filter name
        :returns: Filter object
        """
        for filterObject in self.filters:

            if filterObject.name == filter:
                return filterObject

    def getFilterName(self):
        """Input box to type the name of the filter to save.

        :returns: Return the name typed
        """

        from PyQt5.QtWidgets import QInputDialog, QLineEdit

        text, ok_pressed = QInputDialog.getText(
            None, "Save a filter", "Filter name: ", QLineEdit.Normal, ""
        )

        if ok_pressed and text != "":
            return text

    def getName(self):
        """Return the name of the project.

        :returns: string of the name of the project if it's not Unnamed
                  project, otherwise empty string
        """

        return self.properties["name"]

    def get_orphan_bricks(self, bricks=None):
        """
        Identifies orphan bricks and their associated weak files.

        Args:
            bricks (list or set, optional): A list or set of brick IDs to
                                            filter the search. If None, all
                                            bricks in the database are
                                            considered. Defaults to None.

        Returns:
            tuple: A tuple containing two sets:
                - `orphan` (set): Brick IDs considered orphaned, meaning they
                                  have no valid or existing outputs linked to
                                  the current database.
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

        brick_docs = self.database.get_document(
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

            docs = self.database.get_document(
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
                        # brick deletion.
                        # non-existing files can be cleared too.
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
        Identifies orphan history entries, their associated orphan bricks,
        and weak files.

        Returns:
            tuple: A tuple containing three sets:
                - `orphan_hist` (set): History IDs that are considered
                                       orphaned, meaning they are no longer
                                       associated with any current document
                                       in the database.
                - `orphan_bricks` (set): Brick IDs associated with orphan
                                         history entries.
                - `orphan_weak_files` (set): Paths to weak files (e.g., script
                                             files or non-existent files)
                                             associated with orphan history
                                             entries.

        """
        orphan_hist = set()
        orphan_bricks = set()
        orphan_weak_files = set()
        used_hist = set()
        hist_docs = self.database.get_document(
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

            if hist[HISTORY_BRICKS] is None:
                orphan_hist.add(hist_id)
                continue

            values = set()

            for brid in hist[HISTORY_BRICKS]:
                brick_doc = self.database.get_value(
                    collection_name=COLLECTION_BRICK,
                    primary_key=brid,
                    field=BRICK_OUTPUTS,
                )

                if brick_doc is None:
                    todo = []

                else:
                    todo = list(brick_doc.values())

                while todo:
                    value = todo.pop(0)

                    if isinstance(value, (list, set, tuple)):
                        todo += value

                    elif isinstance(value, str):
                        path = os.path.abspath(os.path.normpath(value))

                        if path.startswith(proj_dir):
                            value = path[lp:]
                            values.add(value)

            docs = self.database.get_document(
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
                        # brick deletion.
                        # non-existing files can be cleared too.
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
        Get orphan files which do not exist from the database
        """
        # filter_query = '{Bricks} == None'
        # docs = self.session.filter_documents(
        # COLLECTION_CURRENT, filter_query, fields=[TAG_FILENAME],
        # as_list=True)
        docs = self.database.get_document(
            collection_name=COLLECTION_CURRENT,
            fields=[TAG_FILENAME, TAG_BRICKS],
        )
        orphan = set()

        for doc in docs:

            if doc[TAG_BRICKS] is not None:
                bricks = self.database.get_document(
                    collection_name=COLLECTION_BRICK,
                    primary_keys=doc[TAG_BRICKS],
                    fields=[BRICK_ID],
                )

                if bricks:
                    continue

            if not os.path.exists(
                os.path.join(self.folder, doc[TAG_FILENAME])
            ):
                orphan.add(doc[TAG_FILENAME])

        return orphan

    def getSortedTag(self):
        """Return the sorted tag of the project.

        :returns: string of the sorted tag of the project if it's not Unnamed
                  project, otherwise empty string
        """

        return self.properties["sorted_tag"]

    def getSortOrder(self):
        """Return the sort order of the project.

        :returns: string of the sort order of the project if it's not Unnamed
                  project, otherwise empty string
        """

        return self.properties["sort_order"]

    def hasUnsavedModifications(self):
        """Return if the project has unsaved modifications or not.

        :returns: boolean, True if the project has pending modifications,
                  False otherwise
        """

        return self.unsavedModifications

    def init_filters(self):
        """Initialize the filters at project opening."""

        self.currentFilter = Filter(None, [], [], [], [], [], "")
        self.filters = []
        filters_folder = os.path.join(self.folder, "filters")

        for filename in glob.glob(os.path.join(filters_folder, "*")):
            filter, extension = os.path.splitext(os.path.basename(filename))

            # make sure this gets closed automatically
            # as soon as we are done reading
            with open(filename) as f:
                data = json.load(f)

            filter_object = Filter(
                filter,
                data["nots"],
                data["values"],
                data["fields"],
                data["links"],
                data["conditions"],
                data["search_bar_text"],
            )
            self.filters.append(filter_object)

    def loadProperties(self):
        """Load the properties file."""

        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        with open(
            os.path.join(self.folder, "properties", "properties.yml")
        ) as stream:

            try:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    return yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    return yaml.load(stream)

            except yaml.YAMLError as exc:
                print(exc)

    def redo(self, table):
        """Redo the last action made by the user on the project.

        :param table: table on which to apply the modifications

        Actions that can be undone:
            - add_tag
            - remove_tags
            - add_scans
            - modified_values
            - modified_visibilities
        """
        # To avoid circular imports
        from populse_mia.utils import set_item_data

        # We can redo if we have an action to make again
        if len(self.redos) > 0:
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
                tag_to_add = to_redo[1]
                tag_type = to_redo[2]
                tag_unit = to_redo[3]
                tag_default_value = to_redo[4]
                tag_description = to_redo[5]
                values = to_redo[6]  # List of values stored
                # Adding the tag
                self.database.add_field(
                    {
                        "collection_name": COLLECTION_CURRENT,
                        "field_name": tag_to_add,
                        "field_type": tag_type,
                        "description": tag_description,
                        "visibility": True,
                        "origin": TAG_ORIGIN_USER,
                        "unit": tag_unit,
                        "default_value": tag_default_value,
                    }
                )
                self.database.add_field(
                    {
                        "collection_name": COLLECTION_INITIAL,
                        "field_name": tag_to_add,
                        "field_type": tag_type,
                        "description": tag_description,
                        "visibility": True,
                        "origin": TAG_ORIGIN_USER,
                        "unit": tag_unit,
                        "default_value": tag_default_value,
                    }
                )

                # Adding all the values associated
                for value in values:
                    self.database.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=value[0],
                        values_dict={value[1]: value[2]},
                        # COLLECTION_CURRENT, value[0], value[1], value[2]
                    )
                    self.database.set_value(
                        collection_name=COLLECTION_INITIAL,
                        primary_key=value[0],
                        values_dict={value[1]: value[3]},
                        # COLLECTION_INITIAL, value[0], value[1], value[3]
                    )

                column = table.get_index_insertion(tag_to_add)
                table.add_column(column, tag_to_add)

            if action == "remove_tags":
                # To remove the tags, we need the names
                # The second element is a list of the removed tags (Tag class)
                tags_removed = to_redo[1]

                for i in range(0, len(tags_removed)):
                    # We reput each tag in the tag list, keeping
                    # all the tags params
                    tag_to_remove = tags_removed[i][0].field_name
                    self.database.remove_field(
                        COLLECTION_CURRENT, tag_to_remove
                    )
                    self.database.remove_field(
                        COLLECTION_INITIAL, tag_to_remove
                    )
                    column_to_remove = table.get_tag_column(tag_to_remove)
                    table.removeColumn(column_to_remove)

            if action == "add_scans":
                # To add the scans, we need the FileNames and the values
                # associated to the scans
                # The second element is a list of the scans to add
                scans_added = to_redo[1]

                # We add all the scans
                for i in range(0, len(scans_added)):
                    # We remove each scan added
                    scan_to_add = scans_added[i]
                    self.database.add_document(COLLECTION_CURRENT, scan_to_add)
                    self.database.add_document(COLLECTION_INITIAL, scan_to_add)
                    table.scans_to_visualize.append(scan_to_add)

                # We add all the values
                # The third element is a list of the values to add
                values_added = to_redo[2]

                for i in range(0, len(values_added)):
                    value_to_add = values_added[i]
                    self.database.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=value_to_add[0],
                        values_dict={value_to_add[1]: value_to_add[2]},
                        # COLLECTION_CURRENT,
                        # value_to_add[0],
                        # value_to_add[1],
                        # value_to_add[2],
                    )
                    self.database.set_value(
                        collection_name=COLLECTION_INITIAL,
                        primary_key=value_to_add[0],
                        values_dict={value_to_add[1]: value_to_add[3]},
                        # COLLECTION_INITIAL,
                        # value_to_add[0],
                        # value_to_add[1],
                        # value_to_add[3],
                    )

                table.add_rows(
                    self.database.get_document_names(COLLECTION_CURRENT)
                )

            # if action == "remove_scans":
            #     To remove a scan, we only need the FileName of the scan
            #     The second element is the list of removed scans (Path class)
            #     scans_removed = to_redo[1]
            #     for i in range(0, len(scans_removed)):
            #         # We reput each scan, keeping the same values
            #         scan_to_remove = getattr(
            #             scans_removed[i], TAG_FILENAME)
            #         self.session.remove_document(
            #             COLLECTION_CURRENT, scan_to_remove)
            #         self.session.remove_document(
            #             COLLECTION_INITIAL, scan_to_remove)
            #         table.scans_to_visualize.remove(scan_to_remove)
            #         table.removeRow(table.get_scan_row(scan_to_remove))
            #         table.itemChanged.disconnect()
            #         table.update_colors()
            #         table.itemChanged.connect(table.change_cell_color)

            if action == "modified_values":  # Not working
                # To modify the values, we need the cells,
                # and the updated values

                # The second element is a list of modified values
                # (reset or value changed)
                modified_values = to_redo[1]
                table.itemChanged.disconnect()

                for i in range(0, len(modified_values)):
                    # Each modified value is a list of 3 elements:
                    # scan, tag, and old_value
                    value_to_restore = modified_values[i]
                    scan = value_to_restore[0]
                    tag = value_to_restore[1]
                    old_value = value_to_restore[2]
                    new_value = value_to_restore[3]
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

                    # self.session.set_value(
                    self.database.set_value(
                        collection_name=COLLECTION_CURRENT,
                        primary_key=scan,
                        values_dict={tag: new_value},
                        # COLLECTION_CURRENT, scan, tag, new_value
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
                            self.database.get_field_attributes(
                                COLLECTION_CURRENT, tag
                            )["field_type"],
                        )

                table.update_colors()
                table.itemChanged.connect(table.change_cell_color)

            if action == "modified_visibilities":
                # To revert the modifications of the visualized tags
                # Old list of columns
                old_tags = self.database.get_shown_tags()
                # List of the tags shown before the modification (Tag objects)
                showed_tags = to_redo[2]
                self.database.set_shown_tags(showed_tags)
                # Columns updated
                table.update_visualized_columns(
                    old_tags, self.database.get_shown_tags()
                )

    def reput_values(self, values):
        """Re-put the value objects in the database.

        :param values: List of Value objects
        """

        for i in range(0, len(values)):
            # We reput each value, exactly the same as it was before
            valueToReput = values[i]
            self.database.set_value(
                collection_name=COLLECTION_CURRENT,
                primary_key=valueToReput[0],
                values_dict={valueToReput[1]: valueToReput[2]},
            )
            self.database.set_value(
                collection_name=COLLECTION_INITIAL,
                primary_key=valueToReput[0],
                values_dict={valueToReput[1]: valueToReput[3]},
            )

    def saveConfig(self):
        """Save the changes in the properties file."""

        with open(
            os.path.join(self.folder, "properties", "properties.yml"),
            "w",
            encoding="utf8",
        ) as configfile:
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
            file_path = os.path.join(filters_path, filter_name + ".json")

            if os.path.exists(file_path):
                # Filter already exists
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("The filter already exists in the project")
                msg.setInformativeText(
                    "The project already has a filter named " + filter_name
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
        """Save the pending operations of the project (actions
        still not saved).
        """

        self.saveConfig()
        self.unsavedModifications = False

    def setCurrentFilter(self, filter):
        """Set the current filter of the project.

        :param filter: new Filter object
        """

        self.currentFilter = filter

    def setDate(self, date):
        """Set the date of the project.

        :param date: new date of the project
        """

        self.properties["date"] = date

    def setName(self, name):
        """Set the name of the project if it's not Unnamed project,
        otherwise does nothing.

        :param name: new name of the project
        """

        self.properties["name"] = name

    def setSortedTag(self, tag):
        """Set the sorted tag of the project.

        :param tag: new sorted tag of the project
        """

        old_tag = self.properties["sorted_tag"]
        self.properties["sorted_tag"] = tag
        if old_tag != tag:
            self.unsavedModifications = True

    def setSortOrder(self, order):
        """Set the sort order of the project.

        :param order: new sort order of the project (ascending or descending)
        """

        old_order = self.properties["sort_order"]
        self.properties["sort_order"] = order

        if old_order != order:
            self.unsavedModifications = True

    def undo(self, table):
        """Undo the last action made by the user on the project.

        :param table: table on which to apply the modifications

        Actions that can be undone:
            - add_tag
            - remove_tags
            - add_scans
            - modified_values
            - modified_visibilities
        """

        # To avoid circular imports
        from populse_mia.utils import set_item_data

        # We can undo if we have an action to revert
        if len(self.undos) > 0:
            to_undo = self.undos.pop()
            # We pop the undo action in the redo stack
            self.redos.append(to_undo)
            # The first element of the list is the type of action
            # made by the user (add_tag,
            # remove_tags, add_scans, remove_scans, or modified_values)
            action = to_undo[0]
            self.unsavedModifications = True

            if action == "add_tag":
                # For removing the tag added, we just have to memorize
                # the tag name, and remove it
                tag_to_remove = to_undo[1]
                self.database.remove_field(COLLECTION_CURRENT, tag_to_remove)
                self.database.remove_field(COLLECTION_INITIAL, tag_to_remove)
                column_to_remove = table.get_tag_column(tag_to_remove)
                table.removeColumn(column_to_remove)

            if action == "remove_tags":
                # To reput the removed tags, we need to reput the
                # tag in the tag list,
                # and all the tags values associated to this tag
                # The second element is a list of the removed tags
                # ([Tag row, origin, unit, default_value])
                tags_removed = to_undo[1]

                for i in range(0, len(tags_removed)):
                    # We reput each tag in the tag list, keeping
                    # all the tags params
                    tag_to_reput = tags_removed[i][0]
                    self.database.add_field(
                        {
                            "collection_name": COLLECTION_CURRENT,
                            "field_name": tag_to_reput.field_name,
                            "field_type": tag_to_reput.field_type,
                            "description": tag_to_reput.description,
                            "visibility": tag_to_reput.visibility,
                            "origin": tag_to_reput.origin,
                            "unit": tag_to_reput.unit,
                            "default_value": tag_to_reput.default_value,
                        }
                    )
                    self.database.add_field(
                        {
                            "collection_name": COLLECTION_INITIAL,
                            "field_name": tag_to_reput.field_name,
                            "field_type": tag_to_reput.field_type,
                            "description": tag_to_reput.description,
                            "visibility": tag_to_reput.visibility,
                            "origin": tag_to_reput.origin,
                            "unit": tag_to_reput.unit,
                            "default_value": tag_to_reput.default_value,
                        }
                    )

                # The third element is a list of tags values (Value class)
                values_removed = to_undo[2]
                self.reput_values(values_removed)

                for i in range(0, len(tags_removed)):
                    # We reput each tag in the tag list,
                    # keeping all the tags params
                    tag_to_reput = tags_removed[i][0]
                    column = table.get_index_insertion(tag_to_reput.field_name)
                    table.add_column(column, tag_to_reput.field_name)

            if action == "add_scans":
                # To remove added scans, we just need their file name
                # The second element is a list of added scans to remove
                scans_added = to_undo[1]

                for i in range(0, len(scans_added)):
                    # We remove each scan added
                    scan_to_remove = scans_added[i]
                    self.database.remove_document(
                        COLLECTION_CURRENT, scan_to_remove
                    )
                    self.database.remove_document(
                        COLLECTION_INITIAL, scan_to_remove
                    )
                    table.removeRow(table.get_scan_row(scan_to_remove))
                    table.scans_to_visualize.remove(scan_to_remove)

                table.itemChanged.disconnect()
                table.update_colors()
                table.itemChanged.connect(table.change_cell_color)
            # if action == "remove_scans":
            #     To reput a removed scan, we need the scans names,
            #     and all the values associated
            #     The second element is the list of removed scans (Scan class)
            #     scans_removed = to_undo[1]
            #     for i in range(0, len(scans_removed)):
            #         # We reput each scan, keeping the same values
            #         scan_to_reput = scans_removed[i]
            #         self.session.add_document(
            #             COLLECTION_CURRENT, getattr(
            #                 scan_to_reput, TAG_FILENAME))
            #         self.session.add_document(
            #             COLLECTION_INITIAL, getattr(
            #                 scan_to_reput, TAG_FILENAME))
            #         table.scans_to_visualize.append(getattr(
            #             scan_to_reput, TAG_FILENAME))
            #
            #     # The third element is the list of removed values
            #     values_removed = to_undo[2]
            #     self.reput_values(values_removed)
            #     table.add_rows(self.session.get_document_names(
            #         COLLECTION_CURRENT))

            if action == "modified_values":
                # To revert a value changed in the databrowser,
                # we need two things:
                # the cell (scan and tag, and the old value)
                # The second element is a list of modified values (reset,
                modified_values = to_undo[1]
                # or value changed)
                table.itemChanged.disconnect()

                for i in range(0, len(modified_values)):
                    # Each modified value is a list of 3 elements:
                    # scan, tag, and old_value
                    value_to_restore = modified_values[i]
                    scan = value_to_restore[0]
                    tag = value_to_restore[1]
                    old_value = value_to_restore[2]
                    new_value = value_to_restore[3]
                    item = table.item(
                        table.get_scan_row(scan), table.get_tag_column(tag)
                    )

                    if old_value is None:
                        # If the cell was not defined before, we reput it
                        self.database.remove_value(
                            COLLECTION_CURRENT, scan, tag
                        )
                        self.database.remove_value(
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
                        self.database.set_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            values_dict={tag: old_value},
                            # COLLECTION_CURRENT, scan, tag, old_value
                        )
                        set_item_data(
                            item,
                            old_value,
                            self.database.get_field_attributes(
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

            if action == "modified_visibilities":
                # To revert the modifications of the visualized tags
                # Old list of columns
                old_tags = self.database.get_shown_tags()
                # List of the tags visible before the modification
                # (Tag objects)
                visible = to_undo[1]
                self.database.set_shown_tags(visible)
                # Columns updated
                table.update_visualized_columns(
                    old_tags, self.database.get_shown_tags()
                )

    @property
    def unsavedModifications(self):
        """Setter for _unsavedModifications."""
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
        """Unsave the pending operations of the project."""

        self.unsavedModifications = False

    # def update_data_history(self, data):
    #     """
    #     Cleanup earlier history of given data by removing from their bricks
    #     list those which correspond to obsolete runs (data has been
    #     re-written by more recent runs). This function only updates data
    #     status (bricks list), it does not remove obsolete bricks from the
    #     database. This method seems to be obsolete and is no longer used in
    #     Mia (see populse_mia.user_interface.pipeline_manager.
    #     pipeline_manager_tab.PipelineManagerTab.garbage_collect()). This is
    #     why this method is currently commented on.
    #     Returns
    #     -------
    #     a set of obsolete bricks that might become orphan: they are not used
    #     any longer in input data history, and were in the previous ones. But
    #     they still can be used in other data.
    #     """
    #     #
    #     scan_bricks = self.database.get_document(
    #         collection_name=COLLECTION_CURRENT,
    #         primary_keys=list(data),
    #         fields=[TAG_FILENAME, TAG_BRICKS],
    #     )
    #     scan_bricks = {
    #         brick[TAG_FILENAME]: brick[TAG_BRICKS]
    #         for brick in scan_bricks
    #         if brick and brick[TAG_FILENAME] is not None
    #     }
    #
    #     obsolete = set()
    #     used = set()
    #
    #     for output in data:
    #         o_hist = self.get_data_history(output)
    #         p_hist = o_hist["processes"]
    #         used.update(p_hist)
    #         old_bricks = scan_bricks.get(output)
    #
    #         if old_bricks:
    #             new_bricks = [brid for brid in old_bricks if brid in p_hist]
    #
    #             if len(new_bricks) != len(old_bricks):
    #                 print(
    #                     f"update file history for"
    #                     f": {output}: {old_bricks} -> {new_bricks}"
    #                 )
    #                 # self.session.set_value(
    #                 self.database.set_value(
    #                     collection_name=COLLECTION_CURRENT,
    #                     primary_key=output,
    #                     values_dict={TAG_BRICKS: new_bricks},
    #                     # COLLECTION_CURRENT, output, TAG_BRICKS, new_bricks
    #                 )
    #
    #     for bricks in scan_bricks.values():
    #
    #         if bricks:
    #             obsolete.update(brick for brick in bricks
    #                             if brick not in used)
    #
    #     return obsolete

    def update_db_for_paths(self, new_path=None):
        """Update database paths when renaming or loading a project.

        This method updates the `HISTORY` and `BRICK` collections in the
        database to reflect a new project file path. It is useful when a
        project is renamed or a new project is loaded from outside. The
        method identifies the old output directory path and replaces it
        with the new path in relevant database entries.

        If no output directory is found in the history, the method prints a
        warning, and no changes are made.

        Parameters:
            new_path (str, optional): The new project path. If not provided,
                                      the current project folder path is used.
        """
        hist_brick = self.database.get_document(
            collection_name=COLLECTION_HISTORY
        )
        old_path = None

        # Check if hist_brick is empty
        if not hist_brick:
            old_path = False

        for list_hist_brick in hist_brick:

            if not list_hist_brick or list_hist_brick[HISTORY_ID] is None:
                continue

            hist_id = list_hist_brick[HISTORY_ID]
            brick_ids = list_hist_brick[HISTORY_BRICKS]

            for brick_id in brick_ids or []:

                if not brick_id:
                    continue

                inputs = self.database.get_value(
                    collection_name=COLLECTION_BRICK,
                    primary_key=brick_id,
                    field=BRICK_INPUTS,
                )

                if not inputs:
                    continue

                if old_path is None:
                    old_path = inputs.get("output_directory")

                    if old_path:
                        tmp = old_path.partition(
                            os.path.join("data", "derived_data")
                        )
                        old_path = tmp[0] if tmp[0] != old_path else old_path

                # If the old_path is determined, update entries
                if old_path:
                    inputs_string = json.dumps(inputs)
                    new_inputs_string = inputs_string.replace(
                        old_path, new_path or ""
                    )
                    new_inputs = json.loads(new_inputs_string)
                    # self.database.set_value(
                    self.database.set_value(
                        collection_name=COLLECTION_BRICK,
                        primary_key=brick_id,
                        values_dict={BRICK_INPUTS: new_inputs},
                        # COLLECTION_BRICK, brick_id, BRICK_INPUTS, new_inputs
                    )
                    outputs = self.database.get_value(
                        collection_name=COLLECTION_BRICK,
                        primary_key=brick_id,
                        field=BRICK_OUTPUTS,
                    )

                    if outputs:
                        outputs_string = json.dumps(outputs)
                        new_outputs_string = outputs_string.replace(
                            old_path, new_path or ""
                        )
                        new_outputs = json.loads(new_outputs_string)
                        # self.database.set_value(
                        self.database.set_value(
                            collection_name=COLLECTION_BRICK,
                            primary_key=brick_id,
                            values_dict={BRICK_OUTPUTS: new_outputs},
                            #     COLLECTION_BRICK,
                            #     brick_id,
                            #     BRICK_OUTPUTS,
                            #     new_outputs,
                        )

            # Update the history pipeline if hist_id is valid
            if old_path and hist_id:
                old_pipeline_xml = self.database.get_value(
                    collection_name=COLLECTION_HISTORY,
                    primary_key=hist_id,
                    field=HISTORY_PIPELINE,
                )

                if old_pipeline_xml:
                    new_pipeline_xml = old_pipeline_xml.replace(
                        old_path, new_path or ""
                    )
                    # self.database.set_value(
                    self.database.set_value(
                        collection_name=COLLECTION_HISTORY,
                        primary_key=hist_id,
                        values_dict={HISTORY_PIPELINE: new_pipeline_xml},
                        # COLLECTION_HISTORY,
                        # hist_id,
                        # HISTORY_PIPELINE,
                        # new_pipeline_xml,
                    )

        # Handle cases where no valid old_path was found
        if old_path is None:
            print(
                "\nUpdating the paths in the database when renaming the "
                "project:\nNo changes in the HISTORY and BRICK collections "
                "are made because the output_directory has not been found. "
                "The renamed project may be corrupted ...!\n"
            )

        elif old_path is False:
            # The project has no calculation history: There is nothing to do
            # and no message to print.
            return

        else:
            print(
                f"\nUpdating the paths in the database when renaming the "
                f"project:\nChanging {old_path} with "
                f"{new_path or os.path.abspath(self.folder)} ...!\n"
            )

        # hist_brick = self.database.get_documents(
        #     COLLECTION_HISTORY,
        #     #fields=[HISTORY_ID, HISTORY_BRICKS],
        #     #as_list=True,
        # )

        # if hist_brick is not None and hist_brick != []:
        #     old_path = None
        #     force_break_loop = False

        #     for list_hist_brick in hist_brick:
        #         if list_hist_brick[0] is not None:
        #             for brick_id in list_hist_brick[1]:
        #                 if brick_id is not None:
        #                     inputs = self.session.get_value(
        #                         COLLECTION_BRICK, brick_id, BRICK_INPUTS
        #                     )
        #                     old_path = inputs.get("output_directory")

        #                     if old_path is not None:
        #                         tmp = old_path.partition(
        #                             os.path.join("data", "derived_data")
        #                         )

        #                         if tmp[0] != old_path:
        #                             old_path = tmp[0]
        #                             force_break_loop = True
        #                             break

        #         if force_break_loop:
        #             break

        # elif hist_brick == []:
        #     old_path = False

        # if old_path is None:
        #     print(
        #         "\nUpdating the paths in the database when renaming the "
        #         "project:\n"
        #         "No changes in the HISTORY and BRICK collections are made "
        #         "because the output_directory has not been found. The "
        #         "renamed project may be corrupted ...!\n"
        #     )

        # if old_path is False:
        #     # The project has no calculation history: There is nothing to do
        #     # and no message to print.
        #     pass

        # else:
        #     if new_path is None:
        #         new_path = os.path.join(
        #             os.path.abspath(os.path.normpath(self.folder)), ""
        #         )

        #     print(
        #         "\nUpdating the paths in the database when renaming the "
        #         "project:\n"
        #         "Changing {0} with {1} ...!\n".format(old_path, new_path)
        #     )

        #     for list_hist_brick in hist_brick:
        #         if list_hist_brick[0] is not None:
        #             hist_id = list_hist_brick[0]
        #             old_pipeline_xml = self.session.get_value(
        #                 COLLECTION_HISTORY, hist_id, HISTORY_PIPELINE
        #             )
        #             new_pipeline_xml = old_pipeline_xml.replace(
        #                 old_path, new_path
        #             )
        #             self.session.set_value(
        #                 COLLECTION_HISTORY,
        #                 hist_id,
        #                 HISTORY_PIPELINE,
        #                 new_pipeline_xml,
        #             )

        #             if list_hist_brick[1] is not None:
        #                 for brick_id in list_hist_brick[1]:
        #                     if brick_id is not None:
        #                         inputs = self.session.get_value(
        #                             COLLECTION_BRICK, brick_id, BRICK_INPUTS
        #                         )

        #                         inputs_string = json.dumps(inputs)
        #                         new_inputs_string = inputs_string.replace(
        #                             old_path, new_path
        #                         )
        #                         new_inputs = json.loads(new_inputs_string)
        #                         self.session.set_value(
        #                             COLLECTION_BRICK,
        #                             brick_id,
        #                             BRICK_INPUTS,
        #                             new_inputs,
        #                         )
        #                         outputs = self.session.get_value(
        #                             COLLECTION_BRICK, brick_id, BRICK_OUTPUTS
        #                         )

        #                         ouputs_string = json.dumps(outputs)
        #                         new_outputs_string = ouputs_string.replace(
        #                             old_path, new_path
        #                         )
        #                         new_ouputs = json.loads(new_outputs_string)
        #                         self.session.set_value(
        #                             COLLECTION_BRICK,
        #                             brick_id,
        #                             BRICK_OUTPUTS,
        #                             new_ouputs,
        #                         )
