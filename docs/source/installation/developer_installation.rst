.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/linux_installation.rst: WARNING: document isn't included in any toctree

:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_mia's developer installation
====================================

Pre-requirements
----------------

* `For linux - macOS <./pre_req_linux.html>`_

|

* `For Windows 10 <./pre_req_windows10.html>`_

Installation
------------

* Clone the source codes

  * Get source codes from Github. Replace [populse_install_dir] with a directory of your choice ::

      git lfs clone https://github.com/populse/populse_mia.git [populse_install_dir]/populse_mia # "git lfs clone" has been deprecated since Git LFS 2.3.0. From this version, use "git clone" command directly ...

  * Or download the zip file (populse_mia-master.zip) of the project (`green button "Code" <https://github.com/populse/populse_mia>`_, Download ZIP), then extract the data in the directory of your choice [populse_install_dir] ::

      unzip populse_mia-master.zip -d [populse_install_dir]
      mv [populse_install_dir]/populse_mia-master [populse_install_dir]/populse_mia

|

* To use the whole populse project in developer mode (and have the latest versions available), repeat the previous step for all other populse packages (`capsul <https://github.com/populse/capsul>`_, `mia_processes <https://github.com/populse/mia_processes>`_, `mri_conv <https://github.com/populse/mri_conv>`_, `populse_db <https://github.com/populse/populse_db>`_, `soma-workflow <https://github.com/populse//soma-workflow>`_ and `soma-base <https://github.com/populse//soma-base>`_:

  * e.g. for capsul:

    * Get source codes from Github. Replace [populse_install_dir] with a directory of your choice ::

        git lfs clone https://github.com/populse/capsul.git [populse_install_dir]/capsul # "git lfs clone" has been deprecated since Git LFS 2.3.0. From this version, use "git clone" command directly ...

    * Or download the zip file (capsul-master.zip) of the project (`green button "Code" <https://github.com/populse/capsul>`_, Download ZIP), then extract the data in the directory of your choice [populse_install_dir] ::

        unzip capsul-master.zip -d [populse_install_dir]
	mv [populse_install_dir]/capsul-master [populse_install_dir]/capsul

|

* See the `Usage chapter on the GitHub page <https://github.com/populse/populse_mia#usage>`_ to launch populse_mia

|

* In development mode the libraries needed for populse_mia are not installed as with pip. So depending on the libraries already installed on your station it may be necessary to complete this installation. Please refer to the `Requirements chapter on the Github page <https://github.com/populse/populse_mia#requirements>`_ to install the necessary third party libraries.

  * e.g. for nibabel ::

      pip3 install nibabel --user

|

* For some libraries a special version is required. In case of problems when launching populse_mia, please check that all versions of third party libraries are respected by consulting the REQUIRES object in the `info.py <https://github.com/populse/populse_mia/blob/master/python/populse_mia/info.py>`_ module.

  * e.g. for traits ::

      pip3 install traits==5.2.0 --user # The traits librairy is not yet installed
      Pip3 install --force-reinstall traits==5.2.0 --user  # The traits librairy is already installed

|

* If, in spite of that, you observe an ImportError exception at launch ... Well ... you will have to install the involved library (see the two steps above). In this case, please send us a message (populse-support@univ-grenoble-alpes.fr) so that we can update the list of third party libraries needed to run populse_mia properly.

|

* On first launch after a developer installation, please `refer to the preferences page <../documentation/preferences.html>`_ to configure populse_mia.
