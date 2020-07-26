.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/from_source_installation.rst: WARNING: document isn't included in any toctree
:orphan:  
.. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_MIA's from source installation
======================================

* Without waiting for the latest version available on `CheeseShop <https://pypi.org/project/populse-mia/>`_, it is possible to install from source the latest development version of populse_mia. This procedure will be rather reserved to the user mode because in developer mode it is possible to update the clone using the ``git pull`` command. In user mode, a version of populse_mia being already installed we recommend to uninstall first popuse_mia, then download the master branch of populse_mia and finally perform the form source installation ::

    pip3 uninstall populse_mia
    cd /tmp
    git clone https://github.com/populse/populse_mia.git
    cd populse_mia
    python3 setup.py install --user
    cd ..
    rm -rf populse_mia

* It is of course possible to do this for all python packages in the populse project (`capsul <https://github.com/populse/capsul>`_, `mia_processes <https://github.com/populse/mia_processes>`_, `populse_db <https://github.com/populse/populse_db>`_, `soma-workflow <https://github.com/populse//soma-workflow>`_ and `soma-base <https://github.com/populse//soma-base>`_
