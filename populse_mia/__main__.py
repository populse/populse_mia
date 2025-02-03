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

# Populse_MIA imports
from populse_mia.main import main

if __name__ == "__main__":

    try:
        main()

    except Exception as e:
        print(f"Error while running populse_mia: {e}")
