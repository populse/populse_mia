"""
Module that handle the configuration of the software

Load and save the parameters from the miniviewer and the MIA preferences
pop-up in the ``config.yml`` file.
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# isort: off

import glob
import logging
import os
import platform
import yaml
from cryptography.fernet import Fernet
from functools import lru_cache
from pathlib import Path

# isort: on

# Capsul import
from capsul.api import capsul_engine

# populse_mia import
from populse_mia.utils import verCmp

__all__ = ["Config"]

ENCRYPTION_KEY = b"5YSmesxZ4ge9au2Bxe7XDiQ3U5VCdLeRdqimOOggKyc="
logger = logging.getLogger(__name__)


class Config:
    """
    Object that handles the configuration of the software

    Contains:
        Methods:
            - _configure_matlab_only: Configures MATLAB without SPM
            - _configure_matlab_spm: Configures SPM and MATLAB
            - _configure_mcr_only: Configures MCR without SPM
            - _configure_standalone_spm: Configures standalone SPM and MCR
            - _disable_matlab_spm: Disables all MATLAB and SPM configurations
            - get_admin_hash: Get the value of the hash of the admin password
            - get_afni_path: Returns the path of AFNI
            - get_ants_path: Returns the path of ANTS
            - getBackgroundColor: Get background color
            - get_capsul_config: Get CAPSUL config dictionary
            - get_capsul_engine: Get a global CapsulEngine object used for all
              operations in MIA application
            - getChainCursors: Returns if the "chain cursors" checkbox of the
              mini-viewer is activated
            - get_freesurfer_setup: Get freesurfer path
            - get_fsl_config: Returns the path of the FSL config file
            - get_mainwindow_maximized: Get the maximized (full-screen) flag
            - get_mainwindow_size: Get the main window size
            - get_matlab_command: Returns Matlab command
            - get_matlab_path: Returns the path of Matlab's executable
            - get_matlab_standalone_path: Returns the path of Matlab Compiler
              Runtime
            - get_max_projects: Returns the maximum number of projects
              displayed in the "Saved projects" menu
            - get_max_thumbnails: Get max thumbnails number at the data
              browser bottom
            - get_mri_conv_path: Returns the MRIManager.jar path
            - get_mrtrix_path: Returns mrtrix path
            - getNbAllSlicesMax: Returns the maximum number of slices to
              display in the mini viewer
            - get_opened_projects: Returns the opened projects
            - get_projects_save_path: Returns the folder where the projects
              are saved
            - get_properties_path: Returns the software's properties path
            - get_referential: Returns boolean to indicate DataViewer
              referential
            - get_resources_path: Get the resources path
            - getShowAllSlices: Returns if the "show all slices" checkbox of
              the mini viewer is activated
            - getSourceImageDir: Get the source directory for project images
            - get_spm_path: Returns the path of SPM12 (license version)
            - get_spm_standalone_path: Returns the path of SPM12 (standalone
              version)
            - getTextColor: Return the text color
            - getThumbnailTag: Returns the tag that is displayed in the mini
              viewer
            - get_use_afni: Returns the value of "use afni" checkbox in the
              preferences
            - get_use_ants: Returns the value of "use ants" checkbox in the
              preferences
            - get_use_clinical: Returns the value of "clinical mode" checkbox
              in the preferences
            - get_use_freesurfer: Returns the value of "use freesurfer"
              checkbox in the preferences
            - get_use_fsl: Returns the value of "use fsl" checkbox in the
              preferences
            - get_use_matlab: Returns the value of "use matlab" checkbox in
              the preferences
            - get_use_matlab_standalone: Returns the value of "use matlab
              standalone" checkbox in the preferences
            - get_use_mrtrix: Returns the value of "use mrtrix" checkbox in
              the preferences
            - get_user_level: Get the user level in the Capsul config
            - get_user_mode: Returns the value of "user mode" checkbox
              in the preferences
            - get_use_spm: Returns the value of "use spm" checkbox in the
              preferences
            - get_use_spm_standalone: Returns the value of "use spm standalone"
              checkbox in the preferences
            - getViewerConfig: Returns the DataViewer configuration (neuro or
              radio), by default neuro
            - getViewerFramerate: Returns the DataViewer framerate for
              automatic time running images
            - isAutoSave: Checks if auto-save mode is activated
            - isControlV1: Checks if the selected display of the controller is
              of V1 type
            - isRadioView: Checks if miniviewer in radiological orientation (if
              not, then it is in neurological orientation)
            - loadConfig: Reads the config in the config.yml file
            - saveConfig: Saves the config to the config.yml file
            - set_admin_hash: Set the password hash
            - set_afni_path: Set the path of the AFNI
            - set_ants_path: Set the path of the ANTS
            - setAutoSave: Sets the auto-save mode
            - setBackgroundColor: Sets the background color
            - set_capsul_config: Set CAPSUL configuration dict into MIA config
            - setChainCursors: Set the "chain cursors" checkbox of the mini
              viewer
            - set_clinical_mode: Set the value of "clinical mode" in
              the preferences
            - setControlV1: Set controller display mode (True if V1)
            - set_freesurfer_setup: Set freesurfer path
            - set_fsl_config: Set the path of the FSL config file
            - set_mainwindow_maximized: Set the maximized (fullscreen) flag
            - set_mainwindow_size: Set main window size
            - set_matlab_path: Set the path of Matlab's executable
            - set_matlab_standalone_path: Set the path of Matlab Compiler
              Runtime
            - set_max_projects: Set the maximum number of projects displayed in
              the "Saved projects" menu
            - set_max_thumbnails: Set max thumbnails number at the data browser
              bottom
            - set_mri_conv_path: Set the MRIManager.jar path
            - set_mrtrix_path: Set the path of mrtrix
            - setNbAllSlicesMax: Set the maximum number of slices to display in
              the mini viewer
            - set_opened_projects: Set the opened projects
            - set_projects_save_path: Set the folder where the projects are
              saved
            - set_radioView: Set the orientation in miniviewer (True for
              radiological, False for neurological orientation)
            - set_referential: Set the DataViewer referential
            - set_resources_path: Set the resources path
            - setShowAllSlices: Set the "show all slices" checkbox of the mini
              viewer
            - setSourceImageDir: Set the source directory for project images
            - set_spm_path: Set the path of SPM12 (license version)
            - set_spm_standalone_path: Set the path of SPM12 (standalone
              version)
            - setTextColor: Set the text color
            - setThumbnailTag: Set the tag that is displayed in the mini viewer
            - set_use_afni: Set the value of "use afni" checkbox in the
              preferences
            - set_use_ants: Set the value of "use ants" checkbox in the
              preferences
            - set_use_freesurfer: Set the value of "use freesurfer" checkbox
              in the preferences
            - set_use_fsl: Set the value of "use fsl" checkbox in the
              preferences
            - set_use_matlab: Set the value of "use matlab" checkbox in the
              preferences
            - set_use_matlab_standalone: Set the value of "use matlab
              standalone" checkbox in the preferences
            - set_use_mrtrix: Set the value of "use mrtrix" checkbox in the
              preferences
            - set_user_mode: Set the value of "user mode" checkbox in
              the preferences
            - set_use_spm: Set the value of "use spm" checkbox in the
              preferences
            - set_use_spm_standalone: Set the value of "use spm standalone"
              checkbox in the preferences
            - setViewerConfig: Set the Viewer configuration neuro or radio
            - setViewerFramerate: Set the Viewer frame rate for automatic
              running time images
            - update_capsul_config: Update a global CapsulEngine object used
              for all operations in MIA application
    """

    capsul_engine = None

    def __init__(self, properties_path=None):
        """
        Initialization of the Config class

        :param properties_path: If provided, the configuration file will be
            loaded / saved from the given directory. Otherwise, the regular
            heuristics will be used to determine the config path. This option
            allows to use an alternative config directory (for tests for
            instance).
        :type properties_path: str or None
        """

        if properties_path is not None:
            self.properties_path = properties_path

        if os.environ.get("MIA_DEV_MODE", None) is not None:
            self.dev_mode = bool(int(os.environ["MIA_DEV_MODE"]))

        else:
            # FIXME: What can we do if "MIA_DEV_MODE" is not in os.environ?
            logger.warning("MIA_DEV_MODE not found...")

        self.config = self.loadConfig()

    def _configure_matlab_only(self, matlab_path: str) -> None:
        """
        Configures MATLAB without SPM, ensuring that only MATLAB is used.

        :param matlab_path: The directory path of the MATLAB installation.
        :type matlab_path: str
        """
        self.set_matlab_path(matlab_path)
        self.set_use_matlab(True)
        self.set_use_matlab_standalone(False)
        self.set_use_spm(False)
        self.set_use_spm_standalone(False)

    def _configure_matlab_spm(self, spm_dir, matlab_path):
        """
        Configures SPM to use the specified SPM directory with a MATLAB
        installation.

        :param spm_dir: The directory path of the SPM installation.
        :type spm_dir: str
        :param matlab_path: The directory path of the MATLAB installation.
        :type matlab_path: str
        """
        self.set_spm_path(spm_dir)
        self.set_use_spm(True)
        self.set_use_spm_standalone(False)
        self.set_matlab_path(matlab_path)
        self.set_use_matlab(True)
        self.set_use_matlab_standalone(False)

    def _configure_mcr_only(self, mcr_dir: str) -> None:
        """
        Configures MATLAB Compiler Runtime (MCR) without SPM, ensuring
        that only MCR is used.

        :param mcr_dir: The directory path of the MATLAB Compiler Runtime
            (MCR).
        :type mcr_dir: str
        """
        self.set_matlab_standalone_path(mcr_dir)
        self.set_use_matlab_standalone(True)
        self.set_use_matlab(False)
        self.set_use_spm(False)
        self.set_use_spm_standalone(False)

    def _configure_standalone_spm(self, spm_dir, mcr_dir):
        """
        Configures standalone SPM to use the specified SPM and MATLAB
        Compiler Runtime (MCR) directories.

        :param spm_dir: The directory path of the standalone SPM installation.
        :type spm_dir: str
        :param mcr_dir: The directory path of the MATLAB Compiler Runtime
            (MCR).
        :type mcr_dir: str
        """
        self.set_spm_standalone_path(spm_dir)
        self.set_use_spm_standalone(True)
        self.set_use_spm(False)
        self.set_matlab_standalone_path(mcr_dir)
        self.set_use_matlab_standalone(True)
        self.set_use_matlab(False)

    def _disable_matlab_spm(self) -> None:
        """
        Disables all MATLAB and SPM configurations, ensuring that neither
        MATLAB nor SPM is used.
        """
        self.set_use_matlab(False)
        self.set_use_matlab_standalone(False)
        self.set_use_spm(False)
        self.set_use_spm_standalone(False)

    def get_admin_hash(self):
        """
        Retrieves the hashed admin password from the configuration.

        :returns: The hashed admin password if found in config, False if not
            present in config.
        :rtype: str or bool
        """

        try:
            return self.config["admin_hash"]

        except KeyError:
            return False

    def get_afni_path(self):
        """Get the AFNI path.

        :returns: Path to AFNI, or "" if unknown.
        :rtype: str
        """

        return self.config.get("afni", "")

    def get_ants_path(self):
        """Get the ANTS path.

        :returns: Path to ANTS, or "" if unknown.
        :rtype: str
        """

        return self.config.get("ants", "")

    def getBackgroundColor(self):
        """Get background color.

        :returns: (str) Background color, or "" if unknown.
        :rtype: str
        """

        return self.config.get("background_color", "")

    def get_capsul_config(self, sync_from_engine=True):
        """
        Retrieve and construct the Capsul configuration dictionary.

        This function builds a configuration dictionary for Capsul,
        incorporating settings for various neuroimaging tools and processing
        engines. It manages configurations for tools like SPM, FSL,
        FreeSurfer, MATLAB, AFNI, ANTs, and MRTrix.

        The function first retrieves local settings for each tool from the Mia
        preferences, then constructs the appropriate configuration structure.
        If requested, it can synchronize the configuration with the current
        Capsul engine state.

        :param sync_from_engine: If True, synchronizes the configuration with
            the current Capsul engine settings after building the base
            configuration.
        :type sync_from_engine: bool

        :returns: A nested dictionary containing the complete Capsul
            configuration, structured with the following main sections:

            - ``engine_modules``: List of available processing modules
            - ``engine``: Contains global and environment-specific settings, as
              well as configurations specific to certain tools (SPM, FSL, etc.)
        :rtype: dict

        Contains:
            Inner functions:
                - _configure_spm: Configure SPM settings.
                - _configure_tool: Configure various neuroimaging settings
                  (e.g. 'fsl', 'afni', etc.)
        """

        def _configure_spm(spm_configs, path, standalone=False):
            """
            Helper function to configure SPM settings, preserving existing
            configuration IDs if found.

            This function either updates an existing SPM configuration or
            creates a new one based on the provided parameters. It searches
            through existing configurations to find any matching the specified
            path and standalone settings. If found, it reuses that
            configuration's ID; otherwise, it generates a new one.

            :param spm_configs: Dictionary of existing SPM configurations where
                keys are config_ids and values are configuration dictionaries.
            :type spm_configs: dict
            :param path: Directory path for the SPM configuration.
            :type path: str
            :param standalone: Flag indicating whether this is a standalone
                configuration. Defaults to False
            :type standalone: bool
            """
            found_config = {}

            # Look for existing matching configuration
            for config_id, config in spm_configs.items():

                if (
                    config.get("standalone") == standalone
                    and config.get("directory") == path
                ):
                    found_config = config
                    break

            # Use existing config_id if found, otherwise create new one
            if found_config:
                config_id = found_config["config_id"]

            else:
                config_id = f"spm{'-standalone' if standalone else ''}"

            # Update or create configuration
            spm_configs.setdefault(config_id, {}).update(
                {
                    "config_id": config_id,
                    "config_environment": "global",
                    "directory": path,
                    "standalone": standalone,
                }
            )

        def _configure_tool(global_config, tool_name, tool_config):
            """
            Helper function to configure various neuroimaging tools within
            a global configuration.

            This function updates or creates tool-specific configurations
            within a global configuration dictionary. It handles setup for
            neuroimaging tools by managing their paths, configurations, and
            setup parameters.

            :param global_config: Global configuration dictionary where tool
                configurations will be stored. The tool's settings will be
                placed under the key 'capsul.engine.module.{tool_name}'.
            :type global_config: dict
            :param tool_name: Name of the neuroimaging tool being configured
                (e.g., 'fsl', 'afni', etc.).
            :type tool_name: str
            :param tool_config: Tool-specific configuration dictionary that may
                contain:

                - 'path': Directory path for the tool installation
                - 'config': Path to tool's configuration file
                - 'setup': Setup-specific parameters for the tool
            :type tool_config: dict
            """
            tool_section = global_config.setdefault(
                f"capsul.engine.module.{tool_name}", {}
            ).setdefault(tool_name, {})

            base_config = {
                "config_id": tool_name,
                "config_environment": "global",
            }

            if "path" in tool_config:
                base_config["directory"] = tool_config["path"]

            if "config" in tool_config:
                base_config["config"] = tool_config["config"]
                base_config["directory"] = os.path.dirname(
                    os.path.dirname(os.path.dirname(tool_config["config"]))
                )

            if "setup" in tool_config:
                base_config["setup"] = tool_config["setup"]
                # TODO: Change FSL subject dir
                base_config["subjects_dir"] = ""

            tool_section.update(base_config)

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
        # Set up engine configuration structure
        engine_config = capsul_config.setdefault("engine", {})
        global_config = engine_config.setdefault("global", {})
        # Collect all tool configurations
        tool_configs = {
            "spm": {
                "use_standard": self.get_use_spm(),
                "path": self.get_spm_path(),
                "use_standalone": self.get_use_spm_standalone(),
                "standalone_path": self.get_spm_standalone_path(),
            },
            "matlab": {
                "use_standard": self.get_use_matlab(),
                "path": self.get_matlab_path(),
                "use_standalone": self.get_use_matlab_standalone(),
                "standalone_path": self.get_matlab_standalone_path(),
            },
            "fsl": {
                "use": self.get_use_fsl(),
                "config": self.get_fsl_config(),
            },
            "afni": {"use": self.get_use_afni(), "path": self.get_afni_path()},
            "ants": {"use": self.get_use_ants(), "path": self.get_ants_path()},
            "freesurfer": {
                "use": self.get_use_freesurfer(),
                "setup": self.get_freesurfer_setup(),
            },
            "mrtrix": {
                "use": self.get_use_mrtrix(),
                "path": self.get_mrtrix_path(),
            },
        }

        # Make synchronisation from Mia preferences to Capsul config:
        # TODO: We do not deal with the version parameter. This can produce
        #       hidden configurations (spm and spm12 and spm8 ...)!
        # Configure SPM (both standalone and standard versions)
        spm_configs = global_config.setdefault("capsul.engine.module.spm", {})

        if tool_configs["spm"]["use_standalone"]:

            _configure_spm(
                spm_configs,
                tool_configs["spm"]["standalone_path"],
                standalone=True,
            )

        if tool_configs["spm"]["use_standard"]:
            _configure_spm(
                spm_configs, tool_configs["spm"]["path"], standalone=False
            )

        # Configure MATLAB
        matlab_config = global_config.setdefault(
            "capsul.engine.module.matlab", {}
        ).setdefault("matlab", {})

        if tool_configs["matlab"]["use_standalone"]:
            matlab_config.update(
                {
                    "mcr_directory": tool_configs["matlab"]["standalone_path"],
                    "config_id": "matlab",
                    "config_environment": "global",
                }
            )

        if tool_configs["matlab"]["use_standard"]:
            matlab_config.update(
                {
                    "executable": tool_configs["matlab"]["path"],
                    "config_id": "matlab",
                    "config_environment": "global",
                }
            )

        # Configure other tools
        for tool in ["fsl", "afni", "ants", "freesurfer", "mrtrix"]:

            if tool_configs[tool]["use"]:
                _configure_tool(global_config, tool, tool_configs[tool])

        # attributes completion
        attrs_config = global_config.setdefault(
            "capsul.engine.module.attributes", {}
        ).setdefault("attributes", {})

        attrs_config.update(
            {
                "config_id": "attributes",
                "config_environment": "global",
                "attributes_schema_paths": [
                    "capsul.attributes.completion_engine_factory",
                    "populse_mia.user_interface.pipeline_manager.process_mia",
                ],
                "process_completion": "mia_completion",
            }
        )

        # Synchronise from engine, or not
        if sync_from_engine and self.capsul_engine:

            for environment in (
                self.capsul_engine.settings.get_all_environments
            )():
                env_config = engine_config.setdefault(environment, {})
                # would need a better merging system
                env_config.update(
                    self.capsul_engine.settings.export_config_dict(
                        environment
                    )[environment]
                )

        return capsul_config

    @staticmethod
    @lru_cache(maxsize=1)
    def get_capsul_engine():
        """
        Get or create a global CapsulEngine singleton for Mia application
        operations.

        The engine is created only once when first needed (lazy
        initialization). Subsequent calls return the same instance.

        :returns: The global CapsulEngine instance.
        :rtype: capsul.api.capsul_engine
        """

        if Config.capsul_engine is None:
            config = Config()
            config.get_capsul_config()
            Config.capsul_engine = capsul_engine()
            Config().update_capsul_config()

        return Config.capsul_engine

    def getChainCursors(self):
        """Get the value of the checkbox 'chain cursor' in miniviewer.

        :returns: Value of the checkbox.
        :rtype: bool
        """

        return self.config.get("chain_cursors", False)

    def get_freesurfer_setup(self):
        """Get the freesurfer path.

        :returns: Path to freesurfer, or "" if unknown.
        :rtype: str
        """
        return self.config.get("freesurfer_setup", "")

    def get_fsl_config(self):
        """Get the FSL config file  path.

        :returns: Path to the fsl/etc/fslconf/fsl.sh file.
        :rtype: str
        """

        return self.config.get("fsl_config", "")

    def get_mainwindow_maximized(self):
        """Get the maximized (fullscreen) flag.

        :returns: Maximized (fullscreen) flag.
        :rtype: bool
        """

        return self.config.get("mainwindow_maximized", True)

    def get_mainwindow_size(self):
        """Get the main window size.

        :returns: Main window size.
        :rtype: list
        """

        return self.config.get("mainwindow_size", None)

    def get_matlab_command(self):
        """
        Retrieves the appropriate Matlab command based on the configuration.

        :returns: The Matlab executable path or None if no path is specified.
        :rtype: str or None
        """

        if self.config.get("use_spm_standalone"):
            arch_bits, os_name = platform.architecture()

            if "Windows" in os_name:
                pattern = os.path.join(
                    self.config["spm_standalone"],
                    f"spm*_win{arch_bits[:2]}.exe",
                )

            else:
                pattern = os.path.join(
                    self.config["spm_standalone"], "run_spm*.sh"
                )

            spm_script = glob.glob(pattern)
            # An empty string indicates that the script has not been
            # localised, which is bound to cause problems later on.
            return (
                f"{spm_script[0]} {self.config['matlab_standalone']} script"
                if spm_script
                else ""
            )

        return self.config.get("matlab")

    def get_matlab_path(self):
        """Get the path to the matlab executable.

        :returns: A path.
        :rtype: str
        """

        return self.config.get("matlab", None)

    def get_matlab_standalone_path(self):
        """Get the path to matlab compiler runtime.

        :returns: A path.
        :rtype: str
        """

        return self.config.get("matlab_standalone", "")

    def get_max_projects(self):
        """
        Retrieves the maximum number of projects displayed in the
        "Saved projects" menu.

        :returns: The maximum number of projects. Defaults to 5 if not
            specified.
        :rtype: int
        """

        return int(self.config.get("max_projects", 5))

    def get_max_thumbnails(self):
        """
        Retrieves the maximum number of thumbnails displayed in the mini-viewer
        at the bottom of the data browser.

        :returns: The maximum number of thumbnails. Defaults to 5 if not
            specified.
        :rtype: int
        """
        return int(self.config.get("max_thumbnails", 5))

    def get_mri_conv_path(self):
        """Get the MRIManager.jar path.

        :returns: A path.
        :rtype: str
        """

        return self.config.get("mri_conv_path", "")

    def get_mrtrix_path(self):
        """Get the  mrtrix path.

        :returns: A path.
        :rtype: str
        """

        return self.config.get("mrtrix", "")

    def getNbAllSlicesMax(self):
        """
        Get number the maximum number of slices to display in the miniviewer.

        :returns: Maximum number of slices to display in miniviewer.
        :rtype: int
        """

        return int(self.config.get("nb_slices_max", "10"))

    def get_opened_projects(self):
        """Get opened projects.

        :returns: Opened projects.
        :rtype: list
        """
        return self.config.get("opened_projects", [])

    def get_projects_save_path(self):
        """Get the path where projects are saved.

        :returns: A path.
        :rtype: str
        """
        return self.config.get("projects_save_path", "")

    def get_properties_path(self):
        """
        Retrieves the path to the folder containing the "processes" and
        "properties" directories of Mia.

        The properties path is defined in the `configuration_path.yml` file,
        located in `~/.populse_mia`.

        - In **user mode**, the path is retrieved from the
          `properties_user_path` parameter.
        - In **developer mode**, the path is retrieved from the
          `properties_dev_path` parameter.

        If outdated parameters (`mia_path`, `mia_user_path`) are found, they
        are automatically updated in the configuration file.

        :returns: The absolute path to the properties folder.
        :rtype: str
        """

        if (
            hasattr(self, "properties_path")
            and self.properties_path is not None
        ):
            return self.properties_path

        dot_mia_config = os.path.expanduser(
            "~/.populse_mia/configuration_path.yml"
        )

        try:

            with open(dot_mia_config) as stream:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    mia_home_properties_path = yaml.load(
                        stream, Loader=yaml.FullLoader
                    )

                else:
                    mia_home_properties_path = yaml.load(stream)

        except yaml.YAMLError as e:
            logger.warning(f"{e}")
            logger.warning(
                "~/.populse_mia/configuration_path.yml cannot be read, the "
                "path to the properties folder has not been found.."
            )
            raise

        # Patch for obsolete parameters.
        updated = False

        for old_key, new_key in [
            ("mia_path", "properties_user_path"),
            ("mia_user_path", "properties_user_path"),
        ]:

            if old_key in mia_home_properties_path:
                mia_home_properties_path[new_key] = (
                    mia_home_properties_path.pop(old_key)
                )
                updated = True

        if updated:

            with open(dot_mia_config, "w", encoding="utf-8") as configfile:
                yaml.dump(
                    mia_home_properties_path,
                    configfile,
                    default_flow_style=False,
                    allow_unicode=True,
                )

        try:
            key = (
                "properties_dev_path"
                if self.dev_mode
                else "properties_user_path"
            )
            self.properties_path = os.path.join(
                mia_home_properties_path[key],
                "dev" if self.dev_mode else "usr",
            )
            return self.properties_path

        except KeyError as e:
            logger.warning(f"{e}")
            logger.warning(
                "Key not found in ~/.populse_mia/configuration_path.yml!"
            )
            raise

    def get_referential(self):
        """
        Retrieves the chosen referential from the anatomist_2 data viewer.

        :returns: "0" for World Coordinates, "1" for Image ref.
        :rtype: str
        """
        return self.config.get("ref", "0")

    def get_resources_path(self):
        """Get the resources path.

        :returns: A path.
        :rtype: str
        """
        return self.config.get("resources_path", "")

    def getShowAllSlices(self):
        """
        Get whether the show_all_slices parameters was enabled or not in
        the miniviewer.

        :returns: True if the ``show_all_slices`` parameters was enabled.
        :rtype: bool
        """
        return self.config.get("show_all_slices", False)

    def getSourceImageDir(self):
        """Get the source directory for project images.

        :returns: A path.
        :rtype: str
        """
        return self.config.get("source_image_dir", "")

    def get_spm_path(self):
        """Get the path of SPM.

        :returns: A path.
        :rtype: str
        """
        return self.config.get("spm", "")

    def get_spm_standalone_path(self):
        """Get the path to the SPM12 standalone version.

        :returns: A path.
        :rtype: str
        """
        return self.config.get("spm_standalone", "")

    def getTextColor(self):
        """Get the text color.

        :returns: The text color.
        :rtype: str
        """
        return self.config.get("text_color", "")

    def getThumbnailTag(self):
        """Get the tag of the thumbnail displayed in the miniviewer.

        :returns: The tag of the thumbnail displayed in miniviewer.
        :rtype: str
        """
        return self.config.get("thumbnail_tag", "SequenceName")

    def get_use_afni(self):
        """Get the value of "use afni" checkbox in the preferences.

        :returns: The value of "use afni" checkbox.
        :rtype: bool
        """
        return self.config.get("use_afni", False)

    def get_use_ants(self):
        """Get the value of "use ants" checkbox in the preferences.

        :returns: The value of "use ants" checkbox.
        :rtype: bool
        """
        return self.config.get("use_ants", False)

    def get_use_clinical(self):
        """Get the clinical mode in the preferences.

        :returns: The clinical mode.
        :rtype: bool
        """
        return self.config.get("clinical_mode", False)

    def get_use_freesurfer(self):
        """Get the value of "use freesurfer" checkbox in the preferences.

        :returns: The value of "use freesurfer" checkbox.
        :rtype: bool
        """
        return self.config.get("use_freesurfer", False)

    def get_use_fsl(self):
        """Get the value of "use fsl" checkbox in the preferences.

        :returns: The value of "use fsl" checkbox.
        :rtype: bool
        """
        return self.config.get("use_fsl", False)

    def get_use_matlab(self):
        """Get the value of "use matlab" checkbox in the preferences.

        :returns: The value of "use matlab" checkbox.
        :rtype: bool
        """
        return self.config.get("use_matlab", False)

    def get_use_matlab_standalone(self):
        """
        Get the value of "use matlab standalone" checkbox in the preferences.

        :returns: The value of "use matlab standalone" checkbox.
        :rtype: bool
        """
        return self.config.get("use_matlab_standalone", False)

    def get_use_mrtrix(self):
        """Get the value of "use mrtrix" checkbox in the preferences.

        :returns: The value of "use mrtrix" checkbox.
        :rtype: bool
        """
        return self.config.get("use_mrtrix", False)

    def get_user_level(self):
        """Get the user level in the Capsul config.

        :returns: The user level in the Capsul config.
        :rtype: int
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

        :returns: If True, the user mode is enabled.
        :rtype: bool
        """
        return self.config.get("user_mode", True)

    def get_use_spm(self):
        """Get the value of "use spm" checkbox in the preferences.

        :returns: The value of "use spm" checkbox.
        :rtype: bool
        """
        return self.config.get("use_spm", False)

    def get_use_spm_standalone(self):
        """Get the value of "use spm standalone" checkbox in the preferences.

        :returns: The value of "use spm standalone" checkbox.
        :rtype: bool
        """
        return self.config.get("use_spm_standalone", False)

    def getViewerConfig(self):
        """Get the viewer config ``neuro`` or ``radio``, ``neuro`` by default.

        :returns: The viewer config (``neuro`` or ``radio``).
        :rtype: str
        """
        return self.config.get("config_NeuRad", "neuro")

    def getViewerFramerate(self):
        """Get the Viewer framerate.

        :returns: The Viewer framerat (ex. "5").
        :rtype: str
        """
        return self.config.get("im_sec", "5")

    def isAutoSave(self):
        """Get if the auto-save mode is enabled or not.

        :returns: If True, auto-save mode is enabled.
        :rtype: bool
        """
        return self.config.get("auto_save", False)

    def isControlV1(self):
        """
        Gets whether the controller display is of type V1.

        :returns: If True, V1 controller display.
        :rtype: bool
        """
        return self.config.get("control_V1", False)

    def isRadioView(self):
        """
        Get if the display in miniviewer is in radiological orientation.

        :returns: If True, radiological orientation, otherwise neurological
            orientation.
        :rtype: bool
        """
        return self.config.get("radio_view", True)

    def loadConfig(self):
        """Read the config from config.yml file.

         Attempts to read an encrypted YAML configuration file from the
         properties directory, decrypt it using Fernet encryption, and
         parse it as YAML.

        :returns: Parsed configuration from the YAML file. Returns empty dict
            if parsing fails.
        :rtype: dict
        """
        fernet = Fernet(ENCRYPTION_KEY)
        config_path = (
            Path(self.get_properties_path()) / "properties" / "config.yml"
        )

        if not config_path.exists():
            raise yaml.YAMLError(
                f"\nThe configuration file '{config_path}' doesn't "
                f"exist or is corrupted...\n"
            )

        try:
            encrypted_data = config_path.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)

            # For YAML versions >= 5.1, use FullLoader for better security
            if verCmp(yaml.__version__, "5.1", "sup"):
                return yaml.load(decrypted_data, Loader=yaml.FullLoader)

            else:
                # Loader parameter not available in older versions
                return yaml.load(decrypted_data)

        except yaml.YAMLError as exc:
            logger.warning(f"Error loading '{config_path}' file: {exc}")
            return {}

    def saveConfig(self):
        """
        Save the current parameters in the config.yml file.

        Encrypts and writes the current configuration (self.config) to
        config.yml using Fernet encryption. Creates the necessary directory
        structure if it doesn't exist. After saving, updates the capsul
        configuration.
        """
        config_path = (
            Path(self.get_properties_path()) / "properties" / "config.yml"
        )
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        fernet = Fernet(ENCRYPTION_KEY)
        yaml_data = yaml.dump(
            self.config, default_flow_style=False, allow_unicode=True
        )
        encrypted_data = fernet.encrypt(yaml_data.encode())
        # Write encrypted configuration
        config_path.write_bytes(encrypted_data)
        self.update_capsul_config()

    def set_admin_hash(self, admin_hash):
        """
        Set the administrator password hash.

        :param admin_hash: The hashed administrator password to store in the
            configuration.
        :type admin_hash: str
        """
        self.config["admin_hash"] = admin_hash
        # Then save the modification
        self.saveConfig()

    def set_afni_path(self, path):
        """Set the AFNI path.

        :param path: A path.
        :type path: str
        """
        self.config["afni"] = path
        # Then save the modification
        self.saveConfig()

    def set_ants_path(self, path):
        """Set the ANTS path

        :param path: A path.
        :type path: str
        """
        self.config["ants"] = path
        # Then save the modification
        self.saveConfig()

    def setAutoSave(self, save):
        """Set the automatic saving mode.

        :param save: ``True`` to enable automatic saving, ``False`` to disable
            it.
        :type save: bool
        """
        self.config["auto_save"] = save
        # Then save the modification
        self.saveConfig()

    def setBackgroundColor(self, color):
        """Set background color and save configuration.

        :param color: Color string ('Black', 'Blue', 'Green', 'Grey', 'Orange',
         'Red', 'Yellow', 'White')
        :type color: str
        """
        self.config["background_color"] = color
        # Then save the modification
        self.saveConfig()

    def set_capsul_config(self, capsul_config_dict):
        """
        Update Mia configuration with Capsul settings and synchronize tools
        configuration.

        Called after editing Capsul config (via File > Mia preferences >
        Pipeline tab > Edit CAPSUL config) to synchronize Capsul settings
        with Mia preferences. Configures various neuroimaging tools
        (AFNI, ANTs, FSL, etc.) based on the Capsul engine configuration.

        :param capsul_config_dict: Dictionary containing Capsul configuration.
        :type capsul_config_dict: dict

        Structure of capsul_config_dict::

            {
                'engine': {
                    'environment_name': {...configuration...}
                },
                'engine_modules': [...]
            }

        Contains:
            Inner functions:
                - _get_module_config: Extracts module configuration from the
                  global Capsul configuration.
        """

        def _get_module_config(module_name: str) -> dict:
            """
            Extracts the configuration for a specific module from the global
            Capsul configuration.

            :param module_name: The name of the module to retrieve the
                configuration for.
            :type module_name: str

            :returns: The configuration dictionary of the specified module, or
                an empty dictionary if not found.
            :rtype: dict
            """
            module_path = f"capsul.engine.module.{module_name}"
            module_config = global_config.get(module_path, {})
            # TODO: we only take the first element of the dictionary (the one
            #       that is normally edited in the Capsul config GUI). There is
            #       actually a problem because this means that there may be
            #       hidden config(s) ... This can produce bugs and at least
            #       unpredictable results for the user ...
            return next(iter(module_config.values())) if module_config else {}

        self.config["capsul_config"] = capsul_config_dict

        # Initialize new engine and import configurations
        new_engine = capsul_engine()
        engine_config = capsul_config_dict.get("engine", {})

        for environment, config in engine_config.items():

            if environment != "capsul_engine":
                new_engine.import_configs(environment, config)

        global_config = new_engine.settings.export_config_dict("global").get(
            "global", {}
        )

        # Configure simple tools (AFNI, ANTs, MRtrix)
        for tool in ["afni", "ants", "mrtrix"]:
            config = _get_module_config(tool)
            directory = config.get("directory")
            use_tool = bool(directory)

            if directory:
                getattr(self, f"set_{tool}_path")(directory)

            getattr(self, f"set_use_{tool}")(use_tool)

        # Configure Freesurfer
        freesurfer_config = _get_module_config("freesurfer")
        setup_path = freesurfer_config.get("setup")
        use_freesurfer = bool(setup_path)

        if setup_path:
            self.set_freesurfer_setup(setup_path)

        self.set_use_freesurfer(use_freesurfer)

        # Configure FSL
        fsl_config = _get_module_config("fsl")
        fsl_conf_path = fsl_config.get("config")
        fsl_dir_path = fsl_config.get("directory")
        use_fsl = False

        if fsl_conf_path:
            use_fsl = True
            self.set_fsl_config(fsl_conf_path)

        # If only the directory parameter has been set, let's try using
        # the config parameter = directory/etc/fslconf/fsl.sh:
        elif fsl_dir_path:
            default_conf = Path(fsl_dir_path) / "etc" / "fslconf" / "fsl.sh"

            if default_conf.is_file():
                use_fsl = True
                self.set_fsl_config(str(default_conf))

            else:
                logger.warning(
                    f"Could not determine FSL configuration file from "
                    f"directory {fsl_dir_path}. FSL is not correctly defined "
                    f"in preferences (see File > Mia Preferences)."
                )

        self.set_use_fsl(use_fsl)

        # Configure MATLAB/SPM
        matlab_config = _get_module_config("matlab")
        spm_config = _get_module_config("spm")
        matlab_path = matlab_config.get("executable")
        mcr_dir = matlab_config.get("mcr_directory")
        spm_dir = spm_config.get("directory")
        use_spm_standalone = spm_config.get("standalone", False)
        use_matlab = bool(matlab_path) and Path(matlab_path).is_file()
        use_mcr = bool(mcr_dir) and Path(mcr_dir).is_dir()
        spm_dir_valid = bool(spm_dir) and Path(spm_dir).is_dir()

        # Determine configuration mode
        if spm_dir_valid and use_mcr and use_spm_standalone:
            self._configure_standalone_spm(spm_dir, mcr_dir)

        elif spm_dir_valid and use_matlab and not use_spm_standalone:
            self._configure_matlab_spm(spm_dir, matlab_path)

        elif use_matlab:
            self._configure_matlab_only(matlab_path)

        elif use_mcr:
            self._configure_mcr_only(mcr_dir)

        else:
            self._disable_matlab_spm()

        # TODO: Because there are two parameters for matlab (executable and
        #  mcr_directory) in Capsul config, if the user defines both, we don't
        #  know which on to choose! Here we choose to favour matlab in front
        #  of MCR if both are chosen, is it desirable?
        if (
            use_matlab
            and use_mcr
            and not (use_spm_standalone or bool(spm_dir))
        ):
            logger.info(
                "Both Matlab executable and MCR directory are set in Capsul "
                "configuration. Defaulting to Matlab over MCR."
            )

        self.update_capsul_config()

    def setChainCursors(self, chain_cursors):
        """Enable or disable cursor synchronization in the mini viewer.

        :param chain_cursors: ``True`` to synchronize the cursors across the
            mini viewer, ``False`` otherwise.
        :type chain_cursors: bool
        """
        self.config["chain_cursors"] = chain_cursors
        # Then save the modification
        self.saveConfig()

    def set_clinical_mode(self, clinical_mode):
        """Enable or disable clinical mode.

        :param clinical_mode: ``True`` to enable clinical mode, ``False`` to
            disable it.
        :type clinical_mode: bool
        """
        self.config["clinical_mode"] = clinical_mode
        # Then save the modification
        self.saveConfig()

    def setControlV1(self, controlV1):
        """Set the controller display mode.

        :param controlV1: ``True`` to use the V1 controller display mode,
            ``False`` to use the alternative mode (V2).
        :type controlV1: bool
        """
        self.config["control_V1"] = controlV1
        # Then save the modification
        self.saveConfig()

    def set_freesurfer_setup(self, path):
        """Set the freesurfer config file.

        :param path: Path to freesurfer/FreeSurferEnv.sh.
        :type path: str
        """
        self.config["freesurfer_setup"] = path
        # Then save the modification
        self.saveConfig()

    def set_fsl_config(self, path):
        """Set the FSL config file.

        :param path: Path to fsl/etc/fslconf/fsl.sh.
        :type path: str
        """
        self.config["fsl_config"] = path
        # Then save the modification
        self.saveConfig()

    def set_mainwindow_maximized(self, enabled):
        """Set whether the main window is maximized.

        :param enabled: Whether the main window should be maximized.
        :type enabled: bool
        """
        self.config["mainwindow_maximized"] = enabled
        self.saveConfig()

    def set_mainwindow_size(self, size):
        """Set main window size.

        :param size: A list of two integers.
        :type size: list[int]
        """
        self.config["mainwindow_size"] = list(size)
        self.saveConfig()

    def set_matlab_path(self, path):
        """Set the path of Matlab's executable.

        :param path: Path to Matlab's executable.
        :type path: str
        """
        self.config["matlab"] = path
        # Then save the modification
        self.saveConfig()

    def set_matlab_standalone_path(self, path):
        """Set the path of Matlab Compiler Runtime.

        :param path: Path to Matlab Compiler Runtime.
        :type path: str
        """
        self.config["matlab_standalone"] = path
        # Then save the modification
        self.saveConfig()

    def set_max_projects(self, nb_max_projects):
        """
        Set the maximum number of recent projects shown in the "Saved projects"
        menu.

        :param nb_max_projects: Maximum number of recent projects to display.
        :type nb_max_projects: int
        """
        self.config["max_projects"] = nb_max_projects
        # Then save the modification
        self.saveConfig()

    def set_max_thumbnails(self, nb_max_thumbnails):
        """
        Set the maximum number of thumbnails displayed at the bottom of the
        Data Browser.

        :param nb_max_thumbnails: Maximum number of thumbnails to display.
        :type nb_max_thumbnails: int
        """
        self.config["max_thumbnails"] = nb_max_thumbnails
        # Then save the modification
        self.saveConfig()

    def set_mri_conv_path(self, path):
        """Set the MRIManager.jar path.

        :param path: A path.
        :type path: str
        """
        self.config["mri_conv_path"] = path
        # Then save the modification
        self.saveConfig()

    def set_mrtrix_path(self, path):
        """Set the mrtrix path.

        :param path: A path.
        :type path: str
        """
        self.config["mrtrix"] = path
        # Then save the modification
        self.saveConfig()

    def setNbAllSlicesMax(self, nb_slices_max):
        """Set the number of slices to display in the mini-viewer.

        :param nb_slices_max: Maximum number of slices to display.
        :type nb_slices_max: int
        """
        self.config["nb_slices_max"] = nb_slices_max
        # Then save the modification
        self.saveConfig()

    def set_opened_projects(self, new_projects):
        """Set the list of opened projects and saves the modification.

        :param new_projects: A list of paths.
        :type new_projects: list[str]
        """
        self.config["opened_projects"] = new_projects
        # Then save the modification
        self.saveConfig()

    def set_projects_save_path(self, path):
        """Set the folder where the projects are saved.

        :param path: A path.
        :type path: str
        """
        self.config["projects_save_path"] = path
        # Then save the modification
        self.saveConfig()

    def set_radioView(self, radio_view):
        """Set the orientation displayed in the mini viewer.

        :param radio_view: If ``True``, use the radiological orientation;
            otherwise, use the neurological orientation.
        :type radio_view: bool
        """
        self.config["radio_view"] = radio_view
        # Then save the modification
        self.saveConfig()

    def set_referential(self, ref):
        """
        Set the referential to ``image Ref`` or ``World Coordinates`` in
        anatomist_2 data viewer.

        :param ref: "0" for ``World Coordinates``, "1" for ``Image Ref``.
        :type ref: str
        """
        self.config["ref"] = ref
        # Then save the modification
        self.saveConfig()

    def set_resources_path(self, path):
        """Set the resources path.

        :param path: A path.
        :type path: str
        """
        self.config["resources_path"] = path
        # Then save the modification
        self.saveConfig()

    def setShowAllSlices(self, show_all_slices):
        """Set whether all slices are displayed in the mini viewer.

        :param show_all_slices: If ``True``, display all slices; otherwise,
            display only the selected slice.
        :type show_all_slices: bool
        """
        self.config["show_all_slices"] = show_all_slices
        # Then save the modification
        self.saveConfig()

    def setSourceImageDir(self, source_image_dir):
        """Set the source directory for project images.

        :param source_image_dir: A path.
        :type source_image_dir: str
        """
        self.config["source_image_dir"] = source_image_dir
        # Then save the modification
        self.saveConfig()

    def set_spm_path(self, path):
        """Set the path of SPM (MATLAB license version).

        :param path: A path.
        :type path: str
        """
        self.config["spm"] = path
        # Then save the modification
        self.saveConfig()

    def set_spm_standalone_path(self, path):
        """Set the path of SPM (standalone version).

        :param path: A path.
        :type path: str
        """
        self.config["spm_standalone"] = path
        # Then save the modification
        self.saveConfig()

    def setTextColor(self, color):
        """Set text color and save configuration.

        :param color: Color string ('Black', 'Blue', 'Green', 'Grey', 'Orange',
         'Red', 'Yellow', 'White').
        :type color: str
        """
        self.config["text_color"] = color
        # Then save the modification
        self.saveConfig()

    def setThumbnailTag(self, thumbnail_tag):
        """Set the tag displayed in the mini viewer for thumbnails.

        :param thumbnail_tag: Name of the tag to display.
        :type thumbnail_tag: str
        """
        self.config["thumbnail_tag"] = thumbnail_tag
        # Then save the modification
        self.saveConfig()

    def set_use_afni(self, use_afni):
        """Set whether AFNI support is enabled in the preferences.

        :param use_afni: If ``True``, enable AFNI support; otherwise, disable
            it.
        :type use_afni: bool
        """
        self.config["use_afni"] = use_afni
        # Then save the modification
        self.saveConfig()

    def set_use_ants(self, use_ants):
        """Set whether ANTs support is enabled in the preferences.

        :param use_ants: If ``True``, enable ANTs support; otherwise, disable
            it.
        :type use_ants: bool
        """
        self.config["use_ants"] = use_ants
        # Then save the modification
        self.saveConfig()

    def set_use_freesurfer(self, use_freesurfer):
        """Set whether FreeSurfer support is enabled in the preferences.

        :param use_freesurfer: If ``True``, enable FreeSurfer support;
            otherwise, disable it.
        :type use_freesurfer: bool
        """
        self.config["use_freesurfer"] = use_freesurfer
        # Then save the modification
        self.saveConfig()

    def set_use_fsl(self, use_fsl):
        """Set whether FSL support is enabled in the preferences.

        :param use_fsl: If ``True``, enable FSL support; otherwise, disable it.
        :type use_fsl: bool
        """
        self.config["use_fsl"] = use_fsl
        # Then save the modification
        self.saveConfig()

    def set_use_matlab(self, use_matlab):
        """Set whether Matlab support is enabled in the preferences.

        :param use_matlab: If ``True``, enable Matlab support; otherwise,
            disable it.
        :type use_matlab: bool
        """
        self.config["use_matlab"] = use_matlab
        # Then save the modification
        self.saveConfig()

    def set_use_matlab_standalone(self, use_matlab_standalone):
        """Set whether Matlab standalone support is enabled in the preferences.

        :param use_matlab_standalone: If ``True``, enable Matlab standalone
            support; otherwise, disable it.
        :type use_matlab_standalone: bool
        """
        self.config["use_matlab_standalone"] = use_matlab_standalone
        # Then save the modification
        self.saveConfig()

    def set_use_mrtrix(self, use_mrtrix):
        """Set whether MRtrix support is enabled in the preferences.

        :param use_mrtrix: If ``True``, enable MRtrix support; otherwise,
            disable it.
        :type use_mrtrix: bool
        """
        self.config["use_mrtrix"] = use_mrtrix
        # Then save the modification
        self.saveConfig()

    def set_user_mode(self, user_mode):
        """Enable or disable user mode.

        :param user_mode: If ``True``, enable user mode; otherwise, disable it.
        :type user_mode: bool
        """
        self.config["user_mode"] = user_mode
        # Then save the modification
        self.saveConfig()

    def set_use_spm(self, use_spm):
        """Set whether SPM support is enabled in the preferences.

        :param use_spm: If ``True``, enable SPM support; otherwise, disable it.
        :type use_spm: bool
        """
        self.config["use_spm"] = use_spm
        # Then save the modification
        self.saveConfig()

    def set_use_spm_standalone(self, use_spm_standalone):
        """Set whether SPM standalone support is enabled in the preferences.

        :param use_spm_standalone: If ``True``, enable SPM standalone support;
            otherwise, disable it.
        :type use_spm_standalone: bool
        """
        self.config["use_spm_standalone"] = use_spm_standalone
        # Then save the modification
        self.saveConfig()

    def setViewerConfig(self, config_NeuRad):
        """Set the orientation convention used by the data viewer.

        :param config_NeuRad: Orientation convention. Accepted values are
            ``"neuro"`` for neurological orientation and ``"radio"`` for
            radiological orientation.
        :type config_NeuRad: str
        """
        self.config["config_NeuRad"] = config_NeuRad
        # Then save the modification
        self.saveConfig()

    def setViewerFramerate(self, im_sec):
        """Set the framerate for the data viewer.

        :param im_sec: Number of images per second.
        :type im_sec: int
        """
        self.config["im_sec"] = im_sec
        # Then save the modification
        self.saveConfig()

    def update_capsul_config(self):
        """
        Updates the global CapsulEngine object used for all operations in
        the Mia application.

        The CapsulEngine is created once when needed and updated each time
        the configuration is saved. This method ensures that all necessary
        engine modules are loaded and configurations are properly imported
        from the saved settings.

        :returns: The updated CapsulEngine object, or None if the engine is not
            initialized.
        :rtype: capsul.engine.CapsulEngine | None
        """

        if self.capsul_engine is None:
            # Avoid unnecessary updates before the config is actually used
            return

        capsul_config = self.get_capsul_config(sync_from_engine=False)
        engine = Config.capsul_engine
        modules = capsul_config.get("engine_modules", []) + [
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
        ]

        for module in modules:
            engine.load_module(module)

        engine_config = capsul_config.get("engine", {})

        for environment, config in engine_config.items():
            config_copy = dict(config)

            if (
                "capsul_engine" not in config_copy
                or "uses" not in config_copy["capsul_engine"]
            ):
                config_copy["capsul_engine"] = {
                    "uses": {
                        engine.settings.module_name(m): "ALL" for m in config
                    }
                }

            try:
                engine.import_configs(
                    environment, config_copy, cont_on_error=True
                )

            except Exception as exc:
                logger.warning("An issue was detected in MIA's configuration:")
                logger.warning(f"{exc}")
                logger.warning(
                    "Please check the settings in File > "
                    "Mia Preferences > Pipeline ..."
                )

        return engine
