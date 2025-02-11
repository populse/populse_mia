"""
Module containing a class that provides tools adapted to Mia for
interacting with the populse_db API.

:Contains:
   Class:
      - DatabaseMIA
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

from contextlib import contextmanager

from populse_db.database import str_to_type, type_to_str

# Populse_db imports
from populse_db.storage import Storage

# Special attributes for the database
from populse_mia.data_manager import (
    FIELD_ATTRIBUTES_COLLECTION,
    FIELD_TYPE_STRING,
)

# Shema (not in use currently)
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
    Class providing tools for interacting with a database,
    under the supervision of populse_db.

    .. Methods:
        - add_collection: add a new collection to the database.
        - get_collection_names: retrieve the names of all collections
                                in the database.
        - has_collection: checks if a collection exists in the database.
        - get_field_names: retrieve the list of all field names in the
                           specified collection.
        - add_field: adds one or more fields to a collection.
        - remove_field:  removes a field in a collection.
        - add_field_attributes_collection: ensures that the
                                           `FIELD_ATTRIBUTES_COLLECTION`
                                           collection is available in the
                                           database (for internal
                                           operation of populse_mia
                                           and associated fields).
        - remove_field_attributes: remove attributes associated with a
                                   specific field in a collection.
        - update_field_attributes: updates the attributes of a field in
                                   the database.
        - get_field_attributes: retrieve attributes of a specific field or
                                all fields in a collection.
        - set_value: store or update a record in the specified collection.
        - get_value: retrieves the current value of a specific field.
        - remove_value: removes the value for a field.
        - add_document: adds a document in a collection.
        - has_document: checks if a document exists in a collection.
        - filter_documents: retrieve documents from a specified collection
                            that match a given filter.
        - get_document: Retrieve documents from a specified collection with
                         optional filtering.
        - get_document_names: retrieve a list of all document names in the
                              specified collection.
        - remove_document: remove a document from a specified collection.
        - get_primary_key_name: retrieve the primary key of the specified
                                collection.
        - get_shown_tags: give the list of visible tags.
        - set_shown_tags: set the list of visible tags.

    """

    def __init__(
        self,
        database_engine,
        # schema_name="populse_mia.data_manager.database_mia",
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

    @contextmanager
    def schema(self):
        with self.storage.schema() as schema:
            yield DatabaseMIASchema(schema)
    
    @contextmanager
    def data(self, write=None, create=None):
        with self.storage.data(write=write, create=create) as data:
            yield DatabaseMIAData(data)


class DatabaseMIASchema:
    def __init__(self, storage_schema):
        self.storage_schema = storage_schema
    
    @contextmanager
    def data(self):
        with self.storage_schema.data() as storage_data:
            yield DatabaseMIAData(storage_data)
    
    # -- Collections management --

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

        :param collection_name (str): The name of the new collection.
        :param primary_key (str): The primary key column for the collection.
        :param visibility (bool): Visibility of the primary key field.
        :param origin (str): Origin of the primary key field.
        :param unit (str): Unit of the primary key field.
        :param default_value (Any): Default value for the primary key field.
        """
        self.add_field_attributes_collection()

        with self.storage_schema.data() as storage_data:
            if storage_data.has_collection(collection_name):
                return

        self.storage_schema.add_collection(collection_name, primary_key)

        self.update_field_attributes(
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

    def add_field(self, fields):
        """
        Adds one or more fields to the collection.

        Each field should be represented as a dictionary containing
        the following keys:

        - `collection_name` (str): The collection to which the field belongs.
        - `field_name` (str): The name of the field.
        - `field_type` (str): The data type of the field.
        - `description` (str): A brief description of the field.
        - `visibility` (bool): The visibility status of the field.
        - `origin` (str): The origin of the field.
        - `unit` (str): The unit associated with the field.
        - `default_value` (Any): The default value of the field.

        :param fields (dict | list[dict]): A dictionary representing a single
                                           field's attributes, or a list of
                                           dictionaries representing multiple
                                           fields' attributes.
        """

        # Ensure fields is always a list for consistent processing
        if isinstance(fields, dict):
            fields = [fields]

        for field in fields:

            self.storage_schema.add_field(
                collection_name=field["collection_name"],
                field_name=field["field_name"],
                field_type=field["field_type"],
            )

            self.update_field_attributes(
                collection_name=field["collection_name"],
                field_name=field["field_name"],
                visibility=field["visibility"],
                origin=field["origin"],
                unit=field["unit"],
                default_value=field["default_value"],
                description=field["description"],
                field_type=field["field_type"],
            )

    def remove_field(self, collection_name, field_name):
        """
        Removes a specified field in the collection_name

        This method updates the schema to remove the specified field from the
        collection and handles associated attributes cleanup.

        :param collection_name (str): The name of the collection from which
                                      the field will be removed (must exist).
        :param field_name (str): The name of the field to remove (must exist).
        :raises ValueError: If the `collection_name` does not exist or if
                            the `field_name` does not exist.
        """
        try:
            self.storage_schema.remove_field(collection_name, field_name)

        except KeyError as e:
            raise ValueError(
                f"Error removing field '{field_name}' from "
                f"collection '{collection_name}': {e}"
            )

        self.remove_field_attributes(collection_name, field_name)

    # -- field attributes management --
    def add_field_attributes_collection(self):
        """Ensures that the `FIELD_ATTRIBUTES_COLLECTION` is available in
        the database.

        If it does not exist, it creates the collection and adds specific
        fields to it such as 'visibility', 'origin', 'unit', and
        'default_value'.
        """
        with self.storage_schema.data() as storage_data:
            has_collection = storage_data.has_collection(FIELD_ATTRIBUTES_COLLECTION)

        if not has_collection:

            self.storage_schema.add_collection(
                name=FIELD_ATTRIBUTES_COLLECTION,
                primary_key="index",
                # description="The primary key name of the "
                #             "collection as: "
                #             "collection name|collection primary_key "
                #             "column name"
            )
            self.storage_schema.add_field(
                collection_name=FIELD_ATTRIBUTES_COLLECTION,
                field_name="visibility",
                field_type=bool,
                description="Visibility of the index field in "
                "the DataBrowser",
            )
            self.storage_schema.add_field(
                collection_name=FIELD_ATTRIBUTES_COLLECTION,
                field_name="origin",
                field_type=str,
                description="Define the origin of the index "
                "field, TAG_ORIGIN_BUILTIN or "
                "TAG_ORIGIN_USER",
            )
            self.storage_schema.add_field(
                collection_name=FIELD_ATTRIBUTES_COLLECTION,
                field_name="unit",
                field_type=str,
                description="Unit of the index field",
            )
            self.storage_schema.add_field(
                collection_name=FIELD_ATTRIBUTES_COLLECTION,
                field_name="default_value",
                field_type=str,
                description="Default value of the index field",
            )
            self.storage_schema.add_field(
                collection_name=FIELD_ATTRIBUTES_COLLECTION,
                field_name="description",
                field_type=str,
                description="Description of the index field",
            )
            self.storage_schema.add_field(
                collection_name=FIELD_ATTRIBUTES_COLLECTION,
                field_name="field_type",
                field_type=str,
                description="Type of the index field",
            )

    def remove_field_attributes(self, collection_name, field_name):
        """
        Remove attributes associated with a specific field in a collection.

        This method deletes the document storing metadata or attributes for
        the specified field in the given collection.

        :param collection_name (str): The name of the collection containing
                                      the field.
        :param field_name (str): The name of the field whose attributes are
                                 to be removed.
        :raises ValueError: If the attributes document does not exist or
                            cannot be removed.
        """
        index = f"{collection_name}|{field_name}"

        try:
            with self.data() as mia_data:
                mia_data.remove_document(FIELD_ATTRIBUTES_COLLECTION, index)

        except KeyError as e:
            raise ValueError(
                f"Failed to remove attributes for "
                f"field '{field_name}' in "
                f"collection '{collection_name}': {e}"
            )

    def update_field_attributes(
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

        :param collection_name (str): The name of the collection the field
                                      belongs to.
        :param field_name (str): The name of the field to update.
        :param visibility (bool): The visibility status of the field.
        :param origin (str): The origin or source of the field.
        :param unit (str): The unit of measurement for the field.
        :param default_value (Any): The default value to assign to the field.
        :param description (str): The description of the field.
        :param field_type (Any): The type of the field.
        """

        index = f"{collection_name}|{field_name}"
        with self.data() as mia_data:
            mia_data.set_value(
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

class DatabaseMIAData:
    def __init__(self, storage_data):
        self.storage_data = storage_data

    def has_collection(self, collection_name):
        """
         Checks if a collection with the specified name exists in the database.

        :param collection_name (str): The name of the collection to check.
        :returns (bool): `True` if the collection exists, otherwise `False`.
        """
        return self.storage_data.has_collection(collection_name)

    # -- Fields / tags management --

    def get_field_names(self, collection_name):
        """
        Retrieve the list of all field names in the specified collection.

        :param collection_name (str): The name of the collection to retrieve
                                      field names from. The collection must
                                      exist in the database.
        :returns (list | None): A list of all field names in the collection
                                if it exists, or `None` if the collection has
                                no fields or does not exist.
        """
        field_names = list(self.storage_data[collection_name].keys())
        return field_names if field_names else None



    def get_field_attributes(self, collection_name, field_name=None):
        """
        Retrieve attributes of a specific field or all fields in a collection
        from the storage.

        :param collection_name (str): The name of the collection.
        :param field_name (str, optional): The name of a specific field within
                                           the collection. If not provided,
                                           attributes for all fields in the
                                           collection will be retrieved.
        :returns (dict | list[dict]): Attributes of the specified field as a
                                      dictionary, or a list of dictionaries
                                      with attributes for all fields if
                                      `field_name` is not provided.
        """
        if field_name:
            attributes = self.storage_data[FIELD_ATTRIBUTES_COLLECTION][
                f"{collection_name}|{field_name}"
            ].get()

            if attributes is not None:
                attributes["field_type"] = str_to_type(
                    attributes["field_type"]
                )

            return attributes

        elif field_name is None:
            attributes_list = []

            for field_name in self.get_field_names(collection_name):
                attributes = self.storage_data[FIELD_ATTRIBUTES_COLLECTION][
                    f"{collection_name}|{field_name}"
                ].get()

                if attributes is not None:
                    attributes["field_type"] = str_to_type(
                        attributes["field_type"]
                    )
                    attributes_list.append(attributes)

            return attributes_list

        else:
            return None

    # -- Values management --

    def set_value(self, collection_name, primary_key, values_dict):
        """
        Store or update a record in the specified collection.

        This method either stores a new record or updates an existing record
        in the specified collection, using the provided primary key. The
        fields of the record are set according to the data in the provided
        dictionary.

        :param collection_name (str): The name of the collection where the
                                      record will be stored or updated.
        :param primary_key (str): The unique key used to identify the record.
        :param values_dict (dict): A dictionary containing the data to store
                                   or update in the record. Keys represent
                                   field names, and values represent the
                                   corresponding data.
        """

        existing_record = self.storage_data[collection_name][primary_key].get() or {}

        # Preserve non-null values from the existing record and update with
        # new values
        filtered_record = {
            k: v for k, v in existing_record.items() if v is not None
        }
        updated_record = {**filtered_record, **values_dict}

        self.storage_data[collection_name][primary_key] = updated_record

    def get_value(self, collection_name, primary_key, field):
        """
        Retrieves the current value of a specific field in a document from
        the specified collection.

        This method accesses the underlying storage to fetch the value of a
        given field within a document, identified by its primary key, in the
        specified collection.

        :param collection_name (str): The name of the collection containing
                                      the document.
        :param primary_key (str): The unique identifier (primary key) of the
                                  document.
        :param field (str): The name of the field within the document to
                            retrieve.
        :returns (Any): The current value of the specified field.
        """
        return self.storage_data[collection_name][primary_key][field].get()

    def remove_value(self, collection_name, primary_key, field):
        """
        Removes the specified field from a document in the given collection,
        if it exists. Raises a KeyError if the field, collection, or document
        is not found.

        :param collection_name (str): The name of the collection containing
                                      the document.
        :param primary_key (str): The primary key of the document in the
                                  collection.
        :param field (str): The field to be removed from the document.
        :raises KeyError: If the collection or document cannot be found.
        """

        try:

            del self.storage_data[collection_name][primary_key][field]

        except Exception as e:
            raise KeyError(
                f"Failed to remove the '{field}' for "
                f"document ID '{primary_key}' in "
                f"collection '{collection_name}': {e}"
            ) from e

    # -- Documents management --

    def add_document(self, collection_name, document):
        """
        Adds a document to a specified collection in the storage.

        If the specified collection exists, the document is added to it.
        The method assigns a primary key to the document based on the
        collection's primary key configuration. The changes are saved
        to the storage.

        :param collection_name (str): The name of the collection where the
                                      document should be added.
        :param document (str): The document name to be added.
        """

        if self.has_collection(collection_name):
            primary_key = self.get_primary_key_name(collection_name)

            self.storage_data[collection_name][document] = {primary_key: document}

    def has_document(self, collection_name, primary_key):
        """
        Checks if a document with the specified primary key exists in the
        given collection.

        :param collection_name (str): The name of the collection.
        :param primary_key (str): The primary key of the document to check.
        :returns (bool): `True` if the document exists, `False` otherwise.
        """

        if not self.has_collection(collection_name):
            return False

        return primary_key in self.storage_data[collection_name].get()

    def filter_documents(self, collection_name, filter_query):
        """
        Retrieve documents from a specified collection that match a given
        filter.

        This method searches for documents in the specified collection based
        on the provided filter query. It returns the results as a list of
        rows from the collection table.

        The `filter_query` can either be:
            - The result of `self.filter_query()`.
            - A string defining a filter.

        **Filter Query Format:**
            - A filter condition must follow this syntax:
                `{<field>} <operator> "<value>"`.
            - Supported operators:
                `==`, `!=`, `<=`, `>=`, `<`, `>`, `IN`, `ILIKE`, `LIKE`.
            - Multiple filter conditions can be combined using `AND` or `OR`.
            - Example:
                ```
                "((({BandWidth} == "50000")) AND (({FileName} LIKE "%G1%")))"
                ```

        **Note:**
        Due to potential database access issues such as
        `"database already open."`, this implementation currently returns a
        list instead of using `yield`. However, using `yield` may be
        reconsidered in the future for better memory management.

        :param collection_name (str): The name of the collection to filter
                                      (must exist).
        :param filter_query (str): The filter query to apply.
        :returns (list): A list of rows matching the filter criteria.
        """

        if not self.has_collection(collection_name):
            raise ValueError(
                f"The collection {collection_name} does not exist..."
            )

        # with self.storage.data() as dbs:
        #     for i in dbs[collection_name].search(filter_query):
        #         yield i
        # TODO: We do not use yield because it causes errors such as
        #       "database already open." I believe the code should be
        #       improved to prevent this exception. For now, to save time,
        #       we are not exploring the use of yield. However, it will
        #       likely need to be implemented later for memory
        #       management reasons.
        return self.storage_data[collection_name].search(filter_query)

    def get_document(self, collection_name, primary_keys=None, fields=None):
        """
        Retrieve documents from the specified collection with optional
        filtering.

        This method checks if the specified collection exists. If it does, it
        retrieves documents from the collection, optionally filtering by
        primary keys and selecting specific fields. If the collection does not
        exist, an empty list is returned.

        :param collection_name (str): Name of the document collection. The
                                      collection must already exist in the
                                      database.
        :param primary_keys (str | list[str], optional): A single primary key
                                                         or a list of primary
                                                         keys to filter
                                                         documents. If None,
                                                         no filtering by
                                                         primary keys is
                                                         applied.
        :param fields (str | list[str], optional): A single field or a list of
                                                   fields to include in the
                                                   result. If None, all fields
                                                   are included.
        :returns (list): A list of documents matching the specified criteria,
                         or an empty list if the collection does not exist.
        """

        if not self.has_collection(collection_name):
            return []

        documents = self.storage_data[collection_name].get()

        # Filter by primary keys if provided
        if primary_keys:
            primary_key_field = self.get_primary_key_name(collection_name)
            primary_keys = (
                set(primary_keys)
                if isinstance(primary_keys, list)
                else {primary_keys}
            )
            documents = [
                doc
                for doc in documents
                if doc.get(primary_key_field) in primary_keys
            ]

        # Select specific fields if provided
        if fields:
            fields = set(fields) if isinstance(fields, list) else {fields}
            documents = [
                {field: doc.get(field) for field in fields}
                for doc in documents
            ]

        return documents

    def get_document_names(self, collection_name):
        """
        Retrieve a list of all document names in the specified collection.

        :param collection_name (str): The name of the collection to retrieve
                                      document names from. The collection must
                                      already exist.
        :returns (list[str]): A list of document names if the collection
                              exists, otherwise an empty list.
        """
        if self.has_collection(collection_name):
            primary_key = self.get_primary_key_name(collection_name)

            return [
                item[primary_key] for item in self.storage_data[collection_name].get()
            ]

        return []

    def remove_document(self, collection_name, primary_key):
        """
        Remove a document from a specified collection.

        This method deletes the document identified by `primary_key` from
        the given collection in the storage.

        :param collection_name (str): The name of the collection containing
                                      the document.
        :param primary_key (str): The unique identifier of the document to be
                                  removed.
        :raises KeyError: If the collection or the document does not exist.
        """
        try:

            del self.storage_data[collection_name][primary_key]

        except Exception as e:
            raise KeyError(
                f"Failed to remove document with "
                f"ID '{primary_key}' from "
                f"collection '{collection_name}': {e}"
            )

    # -- Utility --

    def get_primary_key_name(self, collection_name):
        """
        Retrieve the primary key of the specified collection.

        This method returns the first key from the specified collection within
        the database.

        :param collection_name (str): The name of the collection to retrieve
                                      the primary key from.
        :returns (str): The first key in the collection, representing the
                        primary key.
        """
        return self.storage_data[collection_name].primary_key()[0]

    def get_shown_tags(self):
        """
        Give the list of visible tags.

        :returns (list): The list of visible tags.
        """
        visible_names = []
        names_set = set()

        for i in self.filter_documents(
            FIELD_ATTRIBUTES_COLLECTION, "{visibility} == true"
        ):

            if i:
                # TODO: The first key in the dict is the primary key ?
                #       Another safer solution would be to use the "index"
                #       key. Indeed, we know that it is the primary key for
                #       the collection FIELD_ATTRIBUTES_COLLECTION.
                tag = i[next(iter(i))]
                tag = tag.split("|")[1]

                if tag not in names_set:
                    names_set.add(tag)
                    visible_names.append(tag)

        return visible_names

    def set_shown_tags(self, fields_shown):
        """
        Set the list of visible tags.

        :param fields_shown (list): A list of visible tags.
        """

        doc_names = self.get_document_names(FIELD_ATTRIBUTES_COLLECTION)

        for doc_name in doc_names:
            collection, field = doc_name.split("|")

            if collection == "current":
                self.storage_data[FIELD_ATTRIBUTES_COLLECTION][doc_name][
                    "visibility"
                ] = (field in fields_shown)

    # -- Currently obsoletes --

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

    def get_collection_names(self):
        """Retrieve the names of all collections in the storage database."""
        # with self.storage.data() as dbs:
        #     return dbs.collection_names()
        raise NotImplementedError(
            "This method (get_collection_names) is not yet available in "
            "DatabaseMIA class."
        )
