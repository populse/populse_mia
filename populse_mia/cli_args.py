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

__all__ = ["positive_int", "parse_args"]


def positive_int(value: str) -> int:
    """
    Convert a string to a strictly positive integer.

    :param value: String representation of an integer.
    :type value: str

    :returns: The converted integer.
    :rtype: int

    :raises argparse.ArgumentTypeError: If the integer is less than 1.
    :raises ValueError: If *value* cannot be converted to an integer.
    """
    value = int(value)

    if value < 1:
        raise argparse.ArgumentTypeError("must be greater than or equal to 1")

    return value


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
        "-ll",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        type=str.upper,
        help="Logging level (default: INFO).",
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

    parser.add_argument(
        "-lis",
        "--log-in-stdout",
        action="store_true",
        help=("Write log messages to stdout instead of a log file."),
    )

    parser.add_argument(
        "-klf",
        "--keep-log-files",
        type=positive_int,
        default=1,
        metavar="N",
        help=("Number of log files to retain " "(default: %(default)s)."),
    )

    return parser.parse_args()
