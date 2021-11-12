import os
from time import time
import glob
from Brain import Brain
import pickle as pkl
import pandas as pd
import numpy as np
from cell_extractor.DetectionPlotter import DetectionPlotter

class CellDetectorBase(Brain):
    def __init__(self,animal,section = 0):
        self.attribute_functions = dict(
            tile_origins = self.get_tile_origins)
        super().__init__(animal)
        self.plotter = DetectionPlotter()
        self.ncol = 2
        self.nrow = 5
        self.section = section
        self.DATA_DIR = f"/data/cell_segmentation/{self.animal}"
        self.AVERAGE_CELL_IMAGE_DIR = os.path.join(self.DATA_DIR,'average_cell_image.pkl')
        self.TILE_INFO_DIR = os.path.join(self.DATA_DIR,'tile_info.csv')
        os.makedirs(self.DATA_DIR,exist_ok = True)
        self.CH3 = os.path.join(self.DATA_DIR,"CH3")
        self.CH1 = os.path.join(self.DATA_DIR,"CH1")
        self.CH3_SECTION_DIR=os.path.join(self.CH3,f"{self.section:03}")
        self.CH1_SECTION_DIR=os.path.join(self.CH1,f"{self.section:03}")
        self.get_tile_and_image_dimensions()
        self.get_tile_origins()
        self.check_tile_information()
    
    def get_tile_information(self):
        self.check_attributes(['tile_origins'])
        ntiles = len(self.tile_origins)
        tile_information = pd.DataFrame(columns = ['id','tile_origin','ncol','nrow','width','height'])
        for tilei in range(ntiles):
            tile_informationi = dict(
                id = tilei,
                tile_origin = self.tile_origins[tilei],
                ncol = self.ncol,
                nrow = self.nrow,
                width = self.width,
                height = self.height) 
            tile_information = tile_information.append(tile_informationi,ignore_index=True)
        return tile_information
    
    def save_tile_information(self):
        tile_information = self.get_tile_information()
        try:
            tile_information.to_csv(self.TILE_INFO_DIR,index = False)
        except IOError as e:
            print(e)
    
    def check_tile_information(self):
        if os.path.exists(self.TILE_INFO_DIR):
            tile_information = pd.read_csv(self.TILE_INFO_DIR)
            tile_information.tile_origin = tile_information.tile_origin.apply(eval)
            assert (tile_information == self.get_tile_information()).all().all()
        else:
            self.save_tile_information()
        
    def get_tile_and_image_dimensions(self):
        self.width,self.height = self.get_image_dimension()
        self.tile_height = int(self.height / self.nrow )
        self.tile_width=int(self.width/self.ncol )
    
    def get_tile_origins(self):
        self.check_attributes(['width'])
        self.tile_origins={}
        for i in range(self.nrow*self.ncol):
            row=int(i/self.ncol)
            col=i%self.ncol
            self.tile_origins[i] = (row*self.tile_height,col*self.tile_width)

    def get_tile_origin(self,tilei):
        self.check_attributes(['tile_origins'])
        return np.array(self.tile_origins[tilei],dtype=np.int32)

    def get_sections_with_csv(self):
        sections = os.listdir(self.CH3)
        sections_with_csv = []
        for sectioni in sections:
            if glob.glob(os.path.join(self.CH3,sectioni,f'*.csv')):
                sections_with_csv.append(int(sectioni))
        return sections_with_csv
    
    def get_example_save_path(self):
        return self.CH3_SECTION_DIR+f'/extracted_cells_{self.section}.pkl'
    
    def get_feature_save_path(self):
        return self.CH3_SECTION_DIR+f'/puntas_{self.section}.csv'
    
    def load_examples(self):
        save_path = self.get_example_save_path()
        try:
            with open(save_path,'br') as pkl_file:
                E=pkl.load(pkl_file)
                self.Examples=E['Examples']
        except IOError as e:
            print(e)
        
    def load_all_examples_in_brain(self,label = 1):
        sections = self.get_sections_with_csv()
        examples = []
        for sectioni in sections:
            base = CellDetectorBase(self.animal,sectioni)
            base.load_examples()
            examplei = [i for tilei in base.Examples for i in tilei if i['label'] == label]
            examples += examplei
        return examples
    
    def load_features(self):
        path=self.get_feature_save_path()
        try:
            self.features = pd.read_csv(path)
        except IOError as e:
            print(e)
    
    def save_features(self):
        for featurei in self.features:
            df_dict=None
            for i in range(len(self.Examples)):
                if df_dict==None:
                    df_dict={}
                    for key in featurei:
                        df_dict[key]=[]
                for key in featurei:
                    df_dict[key].append(featurei[key])
        df=pd.DataFrame(df_dict)
        outfile=self.get_feature_save_path()
        print('df shape=',df.shape,'output_file=',outfile)
        try:
            df.to_csv(outfile,index=False)
        except IOError as e:
            print(e)
    
    def save_examples(self):
        out={'Examples':self.Examples}
        print(f'section {self.section}')
        t1=time()
        try:
            with open(self.get_example_save_path(),'wb') as pkl_file:
                pkl.dump(out,pkl_file)
        except IOError as e:
            print(e)

def get_sections_with_annotation_for_animali(animal):
    base = CellDetectorBase(animal)
    return base.get_sections_with_csv()