# -*- coding: utf-8 -*-
"""Module that contains class to override the default behaviour of
populse_db and some of its methods

:Contains:
   Class:
      - DatabaseMIA
      - DatabaseSessionMIA

"""


##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# from datetime import datetime

# Populse_db imports
from populse_db.storage import Storage

# populse_mia imports
from populse_mia.data_manager.database import DatabaseEngine

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

# Shemas
# schemas = [
#     {
#         "version": "1.0.0",
#         "schema": {
#             FIELD_ATTRIBUTES_COLLECTION: [
#                 {
#                     "index": [str, {
#                         "primary_key": True,
#                         "description": "The index name of the field as: "
#                         "collection name|collection primary_key column name"
#                         }
#                         ],
#                     "visibility": [bool, {
#                         "description": "Visibility of the index field in "
#                         "the DataBrowser"
#                         }
#                         ],
#                     "origin": [str, {
#                         "description": "Define the origin of the index "
#                         "field, TAG_ORIGIN_BUILTIN or TAG_ORIGIN_USER"
#                         }
#                         ],
#                     "unit": [str, {
#                         "description": "Unit of the index field"
#                         }
#                         ],
#                     "default_value": [str, {
#                         "description": "Default value of the index field"
#                         }
#                         ],
#                     "description": [str, {
#                         "description": "I still don't know if we need this "
#                         "field?"
#                         }
#                         ],
#                 }
#             ],
#             COLLECTION_CURRENT: [
#                 {
#                     TAG_FILENAME: [str, {"primary_key": True}],
#                     TAG_CHECKSUM: str,
#                     TAG_TYPE: str,
#                     TAG_EXP_TYPE: str,
#                     TAG_BRICKS: list[str],
#                     TAG_HISTORY: str,
#                 }
#             ],
#             COLLECTION_INITIAL: [
#                 {
#                     TAG_FILENAME: [str, {"primary_key": True}],
#                     TAG_CHECKSUM: str,
#                     TAG_TYPE: str,
#                     TAG_EXP_TYPE: str,
#                     TAG_BRICKS: list[str],
#                     TAG_HISTORY: str,
#                 }
#             ],
#             COLLECTION_BRICK: [
#                 {
#                     BRICK_ID: [str, {"primary_key": True}],
#                     BRICK_NAME: str,
#                     BRICK_INPUTS: dict,
#                     BRICK_OUTPUTS: dict,
#                     BRICK_INIT: str,
#                     BRICK_INIT_TIME: datetime,
#                     BRICK_EXEC: str,
#                     BRICK_EXEC_TIME: datetime,
#                 }
#             ],
#             COLLECTION_HISTORY: [
#                 {
#                     HISTORY_ID: [str, {"primary_key": True}],
#                     HISTORY_PIPELINE: str,
#                     HISTORY_BRICKS: list[str],
#                 }
#             ],
#         },
#     },
# ]


class DatabaseMIA(DatabaseEngine):
    """
    Class overriding the default behavior of populse_db.

    .. Methods:
        - add_collection: overrides the method adding a collection
        - add_field_attributes_collection: add the
                                           FIELD_ATTRIBUTES_COLLECTION
                                           collection (for internal
                                           operation of populse_mia
                                           and associated fields)
        - add_field: adds a field to the database, if it does not already
                     exist
        - add_fields: adds the list of fields
        - remove_field:  removes a field in the collection
        - get_field: get a field of a collection
        - get_fields: get all the fields of a collection
        - get_shown_tags: gives the list of visible tags
        - set_shown_tags: sets the list of visible tags
    """

    def __init__(
        self,
        database_engine,
        schema_name="populse_mia.data_manager.database_mia",
    ):
        """ "Constructor"""
        # Initialize the storage with the provided database engine
        self.storage = Storage(database_engine)

        # with self.storage.schema() as schema:
        #     schema.add_schema(schema_name)

    def __del__(self):
        """ "Destructor for the class.

        This method is automatically called when an object is being
        destroyed. It performs cleanup actions such as closing any
        open resources or connections.
        """
        self.close()

    def close(self):
        """Closes any open resources or connections held by the instance.

        This method sets the `storage` attribute to `None`, effectively
        releasing any held references and cleaning up the object's state.
        """
        self.storage = None

    def add_collection(
        self, name, primary_key, visibility, origin, unit, default_value
    ):
        """Override the method adding a collection of populse_db.

        :param name: New collection name
        :param primary_key: New collection primary_key column
        :param visibility: Primary key visibility
        :param origin: Primary key origin
        :param unit: Primary key unit
        :param default_value: Primary key default value
        """
        self.add_field_attributes_collection()
        has_collection = super(DatabaseMIA, self).has_collection(name)

        if not has_collection:

            with self.storage.schema() as schema:
                schema.add_collection(name, primary_key)

            index = f"{name}|{primary_key}"
            super(DatabaseMIA, self).add_values(
                FIELD_ATTRIBUTES_COLLECTION,
                index,
                {
                    "visibility": visibility,
                    "origin": origin,
                    "unit": unit,
                    "default_value": default_value,
                },
            )

        # super(DatabaseMIA, self).add_collection(name, primary_key)
        # self.add_document(
        #     FIELD_ATTRIBUTES_COLLECTION,
        #     {
        #         "index": "%s|%s" % (name, primary_key),
        #         "field": primary_key,
        #         "visibility": visibility,
        #         "origin": origin,
        #         "unit": unit,
        #         "default_value": default_value,
        #     },
        # )
        raise NotImplementedError(
            "This method (add_collection) is not yet available in "
            "DatabaseMIA class."
        )

    def add_field_attributes_collection(self):
        """Ensures that the `FIELD_ATTRIBUTES_COLLECTION` is available in
        the database.

        If it does not exist, it creates the collection and adds specific
        fields to it such as 'visibility', 'origin', 'unit', and
        'default_value'.
        """
        has_collection = super(DatabaseMIA, self).has_collection(
            FIELD_ATTRIBUTES_COLLECTION
        )

        if not has_collection:

            with self.storage.schema() as schema:
                schema.add_collection(
                    FIELD_ATTRIBUTES_COLLECTION,
                    primary_key="index",
                    # description="The index name of the field as: "
                    # "collection name|collection primary_key column nam"
                )
                schema.add_field(
                    FIELD_ATTRIBUTES_COLLECTION,
                    "visibility",
                    bool,
                    "Visibility of the index field in " "the DataBrowser",
                )
                schema.add_field(
                    FIELD_ATTRIBUTES_COLLECTION,
                    "origin",
                    str,
                    "Define the origin of the index "
                    "field, TAG_ORIGIN_BUILTIN or TAG_ORIGIN_USER",
                )
                schema.add_field(
                    FIELD_ATTRIBUTES_COLLECTION,
                    "unit",
                    str,
                    "Unit of the index field",
                )
                schema.add_field(
                    FIELD_ATTRIBUTES_COLLECTION,
                    "default_value",
                    str,
                    "Default value of the index field",
                )

    def add_field(
        self,
        collection,
        name,
        field_type,
        description,
        visibility,
        origin,
        unit,
        default_value,
        index=False,
        flush=True,
    ):
        """Add a field to the database, if it does not already exist.

        :param collection: field collection (str)
        :param name: field name (str)
        :param field_type: field type (string, int, float, boolean, date,
                           datetime, time, list_string, list_int, list_float,
                           list_boolean, list_date, list_datetime or list_time)
        :param description: field description (str or None)
        :param visibility: Bool to know if the field is visible in the
                           databrowser
        :param origin: To know the origin of a field,
                       in [TAG_ORIGIN_BUILTIN, TAG_ORIGIN_USER]
        :param unit: Origin of the field, in [TAG_UNIT_MS, TAG_UNIT_MM,
                     TAG_UNIT_DEGREE, TAG_UNIT_HZPIXEL, TAG_UNIT_MHZ]
        :param default_value: Default_value of the field, can be str or None
        :param flush: bool to know if the table classes must be updated (put
                      False if in the middle of filling fields) => True by
                      default
        """
        # super(DatabaseSessionMIA, self).add_field(
        #     collection, name, field_type, description
        # )
        # self.add_document(
        #     FIELD_ATTRIBUTES_COLLECTION,
        #     {
        #         "index": "%s|%s" % (collection, name),
        #         "field": name,
        #         "visibility": visibility,
        #         "origin": origin,
        #         "unit": unit,
        #         "default_value": default_value,
        #     },
        # )
        with self.storage.data() as db:
            print("db: ", db)
        raise NotImplementedError(
            "This method (add_field) is not yet available in DatabaseMIA "
            "class."
        )

    def add_fields(self, fields):
        """Add the list of fields.

        :param fields: list of fields (collection, name, type, description,
                       visibility, origin, unit, default_value)
        """

        # for field in fields:
        #     # Adding each field
        #     self.add_field(
        #         field[0],
        #         field[1],
        #         field[2],
        #         field[3],
        #         field[4],
        #         field[5],
        #         field[6],
        #         field[7],
        #         False,
        #     )
        raise NotImplementedError(
            "This method (add_fields) is not yet available in DatabaseMIA "
            "class."
        )

    def remove_field(self, collection, fields):
        """
        Removes a field in the collection

        :param collection: Field collection (str, must be existing)

        :param field: Field name (str, must be existing), or list of fields
         (list of str, must all be existing)

        :raise ValueError: - If the collection does not exist
                           - If the field does not exist
        """
        # super(DatabaseSessionMIA, self).remove_field(collection, fields)
        # if isinstance(fields, str):
        #     fields = [fields]
        # for field in fields:
        #     self.remove_document(
        #         FIELD_ATTRIBUTES_COLLECTION, "%s|%s" % (collection, field)
        #     )
        raise NotImplementedError(
            "This method (remove_field) is not yet available in DatabaseMIA "
            "class."
        )

    def get_field(self, collection, name):
        """Retrieves a field from the specified collection in the database.

        This method first attempts to get the field. If the field is found,
        it then retrieves additional attributes from the
        `FIELD_ATTRIBUTES_COLLECTION` using a specific index format. The
        retrieved attributes (like 'visibility', 'origin', 'unit',
        'default_value') are then set on the field object."""
        # field = super(DatabaseSessionMIA, self).get_field(collection, name)
        # if field is not None:
        #     index = "%s|%s" % (collection, name)
        #     attrs = self.get_document(FIELD_ATTRIBUTES_COLLECTION, index)
        #     for i in ("visibility", "origin", "unit", "default_value"):
        #         setattr(field, i, getattr(attrs, i, None))
        # return field
        raise NotImplementedError(
            "This method (get_field) is not yet available in DatabaseMIA "
            "class."
        )

    def get_fields(self, collection):
        """Retrieves all fields from the specified collection in the database.

        This method first fetches all fields associated with the given
        collection. For each field, it then attempts to retrieve
        additional attributes from the `FIELD_ATTRIBUTES_COLLECTION` using a
        specific index format. These attributes (like 'visibility', 'origin',
        'unit', 'default_value') are set on each field object."""
        # fields = super(DatabaseSessionMIA, self).get_fields(collection)
        # for field in fields:
        #     name = field.field_name
        #     index = "%s|%s" % (collection, name)
        #     attrs = self.get_document(FIELD_ATTRIBUTES_COLLECTION, index)
        #     for i in ("visibility", "origin", "unit", "default_value"):
        #         setattr(field, i, getattr(attrs, i, None))
        # return fields
        raise NotImplementedError(
            "This method (get_fields) is not yet available in DatabaseMIA "
            "class."
        )

    def get_shown_tags(self):
        """Give the list of visible tags.

        :return: the list of visible tags
        """
        # visible_names = []
        # names_set = set()
        # for i in self.filter_documents(
        #     FIELD_ATTRIBUTES_COLLECTION, "{visibility} == true"
        # ):
        #     if i.field not in names_set:
        #         names_set.add(i.field)
        #         visible_names.append(i.field)  # respect list order
        # return visible_names
        raise NotImplementedError(
            "This method (get_shown_tags) is not yet available in "
            "DatabaseMIA class."
        )

    def set_shown_tags(self, fields_shown, *args, **kwargs):
        """Set the list of visible tags.

        :param fields_shown: list of visible tags
        """
        # for field in self.get_documents(FIELD_ATTRIBUTES_COLLECTION):
        #     self.set_value(
        #         FIELD_ATTRIBUTES_COLLECTION,
        #         field.index,
        #         "visibility",
        #         field.field in fields_shown,
        #     )
        raise NotImplementedError(
            "This method (set_shown_tags) is not yet available in "
            "DatabaseMIA class."
        )
