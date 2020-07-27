.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/windows10_installation.rst: WARNING: document isn't included in any toctree
:orphan:
.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+

Populse_mia's developer installation for windows 10
===================================================

* First, assure that you activated the developer mode in the parameters:

.. warning::

  This operation needs administrator rights

  * Click on Start --> Parameters
  * Go in Update and Security

  .. image:: /images/update_and_security.png
    :width: 400
    :align: center

  * Click on Developer environment in the left column and activate the Sideload app;

  .. image:: ../images/developer_mode.png
    :width: 400
    :align: center

  * You might need to restart your computer

* When you restarted your computer, open a PowerShell window on your computer:

  * Click on the Start menu and type "PowerShell"

  .. image:: ../images/open_powershell.jpg
    :width: 300
    :align: center

  * Run the PowerShell application.

* Make sure you have Python installed. You can verify it by typing in PowerShell: ::

    python3 -V

  *Note : depending on your versions, you might need to use `python -V` instead on `python3 -V` to check your version of Python.*

  * If Python is not installed:

    1. In PowerShell, type: ::

        python3

    2. The Microsoft Store will open on the Python 3.8 app, click on Install:

    .. image:: ../images/Python3.8.png
      :width: 500
      :align: center

    3. Check in the shell PowerShell that Python and pip (pip is normally include in the install of Python) are installed: ::

       python3 -V
       pip3 --version

* Make sure you have Git installed. You can verify it by typing in PowerShell: ::

    git --version

  * If Git is not installed, you need to install it (`Here <https://git-scm.com/download/win>`_): ::

      Download the executable for your specific distribution (64 or 32 bits).
      Run it.
      You will be asked many questions depending on you preferences, but the default parameters are enough.

  * At the end of the git installation, you will need to restart PowerShell to restart the environment and be able to use Git.

* During the install, you will need C++ Build tools. You can get it by installing Visual Studio Build Tools 2019 and select C++ Build tools (`Here <https://www.microsoft.com/fr-fr/download/details.aspx?id=58317>`_): ::

  1. Download the executable file and run it.

  2.The installation is in two parts, at the end of the first part a window with every module in charge by Visual Studio will open:

  .. image:: ../images/vs_Build.png
      :width: 500
      :align: center

  3. Select the C++ Build Tools and install it.

* Install java 64-bits for Windows (`Here <https://java.com/fr/download/manual.jsp>`_): ::

    Download the offline (64 bits) file and run it
    Follow the installation

* Now you need to configure your java in order to be used by your system and PowerShell:

.. warning::

  This operation needs administrator rights

    1. In PowerShell, open a system properties window by typing: ::

        sysdm.cpl

    2. Click on the Advanced System Parameter;

    .. image:: ../images/ASP_system_tab.png
      :width: 500
      :align: center

    3. Click on Environment Variable ;

    4. Select Path in the system variables, and click on modify;

    .. image:: ../images/env_var.png
      :width: 500
      :align: center

    5. Click on New;

    6. Paste the path to the folder containing YOUR java executable, it should LOOK like this: ::

        C:\Program Files\Java\jre1.8.0_251\bin

* Enable the NTFS long path:

 .. warning::

    This operation needs administrator rights

    1. In PowerShell type: ::

        gpedit.msc

    2. A Local Group Policy Editor window will open, then Navigate to:

      --> Local Compute Policy
      --> Computer Configuration
      --> Administrator Templates
      --> System
      --> FileSystem
      --> NTFS

    3. Double click on Enable NTFS long path and enable it.

    .. image:: ../images/NTFS.png
      :width: 500
      :align: center

* Populse_mia requires some specific package for Python and particularly numpy and PyQt5, you need to install them before launching the populse_mia installation: ::

    pip3 install numpy --user # be sure to doin't forget the "\--user" at the end of the command, otherwise you might get issues from administrator rights
    pip3 install PyQt5

* Get sources code from GitHub using HTTS or SSH in the directory of your choice (the current directory or replace the [mia_install_dir] with the directory of your choice): ::

    git lfs clone https://github.com/populse/populse_mia.git [mia_install_dir] # using HTTPS
    git lfs clone git@github.com:populse/populse_mia.git [mia_install_dir] # using SSH

* Then, install the Python module distribution: ::

    cd [mia_install_dir]
    python3 setup.py install --user

  *Note : make sure to don't forget '\--user' at the end of the command. If not you might get access errors linked with administrators rights.

* Then, run Populse_mia :

  * By interpreting the main.py file: ::

      cd [mia_install_dir]/python/populse_mia
      python3 main.py

  * By launching the package with python: ::

      python3 -m populse_mia

* Now, configure you populse_mia, click on file and MIA preferences:

  * In the Tools tab, enter the path to your project folder in the Projects preferences.

  .. image:: ../images/tool_tab.png
    :width: 400
    :align: center

  * Get sources code for MRI_conv from GitHub using HTTS or SSH in the directory of your choice (the current directory or replace the [mri_install_dir] with the directory of your choice): ::

      git lfs clone https://github.com/populse/mri_conv.git [mri_install_directory] # using HTTPS
      git lfs clone git@github.com:populse/mri_conv.git [mri_install_directory] # using SSH

  * In the Tools tab of the MIA preferences window in populse_mia, enter the absolute path to MRIManager.jar in the POPULSE third party preferences: ::

    [mri_install_dir]/mri_conv/MRIFileManager/MRIManager.jar

  * Next, in the Pipeline tab of MIA preferences, check Use Matlab and enter the path to the matlab.exe file of your computer: ::

    ../../Matlab/YourVersionOfMatlab/bin/matlab.exe

    .. image:: ../images/pipeline_tab.png
      :width: 400
      :align: center

  * In the Pipeline tab of MIA preferences, if you have licensed SPM version check Use SPM and enter the path to your spm folder: ::

    ../../Matlab/spm12

  * In the Pipeline tab of MIA preferences, if you have standalone SPM version check Use SPM Standalone and enter the path to your spm12 folde: ::

    ../../spm12_r****/spm12

      *Note : in this scenario you only need to check Use SPM Standalone in the Pipeline tab MIA preferences.

* For developing process, make sure to work on your own branch ::

      git checkout -b your_branch_name # creates your own branch locally
      git push -u origin your_branch_name # creates your own branch remotely

|
|
|
|

``Coming from old README:``
 * From source, for Windows 10 distribution, please see [Populse_MIA’s developer installation](https://populse.github.io/populse_mia/html/installation/developer_installation.html)
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

