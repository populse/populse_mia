from bids import BIDSLayout
import os
import yaml
import json
import gzip
import shutil
from PyQt5.QtWidgets import QMainWindow, QProgressBar, QApplication, QFileDialog
import sys
# import threading
# from multiprocessing import Queue, Process
# import time

from populse_mia.data_manager.project import COLLECTION_CURRENT


# data_path =  '..../data/raw_data'
# data_export = '.../Bids_export'


class ProgressBar(QMainWindow):

    def __init__(self):
        super().__init__()

        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 250, 25)
        self.pbar.setValue(0)

        self.setWindowTitle("Conversion progress ... ")
        self.setGeometry(32,32,300,100)


class ExportToBIDS():

    def __init__(self, project):
        current_path = os.path.dirname(os.path.realpath(__file__))
        self.mod_Bids = os.path.join(current_path,'Modalities_BIDS.yml')
        self.project = project
        self.documents = project.session.get_documents_names(
                                            COLLECTION_CURRENT)
        # tags = project.session.get_fields_names(
        #                                 COLLECTION_CURRENT)
        # print('tags :', tags)
        if self.documents:
            self.data_export = self.dialogbox_dir()
            if self.data_export:
                new_tags = {}
                new_tags["Name"] = "Exported with Populse_MIA"
                new_tags["BIDSVersion"] = "1.6.0"
                new_tags["pyBIDSVersion"] = ""

                data_descript = os.path.join(self.data_export, 
                                             "dataset_description.json")

                with open(data_descript, 'w+') as f:
                    json.dump(new_tags, f)

                self.layout = BIDSLayout(self.data_export)
                self.p = ProgressBar()
                self.startExport()

    def dialogbox_dir(self):
        rep = str(QFileDialog.getExistingDirectory(
                                    None, 
                                    "Export to BIDS: Select Directory"))
        return rep

    def find(self, d, tag):
        for ka, va in d.items():
            for kb, vb in va.items():
                t = list(vb.values())
                list_values = [item for sublist in t for item in sublist]
                # if tag in list_values:
                #     yield ka, kb, vb
                if any(s[1:-1] in tag for s in list_values):
                    yield ka, kb, vb

    def save_nii_gz(self, file_nii, dest_file):
        with open(file_nii, 'rb') as f_in:
            with gzip.open(dest_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def save_json(self, tags_orig, dest_file):
        new_tags = {}
        for keys_tg, val_tg in tags_orig.items():
            if isinstance(val_tg, dict):
                new_tags[keys_tg.replace(" ","")] = val_tg['value'][0]
        with open(dest_file, 'w') as f:
            json.dump(new_tags, f)

    def save_bvec_bval(self, bvec_bval, dest, ext):
        dir_name = os.path.dirname(dest)
        base_name = os.path.basename(dest)
        base_name = os.path.splitext(base_name)[0]
        base_name = os.path.splitext(base_name)[0]
        new_bvec_bval = os.path.join(dir_name, base_name + ext)
        shutil.copy(bvec_bval, new_bvec_bval)

    def startExport(self):

        list_nii, sub = [], {}
        
        # print('export to BIDS (' + str(len(self.documents)) + ' files)')
        # list_tag = ['StudyName', 'ProtocolName', 'SequenceName']
        # for doc in self.documents:
        #     print('\n' + doc)
        #     for lst in list_tag:
        #         print("{0} = {1} ; ".format(lst,self.project.session.get_value(
        #                                     COLLECTION_CURRENT,
        #                                     doc,
        #                                     lst)))
        
        data_path = self.project.folder

        for doc in self.documents:
            if doc.endswith('.nii') and 'raw_data' in doc:
                list_nii.append(doc)
                sub_current = self.project.session.get_value(
                                            COLLECTION_CURRENT,
                                            doc,
                                            'StudyName')
                ses_current = self.project.session.get_value(
                                            COLLECTION_CURRENT,
                                            doc,
                                            'CreationDate')
                if sub_current not in sub:
                    sub[sub_current] = ('0' + str(len(sub) + 1), [ses_current])
                else:
                    sub_tmp = sub[sub_current]
                    tmp = sub_tmp[1]
                    # print('tmp = ', tmp)
                    if tmp is None:
                        tmp = [ses_current]
                    else:
                        tmp.append(ses_current)
                    sub[sub_current] = (sub_tmp[0], sorted(list(dict.fromkeys(tmp))))
        
        with open(self.mod_Bids, 'r') as stream:
            modal_bids = yaml.load(stream, yaml.FullLoader)

        n = len(list_nii)
        i = 0
        self.p.pbar.setValue(i)
        self.p.show()
        
        for doc in list_nii:

            QApplication.processEvents()
            i += round(100 / n)
            self.p.pbar.setValue(i)

            tmp = sub[self.project.session.get_value(
                                            COLLECTION_CURRENT,
                                            doc,
                                            'StudyName')]
            seq_name = self.project.session.get_value(
                                            COLLECTION_CURRENT,
                                            doc,
                                            'SequenceName')
            if not seq_name:
                seq_name = self.project.session.get_value(
                                            COLLECTION_CURRENT,
                                            doc,
                                            'ProtocolName')
            suff_found = ''
            for val in self.find(modal_bids['listProtocols'], seq_name):
                suff_found = val
            if not suff_found:
                seq_name = self.project.session.get_value(
                                            COLLECTION_CURRENT,
                                            doc,
                                            'ProtocolName')
                for val in self.find(modal_bids['listProtocols'], seq_name):
                    suff_found = val

            # pattern = "sub-{subject}[_
                         # ses-{session}]_
                         # task-{task}[_
                         # acq-{acquisition}][_
                         # rec-{reconstruction}][_
                         # run-{run}][_echo-{echo}]_{suffix}.nii.gz"
        
            entities = {
            'subject': tmp[0],
            'session': '0' + str(tmp[1].index(self.project.session.get_value(
                                            COLLECTION_CURRENT,
                                            doc,
                                            'CreationDate')) + 1),
            # 'run': 2,
            # 'task': 'nback',
            'datatype': suff_found[0],
            'suffix': suff_found[1]
            }
            path_nii = os.path.join(data_path, doc)
            path_nii_without_ext = os.path.splitext(path_nii)[0]
            tags = {}
            tags["Name"] = "OM"

            try:
                path_const = self.layout.build_path(entities, validate=True)
                dir_path = os.path.dirname(path_const)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, 0o777)
                base_path = os.path.basename(path_const)
                file_json = os.path.splitext(base_path)[0]
                file_json = os.path.splitext(file_json)[0]
                path_json = os.path.join(dir_path, file_json + '.json')

                self.save_nii_gz(path_nii, path_const)
                self.save_json(tags, path_json)
                bval_path = path_nii_without_ext + '-bvals-MRtrix.txt'
                bvec_path = path_nii_without_ext + '-bvecs-MRtrix.txt'
                if os.path.exists(bval_path):
                    self.save_bvec_bval(bval_path, path_const, '.bval')
                if os.path.exists(bvec_path):
                    self.save_bvec_bval(bvec_path, path_const, '.bvec')

                # print(' ' * 10, 'exported to ', path_const)
            except Exception as e:
                print(path_nii)
                print("can't build this data : ", e)
        
        self.p.close()
