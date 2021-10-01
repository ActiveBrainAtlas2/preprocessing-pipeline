import os
from multiprocessing.pool import Pool
import sys
import numpy as np
from datetime import datetime
from lib.utilities_process import workernoshell
from lib.sqlcontroller import SqlController
class TiffSegmentor:
    def __init__(self,animal):
        self.animal = animal
        self.controller = SqlController(animal)
    
    def create_directories_for_channeli(self,channel):
        self.channel = channel
        self.tif_directory = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{self.animal}/preps/CH{self.channel}/full_aligned/'
        self.animal_directory = f'/data/cell_segmentation/{self.animal}'
        self.save_directory = self.animal_directory + f'/CH{self.channel}/'
        if not os.path.exists(self.animal_directory):
            os.mkdir(self.animal_directory)
        if not os.path.exists(self.save_directory):
            os.mkdir(self.save_directory)
        files = os.listdir(self.tif_directory)
        for filei in files:
            file_name = filei[:-4]
            save_folder = self.save_directory+file_name
            if not os.path.exists(save_folder):
                os.mkdir(save_folder)

    def generate_tiff_segments(self,channel,create_csv=False):
        self.create_directories_for_channeli(channel)
        files = os.listdir(self.tif_directory)
        for filei in files:
            file_name = filei[:-4]
            save_folder = self.save_directory+file_name
            if create_csv:
                self.create_sectioni_csv(save_folder,int(file_name))
            if len(os.listdir(save_folder)) == 11:
                continue
            cmd = [f'convert', self.tif_directory + filei, '-compress', 'None', '-crop', '2x5-0-0@', 
            '+repage', '+adjoin', f'{save_folder}/{file_name}tile-%d.tif']
            workernoshell(cmd)
    
    def create_sectioni_csv(self,save_path,sectioni):
        time_stamp = datetime.today().strftime('%Y-%m-%d')
        csv_path = save_path+f'/{self.animal}_premotor_{sectioni}_{time_stamp}.csv'
        if not os.path.isfile(csv_path):
            print('creating '+ csv_path)
            search_dictionary = {'prep_id':self.animal,'input_type_id':1,'person_id':2,'layer':'Premotor','section':sectioni}
            premotor = self.controller.get_layer_data(search_dictionary)
            premotor = self.controller.get_coordinates_from_query_result(premotor)
            np.savetxt(csv_path,premotor,delimiter=',')