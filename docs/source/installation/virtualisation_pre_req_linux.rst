
:orphan:

.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+

Pre-requirements for virtualization using Brainvisa - Linux
============================================================

With Linux, `Singularity <https://sylabs.io/singularity/>`_ seems to work perfectly well.

Given the characteristics of the 2 proposed technologies (`singularity container or virtual machine <https://www.geeksforgeeks.org/difference-between-virtual-machines-and-containers/>`_) it is clear that it is better to use a container for performance reasons.

In the following we propose exclusively for Linux the use of a Singularity container.

.. _singularity_installation:

Install Singularity
-------------------

**Fedora**

Singularity is available in the Fedora repositories.

.. code-block:: bash

   % dnf info singularity
   Last metadata expiration check: 0:01:58 ago on Tue 05 Jul 2022 01:41:01 PM CEST.
   Installed Packages
   Name         : singularity
   Version      : 3.8.4
   Release      : 1.fc33
   Architecture : x86_64
   Size         : 123 M
   Source       : singularity-3.8.4-1.fc33.src.rpm
   Repository   : @System
   From repo    : updates
   Summary      : Application and environment virtualization
   URL          : https://singularity.hpcng.org
   License      : BSD-3-Clause-LBNL
   Description  : Singularity provides functionality to make portable
                : containers that can be used across host environments.


Check that Singularity is already installed in your station:

.. code-block:: bash

   % singularity version
   3.8.4-1.fc33

If Singularity is not already installed:

.. code-block:: bash

   % sudo dnf install singularity  # sudo dnf install singularity-ce, for recent versions of singularity


**Ubuntu**

To date, no suitable version of Singularity is available as system package for Ubuntu.

You can `install it yourself <https://docs.sylabs.io/guides/latest/admin-guide/installation.html#install-from-source>`_.

However, `we advise you to use the package provided by BrainVisa <https://brainvisa.info/download/>`_, corresponding to your OS.
For example download singularity-ce_3.8.3~ubuntu-20.04_amd64.deb then :

.. code-block:: bash

   % sudo dpkg -i singularity-ce_3.8.3~ubuntu-20.04_amd64.deb


Then, check that Singularity is well installed on your station:

.. code-block:: bash

   % singularity -- version


After installing singularity in your station
----------------------------------------------

`Reminder: Two softwares must be installed: Python (version >= 3.7) and Singularity (version > 3.6).`

Open a shell, then:

.. code-block:: bash

   mkdir -p $HOME/brainvisa-5 # create an installation directory

`Download the latest BrainVISA image <https://brainvisa.info/download/>`_ found in brainvisa site into this new directory (ex. brainvisa-5.0.4.sif).

In the opened shell:

.. code-block:: bash

   singularity run -B $HOME/brainvisa-5:/casa/setup $HOME/brainvisa-5/brainvisa-5.0.4.sif # Run Singularity using the downloaded image
   echo 'export PATH=${HOME}/brainvisa-5/bin:${PATH}' >> $HOME/.bashrc # set the bin/ directory of the installation directory in the PATH environment variable

Optionally, you can launch the graphical configuration interface, e.g. to define mounting points, etc:

.. code-block:: bash

   bv

Build from the container terminal (after `bv bash`) or outside the container:

.. code-block:: bash

   bv_maker

Then open an interactive shell in the container:

.. code-block:: bash

   bv bash

And continue with the `Installation part <./virtualisation_user_installation.html#Installation>`_ ...
