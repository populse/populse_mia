# -*- coding: utf-8 -*-
"""Module that contains class and methods to process the different libraries of
the project.

:Contains:
    :Class:
        - DictionaryTreeModel
        - InstallProcesses
        - Node
        - PackageLibrary
        - PackageLibraryDialog
        - ProcessHelp
        - ProcessLibrary
        - ProcessLibraryWidget

    :Functions:
        - import_file
        - node_structure_from_dict


"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

# Other import
import distutils.dir_util
import glob
import inspect
import os
import pkgutil
import shutil
import sys
import tempfile
import traceback
from copy import copy, deepcopy
from datetime import datetime
from functools import partial
from zipfile import ZipFile, is_zipfile

import yaml

# capsul import
from capsul.api import get_process_instance

# PyQt5 import
from PyQt5 import QtCore

# QAbstractItemView is not available from soma (see in PackageLibraryDialog)
from PyQt5.QtWidgets import QAbstractItemView

# PyQt / PySide import, via soma
from soma.qt_gui import qt_backend
from soma.qt_gui.qt_backend import QtGui
from soma.qt_gui.qt_backend.Qt import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from soma.qt_gui.qt_backend.QtCore import (
    QAbstractItemModel,
    QByteArray,
    QMimeData,
    QModelIndex,
    Qt,
    Signal,
)
from soma.qt_gui.qt_backend.QtWidgets import QGroupBox, QListWidget, QMenu

# Populse_MIA import
from populse_mia.software_properties import Config


class DictionaryTreeModel(QAbstractItemModel):
    """Data model providing a tree of an arbitrary dictionary.

    .. Methods:
        - columnCount: return always 1
        - data: return the data requested by the view
        - flags: everything is enabled and selectable, only the leaves can be
        dragged.
        - getNode: return a Node() from given index
        - headerData: return the name of the requested column
        - index: return an index from given row, column and parent
        - insertRows: insert rows from starting position and number given by
        rows
        - mimeData: used when the widget is dragged by the user
        - mimeTypes: return a constant
        - parent: return the parent from given index
        - removeRows: remove the rows from position to position+rows
        - rowCount: the number of rows is the number of children
        - setData: method called when the user changes data
        - to_dict: return the root node as a dictionary

    """

    def __init__(self, root, parent=None):
        """Initialization of the DictionaryTreeModel class."""

        super(DictionaryTreeModel, self).__init__(parent)
        self._rootNode = root

    def columnCount(self, parent):
        """Number of columns is always 1."""

        return 1

    def data(self, index, role):
        """Return the data requested by the view."""

        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return node.name

    def flags(self, index):
        """Everything is enabled and selectable. Only the leaves can be
        dragged.

        """

        node = index.internalPointer()
        if node.childCount() > 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return (
                Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
            )

    def getNode(self, index):
        """Return a Node() from given index."""

        if index.isValid():
            node = index.internalPointer()
            if node:
                return node

        return self._rootNode

    def headerData(self, section, orientation, role):
        """Return the name of the requested column."""

        if role == Qt.DisplayRole:
            if section == 0:
                return "Packages"
            if section == 1:
                return "Value"

    def index(self, row, column, parent):
        """Return an index from given row, column and parent."""

        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def insertRows(self, position, rows, parent=QModelIndex()):
        """Insert rows from starting position and number given by rows."""

        parentNode = self.getNode(parent)
        self.beginInsertRows(parent, position, position + rows - 1)

        for row in range(rows):
            childCount = parentNode.childCount()
            childNode = Node("untitled" + str(childCount))
            success = parentNode.insertChild(position, childNode)

        self.endInsertRows()
        return success

    def mimeData(self, idxs):
        """Used when the widget is dragged by the user.

        :param idxs: mouse event
        :return: QMimeData object

        """

        mimedata = QMimeData()
        for idx in idxs:
            if idx.isValid():
                node = idx.internalPointer()
                txt = node.data(idx.column())
                mimedata.setData("component/name", QByteArray(txt.encode()))
        return mimedata

    def mimeTypes(self):
        """Return a constant."""

        return ["component/name"]

    def parent(self, index):
        """Return the parent from given index.

        :param index: index

        """

        node = self.getNode(index)
        parentNode = node.parent()
        if parentNode == self._rootNode:
            return QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    def removeRows(self, position, rows, parent=QModelIndex()):
        """Remove the rows from position to position+rows.

        :param position: the position of the node
        :param rows: the row of the tnode
        :param parent: the parent node

        """

        parentNode = self.getNode(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)

        for row in range(rows):
            success = parentNode.removeChild(position)

        self.endRemoveRows()
        return success

    def rowCount(self, parent):
        """The number of rows is the number of children.

        :param parent: the parent of the node

        """

        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        return parentNode.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        """This method gets called when the user changes data.

        :param index: index
        :param value: value
        :param role: Qt role
        :return: boolean

        """

        if index.isValid():
            if role == Qt.EditRole:
                node = index.internalPointer()
                node.setData(index.column(), value)
                return True
        return False

    def to_dict(self):
        """Return the root node as a dictionary.

        :return: dictionary

        """

        return self._rootNode.to_dict()


class InstallProcesses(QDialog):
    """A widget that allows to browse a Python package or a zip file to install
    the processes that it is containing.

    :param main_window: current main window
    :param folder: boolean, True if folder, False if zip

    .. Methods:
        - get_filename: opens a file dialog to get the folder or zip file to
        install
        - install: installs the selected file/folder on Populse_MIA
            **Contains: Private function:**
                - _add_package: Add a package and its modules to
                  the package tree
                - _change_pattern_in_folder: Changing all 'old_pattern' pattern
                  to 'new_pattern' in the 'path' folder

    """

    process_installed = Signal()

    def __init__(self, main_window, folder):
        """Initialize the InstallProcesses class.

        :param main_window: current main window
        :param folder: boolean, True if folder, False if zip

        """

        super(InstallProcesses, self).__init__(parent=main_window)
        self.main_window = main_window
        self.setWindowTitle("Install processes")

        v_layout = QVBoxLayout()
        self.setLayout(v_layout)

        if folder is False:
            label_text = "Choose zip file containing Python packages"

        elif folder is True:
            label_text = "Choose folder containing Python packages"

        v_layout.addWidget(QLabel(label_text))

        edit_layout = QHBoxLayout()
        v_layout.addLayout(edit_layout)

        self.path_edit = QLineEdit()
        edit_layout.addWidget(self.path_edit)
        self.browser_button = QPushButton("Browse")
        edit_layout.addWidget(self.browser_button)

        bottom_layout = QHBoxLayout()
        v_layout.addLayout(bottom_layout)

        install_button = QPushButton("Install package")
        bottom_layout.addWidget(install_button)

        quit_button = QPushButton("Quit")
        bottom_layout.addWidget(quit_button)

        install_button.clicked.connect(self.install)
        quit_button.clicked.connect(self.close)
        self.browser_button.clicked.connect(
            lambda: self.get_filename(folder=folder)
        )

    def get_filename(self, folder):
        """Open a file dialog to get the folder or zip file to install.

        :param folder: True if the dialog installs from folder, False if
                       from zip file

        """

        if folder is True:
            filename = QFileDialog.getExistingDirectory(
                self,
                caption="Select a directory",
                directory=os.path.expanduser("~"),
                options=QFileDialog.ShowDirsOnly,
            )

        elif folder is False:
            filename = QFileDialog.getOpenFileName(
                caption="Select a zip file",
                directory=os.path.expanduser("~"),
                filter="Compatible files (*.zip)",
            )

        if filename and isinstance(filename, str):
            self.path_edit.setText(filename)

        elif filename and isinstance(filename, tuple):
            self.path_edit.setText(filename[0])

    def install(self):
        """Install a package from a zip file or a folder.

        **Contains: Private function:**
            - _add_package: Add a package and its modules to the package tree
            - _change_pattern_in_folder: Changing all 'old_pattern' pattern to
              'new_pattern' in the 'path' folder

        """
        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        def _add_package(proc_dic, module_name):
            """Add a package and its modules to the package tree.

            :param proc_dic: the process tree-dictionary
            :param module_name: name of the module
            :return: proc_dic: the modified process tree-dictionary

            """

            if module_name:
                # Reloading the package
                if module_name in sys.modules.keys():
                    del sys.modules[module_name]

                try:
                    __import__(module_name)

                except ImportError as er:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText(
                        (
                            "During the installation of {0}, "
                            "the following exception was raised:"
                            "\n{1}: {2}.\nThis exception maybe "
                            "prevented the installation ..."
                        ).format(module_name, er.__class__, er)
                    )
                    msg.setWindowTitle("Warning")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()
                    self.result_add_package = False
                    raise ImportError(
                        "The {0} brick may not been installed".format(
                            module_name
                        )
                    )

                pkg = sys.modules[module_name]

                # Checking if there are subpackages
                for importer, modname, ispkg in pkgutil.iter_modules(
                    pkg.__path__
                ):
                    if ispkg:
                        _add_package(
                            proc_dic, str(module_name + "." + modname)
                        )

                for k, v in sorted(list(pkg.__dict__.items())):
                    # Checking each class of in the package
                    if inspect.isclass(v):
                        try:
                            print(
                                "\nInstalling %s.%s ..."
                                % (module_name, v.__name__)
                            )
                            get_process_instance(
                                "%s.%s" % (module_name, v.__name__)
                            )
                            # Updating the tree's dictionnary
                            path_list = module_name.split(".")
                            path_list.append(k)
                            pkg_iter = proc_dic

                            for element in path_list:
                                if element in pkg_iter.keys():
                                    pkg_iter = pkg_iter[element]

                                else:
                                    if element is path_list[-1]:
                                        pkg_iter[element] = "process_enabled"

                                    else:
                                        pkg_iter[element] = {}
                                        pkg_iter = pkg_iter[element]

                        except Exception as e:
                            print(
                                '\nError during installation of the "{0}" '
                                "module ...!\nTraceback:".format(module_name)
                            )
                            print(
                                "".join(traceback.format_tb(e.__traceback__)),
                                end="",
                            )
                            print("{0}: {1}\n".format(e.__class__.__name__, e))
                            self.result_add_package = False

                return proc_dic

        def _change_pattern_in_folder(path, old_pattern, new_pattern):
            """Changing all "old_pattern" pattern to "new_pattern" in the
            'path' folder.

            :param path: path of the extracted or copied processes
            :param old_pattern: old pattern
            :param new_pattern: new pattern

            """

            for dname, dirs, files in os.walk(path):
                for fname in files:
                    # Modifying only .py files (pipelines are saved with
                    # this extension)

                    if fname[-2:] == "py":
                        fpath = os.path.join(dname, fname)

                        with open(fpath) as f:
                            s = f.read()

                        s = s.replace(old_pattern + ".", new_pattern + ".")

                        with open(fpath, "w") as f:
                            f.write(s)

        try:
            self.main_window.statusBar().showMessage(
                "Package installation, please wait ..."
            )
            QApplication.processEvents()

        except AttributeError:
            self.main_window.status_label.setText(
                "Package installation, please wait ..."
            )

        self.result_add_package = True
        filename = self.path_edit.text()
        config = Config()

        if not os.path.isdir(filename):
            if not os.path.isfile(filename):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("The specified file cannot be found")
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                return

            if os.path.splitext(filename)[1] != ".zip":
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("The specified file has to be a .zip file")
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                return

        try:
            if (
                os.path.join(config.get_properties_path(), "processes")
                not in sys.path
            ):
                sys.path.append(
                    os.path.join(config.get_properties_path(), "processes")
                )

            # Process config update
            if not os.path.isfile(
                os.path.join(
                    config.get_properties_path(),
                    "properties",
                    "process_config.yml",
                )
            ):
                open(
                    os.path.join(
                        config.get_properties_path(),
                        "properties",
                        "process_config.yml",
                    ),
                    "a",
                ).close()

            with open(
                os.path.join(
                    config.get_properties_path(),
                    "properties",
                    "process_config.yml",
                ),
                "r",
            ) as stream:
                try:
                    if verCmp(yaml.__version__, "5.1", "sup"):
                        process_dic = yaml.load(stream, Loader=yaml.FullLoader)
                    else:
                        process_dic = yaml.load(stream)

                except yaml.YAMLError as exc:
                    process_dic = {}
                    print(exc)

            if process_dic is None:
                process_dic = {}

            # Copying the original process tree
            process_dic_orig = copy(process_dic)

            try:
                packages = process_dic["Packages"]

            except (KeyError, TypeError):
                packages = {}

            try:
                paths = process_dic["Paths"]

            except (KeyError, TypeError):
                paths = []

            # Saving all the install packages names and checking if
            # the MIA_processes are updated
            package_names = []
            mia_processes_not_found = True

            # packages_already: packages already installed in populse_
            # mia (populse_mia/processes)
            packages_already = [
                dire
                for dire in os.listdir(
                    os.path.join(config.get_properties_path(), "processes")
                )
                if not os.path.isfile(
                    os.path.join(
                        config.get_properties_path(), "processes", dire
                    )
                )
            ]

            if is_zipfile(filename):
                # Extraction of the zipped content
                with ZipFile(filename, "r") as zip_ref:
                    packages_name = [
                        member.split("/")[0]
                        for member in zip_ref.namelist()
                        if (
                            len(member.split("/")) == 2
                            and not member.split("/")[-1]
                        )
                    ]

            elif os.path.isdir(filename):
                # !!! careful: if filename is not a zip file,
                # filename must be a directory
                # that contains only the package(s) to install!!!
                packages_name = [os.path.basename(filename)]

            for package_name in packages_name:
                # package_name: package(s) in the zip file or in folder

                if (package_name not in packages_already) or (
                    package_name == "mia_processes"
                ):
                    # Copy MIA_processes in a temporary folder
                    if mia_processes_not_found:
                        if (package_name == "mia_processes") and (
                            os.path.exists(
                                os.path.join(
                                    config.get_properties_path(),
                                    "processes",
                                    "mia_processes",
                                )
                            )
                        ):
                            mia_processes_not_found = False
                            tmp_folder4MIA = tempfile.mkdtemp()
                            shutil.copytree(
                                os.path.join(
                                    config.get_properties_path(),
                                    "processes",
                                    "mia_processes",
                                ),
                                os.path.join(tmp_folder4MIA, "MIA_processes"),
                            )

                    if is_zipfile(filename):
                        with ZipFile(filename, "r") as zip_ref:
                            members_to_extract = [
                                member
                                for member in zip_ref.namelist()
                                if member.startswith(package_name)
                            ]
                            zip_ref.extractall(
                                os.path.join(
                                    config.get_properties_path(), "processes"
                                ),
                                members_to_extract,
                            )

                    elif os.path.isdir(filename):
                        # distutils.dir_util.copy_tree(os.path.join(filename),
                        #                             os.path.join(
                        #                                 config.get_properties_path(),
                        #                                 'processes',
                        #                                 package_name))
                        shutil.copytree(
                            os.path.join(filename),
                            os.path.join(
                                config.get_properties_path(),
                                "processes",
                                package_name,
                            ),
                        )

                else:
                    date = datetime.now().strftime("%Y%m%d%H%M%S")

                    if is_zipfile(filename):
                        with ZipFile(filename, "r") as zip_ref:
                            temp_dir = tempfile.mkdtemp()
                            members_to_extract = [
                                member
                                for member in zip_ref.namelist()
                                if member.startswith(package_name)
                            ]
                            zip_ref.extractall(temp_dir, members_to_extract)
                            shutil.move(
                                os.path.join(temp_dir, package_name),
                                os.path.join(
                                    config.get_properties_path(),
                                    "processes",
                                    package_name + "_" + date,
                                ),
                            )

                    elif os.path.isdir(filename):
                        shutil.copytree(
                            os.path.join(filename),
                            os.path.join(
                                config.get_properties_path(),
                                "processes",
                                package_name + "_" + date,
                            ),
                        )

                    original_package_name = package_name
                    package_name = package_name + "_" + date

                    # Replacing the original package name pattern in
                    # all the extracted files by the package name
                    # with the date
                    _change_pattern_in_folder(
                        os.path.join(
                            config.get_properties_path(),
                            "processes",
                            package_name,
                        ),
                        original_package_name,
                        package_name,
                    )

                package_names.append(package_name)
                # package_names contains all the extracted packages
                final_package_dic = _add_package(packages, package_name)

            if (
                not os.path.join(config.get_properties_path(), "processes")
                in paths
            ):
                paths.append(
                    os.path.join(config.get_properties_path(), "processes")
                )

            process_dic["Packages"] = final_package_dic
            process_dic["Paths"] = paths

            # Idea: Should we encrypt the path ?

            with open(
                os.path.join(
                    config.get_properties_path(),
                    "properties",
                    "process_config.yml",
                ),
                "w",
                encoding="utf8",
            ) as stream:
                yaml.dump(
                    process_dic,
                    stream,
                    default_flow_style=False,
                    allow_unicode=True,
                )

            self.process_installed.emit()

            # Cleaning the temporary folder
            if "tmp_folder4MIA" in locals():
                shutil.rmtree(tmp_folder4MIA)

            if "temp_dir" in locals():
                shutil.rmtree(temp_dir)

        except Exception as e:
            print(
                '\nError during installation of the "{0}" library '
                "...!\nTraceback:".format(package_name)
            )
            print("".join(traceback.format_tb(e.__traceback__)), end="")
            print("{0}: {1}\n".format(e.__class__.__name__, e))
            self.result_add_package = False
            messg = ('Installation of the "{0}" library ' "aborted!").format(
                package_name
            )

            try:
                self.main_window.statusBar().showMessage(messg)
                QApplication.processEvents()

            except AttributeError:
                self.main_window.status_label.setText(messg)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(
                'Installation of the "{0}" library aborted ... !\nPlease see '
                "the standard output screen for more "
                "details.".format(package_name)
            )
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()
            self.close()

            # Resetting process_config.yml
            if process_dic_orig is None:
                process_dic_orig = {}

            with open(
                os.path.join(
                    config.get_properties_path(),
                    "properties",
                    "process_config.yml",
                ),
                "w",
                encoding="utf8",
            ) as stream:
                yaml.dump(
                    process_dic_orig,
                    stream,
                    default_flow_style=False,
                    allow_unicode=True,
                )

            # Deleting the extracted files
            if package_names is None:
                package_names = []

            for package_name in package_names:
                if os.path.exists(
                    os.path.join(
                        config.get_properties_path(), "processes", package_name
                    )
                ):
                    shutil.rmtree(
                        os.path.join(
                            config.get_properties_path(),
                            "processes",
                            package_name,
                        )
                    )

            # If the error comes from a MIA_process update,
            # the old version is restored
            if not mia_processes_not_found:
                distutils.dir_util.copy_tree(
                    os.path.join(tmp_folder4MIA, "mia_processes"),
                    os.path.join(
                        config.get_properties_path(),
                        "processes",
                        "mia_processes",
                    ),
                )

            if "tmp_folder4MIA" in locals():
                shutil.rmtree(tmp_folder4MIA)

            if "temp_dir" in locals():
                shutil.rmtree(temp_dir)

        else:
            if self.result_add_package:
                messg = (
                    'The "{0}" library has been ' "correctly installed."
                ).format(package_name)

                try:
                    self.main_window.statusBar().showMessage(messg)
                    QApplication.processEvents()

                except AttributeError:
                    self.main_window.status_label.setText(messg)

                msg = QMessageBox()
                msg.setWindowTitle("Installation completed")
                msg.setText(
                    'The "{0}" package has been correctly '
                    "installed.".format(package_name)
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                self.close()

            else:
                messg = (
                    'The "{0}" library has not been ' "correctly installed."
                ).format(package_name)

                try:
                    self.main_window.statusBar().showMessage(messg)
                    QApplication.processEvents()

                except AttributeError:
                    self.main_window.status_label.setText(messg)

                msg = QMessageBox()
                msg.setWindowTitle("Installation completed with error(s)")
                msg.setText(
                    'The "{0}" package has not been correctly '
                    "installed.".format(package_name)
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(msg.close)
                msg.exec()
                self.close()


class Node(object):
    """Class to handle a package children.

    .. Methods:
        -  __repr__: Define what should be printed by the class
        - _recurse_dict: add the name and value of the farthest child in the
        dictionary
        - addChild: add a child to the children list
        - attrs:
        - child: return a child from its index in the list
        - childCount: return the number of children
        - data: return the name or the value of the object
        - insertChild: insert a child to a specific position
        - log: return the logs
        - name: return the name of the object
        - parent: return the parent of the object
        - removeChild: remove a specific child
        - row: return the index of the object in its parent list of children
        - to_dict: return a dictionary of the children
        - to_list: return the list of children with their names and values
        - value: return the value of the object
            **Contains: Private function:**
                 - fget: get the value
                 - fset: set the value
        - setData: update the name or the value of the object
        - resource: return a None

    """

    def __init__(self, name, parent=None):
        """Initialization of the Node class."""

        self._name = name
        self._parent = parent
        self._children = []
        self._value = None
        if parent is not None:
            parent.addChild(self)

    def __repr__(self):
        """Define what should be printed by the class.

        :return: the logs

        """

        return self.log()

    def _recurse_dict(self, d):
        """Add the name and value of the farthest child in the dictionary.

        :param d: dictionary

        """

        if self._children:
            d[self.name] = {}
            for child in self._children:
                child._recurse_dict(d[self.name])
        else:
            d[self.name] = self.value

    def addChild(self, child):
        """Add a child to the children list.

        :param child: child to add

        """

        self._children.append(child)

    def attrs(self):
        """

        :return:

        """

        classes = self.__class__.__mro__
        keyvalued = {}
        for cls in classes:
            for key, value in cls.items():
                if isinstance(value, property):
                    keyvalued[key] = value.fget(self)
        return keyvalued

    def child(self, row):
        """Return a child from its index in the list.

        :param row: index in the list of children
        :return: child

        """

        return self._children[row]

    def childCount(self):
        """Return the number of children.

        :return: the length of the children list
        """
        return len(self._children)

    def data(self, column):
        """Return the name or the value of the object.

        :param column: 0 for name, 1 for value
        :return: string

        """

        if column == 0:
            parent = self._parent
            text = self.name
            while parent.name != "Root":
                text = parent.name + "." + text
                parent = parent._parent
            return text  # self.name

        elif column == 1:
            return self.value

    def insertChild(self, position, child):
        """Insert a child to a specific position.

        :param position: position
        :param child: child
        :return: boolean, True if the insertion was successful

        """

        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self
        return True

    def log(self, tabLevel=-1):
        """Return the logs.

        :param tabLevel: Number of tabulation
        :return: string

        """

        output = ""
        tabLevel += 1

        for i in range(tabLevel):
            output += "    "

        output += "".join(("|----", self._name, " = ", "\n"))

        for child in self._children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += "\n"
        return output

    def name():
        """Return the name of the object.

        :return: name

        """

        def fget(self):
            """Get the name of the object."""

            return self._name

        def fset(self, value):
            """Set tye name of the object."""

            self._name = value

        return locals()

    name = property(**name())

    def parent(self):
        """Return the parent of the object.

        :return: parent

        """

        return self._parent

    def removeChild(self, position, child):
        """Remove a specific child.

        :param position: position of the child
        :param child: child to remove
        :return: boolean, True if the child was removed

        """

        if position < 0 or position > len(self._children):
            return False

        self._children.pop(position)
        child._parent = None
        return True

    def row(self):
        """Return the index of the object in its parent list of children.

        :return: index

        """

        if self._parent is not None:
            return self._parent._children.index(self)

    def to_dict(self, d={}):
        """Return a dictionary of the children.

        :param d: dictionary
        :return: dictionary of children

        """

        for child in self._children:
            child._recurse_dict(d)
        return d

    def to_list(self):
        """Return the list of children with their names and values.

        :return: list

        """

        output = []
        if self._children:
            for child in self._children:
                output += [self.name, child.to_list()]
        else:
            output += [self.name, self.value]
        return output

    def value():
        """Return the value of the object.

        :return: value

        """

        def fget(self):
            """Get the value of the object."""

            return self._value

        def fset(self, value):
            """Set tye value of the object."""

            self._value = value

        return locals()

    value = property(**value())

    def setData(self, column, value):
        """Update the name or the value of the object.

        :param column: 0 for name, 1 for value
        :param value: new value

        """

        if column == 0:
            self.name = value
        if column == 1:
            self.value = value

    def resource(self):
        """Return None

        :return: None

        """

        return None


class PackageLibrary(QTreeWidget):
    """Tree that displays the user-added packages and their modules.
    The user can check or not each module/package.

    .. Methods:
        - fill_item: fills the items of the tree recursively
        - generate_tree: generates the package tree
        - recursive_checks: checks/unchecks all child items
        - recursive_checks_from_child: checks/unchecks all parent items
        - set_module_view: sets if a module has to be enabled or disabled in
                           the process library
        - update_checks: updates the checks of the tree from an item

    """

    def __init__(self, package_tree, paths):
        """Initialization of the PackageLibrary widget.

        :param package_tree: representation of the packages as
                             a tree-dictionary
        :param paths: list of paths to add to the system to import the packages

        """

        super(PackageLibrary, self).__init__()

        self.itemChanged.connect(self.update_checks)
        self.package_tree = package_tree
        self.paths = paths
        self.generate_tree()
        self.setAlternatingRowColors(True)
        self.setHeaderLabel("Packages")

    def fill_item(self, item, value):
        """Fill the items of the tree recursively.

        :param item: current item to fill
        :param value: value of the item in the tree

        """

        item.setExpanded(True)

        if type(value) is dict:
            for key, val in sorted(value.items()):
                child = QTreeWidgetItem()
                child.setText(0, str(key))
                item.addChild(child)
                if type(val) is dict:
                    self.fill_item(child, val)
                else:
                    if val == "process_enabled":
                        child.setCheckState(0, Qt.Checked)
                        self.recursive_checks_from_child(child)
                    elif val == "process_disabled":
                        child.setCheckState(0, Qt.Unchecked)

        elif type(value) is list:
            for val in value:
                child = QTreeWidgetItem()
                item.addChild(child)
                if type(val) is dict:
                    child.setText(0, "[dict]")
                    self.fill_item(child, val)
                elif type(val) is list:
                    child.setText(0, "[list]")
                    self.fill_item(child, val)
                else:
                    child.setText(0, str(val))

                child.setExpanded(True)

        else:
            child = QTreeWidgetItem()
            child.setText(0, str(value))
            item.addChild(child)

    def generate_tree(self):
        """Generate the package tree"""

        self.itemChanged.disconnect()
        self.clear()
        self.fill_item(self.invisibleRootItem(), self.package_tree)
        self.itemChanged.connect(self.update_checks)

    def recursive_checks(self, parent):
        """Check/uncheck all child items.

        :param parent: parent item

        """

        check_state = parent.checkState(0)

        if parent.childCount() == 0:
            self.set_module_view(parent, check_state)

        for i in range(parent.childCount()):
            parent.child(i).setCheckState(0, check_state)
            self.recursive_checks(parent.child(i))

    def recursive_checks_from_child(self, child):
        """Check/uncheck all parent items.

        :param child: child item

        """

        check_state = child.checkState(0)

        if child.childCount() == 0:
            self.set_module_view(child, check_state)

        if child.parent():
            parent = child.parent()
            if child.checkState(0) == Qt.Checked:
                if parent.checkState(0) == Qt.Unchecked:
                    parent.setCheckState(0, Qt.Checked)
                    self.recursive_checks_from_child(parent)
            else:
                # checked_children = []
                # for child in range(parent.childCount()):
                #
                #     if child.checkState(0) == Qt.Checked:
                #         checked_children.append()

                checked_children = [
                    child
                    for child in range(parent.childCount())
                    if parent.child(child).checkState(0) == Qt.Checked
                ]
                if not checked_children:
                    parent.setCheckState(0, Qt.Unchecked)
                    self.recursive_checks_from_child(parent)

    def set_module_view(self, item, state):
        """Set if a module has to be enabled or disabled in the process
        library.

        :param item: item selected in the current tree
        :param state: checked or not checked (Qt.Checked == 2. So if
                      val == 2 -> checkbox is checked, and if
                      val == 0 -> checkbox is not checked)
        """

        if state == Qt.Checked:
            val = "process_enabled"
        else:
            val = "process_disabled"

        list_path = []
        list_path.append(item.text(0))
        self.top_level_items = [
            self.topLevelItem(i) for i in range(self.topLevelItemCount())
        ]

        while item not in self.top_level_items:
            item = item.parent()
            list_path.append(item.text(0))
        # pkg_iter take only the modules concerning the top package where a
        # change of status where done.
        pkg_iter = self.package_tree
        list_path = list(reversed(list_path))
        for element in list_path:
            if element in pkg_iter.keys():
                if element is list_path[-1]:
                    pkg_iter[element] = val
                else:
                    pkg_iter = pkg_iter[element]
            else:
                print("Package not found")
                break

    def update_checks(self, item, column):
        """Update the checks of the tree from an item.

        :param item: item on which to begin
        :param column: column from the check (should always be 0)

        """

        # Checked state is stored on column 0
        if column == 0:
            self.itemChanged.disconnect()
            if item.childCount():
                self.recursive_checks(item)
            if item.parent():
                self.recursive_checks_from_child(item)

            self.itemChanged.connect(self.update_checks)


class PackageLibraryDialog(QDialog):
    """Dialog that controls which processes to show in the process library.

    .. Methods:
        - add_package: add a package and its modules to the package tree
        - add_package_with_text: add a package from the line edit's text
        - browse_package: open a browser to select a package
        - delete_package: delete a package, only available to administrators
        - delete_package_with_text: delete a package from the line edit's text
        - install_processes_pop_up: open the install processes pop-up
        - load_config: update the config and loads the corresponding packages
        - load_packages: update the tree of the process library
        - ok_clicked: called when apply changes is clicked
        - remove_package: remove a package from the package tree
        - remove_package_with_text: remove the package in the line edit from
          the package tree
        - reset_action: called to reset a previous add or remove package action
        - save: save the tree to the process_config.yml file
        - save_config: save the current config to process_config.yml
        - update_config: update the process_config and package_library
          attributes

    """

    signal_save = Signal()

    def __init__(self, mia_main_window=None, parent=None):
        """Initialization of the PackageLibraryDialog widget"""
        super(PackageLibraryDialog, self).__init__(parent)

        self.main_window = mia_main_window

        config = Config()

        if config.get_user_mode():
            self.setWindowTitle("Package library manager [user mode]")
        else:
            self.setWindowTitle("Package library manager [admin mode]")
        # True if the path specified in the line edit is a path with '/'
        self.is_path = False

        self.process_config = self.load_config()
        self.load_packages()

        self.pkg_config = deepcopy(self.packages)

        self.package_library = PackageLibrary(self.packages, self.paths)

        self.status_label = QLabel()
        self.status_label.setText("")
        self.status_label.setStyleSheet(
            "QLabel{font-size:10pt;font:italic;text-align: center}"
        )

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(
            "Type a Python package (ex. nipype.interfaces.spm)"
        )

        """push_button_browse = QPushButton()
        push_button_browse.setText("Browse")
        push_button_browse.clicked.connect(self.browse_package)"""

        push_button_add_pkg_file = QPushButton(
            default=False, autoDefault=False
        )
        push_button_add_pkg_file.setText("Zipfile")
        push_button_add_pkg_file.clicked.connect(
            partial(self.install_processes_pop_up, False)
        )

        push_button_add_pkg_folder = QPushButton(
            default=False, autoDefault=False
        )
        push_button_add_pkg_folder.setText("Folder")
        push_button_add_pkg_folder.clicked.connect(
            partial(self.install_processes_pop_up, True)
        )

        push_button_add_pkg = QPushButton(default=False, autoDefault=False)
        push_button_add_pkg.setText("Add/Update package")
        push_button_add_pkg.clicked.connect(self.add_package_with_text)

        push_button_rm_pkg = QPushButton(default=False, autoDefault=False)
        push_button_rm_pkg.setText("Remove package")
        push_button_rm_pkg.clicked.connect(self.remove_package_with_text)

        push_button_del_pkg = QPushButton(default=False, autoDefault=False)
        push_button_del_pkg.setText("Delete package")
        # push_button_del_pkg.clicked.connect(self.delete_package)
        push_button_del_pkg.clicked.connect(self.delete_package_with_text)

        self.add_dic = {}
        self.remove_dic = {}
        self.delete_dic = {}

        self.add_list = QListWidget()
        self.remove_list = QListWidget()
        self.del_list = QListWidget()

        # using soma: AttributeError: module 'PyQt5.QtGui' has no
        #             attribute 'QAbstractItemView'
        """
        self.add_list.setSelectionMode(
            QtGui.QAbstractItemView.ExtendedSelection)
        self.remove_list.setSelectionMode(
            QtGui.QAbstractItemView.ExtendedSelection)
        self.del_list.setSelectionMode(
            QtGui.QAbstractItemView.ExtendedSelection)
        """
        # so use QAbstractItemView directly from PyQt5.QtWidgets
        self.add_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.remove_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.del_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        push_button_save = QPushButton(default=False, autoDefault=False)
        push_button_save.setText("Apply changes")
        push_button_save.clicked.connect(partial(self.ok_clicked))

        push_button_cancel = QPushButton(
            "Cancel", default=False, autoDefault=False
        )
        push_button_cancel.setObjectName("pushButton_cancel")
        push_button_cancel.clicked.connect(self.close)

        # Layout

        h_box_line_edit = QHBoxLayout()
        h_box_line_edit.addWidget(self.line_edit)
        # h_box_line_edit.addWidget(push_button_add_pkg)
        # h_box_browse.addWidget(push_button_browse)

        h_box_install = QHBoxLayout()
        h_box_install.addWidget(QLabel("Install processes from:"))
        h_box_install.addStretch(1)
        h_box_install.addWidget(push_button_add_pkg_file)
        h_box_install.addWidget(push_button_add_pkg_folder)

        h_box_label = QHBoxLayout()
        h_box_label.addStretch(1)
        h_box_label.addWidget(self.status_label)
        h_box_label.addStretch(1)

        h_box_save = QHBoxLayout()
        h_box_save.addStretch(1)
        h_box_save.addWidget(push_button_save)
        h_box_save.addWidget(push_button_cancel)

        h_box_buttons = QHBoxLayout()
        h_box_buttons.addWidget(push_button_add_pkg)
        h_box_buttons.addWidget(push_button_rm_pkg)
        if config.get_user_mode() is False:
            h_box_buttons.addWidget(push_button_del_pkg)

        group_import = QGroupBox("Added packages")
        group_remove = QGroupBox("Removed packages")
        group_delete = QGroupBox("Deleted packages")
        h_box_import = QHBoxLayout()
        h_box_remove = QHBoxLayout()
        h_box_delete = QHBoxLayout()

        h_box_import.addWidget(self.add_list)
        h_box_remove.addWidget(self.remove_list)
        h_box_delete.addWidget(self.del_list)

        cancel_add = QPushButton("Reset", default=False, autoDefault=False)
        cancel_rem = QPushButton("Reset", default=False, autoDefault=False)
        cancel_del = QPushButton("Reset", default=False, autoDefault=False)

        cancel_add.clicked.connect(
            partial(self.reset_action, self.add_list, True)
        )
        cancel_rem.clicked.connect(
            partial(self.reset_action, self.remove_list, False)
        )
        cancel_del.clicked.connect(
            partial(self.reset_action, self.del_list, False)
        )

        h_box_import.addWidget(cancel_add)
        h_box_remove.addWidget(cancel_rem)
        h_box_delete.addWidget(cancel_del)

        group_import.setLayout(h_box_import)
        group_remove.setLayout(h_box_remove)
        group_delete.setLayout(h_box_delete)

        v_box = QVBoxLayout()
        v_box.addStretch(1)
        v_box.addLayout(h_box_install)
        v_box.addStretch(1)
        v_box.addLayout(h_box_label)
        v_box.addLayout(h_box_line_edit)
        v_box.addStretch(1)
        v_box.addLayout(h_box_buttons)
        v_box.addStretch(1)
        v_box.addWidget(group_import)
        v_box.addStretch(1)
        v_box.addWidget(group_remove)
        v_box.addStretch(1)
        v_box.addWidget(group_delete)
        v_box.addStretch(1)
        v_box.addLayout(h_box_save)

        h_box = QHBoxLayout()
        h_box.addWidget(self.package_library)
        h_box.addLayout(v_box)

        self.setLayout(h_box)

    def add_package(
        self,
        module_name,
        class_name=None,
        show_error=False,
        init_package_tree=False,
    ):
        """Add a package and its modules to the package tree.

        :param module_name: name of the module
        :param class_name: name of the class
        :param show_error: display error in a message box in case of error. If
          False, errors are silent and error messages returned at the end of
          execution
        :param init_package_tree: boolean to initialize the package tree

        """

        if init_package_tree is True:
            self.update_config()
            del self.packages

        self.packages = self.package_library.package_tree
        config = Config()

        if module_name:
            if (
                os.path.join(config.get_properties_path(), "processes")
                not in sys.path
            ):
                sys.path.append(
                    os.path.join(config.get_properties_path(), "processes")
                )

            # Reloading the package
            if module_name in sys.modules.keys():
                del sys.modules[module_name]

            err_msg = []

            try:
                __import__(module_name)
                pkg = sys.modules[module_name]

                # Checking if there are subpackages
                if hasattr(pkg, "__path__"):
                    for importer, modname, ispkg in pkgutil.iter_modules(
                        pkg.__path__
                    ):
                        if ispkg and modname != "__main__":
                            err_msg += self.add_package(
                                str(module_name + "." + modname),
                                class_name,
                                show_error=False,
                            )

                for k, v in sorted(list(pkg.__dict__.items())):
                    # Checking each class of in the package
                    if inspect.isclass(v):
                        try:
                            get_process_instance(
                                "%s.%s" % (module_name, v.__name__)
                            )

                        except Exception as e:
                            print(
                                '\nError during installation of the "{0}" '
                                "module ...!\nTraceback:".format(module_name)
                            )
                            print(
                                "".join(traceback.format_tb(e.__traceback__)),
                                end="",
                            )
                            print("{0}: {1}\n".format(e.__class__.__name__, e))

                        else:
                            # Updating the tree's dictionary
                            path_list = module_name.split(".")
                            path_list.append(k)
                            pkg_iter = self.packages
                            recurs = False

                            for element in path_list:
                                if element == class_name:
                                    recurs = True

                                if (
                                    element in pkg_iter.keys()
                                    and element is not path_list[-1]
                                ):
                                    pkg_iter = pkg_iter[element]

                                else:
                                    if element is path_list[-1]:
                                        if (
                                            element == class_name
                                            or recurs is True
                                        ):
                                            print(
                                                "\nAdding %s.%s ..."
                                                % (module_name, v.__name__)
                                            )
                                            pkg_iter[element] = (
                                                "process_enabled"
                                            )

                                        elif element in pkg_iter.keys():
                                            pkg_iter = pkg_iter[element]

                                        # else:
                                        #     print(
                                        #         '\nA not installed pipeline '
                                        #         'was detected in the %s '
                                        #         'library:' % (path_list[0]))
                                        #     print('- %s.%s ...' % (
                                        #         module_name, v.__name__))
                                        #     print(
                                        #        'This pipeline is now '
                                        #        'installed but disabled '
                                        #        '(see File > Package Library '
                                        #        'Manager to enable it) ...')
                                        #     pkg_iter[
                                        #         element] = 'process_disabled'

                                    else:
                                        pkg_iter[element] = {}
                                        pkg_iter = pkg_iter[element]

                self.package_library.package_tree = self.packages
                self.package_library.generate_tree()
                return err_msg

            except Exception as err:
                err_msg.append(
                    "in {2}: {0}: {1}.".format(err.__class__, err, module_name)
                )

            if show_error and len(err_msg) != 0:
                msg = QMessageBox()
                msg.setText("\n".join(err_msg))
                msg.setIcon(QMessageBox.Warning)
                msg.exec_()

            return err_msg

        else:
            return "No package selected!"

    def add_package_with_text(self, _2add=False, update_view=True):
        """Add a package from the line edit's text.
        :param _2add: name of package
        :param update_view: boolean to update the QListWidget

        """

        if _2add is False:
            _2add = self.line_edit.text()

        if self.is_path:  # Currently, the self.is_path = False
            # (Need to pass by the method browse_package to initialise to
            # True and the Browse button is commented.
            # Could be interesting to permit a backdoor to pass
            # the absolute path in the field for add package,
            # to be continued... )

            path, package = os.path.split(_2add)
            # Adding the module path to the system path
            sys.path.append(path)
            self.add_package(package)
            self.paths.append(os.path.relpath(path))

        else:
            # self.package_library.package_tree = self.load_config(
            #       )['Packages']
            old_status = self.status_label.text()

            self.status_label.setText("Adding {0}. Please wait.".format(_2add))
            QApplication.processEvents()

            if os.path.splitext(_2add)[1]:
                part = ""
                old_part = ""
                flag = False

                for content in _2add.split("."):
                    part += content

                    try:
                        __import__(part)

                    except ImportError:
                        try:
                            flag = True

                            if content in dir(sys.modules[old_part]):
                                errors = self.add_package(
                                    os.path.splitext(_2add)[0],
                                    os.path.splitext(_2add)[1][1:],
                                )
                                break

                            else:
                                errors = self.add_package(_2add)
                                break

                        except KeyError:
                            errors = (
                                "No package, module or class "
                                "named {}!".format(_2add)
                            )
                            break

                    old_part = part
                    part += "."

                if flag is False:
                    errors = self.add_package(
                        os.path.splitext(_2add)[0],
                        os.path.splitext(_2add)[1][1:],
                    )

            else:
                errors = self.add_package(
                    os.path.splitext(_2add)[0], os.path.splitext(_2add)[0]
                )

            if len(errors) == 0:
                self.status_label.setText(
                    "{0} added to the Package Library.".format(_2add)
                )
                if update_view:
                    if _2add not in self.add_dic:
                        self.add_list.addItem(_2add)
                        self.add_dic[_2add] = self.add_list.count() - 1
                if _2add in self.remove_dic:
                    index = self.remove_dic[_2add]
                    self.remove_list.takeItem(self.remove_dic[_2add])
                    self.remove_dic.pop(_2add)
                    for key in self.remove_dic:
                        if self.remove_dic[key] > index:
                            self.remove_dic[key] = self.remove_dic[key] - 1
                if _2add in self.delete_dic:
                    index = self.delete_dic[_2add]
                    self.del_list.takeItem(self.delete_dic[_2add])
                    self.delete_dic.pop(_2add)
                    for key in self.delete_dic:
                        if self.delete_dic[key] > index:
                            self.delete_dic[key] = self.delete_dic[key] - 1
                # if self.line_edit.text() in self.remove_list:
                #     self.remove_list.

            else:
                self.status_label.setText(old_status)
                msg = QMessageBox()

                if isinstance(errors, str):
                    msg.setText(errors)

                elif isinstance(errors, list):
                    msg.setText("\n".join(errors))

                msg.setIcon(QMessageBox.Warning)
                msg.exec_()

    # def browse_package(self):
    #     """Open a browser to select a package."""
    #
    #     file_dialog = QFileDialog()
    #     file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
    #
    #     # To select files or directories, we should use a proxy model
    #     # but mine is not working yet...
    #
    #     # file_dialog.setProxyModel(FileFilterProxyModel())
    #     file_dialog.setFileMode(QFileDialog.Directory)
    #     # file_dialog.setFileMode(QFileDialog.Directory |
    #     # QFileDialog.ExistingFile)
    #     # file_dialog.setFilter("Processes (*.py *.xml)")
    #
    #     if file_dialog.exec_():
    #         file_name = file_dialog.selectedFiles()[0]
    #         file_name = os.path.abspath(file_name)
    #         self.is_path = True
    #         self.line_edit.setText(file_name)

    def delete_package(
        self,
        index=1,
        to_delete=None,
        remove=True,
        loop=False,
        from_pipeline_manager=False,
    ):
        """Delete a package, only available to administrators.

        Remove the package from the package library tree, update the
        __init__ file and delete the package directory and files if there
        are empty.

        :param index: recursive index to move between modules
        :param to_delete: the brick (class) do delete (ex. test.Test)
        :param remove: (boolean) if True, remove the brick(s) from the
                       package tree
        :param loop: (boolean) to loop silently (if True no confirmation
                     is requested before deletion)

        :return: the list of deleted brick (class)

        """

        deleted_packages = []
        self.packages = self.package_library.package_tree
        config = Config()

        if not to_delete:
            to_delete = self.line_edit.text()

        if to_delete == "":
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("Package not found.")
            self.msg.setInformativeText(
                "Please write the python path to the package you want to "
                "delete."
            )
            self.msg.setWindowTitle("Warning")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.buttonClicked.connect(self.msg.close)
            self.msg.show()
            return deleted_packages

        if to_delete.split(".")[0] in ["nipype", "mia_processes", "capsul"]:
            if from_pipeline_manager:
                inform_text = (
                    "This package belongs to "
                    + to_delete.split(".")[0]
                    + " which is required "
                    "by populse mia.\n You can still hide it in the "
                    "package library manager."
                )

            else:
                inform_text = (
                    "This package belongs to "
                    + to_delete.split(".")[0]
                    + " which is required "
                    "by populse_mia.\nTherefore, it has only been "
                    "hidden (removed)."
                )

            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Critical)
            self.msg.setText("This package can not be deleted.")
            self.msg.setInformativeText(inform_text)
            self.msg.setWindowTitle("Error")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.buttonClicked.connect(self.msg.close)
            self.msg.show()
            return deleted_packages

        if index == 1 and loop is False:
            msgtext = "Do you really want to delete the package {}?".format(
                to_delete
            )
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            title = "populse_mia - Warning: Delete package"
            reply = msg.question(
                self, title, msgtext, QMessageBox.Yes, QMessageBox.No
            )
        else:
            reply = QMessageBox.Yes

        if reply == QMessageBox.Yes:
            pkg_list = to_delete.split(".")

            if index <= len(pkg_list):
                path = os.path.join(
                    config.get_properties_path(),
                    "processes",
                    *pkg_list[0:index],
                )
                sub_deleted_packages = self.delete_package(
                    index + 1,
                    to_delete,
                    from_pipeline_manager=from_pipeline_manager,
                )

                for sub_pkg in sub_deleted_packages:
                    if sub_pkg not in deleted_packages:
                        deleted_packages.append(sub_pkg)

                if os.path.exists(path):
                    del_path = False

                    if (len(glob.glob(os.path.join(path, "*"))) == 0) or (
                        index == len(pkg_list)
                    ):
                        del_path = True

                    else:
                        is_import = False

                        for root, dirs, files in os.walk(path):
                            if "__init__.py" in files:
                                with open(
                                    os.path.join(root, "__init__.py"), "r"
                                ) as f:
                                    lines = f.readlines()

                                for line in lines:
                                    if (
                                        not line.startswith("#")
                                        and "import" in line
                                    ):
                                        is_import = True

                        if (
                            not is_import
                            and os.path.split(path)[-1] != "User_processes"
                        ):
                            del_path = True

                    if del_path:
                        shutil.rmtree(path)
                        self.main_window.statusBar().showMessage(
                            "{0} was "
                            "deleted ({1} library) ...".format(
                                path, os.path.split(path)[-1]
                            )
                        )
                        # fmt: off
                        print(
                            "\nDeleting {0} "
                            "...".format(
                                ".".join(
                                    path.split(os.sep)[
                                        path.split(os.sep).index("processes")
                                        + 1:
                                    ]
                                )
                            )
                        )
                        # fmt: on

                        if index > 0 and remove:
                            self.remove_package_with_text(
                                ".".join(pkg_list[0:index]), False
                            )

                else:
                    init = os.path.join(
                        config.get_properties_path(),
                        "processes",
                        *pkg_list[: index - 1],
                        "__init__.py",
                    )

                    if os.path.isfile(init):
                        with open(init, "r") as f:
                            lines = f.readlines()

                        import_line = False
                        imports_in_init = dict()
                        imports_string = ""

                        for line in lines:
                            if (line.startswith("#") is False) and (
                                "import" in line
                            ):
                                from_package = line.split(" ")[1]
                                from_package = from_package[1:]
                                imports_in_init[from_package] = []

                        for line in lines:
                            if (line.startswith("#") is False) and (
                                ("import" in line) or (import_line is True)
                            ):
                                if "from" in line:
                                    from_package = line.split(" ")[1]
                                    from_package = from_package[1:]
                                    imports_string = "".join(
                                        [
                                            imports_string,
                                            line.split("import")[1],
                                        ]
                                    )

                                elif import_line is True:
                                    imports_string = imports_string + line

                                if "(" in line:
                                    import_line = True

                                if ")" in line:
                                    import_line = False

                                if import_line is False:
                                    imports = imports_string.split(",")
                                    imports = [
                                        " ".join(i.split()) for i in imports
                                    ]

                                    for imp in imports:
                                        imports_in_init[from_package].append(
                                            imp.replace("(", "").replace(
                                                ")", ""
                                            )
                                        )

                                    imports_string = ""

                        if not imports_in_init:
                            print(
                                "\nThe {} brick seems to be corrupted and is "
                                "not accessible ...".format(to_delete)
                            )

                        for key in imports_in_init:
                            if pkg_list[index - 1] in imports_in_init[key]:
                                filename = key + ".py"
                                delete_all = True

                                if len(imports_in_init[key]) > 1:
                                    msgtext = (
                                        "The brick (class) {0} alone "
                                        "cannot be deleted because it "
                                        "belongs to {1} module that "
                                        "contains following brick(s)"
                                        ":".format(
                                            pkg_list[index - 1],
                                            ".".join(
                                                pkg_list[: index - 1] + [key]
                                            ),
                                        )
                                    )

                                    for brick in imports_in_init[key]:
                                        msgtext = msgtext + "\n  - " + brick

                                    msg = QMessageBox()
                                    msg.setText(msgtext)
                                    msg.setIcon(QMessageBox.Warning)
                                    title = (
                                        "populse_mia - Warning: "
                                        "Delete package"
                                    )
                                    msg.setWindowTitle(title)
                                    msg.setStandardButtons(
                                        QMessageBox.Yes | QMessageBox.No
                                    )
                                    button_delete = msg.button(
                                        QtGui.QMessageBox.Yes
                                    )
                                    button_delete.setText("Delete all")
                                    button_cancel = msg.button(
                                        QtGui.QMessageBox.No
                                    )
                                    button_cancel.setText("Cancel")
                                    returnValue = msg.exec()

                                    if returnValue == QMessageBox.No:
                                        delete_all = False

                                if delete_all is True:
                                    dir_init = os.path.split(init)[0]
                                    file2del = os.path.join(dir_init, filename)

                                    if os.path.isfile(file2del):
                                        # fmt: off
                                        name = file2del.split(os.sep)[
                                            file2del.split(os.sep).index(
                                                "processes"
                                            )
                                            + 1:-1
                                        ]
                                        # fmt: on
                                        name = ".".join(name)

                                        for pkg in imports_in_init[key]:
                                            deleted_packages.append(
                                                ".".join([name, pkg])
                                            )

                                        for pkg in deleted_packages:
                                            print(
                                                "\nDeleting {0} "
                                                "...".format(pkg)
                                            )

                                        os.remove(file2del)
                                        (
                                            self.main_window.statusBar
                                        )().showMessage(
                                            "{0} was deleted ({1} "
                                            "brick(s)) "
                                            "...".format(
                                                file2del,
                                                ", ".join(
                                                    imports_in_init[key]
                                                ),
                                            )
                                        )

                                    if remove:
                                        for pkg in deleted_packages:
                                            self.remove_package_with_text(
                                                pkg, False
                                            )

                                    # rewrite __init_.py to wipe module
                                    import_line = False

                                    with open(init, "w") as f:
                                        for line in lines:
                                            if key in line:
                                                if "(" in line:
                                                    import_line = True

                                            elif import_line is True:
                                                if ")" in line:
                                                    import_line = False

                                            elif import_line is False:
                                                f.write(line)

                                    # if all packages have been deleted,
                                    # cleaning up empty files
                                    with open(init, "r") as f:
                                        lines = f.readlines()

                                    is_import = False

                                    for line in lines:
                                        if (
                                            not line.startswith("#")
                                            and "import" in line
                                        ):
                                            is_import = True

                                    if (
                                        not is_import
                                        and pkg_list[0] != "User_processes"
                                    ):
                                        os.remove(init)

                                        for elt in os.listdir(dir_init):
                                            if elt == "__pycache__":
                                                shutil.rmtree(
                                                    os.path.join(
                                                        dir_init, elt
                                                    ),
                                                    ignore_errors=True,
                                                )

                                            if os.path.isfile(
                                                os.path.join(dir_init, elt)
                                            ):
                                                os.remove(
                                                    os.path.join(dir_init, elt)
                                                )

            self.package_library.package_tree = self.packages
            self.package_library.generate_tree()
            self.save(False)

            return deleted_packages

    def delete_package_with_text(self, _2del=False, update_view=True):
        """Delete a package from the line edit's text.
        :param _2del: name of package
        :param update_view: boolean to update the QListWidget

        """
        old_status = self.status_label.text()

        if _2del is False:
            _2del = self.line_edit.text()
            self.status_label.setText(
                "Deleting {0}. Please wait.".format(_2del)
            )
            QApplication.processEvents()

        if _2del not in self.delete_dic:
            package_removed = self.remove_package(_2del)

        else:
            package_removed = True

        if package_removed is True:
            if update_view:
                if _2del not in self.delete_dic:
                    self.del_list.addItem(_2del)
                    self.delete_dic[_2del] = self.del_list.count() - 1

            if _2del in self.add_dic:
                index = self.add_dic[_2del]
                self.add_list.takeItem(self.add_dic[_2del])
                self.add_dic.pop(_2del)
                for key in self.add_dic:
                    if self.add_dic[key] > index:
                        self.add_dic[key] = self.add_dic[key] - 1

            if _2del in self.remove_dic:
                index = self.remove_dic[_2del]
                self.remove_list.takeItem(self.remove_dic[_2del])
                self.remove_dic.pop(_2del)
                for key in self.remove_dic:
                    if self.remove_dic[key] > index:
                        self.remove_dic[key] = self.remove_dic[key] - 1

            self.status_label.setText(
                "{0} deleted from Package Library.".format(_2del)
            )

        else:
            self.status_label.setText(old_status)

    def install_processes_pop_up(self, folder=False):
        """Open the install processes pop-up.

        :param folder: boolean, True if installing from a folder

        """

        self.pop_up_install_processes = InstallProcesses(self, folder=folder)
        self.pop_up_install_processes.show()
        # self.pop_up_install_processes.process_installed.connect(
        #    self.parent.pipeline_manager.processLibrary.update_process_library)
        self.pop_up_install_processes.process_installed.connect(
            self.update_config
        )

    @staticmethod
    def load_config():
        """Update the config and loads the corresponding packages.

        :return: the config as a dictionary

        """
        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        config = Config()

        with open(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            ),
            "r",
        ) as stream:
            try:
                if verCmp(yaml.__version__, "5.1", "sup"):
                    return yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    return yaml.load(stream)

            except yaml.YAMLError as exc:
                print(exc)

    def load_packages(self):
        """Update the tree of the process library."""

        try:
            self.packages = self.process_config["Packages"]
        except KeyError:
            self.packages = {}
        except TypeError:
            self.packages = {}
        try:
            self.paths = self.process_config["Paths"]
        except KeyError:
            self.paths = []
        except TypeError:
            self.paths = []

    def ok_clicked(self):
        """Called when apply changes is clicked."""

        pkg_to_delete = list(self.delete_dic.keys())
        reply = None
        deleted_packages = []
        for i in pkg_to_delete:
            if i not in deleted_packages:
                if reply is None:
                    msgtext = (
                        "Do you really want to delete "
                        'the "{0}" package?'.format(i)
                    )
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    title = "populse_mia - Warning: Delete package"
                    reply = msg.question(
                        self,
                        title,
                        msgtext,
                        QMessageBox.Yes
                        | QMessageBox.No
                        | QMessageBox.YesToAll
                        | QMessageBox.NoToAll,
                    )
                if reply == QMessageBox.YesToAll or reply == QMessageBox.Yes:
                    sub_deleted_packages = self.delete_package(
                        to_delete=i, remove=False, loop=True
                    )
                    for sub_pkg in sub_deleted_packages:
                        if sub_pkg not in deleted_packages:
                            deleted_packages.append(sub_pkg)
                # TODO Do we want to reinitialize the initial state ?
                elif reply == QMessageBox.NoToAll or reply == QMessageBox.No:
                    self.add_package_with_text(i)
                if reply == QMessageBox.No or reply == QMessageBox.Yes:
                    reply = None
        self.save()

    # def remove_package(self, package, check_flag=True):
    def remove_package(self, package):
        """Remove a package from the package tree.

        :param package: module's representation as a string
           (e.g.: nipype.interfaces.spm)
        :return: True if the package has been removed correctly

        """
        self.packages = self.package_library.package_tree
        config = Config()

        if package:
            if (
                os.path.join(config.get_properties_path(), "processes")
                not in sys.path
            ):
                sys.path.append(
                    os.path.join(config.get_properties_path(), "processes")
                )

            path_list = package.split(".")
            pkg_iter = self.packages

            if package in self.remove_dic or package in self.delete_dic:
                check_flag = True

            else:
                check_flag = False

            for element in path_list:
                if element in pkg_iter.keys():
                    if element is not path_list[-1]:
                        pkg_iter = pkg_iter[element]

                    else:
                        del pkg_iter[element]

                        if path_list[: path_list.index(element)]:
                            print(
                                "\nRemoving {0}.{1} ...".format(
                                    ".".join(
                                        path_list[: path_list.index(element)]
                                    ),
                                    element,
                                )
                            )

                        else:
                            print("\nRemoving {0} ...".format(element))

                elif check_flag is True:
                    pass

                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle(
                        "Warning: Package not found in Package Library"
                    )
                    msg.setText("Package {0} not found".format(package))
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.buttonClicked.connect(msg.close)
                    msg.exec()
                    return None

        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning: Package not found in Package Library")
            msg.setText("No package selected!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(msg.close)
            msg.exec()
            return False

        self.package_library.package_tree = self.packages
        self.package_library.generate_tree()
        return True

    # def remove_package_with_text(self, _2rem=None, update_view=True,
    #                                                          check_flag=True):
    def remove_package_with_text(
        self, _2rem=None, update_view=True, tree_remove=True
    ):
        """Remove the package in the line edit from the package tree.

        :param _2rem: name of package
        :param update_view: boolean to update the QListWidget
        :param tree_remove: boolean, remove from the tree

        """

        old_status = self.status_label.text()

        if _2rem is False:
            _2rem = self.line_edit.text()
            self.status_label.setText(
                "Removing {0}. Please wait.".format(_2rem)
            )
            QApplication.processEvents()

        # package_removed = self.remove_package(_2rem, check_flag)
        if _2rem not in self.delete_dic and tree_remove:
            package_removed = self.remove_package(_2rem)
        else:
            package_removed = True

        if package_removed is True:
            if update_view and _2rem not in self.remove_dic:
                self.remove_list.addItem(_2rem)
                self.remove_dic[_2rem] = self.remove_list.count() - 1
            if _2rem in self.add_dic:
                index = self.add_dic[_2rem]
                self.add_list.takeItem(self.add_dic[_2rem])
                self.add_dic.pop(_2rem)
                for key in self.add_dic:
                    if self.add_dic[key] > index:
                        self.add_dic[key] = self.add_dic[key] - 1
            if _2rem in self.delete_dic:
                index = self.delete_dic[_2rem]
                self.del_list.takeItem(self.delete_dic[_2rem])
                self.delete_dic.pop(_2rem)
                for key in self.delete_dic:
                    if self.delete_dic[key] > index:
                        self.delete_dic[key] = self.delete_dic[key] - 1
            self.status_label.setText(
                "{0} removed from Package Library.".format(_2rem)
            )
        else:
            self.status_label.setText(old_status)

    def reset_action(self, itemlist, add):
        """Called to reset a prevous add or remove package action.

        :param itemlist: the QListWidget from add or remove package
        :param add: boolean to know which list to update

        """

        for i in itemlist.selectedItems():
            if add is True:
                in_config = True
                for pkg in i.text().split("."):
                    if pkg in self.pkg_config:
                        self.pkg_config = self.pkg_config[pkg]
                    else:
                        in_config = False
                if in_config:
                    self.remove_package_with_text(
                        i.text(), update_view=False, tree_remove=False
                    )
                else:
                    self.remove_package_with_text(i.text(), update_view=False)

            else:
                self.add_package_with_text(i.text(), update_view=False)

    def save(self, close=True):
        """Save the tree to the process_config.yml file."""

        # Updating the packages and the paths according to the
        # package library tree

        self.packages = self.package_library.package_tree
        self.paths = self.package_library.paths

        if self.process_config:
            if self.process_config.get("Packages"):
                del self.process_config["Packages"]

            if self.process_config.get("Paths"):
                del self.process_config["Paths"]
        else:
            self.process_config = {}

        self.process_config["Packages"] = self.packages
        self.process_config["Paths"] = list(set(self.paths))
        config = Config()

        with open(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            ),
            "w",
            encoding="utf8",
        ) as configfile:
            yaml.dump(
                self.process_config,
                configfile,
                default_flow_style=False,
                allow_unicode=True,
            )
            self.signal_save.emit()

        if close:
            self.close()

    def save_config(self):
        """Save the current config to process_config.yml."""

        config = Config()
        self.process_config["Packages"] = self.packages
        self.process_config["Paths"] = self.paths

        with open(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            ),
            "w",
            encoding="utf8",
        ) as stream:
            yaml.dump(
                self.process_config,
                stream,
                default_flow_style=False,
                allow_unicode=True,
            )
        # self.update_config()

    def update_config(self):
        """Update the process_config and package_library attributes."""

        self.process_config = self.load_config()
        self.load_packages()
        self.package_library.package_tree = self.packages
        self.package_library.paths = self.paths
        self.package_library.generate_tree()


class ProcessHelp(QWidget):
    """A widget that displays information about the selected process.

    :param process: selected process

    """

    def __init__(self, process):
        """Generate the help.

        :param process: selected process

        """

        super(ProcessHelp, self).__init__()

        label = QLabel()
        label.setText(process.help())


class ProcessLibrary(QTreeView):
    """
    Tree to display the available Capsul's processes

    :param d: dictionary corresponding to the tree (dict)

    .. Methods:
        - keyPressEvent: event when the delete key is pressed
        - load_dictionary: loads a dictionary to the tree
        - mousePressEvent: event when the mouse is pressed
        - to_dict: returns a dictionary from the current tree

    """

    item_library_clicked = QtCore.Signal(str)

    def __init__(self, d, pkg_lib):
        """Initialization of the ProcessLibrary class.

        :param d: dictionary: dictionary corresponding to the tree
        :param pkg_lib: an instance of the PackageLibraryDialog class

        """

        super(ProcessLibrary, self).__init__()
        self.load_dictionary(d)
        self.pkg_library = pkg_lib

    def keyPressEvent(self, event):
        """Event when the delete key is pressed."""
        config = Config()

        if event.key() == QtCore.Qt.Key_Delete and not config.get_user_mode():
            for idx in self.selectedIndexes():
                if idx.isValid():
                    idx = idx.sibling(idx.row(), 0)
                    node = idx.internalPointer()

                    if node is not None:
                        txt = node.data(idx.column())
                        (self.pkg_library.package_library.package_tree) = (
                            self.pkg_library.load_config
                        )()["Packages"]
                        self.pkg_library.delete_package(
                            to_delete=txt, from_pipeline_manager=True
                        )

    def load_dictionary(self, d):
        """Load a dictionary to the tree.

        :param d: dictionary to load. See the packages attribute in the
                  ProcessLibraryWidget class

        """

        self.dictionary = d
        self._nodes = node_structure_from_dict(d)
        self._model = DictionaryTreeModel(self._nodes)
        self.setModel(self._model)
        # there are too many processes in nipype interfaces, opening
        # all is untractable.
        # self.expandAll()

    def mousePressEvent(self, event):
        """Event when the mouse is pressed."""

        idx = self.indexAt(event.pos())
        # print('idx',dir(idx.model()))
        config = Config()

        if idx.isValid:
            idx = idx.sibling(idx.row(), 0)
            node = idx.internalPointer()

            if node is not None:
                self.setCurrentIndex(idx)
                txt = node.data(idx.column())
                path = txt.encode()
                self.item_library_clicked.emit(path.decode("utf8"))

                if event.button() == Qt.RightButton:
                    self.menu = QMenu(self)
                    self.remove = self.menu.addAction("Remove package")

                    if config.get_user_mode() is False:
                        self.action_delete = self.menu.addAction(
                            "Delete package"
                        )

                    else:
                        self.action_delete = False

                    action = self.menu.exec_(self.mapToGlobal(event.pos()))

                    if action == self.remove:
                        (self.pkg_library.package_library.package_tree) = (
                            self.pkg_library.load_config()["Packages"]
                        )
                        self.pkg_library.remove_package(txt)
                        self.pkg_library.save()

                    if action == self.action_delete:
                        (self.pkg_library.package_library.package_tree) = (
                            self.pkg_library.load_config()["Packages"]
                        )
                        self.pkg_library.delete_package(
                            to_delete=txt, from_pipeline_manager=True
                        )
                # print('dictionary ',path.decode('utf8'))
                # self.item_library_clicked.emit(model.itemData(idx)[0])

        return QTreeView.mousePressEvent(self, event)

    def to_dict(self):
        """Return a dictionary from the current tree.

        :return: the dictionary of the tree

        """

        return self._model.to_dict()


class ProcessLibraryWidget(QWidget):
    """
    Widget that handles the available Capsul's processes in the software.

    :param main_window: current main window

    .. Methods:
        - load_config: read the config in process_config.yml and return it as
        a dictionary
        - load_packages: sets packages and paths to the widget and to the
        system paths
        - open_pkg_lib: opens the package library
        - save_config: saves the current config to process_config.yml
        - update_config: updates the config and loads the corresponding
        packages
        - update_process_library: updates the tree of the process library

    """

    def __init__(self, main_window=None):
        """Initialize the ProcessLibraryWidget.

        :param main_window: current main window

        """

        super(ProcessLibraryWidget, self).__init__(parent=main_window)
        self.setWindowTitle("Process Library")
        self.main_window = main_window

        # Process Config
        self.update_config()

        # Package Library
        self.pkg_library = PackageLibraryDialog(
            mia_main_window=self.main_window, parent=self.main_window
        )
        self.pkg_library.signal_save.connect(self.update_process_library)

        # Process Library
        self.process_library = ProcessLibrary(self.packages, self.pkg_library)
        self.process_library.setDragDropMode(self.process_library.DragOnly)
        self.process_library.setAcceptDrops(False)
        self.process_library.setDragEnabled(True)
        self.process_library.setSelectionMode(
            self.process_library.SingleSelection
        )
        # we can't leave all trees open because nipype contains far too many
        # processes
        self.process_library.collapseAll()
        self.process_library.expandToDepth(1)

        # # Push button to call the package library
        # push_button_pkg_lib = QPushButton()
        # push_button_pkg_lib.setText('Package library manager')
        # push_button_pkg_lib.clicked.connect(self.open_pkg_lib)

        # Test to see the inputs/outputs of a process
        self.label_test = QLabel()

        # Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.label_test)
        self.splitter.addWidget(self.process_library)

        # Layout
        h_box = QVBoxLayout()
        # h_box.addWidget(push_button_pkg_lib)
        h_box.addWidget(self.splitter)

        self.setLayout(h_box)

    @staticmethod
    def load_config():
        """Read the config in process_config.yml and return it as a dictionary.

        :return: the config as a dictionary

        """
        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        config = Config()

        if not os.path.exists(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            )
        ):
            open(
                os.path.join(
                    config.get_properties_path(),
                    "properties",
                    "process_config.yml",
                ),
                "a",
            ).close()

        with open(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            ),
            "r",
        ) as stream:
            try:
                if verCmp(yaml.__version__, "5.1", "sup"):
                    return yaml.load(stream, Loader=yaml.FullLoader)
                else:
                    return yaml.load(stream)

            except yaml.YAMLError as exc:
                print(exc)

    def load_packages(self):
        """Set packages and paths to the widget and to the system paths."""

        try:
            self.packages = self.process_config["Packages"]
        except KeyError:
            self.packages = {}
        except TypeError:
            self.packages = {}

        try:
            self.paths = self.process_config["Paths"]
        except KeyError:
            self.paths = []
        except TypeError:
            self.paths = []

        for path in self.paths:
            # Adding the module path to the system path
            # sys.path.insert(0, os.path.abspath(path))
            if path not in sys.path:
                sys.path.append(path)

    def open_pkg_lib(self):
        """Open the package library."""

        self.pkg_library.show()

    def save_config(self):
        """Save the current config to process_config.yml."""

        config = Config()

        self.process_config["Packages"] = self.packages
        self.process_config["Paths"] = self.paths

        with open(
            os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            ),
            "w",
            encoding="utf8",
        ) as stream:
            yaml.dump(
                self.process_config,
                stream,
                default_flow_style=False,
                allow_unicode=True,
            )

    def update_config(self):
        """Update the config and loads the corresponding packages."""

        self.process_config = self.load_config()
        self.load_packages()

    def update_process_library(self):
        """Update the tree of the process library."""

        self.update_config()
        self.process_library.package_tree = self.packages
        self.process_library.load_dictionary(self.packages)


def import_file(full_name, path):
    """Import a python module from a path (3.4+ only).

    Does not call sys.modules[full_name] = path

    :param full_name: name of the package
    :param path: path of the package
    :return: the corresponding module

    """

    from importlib import util

    spec = util.spec_from_file_location(full_name, path)
    mod = util.module_from_spec(spec)

    spec.loader.exec_module(mod)
    return mod


def node_structure_from_dict(datadict, parent=None, root_node=None):
    """Return a hierarchical node stucture required by the TreeModel.

    :param datadict: dictionary
    :param parent: Parent of the node
    :param root_node: Root of the node

    """

    if not parent:
        root_node = Node("Root")
        parent = root_node

    for name, data in sorted(datadict.items()):
        if isinstance(data, dict):
            if True in [
                True for value in data.values() if value == "process_enabled"
            ]:
                list_name = [
                    value
                    for value in data.values()
                    if value == "process_enabled"
                ]

            else:
                list_name = []
                list_values = [
                    value for value in data.values() if isinstance(value, dict)
                ]

                while list_values:
                    value = list_values.pop()

                    for i in value.values():
                        if not isinstance(i, dict):
                            list_name.append(i)

                    list_values = list_values + [
                        i for i in value.values() if isinstance(i, dict)
                    ]

            # if not list_name: list_name = [i for i in data.values()]

            if all(item == "process_disabled" for item in list_name):
                continue

            node = Node(name, parent)
            node = node_structure_from_dict(data, node, root_node)

        elif data == "process_enabled":
            node = Node(name, parent)
            node.value = data

    return root_node


# class FileFilterProxyModel(QSortFilterProxyModel):
#     """Just a test for the moment. Should be useful to use in
#        the file dialog.
#
#     .. Methods:
#         - filterAcceptsRow:
#
#     """
#
#     def __init__(self):
#         """Initialization of the FileFilterProxyModel class."""
#         super(FileFilterProxyModel, self).__init__()
#
#     def filterAcceptsRow(self, source_row, source_parent):
#         """
#
#         :param source_row:
#         :param source_parent:
#         :return: boolean
#         """
#         source_model = self.sourceModel()
#         index0 = source_model.index(source_row, 0, source_parent)
#         # Always show directories
#         if source_model.isDir(index0):
#             return True
#         # filter files
#         filename = source_model.fileName(index0)
#         # filename=self.sourceModel().index(row,0,parent).data().lower()
#         # return True
#         if filename.count(".py") + filename.count(".xml") == 0:
#             return False
#         else:
#             return True
#
#     def flags(self, index):
#         flags = super(FileFilterProxyModel, self).flags(index)
#         source_model = self.sourceModel()
#         if source_model.isDir(index):
#             flags |= Qt.ItemIsSelectable
#             return flags
#
#         # filter files
#         filename = source_model.fileName(index)
#
#         if filename.count(".py") + filename.count(".xml") == 0:
#             flags &= ~Qt.ItemIsSelectable
#             return flags
#         else:
#             flags |= Qt.ItemIsSelectable
#             return flags

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("using Qt backend:", qt_backend.get_qt_backend())
    plw = ProcessLibraryWidget()
    plw.show()
    sys.exit(app.exec_())
