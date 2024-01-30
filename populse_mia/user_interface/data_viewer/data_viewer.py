# -*- coding: utf-8 -*-
"""
This module provides an abstract base class for data viewer implemenataions in
populse-mia.

Data viewers are supposed to inherit :class:`DataViewer` and implement (at
least) its methods. A data viewer is given a project and documents list, and is
thus allowed to access databasing features and documents attributes.

Coding a data viewer
--------------------

A data viewer is identified after its module name, and is currently searched
for as a submodule of :mod:`populse_mia.user_interface.data_viewer`. The
data viewer module may be implemented as a "regular" module (.py file) or a
package (directory) and should contain at least a
class named ``MiaViewer`` which:

  - is a Qt ``QWidget`` (inherits ``QWidget`` as 1st inheritance as is required
    by Qt)
  - implements the :class:`DataViewer` API (normally by inheriting it as second
    inheritance after ``QWidget`` but this is not technically required if the
    API is implemented)

"""


class DataViewer(object):
    """
    Populse-MIA data viewers abstract base class: it just gives an API to be
    overloaded by subclasses.

    The API is made willingly very simple and limited. Viewers implementations
    are free to use Populse database features to implement fancy views. The
    base functions are to regiter a project and documents list, display or
    remove given files.
    """

    def display_files(self, files):
        """
        Display the selected document files
        """

        raise NotImplementedError(
            "display_files is abstract and should be overloaded in data "
            "viewer implementations"
        )

    def clear(self):
        """
        Hide / unload all displayed documents
        """

        self.remove_files(self.displayed_files())

    def displayed_files(self):
        """
        Get the list of displayed files
        """
        raise NotImplementedError(
            "displayed_files is abstract and should be overloaded in data "
            "viewer implementations"
        )

    def remove_files(self, files):
        """
        Remove documents from the displayed ones (hide, unload...)
        """

        raise NotImplementedError(
            "remove_files is abstract and should be overloaded in data "
            "viewer implementations"
        )

    def set_documents(self, projet, documents):
        """
        Sets the project and list of possible documents
        """

        raise NotImplementedError(
            "set_documents is abstract and should be overloaded in data "
            "viewer implementations"
        )

    def close(self):
        """Blabla"""

        self.clear()
