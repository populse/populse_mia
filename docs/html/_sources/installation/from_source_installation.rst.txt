.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/from_source_installation.rst: WARNING: document isn't included in any toctree

:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_MIA's from source installation
======================================

Without waiting for the latest version available on
`PyPI <https://pypi.org/project/populse-mia/>`_, it is possible to install
the latest development version of ``populse_mia`` directly from the source
code. This procedure is mainly intended for users. In developer mode, the
local clone can simply be updated using the ``git pull`` command.

To install ``populse_mia`` from source in user mode, clone the repository,
install it, and then remove the clone if it is no longer needed: ::

    cd /tmp
    git clone https://github.com/populse/populse_mia.git
    cd populse_mia
    python3 -m pip install --user --force-reinstall .
    cd ..
    rm -rf populse_mia

The same procedure can be used for the other Python packages in the Populse
project, including
`capsul <https://github.com/populse/capsul>`_,
`mia_processes <https://github.com/populse/mia_processes>`_,
`populse_db <https://github.com/populse/populse_db>`_,
`soma-workflow <https://github.com/populse/soma-workflow>`_, and
`soma-base <https://github.com/populse/soma-base>`_.
