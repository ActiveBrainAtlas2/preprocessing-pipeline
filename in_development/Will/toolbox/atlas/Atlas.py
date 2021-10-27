import os
import numpy as np
class Atlas:
    def __init__(self,atlas_folder):
        self.atlas_folder = atlas_folder
        self.origins = {}
        self.structures = {}
    
    def load_atlas(self):
        origin_folder = os.path.join(self.atlas_folder,'origin')
        structure_folder = os.path.join(self.atlas_folder,'structure')

    def load_origins(self,origin_folder):
        origin_files = os.listdir(origin_folder)
        for filei in origin_files:
            structure_name = self.get_structure_name(filei)
            file_path = os.path.join(origin_folder,filei)
            self.origins[structure_name] = np.loadtxt(file_path)
        
    def load_structures(self,structure_folder):
        struture_files = os.listdir(structure_folder)
        for filei in struture_files:
            structure_name = self.get_structure_name(filei)
            file_path = os.path.join(structure_folder,filei)
            self.structures[structure_name] = np.load(file_path)

    def get_structure_name(file_name):
        return file_name.split('.')[0]

    def compare_atlas(self,new_atlas):
        assert(self.origins == new_atlas.origins)
        assert(self.structures == new_atlas.structures)