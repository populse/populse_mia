Linux
=====
With Linux, Singularity seems to work perfectly well. Given the characteristics of the 2 proposed technologies ([container or virtual machine](https://www.geeksforgeeks.org/difference-between-virtual-machines-and-containers/)) it is clear that it is better to use a container for performance reasons.
In the following we propose exclusively for linux the use of a Singularity container.

**Short**:  
  *Read-only container*:
  - "Two softwares must be installed: Python (version >= 3.7) and Singularity (version > 3.6)"
  - mkdir -p $HOME/casa_distro/brainvisa-opensource-master # create an installation directory
  - "[download the last casa-dev image](https://brainvisa.info/download/) (ex. casa-dev-5.0-1.sif), preferably into the $HOME/casa_distro directory"
  - singularity run -B $HOME/casa_distro/brainvisa-opensource-master:/casa/setup $HOME/casa_distro/casa-dev-5.0-1.sif branch=master distro=opensource # execute the container image using Singularity
  - "set the bin/ directory of the installation directory in the PATH environment variable of the host system, typically add `export PATH="$HOME/casa_distro/brainvisa-opensource-master/bin:$PATH"` in $HOME/.bashrc if unix bash shell
  - "add `cmake_options += -DPYTHON_EXECUTABLE=/usr/bin/python3` in the [ build $CASA_BUILD ] section of the $HOME/casa_distro/brainvisa-opensource-master/conf/bv_maker.cfg file (host) to make python3 as default"
  - bv_maker #  to build from within container terminal or from outside the container
  - bv # to run the configuration GUI
  - bv bash # to open a terminal in the container

  *To create a container within a writable directory*:
  - sudo singularity build --sandbox $HOME/casa_distro/casa-dev-5.0-1_wr $HOME/casa_distro/casa-dev-5.0-1.sif # to make an editable image (casa-dev-5.0-1_wr)
  - sudo singularity run --writable $HOME/casa_distro/casa-dev-5.0-1_wr bash # to modify the image
  - "It is now possible to modify the image. For example let's update all packages and install emacs:"
  - Singularity> apt update  # Singularity> is the prompt
  - Singularity> apt-get install -y software-properties-common
  - Singularity> add-apt-repository ppa:kelleyk/emacs
  - Singularity> apt install emacs26
  - "Edit the $HOME/casa_distro/brainvisa-opensource-master/conf/casa_distro.json file and change the value of the `image` key (ex. "image": "/home/econdami/casa_distro/casa-dev-5.0-1_wr" in place of "image": "/home/econdami/casa_distro/casa-dev-5.0-1.sif")"
  - "Then using `bv` or `bv bash` will use the casa-dev-5.0-1_wr image" 

**[Longer](https://brainvisa.info/web/download.html)**


MacOS (VirtualBox)
====================

While waiting for a working version of Singularity for Mac, here the procedure to use VirtualBox :

A - VirtualBox install

	1 - Go to the VirtualBox site  https://www.virtualbox.org
	2 - click on Download VirtualBox 6.1
	3 - choose OS X hosts
	4 - a dmg file is downloading
	5 - double click on this file,  a virtual disk named ‘VirtualBox’ will appear on the Desktop
	6 - Open this disk, double click on ‘VirtualBox.pkg’ and follow the instructions
 
B – BrainVisa install

	1 - go to https://brainvisa.info/web/download.html#vbox-install (chapiter ‘Install with VirtualBox’)
	2 - download the image file Brainvisa 5.0.2 (8Gb)
	3 - start VirtualBox
	4 - in VirtualBox, import the downloaded image
	5 - enter parameters (CPU, RAM, DVD ...) and complete the 'Machine Base Folder' field
	6 - click on 'Import'
	7 - a 'brainvisa-5.0.2' session appears, start it

if you have pb with Kernel driver not installed (rc=-1908) do the following procedure : ([for illustration see here](https://medium.com/@Aenon/mac-virtualbox-kernel-driver-error-df39e7e10cd8 ))

	1 - reboot your machine
	2 - start VirtualBox
	3 - start 'brainvisa-5.0.2' session (the error window reappears)
	4 - launch System Preferences
	5 - click on Security & Privacy
	6 - click 'Allow'
	7 - relaunch 'brainvisa-5.0.2' session
 
 C - Requirements install

	1 - open a terminal (double click  'LXTerminal' on desktop)
	2 - sudo apt-get update (password: brainvisa)
	
	Python3.7 install:
	3 - sudo apt install software-properties-common</p>
	4 - sudo add-apt-repository ppa:deadsnakes/ppa
	5 - sudo apt install python3.7
	6 - sudo apt-get install python3.7-dev
	7 - sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
	8 - sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2
	9 - sudo update-alternatives --config  python3 (enter 2 for Python3.7)

	Git install:
	10 - sudo apt install git 
	11 - sudo apt install git-lfs
 
	Pip install:
	12 - sudo apt install python3-pip
	13 - pip3 install --upgrade pip
	
D - MIA install
	
	1 - pip3 install --target /home/brainvisa/.local/lib/python3.7/site_packages/ PyQt5
	2 - pip3 install --target /home/brainvisa/.local/lib/python3.7/site_packages/ scikit-image
	3 - pip3 install --target /home/brainvisa/.local/lib/python3.7/site_packages/ nipype
	4 - pip3 install --target /home/brainvisa/.local/lib/python3.7/site_packages/ lark
	6 - pip3 install --target /home/brainvisa/.local/lib/python3.7/site_packages/ cryptography
	7 - mkdir $HOME/Mia && cd Mia (create and go to the installation directory)
	8 - git clone https://github.com/populse/populse_mia.git
	9 - git clone https://github.com/populse/mia_processes.git
	10 - cd populse_mia
	11 - sudo python3 setup.py install
	12 - cd ..
	13 - git clone https://github.com/populse/soma-base.git
	14 - git clone https://github.com/populse/soma-workflow.git
	15 - git clone https://github.com/populse/capsul.git
	16 - cd soma-base
	17 - sudo python3 setup install

**
there is still a problem to be solved: Anatomist does not work in populse
**



MacOS (SingularityCE Vagrant Box)
===================================

Under MacOS High Sierra (10.13.6), Singularity Vagrant Box seems to work well enough and better than with VirtualBox.

A - Install Vagrant:

	1 - brew tap hashicorp/tap
	2 - brew install vagrant

B - Install Xquartz:

	1 - go to https://www.xquartz.org and download XQuartz-2.8.1.dmg
	2 - Install it
	3 - cd /etc/ssh
	4 - sudo nano ssh_config
	5 - add 'ForwardX11 yes' in Host * section
	6 - reboot machine

C - Install SingularityCE Vagrant Box:

	1 - mkdir vm-singularity && cd vm-singularity
	2 - export VM=sylabs/singularity-ce-3.8-ubuntu-bionic64 && vagrant init $VM && vagrant up && vagrant ssh
	3 - exit (exit vagrant)

D - Install Brainvisa

	1 - cd  vm-singularity
	2 - vagrant up && vagrant ssh (the 'vagrant@vagrant' prompt appears and XQuartz is launched)
	3 - mkdir casa-dev-5.0.4 && cd casa-dev-5.0.4
	4 - wget https://brainvisa.info/download/casa-dev-5.0-4.sif
	5 - singularity run -B .:/casa/setup casa-dev-5.0-4.sif branch=master distro=opensource
	4 - cd conf/
	5 - nano bv_maker.cfg
	6 - add cmake_options += -DPYTHON_EXECUTABLE=/usr/bin/python3 in the [ build $CASA_BUILD ] section
	7 - cd
	8 - nano .bashrc
	9 - add export PATH="$HOME/casa-dev-5.0.4/bin:$PATH" 
	10 - bv_maker (this step is long)

E - Install Populse-mia

	1 - bv bash (the 'opensource-master' prompt appears)
	2 - cd
	3 - mkdir Mia && cd Mia
	4 - git clone https://github.com/populse/populse_mia.git
	5 - git clone https://github.com/populse/mia_processes.git
	6 - git clone https://github.com/populse/soma-base.git
	7 - git clone https://github.com/populse/soma-workflow.git
	8 - git clone https://github.com/populse/populse_db.git


Windows
=======

====== Singularity ======
Created Friday 01 October 2021

Before everything, we need to have WSL (windows Subsystem Linux). With this we can install a linux ubuntu.

==== WSL2 (Windows Subsystem Linux) installation ====

	* Windows 10 must be up to date
	* You need to have enough free space on your system disk : around 20 Gb
	* open a powershell as administrator (right clic on powershell icon) :
		''wsl --install -d Ubuntu-20.04''

	{{./pasted_image.png}}
	
	* Reboot the computer	
	* Normaly a linux ubuntu window is already available, enter it :
		* tape a user / pwd who will be administrator of this linux
		* then you can write your first commands to make ubuntu up to date :
		'''
		sudo apt update
		#at this first sudo command, the system may ask you to enter the password you just enter before.
		sudo apt upgrade -y
		exit
		'''

	* close this window

Usefull : in the Ubuntu wsl Windows terminal, we can access windows files via [[/mnt/c/]]

To know more :  
	* [[https://docs.microsoft.com/en-us/windows/wsl/install-manual|Manual installation steps for older versions of WSL]]
	* [[https://docs.microsoft.com/en-us/windows/wsl/install|Install WSL]]
	* [[https://docs.microsoft.com/en-us/windows/wsl/basic-commands|Basic commands for WSL]]


==== Installation d’un serveur X sous windows avec VcXsrv ====
We also need a X windows serveur to allow linux applications graphic user interface (GUI) works

Get VcXsrv https://sourceforge.net/projects/vcxsrv/files/latest/download
Execute it, click next and install to Install it 
Looking for XLaunch application icon, launch it

and at the end :
	uncheck Native Opengl
	check Disable access control

	do 'Save Configuration' in a file that allow you to launch it later

Allow access asked by WIndows Firewall


==== Singularity Installation ====

On ubuntu, at this time (27-08-2021) there is no package for singularity

Then to allow singularity installation we need go language and some dependances for compilation :
	https://singularity.hpcng.org/admin-docs/3.8/

If you anticipate needing to remove Singularity, it might be easier to install it in a custom directory using the --prefix option to mconfig. In that case Singularity can be uninstalled simply by deleting the parent directory. Or it may be useful to install Singularity using a package manager so that it can be updated and/or uninstalled with ease in the future. 

Open an ubuntu session in windows : 
	click on ubuntu new icon 
	or 
	open a normal windows powershell >
		''ubuntu.20.04.exe''

In Ubuntu window terminal, install the following dependencies:

'''
sudo apt-get update && sudo apt-get install -y \
	build-essential python3-dev \
	uuid-dev \
	libgpgme-dev \
	squashfs-tools \
	libseccomp-dev \
	wget \
	pkg-config \
	git \
	cryptsetup-bin \
	python-is-python3 \
	golang

sudo apt install golang #ubuntu 20.04
'''
  need golang version > 1.13 not available on ubuntu 18,04 (1.10 only)		
		''cd /tmp''
''	wget https://golang.org/dl/go1.17.linux-amd64.tar.gz''
''	tar -xzf go1.17.linux-amd64.tar.gz''
''	chown -R root:root go''
''	sudo mv go /usr/local/''
''	rm go1.17.linux-amd64.tar.gz''
 
'''
echo 'export GOPATH=${HOME}/go' >> ~/.bashrc 
echo 'export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin' >> ~/.bashrc 
source ~/.bashrc
'''


Get singularity :

'''
export VERSION=3.8.0 && # adjust this as necessary \
	wget https://github.com/sylabs/singularity/releases/download/v${VERSION}/singularity-ce-${VERSION}.tar.gz && \
	tar -xzf singularity-ce-${VERSION}.tar.gz && \
	cd singularity-ce-${VERSION}
sudo mkdir /opt/singularity
./mconfig –prefix=/opt/singularity
cd /home/gpi/singularity-ce-3.8.0/builddir
make
sudo make install
'''

Test it with : 
	''/opt/singularity/bin/singularity version''


==== singularity BrainVisa image installation ====

pour cela il faut avoir l’image .sif en ecriture et brainvisa compatible python 3, QT5, Récupérer l’image développeur de brainvisa
 
voir doc : https://github.com/populse/populse_mia/blob/master/developer_doc/UsingVirtualisation.md

==== Installation du conteneur singularity brainvisa_dev==casa-distro_dev : ====
this allow to have a anatomist viewer in populse_mia

mkdir brainvisa_dev_5.0.4
cd brainvisa_dev_5.0.4
wget https://brainvisa.info/download/casa-dev-5.0-4.sif
mkdir brainvisa_ro
echo	'export PATH=${PATH}:/opt/singularity/bin/:${HOME}/brainvisa_dev_5.0.4/brainvisa_ro/bin' >> ~/.bashrc &&\
source ~/.bashrc
singularity run -B $HOME/brainvisa_dev_5.0.4/brainvisa_ro:/casa/setup $HOME/brainvisa_dev_5.0.4/casa-dev-5.0-4.sif

echo "export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0" >> ~/.bashrc &&\
source ~/.bashrc

nano brainvisa_ro/conf/bv_maker.cfg
  cmake_options += -DPYTHON_EXECUTABLE=/usr/bin/python3
  cmake_options += -DDESIRED_QT_VERSION=5

sudo apt install python3-distutils -y 

sudo ln -s python3 /usr/bin/python

bv_maker


sudo apt-get install python3-dev 

# require for mri_conv
sudo apt install openjdk-14-jre-headless
# to use a python3 virtual environment
sudo apt install python3-venv git git-lfs

mkdir ~/DEV
mkdir ~/DEV/populse_dev
cd ~/DEV/populse_dev
git-lfs clone https://github.com/populse/populse_mia.git #git-lfs allow icons and other ressources to be download
git clone https://github.com/populse/mia_processes
git clone https://github.com/populse/mri_conv

bv python populse_mia/python/populse_mia/main.py



