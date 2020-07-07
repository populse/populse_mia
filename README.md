<p align="center" >
	<img src="https://github.com/populse/populse_mia/blob/master/python/populse_mia/sources_images/Logo_populse_mia.jpg" alt="populse_mia logo" height="220" width="300">
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

* From PyPI

  * Please, see the [Populse_MIA’s user installation](https://populse.github.io/populse_mia/html/installation/user_installation.html)

* From source, for Linux distributions
  * A compatible version of Python must be installed
  * Install a Version Control System, for example [git](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control). Depending of your distribution, [package management system](https://en.wikipedia.org/wiki/Package_manager) can be different

        sudo apt-get install git # Debian like
        sudo dnf install git # Fedora 22 and later
        # etc.
  * We use Git extension for versioning large files ([Git LFS](https://git-lfs.github.com/)) of the populse_mia project. We therefore recommend to [install git-lfs](https://github.com/git-lfs/git-lfs/wiki/Installation).
  * Clone the source codes

    * Get source codes from Github. Replace [mia_install_dir] with a directory of your choice

          git lfs clone https://github.com/populse/populse_mia.git [mia_install_dir]

    * Or download the zip file (populse_mia-master.zip) of the project ([green button "Clone or download"](https://github.com/populse/populse_mia)), then extract the data in the directory of your choice [mia_install_dir]

           unzip populse_mia-master.zip -d [mia_install_dir]  # In this case [mia_install_dir] becomes [mia_install_dir]/populse_mia-master

  * Install the Python module distribution

        cd [mia_install_dir]  
        python3 setup.py install --user # Ensure that you use python >= 3.5 (use python3.x to be sure)  

  * To run populse_mia from the source code, don't remove it. Otherwise:

        cd ..  
        rm -r [mia_install_dir]  

 * From source, for Windows 10 distribution
 	 * First assure that you have activated the developer mode for Windows in the parameters : (```You will need administrator right for this```)
	 	* Click on start and parameters ;
		* Go in Update & Security ;
		* Click on For developer in the left column and activate the Sideload app ;
		* You might need to restart you computer.
	 * Open a PowerShell window on your computer :
	 	* Click on start menu and type "PowerShell" ;
		* Run the PowerShell application.
 	 * A compatible version of Python must be installed, to verify it, type in PowerShell :
	 	
			python3 -V
		
	 *Note : depending on your versions, you might need to use "python -V" instead of "python3 -V" to check you version of Python
	 
	 * If you don't have python, you need to install it :
	 
	 	1. In PowerShell type :
	 	
                python3

		2. The Microsoft Store will open with the Python 3.8 app. Click on install ;
		3. Install it on your computer ;
		4. Reopen PowerShell and check that Python and pip are installed :
	
			    python3 -V
			    pip3 --version
	 
	 * Install a Version Control System, for example [git](https://git-scm.com/download/win). Depending of your distribution, [package management system](https://en.wikipedia.org/wiki/Package_manager) can be different

	 	   Download the executable for your specific distribution (64 or 32 bits)
		   Execute it
		   You will be asked many questions depending on your preferences, but the default parameters are enough
		   
	  * At the end of the git installation you will need to restart PowerShell to refresh the environment
	  
      * Populse_mia requires java 64-bits for running, you can install it [here](https://java.com/fr/download/manual.jsp) :
      
            Download and run the file
            Follows the installation
        
      * Now you need to configure your java in order to be use by your system : (```You will need administrator right for this```)
      
        1. In PowerShell, open a system properties windows by typing :
        
                sysdm.cpl
        
        2. Click on the Advanced System Parameter ;
        3. Click on Environment Variable ;
        4. Select Path in system variable, and click on modify ;
        5. Click New ;
        6. Paste the path to the folder containing your java executable, it should look like this : 
                
                C:\Program Files\Java\jre1.8.0_251\bin
                
      * Enable the NTFS long path (```You will need administrator right for this```) :
      
        1. In PowerShell type : 
        
                gpedit.msc
                
        2. A Local Group Policy Editor window will open, then navigate to :
            --> Local Compute Policy
            --> Computer Configuration
            --> Administrator Template
            --> System
            --> FileSystem
            --> NTFS
        3. Double click Enable NTFS long path and enable it.
        
      * Populse_mia requires some specific package for Python and particularly numpy and PyQt5, you need to install them before launching the populse_mia installation :
      
            pip3 install numpy --user # Be sure to don't forget "--user" at the end of the command, otherwise you might get issues from administrator rights
            pip3 install PyQt5 --user

      * Get source codes from Github. Replace [mia_install_dir] with a directory of your choice

	        git lfs clone https://github.com/populse/populse_mia.git [mia_install_dir]

	  * Or download the zip file (populse_mia-master.zip) of the project ([green button "Clone or download"](https://github.com/populse/populse_mia)), then extract the data in the directory of your choice [mia_install_dir]

	        unzip populse_mia-master.zip -d [mia_install_dir]  # In this case [mia_install_dir] becomes [mia_install_dir]/populse_mia-master

	  * Install the Python module distribution

	         cd [mia_install_dir]  
	         python3 setup.py install --user # Ensure that you use python >= 3.5 | Be sure to don't forget "--user" at the end of the command, otherwise you might get	access issues from administrators rights.

# Usage

  * For all platforms: after a source installation, launching from the source code directory via command line

    * Interprets the main.py file

          cd [mia_install_dir]/python/populse_mia  
          python3 main.py  
    
    * Now, to configure your populse_mia, click on file and MIA preferences 
  	* In the Tools tab, enter the path to your project folder under Project preferences ;
	* Get sources code for MRI_conv from GitHub using HTTPS or SSH in the directory of your choice (the current directory or replace the [mri_install_dir] with the directory of your choice) :
	
			git lfs clone https://github.com/populse/mri_conv.git [mri_install_dir] # using HTTPS
			git lfs clone git@github.com:populse/mri_conv.git [mri_install_dir] # using SSH
		
	* In the Tools tab of the MIA preferences window in populse_mia, enter the absolute path to MRIManager.jar in the POPULSE third party preferences
		
			[mri_install_dir]/mri_conv/MRIFileManager/MRIManager.jar
		
	

        * Next, in the Pipeline tab of MIA preferences, check Use Matlab and enter the path to the matlab.exe file of your computer :
	
			../../Matlab/YourVersionOfMatlab/bin/matlab.exe
		
	    * In the Pipeline tab of MIA preferences, check Use SPM and enter the path to your spm folder :
	
			../../Matlab/spm12

  * For all platforms, after a [Populse_MIA’s user installation](https://populse.github.io/populse_mia/html/installation/user_installation.html)

        python3 -m populse_mia

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
