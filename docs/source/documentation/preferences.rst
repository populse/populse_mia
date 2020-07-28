.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/documentation/preferences.rst: WARNING: document isn't included in any toctree

:orphan:

.. toctree::

+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <./documentation.html>`_|`Installation <../installation/installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+


Populse_MIA's preferences
=========================

This page is a user guide for Populse_MIA's preferences.

Software presentation
---------------------

Populse_MIA's preferences are composed of three tabs:

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

  * User mode
      * When user mode is enabled, more default tags are stored in the database and the process library is disabled (no pipeline creation).


Projects preferences
^^^^^^^^^^^^^^^^^^^^

  * Projects folder
      * Sets the folder where the projects are stored.

  * Number of projects in "Saved projects"
      * Sets the number of the visualized projects under "Saved projects" action of the menu bar.

POPULSE third party preferences
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  * Absolute path to MRIManager.jar
      * Sets the path to the executable file of MRI File Manager (usually stored in the "MRIFileManager" folder next to "populse_mia" install path, `if populse_mia was installed in user mode <../installation/user_installation.html>`_).
	 * e.g.  /home/ArthurBlair/.populse_mia/MRIFileManager/MRIManager.jar

.. _pipeline-label:

Pipeline
--------

.. image:: ../images/preferences_2.png
   :align: center
   :name: Preferences pipeline


Matlab
^^^^^^

  * Use Matlab
      * Enable it if you want to use Matlab (license or compiled version).

  * Matlab path
      * Sets the path to Matlab's executable
          * e.g. for linux - macOS: ``/usr/local/MATLAB/R2018a/bin/matlab``
	  * e.g. for Windows 10: ``C:/Program Files/Matlab/R2019a/bin/matlab.exe``

  * Matlab standalone path
      * Sets the path to Matlab's compiled version folder
	  * e.g. for linux - macOS: ``/usr/local/MATLAB/MATLAB_Runtime/v93/``
	  * e.g. for Windows 10: Nothing to declare here if you use spm standalone!

SPM
^^^

  * Use SPM
      * Enable it if you want to use SPM12 (license version).

  * SPM path
      * Sets the path to SPM12 folder
          * e.g. for linux - macOS: ``/usr/local/SPM/spm12``
	  * e.g. for Windows 10: ``C:/Program Files/Matlab/spm12``

  * Use SPM standalone
      * Enable it if you want to use SPM12 (standalone version).

  * SPM standalone path
      * Sets the path to SPM12 standalone folder
	  * e.g. for linux - macOS: ``/usr/local/SPM/spm12_standalone`` (folder containing run_spm12.sh)
	  * e.g. for Windows 10: ``C:/Program Files/Matlab/spm12_r7771/spm12`` (with Windows 10, it is not necessary to declare the above Matlab standalone path in this case!)

To use SPM standalone, please make sure to have it installed. To install it, please follow this `manual <https://en.wikibooks.org/wiki/SPM/Standalone>`_.

.. _appearance-label:

Appearance
----------

.. image:: ../images/preferences_3.png
   :align: center
   :name: Preferences appearance

| 

  * Background color
      * Changes the Populse_MIA's background color.

  * Text color
      * Changes the Populse_MIA's text color.

