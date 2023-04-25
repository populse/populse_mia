.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/linux_installation.rst: WARNING: document isn't included in any toctree

:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_mia's developer installation
====================================

For developer, it is possible to install Populse_MIA either directly on host or using virtualisation (by using `BrainVISA <https://brainvisa.info/web/>`_ images which are available for two free and open source virtualisation technologies: `Singularity <https://en.wikipedia.org/wiki/Singularity_(software)>`_ and `VirtualBox <https://en.wikipedia.org/wiki/VirtualBox>`_.).

The `data viewer <../documentation/data_viewer.html>`_ currently available by default in Mia is based on `Anatomist <https://brainvisa.info/web/anatomist.html>`_, which should be compiled.
Therefore, on the host, there are no access to the data viewer.

- `Install a light version of Mia on the host for developer <./host_developer_installation.html>`_ (without data viewer)

  `Pre-requirements <./host_developer_installation.html#pre-requirements>`_
    * `For linux - macOS <./host_pre_req_linux_macos.html>`_
    * `For Windows 10 <./host_pre_req_windows10.html>`_

  `Installation <./host_developer_installation.html#isntallation>`_
    * Installation by cloning the source codes
    * Installation by using mia_install project

- `Use virtualisation to install Mia for developer <./virtualisation_developer_installation.html>`_ (with a data viewer access but with an additional cost for hard disk space)

  `Pre-requirements <./virtualisation_developer_installation.html#pre-requirements>`_

  `Installation <./virtualisation_developer_installation.html#isntallation>`_
