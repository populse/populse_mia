"""
This module provides an abstract base class for data viewer implemenataions in
populse_mia.

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

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

from abc import ABC, abstractmethod

from soma.qt_gui.qt_backend import Qt


class MetaDataViewer(type(Qt.QWidget), type(ABC)):
    """
    Custom metaclass that combines ABC and QWidget's metaclasses.
    """

    pass


class DataViewer(ABC, Qt.QWidget, metaclass=MetaDataViewer):
    """
    An abstract base class for data viewers with a minimal, extensible API.

    This class defines a standard interface for data viewers, allowing
    subclasses to implement custom visualization strategies. The base methods
    provide a simple contract for managing and displaying documents across
    different viewer implementations.

    The API is intentionally kept simple to provide flexibility for specific
    use cases while ensuring a consistent basic functionality.

    .. Methods:
        - clear: Remove all currently displayed files.
        - close: Close the viewer by clearing all displayed files.
        - display_files: Display the specified document files.
        - displayed_files: Retrieve the list of currently displayed files.
        - remove_files: Remove specified files from the display.
        - set_documents: Set the project context and available documents.

    """

    def clear(self):
        """
        Remove all currently displayed files.

        This method provides a default implementation that removes
        all files currently being displayed by calling remove_files().
        """
        self.remove_files(self.displayed_files())

    def close(self):
        """
        Close the viewer by clearing all displayed files.

        This method provides a standard way to clean up and close the viewer,
        ensuring all resources are released.
        """
        self.clear()

    @abstractmethod
    def display_files(self, files):
        """
        Display the specified document files.

        This method must be implemented by subclasses to define how
        files are visually presented or loaded.

        :param files (List): A list of files to be displayed.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement display_files method"
        )

    @abstractmethod
    def displayed_files(self):
        """
        Retrieve the list of currently displayed files.

        :return (list): A list of files currently being displayed.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement displayed_files method"
        )

    @abstractmethod
    def remove_files(self, files):
        """
        Remove specified files from the display.

        :param files (list): A list of files to be removed from display.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement remove_files method"
        )

    @abstractmethod
    def set_documents(self, project, documents):
        """
        Set the project context and available documents.

        :param project: The project associated with the documents.
        :param documents (list): The list of available documents.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement set_documents method"
        )
