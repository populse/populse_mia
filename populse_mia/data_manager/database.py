# -*- coding: utf-8 -*-
"""blabla"""


class DatabaseEngine:
    """The base class for all engines allowing to store, retrieve and
    search metadata associated with a key that can be either a string
    or a path (i.e. a file or directory name).
    """

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

    def collection_names(self):
        """blabla"""
        with self.storage.data() as dbs:
            return dbs.collection_names()

    def add_values(self, collection_name, primary_key, values_dict):
        """blabla"""
        with self.storage.data(write=True) as dbs:
            dbs[collection_name][primary_key] = values_dict

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
