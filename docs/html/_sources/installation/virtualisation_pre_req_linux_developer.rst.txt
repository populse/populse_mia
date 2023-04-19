
:orphan:

.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+

Pre-requirements for virtualization developer- Linux
==============================================

With Linux, `Singularity <https://sylabs.io/singularity/>`_ seems to work perfectly well.

Given the characteristics of the 2 proposed technologies (`singularity container or virtual machine <https://www.geeksforgeeks.org/difference-between-virtual-machines-and-containers/>`_) it is clear that it is better to use a container for performance reasons.

In the following we propose exclusively for Linux the use of a Singularity container.

Install Singularity
-------------------

Install singularity `as for user installation <./virtualisation_pre_req_linux.html#singularity_installation>`_

After installing singularity in your station
----------------------------------------------

`Reminder: Two softwares must be installed: Python (version >= 3.7) and Singularity (version > 3.6).`

**Install Read only_container**

Open a shell, then:

.. code-block:: bash

   mkdir -p $HOME/casa_distro/brainvisa-opensource-master # create an installation directory

`Download the latest BrainVISA developer image (casa-dev) <https://brainvisa.info/download/>`_ found in brainvisa site into this new directory (ex. casa-dev-5.4.4.sif).

In the opened shell, execute the container image:

.. code-block:: bash

   singularity run -c -B $HOME/casa_distro/brainvisa-opensource-master:/casa/setup $HOME/casa_distro/casa-dev-5.4.4.sif branch=master distro=opensource # Run Singularity using the downloaded image
   echo 'export PATH="$HOME/casa_distro/brainvisa-opensource-master/bin:$PATH"' >> $HOME/.bashrc # set the bin/ directory of the installation directory in the PATH environment variable

Optionally, you can launch the graphical configuration interface, e.g. to define mounting points, etc:

.. code-block:: bash

   bv

Then open an interactive shell in the container:

.. code-block:: bash

   bv bash

And build from within the terminal (it may take some time ):

.. code-block:: bash

   bv_maker

And continue with the `Installation part <./virtualisation_developer_installation.html#Installation>`_ 


**Create a container within a writable directory**

Only if you need to add librairies with apt in your container. 
  - sudo singularity build --sandbox $HOME/casa_distro/casa-dev-5.3-6_wr $HOME/casa_distro/casa-dev-5.3-6.sif # to make an editable image (casa-dev-5.3-6_wr)
  - sudo singularity run --writable $HOME/casa_distro/casa-dev-5.3-6_wr bash # to modify the image
  - "It is now possible to modify the image. For example let's update all packages and install emacs:"
  - Singularity> apt update  # Singularity> is the prompt
  - Singularity> apt-get install -y software-properties-common
  - Singularity> add-apt-repository ppa:kelleyk/emacs
  - Singularity> apt install emacs26
  - "Edit the $HOME/casa_distro/brainvisa-opensource-master/conf/casa_distro.json file and change the value of the `image` key (ex. "image": "/home/econdami/casa_distro/casa-dev-5.3-6_wr" in place of "image": "/home/econdami/casa_distro/casa-dev-5.3-6.sif")"
  - "Then using `bv` or `bv bash` will use the casa-dev-5.3-6_wr image"
