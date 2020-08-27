.. :orphan: is used below to try to remove the following warning: checking consistency... /home/econdami/Git_Projects/populse_mia/docs/source/documentation/developer_documentation.rst: WARNING: document isn't included in any toctree
:orphan:
.. toctree::

+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+
|`Home <../index.html>`_|`Documentation <./documentation.html>`_|`Installation <../installation/installation.html>`_|`GitHub <https://github.com/populse/populse_mia>`_|
+-----------------------+---------------------------------------+---------------------------------------------------+--------------------------------------------------+

How to contribute to the populse_mia package
============================================

Non-Populse member
------------------

* `Fork <https://help.github.com/articles/fork-a-repo/>`_ Populse_mia on GitHub and clone your Populse_mia repository
  
* Get source code from Github using HTTPS or SSH. Replace [populse_install_dir] with a directory of your choice ::

        git lfs clone https://github.com/your_user_name/populse_mia.git [mia_install_dir]/populse_mia # using HTTPS
        git lfs clone git@github.com:your_user_name/populse_mia.git [mia_install_dir]/populse_mia # using SSH

* If you have made some changes to improve the code and want to share them, feel free to open pull requests:

        * Commit and push your changes to your personal repository (`git add ..., git commit -m "a shor message", git push <https://stackoverflow.com/questions/6143285/git-add-vs-push-vs-commit)>`_)

        * Open a `pull request <https://help.github.com/articles/creating-a-pull-request/>`_ on GitHub

Populse member
--------------

* `Make a populse_mia's developer installation <https://populse.github.io/populse_mia/html/installation/developer_installation.html>`_
  
* Make sure to work on your own branch ::

    git checkout -b your_branch_name # creates your own branch locally
    git push -u origin your_branch_name # creates your own branch remotely

* When you've completed your changes, merge your branch with the master branch then push to GitHub (Beware! The master branch must always remain as clean as possible. Make sure your changes bring an improvement without regression) ::

    git checkout master
    git merge your_branch_name
    git push

Populse_mia's developer documentation
=====================================

The `description of populse_mia modules <../populse_mia.html>`_ is updated as often as possible.

Conventions
-----------

We follow as much as possible the `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ for coding conventions and the `PEP 257 <https://www.python.org/dev/peps/pep-0257/>`_ for docstring conventions. We are encouraging people that want to colabore to the populse project to follow these guidelines.

