.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/user_installation.rst: WARNING: document isn't included in any toctree

:orphan:

.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Mia's user installation
=======================

Since version 2.0.0, Mia can be installed directly on the host or using virtualisation. On the host, the user will not have access to the `DataViewer <../documentation/data_viewer.html>`_  because the one currently available by default in Mia is based on `Anatomist <https://brainvisa.info/web/anatomist.html>`_, which should be compiled. We therefore propose to use the `BrainVISA <https://brainvisa.info/web/>`_ images which are available for two free and open source virtualisation technologies: `Singularity <https://en.wikipedia.org/wiki/Singularity_(software)>`_ and `VirtualBox <https://en.wikipedia.org/wiki/VirtualBox>`_.

Thus, by installing a container or a virtual machine, the user has access to all the stuffs already made available by the BrainVisa developers, such as Anatomist.

In a nutshell, it is possible `to install a light version of Mia on the host <./host_user_installation.html>`_, without DataViewer, or `to use virtualisation to install Mia <./virtualisation_user_installation.html>`_, with the DataViewer access (with an additional cost for hard disk space).
