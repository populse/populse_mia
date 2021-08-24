.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/user_installation.rst: WARNING: document isn't included in any toctree

:orphan:

.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_mia's user installation
===============================

Pre-requirements
----------------

* `For linux - macOS <./pre_req_linux.html>`_

|

* `For Windows 10 <./pre_req_windows10.html>`_

Installation
------------

* First download the archive `here <https://github.com/servoz/populse_mia_install/archive/master.zip>`_.

|

* Unzip it and launch the following command in the extracted folder ("populse_mia_install-master"): ::

        python3 install_mia.py

|

* If PyQt5 and pyyaml are not installed in your Python environment they will be first installed before launching the populse_mia's installation. 

.. image:: ../images/mia_install_1.png
   :align: center
   :name: PyQt5 and pyyaml

|
	  
* An error can sometimes occur, depending on your OS, after the installation of both packages, the Python environment not being correctly updated. If this error occurs launch the same command again to install populse_mia: ::

        python3 install_mia.py

|

* The populse_mia installation is now launched and you have to select three mandatory parameters:

  * Populse_mia installation path: the folder where to install few directories and files necessary for the operation of populse_mia, set by default to ".populse_mia" in the current user's directory. Two folders will be created in the selected folder

    * populse_mia: containing populse_mia's configuration and resources files.

    * MRIFileManager: containing the file converter used in Populse_MIA.

  * Populse_mia projects path: the folder containing the analysis projects saved in populse_mia. A "projects" folder will be created in the selected folder.

  * Operating mode: Choose between clinical and research mode (more information about `operating mode <../documentation/documentation.html#operating-mode>`_).

|

* If you already want to configure the use of Matlab and SPM (in license or standalone mode), you can also specify these several paths:

  * Matlab path:

    * Path of the Matlab executable file (is detected automatically).

      * e.g. for linux - macOS: /usr/local/MATLAB/R2018a/bin/matlab

      * e.g. for Windows 10: C:/Program Files/Matlab/R2019a/bin/matlab.exe

  * Matlab standalone path:

    * Path of the folder containing Matlab Compiler Runtine.

      * e.g. for linux - macOS: /usr/local/MATLAB/MATLAB_Runtime/v93/

      * e.g. for Windows 10: Nothing to declare here if you use spm standalone!

  * SPM path:

    * Path of the folder containing SPM12 code.

      * e.g. for linux - macOS: /usr/local/SPM/spm12

      * e.g. for Windows 10: C:/Program Files/Matlab/spm12

  * SPM standalone path:

    * Path to SPM12 standalone folder.

      * e.g. for linux - macOS: /usr/local/SPM/spm12_standalone (folder containing run_spm12.sh)

      * e.g. for Windows 10: C:/Program Files/Matlab/spm12_r7771/spm12 (with Windows 10, it is not necessary to declare the above Matlab standalone path in this case!)

.. image:: ../images/mia_install_2.png
   :align: center
   :name: Populse_MIA install widge

|

* Click on "Install" to install populse_mia with the selected parameters.

|

* The installation status is displayed. The last step (Python packages installation) may take a few minutes.

.. image:: ../images/mia_install_3.png
   :align: center
   :name: Populse_MIA install widget status

|

* When the packages have been installed, a summary of the installation is displayed.

.. image:: ../images/mia_install_4.png
   :align: center
   :name: Populse_MIA install widget summary

|

* See the `Usage chapter on the GitHub page <https://github.com/populse/populse_mia>`_ to launch populse_mia.














