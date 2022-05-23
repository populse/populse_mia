# -*- coding: utf-8 -*- #
"""
Module used by MIA bricks to run processes.

:Contains:
    :Class:
        - MIAProcessCompletionEngine
        - MIAProcessCompletionEngineFactory
        - ProcessMIA
 

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# Capsul imports
import copy
import weakref

import six
from capsul.api import capsul_engine, Process, Pipeline
from capsul.attributes.completion_engine import (ProcessCompletionEngine,
                                                 ProcessCompletionEngineFactory)
from capsul.attributes.completion_engine_factory import (
    BuiltinProcessCompletionEngineFactory)
from capsul.pipeline.pipeline_nodes import ProcessNode
from capsul.process.process import NipypeProcess
from capsul.pipeline.process_iteration import ProcessIteration

# nipype imports
from nipype.interfaces.base import File, traits_extension, InputMultiObject

# Populse_MIA imports
from populse_mia.data_manager.project import COLLECTION_CURRENT
from populse_mia.software_properties import Config

# Soma-base import
from soma.controller.trait_utils import relax_exists_constraint
from soma.utils.weak_proxy import get_ref

# Other imports
import os
import uuid
import traceback
import traits.api as traits
from traits.trait_base import Undefined


class MIAProcessCompletionEngine(ProcessCompletionEngine):
    """
    A specialized
    :class:`~capsul.attributes.completion_engine.ProcessCompletionEngine` for
    completion of *all processes* within the Populse_MIA context.

    :class:`PopulseMIA` processes instances and :class:NipypeProcess` instances
    have a special handling.

    :class:`PopulseMIA` processes use their method
    :meth:`ProcessMIA.list_outputs` to perform completion from given input
    parameters. It is currently not based on attributes like in capsul
    completion, but on filenames.

    Processes also get their matlab / SPM settings filled in from the config if
    they need them (:class:`NipypeProcess` instances).

    If the process use it and it is in the study config, their "project"
    parameter is also filled in, as well as the "output_directory" parameter.

    The "normal" Capsul completion system is also complemented using MIA
    database: attributes from input parameters in the database (called "tags"
    here in MIA) are added to the completion attributes.

    The MIA project will keep track of completed processes, in the correct
    completion order, so that other operations can be performed following the
    same order later after completion.
    """

    def __init__(self, process, name, fallback_engine):

        super(MIAProcessCompletionEngine, self).__init__(process, name)

        self.fallback_engine = fallback_engine
        self.completion_progress = 0.0
        self.completion_progress_total = 0.0

    def complete_attributes_with_database(self, process_inputs={}):
        '''
        Augments the Capsul completion system attributes associated with a
        process. Attributes from the database are queried for input parameters,
        and added to the completion attributes values, if they match.
        '''

        # re-route to underlying fallback engine
        attributes = self.fallback_engine.get_attribute_values()
        process = self.process
        if isinstance(process, ProcessNode):
            process = process.process
        if not isinstance(process, Process):
            return attributes

        if not hasattr(process, 'get_study_config'):
            return attributes
        study_config = process.get_study_config()

        project = getattr(study_config, 'project', None)
        if not project:
            return attributes

        fields = project.session.get_fields_names(COLLECTION_CURRENT)
        pfields = [field for field in fields if attributes.trait(field)]
        if not pfields:
            return attributes

        proj_dir = os.path.join(os.path.abspath(os.path.realpath(
            project.folder)), '')
        pl = len(proj_dir)

        for param, par_value in process.get_inputs().items():

            # update value from given forced input
            par_value = process_inputs.get(param, par_value)
            if isinstance(par_value, list):
                par_values = par_value
            else:
                par_values = [par_value]

            fvalues = [[] for field in pfields]
            for value in par_values:
                if not isinstance(value, str):
                    continue

                ap = os.path.abspath(os.path.realpath(value))
                if not ap.startswith(proj_dir):
                    continue

                rel_value = ap[pl:]
                document = project.session.get_document(
                    COLLECTION_CURRENT, rel_value, fields=pfields,
                    as_list=True)
                if document:
                    for fvalue, dvalue in zip(fvalues, document):
                        fvalue.append(dvalue if dvalue is not None else '')
                else:
                    # ignore this input not in the database
                    for fvalue in fvalues:
                        fvalue.append(None)

            # temporarily block attributes change notification in order to
            # avoid triggering another completion while we are already in this
            # process.
            completion_ongoing_f = self.fallback_engine.completion_ongoing
            self.fallback_engine.completion_ongoing = True
            completion_ongoing = self.completion_ongoing
            self.completion_ongoing = True

            if fvalues[0] and not all([all([x is None for x in y])
                                       for y in fvalues]):
                if isinstance(par_value, list):
                    for field, value in zip(pfields, fvalues):
                        setattr(attributes, field, value)
                else:
                    for field, value in zip(pfields, fvalues):
                        setattr(attributes, field, value[0])

            # restore notification
            self.fallback_engine.completion_ongoing = completion_ongoing_f
            self.completion_ongoing = completion_ongoing

        return attributes

    @staticmethod
    def complete_nipype_common(process):
        '''
        Set Nipype parameters for SPM. This is used both on
        :class:`NipypeProcess` and :class:`ProcessMIA` instances which have the
        appropriate parameters.
        '''

        # Test for matlab launch
        if process.trait('use_mcr'):
            config = Config()

            if config.get_use_spm_standalone():
                process.use_mcr = True
                process.paths = config.get_spm_standalone_path().split()
                process.matlab_cmd = config.get_matlab_command()

            elif config.get_use_spm():
                process.use_mcr = False
                process.paths = config.get_spm_path().split()
                process.matlab_cmd = config.get_matlab_command()

        # add "project" attribute if the process is using it
        study_config = process.get_study_config()
        project = getattr(study_config, 'project', None)

        if project:

            if hasattr(process, 'use_project') and process.use_project:
                process.project = project

            # set output_directory
            if (process.trait('output_directory') and
                    process.output_directory in (None, Undefined, '')):
                out_dir = os.path.abspath(os.path.join(project.folder,
                                                       'data',
                                                       'derived_data'))

                # ensure this output_directory exists since it is not
                # actually an output but an input, and thus it is supposed
                # to exist in Capsul.
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)

                process.output_directory = out_dir

            if ((hasattr(process, '_nipype_interface_name') and
                 process._nipype_interface_name == 'spm') or
                    (hasattr(process, 'process') and
                     hasattr(process.process, '_nipype_interface_name') and
                     process.process._nipype_interface_name == 'spm')):
                tname = None
                tmap = getattr(process, '_nipype_trait_mapping', {})
                tname = tmap.get('_spm_script_file', '_spm_script_file')

                if (not process.trait(tname) and
                        process.trait('spm_script_file')):
                    tname = 'spm_script_file'

                if tname:

                    if hasattr(process, '_nipype_interface'):
                        iscript = (process._nipype_interface
                                   .mlab.inputs.script_file)

                    elif (hasattr(process, 'process') and
                          hasattr(process.process, '_nipype_interface')):
                        # ProcessMIA with a NipypeProcess inside
                        iscript = (process.process._nipype_interface
                                   .mlab.inputs.script_file)

                    else:
                        iscript = process.name + '.m'

                    process.uuid = str(uuid.uuid4())
                    iscript = (os.path.basename(iscript)[:-2]
                               + '_%s.m' % process.uuid)
                    setattr(process, tname,
                            os.path.abspath(os.path.join(
                                project.folder, 'scripts', iscript)))

                process.mfile = True

    def complete_parameters(self, process_inputs={}, complete_iterations=True):

        self.completion_progress = self.fallback_engine.completion_progress
        self.completion_progress_total \
            = self.fallback_engine.completion_progress_total

        # print('complete_parameters', self.process.name, ', attributes:', self.fallback_engine.get_attribute_values().export_to_dict())

        # handle database attributes and indexation
        self.complete_attributes_with_database(process_inputs)
        in_process = get_ref(self.process)

        if isinstance(in_process, ProcessNode):
            in_process = in_process.process

        # nipype special case -- output_directory is set from MIA project        
        if isinstance(in_process, (NipypeProcess, ProcessMIA)):
            self.complete_nipype_common(in_process)

        if not isinstance(in_process, ProcessMIA):

            if not isinstance(in_process, Pipeline):

                if in_process.context_name.split('.')[0] == 'Pipeline':
                    node_name = '.'.join(in_process.context_name.split('.')[1:])

                else:
                    node_name = in_process.context_name

                if isinstance(in_process, NipypeProcess):
                    print('\n. {0} ({1}) nipype node ...'.format(
                        node_name,
                        '.'.join((in_process._nipype_interface.__module__,
                                  in_process._nipype_interface.__class__.__name__))))

                else:
                    print('\n. {0} ({1}) regular node ...'.format(
                        node_name,
                        '.'.join((in_process.__module__,
                                  in_process.__class__.__name__))))

            self.fallback_engine.complete_parameters(
                process_inputs, complete_iterations=complete_iterations)
            self.completion_progress = self.fallback_engine.completion_progress
            self.completion_progress_total = (self.fallback_engine.
                                              completion_progress_total)

        else:
            # here the process is a ProcessMIA instance. Use the specific
            # method

            # self.completion_progress = 0.
            # self.completion_progress_total = 1.

            name = getattr(self.process, 'context_name', self.process.name)
            if name.split('.')[0] == 'Pipeline':
                node_name = '.'.join(name.split('.')[1:])

            else:
                node_name = name

            print('\n. {0} ({1}) MIA node ...'.format(
                node_name,
                '.'.join((self.process.__module__,
                          self.process.__class__.__name__))))

            self.complete_parameters_mia(process_inputs)
            self.completion_progress = self.completion_progress_total

            # we must keep a copy of inheritance dict,
            # since it changes at each iteration and is not included in workflow
            # TODO: a better solution would be to save for each node the inheritance between plugs
            # and not between filenames (that changes over iteration)
            project = self.get_project(in_process)
            if project is not None:
                # record completion order to perform 2nd pass tags recording and
                # indexation
                if not hasattr(project, 'node_inheritance_history'):
                    project.node_inheritance_history = {}

                node = self.process

                if isinstance(node, Pipeline):
                    node = node.pipeline_node

                # Create a copy of current inheritance dict
                if node_name not in project.node_inheritance_history:
                    project.node_inheritance_history[node_name] = []
                if hasattr(node, 'inheritance_dict'):
                    project.node_inheritance_history[node_name].append(node.inheritance_dict)

    def complete_parameters_mia(self, process_inputs={}):
        '''
        Completion for :class:`ProcessMIA` instances. This is done using their
        :meth: `ProcessMIA.list_outputs` method, which fills in output
        parameters from input values, and sets the internal `inheritance_dict`
        used after completion for data indexation in MIA.
        '''
        self.set_parameters(process_inputs)
        verbose = False
        node = self.process
        process = node

        if isinstance(node, ProcessNode):
            process = node.process

            is_plugged = {key:
                              (bool(plug.links_to) or bool(plug.links_from))
                          for key, plug in node.plugs.items()}
        else:
            is_plugged = None  # we cannot get this info

        try:
            # set inheritance dict to the node
            initResult_dict = process.list_outputs(is_plugged=is_plugged)

        except Exception as e:
            print('\nError during initialisation ...!\nTraceback:')
            print(''.join(traceback.format_tb(e.__traceback__)), end='')
            print('{0}: {1}\n'.format(e.__class__.__name__, e))
            initResult_dict = {}

        if not initResult_dict:
            return  # the process is not really configured

        outputs = initResult_dict.get('outputs', {})

        if not outputs:
            return  # the process is not really configured

        for parameter, value in outputs.items():
            if parameter == 'notInDb' \
                    or process.is_parameter_protected(parameter):
                continue  # special non-param or set manually
            try:
                setattr(process, parameter, value)
            except Exception as e:
                if verbose:
                    print('Exception:', e)
                    print('param:', parameter)
                    print('value:', repr(value))
                    traceback.print_exc()

        MIAProcessCompletionEngine.complete_nipype_common(process)

    def get_attribute_values(self):
        # re-route to underlying fallback engine
        return self.fallback_engine.get_attribute_values()

    def get_path_completion_engine(self):
        # re-route to underlying fallback engine
        return self.fallback_engine.get_path_completion_engine()

    @staticmethod
    def get_project(process):
        project = None
        if isinstance(process, ProcessNode):
            process = process.process
        if hasattr(process, 'get_study_config'):
            study_config = process.get_study_config()
            project = getattr(study_config, 'project', None)
        return project

    def path_attributes(self, filename, parameter=None):
        # re-route to underlying fallback engine
        return self.fallback_engine.path_attributes(filename, parameter)

    def remove_switch_observer(self, observer=None):
        # reimplemented since it is expectes in switches completion engine
        return self.fallback_engine.remove_switch_observer(observer)


class MIAProcessCompletionEngineFactory(ProcessCompletionEngineFactory):
    """
    Completion engine factory specialization for Popules MIA context.
    Its ``factory_id`` is "mia_completion".

    This factory is activated in the
    :class:`~capsul.study_config.study_config.StudyConfig` instance by setting
    2 parameters::

        study_config.attributes_schema_paths = study_config.attributes_schema_paths \
            + ['populse_mia.user_interface.pipeline_manager.process_mia']
        study_config.process_completion =  'mia_completion'

    Once this is done, the completion system will be activated for all
    processes, and use differently all MIA processes and nipype processes. For
    regular processes, additional database operations will be performed, then
    the underlying completion system will be called (FOM or other).
    """

    factory_id = 'mia_completion'

    def get_completion_engine(self, process, name=None):
        if hasattr(process, 'completion_engine'):
            return process.completion_engine

        engine_factory = None
        if hasattr(process, 'get_study_config'):
            study_config = process.get_study_config()

            engine = study_config.engine
            if 'capsul.engine.module.attributes' in engine._loaded_modules:
                try:
                    former_factory = 'builtin'  # TODO how to store this ?
                    engine_factory \
                        = engine._modules_data['attributes'] \
                        ['attributes_factory'].get(
                        'process_completion', former_factory)
                except ValueError:
                    pass  # not found
        if engine_factory is None:
            engine_factory = BuiltinProcessCompletionEngineFactory()

        fallback = engine_factory.get_completion_engine(process, name=name)

        # iteration
        in_process = process
        if isinstance(process, ProcessNode):
            in_process = process.process
        if isinstance(in_process, ProcessIteration):
            # iteration nodes must follow their own way
            return fallback

        return MIAProcessCompletionEngine(process, name, fallback)


class ProcessMIA(Process):
    """Class overriding the default capsul Process class, in order to
    customise the run for MIA bricks.

   This class is mainly used by MIA bricks.

    .. Methods:

        - _after_run_process: Try to recover the output values, when the
                              calculation has been delegated to a process in
                              ProcessMIA
        - _run_processes: Call the run_process_mia method in the 
                          ProcessMIA subclass
        - init_default_traits: Automatically initialise necessary parameters
                               for nipype or capsul
        - list_outputs: Override the outputs of the process
        - make_initResult: Make the final dictionnary for outputs,
                           inheritance and requirement from the
                           initialisation of a brick
        - relax_nipype_exists_constraints: Relax the exists constraint of
                                           the process.inputs traits
        - requirements: Capsul Process.requirements() implementation using
                        MIA's ProcessMIA.requirement attribute
        - run_process_mia: Implements specific runs for ProcessMia
                           subclasses

    """

    def __init__(self, *args, **kwargs):
        super(ProcessMIA, self).__init__(*args, **kwargs)
        self.requirement = None
        self.outputs = {}
        self.inheritance_dict = {}

    def _after_run_process(self, run_process_result):
        """Try to recover the output values.
        """
        if hasattr(self, 'process') and isinstance(self.process, NipypeProcess):

            for mia_output in self.user_traits():
                wrapped_output = self.trait(mia_output).nipype_process_name

                if wrapped_output:
                    new = getattr(self.process, wrapped_output, None)
                    old = getattr(self, mia_output, None)

                    if (new and old != new):
                        setattr(self, mia_output, new)

    def _run_process(self):
        """Call the run_process_mia method in the Process_Mia subclass"""
        self.run_process_mia()

    def init_default_traits(self):
        """Automatically initialise necessary parameters for nipype or capsul"""
        if 'output_directory' not in self.user_traits():
            self.add_trait("output_directory",
                           traits.Directory(output=False,
                                            optional=True,
                                            userlevel=1))

        if self.requirement is not None and 'spm' in self.requirement:

            if 'use_mcr' not in self.user_traits():
                self.add_trait("use_mcr",
                               traits.Bool(optional=True,
                                           userlevel=1))

            if 'paths' not in self.user_traits():
                self.add_trait("paths",
                               InputMultiObject(traits.Directory(),
                                                optional=True,
                                                userlevel=1))

            if 'matlab_cmd' not in self.user_traits():
                self.add_trait("matlab_cmd",
                               traits_extension.Str(optional=True,
                                                    userlevel=1))

            if 'mfile' not in self.user_traits():
                self.add_trait("mfile",
                               traits.Bool(optional=True,
                                           userlevel=1))

            if 'spm_script_file' not in self.user_traits():
                spm_script_file_desc = ('The location of the output SPM matlab '
                                        'script automatically generated at the '
                                        'run step time (a string representing '
                                        'a file).')
                self.add_trait("spm_script_file",
                               File(output=True,
                                    optional=True,
                                    input_filename=True,
                                    userlevel=1,
                                    desc=spm_script_file_desc))

    def init_process(self, int_name):
        """
        Instantiation of the process attribute given an process identifier.

        :param int_name: a process identifier
        """
        if getattr(self, 'study_config'):
            ce = self.study_config.engine

        else:
            ce = capsul_engine()

        self.process = ce.get_process_instance(int_name)

    def list_outputs(self):
        """Override the outputs of the process."""
        self.relax_nipype_exists_constraints()

        if self.outputs:
            self.outputs = {}

        if self.inheritance_dict:
            self.inheritance_dict = {}

    def make_initResult(self):
        """Make the initResult_dict from initialisation."""
        if ((self.requirement is None) or
                (not self.inheritance_dict) or
                (not self.outputs)):
            print('\nDuring the {0} process initialisation, some possible '
                  'problems were detected:'.format(self))

            if self.requirement is None:
                print('- requirement attribute was not found ...')

            if not self.inheritance_dict:
                print('- inheritance_dict attribute was not found ...')

            if not self.outputs:
                print('- outputs attribute was not found ...')

            print()

        if (self.outputs and
                self.requirement is not None and
                'spm' in self.requirement):
            self.outputs["notInDb"] = ["spm_script_file"]

        return {'requirement': self.requirement, 'outputs': self.outputs,
                'inheritance_dict': self.inheritance_dict}

    def relax_nipype_exists_constraints(self):
        """Relax the exists constraint of the process.inputs traits"""
        if hasattr(self, 'process') and hasattr(self.process, 'inputs'):
            ni_inputs = self.process.inputs
            for name, trait in ni_inputs.traits().items():
                relax_exists_constraint(trait)

    def requirements(self):
        """Capsul Process.requirements() implementation using MIA's
        ProcessMIA.requirement attribute
        """
        if self.requirement:
            return {req: 'any' for req in self.requirement}
        return {}

    def run_process_mia(self):
        """
        Implements specific runs for Process_Mia subclasses
        """
        if self.output_directory and hasattr(self, 'process'):
            self.process.output_directory = self.output_directory

        if self.requirement is not None and 'spm' in self.requirement:

            if self.spm_script_file:
                self.process._spm_script_file = self.spm_script_file

            if self.use_mcr:
                self.process.use_mcr = self.use_mcr

            if self.paths:
                self.process.paths = self.paths

            if self.matlab_cmd:
                self.process.matlab_cmd = self.matlab_cmd

            if self.mfile:
                self.process.mfile = self.mfile
