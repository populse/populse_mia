.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/installation/from_source_installation.rst: WARNING: document isn't included in any toctree

:orphan:

  .. toctree::

+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <../documentation/documentation.html>`_|`Installation <./installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+------------------------------------------------------+-------------------------------------+--------------------------------------------------+


Populse_MIA installation from source
====================================

Without waiting for the latest version available on
`PyPI <https://pypi.org/project/populse-mia/>`_, it is possible to install
the latest development version of ``populse_mia`` directly from the source
code. This procedure is mainly intended for users. In developer mode, the
local clone can simply be updated using the ``git pull`` command.

First, clone the repository:

.. code-block:: bash

    cd /tmp
    git clone https://github.com/populse/populse_mia.git
    cd populse_mia

Then install the package according to your Python environment:

* **System Python** (outside a virtual environment):

  .. code-block:: bash

      python3 -m pip install --user --force-reinstall .

* **Virtual environment**:

  Install the package without the ``--user`` option:

  .. code-block:: bash

      python3 -m pip install --force-reinstall .

If the cloned repository is no longer needed, it can be removed:

.. code-block:: bash

    cd ..
    rm -rf populse_mia

The same procedure can be used for the other Python packages in the Populse
project, including
`capsul <https://github.com/populse/capsul>`_,
`mia_processes <https://github.com/populse/mia_processes>`_,
`populse_db <https://github.com/populse/populse_db>`_,
`soma-workflow <https://github.com/populse/soma-workflow>`_, and
`soma-base <https://github.com/populse/soma-base>`_.

.. note::

   The ``--user`` option installs the package into the user's
   ``site-packages`` directory and should only be used when installing with
   the system Python. It must **not** be used from within a virtual
   environment, where packages are installed directly into the virtual
   environment.
