<p align="center" >
	<img src="https://github.com/populse/populse_mia/blob/master/python/populse_mia/sources_images/Logo_populse_mia_HR.jpeg" alt="populse_mia logo" height="220" width="300">
</p>

[![](https://travis-ci.org/populse/populse_mia.svg?branch=master)](https://travis-ci.org/populse/populse_mia)
[![](https://ci.appveyor.com/api/projects/status/2km9ddxkpfkgra7v?svg=true)](https://ci.appveyor.com/project/populse/populse-mia)
[![](https://codecov.io/github/populse/populse_mia/coverage.svg?branch=master)](https://codecov.io/github/populse/populse_mia)
[![](https://img.shields.io/badge/license-CeCILL-blue.svg)](https://github.com/populse/populse_mia/blob/master/LICENSE)
[![](https://img.shields.io/pypi/v/populse_mia.svg)](https://pypi.org/project/populse-mia/)
[![](https://img.shields.io/badge/python-3.5%2C%203.6%2C%203.7-yellow.svg)](#)
[![](https://img.shields.io/badge/platform-Linux%2C%20OSX%2C%20Windows-orange.svg)](#)

# Documentation

[The documentation is available on populse_mia's website here](https://populse.github.io/populse_mia)

# Installation

* From PyPI, [for users](https://populse.github.io/populse_mia/html/installation/user_installation.html)

* From source, [for developers](https://populse.github.io/populse_mia/html/installation/developer_installation.html) (or to use the latest version of populse_mia)

# Usage

  * After an [installation in user mode](https://populse.github.io/populse_mia/html/installation/user_installation.html):

        python3 -m populse_mia

  * After an [installation in developer mode](https://populse.github.io/populse_mia/html/installation/developer_installation.html), interprets the main.py file from the source code directory:
  
        cd [mia_install_dir]/python/populse_mia  
        python3 main.py  

  * Depending on the operating system used, it was observed some compatibility issues with PyQt5/SIP. In this case, we recommend, as a first attempt, to do:

        python3 -m pip install --force-reinstall pyqt5==5.14.0
        python3 -m pip install --force-reinstall PyQt5-sip==5.0.1

# Tests

* Unit tests written thanks to the python module unittest
* Continuous integration made with Travis (Linux, OSX), and AppVeyor (Windows)
* Code coverage calculated by the python module codecov
* The module is ensured to work with Python >= 3.5
* The module is ensured to work on the platforms Linux, OSX and Windows
* The script of tests is python/populse_mia/test.py, so the following command launches the tests:

      python3 python/populse_mia/test.py (from populse_mia root folder, for example [mia_install_dir])

# Requirements

* capsul
* lark-parser
* matplotlib
* mia-processes
* nibabel
* nipype
* pillow
* populse-db
* pyqt5
* python-dateutil
* pyyaml
* scikit-image
* scipy
* SIP
* sqlalchemy
* snakeviz
* soma_workflow
* traits

# Other packages used

* copy
* os
* six
* tempfile
* unittest

# License

* The whole populse project is open source
* Populse_mia is precisely released under the CeCILL software license
* You can find all the details on the license [here](http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html), or refer to the license file [here](https://github.com/populse/populse_mia/blob/master/LICENSE)

# Support and Communication

If you have a problem or would like to ask a question about how to do something in populse_mia, please [open an issue](https://github.com/populse/populse_mia/issues).

You can even contact the developer team by using populse-support@univ-grenoble-alpes.fr.
