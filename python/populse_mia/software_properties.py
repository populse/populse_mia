# -*- coding: utf-8 -*- #
"""Module that handle the configuration of the software

Load and save the parameters from the miniviewer and the MIA preferences
pop-up in the config.yml file.

:Contains:
    :Class:
        - Config
    :Function:
        - verCmp

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import os
import platform
import yaml
import re
import glob
from cryptography.fernet import Fernet

CONFIG = b'5YSmesxZ4ge9au2Bxe7XDiQ3U5VCdLeRdqimOOggKyc='


def verCmp(first_ver, sec_ver, comp):
    """Version comparator.

    The verCmp() function returns a boolean value to indicate whether its
    first argument (first_ver) is equal to, less or equal to, or greater or
    equal to its second argument (sec_ver), as follows:
      - if third argument (comp) is 'eq': when the first argument is equal to the
        second argument, return True (False if not).
      - if third argument (comp) is 'sup': when the first argument is greater
        than the second argument, return True (False if not).
      - if third argument (comp) is 'inf': when the first argument is less than
        the second argument, return True (False if not).

    :param first_ver: the version of a package (a string; ex. '0.13.0')
    :param sec_ver: the version of a package (a string; ex. '0.13.0')
    :param comp: comparator argument (accepted values: 'sup', 'inf' and 'eq' )

    :returns: False or True

    :Contains:
      Private function:
        - normalise

     """

    def normalise(v):
        """Transform a version of a package to a corresponding list of integer.

        :returns: a list of integer (ex. [0, 13, 0])

        """
        v = re.sub("[^0-9\.]", "", v)
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]

    if comp == 'eq':

        if normalise(first_ver) == normalise(sec_ver):
            return True

        else:
            return False

    elif comp == 'sup':

        if (normalise(first_ver) > normalise(sec_ver)) or (
        verCmp(first_ver, sec_ver, 'eq')):
            return True

        else:
            return False

    elif comp == 'inf':

        if (normalise(first_ver) < normalise(sec_ver)) or (
        verCmp(first_ver, sec_ver, 'eq')):
            return True

        else:
            return False


class Config:
    """
    Object that handles the configuration of the software

    .. Methods:
        - get_admin_hash: get the value of the hash of the admin password
        - getBackgroundColor: get background color
        - get_capsul_config: get CAPSUL config dictionary
        - get_capsul_engine: get a global CapsulEngine object used for all
          operations in MIA application
        - getChainCursors: returns if the "chain cursors" checkbox of the
          mini viewer is activated
        - get_config_path: returns the configuration file directory
        - get_mainwindow_maximized: get the maximized (fullscreen) flag
        - get_mainwindow_size: get the main window size
        - get_matlab_command: returns Matlab command
        - get_matlab_path: returns the path of Matlab's executable
        - get_matlab_standalone_path: returns the path of Matlab Compiler
          Runtime
        - get_max_projects: returns the maximum number of projects displayed in
          the "Saved projects" menu
        - get_mia_path: returns the software's install path
        - get_mri_conv_path: sets the MRIManager.jar path
        - getNbAllSlicesMax: returns the maximum number of slices to display in
          the mini viewer
        - get_opened_projects: returns the opened projects
        - getPathToProjectsFolder: returns the project's path
        - get_projects_save_path: returns the folder where the projects are
          saved
        - getShowAllSlices: returns if the "show all slices" checkbox of the
          mini viewer is activated
        - getSourceImageDir: get the source directory for project images
        - get_spm_path: returns the path of SPM12 (license version)
        - get_spm_standalone_path: returns the path of SPM12 (standalone
          version)
        - getTextColor: return the text color
        - getThumbnailTag: returns the tag that is displayed in the mini viewer
        - get_use_matlab: returns the value of "use matlab" checkbox in the
          preferences
        - get_use_matlab_standalone: returns the value of "use matlab
          standalone" checkbox in the preferences
        - get_user_level: get the user level in the Capsul config
        - get_user_mode: returns the value of "user mode" checkbox
          in the preferences
        - get_use_spm: returns the value of "use spm" checkbox in the
          preferences
        - get_use_spm_standalone: returns the value of "use spm standalone"
          checkbox in the preferences
        - getPathData: returns the data's path (currently commented)
        - getPathToProjectsDBFile: returns the already-saved projects's path
          (currently commented)
        - isAutoSave: checks if auto-save mode is activated
        - loadConfig: reads the config in the config.yml file
        - saveConfig: saves the config to the config.yml file
        - set_admin_hash: set the password hash
        - setAutoSave: sets the auto-save mode
        - setBackgroundColor: sets the background color
        - set_capsul_config: set CAPSUL configuration dict into MIA config
        - setChainCursors: set the "chain cursors" checkbox of the mini viewer
        - set_mainwindow_maximized: set the maximized (fullscreen) flag
        - set_mainwindow_size: set main window size
        - set_matlab_path: set the path of Matlab's executable
        - set_matlab_standalone_path: set the path of Matlab Compiler Runtime
        - set_max_projects: set the maximum number of projects displayed in
          the "Saved projects" menu
        - set_mri_conv_path: set the MRIManager.jar path
        - setNbAllSlicesMax: set the maximum number of slices to display in
          the mini viewer
        - set_opened_projects: set the opened projects
        - set_projects_save_path: set the folder where the projects are saved
        - setShowAllSlices: set the "show all slices" checkbox of the mini
          viewer
        - setSourceImageDir: set the source directory for project images
        - set_spm_path: set the path of SPM12 (license version)
        - set_spm_standalone_path: set the path of SPM12 (standalone version)
        - setTextColor: set the text color
        - setThumbnailTag: set the tag that is displayed in the mini viewer
        - set_use_matlab: set the value of "use matlab" checkbox in the
          preferences
        - set_use_matlab_standalone: set the value of "use matlab standalone"
          checkbox in the preferences
        - set_user_mode: set the value of "user mode" checkbox in
          the preferences
        - set_use_spm: set the value of "use spm" checkbox in the preferences
        - set_use_spm_standalone: set the value of "use spm standalone"
          checkbox in the preferences
        - set_mia_path: set the software's install path (currently commented)
        - setPathToData: set the data's path (currently commented)
        - update_capsul_config: update a global CapsulEngine object used for
          all operations in MIA application


    """
    capsul_engine = None

    def __init__(self, config_path=None, load=True):
        """Initialization of the Config class

        :Parameters:
            - :config_path: str (optional). If provided, the configuration file
               will be loaded/saved from the given directory. Otherwise the
               regular eutristics will be used to determine the config path.
               This option allows to use an alternative config directory (for
               tests for instance).
        """
        self.dev_mode = False
        if config_path is not None:
            self.config_path = config_path
        self.config = self.loadConfig()
        if "mia_user_path" not in self.config.keys():
            self.config["mia_user_path"] = self.get_mia_path()
            self.saveConfig()

    def get_admin_hash(self):
        """Get the value of the hash of the admin password.

        :return: string

        """
        try:
            return self.config["admin_hash"]
        except KeyError:
            return False

    def get_capsul_config(self, sync_from_engine=True):
        """Get CAPSUL config dictionary
        """
        capsul_config = self.config.setdefault("capsul_config", {})
        capsul_config.setdefault(
            "engine_modules",
            ['nipype', 'fsl', 'freesurfer', 'matlab', 'spm', 'fom', 'python'])
        sconf = capsul_config.setdefault("study_config", {})
        sconf.update(
            {'attributes_schema_paths':
                ['capsul.attributes.completion_engine_factory',
                 'populse_mia.user_interface.pipeline_manager.process_mia'],
            'process_completion': 'mia_completion'})

        # update study config from mia config values
        spm_standalone_path = self.get_spm_standalone_path()
        spm_path = self.get_spm_path()
        matlab_path = self.get_matlab_path()
        matlab_standalone_path = self.get_matlab_standalone_path()
        use_spm = self.get_use_spm()
        use_spm_standalone = self.get_use_spm_standalone()
        use_matlab = self.get_use_matlab()

        if use_spm_standalone and os.path.exists(
                spm_standalone_path) and os.path.exists(
                    matlab_standalone_path):

            spm_exec = glob.glob(os.path.join(spm_standalone_path,
                                              'run_spm*.sh'))
            if spm_exec:
                spm_exec = spm_exec[0]
                sconf['spm_exec'] = spm_exec

            if use_matlab and matlab_path and os.path.exists(matlab_path):

                sconf.update(dict(
                    use_spm=True,
                    spm_directory=spm_standalone_path,
                    matlab_exec=matlab_path,
                    spm_standalone=True))
            else:
                sconf.update(dict(
                    use_spm=True, spm_directory=spm_standalone_path,
                    spm_standalone=True))

        # Using without SPM standalone
        elif use_spm and use_matlab:
            sconf.update(dict(
                use_spm=True, matlab_exec=matlab_path,
                spm_directory=spm_path, spm_standalone=False,
                use_matlab=True))
        else:
            sconf.update(dict(use_spm=False))

        if sync_from_engine and self.capsul_engine:
            econf = capsul_config.setdefault('engine', {})
            for environment in \
                    self.capsul_engine.settings.get_all_environments():
                eeconf = econf.setdefault(environment, {})
                # would need a better merging system
                eeconf.update(
                    self.capsul_engine.settings.select_configurations(
                        environment))

        return capsul_config

    @staticmethod
    def get_capsul_engine():
        """
        Get a global CapsulEngine object used for all operations in MIA
        application. The engine is created once when needed.
        """
        from capsul.api import capsul_engine

        config = Config()
        capsul_config = config.get_capsul_config()

        if Config.capsul_engine is None:
            Config.capsul_engine = capsul_engine()
            Config().update_capsul_config()

        return Config.capsul_engine

    def update_capsul_config(self):
        """
        Update a global CapsulEngine object used for all operations in MIA
        application. The engine is created once when needed, and updated
        each time the config is saved.
        """
        if self.capsul_engine is None:
            # don't do anything until the config is really created: this
            # avoids unneeded updates before it is actually used.
            return

        capsul_config = self.get_capsul_config(sync_from_engine=False)
        engine = Config.capsul_engine

        for module in capsul_config.get('engine_modules', []) \
                + ['fom', 'nipype', 'python', 'fsl', 'freesurfer', 'axon']:
            engine.load_module(module)

        study_config = engine.study_config
        study_config.import_from_dict(capsul_config.get('study_config', {}))

        engine_config = capsul_config.get('engine')
        if engine_config:
            for environment, config in engine_config.items():
                c = dict(config)
                if 'capsul_engine' not in c \
                        or 'uses' not in c['capsul_engine']:
                    c['capsul_engine'] = {
                        'uses': {engine.settings.module_name(m): 'ALL'
                                  for m in config.keys()}}
                for mod, val in config.items():
                    if 'config_id' not in val:
                        val['config_id'] = mod.split('.')[-1]
                engine.import_configs(environment, c)

        return engine


    def get_user_mode(self):
        """Get if user mode is disabled or enabled in the preferences.

        :return: boolean

        """
        return self.config.get("user_mode", False)

    def get_user_level(self):
        """Get the user level in the Capsul config

        Returns
        -------
        userlevel: int
        """
        return self.config.get("capsul_config", {}).get(
            "engine", {}).get("global", {}).get(
              'capsul.engine.module.axon', {}).get('user_level', 0)

    def get_mainwindow_maximized(self):
        """Get the maximized (fullscreen) flag
        """

        return self.config.get('mainwindow_maximized', True)

    def get_mainwindow_size(self):
        """Get the main window size
        """

        return self.config.get('mainwindow_size', None)

    def get_matlab_command(self):
        """Get Matlab command.

        :return: Returns path to matlab executable or nothing if matlab
                 path not specified

        """
        if self.config.get("use_spm_standalone"):
            archi = platform.architecture()
            if 'Windows' in archi[1]:
                spm_script = glob.glob(os.path.join(self.config["spm_standalone"],
                                                    'spm*_win' + archi[0][:2] + '.exe'))
            else:
                spm_script = glob.glob(os.path.join(self.config["spm_standalone"],
                                                    'run_spm*.sh'))
            if spm_script:
                spm_script = spm_script[0]
                return '{0} {1} script'.format(
                    spm_script, self.config["matlab_standalone"])
            else:
                return ''  # will not work.
        else:
            return self.config.get("matlab", None)

    def get_matlab_path(self):
        """Get the path to the matlab executable.

        :return: String of path

        """
        return self.config.get("matlab", "")

    def get_matlab_standalone_path(self):
        """Get the path to matlab compiler runtime.

        :return: string of path

        """
        return self.config.get("matlab_standalone", "")

    def get_max_projects(self):
        """Get the maximum number of projects displayed in the "Saved
        projects" menu.

        :return: Integer

        """
        try:
            return int(self.config["max_projects"])
        except KeyError as e:
            return 5

    def get_mia_path(self):
        """Get the path to the folder containing the processes, properties
        and resources folders of mia (mia_path).

        During the mia installation, the mia_path is defined and stored in the
        configuration.yml file, located in the .populse_mia folder (himself
        located in the user's home). If mia is launched in admin mode,
        mia path is the cloned git repository. If mia is launched in user
        mode, mia path must compulsorily be returned from the mia_path
        parameter of the configuration.yml

        :return: string of path to mia folder

        """
        mia_path = getattr(self, 'mia_path', None)
        if mia_path:
            return mia_path
        dot_mia_config = os.path.join(os.path.expanduser("~"),
                                      ".populse_mia", "configuration.yml")

        if os.path.isfile(dot_mia_config):

            with open(dot_mia_config, 'r') as stream:

                try:
                    if verCmp(yaml.__version__, '5.1', 'sup'):
                        mia_home_config = yaml.load(stream,
                                                    Loader=yaml.FullLoader)
                    else:
                        mia_home_config = yaml.load(stream)

                    if ("dev_mode" in mia_home_config.keys() and
                            mia_home_config["dev_mode"] == True):
                        # Only for admin mode
                        self.dev_mode = True
                        config_path = os.path.dirname(os.path.realpath(
                            __file__))

                        while "properties" not in os.listdir(config_path):
                            config_path = os.path.dirname(config_path)

                        self.mia_path = config_path
                        return config_path

                    # Only for user mode
                    self.dev_mode = False

                    # mia_path is obsolete. Use mia_user_path instead
                    if "mia_path" in mia_home_config:
                        mia_home_config["mia_user_path"] = \
                                                     mia_home_config["mia_path"]
                        del mia_home_config["mia_path"]

                        with open(dot_mia_config,
                                  'w', encoding='utf8') as configfile:
                            yaml.dump(mia_home_config, configfile,
                                      default_flow_style=False,
                                      allow_unicode=True)

                    self.mia_path = mia_home_config["mia_user_path"]
                    return self.mia_path

                except (yaml.YAMLError, KeyError) as e:
                    print('\nMia path (where is located the processes, '
                          'the properties and resources folders) has not '
                          'been found ...')

        else:  # Only for admin mode

            try:
                self.mia_path = self.config["mia_user_path"]
                return self.mia_path

            except (KeyError, AttributeError):
                config_path = os.path.dirname(os.path.realpath(
                    __file__))

                while "properties" not in os.listdir(config_path):
                    config_path = os.path.dirname(config_path)

                self.mia_path = config_path
                return config_path

    def get_config_path(self):
        """Get the MIA config path (including "properties" directory)
        """
        config_path = getattr(self, 'config_path', None)
        if config_path:
            return config_path
        mia_path = self.get_mia_path()
        return os.path.join(mia_path, 'properties')

    def get_mri_conv_path(self):
        """Get the MRIManager.jar path.

        :return: string of the path

        """
        return self.config.get("mri_conv_path", "")

    def get_opened_projects(self):
        """Get opened projects.

        :return: list of opened projects

        """
        return self.config.get("opened_projects", [])

    def get_projects_save_path(self):
        """Get the path where projects are saved.

        :return: string of path

        """
        try:
            return self.config["projects_save_path"]
        except KeyError:
            if not os.path.isdir(os.path.join(self.get_mia_path(),
                                              'projects')):
                os.mkdir(os.path.join(self.get_mia_path(), 'projects'))
            return os.path.join(self.get_mia_path(), 'projects')

    def get_spm_path(self):
        """Get the path of SPM12.

        :return: string of path

        """
        return self.config.get("spm", "")

    def get_spm_standalone_path(self):
        """Get the path to the SPM12 (standalone version).

        :return: String of path

        """
        return self.config.get("spm_standalone", "")

    def get_use_matlab(self):
        """Get the value of "use matlab" checkbox in the preferences.

        :return: boolean

        """
        return self.config.get("use_matlab", False)

    def get_use_matlab_standalone(self):
        """Get the value of "use matlab standalone" checkbox in the
        preferences.

        :return: boolean

        """
        return self.config.get("use_matlab_standalone", False)

    def get_use_spm(self):
        """Get the value of "use spm" checkbox in the preferences.

        :return: boolean

        """
        return self.config.get("use_spm", False)

    def get_use_spm_standalone(self):
        """Get the value of "use spm standalone" checkbox in the preferences.

        :return: boolean

        """
        return self.config.get("use_spm_standalone", False)

    def getBackgroundColor(self):
        """Get background color.

        :return: string of the background color

        """
        return self.config.get("background_color", "")

    def getChainCursors(self):
        """Get the value of the checkbox 'chain cursor' in miniviewer.

        :return: boolean

        """
        return self.config.get("chain_cursors", False)

    def getNbAllSlicesMax(self):
        """Get number the maximum number of slices to display in the
        miniviewer.

        :return: Integer

        """
        return int(self.config.get("nb_slices_max", "10"))

    def getPathToProjectsFolder(self):
        """Get the project's path.

        :return: string of the path

        """
        return self.config.get("projects_save_path", "")

    def getSourceImageDir(self):
        """Get the source directory for project images."""
        return self.config.get("source_image_dir", "")

    def getShowAllSlices(self):
        """Get whether the show_all_slices parameters was enabled
        or not in the miniviewer.

        :return: boolean

        """
        #Used in MiniViewer
        return self.config.get("show_all_slices", False)

    def getTextColor(self):
        """Get the text color.

        :return: string

        """
        return self.config.get("text_color", "")

    def getThumbnailTag(self):
        """Get the tag of the thumbnail displayed in the miniviewer.

        :return: string

        """
        return self.config.get("thumbnail_tag", "SequenceName")

    def isAutoSave(self):
        """Get if the auto-save mode is enabled or not.

        :return: boolean

        """
        # used only in tests and when the background/text color is changed
        return self.config.get("auto_save", False)

    def loadConfig(self):
        """Read the config in the config.yml file.

        :return: Returns a dictionary of the contents of config.yml

        """
        f = Fernet(CONFIG)
        config_file = os.path.join(self.get_config_path(), 'config.yml')
        if not os.path.exists(config_file):
            return {}
        with open(config_file, 'rb') as stream:
            try:
                stream = b"".join(stream.readlines())
                decrypted = f.decrypt(stream)
                if verCmp(yaml.__version__, '5.1', 'sup'):
                    return yaml.load(decrypted, Loader=yaml.FullLoader)

                else:
                    return yaml.load(decrypted)

            except yaml.YAMLError as exc:
                print('error loading YAML file: %s' % config_file)
                print(exc)
                #import traceback
                #traceback.print_stack()
        # in case of problem, return an empty config
        return {}

    def saveConfig(self):
        """Save the current parameters in the config.yml file."""
        f = Fernet(CONFIG)
        config_file = os.path.join(self.get_config_path(), 'config.yml')
        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))
        with open(config_file, 'wb') as configfile:
            stream = yaml.dump(self.config, default_flow_style=False,
                      allow_unicode=True)
            configfile.write(f.encrypt(stream.encode()))

        self.update_capsul_config()

    def set_admin_hash(self, hash):
        """Set the password hash.

        :param: path: string of hash

        """
        self.config["admin_hash"] = hash
        # Then save the modification
        self.saveConfig()

    def set_capsul_config(self, capsul_config_dict):
        """Set CAPSUL configuration dict into MIA config
        """
        self.config['capsul_config'] = capsul_config_dict
        self.update_capsul_config()  # store into capsul engine

        # update MIA values
        engine_config = capsul_config_dict.get('engine')
        if engine_config:
            from capsul.api import capsul_engine
            new_engine = capsul_engine()
            for environment, config in engine_config.items():
                new_engine.import_configs(environment, config)
            capsul_config = new_engine.study_config.export_to_dict()
        else:
            capsul_config = capsul_config_dict.get('study_config', {})

        matlab_path = capsul_config.get('matlab_exec')
        use_matlab = capsul_config.get('use_matlab', None)
        if use_matlab and matlab_path:
            self.set_matlab_path(matlab_path)
            self.set_use_matlab(True)
        elif use_matlab is False:
            self.set_use_matlab(False)
            # self.set_matlab_path("")

        if capsul_config.get('use_spm', False):
            spm_dir = capsul_config.get('spm_directory')
            spm_standalone = capsul_config.get('spm_standalone')
            if spm_standalone:
                mcr = os.path.join(spm_dir, 'mcr', 'v713')
                if os.path.isdir(mcr) and os.path.isdir(spm_dir):
                    self.set_spm_standalone_path(spm_dir)
                    self.set_matlab_standalone_path(mcr)
                    self.set_use_spm_standalone(True)
                    self.set_use_matlab_standalone(True)
                    self.set_use_matlab(False)
            else:
                self.set_use_spm_standalone(False)
                if self.get_use_matlab():
                    self.set_spm_path(spm_dir)
                    self.set_use_spm(True)
                else:
                    self.set_use_spm(False)
        else:
            self.set_use_spm(False)
            self.set_use_spm_standalone(False)

    def set_user_mode(self, user_mode):
        """Enable of disable user mode.

        :param: user_mode: boolean

        """
        self.config["user_mode"] = user_mode
        # Then save the modification
        self.saveConfig()

    def set_mainwindow_maximized(self, enabled):
        """Set the maximized (fullscreen) flag
        """

        self.config['mainwindow_maximized'] = enabled
        self.saveConfig()

    def set_mainwindow_size(self, size):
        """Set main window size
        """

        self.config['mainwindow_size'] = list(size)
        self.saveConfig()

    def set_matlab_path(self, path):
        """Set the path of Matlab's executable.

        :param: path: string of path

        """
        self.config["matlab"] = path
        # Then save the modification
        self.saveConfig()

    def set_matlab_standalone_path(self, path):
        """Set the path of Matlab Compiler Runtime.

        :param: path: string of path

        """
        self.config["matlab_standalone"] = path
        # Then save the modification
        self.saveConfig()

    def set_max_projects(self, nb_max_projects):
        """Set the maximum number of projects displayed in
        the "Saved projects" menu.

        :param: nb_max_projects: Integer

        """
        self.config["max_projects"] = nb_max_projects
        # Then save the modification
        self.saveConfig()

    def set_mri_conv_path(self, path):
        """Set the MRIManager.jar path.

        :param: path: string of the path

        """
        self.config["mri_conv_path"] = path
        # Then save the modification
        self.saveConfig()

    def set_opened_projects(self, new_projects):
        """Set the list of opened projects and saves the modification.

        :param: new_projects: List of path

        """
        self.config["opened_projects"] = new_projects
        # Then save the modification
        self.saveConfig()

    def set_projects_save_path(self, path):
        """Set the folder where the projects are saved.

        :param: path: string of path
        """
        self.config["projects_save_path"] = path
        # Then save the modification
        self.saveConfig()

    def set_spm_path(self, path):
        """Set the path of SPM12 (license version).

        :param: path: string of path

        """
        self.config["spm"] = path
        # Then save the modification
        self.saveConfig()

    def set_spm_standalone_path(self, path):
        """Set the path of SPM12 (standalone version).

        :param: path: string of path

        """
        self.config["spm_standalone"] = path
        # Then save the modification
        self.saveConfig()

    def set_use_matlab(self, use_matlab):
        """Set the value of "use matlab" checkbox in the preferences.

        :param: use_matlab: boolean

        """
        self.config["use_matlab"] = use_matlab
        # Then save the modification
        self.saveConfig()

    def set_use_matlab_standalone(self, use_matlab_standalone):
        """Set the value of "use_matlab_standalone" checkbox in the
        preferences.

        :param: use_matlab: boolean

        """
        self.config["use_matlab_standalone"] = use_matlab_standalone
        # Then save the modification
        self.saveConfig()

    def set_use_spm(self, use_spm):
        """Set the value of "use spm" checkbox in the preferences.

        :param: use_spm: boolean
        """
        self.config["use_spm"] = use_spm
        # Then save the modification
        self.saveConfig()

    def set_use_spm_standalone(self, use_spm_standalone):
        """Set the value of "use spm standalone" checkbox in the preferences.

        :param:use_spm_standalone: boolean

        """
        self.config["use_spm_standalone"] = use_spm_standalone
        # Then save the modification
        self.saveConfig()

    def setAutoSave(self, save):
        """Set auto-save mode.

        :param: save: boolean
        """
        self.config["auto_save"] = save
        # Then save the modification
        self.saveConfig()

    def setBackgroundColor(self, color):
        """Set background color and save configuration.

        :param: color: Color string ('Black', 'Blue', 'Green', 'Grey',
            'Orange', 'Red', 'Yellow', 'White')
        """
        self.config["background_color"] = color
        # Then save the modification
        self.saveConfig()

    def setChainCursors(self, chain_cursors):
        """Set the value of the checkbox 'chain cursor' in the miniviewer.

        :param: chain_cursors: Boolean
        """
        self.config["chain_cursors"] = chain_cursors
        # Then save the modification
        self.saveConfig()

    def setNbAllSlicesMax(self, nb_slices_max):
        """Set the number of slices to display in the miniviewer.

        :param: nb_slices_max: Int

        """
        self.config["nb_slices_max"] = nb_slices_max
        # Then save the modification
        self.saveConfig()

    def setShowAllSlices(self, show_all_slices):
        """Set the show_all_slides setting in miniviewer.

        :param: show_all_slices: Boolean
        """
        self.config["show_all_slices"] = show_all_slices
        # Then save the modification
        self.saveConfig()

    def setSourceImageDir(self, source_image_dir):
        """Set the source directory for project images."""
        self.config["source_image_dir"] = source_image_dir
        # Then save the modification
        self.saveConfig()

    def setTextColor(self, color):
        """Set text color and save configuration.

        :param: color: Color string ('Black', 'Blue', 'Green', 'Grey',
            'Orange', 'Red', 'Yellow', 'White')

        """
        self.config["text_color"] = color
        # Then save the modification
        self.saveConfig()

    def setThumbnailTag(self, thumbnail_tag):
        """Set the tag that is displayed in the mini viewer.

        :param: thumbnail_tag: String

        """
        self.config["thumbnail_tag"] = thumbnail_tag
        # Then save the modification
        self.saveConfig()

    # def set_mia_path(self, path):
    #     """
    #
    #     :param:#         path:
    #
    #     :return:
    #
    #     """
    #     self.config["mia_user_path"] = path
    #     # Then save the modification
    #     self.saveConfig()

    # def getPathData(self):
    #     """
    #     Get the path tp the data directory
    #     :return: returns the path to the data directory
    #
    #     """
    #     return self.config["paths"]["data"]

    # def getPathToProjectsDBFile(self):
    #     """
    #
    #     :return:
    #
    #     """
    #     folder = self.getPathToProjectsFolder()
    #     return os.path.join(folder, 'projects.json')

    # def setPathToData(self,path):
    #     """
    #
    #     :param:#         path:
    #
    #     :return:
    #
    #     """
    #     if path is not None and path != '':
    #         self.config["paths"]["data"] = path
    #         # Then save the modification
    #         self.saveConfig()
