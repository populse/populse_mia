<p align="center" >
	<img src="https://github.com/populse/populse_mia/blob/master/populse_mia/sources_images/Logo_populse_mia_HR.jpeg" alt="populse_mia logo" height="220" width="300">
</p>

[//]: [![](https://travis-ci.com/populse/populse_mia.svg?branch=master)](https://app.travis-ci.com/github/populse/populse_mia)
[![Build status](https://ci.appveyor.com/api/projects/status/2km9ddxkpfkgra7v/branch/master?svg=true)](https://ci.appveyor.com/project/populse/populse-mia/branch/master)
[![codecov](https://codecov.io/gh/populse/populse_mia/branch/master/graph/badge.svg?token=40NTt0KVVV)](https://codecov.io/gh/populse/populse_mia)
[![](https://img.shields.io/badge/license-CeCILL-blue.svg)](https://github.com/populse/populse_mia/blob/master/LICENSE)
[![](https://img.shields.io/pypi/v/populse_mia.svg)](https://pypi.org/project/populse-mia/)
[![](https://img.shields.io/pypi/status/populse_mia.svg)](https://pypi.org/project/populse-mia/)
[![](https://img.shields.io/badge/python-3.9%2C%203.10%2C%203.11-yellow.svg)](#)
[![](https://img.shields.io/badge/platform-Linux%2C%20OSX%2C%20Windows-orange.svg)](#)

# Documentation

[The documentation is available on populse_mia's website here](https://populse.github.io/populse_mia)

# Installation

* From PyPI, [for users](https://populse.github.io/populse_mia/html/installation/user_installation.html)

* By cloning the package, [for developers](https://populse.github.io/populse_mia/html/installation/developer_installation.html)

* From source, [to use the latest version of populse_mia](https://populse.github.io/populse_mia/html/installation/from_source_installation.html)

* [Third-party software](https://populse.github.io/populse_mia/html/installation/3rd-party_installations.html)

* The populse project uses Git Large File Storage (LFS). In developer mode (without installing the source codes), after cloning the source codes, it is advisable to retrieve the large files with Git LFS:

    * If Git LFS is not already installed on your system, you need to install it first.
        * Ex. on Fedora:

            sudo dnf install git-lfs

    * Initialize Git LFS
        * On a reposirory:

            git lfs install

    * Retrieve Files with Git LFS
        * On a repository:

            git lfs pull

# Usage

  * After an [installation in user mode](https://populse.github.io/populse_mia/html/installation/user_installation.html):

        python3 -m populse_mia

  * After an [installation in developer mode](https://populse.github.io/populse_mia/html/installation/developer_installation.html), interprets the main.py file from the source code directory:

        cd [populse_install_dir]/populse_mia/populse_mia
        python3 main.py

  * Depending on the operating system used, it was observed some compatibility issues with PyQt5/SIP. In this case, we recommend, as a first attempt, to do:

        python3 -m pip install --force-reinstall pyqt5==5.14.0
        python3 -m pip install --force-reinstall PyQt5-sip==5.0.1

  * A minimal data set (~500 MB, zip file with Bruker, Philips and NIfTI data) can be downloaded [here](https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miadatausers/-/archive/main/miadatausers-main.zip) to allow users to quickly start using and testing Mia.

# Contributing to the project

If you'd like to contribute to the project please read our [developer documentation page](https://populse.github.io/populse_mia/html/documentation/developer_documentation.html). Please also read through [our code of conduct](https://github.com/populse/populse_mia/blob/master/CODE_OF_CONDUCT.md).

# Tests

* Unit tests written thanks to the python module unittest
* Continuous integration made with Travis (Linux, OSX), and AppVeyor (Windows)
* Code coverage calculated by the python module codecov
* The module is ensured to work with Python >= 3.6
* The module is ensured to work on the platforms Linux, OSX and Windows
* The script of tests is populse_mia/test.py, so the following command launches the tests:

      python3 populse_mia/test.py (from populse_mia root folder, for example [populse_install_dir]/populse_mia)

# Requirements

* capsul >= 2.5.0, < 3.0.0
* cryptography
* matplotlib
* mia-processes >= 2.5.0, < 3.0.0
* nibabel
* nipype
* pillow
* populse-db >= 2.5.0, < 3.0.0
* pre-commit
* pyqt5
* python-dateutil
* pyyaml
* scikit-image
* scipy
* snakeviz
* soma-base >= 5.2.0, < 6.0.0
* soma-workflow >= 3.2.2
* six >= 1.13
* traits

# Other packages used

* sphinx
* unittest

# License

* The whole populse project is open source
* Populse_mia is precisely released under the CeCILL software license
* All license details can be found [here](http://cecill.info/licences/Licence_CeCILL_V2.1-en.html), or refer to the license file [here](https://github.com/populse/populse_mia/blob/master/LICENSE).

# Support and Communication

All bugs, concerns and enhancement requests for populse_mia can be submitted [here](https://github.com/populse/populse_mia/issues).

The developer team can even be contacted using populse-support@univ-grenoble-alpes.fr.
