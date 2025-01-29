# -*- coding: utf-8 -*-
"""Module that contains class to override the default behaviour of
populse_db and some of its methods

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

# from datetime import datetime

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

    # -- Fields / tags management --

    def get_field_names(self, collection):
        """Retrieve the list of all field names in the specified collection.

        Args:
        collection (str): The name of the collection to retrieve field names
                          from. The collection must exist in the database.

        Returns:
            list: A list of all field names in the collection if it exists.
            None: If the collection has no fields or does not exist.
        """
        with self.storage.data() as dbs:
            field_names = list(dbs[collection].keys())
            return field_names if field_names else None

    def add_field(self, fields):
        """
        Adds one or more fields to the collection.

        Each field should be represented as a dictionary containing
        the following keys:
        - collection_name: The collection to which the field belongs.
        - field_name: The name of the field.
        - field_type: The data type of the field.
        - description: A brief description of the field.
        - visibility: The visibility status of the field.
        - origin: The origin of the field.
        - unit: The unit associated with the field.
        - default_value: The default value of the field.

        :param fields: A dictionary representing a single field's attributes,
                       or a list of dictionaries representing multiple
                       fields' attributes.
        """

        # Ensure fields is always a list for consistent processing
        if isinstance(fields, dict):
            fields = [fields]

        for field in fields:

            with self.storage.schema() as schema:
                schema.add_field(
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

        :param collection_name: The name of the collection from which the field
                                will be removed (str, must be existing).

        :param field_name: The name of the field to remove (str, must
                           be existing).

        :raise ValueError: - If the collection_name does not exist
                           - If the field_name does not exist
        """
        try:
            with self.storage.schema() as schema:
                schema.remove_field(collection_name, field_name)

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
        has_collection = self.has_collection(FIELD_ATTRIBUTES_COLLECTION)

        if not has_collection:

            with self.storage.schema() as schema:
                schema.add_collection(
                    name=FIELD_ATTRIBUTES_COLLECTION,
                    primary_key="index",
                    # description="The primary key name of the "
                    #             "collection as: "
                    #             "collection name|collection primary_key "
                    #             "column name"
                )
                schema.add_field(
                    collection_name=FIELD_ATTRIBUTES_COLLECTION,
                    field_name="visibility",
                    field_type=bool,
                    description="Visibility of the index field in "
                    "the DataBrowser",
                )
                schema.add_field(
                    collection_name=FIELD_ATTRIBUTES_COLLECTION,
                    field_name="origin",
                    field_type=str,
                    description="Define the origin of the index "
                    "field, TAG_ORIGIN_BUILTIN or "
                    "TAG_ORIGIN_USER",
                )
                schema.add_field(
                    collection_name=FIELD_ATTRIBUTES_COLLECTION,
                    field_name="unit",
                    field_type=str,
                    description="Unit of the index field",
                )
                schema.add_field(
                    collection_name=FIELD_ATTRIBUTES_COLLECTION,
                    field_name="default_value",
                    field_type=str,
                    description="Default value of the index field",
                )
                schema.add_field(
                    collection_name=FIELD_ATTRIBUTES_COLLECTION,
                    field_name="description",
                    field_type=str,
                    description="Description of the index field",
                )
                schema.add_field(
                    collection_name=FIELD_ATTRIBUTES_COLLECTION,
                    field_name="field_type",
                    field_type=str,
                    description="Type of the index field",
                )

    def remove_field_attributes(
        self,
        collection_name,
        field_name,
    ):
        """
        Remove attributes associated with a specific field in a collection.

        This method deletes the document storing metadata or attributes for
        the specified field in the given collection.

        Args:
            collection_name (str): The name of the collection containing
                                   the field.
            field_name (str): The name of the field whose attributes are
                              to be removed.

        Raises:
            ValueError: If the attributes document does not exist or cannot
                        be removed.
        """
        index = f"{collection_name}|{field_name}"

        try:
            self.remove_document(FIELD_ATTRIBUTES_COLLECTION, index)

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
        self.add_value(
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

    def get_field_attributes(self, collection_name, field_name=None):
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

            elif field_name is None:
                attributes_list = []

                for field_name in self.get_field_names(collection_name):
                    attributes = dbs[FIELD_ATTRIBUTES_COLLECTION][
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

    def add_value(self, collection_name, primary_key, values_dict):
        """
        Store or update a record in the specified collection.

        This method either stores a new record or updates an existing record
        in the specified collection, using the provided primary key. The
        fields of the record are set according to the data in the provided
        dictionary.

        Parameters:
            collection_name (str): The name of the collection where the record
                                   will be stored or updated.
            primary_key (str): The unique key used to identify the record.
            values_dict (dict): A dictionary containing the data to store or
                                update in the record. Keys represent field
                                names, and values represent the corresponding
                                data.
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

    def remove_value(self, collection_name, primary_key, field):
        """
        Removes the specified field from a document in the given collection,
        if it exists. Raises a KeyError if the field, collection, or document
        is not found.

        :param collection_name: The name of the collection containing
                                the document (str).
        :param primary_key: The primary key of the document in
                            the collection (str).
        :param field: The field to be removed from the document (str).

        :raises KeyError: If the collection or document cannot be found.
        """

        try:

            with self.storage.data(write=True) as dbs:
                del dbs[collection_name][primary_key][field]

        except Exception as e:
            raise KeyError(
                f"Failed to remove the '{field}' for "
                f"document ID '{primary_key}' in "
                f"collection '{collection_name}': {e}"
            ) from e

    # -- Documents management --

    def add_document(self, collection, document):
        """
        Adds a document to a specified collection in the storage.

        If the specified collection exists, the document is added to it.
        The method assigns a primary key to the document based on the
        collection's primary key configuration. The changes are saved
        to the storage.

        Parameters:
        ----------
        collection : str
                     The name of the collection where the document should
                     be added.
        document : str
                   The document name to be added.
        """

        if self.has_collection(collection):
            primary_key = self.primary_key(collection)

            with self.storage.data(write=True) as dbs:
                dbs[collection][document] = {primary_key: document}

    def has_document(self, collection_name, primary_key):
        """
        Checks if a document with the specified primary key exists in the
        given collection.

        Args:
            collection_name (str): The name of the collection.
            primary_key (str): The primary key of the document to check.

        Returns:
            bool: True if the document exists, False otherwise.
        """

        if not self.has_collection(collection_name):
            return False

        with self.storage.data() as dbs:
            return primary_key in dbs[collection_name].get()

    def filter_documents(self, collection, filter_query):
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

        # with self.storage.data() as dbs:
        #     for i in dbs[collection].search(filter_query):
        #         yield i
        # TODO: We do not use yield because it causes errors such as
        #       "database already open." I believe the code should be
        #       improved to prevent this exception. For now, to save time,
        #       we are not exploring the use of yield. However, it will
        #       likely need to be implemented later for memory
        #       management reasons.
        with self.storage.data() as dbs:
            return dbs[collection].search(filter_query)

    # def get_document(self, collection, document_id):
    #     """
    #     Retrieves a document from the specified collection using its
    #     identifier.

    #     :param collection: Name of the document collection (str).
    #                        Must exist.
    #     :param document_id: Identifier of the document to
    #                         retrieve (str or int).

    #     :return: The document instance if found, otherwise None.
    #     """
    #     if not self.has_collection(collection):
    #         return None

    #     with self.storage.data() as dbs:
    #         return dbs[collection][document_id].get()

    def get_document(self, collection_name, primary_keys=None, fields=None):
        """
        Retrieve documents from the specified collection with optional
        filtering.

        This method checks if the specified collection exists. If it does, it
        retrieves documents from the collection, optionally filtering by
        primary keys and selecting specific fields. If the collection does not
        exist, an empty list is returned.

        :param collection_name: Name of the document collection (str). The
                                collection must already exist in the database.
        :param primary_keys: A single primary key or a list of primary keys to
                             filter documents (str or list of str). If None,
                             no filtering by primary keys is applied.
        :param fields: A single field or a list of fields to include in the
                       result (str or list of str). If None, all fields are
                       included.

        :return: A list of documents matching the specified criteria, or an
                 empty list if the collection does not exist.
        """

        if not self.has_collection(collection_name):
            return []

        with self.storage.data() as dbs:
            documents = dbs[collection_name].get()

        # Filter by primary keys if provided
        if primary_keys:
            primary_key_field = self.primary_key(collection_name)
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

    def remove_document(self, collection_name, primary_key):
        """
        Remove a document from a specified collection.

        This method deletes the document identified by `primary_key` from
        the given collection in the storage.

        Args:
            collection_name (str): The name of the collection
                                   containing the document.
            primary_key (str): The unique identifier of the document to
                               be removed.

        Raises:
            KeyError: If the collection or the document does not exist.
        """
        try:

            with self.storage.data(write=True) as dbs:
                del dbs[collection_name][primary_key]

        except Exception as e:
            raise KeyError(
                f"Failed to remove document with "
                f"ID '{primary_key}' from "
                f"collection '{collection_name}': {e}"
            )

    # -- Utility --

    def primary_key(self, collection):
        """Retrieve the primary key of the specified collection.

        This method returns the first key from the specified collection within
        the database.

        Args:
            collection (str): The name of the collection to retrieve the
                              primary key from.

        Returns:
            str: The first key in the collection, representing the primary
                 key.
        """
        with self.storage.data() as dbs:
            # TODO: Are we sure that the primary key is ALWAYS the first
            #       element in the dbs[collection].keys() dict_keys list?
            return next(iter(dbs[collection].keys()))

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

    # -- Currently obsoletes --

    def get_field(self, collection_name, field_name):
        """blabla"""

        raise NotImplementedError(
            "This method (get_field) is obsolete and is no longer "
            "available in the DatabaseMIA class. Use get_field_attributes "
            " instead ......!"
        )

    def set_value(self, collection, document_id, field, new_value):
        """Sets the value associated to <collection, document, field> if
        it exists.
        """
        raise NotImplementedError(
            "This method (set_value) is obsolete and is no longer "
            "available in the DatabaseMIA class. Use add_value "
            " instead ......!"
        )

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
