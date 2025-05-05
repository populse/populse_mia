"""
Module that contains multiple functions used across Mia.

:Contains:
    :Classes:
        - PackagesInstall
    :Functions:
        - _is_valid_date(date_str, date_format)
        - check_python_version
        - check_value_type
        - dict4runtime_update
        - get_db_field_value
        - get_document_names
        - get_field_names
        - get_shown_tags
        - get_value
        - launch_mia
        - message_already_exists
        - remove_document
        - set_db_field_value
        - set_filters_directory_as_default
        - set_item_data
        - set_projects_directory_as_default
        - table_to_database
        - type_name
        - verCmp
        - verify_processes
        - verify_setup
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import ast
import inspect
import logging
import os
import pkgutil
import re
import sys
import traceback
import types
import typing
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import get_args, get_origin

import dateutil.parser
import yaml

# Capsul imports
from capsul.api import Node, get_process_instance  # noqa E402
from packaging import version

# PyQt5 imports
from PyQt5.QtCore import QDate, QDateTime, QDir, QLockFile, Qt, QTime, QVariant
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# Soma-base imports
from soma.qt_gui.qtThread import QtThreadCall  # noqa E402

# Populse_mia imports
from populse_mia.data_manager import (  # noqa E402
    COLLECTION_CURRENT,
    COLLECTION_INITIAL,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_INTEGER,
    FIELD_TYPE_JSON,
    FIELD_TYPE_STRING,
    FIELD_TYPE_TIME,
)
from populse_mia.data_manager.project import Project  # noqa E402
from populse_mia.data_manager.project_properties import (  # noqa E402
    SavedProjects,
)
from populse_mia.user_interface.main_window import MainWindow

logger = logging.getLogger(__name__)


class PackagesInstall:
    """
    Helps make a pipeline package available in the Mia pipeline library
    recursively.

    :Contains:
        :Method:
            - __init__: constructor
            - add_package: provide recursive representation of a package
    """

    # These classes should not appear in available processes
    _already_loaded = {
        "populse_mia.user_interface.pipeline_manager.process_mia.ProcessMIA",
        "capsul.process.process.Process",
        "capsul.process.process.NipypeProcess",
        "capsul.process.process.FileCopyProcess",
        "capsul.pipeline.pipeline_nodes.ProcessNode",
        "capsul.pipeline.pipeline_nodes.PipelineNode",
        "capsul.pipeline.pipeline_nodes.Node",
    }

    def __init__(self):
        """Initializes the package registry."""

        self.packages = {}

    def add_package(self, module_name, class_name=None):
        """
        Recursively adds a package and its subpackages/modules to the Mia
        pipeline library.

        :param module_name (str): Name of the module to add to the pipeline
                                  library.
        :param class_name (str): Specific class to add (optional). Only this
                                 pipeline will be added to the pipeline
                                 library.
        :return: dictionary of dictionaries containing
                 package/subpackages/pipelines status.
                 ex: {package: {subpackage: {pipeline: 'process_enabled'}}}
        """

        # (filter out test modules)
        if (
            module_name
            and "test" not in module_name.split(".")
            and "tests" not in module_name.split(".")
        ):
            # reloading the package
            sys.modules.pop(module_name, None)

            try:
                __import__(module_name)
                pkg = sys.modules[module_name]

                for k, v in sorted(pkg.__dict__.items()):

                    if class_name and k != class_name:
                        continue

                    # checking each class in the package
                    if inspect.isclass(v):

                        if v in self._already_loaded:
                            continue

                        if hasattr(v, "__module__"):
                            vname = f"{v.__module__}.{v.__name__}"

                        elif hasattr(v, "__package__"):
                            vname = f"{v.__package__}.{v.__name__}"

                        else:
                            logger.warning(f"No module nor package for {v}")
                            vname = v.__name__

                        if vname in self._already_loaded:
                            continue

                        self._already_loaded.add(vname)

                        try:

                            try:
                                get_process_instance(
                                    f"{module_name}.{v.__name__}"
                                )

                            except Exception:

                                if v is Node or not issubclass(v, Node):
                                    raise

                            # updating the tree's dictionary
                            path_list = module_name.split(".") + [k]
                            pkg_iter = self.packages

                            for element in path_list:

                                if element in pkg_iter.keys():
                                    pkg_iter = pkg_iter[element]

                                else:

                                    if element is path_list[-1]:
                                        pkg_iter[element] = "process_enabled"
                                        logger.info(
                                            f"Detected brick: {element}"
                                        )

                                    else:
                                        pkg_iter[element] = {}
                                        pkg_iter = pkg_iter[element]

                        except Exception:
                            pass

                # check if there are subpackages, in this case explore them
                path = getattr(pkg, "__path__", None)

                if (
                    path is None
                    and hasattr(pkg, "__file__")
                    and os.path.basename(pkg.__file__).startswith("__init__.")
                ):
                    path = [os.path.dirname(pkg.__file__)]

                if path:

                    for _, modname, _ in pkgutil.iter_modules(path):

                        if modname == "__main__":
                            continue  # skip main

                        logger.info(
                            f"Exploring subpackages of {module_name}: "
                            f"{module_name}.{modname} ..."
                        )
                        self.add_package(
                            f"{module_name}.{modname}", class_name
                        )

            except Exception as e:
                logger.warning(
                    f"When attempting to add a package ({module_name}) or "
                    f"its modules to the package tree, the following "
                    f"exception was caught:"
                )
                logger.warning(f"{e}")

            return self.packages


def _is_valid_date(date_str, date_format):
    """
    Checks if a string matches the given date format.

    :param date_str (str): The date string to validate.
    :param date_format (str): The expected date format.

    :return (bool): True if the string matches the format, False otherwise.
    """
    try:
        datetime.strptime(date_str, date_format)
        return True

    except ValueError:
        return False


def check_python_version():
    """
    Checks if the Python version is at least 3.10.

    :raises RuntimeError: If the Python version is lower than 3.10.
    """

    if sys.version_info[:2] < (3, 10):
        raise RuntimeError(
            f"Mia requires Python >= 3.10 (current version: "
            f"{sys.version_info.major}.{sys.version_info.minor})."
        )


def check_value_type(value, value_type, is_subvalue=False):
    """
    Checks the type of new value in a table cell (QTableWidget).

    :param value (str): Value of the cell (always a str, can be a string
                        representation of a list)
    :param value_type (type): Expected type (can be list[str], list[int], etc.)
    :param is_subvalue (bool): Whether the value is a subvalue of a list.
    :return: True if the value is valid to replace the old one,
             False otherwise
    """

    # Convert string to a list if it appears to be list-like
    if isinstance(value, str) and (
        value.startswith("[") and value.endswith("]")
    ):

        try:
            # safely evaluate the string as a list
            value = ast.literal_eval(value)

        except (ValueError, SyntaxError):
            # If it's not a valid list, return False
            return False

    # Check if value_type is a list (e.g., list[int], list[str], etc.)
    origin_type = typing.get_origin(value_type)

    if origin_type is list:
        # Extract the element type from the list (e.g., int for list[int])
        element_type = typing.get_args(value_type)[0]

        if is_subvalue:
            # Check for a single element against the list's element
            # type (e.g., "10" against list[int])
            return check_value_type(value, element_type)

        # Otherwise, validate if value is a list and all elements
        # match the element type
        return isinstance(value, list) and all(
            isinstance(v, element_type) for v in value
        )

    # Mapping for basic types
    type_validators = {
        FIELD_TYPE_INTEGER: lambda v: v.lstrip("-").isdigit(),
        FIELD_TYPE_FLOAT: lambda v: (
            v.replace(".", "", 1).lstrip("-").isdigit()
        ),
        FIELD_TYPE_BOOLEAN: lambda v: str(v) in {"True", "False"},
        FIELD_TYPE_STRING: lambda v: isinstance(v, str),
        FIELD_TYPE_DATE: lambda v: isinstance(v, QDate)
        or (isinstance(v, str) and _is_valid_date(v, "%d/%m/%Y")),
        FIELD_TYPE_DATETIME: lambda v: (
            isinstance(v, QDateTime)
            or (
                isinstance(v, str)
                and _is_valid_date(v, "%d/%m/%Y %H:%M:%S.%f")
            )
        ),
        FIELD_TYPE_TIME: lambda v: isinstance(v, QTime)
        or (isinstance(v, str) and _is_valid_date(v, "%H:%M:%S.%f")),
    }

    return type_validators.get(value_type, lambda _: False)(value)


def dict4runtime_update(runtime_dict, project, db_filename, *tags):
    """
    Update a dictionary with tag values from the project's current collection.

    This function populates the `runtime_dict` with values associated with
    the specified tags from the `COLLECTION_CURRENT` database collection. If
    a tag is not present or its value is `None`, it is assigned the string
    "Undefined". Date values are converted to ISO-formatted strings.

    :param runtime_dict (dict): Dictionary used to transfer data from
                                `list_outputs` to `run_process_mia`.
    :param project: The project instance containing the database.
    :param db_filename (str): The name of the database file to query.
    :param tags: Variable number of tag names to retrieve from the database.
    """

    with project.database.data() as database_data:
        field_names = database_data.get_field_names(COLLECTION_CURRENT)

        for tag in tags:
            value = (
                database_data.get_value(COLLECTION_CURRENT, db_filename, tag)
                if tag in field_names
                else None
            )

            if isinstance(value, datetime.date):
                value = value.isoformat()

            runtime_dict[tag] = value if value is not None else "Undefined"


def get_db_field_value(project, document, field):
    """
    Retrieve the value of a specific field for a document from the project's
    database.

    :param project (Project): The current project instance containing the
                              database.
    :param document (str): The absolute path to the document.
    :param field (str): The name of the field whose value should be retrieved.

    :returns: The value of the specified field for the document in the current
              collection.
    """
    project_name = project.getName()
    start_index = document.find(project_name) + len(project_name) + 1
    db_filename = document[start_index:]

    with project.database.data() as database_data:

        return database_data.get_value(COLLECTION_CURRENT, db_filename, field)


def get_document_names(project, collection):
    """
    Retrieves the names of all documents in the specified collection
    from the project's database.

    :param project: The project instance containing the database.
    :param collection (str): The name of the collection to query.

    :returns (list[str]): A list of document names in the collection.
    """

    with project.database.data() as database_data:
        return database_data.get_document_names(collection)


def get_field_names(project, collection):
    """
    Retrieves the list of field names (i.e., column names) for documents
    in the specified collection of the project's database.

    :param project: The project instance containing the database.
    :param collection (str): The name of the collection to inspect.

    :returns (list[str]): A list of field names in the collection.
    """

    with project.database.data() as database_data:
        return database_data.get_field_names(collection)


def get_shown_tags(project):
    """
    Retrieves the list of tags that are marked as 'shown' in the project's
    database.

    :param project: The project instance containing the database.

    :returns (list[str]): A list of tag names marked as shown.
    """

    with project.database.data() as database_data:
        return database_data.get_shown_tags()


def get_value(project, collection, file_name, field):
    """
    Retrieves the value of a specific field from a document in the given
    collection.

    :param project: The project instance containing the database.
    :param collection (str): The name of the collection containing the
                             document.
    :param file_name (str): The name of the document (typically the file name).
    :param field (str): The name of the field whose value is to be retrieved.

    :returns: The value of the specified field, or None if not found.
    """

    with project.database.data() as database_data:
        return database_data.get_value(collection, file_name, field)


def launch_mia(app, args):
    """
    Launches the Mia software application.

    This function:
    - Overloads the sys.excepthook handler with the _my_excepthook function
      to log uncaught exceptions in non-interactive mode.
    - Checks if Mia is already running in another instance, and prevents
      multiple instances from opening.
    - Verifies if saved projects still exist, updating the list of opened
      projects if necessary.
    - Instantiates the 'project' object and launches Mia's GUI.

    :param app (QApplication): The Qt application instance.
    :param args (Namespace): Command line arguments.

    :Private functions:
        - _my_excepthook: Logs uncaught exceptions in non-interactive mode.
        - _verify_saved_projects: Checks if saved projects still exist and
           updates the list.
    """

    # import Config only here to prevent circular import issue
    from populse_mia.software_properties import Config

    # useful for WebEngine
    try:
        # QtWebEngineWidgets need to be imported before QCoreApplication
        # instance is created (used later)
        from soma.qt_gui.qt_backend import QtWebEngineWidgets  # noqa: F401

    except ImportError:
        pass  # QtWebEngineWidgets is not installed

    def _my_excepthook(etype, evalue, tback):
        """
        Log all uncaught exceptions in non-interactive mode and cleans
        up before exiting.

        All python exceptions are handled by function, stored in
        sys.excepthook. By overloading the sys.excepthook handler with
        _my_excepthook function, this last function is called whenever
        there is an unhandled exception (so one that exits the interpreter).
        We take advantage of it to clean up mia software before closing.

        :param etype (type): exception class
        :param evalue (Exception): exception instance
        :param tback(traceback): traceback object

        :Contains:
            :Private function:
                - _clean_up(): cleans up the mia software during "normal"
                               closing.
        """

        def _clean_up():
            """Cleans up Mia software during "normal" closing.

            Make a cleanup of the opened projects just before exiting mia.
            """
            config = Config()
            opened_projects = config.get_opened_projects()

            try:
                opened_projects.remove(main_window.project.folder)
                config.set_opened_projects(opened_projects)
                main_window.remove_raw_files_useless()

            except (AttributeError, NameError):
                config.set_opened_projects([])

            logger.info("Clean up before closing mia completed.")

        # log the exception here
        logger.info("Exception hooking in progress ...")
        _clean_up()
        # then call the default handler
        sys.__excepthook__(etype, evalue, tback)
        # there was some issue/error/problem, so exiting
        sys.exit(1)

    def _verify_saved_projects():
        """
        Verifies if saved projects still exist and updates the
        list accordingly.

        :return: List of deleted projects
        """
        saved_projects = SavedProjects()
        deleted_projects = [
            os.path.abspath(proj)
            for proj in saved_projects.pathsList
            if not os.path.isdir(proj)
        ]

        for proj in deleted_projects:
            saved_projects.removeSavedProject(proj)

        return deleted_projects

    global main_window
    sys.excepthook = _my_excepthook
    # working from the scripts directory
    # os.chdir(os.path.dirname(os.path.realpath(__file__)))
    lock_file = QLockFile(
        QDir.temp().absoluteFilePath("lock_file_populse_mia.lock")
    )

    if not lock_file.tryLock(100) and args.multi_instance is False:
        # software already opened in another instance
        logger.error("Another instance of Mia is already running. Exiting...")
        return

    # no instances of the software is opened, or args.multi_instance
    # is set to True, so the list of opened projects can be cleared
    config = Config()
    config.set_opened_projects([])
    deleted_projects = _verify_saved_projects()
    project = Project(None, True)
    main_window = MainWindow(project, deleted_projects=deleted_projects)
    main_window.setAttribute(Qt.WA_DeleteOnClose | Qt.WA_QuitOnClose)
    main_window.show()
    # make sure to instantiate the QtThreadCall singleton from the main thread
    QtThreadCall()
    app.exec()


def message_already_exists():
    """
    Displays a message box to tell that a project name already exists.
    """

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText("This name already exists in this parent folder")
    msg.setWindowTitle("Warning")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.buttonClicked.connect(msg.close)
    msg.exec()


def remove_document(project, collection, documents):
    """
    Removes one or multiple documents from the specified collection
    in the given project's database.

    :param project: The project instance containing the database.
    :param collection (str): The name of the collection from which documents
                             will be removed.
    :param documents (str or list[str]): A single document name or a list of
                                         document names to remove.
    """
    if isinstance(documents, str):
        documents = [documents]

    with project.database.data() as database_data:

        for document in documents:
            database_data.remove_document(collection, document)


def set_db_field_value(project, document, tag_to_add):
    """
    Create or update a field and its value for a document in the project's
    database.

    If the specified field does not exist in the current and initial
    collections, it is added to both. The field is then assigned a value for
    the given document.

    :param project (Project): The project instance containing the database
                              and schema.
    :param document (str): The absolute path of the document.
    :param tag_to_add (dict): A dictionary describing the field with keys:
                              'name', 'value', 'default_value',
                              'description', 'field_type', 'origin',
                              'unit', and 'visibility'.
    """
    tag_name = tag_to_add["name"]
    project_name = project.getName()
    # fmt: off
    db_filename = document[
        document.find(project_name) + len(project_name) + 1:
    ]
    # fmt: on

    with (
        project.database.schema() as database_schema,
        database_schema.data() as database_data,
    ):

        for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):

            if tag_name not in database_data.get_field_names(collection):
                database_schema.add_field(
                    {
                        "collection_name": collection,
                        "field_name": tag_name,
                        "field_type": tag_to_add["field_type"],
                        "description": tag_to_add["description"],
                        "visibility": tag_to_add["visibility"],
                        "origin": tag_to_add["origin"],
                        "unit": tag_to_add["unit"],
                        "default_value": tag_to_add["default_value"],
                    }
                )

        if not database_data.has_document(COLLECTION_CURRENT, db_filename):

            for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
                database_data.add_document(collection, db_filename)

        for collection in (COLLECTION_CURRENT, COLLECTION_INITIAL):
            database_data.set_value(
                collection, db_filename, {tag_name: tag_to_add["value"]}
            )


def set_filters_directory_as_default(dialog):
    """
    Sets the filters directory as default (Json files)

    :param dialog (QFileDialog): current file dialog
    """
    filters_dir = os.path.abspath(
        os.path.join(os.curdir, "..", "..", "filters")
    )
    os.makedirs(filters_dir, exist_ok=True)
    dialog.setDirectory(filters_dir)


def set_item_data(item, value, value_type):
    """
    Sets the data for a given item in the data browser based on the
    expected type.

    This function prepares the input `value` according to the specified
    `value_type`, converting it into a format suitable for PyQt's `QVariant`.
    It supports both primitive types (e.g., `int`, `str`, `float`) and more
    complex types like `datetime`, `date`, `time`, and lists of these types.

    :param item (QStandardItem): The item to update (expected to
                                 support `setData` method).
    :param value (Any): The new value to set for the item.
    :param value_type (Type): The expected type of the value, which can be a
                              standard Python type (e.g., `str`, `int`,
                              `float`, `bool`) or a `typing`-based list
                              type (e.g., `list[int]`, `list[datetime]`).
    """

    conversion_map = {
        FIELD_TYPE_DATETIME: lambda v: (
            v
            if isinstance(v, QDateTime)
            else (
                QDateTime(v)
                if isinstance(v, FIELD_TYPE_DATETIME)
                else (
                    QDateTime(
                        FIELD_TYPE_STRING.strptime(v, "%d/%m/%Y %H:%M:%S.%f")
                    )
                    if isinstance(v, FIELD_TYPE_STRING)
                    else None
                )
            )
        ),
        FIELD_TYPE_DATE: lambda v: (
            v
            if isinstance(v, QDate)
            else (
                QDate(v)
                if isinstance(v, FIELD_TYPE_DATE)
                else (
                    QDate(FIELD_TYPE_DATETIME.strptime(v, "%d/%m/%Y").date())
                    if isinstance(v, FIELD_TYPE_STRING)
                    else None
                )
            )
        ),
        FIELD_TYPE_TIME: lambda v: (
            v
            if isinstance(v, QTime)
            else (
                QTime(v)
                if isinstance(v, FIELD_TYPE_TIME)
                else (
                    QTime(
                        FIELD_TYPE_DATETIME.strptime(v, "%H:%M:%S.%f").time()
                    )
                    if isinstance(v, FIELD_TYPE_STRING)
                    else None
                )
            )
        ),
        FIELD_TYPE_FLOAT: lambda v: FIELD_TYPE_FLOAT(v),
        FIELD_TYPE_INTEGER: lambda v: FIELD_TYPE_INTEGER(v),
        FIELD_TYPE_BOOLEAN: lambda v: FIELD_TYPE_BOOLEAN(v),
        FIELD_TYPE_STRING: lambda v: FIELD_TYPE_STRING(v),
        FIELD_TYPE_JSON: lambda v: v,  # Assume valid JSON-like dict
    }

    def prepare_value(value, expected_type):
        """
        Prepares the input value according to its expected type.

        :param value (Any): The value to prepare.
        :param expected_type (Type): The expected type of the value.
        :return (Any): The prepared value suitable for use in a PyQt item.

        """
        if expected_type in conversion_map:
            converted_value = conversion_map[expected_type](value)

            if converted_value is not None:
                return converted_value

        if get_origin(expected_type) is list:
            sub_value_type = get_args(expected_type)[0]

            if isinstance(value, FIELD_TYPE_STRING):
                value = ast.literal_eval(value)

            return [prepare_value(v, sub_value_type) for v in value]

        raise TypeError(f"Unsupported type: {expected_type}")

    try:
        # Prepare the value according to its type
        value_prepared = prepare_value(value, value_type)

        # If the value is a list, convert it to a string for
        # PyQt compatibility
        if get_origin(value_type) is list:
            value_prepared = FIELD_TYPE_STRING(value_prepared)

        # Set the prepared value in the item
        item.setData(Qt.EditRole, QVariant(value_prepared))

    except Exception as e:
        raise ValueError(f"Failed to set item data: {e}")


def set_projects_directory_as_default(dialog):
    """
    Sets the projects directory as default.

    :param dialog (QFileDialog): current file dialog.
    """
    # import Config only here to prevent circular import issue
    from populse_mia.software_properties import Config

    config = Config()
    projects_directory = Path(config.get_projects_save_path())
    projects_directory.mkdir(parents=True, exist_ok=True)
    dialog.setDirectory(str(projects_directory))


def table_to_database(value, value_type):
    """
    Prepares the value to the database based on its type.

    :param value (Any): Value to convert.
    :param value_type (Type): Value type.
    :return (Any): The value converted for the database.
    """

    if value_type == FIELD_TYPE_FLOAT:
        return float(value)

    elif value_type == FIELD_TYPE_STRING:
        return str(value)

    elif value_type == FIELD_TYPE_INTEGER:
        return int(value)

    elif value_type == FIELD_TYPE_BOOLEAN:
        return value in {"True", True} if value != "False" else False

    elif value_type == FIELD_TYPE_DATETIME:

        if isinstance(value, QDateTime):
            return value.toPyDateTime()

        if isinstance(value, str):

            try:
                return datetime.strptime(value, "%d/%m/%Y %H:%M:%S.%f")

            except ValueError:
                return dateutil.parser.parse(value)

    elif value_type == FIELD_TYPE_DATE:

        if isinstance(value, QDate):
            return value.toPyDate()

        if isinstance(value, str):
            return datetime.strptime(value, "%d/%m/%Y").date()

    elif value_type == FIELD_TYPE_TIME:

        if isinstance(value, QTime):
            return value.toPyTime()

        if isinstance(value, str):
            return datetime.strptime(value, "%H:%M:%S.%f").time()

    elif get_origin(value_type) is list:
        list_type = get_args(value_type)[0]
        return [
            table_to_database(v, list_type) for v in ast.literal_eval(value)
        ]

    else:
        raise TypeError(f"Unsupported type: {value_type}")


def type_name(t):
    """
    Returns the name of a type or a string representation for generic
    aliases.

    :param t (Any): The type to get the name or representation for.
                    This can be a regular type (e.g., `str`, `list`) or a
                    generic alias (e.g., `list[str]`).
    :return: The name of the type (e.g., 'str') or the string representation
             of the generic alias (e.g., 'list[str]').
    """
    return str(t) if isinstance(t, types.GenericAlias) else t.__name__


def verCmp(first_ver, sec_ver, comp):
    """Version comparator.

    Compares two versions according to the specified comparator:
      - 'eq': Returns True if the first version is equal to the second.
      - 'sup': Returns True if the first version is greater than or equal
               to the second.
      - 'inf': Returns True if the first version is less than or equal to
               the second.

    :param first_ver (str): The first version to compare (e.g., '0.13.0').
    :param sec_ver (str): The second version to compare (e.g., '0.13.0').
    :param comp (str): The comparator to use ('sup', 'inf', 'eq').

    :return: True if the comparison condition is satisfied, False otherwise.

    :Contains:
        :Private function:
            - normalise: transform a version of a package to a corresponding
              list of integer
    """

    def normalise(v):
        """Transform a version of a package to a list of integer.

        :param v (str): version of a package (ex. 5.4.1)

        :return (list[int]): a list of integer (ex. [0, 13, 0])
        """

        v = re.sub(r"[^0-9\.]", "", v)
        return [int(x) for x in re.sub(r"(\.0+)*$", "", v).split(".")]

    first_normalised = normalise(first_ver)
    second_normalised = normalise(sec_ver)

    if comp == "eq":
        return first_normalised == second_normalised

    if comp == "sup":
        return first_normalised >= second_normalised

    if comp == "inf":
        return first_normalised <= second_normalised

    raise ValueError(f"Invalid comparison type: {comp}")


def verify_processes(nipypeVer, miaProcVer, capsulVer):
    """Install or update to the last version available on the station, for
    nipype, capsul and mia_processes processes libraries.

    :param nipypeVer: nipype version currently installed (str).
    :param miaProcVer: mia_processes version currently installed (str).
    :param capsulVer: capsul version currently installed (str).

    By default, Mia provides three process libraries in the pipeline library
    (available in Pipeline Manager tab). The nipype, given as it is because
    it is developed by another team (https://github.com/nipy/nipype), and
    mia_processes, capsul which are developed under the umbrella of populse
    (https://github.com/populse/mia_processes). When installing Mia in
    user mode, these three libraries are automatically installed on the
    station. The idea is to use the versioning available with pypi
    (https://pypi.org/). Thus, it is sufficient for the user to change the
    version of the library installed on the station (pip install...) to
    also change the version available in Mia. Indeed, when starting Mia, the
    verify_processes function will update the nipype, capsul and
    mia_processes libraries in the pipeline library accordingly. Currently, it
    is mandatory to have nipype, capsul and mia_processes installed in the
    station.
    All this information, as well as the installed versions and package
    paths are saved in the  properties_path/properties/process_config.yml file.
    When an upgrade or downgrade is performed for a package, the last
    configuration used by the user is kept (if a pipeline was visible, it
    remains so and vice versa). However, if a new pipeline is available in
    the new version it is automatically marked as visible in the library.

    :Contains:
        :Private function:
            - _deepCompDic: keep the previous config existing before packages
              update
    """

    # import Config only here to prevent circular import issue
    from populse_mia.software_properties import Config

    def _deepCompDic(old_dic, new_dic):
        """
        Recursively compares two dictionaries and retains the previous
        configuration where applicable.


        This function is used to preserve user display preferences in the
        Pipeline Manager Editor, ensuring that configurations not updated
        or changed remain intact.

        :param old_dic (dict): The previous package configuration.
        :param new_dic (dict): The new package configuration.
        :return: True if all keys at the current level match, False if not.
        """

        if isinstance(old_dic, str):
            return True

        for key, value in old_dic.items():

            if key in new_dic and _deepCompDic(value, new_dic[key]):
                new_dic[key] = value

    othPckg = None
    # othPckg: a list containing all packages, other than nipype, mia_processes
    #          and capsul, used during the previous launch of mia.
    pack2install = []
    # pack2install: a list containing the package (nipype and/or
    #               mia_processes and/or capsul) to install
    proc_content = None
    # proc_content: python dictionary object corresponding to the
    #               process_config.yml property file
    config = Config()
    proc_config = os.path.join(
        config.get_properties_path(), "properties", "process_config.yml"
    )
    logger.info(
        "Checking the installed version for nipype, mia_processes "
        "and capsul ..."
    )

    # Read process configuration file if it exists
    if os.path.isfile(proc_config):

        with open(proc_config) as stream:

            if version.parse(yaml.__version__) > version.parse("5.1"):
                proc_content = yaml.load(stream, Loader=yaml.FullLoader)

            else:
                proc_content = yaml.load(stream)

    if (isinstance(proc_content, dict)) and ("Packages" in proc_content):
        othPckg = [
            pkg
            for pkg in proc_content["Packages"]
            if pkg not in ["mia_processes", "nipype", "capsul"]
        ]

    # Check if packages used during the previous launch are still available
    if othPckg:

        for pckg in othPckg:

            try:
                __import__(pckg)

            except ImportError as e:

                # Attempt to update sys.path, for the processes/ directory
                # currently used, and re-import
                processes_path = os.path.join(
                    config.get_properties_path(), "processes"
                )

                if processes_path not in sys.path:
                    sys.path.append(processes_path)

                    try:
                        __import__(pckg)

                        # update the Paths parameter (processes/ directory
                        # currently used) saved later in the
                        # properties_path/properties/process_config.yml file
                        if ("Paths" in proc_content) and (
                            isinstance(proc_content["Paths"], list)
                        ):

                            if processes_path not in proc_content["Paths"]:
                                proc_content["Paths"].append(processes_path)

                        else:
                            proc_content["Paths"] = [processes_path]

                        with open(proc_config, "w", encoding="utf8") as stream:
                            yaml.dump(
                                proc_content,
                                stream,
                                default_flow_style=False,
                                allow_unicode=True,
                            )

                        # Finally, the processes' directory currently used is
                        # removed from the sys.path because this directory is
                        # now added to the Paths parameter in the
                        # properties_path/properties/process_config.yml file
                        sys.path.remove(processes_path)

                    # If an exception is raised, ask the user to remove the
                    # package from the pipeline library or reload it
                    except ImportError as e:
                        logger.warning(f"{e}")
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle(f"populse_mia - warning: {e}")
                        msg_path = os.path.join(processes_path, pckg)
                        msg.setText(
                            f"At least, {e.msg.split()[-1]} has not been "
                            f"found in {msg_path}."
                            f"\nTo prevent mia crash when using it, "
                            f"please remove (see File > Package "
                            f"library manager) or load again (see More"
                            f" > Install processes) the corresponding "
                            f"process library."
                        )
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.buttonClicked.connect(msg.close)
                        msg.exec()
                        sys.path.remove(
                            os.path.join(
                                config.get_properties_path(), "processes"
                            )
                        )

                # The processes/ directory being already in the sys.path, the
                # package is certainly not properly installed in the processes
                # directory
                else:
                    logger.warning(f"No module named '{pckg}'")
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle(f"populse_mia - warning: {e}")
                    msg_path = os.path.join(
                        config.get_properties_path(), "processes"
                    )
                    msg.setText(
                        f"At least, {e.msg.split()[-1]} has not been "
                        f"found in {msg_path}."
                        f"\nTo prevent mia crash when using it, "
                        f"please remove (see File > Package "
                        f"library manager) or load again (see More"
                        f" > Install processes) the corresponding "
                        f"process library."
                    )
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()

            except SyntaxError as e:
                logger.warning(
                    f"A problem is detected with the '{pckg}' "
                    f"package...\nTraceback:"
                )
                logger.warning("".join(traceback.format_tb(e.__traceback__)))
                logger.warning(f"{e.__class__.__name__}: {e}")
                trabck = "".join(traceback.format_tb(e.__traceback__))
                txt = (
                    f"A problem is detected with the '{pckg}' package...\n\n"
                    f"Traceback:\n{trabck} {e.__class__.__name__} {e} \n\n"
                    f"This may lead to a later crash of Mia ...\n"
                    f"Do you want Mia tries to fix this issue "
                    f"automatically?\nBe careful, risk of destruction of "
                    f"the '{e.filename}' module!"
                )
                lineCnt = txt.count("\n")
                msg = QMessageBox()
                msg.setWindowTitle(f"populse_mia - warning: {e}")

                if lineCnt > 15:
                    scroll = QScrollArea()
                    scroll.setWidgetResizable(1)
                    content = QWidget()
                    scroll.setWidget(content)
                    layout = QVBoxLayout(content)
                    tmpLabel = QLabel(txt)
                    tmpLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    layout.addWidget(tmpLabel)
                    msg.layout().addWidget(
                        scroll, 0, 0, 1, msg.layout().columnCount()
                    )
                    msg.setStyleSheet(
                        "QScrollArea{min-width:550 px; min-height: 300px}"
                    )

                else:
                    msg.setText(txt)
                    msg.setIcon(QMessageBox.Warning)

                ok_button = msg.addButton(QMessageBox.Ok)
                msg.addButton(QMessageBox.No)
                msg.exec()

                if msg.clickedButton() == ok_button:

                    with open(e.filename) as file:
                        filedata = file.read()
                        filedata = filedata.replace(
                            "<undefined>", "'<undefined>'"
                        )

                    with open(e.filename, "w") as file:
                        file.write(filedata)

            except ValueError as e:
                logger.warning(
                    f"A problem is detected with the '{pckg}' "
                    "package...\nTraceback:"
                )
                logger.warning("".join(traceback.format_tb(e.__traceback__)))
                logger.warning(f"{e.__class__.__name__}: {e}")
                trabck = "".join(traceback.format_tb(e.__traceback__))
                txt = (
                    f"A problem is detected with the '{pckg}' package...\n\n"
                    f"Traceback:\n{trabck} {e.__class__.__name__} \n{e}\n\n"
                    f"This may lead to a later crash of Mia ...\nPlease, "
                    f"try to fix it !..."
                )
                msg = QMessageBox()
                msg.setWindowTitle(f"populse_mia - warning: {e}")
                msg.setText(txt)
                msg.setIcon(QMessageBox.Warning)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()

    if not isinstance(proc_content, dict) or not all(
        k in proc_content for k in ["Packages", "Versions"]
    ):
        # The process_config.yml file is corrupted or no pipeline/process
        # was available during the previous use of mia or their versions
        # are not known
        pack2install = [
            "nipype.interfaces",
            "mia_processes",
            "capsul.pipeline",
        ]
        old_nipypeVer = None
        old_miaProcVer = None
        old_capsulVer = None

    else:

        # During the previous use of Mia, nipype was not available or its
        # version was not known or its version was different from the one
        # currently available on the station
        if (
            (isinstance(proc_content, dict))
            and ("Packages" in proc_content)
            and ("nipype" not in proc_content["Packages"])
        ):
            old_nipypeVer = None
            pack2install.append("nipype.interfaces")

            if (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("nipype" in proc_content["Versions"])
            ):
                logger.warning(
                    "The process_config.yml file seems to be corrupted! "
                    "Let's try to fix it by installing the current nipype "
                    "processes library again in mia ..."
                )

        else:

            if (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and (proc_content["Versions"] is None)
            ) or (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("nipype" in proc_content["Versions"])
                and (proc_content["Versions"]["nipype"] is None)
            ):
                old_nipypeVer = None
                pack2install.append("nipype.interfaces")
                logger.warning(
                    "The process_config.yml file seems to be corrupted! "
                    "Let's try to fix it by installing the nipype processes "
                    "library again in mia ..."
                )

            elif (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("nipype" in proc_content["Versions"])
                and (proc_content["Versions"]["nipype"] != nipypeVer)
            ):
                old_nipypeVer = proc_content["Versions"]["nipype"]
                pack2install.append("nipype.interfaces")

        # During the previous use of mia, mia_processes was not available or
        # its version was not known or its version was different from the one
        # currently available on the station
        if (
            (isinstance(proc_content, dict))
            and ("Packages" in proc_content)
            and ("mia_processes" not in proc_content["Packages"])
        ):
            old_miaProcVer = None
            pack2install.append("mia_processes")

            if (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("mia_processes" in proc_content["Versions"])
            ):
                logger.warning(
                    "The process_config.yml file seems to be corrupted! "
                    "Let's try to fix it by installing the mia_processes "
                    "processes library again in mia ..."
                )

        else:

            if (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and (proc_content["Versions"] is None)
            ) or (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("mia_processes" in proc_content["Versions"])
                and (proc_content["Versions"]["mia_processes"] is None)
            ):
                old_miaProcVer = None
                pack2install.append("mia_processes")
                logger.warning(
                    "The process_config.yml file seems to be corrupted! "
                    "Let's try to fix it by installing the mia_processes "
                    "processes library again in mia ..."
                )

            elif (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("mia_processes" in proc_content["Versions"])
                and (proc_content["Versions"]["mia_processes"] != miaProcVer)
            ):
                old_miaProcVer = proc_content["Versions"]["mia_processes"]
                pack2install.append("mia_processes")

        # During the previous use of mia, capsul was not available or
        # its version was not known or its version was different from the one
        # currently available on the station
        if (
            (isinstance(proc_content, dict))
            and ("Packages" in proc_content)
            and ("capsul" not in proc_content["Packages"])
        ):
            old_capsulVer = None
            pack2install.append("capsul.pipeline")

            if (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("capsul" in proc_content["Versions"])
            ):
                logger.warning(
                    "The process_config.yml file seems to be corrupted! "
                    "Let's try to fix it by installing the capsul "
                    "processes library again in Mia ..."
                )

        else:

            if (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and (proc_content["Versions"] is None)
            ) or (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("capsul" in proc_content["Versions"])
                and (proc_content["Versions"]["capsul"] is None)
            ):
                old_capsulVer = None
                pack2install.append("capsul.pipeline")
                logger.warning(
                    "The process_config.yml file seems to be corrupted! "
                    "Let's try to fix it by installing the capsul "
                    "processes library again in Mia ..."
                )

            elif (
                (isinstance(proc_content, dict))
                and ("Versions" in proc_content)
                and ("capsul" in proc_content["Versions"])
                and (proc_content["Versions"]["capsul"] != capsulVer)
            ):
                old_capsulVer = proc_content["Versions"]["capsul"]
                pack2install.append("capsul.pipeline")

    final_pckgs = dict()  # final_pckgs: the final dic of dic with the
    final_pckgs["Packages"] = {}  # information about the installed packages,
    final_pckgs["Versions"] = {}  # their versions, and the path to access them

    for pckg in pack2install:
        package = PackagesInstall()

        if "nipype" in pckg:  # Save the packages version
            final_pckgs["Versions"]["nipype"] = nipypeVer

            if old_nipypeVer is None:
                logger.info(
                    f"** Installation in Mia of the {pckg} processes "
                    f"library, {nipypeVer} version ..."
                )

            else:
                logger.info(
                    f"** Upgrading of the {pckg} processes library, "
                    f"from {old_nipypeVer} to {nipypeVer} version ..."
                )

        if "mia_processes" in pckg:
            final_pckgs["Versions"]["mia_processes"] = miaProcVer

            if old_miaProcVer is None:
                logger.info(
                    f"** Installation in Mia of the {pckg} processes "
                    f"library, {miaProcVer} version ..."
                )

            else:
                logger.info(
                    f"** Upgrading of the {pckg} processes library, "
                    f"from {old_miaProcVer} to {miaProcVer} version ..."
                )

        if "capsul" in pckg:
            final_pckgs["Versions"]["capsul"] = capsulVer

            if old_capsulVer is None:
                logger.info(
                    f"** Installation in Mia of the {pckg} processes "
                    f"library, {capsulVer} version ..."
                )

            else:
                logger.info(
                    f"** Upgrading of the {pckg} processes library, "
                    f"from {old_capsulVer} to {capsulVer} version ..."
                )

        logger.info(f"\nExploring {pckg} ...")
        pckg_dic = package.add_package(pckg)
        # pckg_dic: a dic of dic representation of a package and its
        #           subpackages/modules
        #           Ex. {package: {subpackage: {pipeline:'process_enabled'}}}

        for item in pckg_dic:
            final_pckgs["Packages"][item] = pckg_dic[item]

    if pack2install:

        if len(pack2install) == 2:

            if not any("nipype" in s for s in pack2install):
                logger.info(
                    f"** The nipype processes library in Mia is already "
                    f"using the current installed version ({nipypeVer}) "
                    f"for this station."
                )

            elif not any("mia_processes" in s for s in pack2install):
                logger.info(
                    f"** The mia_processes library in Mia is already "
                    f"using the current installed version ({miaProcVer}) "
                    f"for this station."
                )

            elif not any("capsul" in s for s in pack2install):
                logger.info(
                    f"** The capsul library in Mia is already "
                    f"using the current installed version ({capsulVer}) "
                    f"for this station."
                )

        elif len(pack2install) == 1:

            if any("nipype" in s for s in pack2install):
                logger.info(
                    f"** The mia_processes and capsul processes libraries "
                    f"are already using in Mia the current installed "
                    f"version ({miaProcVer} and {capsulVer} respectively) "
                    f"for this station."
                )

            elif any("mia_processes" in s for s in pack2install):
                logger.info(
                    f"** The nipype and capsul processes libraries are "
                    f"already using in Mia the current installed "
                    f"version ({nipypeVer} and {capsulVer} respectively) for "
                    f"this station."
                )

            elif any("capsul" in s for s in pack2install):
                logger.info(
                    f"** The mia_processes and nipype processes libraries "
                    f"are already using in Mia the current installed "
                    f"version ({miaProcVer} and {nipypeVer} respectively) "
                    f"for this station."
                )

        if (isinstance(proc_content, dict)) and ("Paths" in proc_content):
            # Save the path to the packages
            final_pckgs["Paths"] = proc_content["Paths"]

        if (isinstance(proc_content, dict)) and ("Versions" in proc_content):

            if proc_content["Versions"] is None:

                for k in ("nipype", "mia_processes", "capsul"):

                    if k not in final_pckgs["Versions"]:
                        final_pckgs["Versions"][k] = None

            else:

                for item in proc_content["Versions"]:

                    if item not in final_pckgs["Versions"]:
                        final_pckgs["Versions"][item] = proc_content[
                            "Versions"
                        ][item]

        # Try to keep the previous configuration before the update
        # of the packages
        if (isinstance(proc_content, dict)) and ("Packages" in proc_content):
            _deepCompDic(proc_content["Packages"], final_pckgs["Packages"])

            for item in proc_content["Packages"]:

                if item not in final_pckgs["Packages"]:
                    final_pckgs["Packages"][item] = proc_content["Packages"][
                        item
                    ]

        with open(proc_config, "w", encoding="utf8") as stream:
            yaml.dump(
                final_pckgs,
                stream,
                default_flow_style=False,
                allow_unicode=True,
            )

    else:
        logger.info(
            f"** Mia is already using the current installed version of nipype"
            f", mia_processes and capsul for this station "
            f"({nipypeVer}, {miaProcVer} and {capsulVer}, respectively)"
        )


def verify_setup(
    dev_mode,
    pypath=[],
    dot_mia_config=os.path.join(
        os.path.expanduser("~"), ".populse_mia", "configuration_path.yml"
    ),
):
    """Check and try to correct the configuration if necessary.

    :param dev_mode (bool): the current developer mode.
                            (True: dev, False: user)
    :param pypath (list): List of paths for the capsul config.
    :dot_mia_config: Path to the configuration_path.yml file.

    :Contains:
        :Private function:
            - _browse_properties_path: the user define the properties_path
                                       parameter
            - _cancel_clicked: exit form Mia
            - _make_default_config: make default configuration
            - _save_yml_file: save data in a YAML file
            - _verify_miaConfig: check the config and try to fix if necessary
    """

    # import Config only here to prevent circular import issue
    from populse_mia.software_properties import Config

    def _browse_properties_path(dialog):
        """
        Let the user define the properties_path parameter.

        This method, used only if the Mia configuration parameters are
        not accessible, goes with the _verify_miaConfig() function,
        which will use the value of the properties_path parameter,
        defined here.

        :param dialog: PyQt5.QtWidgets.QDialog object ('msg' in the
                       main function)
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        options |= QFileDialog.ReadOnly
        caption = (
            f"Please select a root directory for configuration, "
            f"{'dev' if dev_mode else 'user'} mode."
        )
        existDir = QFileDialog(dialog, caption)
        existDir.setFileMode(QFileDialog.DirectoryOnly)
        existDir.setFilter(
            existDir.filter()
            | QDir.AllEntries
            | QDir.Hidden
            | QDir.NoDotAndDotDot
        )
        existDir.setOptions(options)
        existDir.setDirectory(
            os.path.join(os.path.expanduser("~"), ".populse_mia")
        )

        if existDir.exec():
            dialog.file_line_edit.setText(existDir.selectedFiles()[0])

    def _cancel_clicked(dialog):
        """
        Cancel the configuration check.

        :param dialog: PyQt5.QtWidgets.QDialog object ('msg' in the
                       main function)
        """
        dialog.close()
        logger.error(
            "No configuration has been detected. Mia is shutting down..."
        )
        sys.exit(0)

    def _make_default_config(dialog):
        """
        Create default configuration files and directories.

        Default directories (properties_path/properties,
        properties_path/processes/User_processes), configuration files
        (properties_path/properties/saved_projects.yml,
        properties_path/properties/config.yml) and
        properties_path/processes/User_processes__init__.py are created
        only if they do not exist (they are not overwritten if they already
        exist).

        :param dialog: PyQt5.QtWidgets.QDialog object ('msg' in the
                       main function)
        """

        properties_path = dialog.file_line_edit.text().rstrip(os.sep)

        if properties_path.endswith(os.sep):
            properties_path = dialog.file_line_edit.text().rstrip(os.sep)
            dialog.file_line_edit.setText(properties_path)

        if dev_mode is True:

            if not os.path.split(properties_path)[-1] == "dev":
                properties_path = os.path.join(properties_path, "dev")

            else:
                dialog.file_line_edit.setText(os.path.dirname(properties_path))

        else:

            if not os.path.split(properties_path)[-1] == "usr":
                properties_path = os.path.join(properties_path, "usr")

            else:
                dialog.file_line_edit.setText(os.path.dirname(properties_path))

        # properties folder management / initialisation:
        properties_dir = os.path.join(properties_path, "properties")

        if not os.path.exists(properties_dir):
            os.makedirs(properties_dir, exist_ok=True)
            logger.info(f"The {properties_dir} directory is created...")

        config_files = [
            ("saved_projects.yml", {"paths": []}),
            (
                "config.yml",
                "gAAAAABd79UO5tVZSRNqnM5zzbl0KDd7Y98KCSKCNizp9aDq"
                "ADs9dAQHJFbmOEX2QL_jJUHOTBfFFqa3OdfwpNLbvWNU_rR0"
                "VuT1ZdlmTYv4wwRjhlyPiir7afubLrLK4Jfk84OoOeVtR0a5"
                "a0k0WqPlZl-y8_Wu4osHeQCfeWFKW5EWYF776rWgJZsjn3fx"
                "Z-V2g5aHo-Q5aqYi2V1Kc-kQ9ZwjFBFbXNa1g9nHKZeyd3ve"
                "6p3RUSELfUmEhS0eOWn8i-7GW1UGa4zEKCsoY6T19vrimiuR"
                "Vy-DTmmgzbbjGkgmNxB5MvEzs0BF2bAcina_lKR-yeICuIqp"
                "TSOBfgkTDcB0LVPBoQmogUVVTeCrjYH9_llFTJQ3ZtKZLdeS"
                "tFR5Y2I2ZkQETi6m-0wmUDKf-KRzmk6sLRK_oz6GmuTAN8A5"
                "1au2v1M=",
            ),
        ]

        for filename, content in config_files:
            file_path = os.path.join(properties_dir, filename)

            if not os.path.exists(file_path):
                _save_yml_file(content, file_path)
                logger.info(f"The {file_path} file is created...")

        # processes/User_processes folder management / initialisation:
        user_processes_dir = os.path.join(
            properties_path, "processes", "User_processes"
        )

        if not os.path.exists(user_processes_dir):
            os.makedirs(user_processes_dir, exist_ok=True)
            logger.info("The {user_processes_dir} directory is created...")

        init_file = os.path.join(user_processes_dir, "__init__.py")

        if not os.path.exists(init_file):
            Path(init_file).touch()
            logger.info(f"The {init_file} file is created...")

        logger.info("Default configuration checked!")

    def _save_yml_file(content, file_path):
        """Save data in a YAML file.

        :param content (dict): The content of the file_path.
        :param file_path: A .yml file path.
        """

        with open(file_path, "w", encoding="utf8") as configfile:
            yaml.dump(
                content,
                configfile,
                default_flow_style=False,
                allow_unicode=True,
            )

    def _verify_miaConfig(dialog=None):
        """Check the config is not corrupted and try to fix if necessary.

        The purpose of this method is twofold. First, it allows to
        update the obsolete values for some parameters of the
        properties_path/properties/config.yml file. Secondly, it allows
        to correct the value of the properties_user_path / properties_dev_path
        parameter in the ~/.populse_mia/configuration_path.yml file.

        This method goes with the _browse_properties_path() function, the
        latter having allowed the definition of the properties_path parameter,
        the objective here is to check if the value of this parameter is valid.
        The properties_path parameters are saved in the
        ~/.populse_mia/configuration_path.yml file (the properties_user_path
        or the properties_dev_path parameter is mandatory).
        Then the data in the properties/config.yml file are checked. If an
        exception is raised during the _verify_miaConfig function, the
        "Properties path selection" window is not closed and the user is again
        prompted to set the properties_path parameter.

        :param dialog: PyQt5.QtWidgets.QDialog object ('msg' in the
                       main function)
        """

        save_flag = False
        config = None

        if dialog:

            if not dialog.file_line_edit.text():
                # FIXME: Shouldn't we carry out a more thorough invalidity
                #        check (we're only checking the empty
                #        string here)?
                logger.warning(
                    "Warning: configuration root directory is invalid..."
                )
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Mia configuration Error")
                msg.setText("No configuration path found...")
                msg.exec()
                return

            with open(dot_mia_config) as stream:

                try:

                    if verCmp(yaml.__version__, "5.1", "sup"):
                        mia_home_properties_path = yaml.load(
                            stream, Loader=yaml.FullLoader
                        )

                    else:
                        mia_home_properties_path = yaml.load(stream)

                    if mia_home_properties_path is None or not isinstance(
                        mia_home_properties_path, dict
                    ):
                        raise yaml.YAMLError(
                            f"\nThe '{dot_mia_config}' file seems to be "
                            f"corrupted...\n"
                        )

                except yaml.YAMLError:
                    logger.warning(
                        f"\n {dot_mia_config} cannot be read, the path "
                        f"to the properties has not been found..."
                    )
                    mia_home_properties_path = dict()

            mia_home_properties_path_new = dict()

            try:
                _make_default_config(dialog)

            except Exception as e:
                logger.warning(f"Automatic configuration fails: {e} ...")
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Mia configuration Error")
                msg.setText("Automatic configuration fails...")
                msg.exec()
                return

            if dev_mode:
                mia_home_properties_path_new["properties_dev_path"] = (
                    dialog.file_line_edit.text()
                )

            else:
                mia_home_properties_path_new["properties_user_path"] = (
                    dialog.file_line_edit.text()
                )

            mia_home_properties_path = {
                **mia_home_properties_path,
                **mia_home_properties_path_new,
            }
            key_to_del = [
                k
                for k, v in mia_home_properties_path.items()
                if k not in ("properties_dev_path", "properties_user_path")
            ]

            for k in key_to_del:
                del mia_home_properties_path[k]

            logger.info(f"New values in {dot_mia_config}: ")

            for key, value in mia_home_properties_path_new.items():
                logger.info(f"- {key}: {value}")

            print()
            _save_yml_file(mia_home_properties_path, dot_mia_config)

            try:
                config = Config()

                # Check properties/config.yml by checking if
                # key == 'name' / value == 'MIA':
                if config.config["name"] != "MIA":
                    raise yaml.YAMLError(
                        f"\nThe '{dot_mia_config}' file seems to be "
                        f"corrupted...\n"
                    )

                if not config.get_admin_hash():
                    config.set_admin_hash(
                        "60cfd1916033576b0f2368603fe612fb"
                        "78b8c20e4f5ad9cf39c9cf7e912dd282"
                    )

            except Exception as e:
                logger.warning(
                    f"Could not fetch the "
                    f"properties/config.yml file: {e} ..."
                )
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Mia configuration Error")
                msg.setText("No configuration path found...")
                msg.exec()
                return

            else:
                dialog.close()

        else:
            config = Config()

            # Check properties/config.yml by checking if
            # key == 'name' / value == 'MIA':
            if config.config["name"] != "MIA":
                raise yaml.YAMLError(
                    f"\nThe '{dot_mia_config}' file seems to be "
                    f"corrupted...\n"
                )

            if not config.get_admin_hash():
                config.set_admin_hash(
                    "60cfd1916033576b0f2368603fe612fb"
                    "78b8c20e4f5ad9cf39c9cf7e912dd282"
                )

        if config is not None:

            for key, value in config.config.items():

                # Patch for obsolete values
                if value == "no":
                    save_flag = True
                    config.config[key] = False

                if value == "yes":
                    save_flag = True
                    config.config[key] = True

                if save_flag is True:
                    config.saveConfig()

    # The directory in which the configuration is located must be
    # declared in ~/.populse_mia/configuration_path.yml
    # dot_mia_config = os.path.join(
    #     os.path.expanduser("~"), ".populse_mia", "configuration_path.yml"
    # )

    # ~/.populse_mia/configuration_path.yml management/initialisation
    if not os.path.exists(os.path.dirname(dot_mia_config)):
        os.mkdir(os.path.dirname(dot_mia_config))
        logger.info(
            f"The {os.path.dirname(dot_mia_config)} directory is "
            f"created..."
        )
        Path(os.path.join(dot_mia_config)).touch()

    if not os.path.exists(dot_mia_config):
        Path(os.path.join(dot_mia_config)).touch()

    try:

        # Just to check if dot_mia_config file is well readable/writeable
        with open(dot_mia_config) as stream:

            if version.parse(yaml.__version__) > version.parse("5.1"):
                mia_home_properties_path = yaml.load(
                    stream, Loader=yaml.FullLoader
                )

            else:
                mia_home_properties_path = yaml.load(stream)

        if mia_home_properties_path is None:
            raise yaml.YAMLError(
                f"\nThe '{dot_mia_config}' file seems to be "
                f"corrupted or the configuration has never "
                f"been initialized...\n"
            )

        if dev_mode and "properties_dev_path" not in mia_home_properties_path:
            raise yaml.YAMLError(
                f"\nNo properties path found in {dot_mia_config}...\n"
            )

        elif (
            not dev_mode
            and "properties_user_path" not in mia_home_properties_path
        ):
            raise yaml.YAMLError(
                f"\nNo properties path found in {dot_mia_config}...\n"
            )

        _save_yml_file(mia_home_properties_path, dot_mia_config)
        _verify_miaConfig()

    except Exception as e:
        # the ~/.populse_mia/configuration_path.yml or the
        # properties/config.yml file does not exist or has not been
        # correctly read...

        # FIXME: We may be need a more precise Exception class to catch ?
        logger.warning(
            f"An issue has been detected when opening "
            f"the {dot_mia_config} file or with the parameters returned "
            f"from this file:{e}"
        )

        # open popup, we choose the properties path dir
        msg = QDialog()
        msg.setWindowTitle("populse_mia - properties path selection")
        vbox_layout = QVBoxLayout()
        hbox_layout = QHBoxLayout()
        file_label = QLabel(
            "No configuration parameters found. Please select a root "
            "directory for configuration."
        )
        msg.file_line_edit = QLineEdit()
        msg.file_line_edit.setText(os.path.dirname(dot_mia_config))
        msg.file_line_edit.setFixedWidth(400)
        file_button = QPushButton("Browse")
        file_button.clicked.connect(partial(_browse_properties_path, msg))
        vbox_layout.addWidget(file_label)
        hbox_layout.addWidget(msg.file_line_edit)
        hbox_layout.addWidget(file_button)
        vbox_layout.addLayout(hbox_layout)
        hbox_layout = QHBoxLayout()
        msg.ok_button = QPushButton("Ok")
        msg.ok_button.clicked.connect(partial(_verify_miaConfig, msg))
        msg.cancel_button = QPushButton("Cancel")
        msg.cancel_button.clicked.connect(partial(_cancel_clicked, msg))
        hbox_layout.addWidget(msg.cancel_button)
        hbox_layout.addWidget(msg.ok_button)
        vbox_layout.addLayout(hbox_layout)
        msg.setLayout(vbox_layout)
        msg.exec()

    # Adding personal libraries User_processes (and others if any) to sys.path
    # and to pypath.
    config = Config()
    properties_path = config.get_properties_path()
    user_proc = os.path.join(properties_path, "processes")

    if os.path.isdir(user_proc):
        user_proc_dir = os.listdir(user_proc)

        if user_proc_dir:
            sys.path.append(user_proc)
            pypath.append(user_proc)

            for elt in user_proc_dir:
                logger.info(f"  . Using {elt} package from {user_proc}...")

        del user_proc_dir

        try:
            del elt

        except NameError:
            # There's nothing in the "processes" directory! Let's try to fix
            #  it and put at least one valid directory User_processes
            os.mkdir(os.path.join(user_proc, "User_processes"))
            Path(
                os.path.join(user_proc, "User_processes", "__init__.py")
            ).touch()

    if pypath:
        config.get_capsul_engine()
        c = config.get_capsul_config()
        pc = (
            c.setdefault("engine", {})
            .setdefault("global", {})
            .setdefault("capsul.engine.module.python", {})
            .setdefault("python", {})
        )
        pc["executable"] = sys.executable
        pc["config_id"] = "python"
        pc["config_environment"] = "global"

        if "path" in pc:
            matches = [
                "capsul",
                "mia_processes",
                "populse_mia",
                os.path.join("populse_db", "python"),
                os.path.join("soma-base", "python"),
                os.path.join("soma-workflow", "python"),
                os.path.join("populse_mia", "processes"),
            ]

            for i in pc["path"]:

                if i not in pypath and not any(x in i for x in matches):
                    pypath.append(i)

        pc["path"] = pypath
        logger.info(f"Changed python conf: {pc}")
        config.update_capsul_config()
        config.saveConfig()
