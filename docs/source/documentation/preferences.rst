.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/documentation/preferences.rst: WARNING: document isn't included in any toctree

:orphan:

.. toctree::

+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <./documentation.html>`_|`Installation <../installation/installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+


Populse_mia's preferences
=========================

This page is a user guide for populse_mia's preferences.

Access these preferences by going, when populse_mia is launched, to File > Mia preferences.

Populse_mia’s presentation
--------------------------

Populse_mia's preferences are composed of three tabs:

    * :ref:`tools-label`
        * Global preferences
    * :ref:`pipeline-label`
        * Matlab and SPM configuration
    * :ref:`appearance-label`
        * Software's appearance


.. _tools-label:

Tools
-----

.. image:: ../images/preferences_1.png
   :align: center
   :name: Preferences tools


Global preferences
^^^^^^^^^^^^^^^^^^

    * Auto save
        * When auto save is enabled, the project is saved after each actions done in the Data Browser.

    * Clinical mode
        * When ``Clinical mode`` is enabled, more default tags (ex. Age, Sex, Pathologie, etc.) are stored in the database.

    * Admin mode
        * Get extended rights (delete projects, processes, etc.).

    * Version 1 controller
        * If selected, uses the populse_mia V1 controller GUI. Otherwise, it uses the populse_mia V2 controller (based on caspul). In some cases, using the V1 controller will give better results than the V2.

    * Number of thumbnails in Data Browser
        * Set number of thumbnails wanted in Data Browser.

    * Radiological orientation in miniviewer (data browser)
        * Uses radiological orientation if selected. Otherwise, neurological orientation is used.


Projects preferences
^^^^^^^^^^^^^^^^^^^^

    * Projects folder
        * Sets the folder where the projects are stored.

    * Number of projects in ``Saved projects``
        * Sets the number of the visualized projects under ``Saved projects`` action of the menu bar (File > Saved projects).

POPULSE third party preferences
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    * Absolute path to MRIManager.jar
        * Sets the path to the executable file of MRI File Manager (usually stored in the "MRIFileManager" folder next to ``populse_mia`` install path, `if populse_mia was installed in user mode <../installation/user_installation.html>`_).
	   * e.g.  /home/user/.populse_mia/MRIFileManager/MRIManager.jar

External ressources preferences
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    * Some processes may require external data to function correctly (such as ROIs, templates, etc.). The folder containing this resource data can be defined here. The `following data <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miaresources>`_ can be used by default.

.. _pipeline-label:

Pipeline
--------

.. image:: ../images/preferences_2.png
   :align: center
   :name: Preferences pipeline

Third-party software path configuration. To use third-party software, it is of course necessary to `install it first <../installation/3rd-party_installations.html>`_.

Matlab
^^^^^^

    * Use Matlab: Activate it to use Matlab (license).
        * Matlab path: Sets the path to Matlab's executable.
            * e.g. for linux - macOS: ``/usr/local/MATLAB/R2018a/bin/matlab``
            * e.g. for Windows 10: ``C:/Program Files/Matlab/R2019a/bin/matlab.exe``

    * Use Matlab standalone: Activate it to use Matlab compiled version (MCR).
        * Matlab standalone path: Sets the path to Matlab's compiled version folder.
	    * e.g. for linux - macOS: ``/usr/local/MATLAB/MATLAB_Runtime/v97/``
	    * e.g. for Windows 10: Nothing to declare here if spm standalone is used!

SPM
^^^

    * Use SPM: Enable it if SPM12 (with Matlab license version) is used.
        * SPM path: Sets the path to SPM12 folder.
            * e.g. for linux - macOS: ``/usr/local/SPM/spm12``
	    * e.g. for Windows 10: ``C:/Program Files/Matlab/spm12``

    * Use SPM standalone: Enable it if SPM12 standalone version (with MCR) is used.
        * SPM standalone path: Sets the path to SPM12 standalone folder.
	    * e.g. for linux - macOS: ``/usr/local/SPM/spm12_standalone`` (folder containing run_spm12.sh).
	    * e.g. for Windows 10: ``C:/Program Files/Matlab/spm12_r7771/spm12`` (with Windows 10, it is not necessary to declare the above Matlab standalone path in this case!).

FSL
^^^

    * Use FSL: Enable it if FSL is used.
        * FSL path: Sets the path to the FSL config file (fsl_directory/etc/fslconf/fsl.sh).

AFNI
^^^^

    * Use AFNI: Enable it if AFNI is used.
        * AFNI path: Sets the path to the AFNI abin folder (AFNI_directory/abin).

ANTS
^^^^

    * Use ANTS: Enable it if ANTS is used.
        * ANTS path: Sets the path to the ANTS bin folder (ANTS_dir/bin).

FreeSurfer
^^^^^^^^^^

    * Use FreeSurfer: Enable it if FreeSurfer is used.
        * FreeSurfer path: Sets the path to the FreeSurferEnv.sh file (FreeSurfer_dir/FreeSurferEnv.sh).

.. _appearance-label:

Appearance
----------

.. image:: ../images/preferences_3.png
   :align: center
   :name: Preferences appearance

|

    * Background color
        * Changes the Populse_mia's background color.

    * Text color
        * Changes the Populse_mia's text color.

    * Use full screen
        * Use full screen.

    * Main window size
        * Change main window size
