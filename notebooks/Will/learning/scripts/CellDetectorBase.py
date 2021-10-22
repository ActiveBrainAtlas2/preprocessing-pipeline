import os
from time import time
import glob
from Brain import Brain
import pickle as pkl

class CellDetectorBase(Brain):
    def __init__(self,animal,section):
        super().__init__(animal)
        self.section = section
        self.DATA_DIR = f"/data/cell_segmentation/{self.animal}/CH3/"
        self.SECTION_DIR=os.path.join(self.DATA_DIR,f"{self.section:03}")
    
    def get_sections_with_csv(self):
        sections = os.listdir(self.DATA_DIR)
        sections_with_csv = []
        for sectioni in sections:
            if glob.glob(os.path.join(self.DATA_DIR,sectioni,f'*.csv')):
                sections_with_csv.append(int(sectioni))
        return sections_with_csv
    
    def get_example_save_path(self):
        return self.SECTION_DIR+f'/extracted_cells_{self.section}.pkl'
    
    def get_feature_save_path(self):
        return self.DATA_DIR+f'/puntas_{self.section}.csv'
    
    def load_examples(self):
        save_path = self.get_example_save_path()
        with open(save_path,'br') as pkl_file:
            E=pkl.load(pkl_file)
            self.Examples=E['Examples']