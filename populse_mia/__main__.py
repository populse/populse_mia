"""
Enable populse_mia to be run as a module.

This allows running populse_mia using:
    python3 -m populse_mia

This will execute the main entry point of the application.

"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

import logging
import sys

# populse_mia import
from .cli_args import parse_args
from .install.mia_install import run_installer
from .logging_config import configure_logging
from .main import main

__all__ = ["run"]

logger = logging.getLogger(__name__)


def run():
    """
    Run the Populse Mia application.

    Parse the command-line arguments, configure logging, and either launch the
    application or run the 'Installation and Repair' mode.

    """
    args = parse_args()
    configure_logging(
        log_in_stdout=args.log_in_stdout,
        keep_log_files=args.keep_log_files,
        log_level=args.log_level,
    )

    msg = "Starting Mia..."
    print("\n" + msg + "\n")
    logger.info(msg)
    logger.info("Python version: %s", sys.version)
    logger.info("Python executable: %s", sys.executable)
    logger.info("--multi_instance is set to: %s", args.multi_instance)
    logger.info("--log_level is set to: %s", args.log_level)
    logger.info("--log_in_stdout is set to: %s", args.log_in_stdout)
    logger.info("--keep_log_files is set to: %s", args.keep_log_files)
    logger.info("--install is set to: %s", args.install)

    if args.install:
        run_installer()
        msg = "Stopping Mia..."
        logger.info("Stopping Populse Mia...")
        print("\n" + msg + "\n")
        return

    main(args)


if __name__ == "__main__":
    run()
