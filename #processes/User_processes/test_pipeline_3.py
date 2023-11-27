# -*- coding: utf-8 -*-
"""blablabla"""

from capsul.api import Pipeline
import traits.api as traits


class Test_pipeline_3(Pipeline):
    """blablabla"""

    def pipeline_definition(self):
        """blablabla"""

        # nodes
        self.add_process("smooth_1", "nipype.interfaces.spm.preprocess.Smooth")

        # links
        self.export_parameter("smooth_1", "in_files", is_optional=False)
        self.export_parameter("smooth_1", "_smoothed_files", is_optional=True)
        self.export_parameter("smooth_1", "_spm_script_file", is_optional=True)

        # parameters order

        self.reorder_traits(("in_files", "_smoothed_files", "_spm_script_file"))

        self.do_autoexport_nodes_parameters = False
