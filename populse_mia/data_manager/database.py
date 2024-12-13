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
        with self.storage.data() as dbs:
            dbs[collection_name][primary_key] = values_dict
