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

Pre-commit
----------

* Description

  The populse_mia software calls a set of `git hooks <https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks#_git_hooks>`_ before each piece of code is commited. This feature is accomplished with the `pre-commit <https://pre-commit.com/>`_ package and helps to better format the code, include documentation and much more.

* Installation

  Start by installing the package: ::

    pip3 install pre-commit

  Before commiting for the first time and after every change in the .pre-commit-config.yaml file, launch: ::

    pre-commit install

* Usage

  * If a commit passes the pre-commit feature, it can be then normally pushed to the origin.
  
  * An example of a passing commit: ::

      # INPUT
      git add user_interface/data_viewer/data_viewer.py
      git commit

      # OUTPUT
      check python ast.........................................................Passed
      check json...........................................(no files to check)Skipped
      black....................................................................Passed
      [pre_commit c10882d05] Add features to data_viewer.
        1 file changed, 29 insertions(+), 24 deletions(-)

  * On the other hand, if a commit fails the pre-commit (eg. for containing a file not formatted according to `PEP8 <https://peps.python.org/pep-0008/>`_), failing file will be fixed and recreated as an unstaged file. Those files should be then added and commited again. In the case where the pre-commit feature cannot fix the error by itself, the developer should modify the accordingly and recommit the changes.
  
  * An example of a failing commit: ::

      # INPUT
      git add user_interface/data_viewer/data_viewer.py
      git commit

      # OUTPUT
      check python ast.........................................................Passed
      check json...........................................(no files to check)Skipped
      black....................................................................Failed
      - hook id: black
      - files were modified by this hook
      
      reformatted python/populse_mia/user_interface/data_viewer/data_viewer.py
      
      All done! ✨ 🍰 ✨
      1 file reformatted.
    
      # INPUT
      git status

      # OUTPUT
      On branch pre_commit
      Your branch is up to date with 'origin/pre_commit'.
      
      Changes to be committed:
        (use "git restore --staged <file>..." to unstage)
                    modified:   user_interface/data_viewer/data_viewer.py
      
      Changes not staged for commit:
        (use "git add <file>..." to update what will be committed)
        (use "git restore <file>..." to discard changes in working directory)
              modified:   user_interface/data_viewer/data_viewer.py

      # INPUT
      git add user_interface/data_viewer/data_viewer.py
      git commit
    
      # OUTPUT
      check python ast.........................................................Passed
      check json...........................................(no files to check)Skipped
      black....................................................................Passed
      [pre_commit c10882d05] Add features to data_viewer.
       1 file changed, 29 insertions(+), 24 deletions(-)
