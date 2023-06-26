import os
import numpy as np 

from brain_structure_manager import BrainStructureManager
from library.registration.utilities import get_similarity_transformation_from_dicts
from library.registration.algorithm import brain_to_atlas_transform, umeyama
from library.image_manipulation.filelocation_manager import data_path
from library.controller.structure_com_controller import StructureCOMController

atlas = 'atlasV8'

class Atlas(BrainStructureManager):
    def __init__(self, atlas = atlas):
        BrainStructureManager.__init__(self,'Atlas')
        self.atlas = atlas
        self.animal = atlas
        self.set_path_and_create_folders()
        self.fixed_brain = BrainStructureManager('MD589')
        self.moving_brain = [BrainStructureManager(braini) for braini in ['MD594', 'MD585']]
        self.brains = self.moving_brain
        self.brains.append(self.fixed_brain)
        super().__init__('Atlas')
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(data_path, 'atlas_data', self.atlas)
        self.volume_path = os.path.join(self.animal_directory, 'structure')
        self.origin_path = os.path.join(self.animal_directory, 'origin')
        os.makedirs(self.animal_directory, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.origin_path, exist_ok=True)

    def get_transform_to_align_brain(self, brain):
        moving_com = (brain.get_com_array()*self.um_to_pixel).T
        fixed_com = (self.fixed_brain.get_com_array()*self.um_to_pixel).T
        
        print(f'moving brain={brain.animal} data={moving_com.shape}')
        print(f'fixed brain={self.fixed_brain.animal} data={fixed_com.shape}')
        r, t = umeyama(moving_com, fixed_com)
        return r, t

    def align_point_from_braini(self,braini,point):
        r,t = self.get_transform_to_align_brain(braini)
        return brain_to_atlas_transform(point, r, t)

    def load_atlas(self):
        self.load_origins()
        self.load_volumes()
    
    def load_com(self):
        self.COM = self.sqlController.get_atlas_centers()
    
    def get_average_coms(self):
        fixed_brain = self.fixed_brain.animal
        controller = StructureCOMController(fixed_brain)
        coms = controller.get_all_manual_COM()
        annotated_animals = np.array(list(coms.keys()))
        annotated_animals = annotated_animals[annotated_animals!=fixed_brain]
        annotations = [coms[fixed_brain]]
        self.fixed_brain.load_com()
        for animal in annotated_animals:
            com = coms[animal]
            r, t = get_similarity_transformation_from_dicts(fixed = coms[fixed_brain],\
                    moving = com)
            transformed = np.array([brain_to_atlas_transform(point, r, t) for point in com.values()])
            annotations.append(dict(zip(com.keys(),transformed)))
        averages = {}
        self.structures = [structure.abbreviation for structure in controller.get_structures()]
        for structurei in self.structures:
            averages[structurei] = np.average([ prepi[structurei] for prepi \
                in annotations if structurei in prepi],0)
        return averages

class AtlasInitiator(Atlas):
    def __init__(self,atlas = atlas, com_function = None,threshold = 0.9,sigma = 3.0,conversion_factor = None):
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
        self.structures = list(self.COM.keys())
        self.convert_unit_of_com_dictionary(self.COM,conversion_factor)
        self.origins = self.get_origin_from_coms()
 