

:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+

Populse_mia's developer installation on host
============================================

Pre-requirements
----------------

* `For linux - macOS <./host_pre_req_linux_macos.html>`_

* `For Windows 10 <./host_pre_req_windows10.html>`_

Installation
------------

**Installation by cloning the source codes**

`populse_mia <https://github.com/populse/populse_mia>`__ sources can be found on gihub.

To use the whole populse project in developer mode on host (and have the latest versions available), it will be necessary to clone all this projects:
    |   - `populse_mia <https://github.com/populse/populse_mia>`__
    |   - `capsul <https://github.com/populse/capsul>`_
    |   - `mia_processes <https://github.com/populse/mia_processes>`__
    |   - `mri_conv <https://github.com/populse/mri_conv>`_
    |   - `populse_db <https://github.com/populse/populse_db>`_
    |   - `soma-workflow <https://github.com/populse//soma-workflow>`_
    |   - `soma-base <https://github.com/populse//soma-base>`_

* For each project:

  * Get source codes from Github. Replace [populse_install_dir] with a directory of your choice. For example for populse_mia: ::

      git clone https://github.com/populse/populse_mia.git [populse_install_dir]/populse_mia

  * Or download the zip file (for example populse_mia-master.zip) of the project (green button "Code", Download ZIP in Github), then extract the data in the directory of your choice [populse_install_dir]: ::

      unzip populse_mia-master.zip -d [populse_install_dir]
      mv [populse_install_dir]/populse_mia-master [populse_install_dir]/populse_mia

|

* You can also download the following folders:

      * `miaresources <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miaresources>`_ : it contains usefull resources like templates for mia_processes (necessary to run correctly bricks and pipeline). To add to Mia preferences (external resources).

      * `miautdata <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miautdata>`_ : it contains data for unit tests in populse_mia

      * `miadatausers <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miadatausers>`_ : it contains initial user data for using / testing Mia

|

* To launch populse_mia: ::

      python '[populse_install_dir]/populse_mia/populse_mia/main.py'

|

* In development mode the libraries needed for populse_mia  and mia_processes are not installed as with pip. So depending on the libraries already installed on your station it may be necessary to complete this installation. Please refer to the Requirements chapter on the Github page for `populse_mia <https://github.com/populse/populse_mia#requirements>`_  and for `mia_processes <https://github.com/populse/mia_processes/blob/master/README.md#requirements>`__  to install the necessary third party libraries.


  * Third party librairies installation, e.g. for nibabel ::

      pip3 install nibabel --user

|

* For some libraries a special version is required. In case of problems when launching populse_mia, please check that all versions of third party libraries are respected by consulting the REQUIRES object in the `populse_mia info.py <https://github.com/populse/populse_mia/blob/master/python/populse_mia/info.py>`_  and `mia_processes info.py <https://github.com/populse/mia_processes/blob/master/mia_processes/info.py>`_ module.

  * e.g. for traits ::

      pip3 install traits==5.2.0 --user # The traits librairy is not yet installed
      Pip3 install --force-reinstall traits==5.2.0 --user  # The traits librairy is already installed

|

* If, in spite of that, you observe an ImportError exception at launch ... Well ... you will have to install the involved library (see the two steps above). In this case, please send us a message (populse-support@univ-grenoble-alpes.fr) so that we can update the list of third party libraries needed to run populse_mia properly.

|

* On first launch after a developer installation, please `refer to the preferences page <../documentation/preferences.html>`_ to configure populse_mia.

|

**Installation by using mia_install project**

In order to avoid dependencies issues, it is possible to first install populse_mia as an user by using `mia_install project <https://github.com/populse/mia_install>`_, then remove all the populse_mia projects and finally clone the sources to have the latest version available.
All the dependencies should be install with populse_mia project.

* Install populse_mia with mia_install project following `user installation <./host_user_installation.html>`_. This step will allow the installation of all the dependencies needed.

|

* Uninstall the libraries from populse project (capsul, mia_processes, populse_db, populse_mia, soma-base, soma-workflow): ::

      pip uninstall populse_mia

|

* Remove the ./populse_mia folder: ::

      rm -Rf /home/username/.populse_mia/

|

* Clone sources as described in the "Installation by cloning the source codes" part above.

|

* To launch populse_mia: ::

      python '[populse_install_dir]/populse_mia/populse_mia/main.py'

|

* On first launch after a developer installation, please `refer to the preferences page <../documentation/preferences.html>`_ to configure populse_mia.

|

* You can also download the following folders:

      * `miaresources <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miaresources>`_ : it contains usefull resources like templates for mia_processes (necessary to run correctly bricks and pipeline). To add to Mia preferences (external resources).

      * `miautdata <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miautdata>`_ : it contains data for unit tests in populse_mia

      * `miadatausers <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miadatausers>`_ : it contains initial user data for using / testing Mia
