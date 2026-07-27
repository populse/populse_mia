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

from populse_mia.logging_config import configure_logging

# populse_mia import
from populse_mia.main import main

from .cli_args import parse_args

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    try:
        args = parse_args()
        configure_logging(
            log_in_stdout=args.log_in_stdout,
            keep_log_files=args.keep_log_files,
        )
        logger.info("Starting Populse Mia...")
        # Print the multi_instance argument value
        logger.info(f"--multi_instance is set to: {args.multi_instance}")
        main(args)

    except Exception as e:
        print(f"Error while running populse_mia: {e}")
