"""
MIA (Multiparametric Image Analysis) is a comprehensive image processing
environment primarily designed for the analysis and visualization of large
MRI datasets.

MRI data analysis often requires executing complex processing pipelines on
datasets acquired during single or multiple MRI exams. In large-scale studies,
where data processing must be repeated across numerous acquisition sessions,
manually running processing modules or relying on simple ad-hoc scripts can
become error-prone, cumbersome, and difficult to reproduce. Additionally, data
processing pipelines are often distributed across various heterogeneous
toolboxes, developed either in-house or by other researchers, further
increasing the complexity of manually invoking these modules.

MIA (populse_mia) aims to simplify complex data processing by providing
intuitive tools that define inputs and outputs at a conceptual level. It
organizes data based on their roles in an analysis project, such
as “scan type,” “subject,” or “subject group,” making it easier to structure
and automate workflows.
"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

from .info import __version__  # noqa: F401

# import importlib.metadata

# try:
#    __version__ = importlib.metadata.__version__ = importlib.metadata.version(
#        "populse_mia"
#    )

# except importlib.metadata.PackageNotFoundError:
#    __version__ = None
