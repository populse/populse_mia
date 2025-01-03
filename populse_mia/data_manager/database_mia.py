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

from populse_db.database import FIELD_TYPE_STRING, str_to_type, type_to_str

# Populse_db imports
from populse_db.storage import Storage

# Field types
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

# FIELD_TYPE_STRING = str
# FIELD_TYPE_INTEGER = int
# FIELD_TYPE_FLOAT = float
# FIELD_TYPE_BOOLEAN = bool
# FIELD_TYPE_DATE = date
# FIELD_TYPE_DATETIME = datetime
# FIELD_TYPE_TIME = time
# FIELD_TYPE_JSON = dict
# FIELD_TYPE_LIST_STRING = list[str]
# FIELD_TYPE_LIST_INTEGER = list[int]
# FIELD_TYPE_LIST_FLOAT = list[float]
# FIELD_TYPE_LIST_BOOLEAN = list[bool]
# FIELD_TYPE_LIST_DATE = list[date]
# FIELD_TYPE_LIST_DATETIME = list[datetime]
# FIELD_TYPE_LIST_TIME = list[time]
# FIELD_TYPE_LIST_JSON = list[dict]

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


class DatabaseMIA:
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
        self,
        collection_name,
        primary_key,
        visibility,
        origin,
        unit,
        default_value,
    ):
        """Add a new collection to the storage database, if it does not
        already exist.

        This method overrides the default behavior to add a collection with
        additional field attributes, ensuring proper schema updates and
        collection initialization.

        Parameters:
            collection_name (str): The name of the new collection.
            primary_key (str): The primary key column for the collection.
            visibility (bool): Visibility of the primary key field.
            origin (str): Origin of the primary key field.
            unit (str): Unit of the primary key field.
            default_value (Any): Default value for the primary key field.
        """
        self.add_field_attributes_collection()

        if self.has_collection(collection_name):
            return

        with self.storage.schema() as schema:
            schema.add_collection(collection_name, primary_key)

        self.update_field_att_col(
            collection_name=collection_name,
            field_name=primary_key,
            visibility=visibility,
            origin=origin,
            unit=unit,
            default_value=default_value,
            description=f"Primary_key of the document "
            f"collection {collection_name}",
            field_type=FIELD_TYPE_STRING,
        )

    def collection_names(self):
        """Retrieve the names of all collections in the storage database."""
        with self.storage.data() as dbs:
            return dbs.collection_names()

    def has_collection(self, collection_name):
        """Checks if a collection with the specified name exists
        in the database.

        Parameters:
        - collection_name (str): The name of the collection to check.

        Returns:
        - bool: `True` if the collection exists, otherwise `False`.

        """
        with self.storage.data() as dbs:
            return dbs.has_collection(collection_name)

    def get_fields_names(self, collection):
        """Retrieve the list of all field names in the specified collection.

        Args:
        collection (str): The name of the collection to retrieve field names
                          from. The collection must exist in the database.

        Returns:
            list: A list of all field names in the collection if it exists.
            None: If the collection has no fields or does not exist.
        """
        with self.storage.data() as dbs:
            fields_names = list(dbs[collection].keys())
            return fields_names if fields_names else None

    def add_field(
        self,
        collection_name,
        field_name,
        field_type,
        description,
        visibility,
        origin,
        unit,
        default_value,
        index=False,
    ):
        """Add a field to the database, if it does not already exist.

        :param collection_name: field collection (str)
        :param field_name: field name (str)
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
        """
        with self.storage.schema() as schema:
            schema.add_field(collection_name, field_name, field_type)

        self.update_field_att_col(
            collection_name=collection_name,
            field_name=field_name,
            visibility=visibility,
            origin=origin,
            unit=unit,
            default_value=default_value,
            description=description,
            field_type=field_type,
        )

    def add_fields(self, fields):
        """
        Adds a list of fields to the collection.

        Each field should be a dictionary containing the following keys:
        - collection_name: The collection to which the field belongs.
        - field_name: The name of the field.
        - field_type: The data type of the field.
        - description: A brief description of the field.
        - visibility: The visibility status of the field.
        - origin: The origin of the field.
        - unit: The unit associated with the field.
        - default_value: The default value of the field.
        - index:

        :param fields: List of dictionaries, each representing a
                       field's attributes.
        """
        for field in fields:
            self.add_field(**field)

    def get_field_attrib(self, collection_name, field_name=None):
        """
        Retrieve attributes of a specific field or all fields in a collection
        from the storage.

        Args:
            collection_name (str): The name of the collection.
            field_name (str, optional): The name of a specific field within
            the collection. If not provided, attributes for all fields in the
            collection will be retrieved.

        Returns:
            dict or list of dict: Attributes of the specified field as a
            dictionary, or a list of dictionaries with attributes for all
            fields if `field_name` is not provided.
        """
        with self.storage.data() as dbs:

            if field_name:
                attributes = dbs[FIELD_ATTRIBUTES_COLLECTION][
                    f"{collection_name}|{field_name}"
                ].get()

                if attributes is not None:
                    attributes["field_type"] = str_to_type(
                        attributes["field_type"]
                    )

                return attributes

            attributes_list = []

            for field in self.get_fields_names(collection_name):
                attributes = dbs[FIELD_ATTRIBUTES_COLLECTION][
                    f"{collection_name}|{field}"
                ].get()

            if attributes is not None:
                attributes["field_type"] = str_to_type(
                    attributes["field_type"]
                )
                attributes_list.append(attributes)

        return attributes_list

    def get_field(self, collection_name, field_name):
        """blabla"""

        # print("#########")
        # print(
        #     "Please note that the get_field() function is obsolete. "
        #     "Use get_field_attrib instead ......!"
        # )
        # print("#########")
        # return None
        raise NotImplementedError(
            "This method (get_field) is not yet available in "
            "DatabaseMIA class."
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
            "This method (get_fields) is not yet available in "
            "DatabaseMIA class."
        )

    def add_value(self, collection_name, primary_key, field, value):
        """Adds a value for <collection, document_id, field>"""
        with self.storage.data(write=True) as dbs:
            dbs[collection_name][primary_key][field] = value

    def add_values(self, collection_name, primary_key, values_dict):
        """Store or update a record in the specified collection.

        Args:
        collection_name (str): The name of the collection where the record
                               will be stored.
        primary_key (str): The unique key used to identify the record.
        values_dict (dict): A dictionary containing the data to store
                            or update.
        """
        with self.storage.data(write=True) as dbs:
            dbs[collection_name][primary_key] = values_dict

    def get_value(self, collection, primary_key, field):
        """
        Retrieves the current value of a specific field in a document from
        the specified collection.

        This method accesses the underlying storage to fetch the value of a
        given field within a document, identified by its primary key, in the
        specified collection.

        :param collection: The name of the collection containing the document.
        :type collection: str
        :param primary_key: The unique identifier (primary key) of the
                            document.
        :type primary_key: str
        :param field: The name of the field within the document to retrieve.
        :type field: str
        :return: The current value of the specified field.
        :rtype: Any
        """
        with self.storage.data() as dbs:
            return dbs[collection][primary_key][field].get()

    def filter_documents(
        self, collection, filter_query, fields=None, as_list=False
    ):
        """
        Iterates over the collection documents selected by filter_query

        Each item yield is a row of the collection table returned

        filter_query can be the result of self.filter_query() or a string
        containing a filter (in this case self.filter_query() is called to
        get the actual query)

        :param collection: Filter collection (str, must be existing)
        :param filter_query: Filter query (str)

            - A filter row must be written this way:
              {<field>} <operator> "<value>"
            - The operator must be in
              ('==', '!=', '<=', '>=', '<', '>', 'IN', 'ILIKE', 'LIKE')
            - The filter rows can be linked with ' AND ' or ' OR '
            - Example:
              "((({BandWidth} == "50000")) AND (({FileName} LIKE "%G1%")))"
        """

        if not self.has_collection(collection):
            raise ValueError(
                "The collection {0} does not exist".format(collection)
            )

        with self.storage.data() as dbs:
            for i in dbs[collection].search(filter_query):
                yield i

    def get_document(self, collection, document_id):
        """
        Retrieves a document from the specified collection using its
        identifier.

        :param collection: Name of the document collection (str).
                           Must exist.
        :param document_id: Identifier of the document to
                            retrieve (str or int).

        :return: The document instance if found, otherwise None.
        """
        if not self.has_collection(collection):
            return None

        with self.storage.data() as dbs:
            return dbs[collection][document_id].get()

    def get_documents(self, collection):
        """
        Retrieves all document rows from the specified collection.

        This method yields each document row in the collection if the
        collection exists. If the collection does not exist, an empty
        generator is returned.

        :param collection: Name of the document collection (str).
                           Must be an existing collection.

        :return: An iterator over the document rows, or an empty generator
                 if the collection does not exist or the collection has no
                 document.
        """
        if self.has_collection(collection):

            with self.storage.data() as dbs:
                yield from dbs[collection].get()

        else:
            yield from iter(())

    def get_document_names(self, collection):
        """Retrieve a list of all document names in the specified collection.

        Args:
            collection (str): The name of the collection to retrieve document
                              names from. The collection must already exist.

        Returns:
            list[str]: A list of document names if the collection exists,
                       otherwise an empty list.
        """
        if self.has_collection(collection):

            primary_key = self.primary_key(collection)

            with self.storage.data() as dbs:
                return [item[primary_key] for item in dbs[collection].get()]

        return []

    def primary_key(self, collection):
        """Retrieve the primary key of the specified collection.

        This method returns the first key from the specified collection within
        the database.

        Args:
            collection (str): The name of the collection to retrieve the
                              primary key from.

        Returns:
            str: The first key in the collection, representing the primary key.
        """
        with self.storage.data() as dbs:
            return next(iter(dbs[collection].keys()))

    def add_field_attributes_collection(self):
        """Ensures that the `FIELD_ATTRIBUTES_COLLECTION` is available in
        the database.

        If it does not exist, it creates the collection and adds specific
        fields to it such as 'visibility', 'origin', 'unit', and
        'default_value'.
        """
        has_collection = self.has_collection(FIELD_ATTRIBUTES_COLLECTION)

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
                    "Visibility of the index field in the DataBrowser",
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
                schema.add_field(
                    FIELD_ATTRIBUTES_COLLECTION,
                    "description",
                    str,
                    "Description of the index field",
                )
                schema.add_field(
                    FIELD_ATTRIBUTES_COLLECTION,
                    "field_type",
                    str,
                    "Type of the index field",
                )

    def update_field_att_col(
        self,
        collection_name,
        field_name,
        visibility,
        origin,
        unit,
        default_value,
        description,
        field_type,
    ):
        """Updates the attributes of a field in the database for a specific
        collection.

        This method constructs an index using the provided collection and
        field_name ('collection|field_name'), and then updates the field's
        attributes in the FIELD_ATTRIBUTES_COLLECTION.

        Parameters:
            collection_name (str): The name of the collection the field
                                   belongs to.
            field_name (str): The name of the field to update.
            visibility (bool): The visibility status of the field.
            origin (str): The origin or source of the field.
            unit (str): The unit of measurement for the field.
            default_value (Any): The default value to assign to the field.
            description (str): The description of the field.
            field_type: The type of the field.
        """

        index = f"{collection_name}|{field_name}"
        self.add_values(
            FIELD_ATTRIBUTES_COLLECTION,
            index,
            {
                "visibility": visibility,
                "origin": origin,
                "unit": unit,
                "default_value": default_value,
                "description": description,
                "field_type": type_to_str(field_type),
            },
        )

    def get_shown_tags(self):
        """Give the list of visible tags.

        :return: the list of visible tags
        """
        visible_names = []
        names_set = set()

        for i in self.filter_documents(
            FIELD_ATTRIBUTES_COLLECTION, "{visibility} == true"
        ):

            if i:
                # TODO: the first key in the dict is the primary key ?
                tag = i[next(iter(i))]
                tag = tag.split("|")[1]

                if tag not in names_set:
                    names_set.add(tag)
                    visible_names.append(tag)

        return visible_names

    def set_shown_tags(self, fields_shown):
        """Set the list of visible tags.

        :param fields_shown: list of visible tags
        """

        doc_names = self.get_document_names(FIELD_ATTRIBUTES_COLLECTION)

        with self.storage.data(write=True) as dbs:

            for doc_name in doc_names:
                collection, field = doc_name.split("|")

                if collection == "current":
                    dbs[FIELD_ATTRIBUTES_COLLECTION][doc_name][
                        "visibility"
                    ] = (field in fields_shown)

    def get_collection(self, name):
        """Returns the collection row of the collection"""
        raise NotImplementedError(
            "This method (get_collection) is not yet available in "
            "DatabaseMIA class."
        )

    def get_collections(self):
        """Gives the list of all collection rows."""
        raise NotImplementedError(
            "This method (get_collections) is not yet available in "
            "DatabaseMIA class."
        )

    def remove_collection(self, name):
        """Removes a collection."""
        raise NotImplementedError(
            "This method (remove_collection) is not yet available in "
            "DatabaseMIA class."
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

    def set_value(self, collection, document_id, field, new_value):
        """Sets the value associated to <collection, document, field> if
        it exists.
        """
        raise NotImplementedError(
            "This method (set_value) is not yet available in "
            "DatabaseMIA class."
        )

    def remove_value(self, collection, document_id, field):
        """Removes the value <collection, document, field> if it exists."""
        raise NotImplementedError(
            "This method (remove_value) is not yet available in "
            "DatabaseMIA class."
        )

    def add_document(self, collection, document, create_missing_fields=True):
        """Adds a document to a collection."""
        raise NotImplementedError(
            "This method (add_document) is not yet available in "
            "DatabaseMIA class."
        )

    def remove_document(self, collection, document_id):
        """Removes a document in the collection."""
        raise NotImplementedError(
            "This method (remove_document) is not yet available in "
            "DatabaseMIA class."
        )
