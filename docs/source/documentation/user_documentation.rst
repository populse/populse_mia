.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/documentation/user_documentation.rst: WARNING: document isn't included in any toctree

:orphan:

.. toctree::

+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <./documentation.html>`_|`Installation <../installation/installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+


Populse_MIA's user documentation
================================

This page is a user guide for Populse_Mia.

A minimal data set (~500 MB, zip file with Bruker, Philips and NIfTI data) can be downloaded `here <https://gricad-gitlab.univ-grenoble-alpes.fr/condamie/miadatausers/-/archive/main/miadatausers-main.zip>`_ to allow users to quickly start using and testing Mia.

Software presentation
---------------------

Populse_MIA is composed of three main tabs:
  * The `Data Browser <./data_browser.html>`_ tab
      * Provides an overview of the data (image or non-image) available in the current analysis project (raw data and derived data)
  * The `Data Viewer <./data_viewer.html>`_ tab
      * An advanced viewer of up to 5-dimensional data, mostly but not exclusively MRI data, spectra,  plots linked to image and non-image data
  * The `Pipeline Manager <./pipeline_manager.html>`_ tab
      * An advanced graphical tool for building process pipelines (`see a complete example here <./pipeline_example.html>`_)

Populse_MIA uses a Populse third party software called `MRI File Manager <./mri_file_manager.html>`_) to import MRI data and convert them to Nifti/JSON format.

Remote parallel computing: see :doc:`the remote computing documentation <remote_computing>`.

Menu bar actions
----------------

* File
    * New project
        * Creates a new and empty analysis project (shortcut: Ctrl+N)
    * Open project
        * Opens a file browser dialog to open a project (shortcut: Ctrl+O)
    * Save project
        * Saves the current project (shortcut: Ctrl+S)
    * Save project as
        * Opens a file browser dialog to save the current project under a new name (shortcut: Maj+Ctrl+S)
    * Import
        * Opens the MRI File Manager to import data to the current project (shortcut: Ctrl+I)
    * Saved projects
        * Lists all the recent projects
    * MIA preferences
        * Opens the software preferences dialog (see preferences manual `here <./preferences.html>`_)
    * Project properties
        * Opens the project properties dialog
    * Package library manager
        * Opens the package library dialog
    * Exit
        * Quits the software (shortcut: Ctrl+W)
* Edit
    * Undo
        * Undoes the last action in Data Browser or Pipeline Manager (shortcut: Ctrl+Z)
    * Redo
        * Redoes the last action in Data Browser or Pipeline Manager (shortcut: Ctrl+Y)
* Help
    * Documentations
        * Links to the documentation
    * Credits
        * Credits
* About
* More
    * Install processes
        * From folder
            * Installs processes to the Process Library from a folder
        * From zip file
            * Installs processes to the Process Library from a zip file

.. toctree::
    :hidden:

    data_browser
    data_viewer
    pipeline_manager
    remote_computing
