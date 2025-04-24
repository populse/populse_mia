"""Module to handle the importation from MRIFileManager and its progress.

:Contains:
    :Class:
        - ImportProgress: Inherit from QProgressDialog and handle the
                          progress bar
        - ImportWorker: Inherit from QThread and manage the threads

    :Functions:
        - read_log: Show the evolution of the progress bar and returns its
                    feedback
        - tags_from_file: Returns a list of [tag, value] contained in a Json
                          file
        - verify_scans: Check if the project's scans have been modified

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# import datetime
import glob
import hashlib  # To generate the md5 of each path
import json
import logging
import os.path
import threading
from datetime import datetime
from time import sleep
from time import time as time_time

# PyQt5 imports
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog

# Populse_mia import
from populse_mia.data_manager import (
    COLLECTION_CURRENT,
    COLLECTION_INITIAL,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_INTEGER,
    FIELD_TYPE_LIST_BOOLEAN,
    FIELD_TYPE_LIST_DATE,
    FIELD_TYPE_LIST_DATETIME,
    FIELD_TYPE_LIST_FLOAT,
    FIELD_TYPE_LIST_INTEGER,
    FIELD_TYPE_LIST_STRING,
    FIELD_TYPE_LIST_TIME,
    FIELD_TYPE_MAPPING,
    FIELD_TYPE_STRING,
    FIELD_TYPE_TIME,
    TAG_CHECKSUM,
    TAG_FILENAME,
    TAG_ORIGIN_BUILTIN,
    TAG_ORIGIN_USER,
    TAG_TYPE,
    TYPE_BVAL,
    TYPE_BVEC,
    TYPE_BVEC_BVAL,
    TYPE_NII,
)

logger = logging.getLogger(__name__)


class ImportProgress(QProgressDialog):
    """
    Displays a progress bar for the import process.

    :param project (Project): The project object being imported.

    Methods:
        - onProgress: Updates the progress bar value.

    """

    def __init__(self, project):
        super().__init__(
            "Please wait while the paths are being imported...", None, 0, 3
        )
        self.setWindowTitle("Importing the paths")
        self.setWindowFlags(
            Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        )
        self.setModal(True)
        self.setMinimumDuration(0)
        self.setValue(0)
        # Required for macOS compatibility:
        self.setMinimumWidth(350)
        self.worker = ImportWorker(project, self)
        self.worker.finished.connect(self.close)
        self.worker.notifyProgress.connect(self.onProgress)
        self.worker.start()

    def onProgress(self, value):
        """
        Updates the progress bar value.

        :param value (int): The current progress value.
        """
        self.setValue(value)


class ImportWorker(QThread):
    """
    Worker thread for importing scans into the project database.

    This class manages the import process, reading from export logs,
    processing scan files, and updating the database accordingly.

    Attributes:
        project: A Project object
        progress: An ImportProgress object
        notifyProgress: Signal emitted to update the progress bar

    .. Methods:
        - run : override the QThread run method.
        - scans_added: get a copy of the scans_added list in a thread-safe
                       manner.
        - _add_tag_to_database: add a new tag to the database
        - _apply_default_values: apply default values for user-defined tags
        - _convert_datetime_values: convert string values to datetime objects
        - _ensure_associated_file_tag_exists: ensure the associated file tag
                                              exists in the database
        - _extract_tag_info: extract tag information from properties
        - _get_export_logs: get the export logs from the raw data folder
        - _process_associated_file: process an associated file
        - _process_associated_files: process associated bvec/bval files
        - _process_datetime_format: process datetime format strings
        - _process_file_tags: process tags from a file
        - _process_fsl_format_files: process FSL format bvec/bval files
        - _process_list_values: process list values
        - _process_log_entries: process each log entry to import scans
        - _process_mrtrix_format_file: process MRtrix format bvec/bval file
        - _process_scan_file: process a single scan file and its associated
                              files
        - _update_database: update the database with the processed documents.
    """

    # Signal to update the progress bar
    notifyProgress = pyqtSignal(int)

    def __init__(self, project, progress):
        super().__init__()
        self.project = project
        self.progress = progress
        self.lock = threading.RLock()
        # Track scans added during the import process. scans_added should
        # always be accessed through the lock, and copied before releasing
        # the lock, because its value will change inside the thread.
        self._scans_added = []

    def run(self):
        """
        Execute the import process.

        This method overrides the QThread run method and is executed when
        the worker is started. It processes the export logs, imports scans,
        and updates the database.
        """
        begin = time_time()
        raw_data_folder = os.path.relpath(
            os.path.join(self.project.folder, "data", "raw_data")
        )
        # Process export logs from MRIManager
        list_dict_log = self._get_export_logs(raw_data_folder)
        # For history tracking
        historyMaker = ["add_scans"]

        # Reset scans_added at the start of a new import
        with self.lock:
            self._scans_added = []

        documents = {}
        values_added = []
        tags_added = []
        tags_names_added = []
        # Process each log entry
        self._process_log_entries(
            list_dict_log,
            raw_data_folder,
            documents,
            values_added,
            tags_added,
            tags_names_added,
        )
        # Apply default values for user-defined tags
        self._apply_default_values(documents, values_added)
        # Update the database
        self._update_database(
            documents, tags_added, values_added, historyMaker
        )
        logger.info(
            f"Data export duration in the database: "
            f"{round(time_time() - begin, 2)} s"
        )

    @property
    def scans_added(self):
        """Get a copy of the scans_added list in a thread-safe manner."""

        with self.lock:
            return self._scans_added.copy()

    def _add_tag_to_database(self, tag_info, tags_added, tags_names_added):
        """
        Add a new tag to the database.

        :param tag_info (dict): Tag information dictionary
        :param tags_added (list): List to track added tags
        :param tags_names_added (list): List to track added tag names
        """
        tag_definition = {
            "collection_name": COLLECTION_CURRENT,
            "field_name": tag_info["name"],
            "field_type": tag_info["type"],
            "description": tag_info["description"],
            "visibility": False,
            "origin": TAG_ORIGIN_BUILTIN,
            "unit": tag_info["unit"],
            "default_value": None,
        }
        # Add to current and initial collections
        tags_added.append(tag_definition.copy())
        tag_definition["collection_name"] = COLLECTION_INITIAL
        tags_added.append(tag_definition)
        tags_names_added.append(tag_info["name"])

    def _apply_default_values(self, documents, values_added):
        """
        Apply default values for user-defined tags.

        :param documents (dict): Dictionary containing document information
        :param values_added (list): List to track added values
        """
        with self.project.database.data() as database_data:

            for tag in database_data.get_field_attributes(COLLECTION_CURRENT):

                if tag["origin"] != TAG_ORIGIN_USER:
                    continue

                for scan in self.scans_added:

                    # Skip if tag has no default value
                    # or document already has a value
                    if (
                        tag["default_value"] is None
                        or database_data.get_value(
                            collection_name=COLLECTION_CURRENT,
                            primary_key=scan,
                            field=tag["index"].split("|")[-1],
                        )
                        is not None
                    ):
                        continue

                    # Add default value to document and history
                    values_added.append(
                        [
                            scan,
                            tag["index"].split("|")[-1],
                            tag["default_value"],
                            tag["default_value"],
                        ]
                    )
                    documents[scan][tag["index"].split("|")[-1]] = tag[
                        "default_value"
                    ]

    def _convert_datetime_values(self, tag_info):
        """
        Convert string values to datetime objects.

        :param tag_info (dict): Tag information dictionary

        :return (dict): Updated tag information dictionary
        """
        value = tag_info["value"]

        if value is not None and value != "":

            try:
                dt_value = datetime.strptime(value, tag_info["format"])

                if tag_info["type"] == FIELD_TYPE_TIME:
                    tag_info["value"] = dt_value.time()

                elif tag_info["type"] == FIELD_TYPE_DATE:
                    tag_info["value"] = dt_value.date()

                else:
                    tag_info["value"] = dt_value

            except (ValueError, TypeError):
                # Keep original value if conversion fails
                pass

        return tag_info

    def _ensure_associated_file_tag_exists(
        self, database_data, tag_name, tags_added, tags_names_added
    ):
        """
        Ensure the associated file tag exists in the database.

        :param database_data: Context-Managed database
        :param tag_name (str): Name of the tag
        :param tags_added (list): List to track added tags
        :param tags_names_added (list): List to track added tag names
        """
        if (
            database_data.get_field_attributes(COLLECTION_CURRENT, tag_name)
            is None
            and tag_name not in tags_names_added
        ):
            tag_info = {
                "name": tag_name,
                "type": FIELD_TYPE_STRING,
                "description": "Associated NIfTI file",
                "unit": None,
            }
            self._add_tag_to_database(tag_info, tags_added, tags_names_added)

    def _extract_tag_info(self, tag_name, properties):
        """
        Extract tag information from properties.

        :param tag_name (str): Name of the tag
        :param properties (any): Properties of the tag

        :return (dict): Dictionary containing tag information
        """
        tag_info = {
            "name": tag_name,
            "format": "",
            "description": None,
            "unit": None,
            "type": FIELD_TYPE_STRING,
            "value": None,
        }

        # Extract properties based on type
        if isinstance(properties, dict):
            tag_info["format"] = properties.get("format", "")

            if properties.get("description", ""):
                tag_info["description"] = properties["description"]

            if properties.get("units", ""):
                tag_info["unit"] = properties["units"]

            if properties.get("type", ""):
                tag_info["type"] = FIELD_TYPE_MAPPING.get(
                    properties["type"], properties["type"]
                )

            tag_info["value"] = properties["value"]

        elif isinstance(properties, list):
            tag_info["value"] = properties[0]

        else:
            tag_info["value"] = properties

        # Handle datetime formats
        if tag_info["format"]:
            tag_info = self._process_datetime_format(tag_info)

        # Process list (or iterable object) values
        if hasattr(tag_info["value"], "__len__") and not isinstance(
            tag_info["value"], str
        ):
            tag_info = self._process_list_values(tag_info)

        # Convert datetime values
        if tag_info["type"] in (
            FIELD_TYPE_DATETIME,
            FIELD_TYPE_DATE,
            FIELD_TYPE_TIME,
        ):
            tag_info = self._convert_datetime_values(tag_info)

        return tag_info

    def _get_export_logs(self, raw_data_folder):
        """Get the export logs from the raw data folder.

        :param raw_data_folder (str): Path to the raw data folder

        Return (list): Log entries
        """
        # Find all export logs
        list_logs = glob.glob(os.path.join(raw_data_folder, "logExport*.json"))

        if not list_logs:
            return []

        # Read the most recent log
        log_to_read = max(list_logs, key=os.path.getctime)

        with open(log_to_read, encoding="utf-8") as file:
            return json.load(file)

    def _process_associated_file(
        self,
        database_data,
        file_database_path,
        checksum,
        file_type,
        associated_file_path,
        tag_name,
        documents,
        values_added,
    ):
        """
        Process an associated file.

        :param database_data: Context-Managed database
        :param file_database_path (str): Relative path of the file
        :param checksum (str): MD5 checksum of the file
        :param file_type (Type): Type of the file
        :param associated_file_path (str): Path of the associated main file
        :param tag_name (str): Name of the association tag
        :param documents (dict): Dictionary to store document information
        :param values_added (list): List to track added values
        """
        document_not_existing = not database_data.has_document(
            collection_name=COLLECTION_CURRENT,
            primary_key=file_database_path,
        )

        if document_not_existing:

            with self.lock:
                self._scans_added.append(file_database_path)

        # Initialize document
        documents[file_database_path] = {
            TAG_FILENAME: file_database_path,
            TAG_CHECKSUM: checksum,
            TAG_TYPE: file_type,
            tag_name: str(associated_file_path),
        }

        # Add values for history if document is new
        if document_not_existing:
            values_added.append(
                [file_database_path, TAG_CHECKSUM, checksum, checksum]
            )
            values_added.append(
                [file_database_path, TAG_TYPE, file_type, file_type]
            )
            values_added.append(
                [
                    file_database_path,
                    tag_name,
                    associated_file_path,
                    associated_file_path,
                ]
            )

    def _process_associated_files(
        self,
        database_data,
        file_name,
        raw_data_folder,
        file_database_path,
        documents,
        values_added,
        tags_added,
        tags_names_added,
    ):
        """
        Process associated bvec/bval files.

        :param database_data: Context-Managed database
        :param file_name (str): Base name of the file
        :param raw_data_folder (str): Path to the raw data folder
        :param file_database_path (str): Relative path of the main file
        :param documents (dict): Dictionary to store document information
        :param values_added (list): List to track added values
        :param tags_added (list): List to track added tags
        :param tags_names_added (list): List to track added tag names
        """
        # Define paths for FSL and MRtrix format files
        bvec_path = os.path.join(raw_data_folder, f"{file_name}.bvec")
        bval_path = os.path.join(raw_data_folder, f"{file_name}.bval")
        bvec_bval_mrtrix_path = os.path.join(
            raw_data_folder, f"{file_name}-bvecs-bvals-MRtrix.txt"
        )
        # Ensure associated file tag exists
        tag_name = "AssociatedNIfTIFile"
        self._ensure_associated_file_tag_exists(
            database_data, tag_name, tags_added, tags_names_added
        )

        # Process FSL format files
        if os.path.exists(bvec_path) and os.path.exists(bval_path):
            self._process_fsl_format_files(
                database_data,
                bvec_path,
                bval_path,
                file_database_path,
                tag_name,
                documents,
                values_added,
            )

        # Process MRtrix format file
        if os.path.exists(bvec_bval_mrtrix_path):
            self._process_mrtrix_format_file(
                database_data,
                bvec_bval_mrtrix_path,
                file_database_path,
                tag_name,
                documents,
                values_added,
            )

    def _process_datetime_format(self, tag_info):
        """
        Process datetime format strings.

        :param tag_info (dict): Tag information dictionary

        :return (dict): Updated tag information dictionary
        """
        format_str = tag_info["format"]
        # Convert from display format to Python datetime format
        format_map = {
            "yyyy": "%Y",
            "MM": "%m",
            "dd": "%d",
            "HH": "%H",
            "mm": "%M",
            "ss": "%S",
            "SSS": "%f",
        }

        for display_fmt, py_fmt in format_map.items():
            format_str = format_str.replace(display_fmt, py_fmt)

        tag_info["format"] = format_str

        # Determine datetime type based on format components
        if all(x in format_str for x in ["%Y", "%m", "%d", "%H", "%M", "%S"]):
            tag_info["type"] = FIELD_TYPE_DATETIME

        elif all(x in format_str for x in ["%Y", "%m", "%d"]):
            tag_info["type"] = FIELD_TYPE_DATE

        elif all(x in format_str for x in ["%H", "%M", "%S"]):
            tag_info["type"] = FIELD_TYPE_TIME

        return tag_info

    def _process_file_tags(
        self,
        database_data,
        file_name,
        path_name,
        file_database_path,
        document_not_existing,
        documents,
        values_added,
        tags_added,
        tags_names_added,
        tags_to_exclude,
    ):
        """
        Process tags from a file.

        :param database_data: Context-Managed database
        :param file_name (str): Base name of the file
        :param path_name (str): Path to the file directory
        :param file_database_path (str): Relative path in the database
        :param document_not_existing (bool): Whether the document is new
        :param documents (dict): Dictionary to store document information
        :param values_added (list): List to track added values
        :param tags_added (list): List to track added tags
        :param tags_names_added (list): List to track added tag names
        :param tags_to_exclude (list): List of tags to exclude
        """
        # Process each tag from the file
        for tag_name, properties in tags_from_file(file_name, path_name):

            # Skip excluded tags
            if tag_name in tags_to_exclude or tag_name == "Json_Version":
                continue

            # Extract tag information
            tag_info = self._extract_tag_info(tag_name, properties)

            # Skip if no value
            if tag_info["value"] is None or tag_info["value"] == "":
                continue

            # Add tag to database if it doesn't exist
            if (
                database_data.get_field_attributes(
                    COLLECTION_CURRENT, tag_name
                )
                is None
                and tag_name not in tags_names_added
            ):
                self._add_tag_to_database(
                    tag_info, tags_added, tags_names_added
                )

            # Add value to document and history if document is new
            if document_not_existing:
                values_added.append(
                    [
                        file_database_path,
                        tag_name,
                        tag_info["value"],
                        tag_info["value"],
                    ]
                )

            documents[file_database_path][tag_name] = tag_info["value"]

    def _process_fsl_format_files(
        self,
        database_data,
        bvec_path,
        bval_path,
        file_database_path,
        tag_name,
        documents,
        values_added,
    ):
        """
        Process FSL format bvec/bval files.

        :param database_data: Context-Managed database
        :param bvec_path (str): Path to the bvec file
        :param bval_path (str): Path to the bval file
        :param file_database_path (str): Relative path of the main file
        :param tag_name (str): Name of the association tag
        :param documents (dict): Dictionary to store document information
        :param values_added (list): List to track added values
        """
        # Process bvec file
        with open(bvec_path, "rb") as bvec_file:
            original_md5_bvec = hashlib.md5(bvec_file.read()).hexdigest()

        bvec_database_path = os.path.relpath(bvec_path, self.project.folder)
        self._process_associated_file(
            database_data,
            bvec_database_path,
            original_md5_bvec,
            TYPE_BVEC,
            file_database_path,
            tag_name,
            documents,
            values_added,
        )

        # Process bval file
        with open(bval_path, "rb") as bval_file:
            original_md5_bval = hashlib.md5(bval_file.read()).hexdigest()

        bval_database_path = os.path.relpath(bval_path, self.project.folder)
        self._process_associated_file(
            database_data,
            bval_database_path,
            original_md5_bval,
            TYPE_BVAL,
            file_database_path,
            tag_name,
            documents,
            values_added,
        )

    def _process_list_values(self, tag_info):
        """
        Process list values.

        :param tag_info (dict): Tag information dictionary

        return (dict): Updated tag information dictionary
        """
        value = tag_info["value"]

        if (len(value) == 1 and isinstance(value[0], list)) or len(value) != 1:

            # Convert type to list type
            if tag_info["type"] == FIELD_TYPE_STRING:
                tag_info["type"] = FIELD_TYPE_LIST_STRING

            elif tag_info["type"] == FIELD_TYPE_INTEGER:
                tag_info["type"] = FIELD_TYPE_LIST_INTEGER

            elif tag_info["type"] == FIELD_TYPE_FLOAT:
                tag_info["type"] = FIELD_TYPE_LIST_FLOAT

            elif tag_info["type"] == FIELD_TYPE_BOOLEAN:
                tag_info["type"] = FIELD_TYPE_LIST_BOOLEAN

            elif tag_info["type"] == FIELD_TYPE_DATE:
                tag_info["type"] = FIELD_TYPE_LIST_DATE

            elif tag_info["type"] == FIELD_TYPE_DATETIME:
                tag_info["type"] = FIELD_TYPE_LIST_DATETIME

            elif tag_info["type"] == FIELD_TYPE_TIME:
                tag_info["type"] = FIELD_TYPE_LIST_TIME

        # Extract value from list
        if len(value) == 1:
            tag_info["value"] = value[0]

        else:
            tag_info["value"] = [v[0] for v in value]

        return tag_info

    def _process_log_entries(
        self,
        list_dict_log,
        raw_data_folder,
        documents,
        values_added,
        tags_added,
        tags_names_added,
    ):
        """
        Process each log entry to import scans.

        :param list_dict_log (list): Log entries
        :param raw_data_folder (str): Path to the raw data folder
        :param documents (dict): Dictionary to store document information
        :param values_added (list): List to track added values
        :param tags_added (list): List to track added tags
        :param tags_names_added (list): List to track added tag names
        """
        # List of tags to exclude
        tags_to_exclude = ["Dataset data file", "Dataset header file"]

        with self.project.database.data() as database_data:

            for dict_log in list_dict_log:

                if dict_log["StatusExport"] != "Export ok":
                    continue

                # Process the main scan file
                file_name = dict_log["NameFile"]
                self._process_scan_file(
                    database_data,
                    file_name,
                    raw_data_folder,
                    dict_log,
                    documents,
                    values_added,
                    tags_added,
                    tags_names_added,
                    tags_to_exclude,
                )

    def _process_mrtrix_format_file(
        self,
        database_data,
        bvec_bval_path,
        file_database_path,
        tag_name,
        documents,
        values_added,
    ):
        """
        Process MRtrix format bvec/bval file.

        :param database_data: Context-Managed database
        :param bvec_bval_path (str): Path to the MRtrix format file
        :param file_database_path (str): Relative path of the main file
        :param tag_name (str): Name of the association tag
        :param documents (dict): Dictionary to store document information
        :param values_added (list): List to track added values
        """
        with open(bvec_bval_path, "rb") as bval_bvec_file:
            original_md5_bvec_bval = hashlib.md5(
                bval_bvec_file.read()
            ).hexdigest()

        bvec_bval_database_path = os.path.relpath(
            bvec_bval_path, self.project.folder
        )
        self._process_associated_file(
            database_data,
            bvec_bval_database_path,
            original_md5_bvec_bval,
            TYPE_BVEC_BVAL,
            file_database_path,
            tag_name,
            documents,
            values_added,
        )

    def _process_scan_file(
        self,
        database_data,
        file_name,
        raw_data_folder,
        dict_log,
        documents,
        values_added,
        tags_added,
        tags_names_added,
        tags_to_exclude,
    ):
        """
        Process a single scan file and its associated files.:

        :param database_data: Context-Managed database
        :param file_name (str): Base name of the scan file
        :param raw_data_folder (str): Path to the raw data folder
        :param dict_log (dict): Log entry for this scan
        :param documents (dict): Dictionary to store document information
        :param values_added (list): List to track added values
        :param tags_added (list): List to track added tags
        :param tags_names_added (list): List to track added tag names
        :param tags_to_exclude (list): List of tags to exclude
        """
        # Process main NIfTI file
        file_path = os.path.join(raw_data_folder, f"{file_name}.nii")
        file_database_path = os.path.relpath(file_path, self.project.folder)

        # Calculate checksum
        with open(file_path, "rb") as scan_file:
            original_md5 = hashlib.md5(scan_file.read()).hexdigest()

        # Check if document already exists
        document_not_existing = not database_data.has_document(
            collection_name=COLLECTION_CURRENT,
            primary_key=file_database_path,
        )

        if document_not_existing:
            with self.lock:
                self._scans_added.append(file_database_path)

        # Initialize document
        documents[file_database_path] = {
            TAG_FILENAME: file_database_path,
            TAG_CHECKSUM: original_md5,
            TAG_TYPE: TYPE_NII,
        }
        # Process tags from file
        self._process_file_tags(
            database_data,
            file_name,
            raw_data_folder,
            file_database_path,
            document_not_existing,
            documents,
            values_added,
            tags_added,
            tags_names_added,
            tags_to_exclude,
        )

        # Add standard values if document is new
        if document_not_existing:
            values_added.append(
                [file_database_path, TAG_CHECKSUM, original_md5, original_md5]
            )
            values_added.append(
                [file_database_path, TAG_TYPE, TYPE_NII, TYPE_NII]
            )

        # Process associated bvec/bval files if they exist
        if dict_log.get("Bvec_bval") == "yes":
            self._process_associated_files(
                database_data,
                file_name,
                raw_data_folder,
                file_database_path,
                documents,
                values_added,
                tags_added,
                tags_names_added,
            )

    def _update_database(
        self, documents, tags_added, values_added, historyMaker
    ):
        """
        Update the database with the processed documents.

        :param documents (dict): Dictionary containing document information
        :param tags_added (list): List of tags to add
        :param values_added (list): List of values to add
        :param historyMaker (list): List for history tracking
        """
        # Emit progress updates
        self.notifyProgress.emit(1)
        sleep(0.1)

        with self.project.database.schema() as database_schema:

            with database_schema.data() as database_data:

                # Add fields
                database_schema.add_field(tags_added)
                self.notifyProgress.emit(2)
                sleep(0.1)
                # Remove existing documents to avoid conflicts
                current_paths = database_data.get_document_names(
                    COLLECTION_CURRENT
                )

            for document in documents:

                if document in current_paths:
                    database_data.remove_document(COLLECTION_CURRENT, document)
                    database_data.remove_document(COLLECTION_INITIAL, document)

                # Add document to current and initial collections
                database_data.set_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=document,
                    values_dict=documents[document],
                )
                database_data.set_value(
                    collection_name=COLLECTION_INITIAL,
                    primary_key=document,
                    values_dict=documents[document],
                )

        self.notifyProgress.emit(3)
        sleep(0.1)

        # Update history
        with self.lock:
            historyMaker.append(self._scans_added)

        historyMaker.append(values_added)
        self.project.undos.append(historyMaker)
        self.project.redos.clear()


def read_log(project, main_window):
    """
    Display a progress bar for data loading and return loaded file paths.

    This function shows the evolution of the progress bar while loading data
    files and returns a list of paths to each data file that was successfully
    loaded.

    :param project (Project): The current project instance in the software
    :param main_window (MainWindow): The software's main window instance used
                                     to display the progress bar.
    :return (list):  A list of paths to the data files (scans) that were
                      successfully added.
    """

    main_window.progress = ImportProgress(project)
    main_window.progress.show()
    main_window.progress.exec()

    with main_window.progress.worker.lock:
        scans_added = list(main_window.progress.worker.scans_added)

    return scans_added


def tags_from_file(file_path, path):
    """
    Returns a list of [tag, value] pairs from a JSON file.

    :param file_path (str): File path of the Json file (without the extension)
    :param path (str): Project path
    :return (List[List[Union[str, dict]]]: A list of the Json tags of the file
    """
    json_tags = []
    file = f"{os.path.join(path, file_path)}.json"

    with open(file) as f:
        data = json.load(f)

    for name, value in data.items():

        # We don't want spaces in PatientName (used by Mia to define
        # subfolders when writing calculation results)
        if (
            name == "PatientName"
            and isinstance(value, dict)
            and "value" in value
        ):
            value["value"][0] = value["value"][0].replace(" ", "")

        json_tags.append([name, value])

    return json_tags


def verify_scans(project):
    """
    Check if the project's scans have been modified.

    :param project (Project): Current project in the software
    :return (List[str]): The list of scans that have been modified
                          or are missing.
    """
    # Returning the files that are problematic
    modified_scans = []

    with project.database.data() as database_data:

        for scan in database_data.get_document_names(COLLECTION_CURRENT):
            file_path = os.path.relpath(os.path.join(project.folder, scan))

            if os.path.exists(file_path):

                # If the file exists, we do the checksum
                try:

                    with open(file_path, "rb") as scan_file:
                        actual_md5 = hashlib.md5(scan_file.read()).hexdigest()

                except Exception:
                    logger.warning(
                        f"Error reading file: '{os.path.abspath(file_path)}'",
                        exc_info=True,
                    )
                    actual_md5 = None

                initial_checksum = database_data.get_value(
                    collection_name=COLLECTION_CURRENT,
                    primary_key=scan,
                    field=TAG_CHECKSUM,
                )

                if initial_checksum and actual_md5 != initial_checksum:
                    modified_scans.append(scan)
            else:
                # Add missing file directly to the list
                modified_scans.append(scan)

        return modified_scans
