import os
from multiprocessing.pool import Pool
import sys
import numpy as np
from datetime import datetime
from lib.utilities_process import workernoshell
from lib.sqlcontroller import SqlController
from cell_extractor.CellDetectorBase import CellDetectorBase
class TiffSegmentor(CellDetectorBase):
    def __init__(self,animal):
        super().__init__(animal,0)
        self.detect_annotator_person_id()
    
    def detect_annotator_person_id(self):
        Beth = 2
        Hannah = 3
        for person_id in [Beth,Hannah]:
            search_dictionary = {'prep_id':self.animal,'input_type_id':1,'person_id':person_id,'layer':'Premotor'}
            has_annotation = self.sqlController.get_layer_data(search_dictionary)
            if has_annotation != []:
                self.person_id = person_id
    
    def get_save_folders(self,save_directory):
        tif_directory = self.path.get_full_aligned()
        files = os.listdir(self.tif_directory)
        self.save_folders = []
        for filei in files:
            file_name = filei[:-4]
            save_folder = os.path.join(save_directory,file_name)
            self.save_folders.append(save_folder)

    def create_directories_for_channeli(self,channel):
        self.channel = channel
        os.path.join(self.path.prep)
        self.tif_directory = self.path.get_full_aligned(self.channel)
        self.save_directory = self.DATA_DIR + f'/CH{self.channel}/'
        if not os.path.exists(self.save_directory):
            os.mkdir(self.save_directory)
        self.get_save_folders(self.save_directory)
        for save_folder in self.save_folders:
            if not os.path.exists(save_folder):
                os.mkdir(save_folder)

    def generate_tiff_segments(self,channel,create_csv=False):
        self.create_directories_for_channeli(channel)
        for save_folder in self.save_folders:
            filei = '/'+save_folder[-3:]+'.tif'
            file_name = save_folder[-3:]
            if create_csv:
                self.create_sectioni_csv(save_folder,int(file_name))
                if len(os.listdir(save_folder)) >= 10:
                    continue
            else:
                if len(os.listdir(save_folder)) == 10:
                    continue
            cmd = [f'convert', self.tif_directory + filei, '-compress', 'LZW', '-crop', 
            f'{self.ncol}x{self.nrow}-0-0@', '+repage', '+adjoin', 
            f'{save_folder}/{file_name}tile-%d.tif']
            print(' '.join(cmd))
            workernoshell(cmd)
    
    def have_csv_in_path(self,path):
        files = os.listdir(path)
        return np.any(['.csv' in filei for filei in files]) 
    
    def create_sectioni_csv(self,save_path,sectioni):
        time_stamp = datetime.today().strftime('%Y-%m-%d')
        csv_path = save_path+f'/{self.animal}_premotor_{sectioni}_{time_stamp}.csv'
        if not self.have_csv_in_path(save_path):
            search_dictionary = {'prep_id':self.animal,'input_type_id':1,\
                'person_id':self.person_id,'layer':'Premotor','section':int(sectioni*20)}
            premotor = self.controller.get_layer_data(search_dictionary)
            premotor = self.controller.get_coordinates_from_query_result(premotor)
            if premotor != []:
                print('creating '+ csv_path)
                np.savetxt(csv_path,premotor,delimiter=',',header='x,y,Section',comments = '',fmt = '%f')