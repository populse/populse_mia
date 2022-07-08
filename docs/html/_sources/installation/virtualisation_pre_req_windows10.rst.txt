.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/user_installation.rst: WARNING: document isn't included in any toctree

:orphan:

.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Pre-requirements of windows installations are the same for `windows host installation in user mode <https://populse.github.io/populse_mia/html/installation/host_pre_req_windows10.html>`_.
But you can avoid numpy and PyQt5 install commands since they will be managed while installing the mia project under ubuntu.

Once pre-requirements are acquired, you will need to install Wsl2 to host a virtual machine of ubuntu to install mia.

1- WSL2 (Windows Subsystem Linux) installation
-------------------------------------------

* In an administrator type Windows account:
      - Windows 10 must be up to date
      - You need to have enough free space on your system disk : around 20 Gb
      - Open a **PowerShell as administrator** (right clic on powershell icon
enter: ::

  wsl --install -d Ubuntu-20.04

|


    .. image:: ../../../developer_doc/images/screenshots/Windows%2010%20-%20PowerShell%20-%20WSL2.png
       :align: center
       :name: Windows 10

|

* Reboot the computer

* Normally a linux ubuntu window is already available, enter it:

- enter a user / password who will be administrator of this linux (asked by the system)


    .. image:: ../../../developer_doc/images/screenshots/Windows%2010%20-%20Ubuntu.png
       :align: center
       :name: Windows 10

|

then you can write your first commands to make ubuntu up to date: ::

   sudo apt update

   #at this first sudo command, the system may ask you to enter the password you just enter before.

   sudo apt upgrade -y

   exit
|

- close this window


Now you have WSL2 and an Ubuntu 20.04 linux.

Before you install a new distribution using ``wsl --install -d distribution``,
make sure that WSL is in 2 mode with: ``wsl --set-default-version 2`` .
The distribution is only available for the current Windows user.  
Usefull : in the Ubuntu WSL Windows terminal, we can access Windows files via ``/mnt/c/``  

To know more:  
   - [Manual installation steps for older versions of WSL](https://docs.microsoft.com/en-us/windows/wsl/install-manual)
   - [Install WSL](https://docs.microsoft.com/en-us/windows/wsl/install)
   - [Basic commands for WSL](https://docs.microsoft.com/en-us/windows/wsl/basic-commands)


2- X server installation in windows with VcXsrv
-----------------------------------------------
|

We also need a X windows server to allow linux applications graphic user interface (GUI) works.  

Get [VcXsrv](https://sourceforge.net/projects/vcxsrv/files/latest/download)
  - Execute it, 
  - click 'next' then 'install' to install it 

Looking for XLaunch application icon, launch it.

Configure it like the screenshots below:
  
   .. image:: ../../../developer_doc/images/screenshots/Xlaunch_1.png
      :align: center
      :name: Xlaunch_1

|

   .. image:: ../../../developer_doc/images/screenshots/Xlaunch_2.png
      :align: center
      :name: Xlaunch_2

|

Disable *'Native opengl'*
Enable *'Disable access control'*
     
   .. image:: ../../../developer_doc/images/screenshots/Xlaunch_3.png
      :align: center
      :name: Xlaunch_3

|

Do *'Save Configuration'* in a file that allow you to launch it later (ie on the Desktop)


   .. image:: ../../../developer_doc/images/screenshots/Xlaunch_4.png
      :align: center
      :name: Xlaunch_4

|

Allow access asked by Windows firewall.
 
P.S: You have to make sure VcXsrv is running every time you to run a GUI via your Ubuntu linux distribution.
  
3 - Dependencies Installation
-----------------------------
|

Open an Ubuntu session in Windows by:

- click on Ubuntu new icon

  or

- open a normal Windows PowerShell,enter ``ubuntu.20.04.exe``


In this Ubuntu window terminal, install the following dependencies: ::

   sudo apt install -y build-essential uuid-dev libgpgme-dev squashfs-tools libseccomp-dev wget pkg-config git git-lfs cryptsetup-bin python3-distutils python3-dev
   # Ubuntu 20.04
   sudo apt install python-is-python3
   # Ubuntu 18.04
   sudo ln -s python3 /usr/bin/python

|

You have completely installed a virtual Ubuntu which is now able to host mia.
You can now follow steps from **installation** via `populse mia installation in user mode <https://populse.github.io/populse_mia/html/installation/virtualisation_user_installation.html>`_.












