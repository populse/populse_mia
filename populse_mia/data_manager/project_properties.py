"""Module that contains the class to handle the projects saved in the software.

Contains:
    Class:
    - SavedProjects

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import os

import yaml
from packaging import version

# Populse_MIA imports
from populse_mia.software_properties import Config


class SavedProjects:
    """
    Handles all saved projects in the software.

    Methods:
        - addSavedProject: Adds a new saved project.
        - loadSavedProjects: Loads saved projects from 'saved_projects.yml'.
        - removeSavedProject: Removes a project from the config file.
        - saveSavedProjects: Saves projects to 'saved_projects.yml'.
    """

    def __init__(self):
        """
        Initializes the saved projects from 'saved_projects.yml'.

        Attributes:
            savedProjects (dict): Dictionary containing saved project paths.
            pathsList (list): List of saved project paths.
        """
        self.savedProjects = self.loadSavedProjects()

        if (isinstance(self.savedProjects, dict)) and (
            "paths" in self.savedProjects
        ):
            self.pathsList = self.savedProjects["paths"]

            if self.pathsList is None:
                self.pathsList = []
                self.savedProjects["paths"] = []
        else:
            self.savedProjects = {"paths": []}
            self.pathsList = []

    def addSavedProject(self, newPath):
        """
        Adds a project path or moves it to the front if it exists.

        :param newPath (str): Path of the new project.

        :return (list): Updated project paths list.
        """

        if newPath in self.pathsList:
            self.pathsList.remove(newPath)

        self.pathsList.insert(0, newPath)
        self.savedProjects["paths"] = self.pathsList
        self.saveSavedProjects()
        return self.pathsList

    def loadSavedProjects(self):
        """
        Loads saved projects from 'saved_projects.yml', or creates a default
        file if missing.

        :return (dict): Loaded project paths.
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
        Removes a project path from pathsList and updates the file.

        :param path (str): Path to remove.
        """

        if path in self.pathsList:
            self.pathsList.remove(path)
            self.savedProjects["paths"] = self.pathsList
            self.saveSavedProjects()

    def saveSavedProjects(self):
        """
        Writes savedProjects to 'saved_projects.yml'.
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
