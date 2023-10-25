
:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+

Populse_mia's third-party softwares installations
=================================================

To use bricks and pipelines from `mia_processes <https://populse.github.io/mia_processes/html/index.html>`_ in populse_mia, it is necessary to install softwares as FSL, SPM, Freesurfer, ANTs...
The softwares paths should be configure in `Mia preferences <../documentation/preferences.html>`_.



Installation on Linux
=====================

 * These installation notes are based on Ubuntu 22.04.02 (and Fedora 37) which use Python3 as default (when ``python`` is typed into a command line).

 * ``/path/to/softs`` is the destination folder where the softwares will be installed, i.e.: ``/opt``, ``/home/APPS`` or other.

 * If populse_mia is installed in a container using `brainvisa Singulary image <./virtualisation_user_installation.html>`_, it's generally not necessary to be inside the container to install third-party softwares (installation on the host may be enough, but this depends on the container's operating system and the host).

 * Populse_mia needs no environment variables, however to test installed third-party softwares outside populse_mia, the following lines must be included in the user's ``.bashrc`` file, or, depending on the operating system, any other script file executed when a user logs on (we recommend not to use these environment variables when using populse_mia by commenting the corresponding lines in the ~/.bashrc file). It may be necessary to open a new shell or restart a session (logout / login) or execute the contents of the .bashrc file (source ~/.bashrc) for the changes to take effect: ::

    # FSL setup
    # FSL configuration is done in /home/user/.bash_profile and /home/user/Documents/MATLAB/startup.m
    export PATH="$PATH:/path/to/softs/fsl_you_have_installed/bin"
    export FSLOUTPUTTYPE=NIFTI
    export FSLDIR=/path/to/softs/fsl_you_have_installed

    # AFNI setup
    ## auto-inserted by @update.afni.binaries:
    export PATH=$PATH:/path/to/softs/AFNI_you_have_installed/abin
    ## auto-inserted by @update.afni.binaries :
    ##    set up tab completion for AFNI programs
    if [ -f $HOME/.afni/help/all_progs.COMP.bash ]
    then
       source $HOME/.afni/help/all_progs.COMP.bash
    fi
    export R_LIBS=/path/to/softs/AFNI_you_have_installed/R

    # ANTS setup
    export ANTSPATH=/path/to/softs/ANTS_you_have_installed
    export PATH="$ANTSPATH:$PATH"
    # The following three lines should not be commented on, in order to obtain perfectly reproducible results with ANTS (as with the MRIQC pipeline, for example).
    export ANTS_RANDOM_SEED=1
    export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1
    export OMP_NUM_THREADS=1

    # Freesurfer setup
    export FREESURFER_HOME=/path/to/softs/FreeSurfer_you_have_installed
    source $FREESURFER_HOME/SetUpFreeSurfer.csh>/dev/null


Installation of `SPM 12 <https://www.fil.ion.ucl.ac.uk/spm/software/spm12/>`_ Standalone and Matlab Runtime
-----------------------------------------------------------------------------------------------------------

 * `Download <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/bids/>`_ the desired version of standalone SPM 12.

   Unzip it. For example: ::

	cd ~/Downloads/
	unzip spm12_r7771_Linux_R2019b.zip -d /path/to/soft/spmStandalone


 * Download and install the corresponding R20xxa/b Matlab Runtime installation for linux `here <https://uk.mathworks.com/products/compiler/matlab-runtime.html>`__.

   * Unzip it: ::

	cd ~/Downloads
	unzip MATLAB_Runtime_R2019b_Update_9_glnxa64.zip

   * And then install it (sudo is only required to install in a directory without write access): ::

        cd MATLAB_Runtime_R2019b_Update_3_glnxa64
	sudo ./install

   * After the installation, the following message is observed (ex. for R2019b (9.7) Matlab Runtime): ::

        On the target computer, append the following to your LD_LIBRARY_PATH environment variable:
        /usr/local/MATLAB/MATLAB_Runtime/v97/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/extern/bin/glnxa64
        If MATLAB Runtime is to be used with MATLAB Production Server, you do not need to modify the above environment variable.

     Click on ``next`` in order to finish the installation.

   * Then if necessary (optional), create a .conf file in the /etc/ld.so.conf.d/ folder and add those previous paths in the file: ::

        sudo nano /etc/ld.so.conf.d/your_lib.conf
	# Matlab 2019b Runtine Library
	/usr/local/MATLAB/MATLAB_Runtime/v97/runtime/glnxa64
	/usr/local/MATLAB/MATLAB_Runtime/v97/bin/glnxa64
	/usr/local/MATLAB/MATLAB_Runtime/v97/sys/os/glnxa64
	/usr/local/MATLAB/MATLAB_Runtime/v97/extern/bin/glnxa64

   * Run ldconfig to update the cache (optional): ::

        sudo ldconfig

   * Check this `manual <https://en.wikibooks.org/wiki/SPM/Standalone>`_ in case of problems during installation.

   * Test SPM12 Standalone and MCR installation (the second path being the path to the Matlab Runtime): ::

         /path/to/spm_standalone/spm12/run_spm12.sh /path/to/MATLAB_Runtime/v97 eval "ver"


Installation of `FSL <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_
----------------------------------------------------------------

 * Download `fslinstaller.py <https://fsl.fmrib.ox.ac.uk/fsldownloads_registration/>`_ (with Fedora 37, choose Linux - Centos 8) then launch the installer: ::

     python fslinstaller.py

 * The installer will ask where to install FSL. Keep the default location or specify a folder: ::

    FSL installation directory [/home/username/fsl]: /path/to/softs/fsl-6.0.6.4/

 * It seems that some versions of the installer automatically add the FSL configuration to ~/.bash_profile. We recommend not to use these environment variables when using populse_mia (comment out the corresponding lines in the  ~/.bash_profile).

 * Test FSL installation on a new terminal: ::

     /path/to/softs/fsl-6.0.6.4/bin/flirt -version


Installation of `AFNI <https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/index.html>`_
-----------------------------------------------------------------------------------

  * For Ubuntu, follow the `quick setup <https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/background_install/install_instructs/steps_linux_ubuntu20.html#quick-setup>`_ of the AFNI's team. For Fedora 37, select the ``Linux, Fedora`` chapter in the table of contents on the left.

  * By default, all data will be installed in $HOME. $HOME/abin can then be moved to a directory dedicated to AFNI (e.g. /data/softs/AFNI). The rest of the data installed in $HOME can be deleted if AFNI is to be used only in Mia.

  * Test AFNI on a new terminal: ::

      /path/to/softs/AFNI_you_have_installed/abin/afni -ver


Installation of `ANTs <http://stnava.github.io/ANTs/>`_
-------------------------------------------------------

  * We strongly recommend installing ANTs via release binaries, available for macos and linux (ubuntu, centos - fedora) from ANTs ``v2.4.1``, and Windows from ``v2.4.4``. For this, `download pre-built releases <https://github.com/ANTsX/ANTs/releases>`_ (select the desired file in the ``Assets`` section, e.g. ants-2.4.1-centos7-X64-gcc.zip) then unzip it. `Some notes <https://github.com/ANTsX/ANTs/wiki/Installing-ANTs-release-binaries>`__ on this subject are available.

  * ANTs since ``v2.4.4`` is also available `via Conda <https://anaconda.org/aramislab/ants>`_.

  * The final solution for installing ANTs is to build it from source (e.g. for release < ``v2.4.1`` `for linux and macos <https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS>`_ and release < ``v2.4.4`` `for windows <https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Windows-10>`_).

  *  Test ANTs on a new terminal: ::

        /path/to/softs/ANTs_you_have_installed/bin/antsRegistration --version


Installation of `FreeSurfer <https://surfer.nmr.mgh.harvard.edu/>`_
-------------------------------------------------------------------

  * Go to the `FreeSurfer Download and Install <https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall>`_ page.

  * Choose the version to install (we strongly recommend installing the latest version), for example at the time of writing, `version 7.x <https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads>`_.

  * Select the packages or tarballs you wish to download to proceed with the installation. `Some notes <https://surfer.nmr.mgh.harvard.edu/fswiki/FS7_linux>`__ on this subject are available.

  * For Fedora 37, centos8 tar archive works fine.

  * Get the freesurfer License `here <https://surfer.nmr.mgh.harvard.edu/registration.html>`__. Copy the license received in the freesurfer folder.

  * Test FreeSurfer on a new terminal: ::

       /path/to/softs/FreeSurfer_you_have_installed/bin/mris_register --version


Installation of `MRtrix  <https://www.mrtrix.org/>`_
----------------------------------------------------

  * `WIP! <https://www.mrtrix.org/download/>`_


Installation on Macos
=====================

Installation of `SPM 12 <https://www.fil.ion.ucl.ac.uk/spm/software/spm12/>`_ Standalone and Matlab Runtime
-----------------------------------------------------------------------------------------------------------

  * Download the spm12_r7532_BI_macOS_R2018b.zip `file <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/>`__. Unzip it. In the same directory where run_spm12.sh can be found unzip spm12_maci64.zip.

  * Download the corresponding MCR for MATLAB Compiler Runtime (MCR) MCR_R2018b_maci64_installer.dmg.zip `file <https://fr.mathworks.com/products/compiler/matlab-runtime.html>`__.

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

    * The spm12_r7771.zip `file <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/>`__ and MCR v4.13 (MATLAB R2010a) MCRInstaller.dmg `file <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/MCR/maci64/>`__ are not compatible with mia (while `./run_spm12.sh /Applications/MATLAB/MATLAB_Compiler_Runtime/v713/ fmri` works fine in a terminal). Using this version of spm standalone, the following message is observed in MIA: `/Volumes/Users/econdami/Documents/spm/spm12Standalone/spm12Stndalone_r7771/run_spm12. sh: line 60: ./spm12.app/Contents/MacOS/spm12_maci64: No such file or directory`.

Installation of others software
-------------------------------

  Please follow the instruction in the documentation of each third-party software.



Installation on Windows
=======================

  Please follow the instruction in the documentation of each third-party software.
