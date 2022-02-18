"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""

import numpy as np
from collections import defaultdict
from abakit.registration.algorithm import brain_to_atlas_transform,umeyama
from lib.utilities_atlas import singular_structures
from lib.SqlController import SqlController
from lib.utilities_atlas_lite import  symmetricalize_volume, find_merged_bounding_box,crop_and_pad_volumes
from atlas.Atlas import Atlas,BrainStructureManager
from Registration.StackRegistration.RigidRegistration import RigidRegistration
from Registration.StackRegistration.AffineRegistration import AffineRegistration
MANUAL = 1
CORRECTED = 2
DETECTED = 3

class BrainMerger(Atlas):

    def __init__(self,threshold = 0.8, moving_brains = ['MD594', 'MD585']):
        super().__init__()
        self.fixed_brain = BrainStructureManager('MD589')
        self.moving_brains = [BrainStructureManager(braini) for braini in moving_brains]
        self.sqlController = SqlController(self.fixed_brain.animal)
        self.threshold = threshold
        self.volumes_to_merge = defaultdict(list)
        self.origins_to_merge = defaultdict(list)
        self.registrator = AffineRegistration()
        self.symmetry_list = singular_structures

    def fine_tune_volume_position(self,fixed_volume,moving_volume,
        optimization_setting,sampling_percentage):
        assert(fixed_volume.size == moving_volume.size)
        self.registrator.load_fixed_image_from_np_array(fixed_volume)
        self.registrator.load_moving_image_from_np_array(moving_volume)
        self.registrator.set_least_squares_as_similarity_metrics(sampling_percentage)
        self.registrator.set_optimizer_as_gradient_descent(optimization_setting)
        self.registrator.set_initial_transformation()
        self.registrator.status_reporter.set_report_events()
        self.registrator.registration_method.Execute(self.registrator.fixed,
         self.registrator.moving)
        self.registrator.applier.transform = self.registrator.transform
        transformed_volume = self.registrator.applier.transform_and_resample_np_array(fixed_volume,
         moving_volume)
        return transformed_volume
    
    def refine_align_volumes(self,volumes):

        optimization_setting = dict(
                learningRate=10,
                numberOfIterations=10000,
                convergenceMinimumValue=1e-5,
                convergenceWindowSize=50)

        volumes_to_align = [1,2]
        for volumei in volumes_to_align:
            transformed_volume = self.fine_tune_volume_position(volumes[0],volumes[volumei],
            optimization_setting,sampling_percentage = 1)
            volumes[volumei] = transformed_volume
        return volumes
    
    def pad_volume(self,size,volume):
        size_difference = size - volume.shape
        xr,yr,zr = ((size_difference)/2).astype(int)
        xl,yl,zl = size_difference - np.array([xr,yr,zr])
        return np.pad(volume,[[xl,xr],[yl,yr],[zl,zr]])


    def get_merged_landmark_probability(self, structure):
        print(f'aligning structure: {structure}')
        force_symmetry=(structure in self.symmetry_list)
        volumes = self.volumes_to_merge[structure]
        sizes = np.array([vi.shape for vi in volumes])
        margin = 10
        volume_size = sizes.max(0)+ margin
        volumes = [self.pad_volume(volume_size, vi) for vi in volumes]
        volumes = list([(v > 0).astype(np.int32) for v in volumes])
        self.refine_align_volumes(volumes)
        merged_volume = np.sum(volumes, axis=0)
        merged_volume_prob = merged_volume / float(np.max(merged_volume))
        if force_symmetry:
            merged_volume_prob = symmetricalize_volume(merged_volume_prob)
        return merged_volume_prob

    def load_data(self,brains):
        for braini in brains:
            braini.load_origins()
            braini.load_volumes()
            braini.load_com()

    def load_data_from_fixed_and_moving_brains(self):
        self.load_data([self.fixed_brain]+self.moving_brains)
        for structure in self.fixed_brain.origins:            
            if structure == 'RtTg':
                braini = self.moving_brains[0]
                origin,volume = braini.origins[structure],braini.volumes[structure]
                r,t = self.get_transform_to_align_brain(braini)
                origin = brain_to_atlas_transform(origin, r, t)
            else:
                origin,volume = self.fixed_brain.origins[structure],self.fixed_brain.volumes[structure]
            self.volumes_to_merge[structure].append(volume)
            self.origins_to_merge[structure].append(origin)
        for brain in self.moving_brains:
            brain.transformed_origins = {}
            r,t = self.get_transform_to_align_brain(brain)
            for structure in brain.origins:
                origin,volume = brain.origins[structure],brain.volumes[structure]
                aligned_origin = brain_to_atlas_transform(origin, r, t)   
                brain.transformed_origins[structure] =  aligned_origin            
                self.volumes_to_merge[structure].append(volume)
                self.origins_to_merge[structure].append(aligned_origin)

    def create_average_com_and_volume(self):
        self.load_data_from_fixed_and_moving_brains()
        for structure in self.volumes_to_merge:
            self.volumes[structure]= self.get_merged_landmark_probability(structure)
        

if __name__ == '__main__':
    merger = BrainMerger()
    merger.create_average_com_and_volume()
    merger.save_mesh_files()
    merger.save_volumes()