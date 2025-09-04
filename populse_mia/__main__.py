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

# Populse_MIA imports
from populse_mia.main import main

from .cli_args import parse_args

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":

    try:
        args = parse_args()
        # Print the multi_instance argument value
        logger.info(f"--multi_instance is set to: {args.multi_instance}")
        main(args)

    except Exception as e:
        print(f"Error while running populse_mia: {e}")
