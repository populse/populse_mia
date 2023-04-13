:orphan:

.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Mia's developer installation - Using virtualization
==============================================

The general installation process is to first, thanks to virtualization, make running BrainVisa on your system (see :ref:`prerequirements`).
Then, the installation will be almost identical to the one done directly on the host (see :ref:`installation`).

You can perform the installation by following the detailed instruction provided by `BrainVisa team (Developer environment installation section) <https://brainvisa.info/web/download.html#developer-environment-installation>`_. 
In this case, skip the :ref:`prerequirements` below and proceed directly to the :ref:`installation`. 
Depending on the solution you have chosen, go to the Singularity container or the VirtualBox virtual machine and then follow the :ref:`installation` section below.
For developer, it is recommended to use the Brainvisa developer image (casa_dev) in order to get the last version available of each project used in populse. 

You can also follow the full procedure below which uses Singularity virtualization technology. 



.. _prerequirements:

Pre-requirements
----------------

* `For linux <./virtualisation_pre_req_linux_developer.html>`_

* For macos, please follow the detailed instruction provided by `BrainVisa team (Developer environment installation section) <https://brainvisa.info/web/download.html#developer-environment-installation>`_.

* For Windows 10, please follow the detailed instruction provided by `BrainVisa team (Developer environment installation section) <https://brainvisa.info/web/download.html#developer-environment-installation>`_.


.. _installation:

Installation
------------

* If you followed `BrainVisa installation <https://brainvisa.info/web/download.html>`_ you should be in the container. Make sure to type the command ``bv bash`` if not.

* Inside the container, get the sources code by following the instructions detailed in the `installation part on host <./host_developer_installation.html#installation>`_. As capsul, populse_db, soma-base and soma-workflow are already in the Brainvisa developer image, it is not necessary to clone these projects. 