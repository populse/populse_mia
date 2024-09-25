

MacOS (SingularityCE Vagrant Box)
===================================

Under MacOS High Sierra (10.13.6), Singularity Vagrant Box seems to work well enough, better than VirtualBox alone.

A - Install a Vagrant provider like VirtualBox (if not already installed):

	1 - Download VirtualBox OSX dmg file [here](https://www.virtualbox.org/wiki/Downloads)
	2 - Open it and Install it
	3 - Maybe you'll need to allow this Oracle application in Preferences Panel then Security icon

B - Install Homebrew (if not already installed):

	1 - In a Terminal (in Applications/Utilities) enter:
	2 - ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

C - Install Vagrant:

	1 - brew tap hashicorp/tap
	2 - brew install vagrant

D - Install Xquartz:

	1 - go to https://www.xquartz.org and download XQuartz-2.8.1.dmg
	2 - Install it
	3 - sudo nano /etc/ssh/ssh_config
	4 - Add 'ForwardX11 yes' in Host * section
	5 - Exit Terminal
	6 - Reboot the system to take effect.

E - Install SingularityCE Vagrant Box:

	1 - mkdir vm-singularity && cd vm-singularity
	2 - export VM=sylabs/singularity-ce-3.8-ubuntu-bionic64 && vagrant init $VM
	3 - vagrant up && vagrant ssh
	3 - This launch the Ubuntu Singularity virtual machine,
		the 'vagrant@vagrant' prompt appears and XQuartz is launched

F - Install Brainvisa

	1 - the '>' before command indicate to enter it in vagrant@vagrant> prompt
	2 - >mkdir casa-dev-5.0.4 && cd casa-dev-5.0.4
	3 - >wget https://brainvisa.info/download/casa-dev-5.0-4.sif
	4 - >singularity run -B .:/casa/setup casa-dev-5.0-4.sif branch=master distro=opensource
	5 - >nano conf/bv_maker.cfg
	6 - in the [ build $CASA_BUILD ] section add:
		cmake_options += -DPYTHON_EXECUTABLE=/usr/bin/python3
	7 - >echo 'export PATH=${PATH}:${HOME}/casa-dev-5.0.4/bin' >> ~/.bashrc
	8 - >source ~/.bashrc
	9 - >bv_maker #(this step takes a long time 30mn to 2h)

G - Install Populse-mia

	1 - >bv bash
	2 - the 'opensource-master' prompt appears represented here by >>
	3 - >>cd
	4 - >>mkdir Mia && cd Mia
	5 - >>git clone https://github.com/populse/populse_mia.git
	6 - >>git clone https://github.com/populse/mia_processes.git
	7 - >>git clone https://github.com/populse/mri_conv
	8 - >>python populse_mia/populse_mia/main.py

Windows
=======
Here you find documentation to install Populse_MIA in Windows 10.
We use virtualization with Singularity.

Before everything, we need to have WSL (Windows Subsystem Linux). With this we can install a linux Ubuntu 22.04, 20.04 or 18.04.
To install linux Ubuntu 22.04 you can either make an upgrade of the linux Ubuntu 20.04.
We recommend an update of  linux Ubuntu 20.04 once it's installed.


### 1 - WSL2 (Windows Subsystem Linux) installation

   - In an administrator type Windows account:
      - Windows 10 must be up to date
      - You need to have enough free space on your system disk : around 20 Gb
      - Open a **PowerShell as administrator** (right clic on powershell icon):
      - enter `wsl --install -d Ubuntu-20.04`
      - <img src="images/screenshots/Windows 10 - PowerShell - WSL2.png" width=80%>

   - Reboot the computer
   - Normally a linux ubuntu window is already available, enter it:
      - enter a user / password who will be administrator of this linux (asked by the system)
      - <img src="images/screenshots/Windows 10 - Ubuntu.png" width=80%>
      - then you can write your first commands to make ubuntu up to date:
```bash
      sudo apt update
      #at this first sudo command, the system may ask you to enter the password you just enter before.
      sudo apt upgrade -y
      exit
```
   - close this window

Now you have WSL2 and an Ubuntu 20.04 linux.
Before you install a new distribution using `wsl --install -d distribution`, make sure that WSL is in 2 mode with:
   `wsl --set-default-version 2`
The distribution is only available for the current Windows user.
Useful : in the Ubuntu WSL Windows terminal, we can access Windows files via `/mnt/c/`

To know more:
   - [Manual installation steps for older versions of WSL](https://docs.microsoft.com/en-us/windows/wsl/install-manual)
   - [Install WSL](https://docs.microsoft.com/en-us/windows/wsl/install)
   - [Basic commands for WSL](https://docs.microsoft.com/en-us/windows/wsl/basic-commands)


### 2- Upgrade Ubuntu 20.04 to 22.04 (Only for devellopers )

If you are a developer, you will need Ubuntu 22.04 to work on the whole project populse.
If not , you can ignore this part 2.
You have precedently update the linux system. You can directly upgrade your linux Ubuntu distriution to 22.04 with the following commands:

* To get if any new rekease is available type:

`sudo apt dist-upgrade`

* Install the update manager:

Although the update manager core will already be there, however, to confirm just run the given command.

`sudo apt install update-manager-core`

* Edit release-upgrades configuration file using the below-given command.

`sudo nano /etc/update-manager/release-upgrades`

* After that change the Prompt value from Normal to LTS. However, by default it will be set to LTS.

`Prompt = lts`

Save the file by pressing Ctrl+O and then exit the same with Ctrl+X.

* Here startes the concrete upgrade by the command:

`sudo do-release-upgrade -d`

After running the above command, the system will update and replace the system repository and after that, once the system is ready to get upgraded, you will ask finally whether you want to upgrade or not. If you have changed your mind then type ‘n‘ and the system will roll back all the made changes.

Once the installation of the new Jammy Jelly Fish is completed, remove the obsolete packages to clear some space by pressing Y and hitting the Enter key.

The WSL Ubuntu App will ask you to restart the system. However, it has not been started as an init system, so that will not be possible. Therefore, simply close the WSL app window and open it again.

* You can check the Ubuntu version installed via the command:

`cat /otc/os-release`

### 3- X server installation in windows with VcXsrv

We also need a X windows server to allow linux applications graphic user interface (GUI) works.

- Get [VcXsrv](https://sourceforge.net/projects/vcxsrv/files/latest/download)
  - Execute it,
  - click 'next' then 'install' to install it

- Looking for XLaunch application icon, launch it

- Configure it like the screenshots below:
   - <img src="images/screenshots/Xlaunch_1.png" width=50%>
   - <img src="images/screenshots/Xlaunch_2.png" width=50%>
   - Disable *'Native opengl'*
   - Enable *'Disable access control'*
   - <img src="images/screenshots/Xlaunch_3.png" width=50%>
   - Do *'Save Configuration'* in a file that allow you to launch it later (ie on the Desktop)
   - <img src="images/screenshots/Xlaunch_4.png" width=80%>

- Allow access asked by Windows firewall

 P.S: You have to make sure VcXsrv is running every time you to run a GUI via your Ubuntu linux distribution.

### 4 - Dependencies Installation

- Open an Ubuntu session in Windows by:
   - click on Ubuntu new icon
  or
   - open a normal Windows PowerShell,
  enter `ubuntu.22.04.exe`

- In this Ubuntu window terminal, install the following dependencies:

```bash
   sudo apt install -y build-essential uuid-dev libgpgme-dev squashfs-tools libseccomp-dev wget pkg-config git git-lfs cryptsetup-bin python3-distutils python3-dev
   # Ubuntu 22.04 & 20.04
   sudo apt install python-is-python3
   # Ubuntu 18.04
   sudo ln -s python3 /usr/bin/python
```


### 6 - Populse_MIA with BrainVisa Singularity image installation

In the aim to install Populse_MIA with anatomist viewer, we need the Brainvisa dev singularity image compatible with python 3, QT5

- #### 5 - 1 - Brainvisa Installation


To install properly BrainVisa you have to refer to [prerequisites guidelines](https://brainvisa.info/web/download.html#prerequisites) for Singularity on linux.

Prerequisite are the software that need to be installed on your computer in order to be able to install and use BrainVISA. As we use her Ubuntu, we recommend to install Singularity. To do it so follow the steps below.

-Create an installation directory:

``mkdir -p $HOME/casa_distro/brainvisa-opensource-master`` (note that we are using a slightly different directories organization from the user case, because the images here can be reused and shared between several development configurations  but this organization is not mandatory, it will just make things simpler for the management tool casa_distro if it is used later)

 -Download the "casa-dev" image found [here](https://brainvisa.info/download/), preferably into the $HOME/casa_distro directory. Download the latest "casa-dev" image.
It’s a .sif file, for instance casa-dev-5.3-8.sif. Type ``wget https://brainvisa.info/download/casa-dev-5.3-8.sif``

 -Execute the container image using Singularity, with an option to tell it to run its setup procedure. The installation directory should be passed, and it will require additional parameters to specify the development environment characteristics. Namely a distro argument will tell which projects set the build will be based on (valid values are opensource, brainvisa, cea etc.), a branch argument will be master, latest_release etc., and other arguments are optional: ``singularity run -B $HOME/casa_distro/brainvisa-opensource-master:/casa/setup $HOME/casa_distro/casa-dev-5.3-8.sif branch=master distro=opensource``.

 -Set the bin/ directory of the installation directory in the PATH environment variable of your host system config, typically in $HOME/.bashrc or $HOME/.bash_profile if you are using a Unix Bash shell:
  ```
  nano ~/.bashrc
  export PATH="$HOME/casa_distro/brainvisa-opensource-master/bin:$PATH"
  source ~/.bashrc

  # we get the ip address to allow X server access and this ip can change when Windows reboot.

  nano ~/.bashrc
  export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2 ":0.0"}')
  source ~/.bashrc

  nano casa_distro/brainvisa-opensource-master/conf/bv_maker.cfg
  [ build $CASA_BUILD ]
     cmake_options += -DPYTHON_EXECUTABLE=/usr/bin/python3
     cmake_options += -DDESIRED_QT_VERSION=5

  bv_maker
  # it takes time to compile.
  ```

Now you can test if the brainvisa configuration GUI works well via the command: ``bv``.


- #### 5 - 2 - Populse_MIA Installation

For the purpose of the container is to make profit of its resources,
you will install populse_mia, mri_conv and mia_processes in the container repertory.


```bash
### enter in the container ###

bv bash

### require for mri_conv ###
sudo apt install -y openjdk-17-jre-headless

mkdir ~/DEV &&\
mkdir ~/DEV/populse_dev &&\
cd ~/DEV/populse_dev
git clone https://github.com/populse/populse_mia.git #git allow icons and other resources to be download
git clone https://github.com/populse/mia_processes
git clone https://github.com/populse/mri_conv
```

To launch mia using an alias, insert the  following commands in the bash of your container.

# mia launch
alias mia='pwd_orig=$PWD; cd /casa/home/DEV/populse_dev/populse_mia/populse_mia; python3 main.py; cd $pwd_orig'

You can now launch mia with the command:
```mia```
