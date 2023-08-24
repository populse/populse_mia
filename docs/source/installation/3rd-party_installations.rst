
:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+

Populse_mia's third-party softwares installations
=================================================

To use bricks and pipelines from `mia_processes <https://populse.github.io/mia_processes/html/index.html>`_ in populse_mia, it is necessary to install softwares as FSL, SPM, Freesurfer, ANTs...
The softwares paths should be configure in Mia preferences.



Installation on Linux
=====================

 * These installation notes are based on Ubuntu 22.04.02 which use Python3 as default (when you type ``python`` in a command line).

 * ``path/to/softs`` is the destination folder where you want to have the softwares installed, i.e.: ``/opt``, ``/home/APPS`` or what you want.

 * If you installed populse_mia in a container using `brainvisa Singulary image <./virtualisation_user_installation.html>`_, it is generally not necessary to be in the container to install third-party software (in fact, this will depend on the operating system in the container and the host).

Installation of `FSL v6.0.6.4 <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_
-------------------------------------------------------------------------

 * Download `fslinstaller.py <https://fsl.fmrib.ox.ac.uk/fsldownloads_registration/>`_ then launch the installer: ::

     python fslinstaller.py

 * The installer will ask you where do you want to install FSL, you can either keep the default location or indicate a folder: ::

    FSL installation directory [/home/username/fsl]: /path/to/softs/fsl-6.0.6.4/

 * populse_mia do not need environment variables, however if you want to test FSL outside populse_mia you need to check if the following lines are included in your ``~/bashrc`` (if not, put it): ::

     FSLDIR=/pathto/softs/FSL/6.04
     PATH=${FSLDIR}/bin:${PATH}
     export FSLDIR PATH
     . ${FSLDIR}/etc/fslconf/fsl.sh

   ``fsl.sh`` defines other environment variables for FSL like ``FSLOUTPUTTYPE=NIFTI-GZ``

 * Test FSL on a new terminal : ::

     flirt -version

Installation of `SPM 12 <https://www.fil.ion.ucl.ac.uk/spm/software/spm12/>`_ Standalone and Matlab Runtime
-----------------------------------------------------------------------------------------------------------

 * `Download <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/bids/>`_ the desired version of standalone SPM 12.

   Unzip it. For example: ::

	cd ~/Downloads/
	unzip  -d /path/to/soft/spmspm12_r7771_Linux_R2019b.zip


 * Download and install the corresponding R20xxa/b Matlab Runtime installation for linux `here <https://uk.mathworks.com/products/compiler/matlab-runtime.html>`_.

   * Unzip it: ::

	cd ~/Downloads
	unzip MATLAB_Runtime_R2019b_Update_9_glnxa64.zip

   * And then install it (sudo is only required if you install to a directory that you do not have write access to.): ::

        cd MATLAB_Runtime_R2019b_Update_3_glnxa64
	sudo ./install

   * After the installation, you get the following message (ex. for R2019b (9.7) Matlab Runtime): ::

        On the target computer, append the following to your LD_LIBRARY_PATH environment variable:
        /usr/local/MATLAB/MATLAB_Runtime/v97/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/extern/bin/glnxa64
        If MATLAB Runtime is to be used with MATLAB Production Server, you do not need to modify the above environment variable.

     Click on ``next`` in order to finish the installation.

   * Then if necessary, create a .conf file in the /etc/ld.so.conf.d/ folder and add those previous paths in the file: ::

        sudo nano /etc/ld.so.conf.d/your_lib.conf
	# Matlab 2019b Runtine Library
	/usr/local/MATLAB/MATLAB_Runtime/v97/runtime/glnxa64
	/usr/local/MATLAB/MATLAB_Runtime/v97/bin/glnxa64
	/usr/local/MATLAB/MATLAB_Runtime/v97/sys/os/glnxa64
	/usr/local/MATLAB/MATLAB_Runtime/v97/extern/bin/glnxa64

   * Run ldconfig to update the cache: ::

        sudo ldconfig

 * Check installation by exectuting SPM12, the second path being the path to the Matlab Runtime: ::

        spm12/run_spm12.sh /usr/local/MATLAB/MATLAB_Runtime/v97

 * Check this `manual <https://en.wikibooks.org/wiki/SPM/Standalone>`_ if you have trouble during installation.

Installation of `AFNI <https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/index.html>`_
-----------------------------------------------------------------------------------

  * Follow the `quick setup <https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/background_install/install_instructs/steps_linux_ubuntu20.html#quick-setup>`_ of the AFNI's team.

  * It will download all AFNI in your home. If you want you can move AFNI folders (abin, AFNI_data5, AFNI_data6, AFNI_demos, afni_handouts, CD, std_leshes, suma_demo, .afni) in an other folder (for e.g ``/path/to/folder/afni``). In this case, change the afni paths set in your bashrc.

Installation of `ANTs <http://stnava.github.io/ANTs/>`_
-------------------------------------------------------

  You can install ANTs via pre-built releases :

  * Dowloand pre-built releases `here <https://github.com/ANTsX/ANTs/tags>`_ and unzip it. Please note that if you want to use mriqc pipeline on populse_mia you need to choose ``v2.3.4``.

  * populse_mia do not need environment variables, however if you want to test ANTs outside populse_mia you need to add ANTs path in your .bashr.

Installation of `freesurfer <https://surfer.nmr.mgh.harvard.edu/>`_
-------------------------------------------------------------------

  * Follow the installation instruction `here <https://surfer.nmr.mgh.harvard.edu/fswiki//FS7_linux>`_. For Ubuntu systeme it is easier to use the tar archive. For Fedora, centos8 tar archive works fine

  * Get the freesurfer License `here <https://surfer.nmr.mgh.harvard.edu/registration.html>`_. Copy the license received in the freesurfer folder.

  * populse_mia do not need environment variables, however if you want to testfFreesurfer outside populse_mia you need to add freesurfer path in your .bashr.



Installation on Macos
=====================

Installation of `SPM 12 <https://www.fil.ion.ucl.ac.uk/spm/software/spm12/>`_ Standalone and Matlab Runtime
-----------------------------------------------------------------------------------------------------------

  * Download the spm12_r7532_BI_macOS_R2018b.zip `file <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/>`_. Unzip it. In the same directory where run_spm12.sh can be found unzip spm12_maci64.zip

  * Download the corresponding MCR for MATLAB Compiler Runtime (MCR) MCR_R2018b_maci64_installer.dmg.zip `file <https://fr.mathworks.com/products/compiler/matlab-runtime.html>`_

  * Start the MATLAB Runtime installer:
      * double click in MCRInstaller.dmg
      * then right click on MCRInstaller.pkg
      * then choose Open with > Installer (default).
	The MATLAB Runtime installer starts, it displays a dialog box.
	Read the information and then click ``Next`` (or ``continue``) to proceed with the installation.
      * Then click Install.
	The default MATLAB Runtime installation directory is now in ``/Applications/MATLAB/MATLAB_Compiler_Runtime/vXX``.

  * Usage: Go where run_spm12.sh file can be found, then just type: ::

        ./run_spm12.sh /Applications/MATLAB/MATLAB_Compiler_Runtime/vXX/

  * If No Java runtime is already installed, a pop-up is opened with a ``No Java runtime present, requesting install`` message.

      * Download `Java for OS X 2017-001 <https://support.apple.com/kb/DL1572?locale=en_US>`_.
      * Click on ``Download`` then Open with > DiskImageMounter (default) > Ok.
      * Right click on the JavaForOSX.pkg then choose Open with Installer (default).
      * The Java for OS X 2017-001 installer starts, it displays a dialog box. Answer the questions then install.

  * Tested on macOS 10.13.6:

    * The spm12_r7771.zip `file <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/>`_ and MCR v4.13 (MATLAB R2010a) MCRInstaller.dmg `file <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/MCR/maci64/>`_ are not compatible with mia (while `./run_spm12.sh /Applications/MATLAB/MATLAB_Compiler_Runtime/v713/ fmri` works fine in a terminal). Using this version of spm standalone, the following message is observed in MIA: `/Volumes/Users/econdami/Documents/spm/spm12Standalone/spm12Stndalone_r7771/run_spm12. sh: line 60: ./spm12.app/Contents/MacOS/spm12_maci64: No such file or directory`.

Installation of others software
-------------------------------

  Please follow the instruction in the documentation of each third-party software.



Installation on Windows
=======================

  Please follow the instruction in the documentation of each third-party software.
