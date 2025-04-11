"""
Rapid Search Widget Module

This module provides the RapidSearch widget, a specialized QLineEdit
component for performing quick searches across visualized tags in the
data browser table.

The RapidSearch widget enables users to filter DataBrowser using various
search patterns and wildcards. It supports searching for specific text
patterns as well as finding entries with undefined or missing values.

Contains:
    Class:
        - RapidSearch
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# PyQt5 import
from PyQt5.QtWidgets import QLineEdit

# Populse_MIA imports
from populse_mia.data_manager import TAG_BRICKS, TAG_FILENAME


class RapidSearch(QLineEdit):
    """
    Widget for pattern searching in table data across visualized tags.

    Supports special search syntax:
    - '%': Wildcard for any string
    - '_': Wildcard for any single character
    - '*Not Defined*': Matches scans with missing values

    Dates should be formatted as: yyyy-mm-dd hh:mm:ss.fff

    .. Methods:
        - prepare_filter: Prepares the rapid search filter
        - prepare_not_defined_filter: Prepares the rapid search filter for
                                      not defined values
    """

    def __init__(self, databrowser):
        """
        Initialize the RapidSearch widget.

        :param databrowser: Parent data browser widget
        """
        super().__init__()
        self.databrowser = databrowser
        self.setPlaceholderText(
            "Rapid search: % (any string), _ (any character), "
            "*Not Defined* (missing values), "
            "dates as yyyy-mm-dd hh:mm:ss.fff"
        )

    def prepare_not_defined_filter(self, tags):
        """
        Create a filter for finding entries with undefined values.

        :param tags (list): List of tags to check for null values

        :return (str): QL-like filter expression for finding null values
        """
        conditions = []

        for tag in tags:

            if tag != TAG_BRICKS:
                conditions.append(f"({{{tag}}} == null)")

        # Join all conditions with OR
        query = " OR ".join(conditions)
        # Add filename constraint
        scans_str = str(self.databrowser.table_data.scans_to_search).replace(
            "'", '"'
        )
        query = f"({query}) AND ({{{TAG_FILENAME}}} IN {scans_str})"
        return f"({query})"

    @staticmethod
    def prepare_filter(search, tags, scans):
        """
        Create a filter for searching text across specified tags.

        :param search (str): Search pattern to look for
        :param tags (list): List of tags to search within
        :param scans (list): List of scans to restrict the search to

        :return (str): SQL-like filter expression for the search
        """
        conditions = []

        for tag in tags:

            if tag != TAG_BRICKS:
                conditions.append(f'({{{tag}}} LIKE "%{search}%")')

        # Join all conditions with OR
        tag_query = " OR ".join(conditions)
        # Add filename constraint
        scans_str = str(scans).replace("'", '"')
        query = f"({tag_query}) AND ({{{TAG_FILENAME}}} IN {scans_str})"
        return query
