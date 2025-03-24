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
import glob
import inspect
import logging
import os
import pkgutil
import shutil
import sys
import tempfile
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

logger = logging.getLogger(__name__)


class DictionaryTreeModel(QAbstractItemModel):
    """
    Data model providing a tree structure for an arbitrary dictionary.

    This model is designed to represent a dictionary as a tree structure,
    enabling interaction with the data through a tree view.

    .. Methods:
        - columnCount: Return always 1.
        - data: Return the data requested by the view.
        - flags: Everything is enabled and selectable, only the leaves can be
                 dragged.
        - getNode: Return a Node() from given index.
        - headerData: Return the name of the requested column.
        - index: Return an index from given row, column and parent.
        - insertRows: Insert rows from starting position and number given by
                      rows.
        - mimeData: Used when the widget is dragged by the user.
        - mimeTypes: Return a constant.
        - parent: return the parent from given index.
        - removeRows: Remove the rows from position to position+rows.
        - rowCount: The number of rows is the number of children.
        - setData: Method called when the user changes data.
        - to_dict: return the root node as a dictionary.
    """

    def __init__(self, root, parent=None):
        """
        Initializes the DictionaryTreeModel with a root node.

        :param root: The root node of the tree.
        "param parent (QObject): The parent object.
        """
        super().__init__(parent)
        self._rootNode = root

    def columnCount(self, parent=None):
        """
        Returns the number of columns, which is always 1.

        :param parent (QModelIndex): The parent index (unused in this
                                     implementation).
        :return (int): The number of columns.
        """
        return 1

    def data(self, index, role):
        """
        Returns the data stored under the given role for the item at the
        given index.

        :param index (QModelIndex): The index of the item.
        :param role (Qt.ItemDataRole): The role of the data to retrieve.
        :return: The data stored under the given role, or None if not
                 available.
        """

        if not index.isValid():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            node = index.internalPointer()
            return node.name

        return None

    def flags(self, index):
        """
        Get the item flags for the specified index.

        :param index (QModelIndex): The model index to retrieve flags for.

        :return (Qt.ItemFlags): The corresponding item flags.
        """
        node = index.internalPointer()
        base_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if node.childCount() == 0:
            base_flags |= Qt.ItemIsDragEnabled

        return base_flags

    def getNode(self, index):
        """
        Retrieves the Node object from the given index.

        :param index (QModelIndex): The index of the node.
        :return: The Node object.
        """
        node = index.internalPointer() if index.isValid() else None
        return node if node else self._rootNode

    def headerData(self, section, orientation, role):
        """
        Returns the data for the given role and section in the header.

        :param section (int): The section number.
        :param orientation (Qt.Orientation): The orientation of the header
                                             (unused in this implementation).
        :param role (Qt.ItemDataRole): The role of the data to retrieve.

        :return (str): The header data, or None if not available.
        """

        if role == Qt.DisplayRole:

            if section == 0:
                return "Packages"

            if section == 1:
                return "Value"

        return None

    def index(self, row, column, parent):
        """
        Creates an index for the given row, column, and parent.

        :param row (int): The row number.
        :param column (int): The column number.
        :param parent (QModelIndex): The parent index.

        :return (QModelIndex): The created index, or an invalid index if
                               not available.
        """
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        return (
            self.createIndex(row, column, childItem)
            if childItem
            else QModelIndex()
        )

    def insertRows(self, position, rows, parent=QModelIndex()):
        """
        Inserts rows starting from the specified position.

        :param position (int): The starting position to insert rows.
        :param rows (int): The number of rows to insert.
        :param parent (QModelIndex): The parent index.
        :return (bool): True if the rows were successfully inserted,
                        False otherwise.
        """
        parentNode = self.getNode(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        all_inserted = True  # Track overall success

        for row in range(rows):
            childCount = parentNode.childCount()
            childNode = Node(f"untitled{childCount}")

            if not parentNode.insertChild(position, childNode):
                all_inserted = False  # Mark as failed if any insertion fails

        self.endInsertRows()
        return all_inserted  # Return final status

    def mimeData(self, indexes):
        """
        Generate MIME data for a drag-and-drop operation.

        :param indexes (list of QModelIndex): The list of model indexes being
                                              dragged.
        :return (QMimeData): A QMimeData object containing serialized node
                             information.
        """
        mimedata = QMimeData()
        encoded_data = QByteArray()

        for index in indexes:

            if index.isValid():
                node = index.internalPointer()
                text = node.data(index.column())
                encoded_data.append(text.encode())  # Accumulate all text data

        mimedata.setData("component/name", encoded_data)
        return mimedata

    def mimeTypes(self):
        """
        Returns the supported MIME types.

        :return (list of str): A list of supported MIME types.
        """
        return ["component/name"]

    def parent(self, index):
        """
        Returns the parent index for the given index.

        :param index (QModelIndex): The index of the item.
        :return (QModelIndex): The parent index, or an invalid index if not
                               available.
        """
        node = self.getNode(index)
        parentNode = node.parent()

        if parentNode == self._rootNode:
            return QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    def removeRows(self, position, rows, parent=QModelIndex()):
        """
        Removes rows starting from the specified position to position+rows.

        :param position (int): The starting position to remove rows.
        :param rows (int): The number of rows to remove.
        :param parent (QModelIndex): The parent index.
        :return (bool): True if all rows were successfully removed,
                        False otherwise.
        """
        parentNode = self.getNode(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)
        all_removed = True  # Track overall success

        for _ in range(rows):

            if not parentNode.removeChild(position):
                all_removed = False  # Mark as failed if any removal fails

        self.endRemoveRows()
        return all_removed  # Return final status

    def rowCount(self, parent):
        """
        Returns the number of rows, which corresponds to the number of
        children.

        :param parent (QModelIndex): The parent index.
        :return (int): The number of rows.
        """
        parentNode = (
            self.getNode(parent) if parent.isValid() else self._rootNode
        )
        return parentNode.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        """
        Updates the data when the user makes changes.

        :param index (QModelIndex): The index of the item.
        :param value: The new value to set.
        :param role (Qt.ItemDataRole): The role of the data to set.
        :return (bool): True if the data was successfully set, False otherwise.
        """

        if index.isValid() and role == Qt.EditRole:
            node = index.internalPointer()
            node.setData(index.column(), value)
            return True

        return False

    def to_dict(self):
        """
        Converts the root node to a dictionary.

        :return (dict): The dictionary representation of the root node.
        """
        return self._rootNode.to_dict()


class InstallProcesses(QDialog):
    """
    Dialog for installing Python packages from a folder or zip file.

    This widget allows users to browse and select a Python package or zip file
    containing packages, then install them into Populse_MIA.

    .. Methods:
        - _add_package: Add a package and its modules to the process tree.
        - _change_pattern_in_folder: Replace pattern in all Python files
                                     within a folder.
        - _install_new_package: Install a new package.
        - _load_process_config: Load the process configuration from YAML.
        - _rollback_changes: Roll back changes in case of installation failure.
        - _show_qmessagebox: Display an error message box.
        - _show_status_message: Update status message in the main window.
        - _update_existing_package: Update an existing package.
        - _validate_input: Validate the input file or directory.
        - get_filename: Opens a file dialog to get the folder or zip file to
                        install.
        - install: Installs the selected file/folder on Populse_mia.

    .. Signals:
        - process_installed: Emitted when a process is successfully installed
    """

    process_installed = Signal()

    def __init__(self, main_window, folder):
        """
        Initialize the installation dialog.

        :param main_window: The main application window
        :param folder (bool): If True, install from folder; if False, install
                              from zip file

        """
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.setWindowTitle("Install processes")
        # Set up layout
        v_layout = QVBoxLayout()
        self.setLayout(v_layout)
        # Choose appropriate label text based on installation type
        label_text = (
            "Choose folder containing Python packages"
            if folder
            else "Choose zip file containing Python packages"
        )
        v_layout.addWidget(QLabel(label_text))
        # File selection section
        edit_layout = QHBoxLayout()
        v_layout.addLayout(edit_layout)
        self.path_edit = QLineEdit()
        edit_layout.addWidget(self.path_edit)
        self.browser_button = QPushButton("Browse")
        edit_layout.addWidget(self.browser_button)
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        v_layout.addLayout(bottom_layout)
        install_button = QPushButton("Install package")
        bottom_layout.addWidget(install_button)
        quit_button = QPushButton("Quit")
        bottom_layout.addWidget(quit_button)
        # Connect signals
        install_button.clicked.connect(self.install)
        quit_button.clicked.connect(self.close)
        self.browser_button.clicked.connect(
            lambda: self.get_filename(folder=folder)
        )

    def _add_package(self, proc_dic, module_name):
        """
        Add a package and its modules to the process tree.

        :param proc_dic (dict): The process tree dictionary to update.
        :param module_name (str): Name of the module to add.

        :return (dict): The updated process tree dictionary.
        """

        if not module_name:
            return proc_dic

        # Reload the package if already loaded
        if module_name in sys.modules:
            del sys.modules[module_name]

        try:
            __import__(module_name)

        except ImportError as err:
            self._show_qmessagebox(
                f"During the installation of {module_name}, "
                f"the following exception was raised:"
                f"\n{err.__class__}: {err}.\n"
                f"This exception may have prevented the installation."
            )

            self.result_add_package = False
            raise ImportError(
                f"The {module_name} brick may not have been installed."
            )

        pkg = sys.modules[module_name]

        # Check for subpackages
        for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__):

            if ispkg:
                self._add_package(proc_dic, f"{module_name}.{modname}")

        # Process each class in the package
        for k, v in sorted(list(pkg.__dict__.items())):

            if not inspect.isclass(v):
                continue

            try:
                logger.info(f"Installing {module_name}.{v.__name__}...")
                get_process_instance(f"{module_name}.{v.__name__}")
                # Update the tree dictionary
                path_list = module_name.split(".")
                path_list.append(k)
                pkg_iter = proc_dic

                for i, element in enumerate(path_list):

                    if element in pkg_iter:
                        pkg_iter = pkg_iter[element]

                    else:

                        if i == len(path_list) - 1:
                            pkg_iter[element] = "process_enabled"

                        else:
                            pkg_iter[element] = {}
                            pkg_iter = pkg_iter[element]

            except Exception:
                logger.warning(
                    f"Error during installation of "
                    f"the '{module_name}' module ...!",
                    exc_info=True,
                )
                self.result_add_package = False

        return proc_dic

    def _change_pattern_in_folder(self, path, old_pattern, new_pattern):
        """
        Replace pattern in all Python files within a folder.

        :param path (str): Directory path to process.
        :param old_pattern (str): Pattern to search for.
        :param new_pattern (str): Pattern to replace with.
        """

        for root, _, files in os.walk(path):

            for fname in files:

                if not fname.endswith(".py"):
                    continue

                # Modifying only .py files (pipelines are saved with
                # this extension)
                fpath = os.path.join(root, fname)

                with open(fpath) as f:
                    content = f.read()

                # Replace the pattern
                updated_content = content.replace(
                    f"{old_pattern}.", f"{new_pattern}."
                )

                with open(fpath, "w") as f:
                    f.write(updated_content)

    def _install_new_package(self, filename, package_name, processes_path):
        """
        Install a new package.

        :param filename (str): Path to zip file or directory.
        :param package_name (str): Name of the package to install.
        :param processes_path (str): Target directory for installation.
        """

        if is_zipfile(filename):

            with ZipFile(filename, "r") as zip_ref:
                members_to_extract = [
                    member
                    for member in zip_ref.namelist()
                    if member.startswith(package_name)
                ]
                zip_ref.extractall(processes_path, members_to_extract)

        elif os.path.isdir(filename):
            shutil.copytree(
                filename, os.path.join(processes_path, package_name)
            )

    def _load_process_config(self, config_path):
        """
        Load the process configuration from YAML.

        :param config_path (str): Path to the configuration file.

        :return (dict): The loaded configuration or empty dict if error.
        """

        try:

            with open(config_path) as stream:
                # Import here to prevent circular import
                from populse_mia.utils import verCmp

                if verCmp(yaml.__version__, "5.1", "sup"):
                    process_dic = yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    process_dic = yaml.load(stream)

            return process_dic or {}

        except yaml.YAMLError as exc:
            logger.warning(f"Error loading process config: {exc}")
            return {}

    def _rollback_changes(
        self,
        config_path,
        original_config,
        processes_path,
        package_names,
        mia_processes_not_found,
        tmp_folder4MIA,
    ):
        """
        Roll back changes in case of installation failure.

        Parameters
        ----------
        :param config_path (str): Path to configuration file.
        :param original_config (dict): Original configuration to restore.
        :param processes_path (str): Path to processes directory.
        :param package_names (list): Names of packages that were being
                                     installed.
        :param mia_processes_not_found (bool): Flag indicating if
                                               Mia processes backup was made.
        :param tmp_folder4MIA (str): Path to Mia processes backup.
        """
        if original_config is None:
            original_config = {}

        # Restore original configuration
        with open(config_path, "w", encoding="utf8") as stream:
            yaml.dump(
                original_config,
                stream,
                default_flow_style=False,
                allow_unicode=True,
            )

        # Remove extracted packages
        for package_name in package_names or []:
            package_path = os.path.join(processes_path, package_name)

            if os.path.exists(package_path):
                shutil.rmtree(package_path)

        # Restore Mia processes if needed
        if not mia_processes_not_found and tmp_folder4MIA:
            shutil.copytree(
                os.path.join(tmp_folder4MIA, "mia_processes"),
                os.path.join(processes_path, "mia_processes"),
                dirs_exist_ok=True,
            )

    def _show_qmessagebox(self, message, critical=True):
        """
        Display an error message box.

        :param message (str): Message to display
        :param critical (bool): If True, display a critical message box.
        """
        msg = QMessageBox()

        if critical:
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Warning")

        else:
            msg.setWindowTitle("Installation completed")

        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(msg.close)
        msg.exec()

    def _show_status_message(self, message):
        """
        Update status message in the main window.

        :param message (str): Status message to display
        """

        try:
            self.main_window.statusBar().showMessage(message)
            QApplication.processEvents()

        except AttributeError:
            self.main_window.status_label.setText(message)

    def _update_existing_package(self, filename, package_name, processes_path):
        """
        Update an existing package.

        :param filename (str): Path to zip file or directory.
        :param package_name (str): Name of the package to update.
        :param processes_path (str): Target directory for installation.

        :return (str): The new package name (with timestamp).
        """
        # Create timestamped name for the new version
        date = datetime.now().strftime("%Y%m%d%H%M%S")
        new_package_name = f"{package_name}_{date}"

        if is_zipfile(filename):

            with tempfile.TemporaryDirectory() as tmp_dir:

                with ZipFile(filename, "r") as zip_ref:
                    members_to_extract = [
                        member
                        for member in zip_ref.namelist()
                        if member.startswith(package_name)
                    ]
                    zip_ref.extractall(tmp_dir, members_to_extract)
                    shutil.move(
                        os.path.join(tmp_dir, package_name),
                        os.path.join(processes_path, new_package_name),
                    )

        elif os.path.isdir(filename):
            shutil.copytree(
                filename, os.path.join(processes_path, new_package_name)
            )

        # Replace package name references in files
        self._change_pattern_in_folder(
            os.path.join(processes_path, new_package_name),
            package_name,
            new_package_name,
        )

        return new_package_name

    def _validate_input(self, filename):
        """
        Validate the input file or directory.

        :param filename (str): Path to the file or directory.

        :return (bool): True if valid, False otherwise
        """

        if not os.path.exists(filename):
            self._show_qmessagebox(
                "The specified file or directory cannot be found"
            )
            return False

        if not os.path.isdir(filename) and not filename.endswith(".zip"):
            self._show_qmessagebox("The specified file has to be a .zip file")
            return False

        return True

    def get_filename(self, folder):
        """
        Open a file dialog to select the package source.

        :param folder (bool): If True, opens a directory selection dialog;
                              If False, opens a zip file selection dialog
        """

        if folder:
            filename = QFileDialog.getExistingDirectory(
                self,
                caption="Select a directory",
                directory=os.path.expanduser("~"),
                options=QFileDialog.ShowDirsOnly,
            )

        else:
            filename = QFileDialog.getOpenFileName(
                caption="Select a zip file",
                directory=os.path.expanduser("~"),
                filter="Compatible files (*.zip)",
            )

        if not filename:
            return

        if isinstance(filename, str):
            self.path_edit.setText(filename)

        elif isinstance(filename, tuple):
            self.path_edit.setText(filename[0])

    def install(self):
        """
        Install a package from a zip file or a folder.

        This method handles the complete installation process:
        1. Extracts or copies the package to the processes directory
        2. Updates the process dictionary
        3. Registers the new package in the configuration

        Any exceptions during installation are caught and reported to the
        user, with automatic rollback of any changes made.
        """
        tmp_folder4MIA = None

        try:
            self._show_status_message("Package installation, please wait...")
            self.result_add_package = True
            filename = self.path_edit.text()
            config = Config()

            # Validate input file/folder
            if not self._validate_input(filename):
                return

            # Setup paths
            processes_path = os.path.join(
                config.get_properties_path(), "processes"
            )
            config_file_path = os.path.join(
                config.get_properties_path(),
                "properties",
                "process_config.yml",
            )

            # Ensure process path is in sys.path
            if processes_path not in sys.path:
                sys.path.append(processes_path)

            # Create process config file if it doesn't exist
            if not os.path.isfile(config_file_path):
                open(config_file_path, "a").close()

            # Load current process configuration
            process_dic = self._load_process_config(config_file_path)
            # Copy the original process tree for rollback if needed
            process_dic_orig = copy(process_dic)
            # Extract package information
            packages = process_dic.get("Packages", {}) or {}
            paths = process_dic.get("Paths", []) or []
            # Get existing packages
            # packages_already: packages already installed in populse_
            # mia (populse_mia/processes)
            packages_already = [
                d
                for d in os.listdir(processes_path)
                if os.path.isdir(os.path.join(processes_path, d))
            ]
            # Handle Mia processes special case
            package_names = []
            mia_processes_not_found = True

            # Get packages names from zip or directory
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
                # Careful: If filename is not a zip file, filename must be a
                # directory that contains only the package(s) to install !!!
                packages_name = [os.path.basename(filename)]

            # Process each package
            for package_name in packages_name:

                # Handle mia_processes backup
                if mia_processes_not_found and package_name == "mia_processes":
                    mia_path = os.path.join(processes_path, "mia_processes")

                    if os.path.exists(mia_path):
                        mia_processes_not_found = False
                        tmp_folder4MIA = tempfile.mkdtemp()
                        shutil.copytree(
                            mia_path,
                            os.path.join(tmp_folder4MIA, "mia_processes"),
                        )

                # Install or update package
                if (
                    package_name not in packages_already
                    or package_name == "mia_processes"
                ):
                    # Fresh install
                    self._install_new_package(
                        filename, package_name, processes_path
                    )

                else:
                    # Update existing package
                    package_name = self._update_existing_package(
                        filename, package_name, processes_path
                    )

                package_names.append(package_name)
                # package_names contains all the extracted packages
                final_package_dic = self._add_package(packages, package_name)

            # Ensure processes path is in config
            if processes_path not in paths:
                paths.append(processes_path)

            # Update and save configuration
            process_dic["Packages"] = final_package_dic
            process_dic["Paths"] = paths
            # FIXME: Should we encrypt the path ?

            with open(config_file_path, "w", encoding="utf8") as stream:
                yaml.dump(
                    process_dic,
                    stream,
                    default_flow_style=False,
                    allow_unicode=True,
                )

            # Signal successful installation
            self.process_installed.emit()

        except Exception:
            # Handle installation failure
            logger.warning(
                f"Error during installation of "
                f"the '{package_name}' library...!",
                exc_info=True,
            )
            self.result_add_package = False
            self._show_status_message(
                f"Installation of the '{package_name}' library aborted!"
            )
            self._show_qmessagebox(
                f"Installation of the '{package_name}' library aborted!\n"
                "Please see the standard output for more details."
            )
            self.close()
            # Restore original configuration
            self._rollback_changes(
                config_file_path,
                process_dic_orig,
                processes_path,
                package_names,
                mia_processes_not_found,
                tmp_folder4MIA,
            )

        else:

            if self.result_add_package:
                message = (
                    f"The '{package_name}' library has been correctly "
                    f"installed."
                )
                self._show_status_message(message)
                self._show_qmessagebox(message, critical=False)
                self.close()

            else:
                message = (
                    f"The '{package_name}' library has not been "
                    f"correctly installed."
                )
                self._show_status_message(message)
                self._show_qmessagebox(message)
                self.close()

        finally:

            # Cleanup temporary directories
            if tmp_folder4MIA and os.path.isdir(tmp_folder4MIA):
                shutil.rmtree(tmp_folder4MIA)


class Node:
    """
    A tree-like structure to manage hierarchical data with parent-child
    relationships.

    This class provides functionality to create and manipulate tree nodes,
    where each node can have a name, value, parent, and multiple children.

    .. Methods:
        -  __repr__: Define what should be printed by the class.
        - _recurse_dict: Recursively build a dictionary representation of the
                         node hierarchy.
        - addChild: Add a child to the children list.
        - attrs: Get attributes of this node as a dictionary.
        - child: Return a child from its index in the list.
        - childCount: return the number of children.
        - data: Return the name or the value of the object.
        - insertChild: Insert a child to a specific position.
        - log: Generate a formatted string representation of the node
               hierarchy.
        - name: Gets or sets the name of the node.
        - parent: Return the parent of the node.
        - removeChild:  Remove a child node at the specified position.
        - resource: Placeholder that always returns None.
        - row: Return the index of the object in its parent list of children.
        - setData: Update the name or the value of the object.
        - to_dict: Convert the node hierarchy to a dictionary.
        - to_list: Convert the node hierarchy to a list.
        - value: Gets or sets the value of the node.
    """

    def __init__(self, name, parent=None):
        """
        Initialize a new Node instance.

        :param name (str): The name of the node.
        :param parent: The parent node. If provided, this node is
                       automatically added as a child to the parent.
                       Defaults to None.
        """

        if parent is not None:
            parent.addChild(self)

        self._name = name
        self._parent = parent
        self._children = []
        self._value = None

    def __repr__(self):
        """
        Return a string representation of the node hierarchy.

        :return (str): A formatted string showing the node hierarchy.
        """
        return self.log()

    def _recurse_dict(self, d):
        """
        Recursively build a dictionary representation of the node hierarchy.

        :param d (dict): The dictionary to populate with the node hierarchy.
        """
        d[self.name] = {} if self._children else self.value

        for child in self._children:
            child._recurse_dict(d[self.name])

    def addChild(self, child):
        """
        Add a child node to this node.

        :param child: The child node to add.
        """
        self._children.append(child)

    def attrs(self):
        """
        Get attributes of this node as a dictionary.

        :return (dict): A dictionary of property names and their values.
        """
        classes = self.__class__.__mro__
        keyvalued = {}

        for cls in classes:

            for key, value in cls.items():

                if isinstance(value, property):
                    keyvalued[key] = value.fget(self)

        return keyvalued

    def child(self, row):
        """
        Get a child node by its index.

        :param row (int): The index of the child node in the children list.

        :return: The child node at the specified index.
        """
        return self._children[row]

    def childCount(self):
        """
        Get the number of children of this node.

        :return (int): The number of child nodes.
        """
        return len(self._children)

    def data(self, column):
        """
        Get data about this node based on the column parameter.

        :param column (int): 0 for the fully qualified name (including parent
                             names), 1 for the value of this node.
        :return (str): The requested data (either string path or node value).
        """

        if column == 0:
            parent = self._parent
            text = self.name

            while parent and parent.name != "Root":
                text = f"{parent.name}.{text}"
                parent = parent._parent

            # self.name
            return text

        elif column == 1:
            return self.value

    def insertChild(self, position, child):
        """
        Insert a child node at a specific position.

        :param position (int): The position at which to insert the child.
        :param child: The child node to insert.

        :return (bool): True if insertion was successful, False otherwise.
        """

        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self
        return True

    def log(self, tabLevel=-1):
        """
        Generate a formatted string representation of the node hierarchy.

        :param tabLevel (int): The current indentation level. Defaults to -1.

        :retur (str): A formatted string showing the node hierarchy.
        """
        tabLevel += 1
        indent = "    " * tabLevel
        output = f"{indent}|----{self._name} = \n"

        for child in self._children:
            output += child.log(tabLevel)

        return f"{output}\n"

    @property
    def name(self):
        """
        Get the name of this node.

        :return (str): The name of the node.
        """
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of this node.

        :param value (str): The new name for the node.
        """
        self._name = value

    def parent(self):
        """Get the parent of this node.

        :return: The parent node or None if this is a root node.

        """
        return self._parent

    def removeChild(self, position, child):
        """
        Remove a child node at the specified position.

        :param position (int): The position of the child to remove.
        :param child: The child node to remove.

        :return (bool): True if removal was successful, False otherwise.
        """

        if position < 0 or position > len(self._children):
            return False

        self._children.pop(position)
        child._parent = None
        return True

    def resource(self):
        """
        Get resource information for this node.

        This method is a placeholder that always returns None.

        :return: None
        """
        return None

    def row(self):
        """Get the index of this node in its parent's children list.

        :return (int): The index of this node in its parent's children list,
                       or None if this node has no parent.
        """

        if self._parent is not None:
            return self._parent._children.index(self)

        return None

    def setData(self, column, value):
        """
        Set the name or value of this node based on the column parameter.

        :param column (int): 0 to set the name, 1 to set the value.
        :param value: The new name or value to set.
        """

        if column == 0:
            self.name = value

        if column == 1:
            self.value = value

    def to_dict(self, d=None):
        """
        Convert the node hierarchy to a dictionary.

        :param d (dict): A dictionary to populate. Defaults to empty dict.

        :return (dict): A dictionary representation of the node hierarchy.
        """

        if d is None:
            d = {}

        for child in self._children:
            child._recurse_dict(d)

        return d

    def to_list(self):
        """
        Convert the node hierarchy to a list.

        :return (list): A list representation of the node hierarchy.
        """
        output = []

        if self._children:

            for child in self._children:
                output += [self.name, child.to_list()]

        else:
            output += [self.name, self.value]

        return output

    @property
    def value(self):
        """
        Get the value of this node.

        :return: The value of the node.
        """
        return self._value

    @value.setter
    def value(self, value):
        """Set the value of this node.

        :param value: The new value for the node.
        """
        self._value = value


class PackageLibrary(QTreeWidget):
    """
    A tree widget that displays user-added packages and their modules.

    This widget allows users to enable or disable packages and modules by
    checking or unchecking them in the tree view. The tree structure
    reflects the hierarchical organization of packages and their modules.

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
        """
        Initialize the PackageLibrary widget.

        :param package_tree (dict): Hierarchical representation of packages.
        :param paths (list): System paths for importing the packages.
        """
        super().__init__()
        self.itemChanged.connect(self.update_checks)
        self.package_tree = package_tree
        self.paths = paths
        self.generate_tree()
        self.setAlternatingRowColors(True)
        self.setHeaderLabel("Packages")

    def fill_item(self, item, value):
        """
        Recursively populate the tree items.

        Traverses the package tree and creates corresponding QTreeWidgetItems
        with appropriate check states.

        :param item (QTreeWidgetItem): Current tree item to populate.
        :param value (dict, list, or str): Value to populate the item with.

        """
        item.setExpanded(True)

        if isinstance(value, dict):

            for key, val in sorted(value.items()):
                child = QTreeWidgetItem()
                child.setText(0, str(key))
                item.addChild(child)

                if isinstance(val, dict):
                    self.fill_item(child, val)

                else:

                    if val == "process_enabled":
                        child.setCheckState(0, Qt.Checked)
                        self.recursive_checks_from_child(child)

                    elif val == "process_disabled":
                        child.setCheckState(0, Qt.Unchecked)

        elif isinstance(value, list):

            for val in value:
                child = QTreeWidgetItem()
                item.addChild(child)

                if isinstance(val, dict):
                    child.setText(0, "[dict]")
                    self.fill_item(child, val)

                elif isinstance(val, list):
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
        """
        Generate the package tree structure.

        Clears the current tree and populates it with items from package_tree.
        Temporarily disconnects the itemChanged signal to prevent unwanted
        updates.
        """
        self.itemChanged.disconnect()
        self.clear()
        self.fill_item(self.invisibleRootItem(), self.package_tree)
        self.itemChanged.connect(self.update_checks)

    def recursive_checks(self, parent):
        """
        Propagate check state down to all child items.

        When a parent item is checked/unchecked, all its children
        inherit the same check state.

        :param parent (QTreeWidgetItem): Parent item whose check state is
                                         propagated.
        """
        check_state = parent.checkState(0)

        if parent.childCount() == 0:
            self.set_module_view(parent, check_state)

        for i in range(parent.childCount()):
            parent.child(i).setCheckState(0, check_state)
            self.recursive_checks(parent.child(i))

    def recursive_checks_from_child(self, child):
        """
        Propagate check state up to parent items.

        When a child item is checked, its parents are also checked.
        When a child item is unchecked, its parent is unchecked only if
        all siblings are also unchecked.

        :param child (QTreeWidgetItem): Child item whose check state affects
                                        parents.
        """
        check_state = child.checkState(0)

        if child.childCount() == 0:
            self.set_module_view(child, check_state)

        if child.parent():
            parent = child.parent()

            if check_state == Qt.Checked:

                if parent.checkState(0) == Qt.Unchecked:
                    parent.setCheckState(0, Qt.Checked)
                    self.recursive_checks_from_child(parent)
            else:
                # Check if any siblings are still checked
                has_checked_siblings = any(
                    parent.child(i).checkState(0) == Qt.Checked
                    for i in range(parent.childCount())
                )

                if not has_checked_siblings:
                    parent.setCheckState(0, Qt.Unchecked)
                    self.recursive_checks_from_child(parent)

    def set_module_view(self, item, state):
        """
        Update the module's enabled/disabled status in the package tree.

        Updates the underlying package_tree data structure when an item's
        check state changes in the UI.

        :param item (QTreeWidgetItem): Tree item corresponding to a module.
        :param state (Qt.CheckState): New check state, Qt.Checked or
                                      Qt.Unchecked.
                                      (Qt.Checked == 2. So if
                                      val == 2 -> checkbox is checked, and if
                                      val == 0 -> checkbox is not checked)
        """
        val = "process_enabled" if state == Qt.Checked else "process_disabled"

        # Build path from item to root
        path = []
        current = item

        while current:
            path.insert(0, current.text(0))
            current = current.parent()

        # Update package_tree according to the path
        pkg_iter = self.package_tree

        for element in path[:-1]:  # Navigate to parent of target node

            if element in pkg_iter:
                pkg_iter = pkg_iter[element]

            else:
                logger.info(f"Package '{element}' not found in tree")
                return

        # Update the value of the target node
        if path[-1] in pkg_iter:
            pkg_iter[path[-1]] = val

        else:
            logger.info(f"Module '{path[-1]}' not found in package")

    def update_checks(self, item, column):
        """
        "Handle check state changes and propagate them.

        When an item's check state changes, this method ensures the change
        is properly propagated to children and parent items.

        :param item (QTreeWidgetItem): Item whose check state changed.
        :param column (int): Column index of the change (should be 0).
        """

        # Checked state is stored on column 0
        if column == 0:
            # Temporarily disconnect to prevent signal recursion
            self.itemChanged.disconnect()

            # Propagate changes down to children
            if item.childCount():
                self.recursive_checks(item)

            # Propagate changes up to parents
            if item.parent():
                self.recursive_checks_from_child(item)

            # Reconnect signal
            self.itemChanged.connect(self.update_checks)


class PackageLibraryDialog(QDialog):
    """Dialog that controls which processes to show in the process library.

    .. Methods:
        - add_package: add a package and its modules to the package tree
        - add_package_with_text: add a package from the line edit's text
        - browse_package: open a browser to select a package (commented)
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
        super().__init__(parent)
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
        push_button_del_pkg.clicked.connect(self.delete_package_with_text)
        self.add_dic = {}
        self.remove_dic = {}
        self.delete_dic = {}
        self.add_list = QListWidget()
        self.remove_list = QListWidget()
        self.del_list = QListWidget()
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
                                f"{module_name}.{modname}",
                                class_name,
                                show_error=False,
                            )

                for k, v in sorted(list(pkg.__dict__.items())):

                    # Checking each class of in the package
                    if inspect.isclass(v):

                        try:
                            get_process_instance(f"{module_name}.{v.__name__}")

                        except Exception:
                            logger.warning(
                                f"Error during installation of "
                                f"the '{module_name}' module...!",
                                exc_info=True,
                            )

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
                                            logger.info(
                                                f"Adding {module_name}."
                                                f"{v.__name__}..."
                                            )
                                            pkg_iter[element] = (
                                                "process_enabled"
                                            )

                                        elif element in pkg_iter.keys():
                                            pkg_iter = pkg_iter[element]

                                    else:
                                        pkg_iter[element] = {}
                                        pkg_iter = pkg_iter[element]

                self.package_library.package_tree = self.packages
                self.package_library.generate_tree()
                return err_msg

            except Exception as err:
                err_msg.append(f"in {module_name}: {err.__class__}: {err}.")

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

        if self.is_path:
            # Currently, self.is_path is always False. We would have to use
            # the browse_package method to initialise it to True, and the
            # Browse button allowing we to do this has been removed. It
            # might be interesting to allow a backdoor to pass the absolute
            # path in the field to add a package, to be continued...
            path, package = os.path.split(_2add)
            # Adding the module path to the system path
            sys.path.append(path)
            self.add_package(package)
            self.paths.append(os.path.relpath(path))

        else:
            old_status = self.status_label.text()
            self.status_label.setText(f"Adding {_2add}. Please wait.")
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
                                f"No package, module or class "
                                f"named {_2add}!"
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
                    f"{_2add} added to the Package Library."
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

        module_split = to_delete.split(".")

        if module_split[0] in ["nipype", "mia_processes", "capsul"]:

            if from_pipeline_manager:

                inform_text = (
                    f"This package belongs to {module_split[0]} which "
                    f"is required by populse mia.\n You can still hide it in "
                    f"the package library manager."
                )

            else:
                inform_text = (
                    f"This package belongs to {module_split[0]} which "
                    f"is required by populse_mia.\nTherefore, it has only "
                    f"been hidden (removed)."
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
            msgtext = f"Do you really want to delete the package {to_delete}?"
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            title = "populse_mia - Warning: Delete package"
            reply = msg.question(
                self, title, msgtext, QMessageBox.Yes, QMessageBox.No
            )

        else:
            reply = QMessageBox.Yes

        if reply == QMessageBox.Yes:
            pkg_list = module_split

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
                                    os.path.join(root, "__init__.py")
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
                            f"{path} was deleted "
                            f"({os.path.split(path)[-1]} library)..."
                        )
                        path_split = path.split(os.sep)
                        proc_idx = path_split.index("processes") + 1
                        logger.info(
                            f"Deleting {'.'.join(path_split[proc_idx:])}..."
                        )

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

                        with open(init) as f:
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
                                    imports_string = f"{imports_string}{line}"

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
                            logger.info(
                                f"The {to_delete} brick seems to be corrupted "
                                f"and is not accessible..."
                            )

                        for key in imports_in_init:

                            if pkg_list[index - 1] in imports_in_init[key]:
                                filename = f"{key}.py"
                                delete_all = True

                                if len(imports_in_init[key]) > 1:
                                    module = ".".join(
                                        pkg_list[: index - 1] + [key]
                                    )
                                    msgtext = (
                                        f"The brick (class) "
                                        f"{pkg_list[index - 1]} alone cannot "
                                        f"be deleted because it belongs to "
                                        f"{module} module that contains "
                                        f"following brick(s):"
                                    )
                                    msgtext += "".join(
                                        f"\n  - {brick}"
                                        for brick in imports_in_init[key]
                                    )
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
                                        path_parts = file2del.split(os.sep)
                                        process_index = (
                                            path_parts.index("processes") + 1
                                        )
                                        name = ".".join(
                                            path_parts[process_index:-1]
                                        )

                                        for pkg in imports_in_init[key]:
                                            deleted_packages.append(
                                                ".".join([name, pkg])
                                            )

                                        for pkg in deleted_packages:
                                            logger.info(f"Deleting {pkg}...")

                                        os.remove(file2del)
                                        brick = ", ".join(imports_in_init[key])
                                        (
                                            self.main_window.statusBar
                                        )().showMessage(
                                            f"{file2del} was deleted ("
                                            f"{brick} brick(s))..."
                                        )

                                    if remove:

                                        for pkg in deleted_packages:
                                            self.remove_package_with_text(
                                                pkg, False
                                            )

                                    # Rewrite __init_.py to wipe module
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

                                    # If all packages have been deleted,
                                    # cleaning up empty files
                                    with open(init) as f:
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
            self.status_label.setText(f"Deleting {_2del}. Please wait...")
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

            self.status_label.setText(f"{_2del} deleted from Package Library.")

        else:
            self.status_label.setText(old_status)

    def install_processes_pop_up(self, folder=False):
        """Open the install processes pop-up.

        :param folder: boolean, True if installing from a folder
        """
        self.pop_up_install_processes = InstallProcesses(self, folder=folder)
        self.pop_up_install_processes.show()
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
        ) as stream:
            try:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    return yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    return yaml.load(stream)

            except yaml.YAMLError as exc:
                logger.warning(exc)

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
                        f"Do you really want to delete " f"the '{i}' package?"
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
                        pckg = path_list[: path_list.index(element)]

                        if pckg:
                            logger.info(
                                f"Removing {'.'.join(pckg)}.{element}..."
                            )

                        else:
                            logger.info(f"Removing {element}...")

                elif check_flag is True:
                    pass

                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle(
                        "Warning: Package not found in Package Library"
                    )
                    msg.setText(f"Package {package} not found")
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
            self.status_label.setText(f"Removing {_2rem}. Please wait.")
            QApplication.processEvents()

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

            self.status_label.setText(f"{_2rem} removed from Package Library.")

        else:
            self.status_label.setText(old_status)

    def reset_action(self, itemlist, add):
        """Called to reset a previous add or remove package action.

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

    def update_config(self):
        """Update the process_config and package_library attributes."""
        self.process_config = self.load_config()
        self.load_packages()
        self.package_library.package_tree = self.packages
        self.package_library.paths = self.paths
        self.package_library.generate_tree()


# TODO: It seems that this class is never used, so it may be an old piece of
#       code. We are commenting on it until we delete it completely if there's
#       no problem.
# class ProcessHelp(QWidget):
#     """A widget that displays information about the selected process."""

#     def __init__(self, process):
#         """
#         Initialize the ProcessHelp widget with the selected process.

#         :param process: The selected process for which help information is
#                         displayed.
#         """
#         super().__init__()
#         label = QLabel(process.help(), self)


class ProcessLibrary(QTreeView):
    """
    A tree view to display available Capsul's processes.


    :param d: dictionary corresponding to the tree (dict)

    .. Methods:
        - keyPressEvent: Event when the delete key is pressed.
        - load_dictionary: Loads a dictionary to the tree.
        - mousePressEvent: Event when the mouse is pressed.
        - to_dict: Returns a dictionary from the current tree.

    .. Signals:
        - item_library_clicked: Signal emitted when an item in the library is
                                clicked.
    """

    item_library_clicked = QtCore.pyqtSignal(str)

    def __init__(self, d, pkg_lib):
        """
        Initialize the ProcessLibrary class.

        :param d (dict): Dictionary corresponding to the tree.
        :param pkg_lib: An instance of the PackageLibraryDialog class.
        """
        super().__init__()
        self.load_dictionary(d)
        self.pkg_library = pkg_lib

    def keyPressEvent(self, event):
        """
        Handles key press events, specifically the Delete key.

        If the Delete key is pressed and the user is not in user mode, the
        selected package(s) will be deleted from the package library.

        :param event (QKeyEvent): The key event triggering this handler.
        """
        config = Config()

        if event.key() == QtCore.Qt.Key_Delete and not config.get_user_mode():

            for idx in self.selectedIndexes():

                if idx.isValid():
                    idx = idx.sibling(idx.row(), 0)
                    node = idx.internalPointer()

                    if node:
                        txt = node.data(idx.column())
                        self.pkg_library.package_library.package_tree = (
                            self.pkg_library.load_config()["Packages"]
                        )
                        self.pkg_library.delete_package(
                            to_delete=txt, from_pipeline_manager=True
                        )

    def load_dictionary(self, d):
        """
        Load a dictionary into the tree.

        :param d (dict): Dictionary to load. See the packages attribute in the
                         ProcessLibraryWidget class.
        """
        self.dictionary = d
        self._nodes = node_structure_from_dict(d)
        self._model = DictionaryTreeModel(self._nodes)
        self.setModel(self._model)

    def mousePressEvent(self, event):
        """
        Handles mouse press events on the tree view.

        If a valid item is clicked, it sets the current index and emits a
        signal with the selected item's text. If the right mouse button is
        pressed, a context menu is displayed, allowing the user to remove or
        delete a package.

        :param event (QMouseEvent): The mouse event triggering this handler.
        """

        idx = self.indexAt(event.pos())
        config = Config()

        if idx.isValid:
            idx = idx.sibling(idx.row(), 0)
            node = idx.internalPointer()

            if node:
                self.setCurrentIndex(idx)
                txt = node.data(idx.column())
                path = txt.encode()
                self.item_library_clicked.emit(path.decode("utf8"))

                if event.button() == Qt.RightButton:
                    self.menu = QMenu(self)
                    self.remove = self.menu.addAction("Remove package")
                    self.action_delete = (
                        self.menu.addAction("Delete package")
                        if not config.get_user_mode()
                        else None
                    )
                    action = self.menu.exec_(self.mapToGlobal(event.pos()))

                    if action == self.remove:
                        self.pkg_library.package_library.package_tree = (
                            self.pkg_library.load_config()["Packages"]
                        )
                        self.pkg_library.remove_package(txt)
                        self.pkg_library.save()

                    elif action == self.action_delete:
                        self.pkg_library.package_library.package_tree = (
                            self.pkg_library.load_config()["Packages"]
                        )
                        self.pkg_library.delete_package(
                            to_delete=txt, from_pipeline_manager=True
                        )

        return super().mousePressEvent(event)

    def to_dict(self):
        """
        Return a dictionary representation of the current tree.

        :return: The dictionary of the tree.
        """
        return self._model.to_dict()


class ProcessLibraryWidget(QWidget):
    """
    Widget that manages the available Capsul's processes in the software.

    .. Methods:
        - _configure_process_library: Configure the process library settings.
        - _setup_layout: Setup the layout for the widget.
        - load_config: Read the config in process_config.yml and return it as
                       a dictionary.
        - load_packages: Set packages and paths to the widget and to the
                         system paths.
        - open_pkg_lib: Open the package library.
        - save_config: Save the current config to process_config.yml.
        - update_config: Update the config and loads the corresponding
                         packages.
        - update_process_library: Update the tree of the process library.
    """

    def __init__(self, main_window=None):
        """
        Initialize the ProcessLibraryWidget.

        :param main_window: The current main window.
        """
        super().__init__(parent=main_window)
        self.setWindowTitle("Process Library")
        self.main_window = main_window
        # Load and update configuration
        self.update_config()
        # Initialize package library
        self.pkg_library = PackageLibraryDialog(
            mia_main_window=self.main_window, parent=self.main_window
        )
        self.pkg_library.signal_save.connect(self.update_process_library)
        # Initialize process library
        self.process_library = ProcessLibrary(self.packages, self.pkg_library)
        self._configure_process_library()
        # Test label to see the inputs/outputs of a process
        self.label_test = QLabel()
        # Setup layout
        self._setup_layout()

    def _configure_process_library(self):
        """
        Configure the process library settings.
        """
        self.process_library.setDragDropMode(self.process_library.DragOnly)
        self.process_library.setAcceptDrops(False)
        self.process_library.setDragEnabled(True)
        self.process_library.setSelectionMode(
            self.process_library.SingleSelection
        )
        self.process_library.collapseAll()
        self.process_library.expandToDepth(1)

    def _setup_layout(self):
        """
        Setup the layout for the widget.
        """
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.label_test)
        self.splitter.addWidget(self.process_library)
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

    @staticmethod
    def load_config():
        """
        Read the configuration from process_config.yml and return it as a
        dictionary.
        .
        :return: The configuration as a dictionary.
        """
        # import verCmp only here to prevent circular import issue
        from populse_mia.utils import verCmp

        config = Config()
        config_path = os.path.join(
            config.get_properties_path(), "properties", "process_config.yml"
        )

        if not os.path.exists(config_path):
            open(config_path, "a").close()

        with open(config_path) as stream:

            try:

                if verCmp(yaml.__version__, "5.1", "sup"):
                    return yaml.load(stream, Loader=yaml.FullLoader)

                else:
                    return yaml.load(stream)

            except yaml.YAMLError as exc:
                logger.warning(exc)
                return {}

    def load_packages(self):
        """Set packages and paths to the widget and to the system paths."""
        self.packages = self.process_config.get("Packages", {})
        self.paths = self.process_config.get("Paths", [])

        for path in self.paths:

            if path not in sys.path:
                sys.path.append(path)

    def open_pkg_lib(self):
        """Open the package library."""
        self.pkg_library.show()

    def save_config(self):
        """Save the current configuration to process_config.yml."""
        config = Config()
        config_path = os.path.join(
            config.get_properties_path(), "properties", "process_config.yml"
        )
        self.process_config["Packages"] = self.packages
        self.process_config["Paths"] = self.paths

        with open(config_path, "w", encoding="utf8") as stream:
            yaml.dump(
                self.process_config,
                stream,
                default_flow_style=False,
                allow_unicode=True,
            )

    def update_config(self):
        """Update the configuration and load the corresponding packages."""
        self.process_config = self.load_config()
        self.load_packages()

    def update_process_library(self):
        """Update the tree of the process library."""
        self.update_config()
        self.process_library.package_tree = self.packages
        self.process_library.load_dictionary(self.packages)


def import_file(full_name, path):
    """
    Import a Python module from a specified file path.

    This function dynamically imports a module from a given file path and
    returns the module object. It does not modify `sys.modules`.

    :param full_name (str): The name of the module to import.
    :param path (str): The file path of the module.
    :return: The imported module.
    """

    from importlib import util

    spec = util.spec_from_file_location(full_name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def node_structure_from_dict(datadict, parent=None, root_node=None):
    """
    Construct a hierarchical node structure from a dictionary.

    This function converts a nested dictionary into a tree structure suitable
    for a TreeModel. It processes nodes based on specific conditions and
    recursively builds the tree.

    :param datadict (dict): The dictionary to convert into a node structure.
    :param parent: The parent node of the current node. Defaults to None.
    :param root_node: The root node of the tree. Defaults to None.

    :return: The root node of the constructed tree.
    """

    if parent is None:
        root_node = Node("Root")
        parent = root_node

    for name, data in sorted(datadict.items()):

        if isinstance(data, dict):
            list_name = [
                value for value in data.values() if value == "process_enabled"
            ]

            if not list_name:
                list_name = []
                list_values = [
                    value for value in data.values() if isinstance(value, dict)
                ]

                while list_values:
                    value = list_values.pop()
                    list_name.extend(
                        i for i in value.values() if not isinstance(i, dict)
                    )
                    list_values.extend(
                        i for i in value.values() if isinstance(i, dict)
                    )

            if all(item == "process_disabled" for item in list_name):
                continue

            node = Node(name, parent)
            node_structure_from_dict(data, node, root_node)

        elif data == "process_enabled":
            node = Node(name, parent)
            node.value = data

    return root_node


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("using Qt backend:", qt_backend.get_qt_backend())
    plw = ProcessLibraryWidget()
    plw.show()
    sys.exit(app.exec_())
