"""
Mia Saved Projects Module

This module provides the `SavedProjects` class, which manages the persistence
and retrieval of user-saved projects in the Mia software. It handles the
following operations:

    - Loading saved projects from a YAML configuration file
      (`saved_projects.yml`).
    - Adding, removing, and updating project paths in the configuration.
    - Serializing and saving the project list back to the YAML file.

The module ensures compatibility with multiple YAML parser versions and
gracefully handles missing or corrupted configuration files by creating a
default structure.

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# isort: off

import os
import yaml
from packaging import version

# isort: on

# populse_mia import
from populse_mia.software_properties import Config

__all__ = [
    "SavedProjects",
]


class SavedProjects:
    """
    Manage the list of saved project paths.

    The saved paths are stored in ``saved_projects.yml`` and are used to
    keep track of recently accessed projects.

    Contains:
        Methods:
            - addSavedProject: Adds a new saved project.
            - loadSavedProjects: Loads saved projects from
              'saved_projects.yml'.
            - removeSavedProject: Removes a project from the config file.
            - saveSavedProjects: Saves projects to 'saved_projects.yml'.
    """

    def __init__(self):
        """
        Initialize the saved project paths from ``saved_projects.yml``.

        If the file does not exist or contains invalid data, initialize an
        empty saved project list.
        """
        # Dictionary containing saved project paths
        self.savedProjects = self.loadSavedProjects()

        if (isinstance(self.savedProjects, dict)) and (
            "paths" in self.savedProjects
        ):
            # List of saved project paths
            self.pathsList = self.savedProjects["paths"]

            if self.pathsList is None:
                self.pathsList = []
                self.savedProjects["paths"] = []

        else:
            self.savedProjects = {"paths": []}
            self.pathsList = []

    def addSavedProject(self, newPath):
        """
        Add a project path to the saved list.

        If the path already exists, it is moved to the beginning of the list.

        :param newPath: Path of the project to save.
        :type newPath: str

        :return: Updated list of saved project paths.
        :rtype: list[str]
        """

        if newPath in self.pathsList:
            self.pathsList.remove(newPath)

        self.pathsList.insert(0, newPath)
        self.savedProjects["paths"] = self.pathsList
        self.saveSavedProjects()

        return self.pathsList

    def loadSavedProjects(self):
        """
        Load saved project paths from ``saved_projects.yml``.

        If the file does not exist, create a default empty configuration.

        :return: Dictionary containing saved project paths.
        :rtype: dict
        """
        config = Config()

        try:

            with open(
                os.path.join(
                    config.get_properties_path(),
                    "properties",
                    "saved_projects.yml",
                ),
            ) as stream:

                if version.parse(yaml.__version__) > version.parse("5.1"):
                    return yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    return yaml.load(stream)

        except FileNotFoundError:
            self.savedProjects = {"paths": []}
            self.pathsList = []
            self.saveSavedProjects()
            return {"paths": []}

        except yaml.YAMLError as exc:
            print(f"Error loading YAML: {exc}")
            return {"paths": []}

    def removeSavedProject(self, path):
        """
        Remove a project path from the saved list.

        :param path: Path of the project to remove.
        :type path: str
        """

        if path in self.pathsList:
            self.pathsList.remove(path)
            self.savedProjects["paths"] = self.pathsList
            self.saveSavedProjects()

    def saveSavedProjects(self):
        """
        Serialize the current saved project paths and write them to
        ``saved_projects.yml``.
        """

        config = Config()

        with open(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "saved_projects.yml",
            ),
            "w",
            encoding="utf8",
        ) as configfile:
            yaml.dump(
                self.savedProjects,
                configfile,
                default_flow_style=False,
                allow_unicode=True,
            )
