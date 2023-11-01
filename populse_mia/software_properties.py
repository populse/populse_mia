# -*- coding: utf-8 -*-
"""Module that handle the configuration of the software

Load and save the parameters from the miniviewer and the MIA preferences
pop-up in the config.yml file.

:Contains:
    :Class:
        - Config

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import glob
import os
import platform

import yaml

# Capsul import
from capsul.api import capsul_engine
from cryptography.fernet import Fernet

# populse_mia import
from populse_mia.utils.utils import verCmp

CONFIG = b"5YSmesxZ4ge9au2Bxe7XDiQ3U5VCdLeRdqimOOggKyc="


class Config:
    """
    Object that handles the configuration of the software

    :Contains:
        :Methods:
            - get_admin_hash: get the value of the hash of the admin password
            - get_afni_path: returns the path of AFNI
            - get_ants_path: returns the path of ANTS
            - getBackgroundColor: get background color
            - get_capsul_config: get CAPSUL config dictionary
            - get_capsul_engine: get a global CapsulEngine object used for all
              operations in MIA application
            - getChainCursors: returns if the "chain cursors" checkbox of the
              mini viewer is activated
            - get_config_path: returns the configuration file directory
            - get_freesurfer_setup: get freesurfer path
            - get_fsl_config: returns the path of the FSL config file
            - get_mainwindow_maximized: get the maximized (full-screen) flag
            - get_mainwindow_size: get the main window size
            - get_matlab_command: returns Matlab command
            - get_matlab_path: returns the path of Matlab's executable
            - get_matlab_standalone_path: returns the path of Matlab Compiler
              Runtime
            - get_max_projects: returns the maximum number of projects
              displayed in the "Saved projects" menu
            - get_max_thumbnails:  get max thumbnails number at the data
              browser bottom
            - get_properties_path: returns the software's properties path
            - get_mri_conv_path: returns the MRIManager.jar path
            - get_mrtrix_path: returns mrtrix path
            - getNbAllSlicesMax: returns the maximum number of slices to
              display in the mini viewer
            - get_opened_projects: returns the opened projects
            - getPathToProjectsFolder: returns the project's path
            - get_projects_save_path: returns the folder where the projects
              are saved
            - get_referential: returns boolean to indicate DataViewer
              referential
            - get_resources_path: get the resources path
            - getShowAllSlices: returns if the "show all slices" checkbox of
              the mini viewer is activated
            - getSourceImageDir: get the source directory for project images
            - get_spm_path: returns the path of SPM12 (license version)
            - get_spm_standalone_path: returns the path of SPM12 (standalone
              version)
            - getTextColor: return the text color
            - getThumbnailTag: returns the tag that is displayed in the mini
              viewer
            - get_use_afni: returns the value of "use afni" checkbox in the
              preferences
            - get_use_ants: returns the value of "use ants" checkbox in the
              preferences
            - get_use_clinical: returns the value of "clinical mode" checkbox
              in the preferences
            - get_use_freesurfer: returns the value of "use freesurfer"
              checkbox in the preferences
            - get_use_fsl: returns the value of "use fsl" checkbox in the
              preferences
            - get_use_matlab: returns the value of "use matlab" checkbox in the
              preferences
            - get_use_matlab_standalone: returns the value of "use matlab
              standalone" checkbox in the preferences
            - get_use_mrtrix: retunrs the value of "use mrtrix" checkbox in the
              prefrence
            - get_user_level: get the user level in the Capsul config
            - get_user_mode: returns the value of "user mode" checkbox
              in the preferences
            - get_use_spm: returns the value of "use spm" checkbox in the
              preferences
            - get_use_spm_standalone: returns the value of "use spm standalone"
              checkbox in the preferences
            - getViewerConfig: returns the DataViewer configuration (neuro or
              radio), by default neuro
            - getViewerFramerate: returns the DataViewer framerate for
              automatic time running images
            - isAutoSave: checks if auto-save mode is activated
            - isControlV1: checks if the selected display of the controller is
              of V1 type
            - isRadioView: checks if miniviewer in radiological orientation (if
              not, then it is in neurological orientation)
            - loadConfig: reads the config in the config.yml file
            - saveConfig: saves the config to the config.yml file
            - set_admin_hash: set the password hash
            - set_afni_path: set the path of the AFNI
            - set_ants_path: set the path of the ANTS
            - set_mrtrix_path: set the path of mrtrix
            - setAutoSave: sets the auto-save mode
            - setBackgroundColor: sets the background color
            - set_capsul_config: set CAPSUL configuration dict into MIA config
            - setChainCursors: set the "chain cursors" checkbox of the mini
              viewer
            - set_clinical_mode: set the value of "clinical mode" in
              the preferences
            - setControlV1: Set controller display mode (True if V1)
            - set_freesurfer_setup: set freesurfer path
            - set_fsl_config: set the path of the FSL config file
            - set_mainwindow_maximized: set the maximized (fullscreen) flag
            - set_mainwindow_size: set main window size
            - set_matlab_path: set the path of Matlab's executable
            - set_matlab_standalone_path: set the path of Matlab Compiler
              Runtime
            - set_max_projects: set the maximum number of projects displayed in
              the "Saved projects" menu
            - set_max_thumbnails: set max thumbnails number at the data browser
              bottom
            - set_mri_conv_path: set the MRIManager.jar path
            - setNbAllSlicesMax: set the maximum number of slices to display in
              the mini viewer
            - set_opened_projects: set the opened projects
            - set_projects_save_path: set the folder where the projects are
              saved
            - set_radioView: set the orientation in miniviewer (True for
              radiological, False for neurological orientation)
            - set_referential: set the DataViewer referential
            - set_resources_path: Set the resources path
            - setShowAllSlices: set the "show all slices" checkbox of the mini
              viewer
            - setSourceImageDir: set the source directory for project images
            - set_spm_path: set the path of SPM12 (license version)
            - set_spm_standalone_path: set the path of SPM12 (standalone
              version)
            - setTextColor: set the text color
            - setThumbnailTag: set the tag that is displayed in the mini viewer
            - set_use_afni: set the value of "use afni" checkbox in the
              preferences
            - set_use_ants: set the value of "use ants" checkbox in the
              preferences
            - set_use_freesurfer: set the value of "use freesurfer" checkbox
               in the preferences
            - set_use_fsl: set the value of "use fsl" checkbox in the
              preferences
            - set_use_matlab: set the value of "use matlab" checkbox in the
              preferences
            - set_use_matlab_standalone: set the value of "use matlab
              standalone" checkbox in the preferences
            - set_use_mrtrix: set the value of "use mrtrix" checkbox in the
              preferences
            - set_user_mode: set the value of "user mode" checkbox in
              the preferences
            - set_use_spm: set the value of "use spm" checkbox in the
              preferences
            - set_use_spm_standalone: set the value of "use spm standalone"
              checkbox in the preferences
            - setViewerConfig: set the Viewer configuration neuro or radio
            - setViewerFramerate: set the Viewer frame rate for automatic
              running time images
            - update_capsul_config: update a global CapsulEngine object used
              for all operations in MIA application
    """

    capsul_engine = None

    def __init__(self, config_path=None):
        """Initialization of the Config class

        :Parameters:
            - :config_path: str (optional). If provided, the configuration file
               will be loaded/saved from the given directory. Otherwise, the
               regular heuristics will be used to determine the config path.
               This option allows to use an alternative config directory (for
               tests for instance).
        """

        if config_path is not None:
            self.config_path = config_path

        if os.environ.get("MIA_DEV_MODE", None) is not None:
            self.dev_mode = bool(int(os.environ["MIA_DEV_MODE"]))

        else:
            # FIXME: What can we do if  "MIA_DEV_MODE" is not in os.environ?
            print("MIA_DEV_MODE not found ...")

        self.config = self.loadConfig()

        if "properties_user_path" not in self.config.keys():
            self.config["properties_user_path"] = self.get_properties_path()
            self.saveConfig()

    def get_admin_hash(self):
        """Get the value of the hash of the admin password.

        :returns: string
        """

        try:
            return self.config["admin_hash"]
        except KeyError:
            return False

    def get_afni_path(self):
        """Get the AFNI path

        :returns: string of path to AFNI
        """

        return self.config.get("afni", "")

    def get_ants_path(self):
        """Get the ANTS path

        :returns: string of path to ANTS
        """

        return self.config.get("ants", "")

    def get_freesurfer_setup(self):
        """Get the freesurfer path

        :returns: string of path to freesurfer
        """
        return self.config.get("freesurfer_setup", "")

    def getBackgroundColor(self):
        """Get background color.

        :returns: string of the background color
        """

        return self.config.get("background_color", "")

    def get_capsul_config(self, sync_from_engine=True):
        """Get CAPSUL config dictionary.

        :param sync_from_engine: if True, perform a synchronisation
                                 with CAPSUL engine (Bool)

        :return: capsul_config: the CAPSUL configuration saved into
                                Mia config (Dict)
        """

        capsul_config = self.config.setdefault("capsul_config", {})
        capsul_config.setdefault(
            "engine_modules",
            [
                "nipype",
                "fsl",
                "freesurfer",
                "matlab",
                "spm",
                "fom",
                "python",
                "afni",
                "ants",
                "mrtrix",
                "somaworkflow",
            ],
        )
        econf = capsul_config.setdefault("engine", {})
        eeconf = econf.setdefault("global", {})

        # Take mia pref parameters
        use_spm = self.get_use_spm()
        spm_path = self.get_spm_path()

        use_spm_standalone = self.get_use_spm_standalone()
        spm_standalone_path = self.get_spm_standalone_path()

        use_matlab = self.get_use_matlab()
        matlab_path = self.get_matlab_path()

        use_matlab_standalone = self.get_use_matlab_standalone()
        matlab_standalone_path = self.get_matlab_standalone_path()

        use_fsl = self.get_use_fsl()
        fsl_config = self.get_fsl_config()

        use_afni = self.get_use_afni()
        afni_path = self.get_afni_path()

        use_ants = self.get_use_ants()
        ants_path = self.get_ants_path()

        use_freesurfer = self.get_use_freesurfer()
        freesurfer_setup = self.get_freesurfer_setup()

        use_mrtrix = self.get_use_mrtrix()
        mrtrix_path = self.get_mrtrix_path()

        # Make synchronisation from Mia pref to Capsul config:

        # TODO: We do not deal with the version parameter. This can produce
        #       hidden configurations (spm and spm12 and spm8 ...)!

        # SPM
        spm_configs = eeconf.setdefault("capsul.engine.module.spm", {})
        if use_spm_standalone:
            m = {}
            for config_id, m in spm_configs.items():
                if (
                    m.get("standalone")
                    and m.get("directory") == spm_standalone_path
                ):
                    break
            if m:
                config_id = m["config_id"]
            else:
                config_id = "spm-standalone"
            m = spm_configs.setdefault(config_id, {})
            m.update(
                {
                    "config_id": config_id,
                    "config_environment": "global",
                    "directory": spm_standalone_path,
                    "standalone": True,
                }
            )

        if use_spm:
            m = {}
            for config_id, m in spm_configs.items():
                if not m.get("standalone") and m.get("directory") == spm_path:
                    break
            if m:
                config_id = m["config_id"]
            else:
                config_id = "spm"
            m = spm_configs.setdefault(config_id, {})
            m.update(
                {
                    "config_id": config_id,
                    "config_environment": "global",
                    "directory": spm_path,
                    "standalone": False,
                }
            )

        # MATLAB
        if use_matlab_standalone:
            m = eeconf.setdefault(
                "capsul.engine.module.matlab", {}
            ).setdefault("matlab", {})
            m["mcr_directory"] = matlab_standalone_path
            m["config_id"] = "matlab"
            m["config_environment"] = "global"

        if use_matlab:
            m = eeconf.setdefault(
                "capsul.engine.module.matlab", {}
            ).setdefault("matlab", {})
            m["executable"] = matlab_path
            m["config_id"] = "matlab"
            m["config_environment"] = "global"

        # FSL
        if use_fsl:
            m = eeconf.setdefault("capsul.engine.module.fsl", {}).setdefault(
                "fsl", {}
            )
            m["config_id"] = "fsl"
            m["config_environment"] = "global"
            m["config"] = fsl_config
            m["directory"] = os.path.dirname(
                os.path.dirname(os.path.dirname(fsl_config))
            )

        # AFNI
        if use_afni:
            m = eeconf.setdefault("capsul.engine.module.afni", {}).setdefault(
                "afni", {}
            )
            m["config_id"] = "afni"
            m["config_environment"] = "global"
            m["directory"] = afni_path

        # ANTS
        if use_ants:
            m = eeconf.setdefault("capsul.engine.module.ants", {}).setdefault(
                "ants", {}
            )
            m["config_id"] = "ants"
            m["config_environment"] = "global"
            m["directory"] = ants_path

        # Freesurfer
        if use_freesurfer:
            m = eeconf.setdefault(
                "capsul.engine.module.freesurfer", {}
            ).setdefault("freesurfer", {})
            m["config_id"] = "freesurfer"
            m["config_environment"] = "global"
            m["setup"] = freesurfer_setup
            # TODO: change fs subject dir
            m["subjects_dir"] = ""

        # mrtrix
        if use_mrtrix:
            m = eeconf.setdefault(
                "capsul.engine.module.mrtrix", {}
            ).setdefault("mrtrix", {})
            m["config_id"] = "mrtrix"
            m["config_environment"] = "global"
            m["directory"] = mrtrix_path

        # attributes completion
        m = eeconf.setdefault(
            "capsul.engine.module.attributes", {}
        ).setdefault("attributes", {})
        m["config_id"] = "attributes"
        m["config_environment"] = "global"
        m["attributes_schema_paths"] = [
            "capsul.attributes.completion_engine_factory",
            "populse_mia.user_interface.pipeline_manager.process_mia",
        ]
        m["process_completion"] = "mia_completion"

        # Synchronise from engine, or not
        if sync_from_engine and self.capsul_engine:
            for environment in (
                self.capsul_engine.settings.get_all_environments
            )():
                eeconf = econf.setdefault(environment, {})
                # would need a better merging system
                eeconf.update(
                    self.capsul_engine.settings.export_config_dict(
                        environment
                    )[environment]
                )

        return capsul_config

    @staticmethod
    def get_capsul_engine():
        """
        Get a global CapsulEngine object used for all operations in MIA
        application. The engine is created once when needed.

        :returns: Config.capsul_engine: capsul.engine.CapsulEngine object
        """

        config = Config()
        config.get_capsul_config()

        if Config.capsul_engine is None:
            Config.capsul_engine = capsul_engine()
            Config().update_capsul_config()

        return Config.capsul_engine

    def getChainCursors(self):
        """Get the value of the checkbox 'chain cursor' in miniviewer.

        :returns: boolean
        """

        return self.config.get("chain_cursors", False)

    def get_config_path(self):
        """Get the config.yml folder path.

        :returns: string of directory path to the config.yml file
        """

        config_path = getattr(self, "config_path", None)

        if config_path:
            return config_path

        properties_path = self.get_properties_path()

        return os.path.join(properties_path, "properties")

    def get_fsl_config(self):
        """Get the FSL config file  path

        :returns: string of path to the fsl/etc/fslconf/fsl.sh file
        """

        return self.config.get("fsl_config", "")

    def get_mainwindow_maximized(self):
        """Get the maximized (fullscreen) flag

        :returns:  boolean
        """

        return self.config.get("mainwindow_maximized", True)

    def get_mainwindow_size(self):
        """Get the main window size

        :returns:  list or None
        """

        return self.config.get("mainwindow_size", None)

    def get_matlab_command(self):
        """Get Matlab command.

        :returns: matlab executable path or nothing if matlab path not
                  specified
        """

        if self.config.get("use_spm_standalone"):
            archi = platform.architecture()
            if "Windows" in archi[1]:
                spm_script = glob.glob(
                    os.path.join(
                        self.config["spm_standalone"],
                        "spm*_win" + archi[0][:2] + ".exe",
                    )
                )
            else:
                spm_script = glob.glob(
                    os.path.join(self.config["spm_standalone"], "run_spm*.sh")
                )
            if spm_script:
                spm_script = spm_script[0]
                return "{0} {1} script".format(
                    spm_script, self.config["matlab_standalone"]
                )
            else:
                return ""  # will not work.
        else:
            return self.config.get("matlab", None)

    def get_matlab_path(self):
        """Get the path to the matlab executable.

        :returns: String of path
        """

        return self.config.get("matlab", None)

    def get_matlab_standalone_path(self):
        """Get the path to matlab compiler runtime.

        :returns: string of path
        """

        return self.config.get("matlab_standalone", "")

    def get_max_projects(self):
        """Get the maximum number of projects displayed in the "Saved
        projects" menu.

        :returns: Integer
        """

        try:
            return int(self.config["max_projects"])

        except KeyError:
            return 5

    def get_max_thumbnails(self):
        """Get the max thumbnails number at the data browser bottom.

        :returns: Integer
        """

        try:
            return int(self.config["max_thumbnails"])

        except KeyError:
            return 5

    def get_properties_path(self):
        """Get the path to the folder containing the processes and properties
        folders of mia (properties_path).

        During the user mode mia installation, the properties_path is defined
        and stored in the configuration.yml file, located in the .populse_mia
        folder (located in the user's home). If mia is launched in user
        mode, properties path must compulsorily be returned from the
        "properties_user_path" parameter of the configuration.yml. If mia is
        launched in developer mode, mia path must compulsorily be returned
        from the "properties_dev_path" parameter of the configuration.yml.

        :returns: string of path to properties folder
        """

        properties_path = getattr(self, "properties_path", None)

        if properties_path:
            return properties_path

        dot_mia_config = os.path.join(
            os.path.expanduser("~"), ".populse_mia", "configuration.yml"
        )

        # if os.path.isfile(dot_mia_config):

        try:
            with open(dot_mia_config, "r") as stream:
                try:
                    if verCmp(yaml.__version__, "5.1", "sup"):
                        mia_home_properties_path = yaml.load(
                            stream, Loader=yaml.FullLoader
                        )

                    else:
                        mia_home_properties_path = yaml.load(stream)

                except yaml.YAMLError as e:
                    print(
                        "\n ",
                        e,
                        "\n ~/.populse_mia/configuration.yml cannot "
                        "be read, the path to the properties folder has not "
                        "been found...",
                    )
                    raise

                else:
                    # Patch for obsolete parameters.
                    if "mia_path" in mia_home_properties_path:
                        mia_home_properties_path[
                            "properties_user_path"
                        ] = mia_home_properties_path["mia_path"]
                        del mia_home_properties_path["mia_path"]

                        with open(
                            dot_mia_config, "w", encoding="utf8"
                        ) as configfile:
                            yaml.dump(
                                mia_home_properties_path,
                                configfile,
                                default_flow_style=False,
                                allow_unicode=True,
                            )

                    if "mia_user_path" in mia_home_properties_path:
                        mia_home_properties_path[
                            "properties_user_path"
                        ] = mia_home_properties_path["mia_user_path"]
                        del mia_home_properties_path["mia_user_path"]

                        with open(
                            dot_mia_config, "w", encoding="utf8"
                        ) as configfile:
                            yaml.dump(
                                mia_home_properties_path,
                                configfile,
                                default_flow_style=False,
                                allow_unicode=True,
                            )

                    try:
                        if self.dev_mode is True:
                            self.properties_path = mia_home_properties_path[
                                "properties_dev_path"
                            ]
                            return self.properties_path

                        elif self.dev_mode is False:
                            self.properties_path = mia_home_properties_path[
                                "properties_user_path"
                            ]
                            return self.properties_path

                    except KeyError as e:
                        print(
                            "\nproperties_dev_path or properties_user_path key"
                            " not found in ~/.populse_mia/configuration.yml:"
                            "\n",
                            e,
                        )
                        raise

        except Exception as e:
            print(
                "\n ~/.populse_mia/configuration.yml cannot be found, the "
                "path to the properties has not been found...:\n",
                e,
            )
            raise

    def get_mri_conv_path(self):
        """Get the MRIManager.jar path.

        :returns: string of the path to the MRIManager.jar
        """

        return self.config.get("mri_conv_path", "")

    def get_mrtrix_path(self):
        """Get the  mrtrix path

        :returns: string of path to mrtrix
        """

        return self.config.get("mrtrix", "")

    def getNbAllSlicesMax(self):
        """Get number the maximum number of slices to display in the
        miniviewer.

        :returns: Integer
        """

        return int(self.config.get("nb_slices_max", "10"))

    def get_opened_projects(self):
        """Get opened projects.

        :returns: list of opened projects
        """

        return self.config.get("opened_projects", [])

    def getPathToProjectsFolder(self):
        """Get the project's path.

        :returns: string of the path
        """

        return self.config.get("projects_save_path", "")

    def get_projects_save_path(self):
        """Get the path where projects are saved.

        :returns: string of path
        """

        try:
            return self.config["projects_save_path"]

        except KeyError:
            # if not os.path.isdir(
            #         os.path.join(self.get_properties_path(), 'projects')):
            #     os.mkdir(os.path.join(self.get_properties_path(),
            #                           'projects'))
            #
            # return os.path.join(self.get_properties_path(), 'projects')
            return ""

    def get_referential(self):
        """Checks in anatomist_2 data viewer which referential has been chosen

        :returns: 0 for World Coordinates, 1 for Image ref
        """

        return self.config.get("ref", "0")

    def get_resources_path(self):
        """Get the resources path.

        :returns: string of the path to the resources folder
        """

        return self.config.get("resources_path", "")

    def getShowAllSlices(self):
        """Get whether the show_all_slices parameters was enabled
        or not in the miniviewer.

        :returns: boolean
        """

        # Used in MiniViewer
        return self.config.get("show_all_slices", False)

    def getSourceImageDir(self):
        """Get the source directory for project images.

        :returns: string of the path
        """

        return self.config.get("source_image_dir", "")

    def get_spm_path(self):
        """Get the path of SPM12.

        :returns: string of path
        """

        return self.config.get("spm", "")

    def get_spm_standalone_path(self):
        """Get the path to the SPM12 (standalone version).

        :returns: String of path
        """

        return self.config.get("spm_standalone", "")

    def getTextColor(self):
        """Get the text color.

        :returns: string
        """

        return self.config.get("text_color", "")

    def getThumbnailTag(self):
        """Get the tag of the thumbnail displayed in the miniviewer.

        :returns: string
        """

        return self.config.get("thumbnail_tag", "SequenceName")

    def get_use_afni(self):
        """Get the value of "use afni" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_afni", False)

    def get_use_ants(self):
        """Get the value of "use ants" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_ants", False)

    def get_use_clinical(self):
        """Get the clinical mode in the preferences.

        :returns: boolean
        """

        return self.config.get("clinical_mode", False)

    def get_use_fsl(self):
        """Get the value of "use fsl" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_fsl", False)

    def get_use_freesurfer(self):
        """Get the value of "use freesurfer" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_freesurfer", False)

    def get_use_matlab(self):
        """Get the value of "use matlab" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_matlab", False)

    def get_use_matlab_standalone(self):
        """Get the value of "use matlab standalone" checkbox in the
        preferences.

        :returns: boolean
        """

        return self.config.get("use_matlab_standalone", False)

    def get_user_level(self):
        """Get the user level in the Capsul config

        :returns: integer
        """

        return (
            self.config.get("capsul_config", {})
            .get("engine", {})
            .get("global", {})
            .get("capsul.engine.module.axon", {})
            .get("user_level", 0)
        )

    def get_user_mode(self):
        """Get if user mode is disabled or enabled in the preferences.

        :returns: boolean
        """

        return self.config.get("user_mode", True)

    def get_use_mrtrix(self):
        """Get the value of "use mrtrix" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_mrtrix", False)

    def get_use_spm(self):
        """Get the value of "use spm" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_spm", False)

    def get_use_spm_standalone(self):
        """Get the value of "use spm standalone" checkbox in the preferences.

        :returns: boolean
        """

        return self.config.get("use_spm_standalone", False)

    def getViewerConfig(self):
        """Get the viewer config neuro or radio, neuro by default

        :returns: String
        """

        return self.config.get("config_NeuRad", "neuro")

    def getViewerFramerate(self):
        """Get the Viewer framerate

        :returns: integer
        """

        return self.config.get("im_sec", "5")

    def isAutoSave(self):
        """Get if the auto-save mode is enabled or not.

        :returns: boolean
        """

        return self.config.get("auto_save", False)

    def isControlV1(self):
        """Get if the display of the controller is of V1 type.

        :returns: boolean
        """

        return self.config.get("control_V1", False)

    def isRadioView(self):
        """Get if the display in miniviewer is in radiological orientation.

        - True for radiological
        - False for neurological

        :returns: boolean
        """

        return self.config.get("radio_view", True)

    def loadConfig(self):
        """Read the config in the config.yml file.

        :returns: Returns a dictionary of the contents of config.yml
        """

        f = Fernet(CONFIG)
        config_file = os.path.join(self.get_config_path(), "config.yml")

        if not os.path.exists(config_file):
            return {}

        with open(config_file, "rb") as stream:
            try:
                stream = b"".join(stream.readlines())
                decrypted = f.decrypt(stream)

                if verCmp(yaml.__version__, "5.1", "sup"):
                    return yaml.load(decrypted, Loader=yaml.FullLoader)

                else:
                    return yaml.load(decrypted)

            except yaml.YAMLError as exc:
                print("error loading YAML file: %s" % config_file)
                print(exc)

        # in case of problem, return an empty config
        return {}

    def saveConfig(self):
        """Save the current parameters in the config.yml file."""

        f = Fernet(CONFIG)
        config_file = os.path.join(self.get_config_path(), "config.yml")

        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))

        with open(config_file, "wb") as configfile:
            stream = yaml.dump(
                self.config, default_flow_style=False, allow_unicode=True
            )
            configfile.write(f.encrypt(stream.encode()))

        self.update_capsul_config()

    def set_admin_hash(self, admin_hash):
        """Set the password hash.

        :param admin_hash: string of hash
        """

        self.config["admin_hash"] = admin_hash
        # Then save the modification
        self.saveConfig()

    def set_afni_path(self, path):
        """Set the AFNI path

        :param path: string of AFNI path
        """

        self.config["afni"] = path
        # Then save the modification
        self.saveConfig()

    def set_ants_path(self, path):
        """Set the ANTS path

        :param path: string of ANTS path
        """

        self.config["ants"] = path
        # Then save the modification
        self.saveConfig()

    def set_mrtrix_path(self, path):
        """Set the mrtrix path

        :param path: string of mrtrix path
        """

        self.config["mrtrix"] = path
        # Then save the modification
        self.saveConfig()

    # def set_freesurfer_path(self, path):
    #     """Set the freesurfer path

    #     :param path: string of freesurfer path
    #     """

    #     self.config["freesurfer"] = path
    #     # Then save the modification
    #     self.saveConfig()

    def setAutoSave(self, save):
        """Set auto-save mode.

        :param save: boolean
        """

        self.config["auto_save"] = save
        # Then save the modification
        self.saveConfig()

    def setBackgroundColor(self, color):
        """Set background color and save configuration.

        :param color: Color string ('Black', 'Blue', 'Green', 'Grey',
                                    'Orange', 'Red', 'Yellow', 'White')
        """

        self.config["background_color"] = color
        # Then save the modification
        self.saveConfig()

    def set_capsul_config(self, capsul_config_dict):
        """Set CAPSUL configuration dict into MIA config.

        This method is used just (and only) after editing capsul config
        (in File > Mia preferences, Pipeline tab, Edit CAPSUL config button),
        in order to synchronise the new Capsul config with the Mia preferences.

        :param capsul_config_dict: a dict; {'engine': {...},
                                            'engine_modules': [...]}
        """

        self.config["capsul_config"] = capsul_config_dict

        # update MIA values
        engine_config = capsul_config_dict.get("engine")
        new_engine = capsul_engine()

        for environment, config in engine_config.items():
            if environment == "capsul_engine":
                continue
            new_engine.import_configs(environment, config)

        engine_config = new_engine.settings.export_config_dict("global")

        # afni
        afni = engine_config.get("global", {}).get("capsul.engine.module.afni")

        if afni:
            afni = next(iter(afni.values()))
            afni_path = afni.get("directory")
            use_afni = bool(afni_path)

            if afni_path:
                self.set_afni_path(afni_path)

            self.set_use_afni(use_afni)

        # ants
        ants = engine_config.get("global", {}).get("capsul.engine.module.ants")

        if ants:
            ants = next(iter(ants.values()))
            ants_path = ants.get("directory")
            use_ants = bool(ants_path)

            if ants_path:
                self.set_ants_path(ants_path)

            self.set_use_ants(use_ants)

        # freesurfer
        freesurfer = engine_config.get("global", {}).get(
            "capsul.engine.module.freesurfer"
        )
        use_freesurfer = False
        if freesurfer:
            freesurfer = next(iter(freesurfer.values()))
            freesurfer_setup_path = freesurfer.get("setup")

            if freesurfer_setup_path:
                use_freesurfer = True
                self.set_freesurfer_setup(freesurfer_setup_path)

            self.set_use_freesurfer(use_freesurfer)

        # fsl
        fsl = engine_config.get("global", {}).get("capsul.engine.module.fsl")
        use_fsl = False

        if fsl:
            fsl = next(iter(fsl.values()))
            fsl_conf_path = fsl.get("config")
            fsl_dir_path = fsl.get("directory")

            if fsl_conf_path:
                use_fsl = True
                self.set_fsl_config(fsl_conf_path)
                self.set_use_fsl(True)

            # If only the directory parameter has been set, let's try using
            # the config parameter = directory/etc/fslconf/fsl.sh:
            elif fsl_dir_path:
                fsl_conf = os.path.join(
                    fsl_dir_path, "etc", "fslconf", "fsl.sh"
                )

                if os.path.isfile(fsl_conf):
                    use_fsl = True
                    self.set_fsl_config(fsl_conf)
                    self.set_use_fsl(True)

                else:
                    print(
                        "\nThe automatic determination of the configuration "
                        "file from the directory known for fsl ({}) did not "
                        "work. FSL is not correctly defined in the "
                        "preferences (see File > Mia Preferences) "
                        "...".format(fsl_dir_path)
                    )

        if use_fsl is False:
            self.set_use_fsl(False)

        # matlab
        matlab = engine_config.get("global", {}).get(
            "capsul.engine.module.matlab"
        )
        use_matlab = False
        use_mcr = False

        if matlab:
            matlab = next(iter(matlab.values()))
            matlab_path = matlab.get("executable")

            if bool(matlab_path) and os.path.isfile(matlab_path):
                use_matlab = True

            mcr_dir = matlab.get("mcr_directory")

            if bool(mcr_dir) and os.path.isdir(mcr_dir):
                use_mcr = True

        # mrtrix
        mrtrix = engine_config.get("global", {}).get(
            "capsul.engine.module.mrtrix"
        )

        if mrtrix:
            mrtrix = next(iter(mrtrix.values()))
            mrtrix_path = mrtrix.get("directory")
            use_mrtrix = bool(mrtrix_path)

            if mrtrix_path:
                self.set_mrtrix_path(mrtrix_path)

            self.set_use_mrtrix(use_mrtrix)

        # spm
        spm = engine_config.get("global", {}).get("capsul.engine.module.spm")
        use_spm_standalone = False
        use_spm = False

        if spm:
            # TODO: we only take the first element of the dictionary (the one
            #       that is normally edited in the Capsul config GUI). There is
            #       actually a problem because this means that there may be
            #       hidden config(s) ... This can produce bugs and at least
            #       unpredictable results for the user ...

            spm = next(iter(spm.values()))
            spm_dir = spm.get("directory", False)
            use_spm_standalone = spm.get("standalone", False)

            if use_spm_standalone and os.path.isdir(spm_dir) and use_mcr:
                pass

            else:
                use_spm_standalone = False

            if (
                use_spm_standalone is False
                and os.path.isdir(spm_dir)
                and use_matlab
            ):
                use_spm = True

            else:
                use_spm = False

        if use_spm:
            self.set_spm_path(spm_dir)
            self.set_use_spm(True)
            self.set_use_spm_standalone(False)
            self.set_matlab_path(matlab_path)
            self.set_use_matlab(True)
            self.set_use_matlab_standalone(False)

        elif use_spm_standalone:
            self.set_spm_standalone_path(spm_dir)
            self.set_use_spm_standalone(True)
            self.set_use_spm(False)
            self.set_matlab_standalone_path(mcr_dir)
            self.set_use_matlab_standalone(True)
            self.set_use_matlab(False)

        # TODO: Because there are two parameters for matlab (executable and
        #  mcr_directory) in Capsul config, if the user defines both, we don't
        #  know which on to choose! Here we choose to favour matlab in front
        #  of MCR if both are chosen, is it desirable?
        elif use_matlab:
            self.set_matlab_path(matlab_path)
            self.set_use_matlab(True)
            self.set_use_matlab_standalone(False)
            self.set_use_spm(False)
            self.set_use_spm_standalone(False)

        elif use_mcr:
            self.set_matlab_standalone_path(mcr_dir)
            self.set_use_matlab_standalone(True)
            self.set_use_matlab(False)
            self.set_use_spm(False)
            self.set_use_spm_standalone(False)

        else:
            self.set_use_matlab(False)
            self.set_use_matlab_standalone(False)
            self.set_use_spm(False)
            self.set_use_spm_standalone(False)

        if (
            use_matlab
            and use_mcr
            and use_spm is False
            and use_spm_standalone is False
        ):
            print(
                "\n The Matlab executable and the mcr_directory parameters "
                "have been set concomitantly in the Capsul configuration. "
                "This leads to an indeterminacy. By default, Matlab is "
                "retained at the expense of MCR."
            )

        self.update_capsul_config()  # store into capsul engine

    def setChainCursors(self, chain_cursors):
        """Set the value of the checkbox 'chain cursor' in the mini viewer.

        :param chain_cursors: Boolean
        """

        self.config["chain_cursors"] = chain_cursors
        # Then save the modification
        self.saveConfig()

    def set_clinical_mode(self, clinical_mode):
        """Enable of disable clinical mode.

        :param clinical_mode: boolean
        """

        self.config["clinical_mode"] = clinical_mode
        # Then save the modification
        self.saveConfig()

    def setControlV1(self, controlV1):
        """Set controller display mode (True if V1).

        :param controlV1: boolean
        """

        self.config["control_V1"] = controlV1
        # Then save the modification
        self.saveConfig()

    def set_fsl_config(self, path):
        """Set  the FSL config file

        :param path: string of path to fsl/etc/fslconf/fsl.sh
        """

        self.config["fsl_config"] = path
        # Then save the modification
        self.saveConfig()

    def set_freesurfer_setup(self, path):
        """Set  the freesurfer config file

        :param path: string of path to freesurfer/FreeSurferEnv.sh
        """

        self.config["freesurfer_setup"] = path
        # Then save the modification
        self.saveConfig()

    def set_mainwindow_maximized(self, enabled):
        """Set the maximized (full-screen) flag

        :param enabled: boolean
        """

        self.config["mainwindow_maximized"] = enabled
        self.saveConfig()

    def set_mainwindow_size(self, size):
        """Set main window size

        :param size: list
        """

        self.config["mainwindow_size"] = list(size)
        self.saveConfig()

    def set_matlab_path(self, path):
        """Set the path of Matlab's executable.

        :param path: string of path
        """

        self.config["matlab"] = path
        # Then save the modification
        self.saveConfig()

    def set_matlab_standalone_path(self, path):
        """Set the path of Matlab Compiler Runtime.

        :param path: string of path
        """

        self.config["matlab_standalone"] = path
        # Then save the modification
        self.saveConfig()

    def set_max_projects(self, nb_max_projects):
        """Set the maximum number of projects displayed in
        the "Saved projects" menu.

        :param nb_max_projects: Integer
        """

        self.config["max_projects"] = nb_max_projects
        # Then save the modification
        self.saveConfig()

    def set_max_thumbnails(self, nb_max_thumbnails):
        """Set max thumbnails number at the data browser bottom.

        :param nb_max_thumbnails: Integer
        """

        self.config["max_thumbnails"] = nb_max_thumbnails
        # Then save the modification
        self.saveConfig()

    def set_mri_conv_path(self, path):
        """Set the MRIManager.jar path.

        :param path: string of the path
        """

        self.config["mri_conv_path"] = path
        # Then save the modification
        self.saveConfig()

    def setNbAllSlicesMax(self, nb_slices_max):
        """Set the number of slices to display in the mini viewer.

        :param nb_slices_max: maximum number of slices to display (Int)
        """

        self.config["nb_slices_max"] = nb_slices_max
        # Then save the modification
        self.saveConfig()

    def set_opened_projects(self, new_projects):
        """Set the list of opened projects and saves the modification.

        :param new_projects: list of path
        """

        self.config["opened_projects"] = new_projects
        # Then save the modification
        self.saveConfig()

    def set_projects_save_path(self, path):
        """Set the folder where the projects are saved.

        :param path: string of path
        """

        self.config["projects_save_path"] = path
        # Then save the modification
        self.saveConfig()

    def set_radioView(self, radio_view):
        """Set the radiological/neurological orientation in mini viewer.

        - True for radiological
        - False for neurological

        :param radio_view: boolean
        """

        self.config["radio_view"] = radio_view
        # Then save the modification
        self.saveConfig()

    def set_referential(self, ref):
        """Set the referential to image ref or world coordinates in anatomist_2
        data viewer.

        :param ref: str; 0 for World Coordinates, 1 for Image ref
        """

        self.config["ref"] = ref
        # Then save the modification
        self.saveConfig()

    def set_resources_path(self, path):
        """Set the resources path.

        :param path: string of the path
        """

        self.config["resources_path"] = path
        # Then save the modification
        self.saveConfig()

    def setShowAllSlices(self, show_all_slices):
        """Set the show_all_slides setting in miniviewer.

        :param show_all_slices: Boolean
        """

        self.config["show_all_slices"] = show_all_slices
        # Then save the modification
        self.saveConfig()

    def setSourceImageDir(self, source_image_dir):
        """Set the source directory for project images.

        :param source_image_dir: String of path
        """

        self.config["source_image_dir"] = source_image_dir
        # Then save the modification
        self.saveConfig()

    def set_spm_path(self, path):
        """Set the path of SPM (license version).

        :param path: string of path
        """

        self.config["spm"] = path
        # Then save the modification
        self.saveConfig()

    def set_spm_standalone_path(self, path):
        """Set the path of SPM (standalone version).

        :param path: string of path
        """

        self.config["spm_standalone"] = path
        # Then save the modification
        self.saveConfig()

    def setTextColor(self, color):
        """Set text color and save configuration.

        :param color: Color string ('Black', 'Blue', 'Green', 'Grey',
                                    'Orange', 'Red', 'Yellow', 'White')
        """

        self.config["text_color"] = color
        # Then save the modification
        self.saveConfig()

    def setThumbnailTag(self, thumbnail_tag):
        """Set the tag that is displayed in the mini viewer.

        :param thumbnail_tag: string
        """

        self.config["thumbnail_tag"] = thumbnail_tag
        # Then save the modification
        self.saveConfig()

    def set_use_afni(self, use_afni):
        """Set the value of "use_afni" checkbox in the preferences.

        :param use_afni: boolean
        """

        self.config["use_afni"] = use_afni
        # Then save the modification
        self.saveConfig()

    def set_use_ants(self, use_ants):
        """Set the value of "use_ants" checkbox in the preferences.

        :param use_ants: boolean
        """

        self.config["use_ants"] = use_ants
        # Then save the modification
        self.saveConfig()

    def set_use_freesurfer(self, use_freesurfer):
        """Set the value of "use_freesurfer" checkbox in the preferences.

        :param use_freesurfer: boolean
        """

        self.config["use_freesurfer"] = use_freesurfer
        # Then save the modification
        self.saveConfig()

    def set_use_fsl(self, use_fsl):
        """Set the value of "use_fsl" checkbox in the preferences.

        :param use_fsl: boolean
        """

        self.config["use_fsl"] = use_fsl
        # Then save the modification
        self.saveConfig()

    def set_use_matlab(self, use_matlab):
        """Set the value of "use matlab" checkbox in the preferences.

        :param use_matlab: boolean
        """

        self.config["use_matlab"] = use_matlab
        # Then save the modification
        self.saveConfig()

    def set_use_matlab_standalone(self, use_matlab_standalone):
        """Set the value of "use_matlab_standalone" checkbox in the
        preferences.

        :param use_matlab: boolean
        """

        self.config["use_matlab_standalone"] = use_matlab_standalone
        # Then save the modification
        self.saveConfig()

    def set_use_mrtrix(self, use_mrtrix):
        """Set the value of "use_mrtrix" checkbox in the preferences.

        :param use_mrtrix: boolean
        """

        self.config["use_mrtrix"] = use_mrtrix
        # Then save the modification
        self.saveConfig()

    def set_user_mode(self, user_mode):
        """Enable of disable user mode.

        :param user_mode: boolean
        """

        self.config["user_mode"] = user_mode
        # Then save the modification
        self.saveConfig()

    def set_use_spm(self, use_spm):
        """Set the value of "use spm" checkbox in the preferences.

        :param use_spm: boolean
        """

        self.config["use_spm"] = use_spm
        # Then save the modification
        self.saveConfig()

    def set_use_spm_standalone(self, use_spm_standalone):
        """Set the value of "use spm standalone" checkbox in the preferences.

        :param use_spm_standalone: boolean
        """

        self.config["use_spm_standalone"] = use_spm_standalone
        # Then save the modification
        self.saveConfig()

    def setViewerConfig(self, config_NeuRad):
        """sets user's configuration neuro or radio for data_viewer

        - neuro: neurological
        - radio: radiological

        :param config_NeuRad: string
        """

        self.config["config_NeuRad"] = config_NeuRad
        # Then save the modification
        self.saveConfig()

    def setViewerFramerate(self, im_sec):
        """sets user's framerate for data_viewer

        :param im_sec: int
        """

        self.config["im_sec"] = im_sec
        # Then save the modification
        self.saveConfig()

    def update_capsul_config(self):
        """
        Update a global CapsulEngine object used for all operations in MIA
        application. The engine is created once when needed, and updated
        each time the config is saved.

        :returns: capsul.engine.CapsulEngine object
        """

        if self.capsul_engine is None:
            # don't do anything until the config is really created: this
            # avoids unneeded updates before it is actually used.
            return

        capsul_config = self.get_capsul_config(sync_from_engine=False)
        engine = Config.capsul_engine

        for module in capsul_config.get("engine_modules", []) + [
            "fom",
            "nipype",
            "python",
            "fsl",
            "freesurfer",
            "axon",
            "afni",
            "ants",
            "mrtrix",
            "somaworkflow",
        ]:
            engine.load_module(module)

        engine_config = capsul_config.get("engine")

        if engine_config:
            for environment, config in engine_config.items():
                c = dict(config)

                if (
                    "capsul_engine" not in c
                    or "uses" not in c["capsul_engine"]
                ):
                    c["capsul_engine"] = {
                        "uses": {
                            engine.settings.module_name(m): "ALL"
                            for m in config.keys()
                        }
                    }

                try:
                    engine.import_configs(environment, c, cont_on_error=True)

                except Exception as exc:
                    print(
                        "\nAn issue is detected in the Mia's "
                        "configuration:\n{}\nPlease check the settings "
                        "in File > Mia Preferences > Pipeline "
                        "...".format(exc)
                    )

        return engine
