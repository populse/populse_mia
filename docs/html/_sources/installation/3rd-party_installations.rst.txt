.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/linux_installation.rst: WARNING: document isn't included in any toctree

:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_mia's 3rd party installations
=====================================

 * This installations notes are based on Ubuntu 20.04 which use Python3 as default (when you type 'python' in a command line). 
 * '/pathto/softs' is the destination folder where you want to have the softwares installed, ie: /opt, /home/APPS or what you want. 
 * A Python3 virtual environment is used. How to do that ? See below at Populse installation in python3 virtual environment. 
 * Lines with '#' are comments. 

Installation of FSL 6
---------------------

 * Download `fslinstaller.py <https://fsl.fmrib.ox.ac.uk/fsldownloads_registration/>`_ then: ::

     # fsl installer needs python2
     sudo apt install python
     # the destination folder where put FSL, do right access with chown
     mkdir /pathto/softs/FSL
     mkdir /pathto/softs/FSL/6.04
     # launch the installer
     python2 fslinstaller.py

 * In ~/.profile file check if this lines includes (if not, put it): ::

     FSLDIR=/pathto/softs/FSL/6.04
     PATH=${FSLDIR}/bin:${PATH}
     export FSLDIR PATH
     . ${FSLDIR}/etc/fslconf/fsl.sh

   fsl.sh defines other environment variables for FSL like FSLOUTPUTTYPE=NIFTI-GZ

 * log out and log in for changes take effect

 * Test it: ::
 
     fsleyes

|

Installation of MRtrix 3
------------------------

 * From `MRtrix documentation <http://userdocs.mrtrix.org/en/3.0.1/installation/build_from_source.html>`_: ::
	
     sudo apt-get install git g++ python-is-python3 libeigen3-dev zlib1g-dev libqt5opengl5-dev libqt5svg5-dev libgl1-mesa-dev libfftw3-dev libtiff5-dev libpng-dev

     cd ~/Downloads   
     git clone https://github.com/MRtrix3/mrtrix3.git
     cd mrtrix3
     ./configure
     ./build
     cd ..
     mv mrtrix3 /pathto/softs/                 # don't forget to put the / at the end of the path
     cd /pathto/softs/mrtrix3
     ./set_path                   
     # to have new path activated to launch mrtrix commands 
     bash

 * Test if it works: ::

     mrview

 * Notes:

   * dwipreproc has changed name to dwifslpreproc

   * mrresize, mrpad, mrcrop commands has been reunified in unique mrgrid command

|

Installation of SPM 12 Standalone and Matlab Runtime
-----------------------------------------------------

 * `Download <https://www.fil.ion.ucl.ac.uk/spm/download/restricted/bids/>`_ the desired version of standalone SPM 12.
   
   Unzip it. For example: ::
	
	cd ~/Downloads/
	unzip spm12_r7771_Linux_R2019b.zip


 * Download and install the corresponding R20xxa/b Matlab Runtime installation for linux `here <https://uk.mathworks.com/products/compiler/matlab-runtime.html>`_.
   
   Unzip it in a matlabRT/ folder: ::

	cd ~/Downloads
	mkdir matlabRT
	unzip -d matlabRT/ MATLAB_Runtime_R2019b_Update_3_glnxa64.zip
	sudo matlabRT/./install

   * After the installation, you get the following message (ex. for R2019b (9.7) Matlab Runtime):

     "On the target computer, append the following to your LD_LIBRARY_PATH environment variable: 
     /usr/local/MATLAB/MATLAB_Runtime/v97/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/extern/bin/glnxa64
     If MATLAB Runtime is to be used with MATLAB Production Server, you do not need to modify the above environment variable."

   * Then if necessary, create a .conf file in the /etc/ld.so.conf.d/ folder and add those previous paths in the file: ::

        sudo nano /etc/ld.so.conf.d/your_lib.conf
	    # Matlab 2020b Runtine Library
	    /usr/local/MATLAB/MATLAB_Runtime/v97/runtime/glnxa64
	    /usr/local/MATLAB/MATLAB_Runtime/v97/bin/glnxa64
	    /usr/local/MATLAB/MATLAB_Runtime/v97/sys/os/glnxa64
	    /usr/local/MATLAB/MATLAB_Runtime/v97/extern/bin/glnxa64

     * Run ldconfig to update the cache: ::

            sudo ldconfig

 * Execute SPM12, the second path being the path to the Matlab Runtime: ::

       spm12/./run_spm12.sh /usr/local/MATLAB/MATLAB_Runtime/v97

| 

Installation of Cuda 11.1
-------------------------

 * Install NVidia driver 455 metapackage from Ubuntu 'Software Update Manager' icon -> 'Settings & Livepatch ...' button -> 'Additional Drivers' tab.
	
 * From	`NVidia documentation <https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html>`_: ::

     get https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
     sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
     sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
     sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
     sudo apt update
     sudo apt install cuda
     sudo nvidia-modprobe
	
 * To compile samples: ::

     sudo apt install freeglut3-dev
     sudo chown -R userloginname /usr/local/cuda-11.1/samples
     # choose a sample application
     cd /usr/local/cuda-11.1/samples/1_Utilities/deviceQuery
     make
     # try it
     ../../bin/x86_64/linux/release/./deviceQuery
	
|

Installation of Populse in python3 virtual environment
------------------------------------------------------

 * From `documentation populse_mia installation for developper <https://populse.github.io/populse_mia/html/installation/developer_installation.html>`_: :: 

     # require for mri_conv
     sudo apt install openjdk-14-jre-headless
     # to use a python3 virtual environment
     sudo apt install python3-venv
 
     mkdir ~/DEV
     mkdir ~/DEV/populse_dev
     cd ~/DEV/populse_dev
     git clone https://github.com/populse/populse_mia.git
     git clone https://github.com/populse/capsul
     git clone https://github.com/populse/mia_processes
     git clone https://github.com/populse/mri_conv
     git clone https://github.com/populse/populse_db
     git clone https://github.com/populse/soma-base
     git clone https://github.com/populse/soma-workflow

     # create and activate the python3 virtual environment
     python -m venv ~/DEV/py3env
     source ~/DEV/py3env/bin/activate
     # For python modules requirements look at https://github.com/populse/populse_mia/blob/master/python/populse_mia/info.py of populse_mia
     pip install wheel pyyaml traits==5.2.0 lark-parser nibabel scikit-image nipype
     # if you want an enhanced python editor/debugger, ie spyder
     pip install spyder
     # to launch it
     cd ~/DEV/populse_dev/populse_mia/python/populse_mia
     python main.py
     # or
     python ~/DEV/populse_dev/populse_mia/python/populse_mia/main.py

 * quit/exit the python3 virtual environment: ::

     deactivate

|

Installation of PyTorch 
-----------------------

 * Simply: ::

     # activate the python3 virtual environment
     source ~/DEV/py3env/bin/activate
     # install
     pip install torch==1.7.0+cu110 torchvision==0.8.1+cu110 torchaudio==0.7.0 -f https://download.pytorch.org/whl/torch_stable.html

 * Test it in python3: ::

     python

     >>> import torch
     >>> x = torch.rand(5, 3)
     >>> print(x)
     tensor([[0.5212, 0.0116, 0.4537],
             [0.4673, 0.1288, 0.9212],
             [0.7345, 0.5193, 0.5020],
             [0.8128, 0.9229, 0.2496],
             [0.9357, 0.4657, 0.8279]])
     >>> torch.cuda.is_available()
     True

 * quit/exit the python3 virtual environment: ::

     deactivate

|

Installation of TractSeg
------------------------

 * Simply: ::

     source ~/DEV/py3env/bin/activate
     pip install TractSeg
     deactivate

|

Installation of MRIcroGL12 (dcm2nniix, 2d-3d viewer, manual ROI)
----------------------------------------------------------------

 * References: 
	`Original website <https://www.mccauslandcenter.sc.edu/mricrogl/source>`_ &
	`Github website <https://github.com/rordenlab/MRIcroGL12>`_

 * `Download last MRIcroGL <https://www.nitrc.org/frs/?group_id=889&release_id=4371>`_, then in a terminal: ::

    cd ~/Downloads
    unzip MRIcroGL_linux.zip
    sudo mv MRIcroGL /pathto/softs/         # put the / at the end of path
    sudo ln -s /pathto/softs/MRIcroGL/MRIcroGL /usr/local/bin/MRIcroGL
    sudo ln -s /pathto/softs/MRIcroGL/Resources/dcm2niix /usr/local/bin/dcm2niix

 * Test it: ::

    MRIcroGL
    dcm2niix -o /destfolder  /dicomfolder

|

Installation of ITKsnap 3 (auto/semi-automatic ROI)
---------------------------------------------------

 * `Download the itksnap3 software <http://www.itksnap.org/pmwiki/pmwiki.php?n=Downloads.SNAP3>`_ then in a terminal: ::

    cd ~/Downloads
    tar -xzf itksnap-3.8.0-20190612-Linux-x86_64.tar.gz
    cd ..
    sudo mv ~/Downloads/itksnap-3.8.0-20190612-Linux-x86_64  /pathto/softs/itksnap-3.8.0
    nano ~/.profile
	PATH=${PATH}:/pathto/softs/itksnap-3.8.0/bin

 * To solve the libpng12.so.0 requirement: 
    * See `help <https://www.linuxuprising.com/2018/05/fix-libpng12-0-missing-in-ubuntu-1804.html>`_
    * `Download the library package <http://ppa.launchpad.net/linuxuprising/libpng12/ubuntu/pool/main/libp/libpng/libpng12-0_1.2.54-1ubuntu1.1+1~ppa0~focal_amd64.deb>`_ installer for Focal Ubuntu 20.04, then : ::

        cd ~/Downloads
        sudo dpkg -i libpng12-0_1.2.54-1ubuntu1.1+1~ppa0~focal_amd64.deb
 
 * Finaly: ::
 
    sudo apt install libcanberra-gtk-module
    # launch it
    itksnap

