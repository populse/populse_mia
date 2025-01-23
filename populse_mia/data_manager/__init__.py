# -*- coding: utf-8 -*-

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

# Special attributes for the database

# from populse_db
from populse_db.database import (  # noqa: F401
    ALL_TYPES,
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_INTEGER,
    FIELD_TYPE_JSON,
    FIELD_TYPE_LIST_BOOLEAN,
    FIELD_TYPE_LIST_DATE,
    FIELD_TYPE_LIST_DATETIME,
    FIELD_TYPE_LIST_FLOAT,
    FIELD_TYPE_LIST_INTEGER,
    FIELD_TYPE_LIST_JSON,
    FIELD_TYPE_LIST_STRING,
    FIELD_TYPE_LIST_TIME,
    FIELD_TYPE_STRING,
    FIELD_TYPE_TIME,
)

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

# Mia tags
TAG_ORIGIN_BUILTIN = "builtin"
TAG_ORIGIN_USER = "user"
TAG_CHECKSUM = "Checksum"
TAG_TYPE = "Type"
TAG_EXP_TYPE = "Exp Type"
TAG_FILENAME = "FileName"
TAG_BRICKS = "History"
TAG_HISTORY = "Full history"
CLINICAL_TAGS = [
    "Site",
    "Spectro",
    "MR",
    "PatientRef",
    "Pathology",
    "Age",
    "Sex",
    "Message",
]

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
