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

# Populse_db imports
from populse_db.database import (
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_STRING,
    Database,
    DatabaseSession,
)

TAG_ORIGIN_BUILTIN = "builtin"
TAG_ORIGIN_USER = "user"

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

FIELD_ATTRIBUTES_COLLECTION = "mia_field_attributes"


class DatabaseSessionMIA(DatabaseSession):
    """Class overriding the database session of populse_db

    .. Methods:
        - add_collection: overrides the method adding a collection
        - add_field: adds a field to the database, if it does not already exist
        - add_fields: adds the list of fields
        - get_shown_tags: gives the list of visible tags
        - set_shown_tags: sets the list of visible tags
    """

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
        super(DatabaseSessionMIA, self).add_collection(name, primary_key)
        self.add_document(
            FIELD_ATTRIBUTES_COLLECTION,
            {
                "index": "%s|%s" % (name, primary_key),
                "field": primary_key,
                "visibility": visibility,
                "origin": origin,
                "unit": unit,
                "default_value": default_value,
            },
        )

    def add_field_attributes_collection(self):
        """Blabla"""

        if not self.engine.has_collection(FIELD_ATTRIBUTES_COLLECTION):
            super(DatabaseSessionMIA, self).add_collection(
                FIELD_ATTRIBUTES_COLLECTION
            )
            super(DatabaseSessionMIA, self).add_field(
                FIELD_ATTRIBUTES_COLLECTION, "visibility", FIELD_TYPE_BOOLEAN
            )
            super(DatabaseSessionMIA, self).add_field(
                FIELD_ATTRIBUTES_COLLECTION, "origin", FIELD_TYPE_STRING
            )
            super(DatabaseSessionMIA, self).add_field(
                FIELD_ATTRIBUTES_COLLECTION, "unit", FIELD_TYPE_STRING
            )
            super(DatabaseSessionMIA, self).add_field(
                FIELD_ATTRIBUTES_COLLECTION, "default_value", FIELD_TYPE_STRING
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
        super(DatabaseSessionMIA, self).add_field(
            collection, name, field_type, description
        )
        self.add_document(
            FIELD_ATTRIBUTES_COLLECTION,
            {
                "index": "%s|%s" % (collection, name),
                "field": name,
                "visibility": visibility,
                "origin": origin,
                "unit": unit,
                "default_value": default_value,
            },
        )

    def add_fields(self, fields):
        """Add the list of fields.

        :param fields: list of fields (collection, name, type, description,
                       visibility, origin, unit, default_value)
        """

        for field in fields:
            # Adding each field
            self.add_field(
                field[0],
                field[1],
                field[2],
                field[3],
                field[4],
                field[5],
                field[6],
                field[7],
                False,
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
        super(DatabaseSessionMIA, self).remove_field(collection, fields)
        if isinstance(fields, str):
            fields = [fields]
        for field in fields:
            self.remove_document(
                FIELD_ATTRIBUTES_COLLECTION, "%s|%s" % (collection, field)
            )

    def get_field(self, collection, name):
        """Blabla"""

        field = super(DatabaseSessionMIA, self).get_field(collection, name)
        if field is not None:
            index = "%s|%s" % (collection, name)
            attrs = self.get_document(FIELD_ATTRIBUTES_COLLECTION, index)
            for i in ("visibility", "origin", "unit", "default_value"):
                setattr(field, i, getattr(attrs, i, None))
        return field

    def get_fields(self, collection):
        """Blabla"""

        fields = super(DatabaseSessionMIA, self).get_fields(collection)
        for field in fields:
            name = field.field_name
            index = "%s|%s" % (collection, name)
            attrs = self.get_document(FIELD_ATTRIBUTES_COLLECTION, index)
            for i in ("visibility", "origin", "unit", "default_value"):
                setattr(field, i, getattr(attrs, i, None))
        return fields

    def get_shown_tags(self):
        """Give the list of visible tags.

        :return: the list of visible tags
        """
        visible_names = []
        names_set = set()
        for i in self.filter_documents(
            FIELD_ATTRIBUTES_COLLECTION, "{visibility} == true"
        ):
            if i.field not in names_set:
                names_set.add(i.field)
                visible_names.append(i.field)  # respect list order
        return visible_names

    def set_shown_tags(self, fields_shown):
        """Set the list of visible tags.

        :param fields_shown: list of visible tags
        """

        for field in self.get_documents(FIELD_ATTRIBUTES_COLLECTION):
            self.set_value(
                FIELD_ATTRIBUTES_COLLECTION,
                field.index,
                "visibility",
                field.field in fields_shown,
            )


class DatabaseMIA(Database):
    """
    Class overriding the default behavior of populse_db
    """

    database_session_class = DatabaseSessionMIA
