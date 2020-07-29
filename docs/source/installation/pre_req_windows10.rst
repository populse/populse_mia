.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/pre_req_windows10.rst: WARNING: document isn't included in any toctree
:orphan:
.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_mia's linux - Windows 10 installation, pre-requirements
===============================================================

* First, assure that you activated the developer mode in the parameters:

.. warning::

  This operation needs administrator rights

  * Click on Start --> Parameters
  * Go in Update and Security

  .. image:: /images/update_and_security.png
     :width: 400
     :align: center

  |

  * Click on Developer environment in the left column and activate the Sideload app

  .. image:: ../images/developer_mode.png
     :width: 400
     :align: center

  |

  * You might need to restart your computer

|

* When you restarted your computer, open a PowerShell window on your computer:

  * Click on the Start menu and type ``PowerShell``

  .. image:: ../images/open_powershell.jpg
     :width: 300
     :align: center

  * Run the PowerShell application

|

* Make sure you have Python installed. You can verify it by typing in PowerShell: ::

    python3 -V

  *Note : depending on your versions, you might need to use `python -V` instead on `python3 -V` to check your version of Python.*

  * If Python is not installed:

    * In PowerShell, type: ::

        python3

    * The Microsoft Store will open on the Python 3.8 app, click on Install:

    .. image:: ../images/Python3.8.png
       :width: 500
       :align: center

    |

    * Check in the shell PowerShell that Python and pip (pip is normally include in the install of Python) are installed: ::

        python3 -V
        pip3 --version

|

* Make sure you have Git installed. You can verify it by typing in PowerShell: ::

    git --version

  * If Git is not installed, you need to install it (`Here <https://git-scm.com/download/win>`_):

    * Download the executable for your specific distribution (64 or 32 bits).
    * Run it.
    * You will be asked many questions depending on you preferences, but the default parameters are enough.
    * At the end of the git installation, you will need to restart PowerShell to restart the environment and be able to use Git.

|

* During the install, you will need C++ Build tools. You can get it by installing Visual Studio Build Tools 2019 and select C++ Build tools (`Here <https://www.microsoft.com/fr-fr/download/details.aspx?id=58317>`_):

  * Download the executable file and run it.

  * The installation is in two parts, at the end of the first part a window with every module in charge by Visual Studio will open:

  .. image:: ../images/vs_Build.png
     :width: 500
     :align: center

  * Select the C++ Build Tools and install it.

|

* Make sure you have java 64-bits installed. You can verify it by typing in PowerShell: ::

    java -version

  * If java 64-bits is not installed, you need to install it (`Here <https://java.com/fr/download/manual.jsp>`_):

    * Download the offline (64 bits) file and run it
    * Follow the installation

|

* Now you need to configure your java in order to be used by your system and PowerShell:

.. warning::

  This operation needs administrator rights

    * In PowerShell, open a system properties window by typing: ::

        sysdm.cpl

    * Click on the Advanced System Parameter

    .. image:: ../images/ASP_system_tab.png
       :width: 500
       :align: center

|

    * Click on Environment Variable

    * Select Path in the system variables, and click on modify

    .. image:: ../images/env_var.png
       :width: 500
       :align: center

|

    * Click on New

    .. image:: ../images/modify_environment_viriable.png
       :width: 500
       :align: center

|

    * Paste the path to the folder containing YOUR java executable, it should LOOK like this: ::

        C:\Program Files\Java\jre1.8.0_251\bin

* Enable the NTFS long path:

.. warning::

  This operation needs administrator rights

    * In PowerShell type: ::

        gpedit.msc

    * A Local Group Policy Editor window will open, then Navigate to:

      --> Local Compute Policy
      --> Computer Configuration
      --> Administrator Templates
      --> System
      --> FileSystem
      --> NTFS

    * Double click on Enable NTFS long path and enable it.

    .. image:: ../images/NTFS.png
       :width: 500
       :align: center

* Populse_mia requires some specific package for Python and particularly numpy and PyQt5, you need to install them before launching the populse_mia installation: ::

    pip3 install numpy --user # be sure to don't forget the "--user" at the end of the command, otherwise you might get issues from administrator rights
    pip3 install PyQt5 --user # be sure to don't forget the "--user" at the end of the command, otherwise you might get issues from administrator rights
