"""Module to handle the projects and their database.

Contains:
    Module:
      - data_loader
      - database_mia
      - filter
      - project
      - project_properties

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

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
FIELD_TYPE_STRING = str
FIELD_TYPE_INTEGER = int
FIELD_TYPE_FLOAT = float
FIELD_TYPE_BOOLEAN = bool
FIELD_TYPE_DATE = date
FIELD_TYPE_DATETIME = datetime
FIELD_TYPE_TIME = time
FIELD_TYPE_JSON = dict
FIELD_TYPE_LIST_STRING = list[str]
FIELD_TYPE_LIST_INTEGER = list[int]
FIELD_TYPE_LIST_FLOAT = list[float]
FIELD_TYPE_LIST_BOOLEAN = list[bool]
FIELD_TYPE_LIST_DATE = list[date]
FIELD_TYPE_LIST_DATETIME = list[datetime]
FIELD_TYPE_LIST_TIME = list[time]
FIELD_TYPE_LIST_JSON = list[dict]
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

# Mapping between V2 and V3 field types
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

# Tag unit
TAG_UNIT_MS = "ms"
TAG_UNIT_MM = "mm"
TAG_UNIT_DEGREE = "degree"
TAG_UNIT_HZPIXEL = "Hz/pixel"
TAG_UNIT_MHZ = "MHz"
ALL_UNITS = [
    TAG_UNIT_MS,
    TAG_UNIT_MM,
    TAG_UNIT_DEGREE,
    TAG_UNIT_HZPIXEL,
    TAG_UNIT_MHZ,
]

# Collections
COLLECTION_CURRENT = "current"
COLLECTION_INITIAL = "initial"
COLLECTION_BRICK = "brick"
COLLECTION_HISTORY = "history"
FIELD_ATTRIBUTES_COLLECTION = "mia_field_attributes"

# Tag origin
TAG_ORIGIN_BUILTIN = "builtin"
TAG_ORIGIN_USER = "user"

# Mia tags
TAG_CHECKSUM = "Checksum"
TAG_TYPE = "Type"
TAG_EXP_TYPE = "Exp Type"
TAG_FILENAME = "FileName"
TAG_BRICKS = "History"
TAG_HISTORY = "Full history"
CLINICAL_TAGS = {
    "Site": "the site where the NMR spectrometer is installed",
    "Spectro": "the NMR spectrometer used",
    "MR": "the field strength of the NMR spectrometer",
    "PatientRef": "the patient's anonymous reference",
    "Pathology": "the patient's pathology",
    "Age": "the patient's age",
    "Sex": "the patient's gender",
    "Message": "a brief message about the patient",
}

# Bricks
BRICK_ID = "ID"
BRICK_NAME = "Name"
BRICK_INPUTS = "Input(s)"
BRICK_OUTPUTS = "Output(s)"
BRICK_INIT = "Init"
BRICK_EXEC = "Exec"
BRICK_INIT_TIME = "Init Time"
BRICK_EXEC_TIME = "Exec Time"

# History
HISTORY_ID = "ID"
HISTORY_PIPELINE = "Pipeline xml"
HISTORY_BRICKS = "Bricks uuid"

# Document types
TYPE_BVEC = "Bvec"
TYPE_BVAL = "Bval"
TYPE_BVEC_BVAL = "Bvec_bval_MRTRIX"
TYPE_NII = "Scan"
TYPE_MAT = "Matrix"
TYPE_TXT = "Text"
TYPE_UNKNOWN = "Unknown"

# Variable shown everywhere when no value for the tag
NOT_DEFINED_VALUE = "*Not Defined*"
