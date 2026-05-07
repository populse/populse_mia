"""
Module to handle the projects and their database.
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

__all__ = [
    "FIELD_TYPE_STRING",
    "FIELD_TYPE_INTEGER",
    "FIELD_TYPE_FLOAT",
    "FIELD_TYPE_BOOLEAN",
    "FIELD_TYPE_DATE",
    "FIELD_TYPE_DATETIME",
    "FIELD_TYPE_TIME",
    "FIELD_TYPE_JSON",
    "FIELD_TYPE_LIST_STRING",
    "FIELD_TYPE_LIST_INTEGER",
    "FIELD_TYPE_LIST_FLOAT",
    "FIELD_TYPE_LIST_BOOLEAN",
    "FIELD_TYPE_LIST_DATE",
    "FIELD_TYPE_LIST_DATETIME",
    "FIELD_TYPE_LIST_TIME",
    "FIELD_TYPE_LIST_JSON",
    "ALL_TYPES",
    "FIELD_TYPE_MAPPING",
    "TAG_UNIT_MS",
    "TAG_UNIT_MM",
    "TAG_UNIT_DEGREE",
    "TAG_UNIT_HZPIXEL",
    "TAG_UNIT_MHZ",
    "ALL_UNITS",
    "COLLECTION_CURRENT",
    "COLLECTION_INITIAL",
    "COLLECTION_BRICK",
    "COLLECTION_HISTORY",
    "FIELD_ATTRIBUTES_COLLECTION",
    "TAG_ORIGIN_BUILTIN",
    "TAG_ORIGIN_USER",
    "TAG_CHECKSUM",
    "TAG_TYPE",
    "TAG_EXP_TYPE",
    "TAG_FILENAME",
    "TAG_BRICKS",
    "TAG_HISTORY",
    "CLINICAL_TAGS",
    "BRICK_ID",
    "BRICK_NAME",
    "BRICK_INPUTS",
    "BRICK_OUTPUTS",
    "BRICK_INIT",
    "BRICK_EXEC",
    "BRICK_INIT_TIME",
    "BRICK_EXEC_TIME",
    "HISTORY_ID",
    "HISTORY_PIPELINE",
    "HISTORY_BRICKS",
    "TYPE_BVEC",
    "TYPE_BVAL",
    "TYPE_BVEC_BVAL",
    "TYPE_NII",
    "TYPE_MAT",
    "TYPE_TXT",
    "TYPE_UNKNOWN",
    "NOT_DEFINED_VALUE",
]

from datetime import date, datetime, time

# Special attributes for the database

# V2 field types (obsolete now)
# FIELD_TYPE_STRING = "string"
# FIELD_TYPE_INTEGER = "int"
# FIELD_TYPE_FLOAT = "float"
# FIELD_TYPE_BOOLEAN = "boolean"
# FIELD_TYPE_DATE = "date"
# FIELD_TYPE_DATETIME = "datetime"
# FIELD_TYPE_TIME = "time"
# FIELD_TYPE_JSON = "json"
# FIELD_TYPE_LIST_STRING = "list_string"
# FIELD_TYPE_LIST_INTEGER = "list_int"
# FIELD_TYPE_LIST_FLOAT = "list_float"
# FIELD_TYPE_LIST_BOOLEAN = "list_boolean"
# FIELD_TYPE_LIST_DATE = "list_date"
# FIELD_TYPE_LIST_DATETIME = "list_datetime"
# FIELD_TYPE_LIST_TIME = "list_time"
# FIELD_TYPE_LIST_JSON = "list_json"
# ALL_TYPES = {
#     FIELD_TYPE_LIST_STRING,
#     FIELD_TYPE_LIST_INTEGER,
#     FIELD_TYPE_LIST_FLOAT,
#     FIELD_TYPE_LIST_BOOLEAN,
#     FIELD_TYPE_LIST_DATE,
#     FIELD_TYPE_LIST_DATETIME,
#     FIELD_TYPE_LIST_TIME,
#     FIELD_TYPE_LIST_JSON,
#     FIELD_TYPE_STRING,
#     FIELD_TYPE_INTEGER,
#     FIELD_TYPE_FLOAT,
#     FIELD_TYPE_BOOLEAN,
#     FIELD_TYPE_DATE,
#     FIELD_TYPE_DATETIME,
#     FIELD_TYPE_TIME,
#     FIELD_TYPE_JSON,
# }

# V3 field types
#: Field type for string values (maps to Python :class:`str`).
FIELD_TYPE_STRING = str

#: Field type for integer values (maps to Python :class:`int`).
FIELD_TYPE_INTEGER = int

#: Field type for floating-point values (maps to Python :class:`float`).
FIELD_TYPE_FLOAT = float

#: Field type for boolean values (maps to Python :class:`bool`).
FIELD_TYPE_BOOLEAN = bool

#: Field type for date values (maps to :class:`datetime.date`).
FIELD_TYPE_DATE = date

#: Field type for datetime values (maps to :class:`datetime.datetime`).
FIELD_TYPE_DATETIME = datetime

#: Field type for time values (maps to :class:`datetime.time`).
FIELD_TYPE_TIME = time

#: Field type for JSON objects (maps to Python :class:`dict`).
FIELD_TYPE_JSON = dict

#: Field type for lists of string values
#: (maps to :class:`list` of :class:`str`).
FIELD_TYPE_LIST_STRING = list[str]

#: Field type for lists of integer values
#: (maps to :class:`list` of :class:`int`).
FIELD_TYPE_LIST_INTEGER = list[int]

#: Field type for lists of floating-point values
#: (maps to :class:`list` of :class:`float`).
FIELD_TYPE_LIST_FLOAT = list[float]

#: Field type for lists of boolean values
#: (maps to :class:`list` of :class:`bool`).
FIELD_TYPE_LIST_BOOLEAN = list[bool]

#: Field type for lists of date values
#: (maps to :class:`list` of :class:`datetime.date`).
FIELD_TYPE_LIST_DATE = list[date]

#: Field type for lists of datetime values
#: (maps to :class:`list` of :class:`datetime.datetime`).
FIELD_TYPE_LIST_DATETIME = list[datetime]

#: Field type for lists of time values
#: (maps to :class:`list` of :class:`datetime.time`).
FIELD_TYPE_LIST_TIME = list[time]

#: Field type for lists of JSON objects
#: (maps to :class:`list` of :class:`dict`).
FIELD_TYPE_LIST_JSON = list[dict]

#: Set of all supported field types (both scalar and list variants).
ALL_TYPES = {
    FIELD_TYPE_LIST_STRING,
    FIELD_TYPE_LIST_INTEGER,
    FIELD_TYPE_LIST_FLOAT,
    FIELD_TYPE_LIST_BOOLEAN,
    FIELD_TYPE_LIST_DATE,
    FIELD_TYPE_LIST_DATETIME,
    FIELD_TYPE_LIST_TIME,
    FIELD_TYPE_LIST_JSON,
    FIELD_TYPE_STRING,
    FIELD_TYPE_INTEGER,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_TIME,
    FIELD_TYPE_JSON,
}

#: Mapping from V2 string field type names to their corresponding V3 Python
#: types. Used for backwards compatibility when reading older database formats.
FIELD_TYPE_MAPPING = {
    "string": str,
    "int": int,
    "float": float,
    "boolean": bool,
    "date": date,
    "datetime": datetime,
    "time": time,
    "json": dict,
    "list_string": list[str],
    "list_int": list[int],
    "list_float": list[float],
    "list_boolean": list[bool],
    "list_date": list[date],
    "list_datetime": list[datetime],
    "list_time": list[time],
    "list_json": list[dict],
}

# Tag units
#: Tag unit for milliseconds.
TAG_UNIT_MS = "ms"

#: Tag unit for millimetres.
TAG_UNIT_MM = "mm"

#: Tag unit for degrees.
TAG_UNIT_DEGREE = "degree"

#: Tag unit for Hz per pixel.
TAG_UNIT_HZPIXEL = "Hz/pixel"

#: Tag unit for megahertz.
TAG_UNIT_MHZ = "MHz"

#: List of all supported tag units.
ALL_UNITS = [
    TAG_UNIT_MS,
    TAG_UNIT_MM,
    TAG_UNIT_DEGREE,
    TAG_UNIT_HZPIXEL,
    TAG_UNIT_MHZ,
]

# Collections
#: Name of the collection storing the current state of the database.
COLLECTION_CURRENT = "current"

#: Name of the collection storing the initial state of the database at import
#: time.
COLLECTION_INITIAL = "initial"

#: Name of the collection storing brick (pipeline process) records.
COLLECTION_BRICK = "brick"

#: Name of the collection storing the full pipeline execution history.
COLLECTION_HISTORY = "history"

#: Name of the internal collection storing field metadata and attributes.
FIELD_ATTRIBUTES_COLLECTION = "mia_field_attributes"

# Tag origins
#: Tag origin indicating the tag is a built-in MIA tag.
TAG_ORIGIN_BUILTIN = "builtin"

#: Tag origin indicating the tag was created by the user.
TAG_ORIGIN_USER = "user"

# MIA tags
#: Tag name for the file checksum, used to detect file modifications.
TAG_CHECKSUM = "Checksum"

#: Tag name for the document type (e.g. Scan, Matrix, Text).
TAG_TYPE = "Type"

#: Tag name for the experimental type of the document.
TAG_EXP_TYPE = "Exp Type"

#: Tag name for the file name of the document.
TAG_FILENAME = "FileName"

#: Tag name for the list of brick IDs that produced the document.
TAG_BRICKS = "History"

#: Tag name for the full pipeline execution history associated with the
#: document.
TAG_HISTORY = "Full history"

#: Dictionary of clinical tag names and their descriptions.
#: These tags store patient and acquisition metadata.
CLINICAL_TAGS = {
    "Age": "patient's age",
    "Institution": "site where the NMR spectrometer is installed",
    "Manufacturer": "manufacturer of the MRI spectrometer",
    # fmt: off
    "Manufacturer's Model":
        "manufacturer's model name of the MRI spectrometer",
    # fmt: on
    "Message": "brief message about the patient",
    "MagneticFieldStrength": "nominal field strength of MR magnet in Tesla",
    "PatientRef": "patient's anonymous reference",
    "Pathology": "patient's pathology",
    "Sex": "patient's gender",
    "SoftwareVersions": "version of the software used to acquire the data",
}

# Brick attributes
#: Brick field name for the unique identifier of a brick.
BRICK_ID = "ID"

#: Brick field name for the name of the brick (pipeline process).
BRICK_NAME = "Name"

#: Brick field name for the list of input parameters of the brick.
BRICK_INPUTS = "Input(s)"

#: Brick field name for the list of output parameters of the brick.
BRICK_OUTPUTS = "Output(s)"

#: Brick field name for the initialisation status of the brick.
BRICK_INIT = "Init"

#: Brick field name for the execution status of the brick.
BRICK_EXEC = "Exec"

#: Brick field name for the timestamp of the brick initialisation.
BRICK_INIT_TIME = "Init Time"

#: Brick field name for the timestamp of the brick execution.
BRICK_EXEC_TIME = "Exec Time"

# History attributes
#: History field name for the unique identifier of a history record.
HISTORY_ID = "ID"

#: History field name for the XML serialisation of the pipeline.
HISTORY_PIPELINE = "Pipeline xml"

#: History field name for the list of brick UUIDs in the history record.
HISTORY_BRICKS = "Bricks uuid"

# Document types
#: Document type for b-vector files used in diffusion MRI.
TYPE_BVEC = "Bvec"

#: Document type for b-value files used in diffusion MRI.
TYPE_BVAL = "Bval"

#: Document type for combined b-vector/b-value files in MRtrix format.
TYPE_BVEC_BVAL = "Bvec_bval_MRTRIX"

#: Document type for NIfTI scan files.
TYPE_NII = "Scan"

#: Document type for matrix files.
TYPE_MAT = "Matrix"

#: Document type for plain text files.
TYPE_TXT = "Text"

#: Document type for files with an unrecognised or unsupported format.
TYPE_UNKNOWN = "Unknown"

# Placeholder value
#: Placeholder string displayed when a tag has no value defined for a document.
NOT_DEFINED_VALUE = "*Not Defined*"
