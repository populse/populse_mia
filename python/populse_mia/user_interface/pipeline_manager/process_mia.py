# -*- coding: utf-8 -*- #
"""
Module used by MIA bricks to run processes.

:Contains:
    :Class:
        - ProcessMIA

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import datetime
from traits.trait_base import Undefined
from traits.trait_handlers import TraitListObject
import os
import uuid

# Capsul imports
from capsul.api import Process, Pipeline
from capsul.pipeline.pipeline_nodes import ProcessNode
from capsul.process.process import NipypeProcess
from soma.utils.weak_proxy import get_ref

# Populse_MIA imports
from populse_mia.data_manager.project import (BRICK_EXEC, BRICK_EXEC_TIME,
                                              BRICK_OUTPUTS,COLLECTION_BRICK,
                                              COLLECTION_CURRENT,
                                              COLLECTION_INITIAL, TAG_BRICKS)


class ProcessMIA(Process):
    """Class overriding the default capsul Process class, in order to
    personalise the run for MIA bricks.

   This class is mainly used by MIA bricks.

    .. Methods:
        - list_outputs: generates the outputs of the process (need to be
           overridden)
        - manage_matlab_launch_parameters: Set the Matlab's config parameters
           when a Nipype process is used

    """

    def list_outputs(self):
        """Override the outputs of the process."""
        pass


# ---- completion system for Capsul ---

from capsul.attributes.completion_engine import (
    ProcessCompletionEngine,
    ProcessCompletionEngineFactory)


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

    def path_attributes(self, filename, parameter=None):
        # re-route to underlying fallback engine
        return self.fallback_engine.path_attributes(filename, parameter)

    def get_path_completion_engine(self):
        # re-route to underlying fallback engine
        return self.fallback_engine.get_path_completion_engine()

    def remove_switch_observer(self, observer=None):
        # reimplemented since it is expectes in switches completion engine
        return self.fallback_engine.remove_switch_observer(observer)

    def get_attribute_values(self):
        # re-route to underlying fallback engine
        return self.fallback_engine.get_attribute_values()

    def complete_parameters(self, process_inputs={}):

        self.completion_progress = self.fallback_engine.completion_progress
        self.completion_progress_total \
            = self.fallback_engine.completion_progress_total

        # handle database attributes and indexation
        self.complete_attributes_with_database(process_inputs)

        in_process = get_ref(self.process)
        if isinstance(in_process, ProcessNode):
            in_process = in_process.process

        # nipype special case -- output_directory is set from MIA project
        if isinstance(in_process, (NipypeProcess, ProcessMIA)):
            self.complete_nipype_common(in_process)

        project = self.get_project(in_process)
        if project is not None:
            # record completion order to perform 2nd pass tags recording and
            # indexation
            if not hasattr(project, 'process_order'):
                project.process_order = []
            node = self.process
            if isinstance(node, Pipeline):
                node = node.pipeline_node
            from capsul.pipeline.pipeline_nodes import Node
            project.process_order.append(node)

        if not isinstance(in_process, ProcessMIA):

            self.fallback_engine.complete_parameters(process_inputs)
            self.completion_progress = self.fallback_engine.completion_progress
            self.completion_progress_total \
                = self.fallback_engine.completion_progress_total

        else:

            # here the process is a ProcessMIA instance. Use the specific
            # method

            #self.completion_progress = 0.
            #self.completion_progress_total = 1.
            self.complete_parameters_mia(process_inputs)
            self.completion_progress = self.completion_progress_total

    @staticmethod
    def get_project(process):
        project = None
        if isinstance(process, ProcessNode):
            process = process.process
        if hasattr(process, 'get_study_config'):
            study_config = process.get_study_config()
            project = getattr(study_config, 'project', None)
        return project

    @staticmethod
    def complete_nipype_common(process):
        '''
        Set Nipype parameters for SPM. This is used both on
        :class:`NipypeProcess` and :class:`ProcessMIA` instances which have the
        appropriate parameters.
        '''

        # Test for matlab launch
        if process.trait('use_mcr'):

            from populse_mia.software_properties import Config

            config = Config()
            if config.get_use_spm_standalone():
                process.use_mcr = True
                process.paths \
                    = config.get_spm_standalone_path().split()
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
                process.project = self.project
            # set output_directory
            if process.trait('output_directory') \
                    and process.output_directory in (None, Undefined, ''):
                out_dir = os.path.abspath(os.path.join(project.folder,
                                                        'data',
                                                        'derived_data'))
                # ensure this output_directory exists since it is not
                # actually an output but an input, and thus it is supposed
                # to exist in Capsul.
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                process.output_directory = out_dir

            tname = None
            tmap = getattr(process, '_nipype_trait_mapping', {})
            tname = tmap.get('_spm_script_file', '_spm_script_file')
            if (not process.trait(tname)
                and process.trait('spm_script_file')):
                tname = 'spm_script_file'
            if tname:
                if hasattr(process, '_nipype_interface'):
                    iscript = (process._nipype_interface
                                .mlab.inputs.script_file)
                elif (hasattr(process, 'process')
                      and hasattr(process.process, '_nipype_interface')):
                    # ProcessMIA with a NipypeProcess inside
                    iscript = (process.process._nipype_interface
                                .mlab.inputs.script_file)
                else:
                    iscript = process.name + '.m'
                process.uuid = str(uuid.uuid4())
                iscript = os.path.basename(iscript)[:-2] \
                    + '_%s.m' % process.uuid
                setattr(process, tname,
                        os.path.abspath(os.path.join(
                            project.folder, 'scripts', iscript)))

            process.mfile = True

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
            initResult_dict = process.list_outputs(is_plugged=is_plugged)
        except Exception as e:
            print(e)
            initResult_dict = {}
        if not initResult_dict:
            return  # the process is not really configured

        outputs = initResult_dict.get('outputs', {})
        for parameter, value in outputs.items():
            if parameter == 'notInDb' \
                    or process.is_parameter_protected(parameter):
                continue  # special non-param or set manually
            try:
                setattr(process, parameter, value)
            except Exception as e:
                if verbose:
                    print('Exception:', e)
                    print('param:', pname)
                    print('value:', repr(value))
                    import traceback
                    traceback.print_exc()

        MIAProcessCompletionEngine.complete_nipype_common(process)

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
                    for fvalue in fvalues:
                      fvalue.append('')

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
                    pass # not found
        if engine_factory is None:

            from capsul.attributes.completion_engine_factory \
              import BuiltinProcessCompletionEngineFactory

            engine_factory = BuiltinProcessCompletionEngineFactory()

        fallback = engine_factory.get_completion_engine(process, name=name)

        return MIAProcessCompletionEngine(process, name, fallback)

