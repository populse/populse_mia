"""
This module provides command-line argument parsing for the Mia application.

It centralizes the definition and parsing of CLI arguments to avoid
duplication and ensure consistency across entry points.
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
    Parse the command-line arguments for the Populse Mia application.

    :returns: The parsed command-line arguments.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Launch the Populse MIA application."
    )
    parser.add_argument(
        "-mi",
        "--multi-instance",
        action="store_true",
        help=(
            "Allow multiple instances of Populse MIA to run simultaneously. "
            "By default, only one instance is allowed."
        ),
    )
    return parser.parse_args()
