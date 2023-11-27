# -*- coding: utf-8 -*-
"""blablabla"""

from capsul.api import Pipeline
import traits.api as traits


class Test_pipeline_2(Pipeline):
    """blablabla"""

    def pipeline_definition(self):
        """blablabla"""

        # nodes
        self.add_process("smooth_1", "nipype.interfaces.spm.preprocess.Smooth")
        self.add_process("smooth_2", "mia_processes.bricks.preprocess.spm.spatial_preprocessing.Smooth")

        # links
        self.export_parameter("smooth_1", "in_files", is_optional=False)
        self.add_link("smooth_1._smoothed_files->smooth_2.in_files")
        self.export_parameter("smooth_2", "smoothed_files", is_optional=False)

        # parameters order

        self.reorder_traits(("in_files", "smoothed_files"))

        # nodes positions
        self.node_position = {
            "inputs": (-158.72567486702476, 0.0),
            "smooth_1": (161.00348869401944, 63.69497664007747),
            "smooth_2": (425.16579928888143, 187.1456296015163),
            "outputs": (790.8471758506131, 187.1456296015163),
        }

        # nodes dimensions
        self.node_dimension = {
            "inputs": (86.19217025915623, 75.0),
            "smooth_1": (232.625, 460.0),
            "smooth_2": (233.578125, 215.0),
            "outputs": (118.36291795522196, 62.0),
        }

        self.do_autoexport_nodes_parameters = False
