"""
This module provides command-line argument parsing for the Mia application.

It centralizes the definition and parsing of CLI arguments to avoid
duplication and ensure consistency across entry points.

:Contains:
    :Function:
        - parse_args()
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import argparse


def parse_args():
    """
    Parse command-line arguments for the Mia application.

    This function configures and parses command-line arguments for
    launching the Mia application.

    :returns (argparse.Namespace): Parsed command-line arguments
                                   containing:
        - multi_instance (bool): Whether multiple instances of the application
                                 can be launched simultaneously
                                 (default: False).
    """
    parser = argparse.ArgumentParser(
        description="Populse Mia Application Entry Point."
    )
    parser.add_argument(
        "--multi_instance",
        type=bool,
        default=False,
        help="Set the value of multi_instance.",
    )
    return parser.parse_args()
