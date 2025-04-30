"""Define software version, description and requirements

:Contains:
    :Function:
        - get_populse_mia_gitversion

"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

import os
import subprocess
import sys

# Current version
version_major = 3
version_minor = 0
version_micro = 0
version_extra = "dev"  # leave empty for release
# version_extra = ""

# Expected by setup.py: string of form "X.Y.Z"
if version_extra:
    __version__ = (
        f"{version_major}.{version_minor}.{version_micro}-{version_extra}"
    )

else:
    __version__ = f"{version_major}.{version_minor}.{version_micro}".format(
        version_major, version_minor, version_micro
    )


def get_populse_mia_gitversion():
    """
    Mia version as reported by the last commit in git.

    :return: The short commit hash as the version or None if not found.
    """

    try:
        import populse_mia

        dir_mia = os.path.realpath(
            os.path.join(
                os.path.dirname(populse_mia.__file__),
                os.path.pardir,
            )
        )

    except ImportError:
        dir_mia = os.getcwd()

    dir_miagit = os.path.join(dir_mia, ".git")

    if not os.path.exists(dir_miagit):
        return None

    try:
        result = subprocess.run(
            ["git", "show", "-s", "--format=%h"],
            cwd=dir_mia,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


if __version__.endswith("-dev"):
    gitversion = get_populse_mia_gitversion()

    if gitversion:
        __version__ = f"{__version__}+{gitversion}"

# Expected by setup.py: the status of the project
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: CEA CNRS Inria "
    "Logiciel Libre License, version 2.1 (CeCILL-2.1)",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Scientific/Engineering",
    "Topic :: Utilities",
]

# project descriptions
DESCRIPTION = "populse mia"
LONG_DESCRIPTION = """
===============
populse_mia
===============
[MIA] Multi parametric Image Analysis:
A complete image processing environment mainly targeted at
the analysis and visualization of large amounts of MRI data
"""

# Other values used in setup.py
NAME = "populse_mia"
ORGANISATION = "populse"
MAINTAINER = "Populse team"
MAINTAINER_EMAIL = "populse-support@univ-grenoble-alpes.fr"
AUTHOR = "Populse team"
AUTHOR_EMAIL = "populse-support@univ-grenoble-alpes.fr"
URL = "http://populse.github.io/populse_mia"
DOWNLOAD_URL = "http://populse.github.io/populse_mia"
LICENSE = "CeCILL"
VERSION = __version__
CLASSIFIERS = CLASSIFIERS
PLATFORMS = "OS Independent"

REQUIRES = [
    "capsul >= 2.6.0, < 3.0.0",
    "cryptography",
    "matplotlib",
    "mia-processes >= 2.7.0, < 3.0.0",
    "nibabel",
    "nipype",
    "pillow",
    "populse-db >= 3.0.0, < 4.0.0",
    "pre-commit",
    "pyqt5",
    "python-dateutil",
    "pyyaml",
    "scikit-image",
    "scipy",
    "snakeviz",
    "soma-base >= 5.3.0, < 6.0.0",
    "soma-workflow >= 3.3.0",
    "six >= 1.13",
    "traits",
]

EXTRA_REQUIRES = {
    "doc": [
        "sphinx>=1.0",
    ],
}

brainvisa_build_model = "pure_python"

# tests to run
test_commands = [f"{sys.executable} -m populse_mia.test"]
