from atlas.BrainStructureManager import BrainStructureManager
from lib.utilities_atlas import ATLAS
from lib.FileLocationManager import DATA_PATH
import os
from abakit.registration.utilities import get_similarity_transformation_from_dicts
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama
import numpy as np 

class Atlas(BrainStructureManager):
    def __init__(self,atlas = ATLAS):
        self.atlas = atlas
        self.fixed_brain = BrainStructureManager('MD589')
        self.moving_brain = [BrainStructureManager(braini) for braini in ['MD594', 'MD585']]
        self.brains = self.moving_brain
        self.brains.append(self.fixed_brain)
        super().__init__('Atlas')
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(DATA_PATH, 'atlas_data', self.atlas)
        self.volume_path = os.path.join(self.animal_directory, 'structure')
        self.origin_path = os.path.join(self.animal_directory, 'origin')
        os.makedirs(self.animal_directory, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.origin_path, exist_ok=True)
    
    def get_transform_to_align_brain(self,brain):
        moving_com = (brain.get_com_array()*self.um_to_pixel).T
        fixed_com = (self.fixed_brain.get_com_array()*self.um_to_pixel).T
        r, t = umeyama(moving_com,fixed_com)
        return r,t
    
    def align_point_from_braini(self,braini,point):
        r,t = self.get_transform_to_align_brain(braini)
        return brain_to_atlas_transform(point, r, t)

    def load_atlas(self):
        self.load_origins()
        self.load_volumes()
    
    def load_com(self):
        self.COM = self.sqlController.get_atlas_centers()
    
    def get_average_coms(self):
        self.check_attributes(['structures'])
        annotated_animals = self.sqlController.get_annotated_animals()
        fixed_brain = self.fixed_brain.animal
        annotated_animals = annotated_animals[annotated_animals!=fixed_brain]
        annotations = [self.sqlController.get_com_dict(fixed_brain)]
        self.fixed_brain.load_com()
        for prepi in annotated_animals:
            com = self.sqlController.get_com_dict(prepi)
            r, t = get_similarity_transformation_from_dicts(fixed = self.fixed_brain.COM,\
                 moving = com)
            transformed = np.array([brain_to_atlas_transform(point, r, t) for point in com.values()])
            annotations.append(dict(zip(com.keys(),transformed)))
        averages = {}
        for structurei in self.structures:
            averages[structurei] = np.average([ prepi[structurei] for prepi \
                in annotations if structurei in prepi],0)
        return averages

class AtlasInitiator(Atlas):
    def __init__(self,atlas = ATLAS,com_function = None,threshold = 0.9,sigma = 3.0,conversion_factor = None):
        Atlas.__init__(self,atlas)
        if com_function == None:
            com_function = self.get_average_coms
        if isinstance(conversion_factor, type(None)):
            conversion_factor = self.fixed_brain.um_to_pixel
        self.load_volumes()
        self.gaussian_filter_volumes(sigma = sigma)
        self.threshold = threshold
        self.threshold_volumes()
        self.volumes = self.thresholded_volumes
        self.COM = com_function()
        self.COM,self.volumes = self.get_shared_coms(self.COM, self.volumes)
        self.structures = list(self.COM.keys())
        self.convert_unit_of_com_dictionary(self.COM,conversion_factor)
        self.origins = self.get_origin_from_coms()
