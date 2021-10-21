"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""

import numpy as np
import sys
from collections import defaultdict
from pathlib import Path
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama
from skimage.filters import gaussian
PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
from lib.utilities_atlas import singular_structures
from lib.sqlcontroller import SqlController
from lib.utilities_atlas_lite import  symmetricalize_volume, find_merged_bounding_box,crop_and_pad_volumes
from atlas.Brain import Atlas,Brain
from rough_alignment.RigidRegistration import RigidRegistration
import SimpleITK as sitk
MANUAL = 1
CORRECTED = 2
DETECTED = 3

class BrainMerger(Atlas):

    def __init__(self,threshold = 0.9,moving_brains = ['MD594', 'MD585']):
        super().__init__()
        self.fixed_brain = Brain('MD589')
        self.moving_brains = [Brain(braini) for braini in moving_brains]
        self.sqlController = SqlController(self.fixed_brain.animal)
        width = self.sqlController.scan_run.width // 32
        height = self.sqlController.scan_run.height // 32
        depth = self.sqlController.get_section_count(self.fixed_brain.animal)
        self.fixed_brain_center = np.array([width//2, height//2, depth//2])
        self.threshold = threshold
        self.volumes_to_merge = defaultdict(list)
        self.origins_to_merge = defaultdict(list)
        self.registrator = RigidRegistration()

    def fine_tune_volume_position(self,fixed_volume,moving_volume,
        gradient_descent_setting,sampling_percentage):
        assert(fixed_volume.size == moving_volume.size)
        self.registrator.load_fixed_image_from_np_array(fixed_volume)
        self.registrator.load_moving_image_from_np_array(moving_volume)
        self.registrator.set_least_squares_as_similarity_metrics(sampling_percentage)
        self.registrator.set_optimizer_as_gradient_descent(gradient_descent_setting)
        self.registrator.status_reporter.set_report_events()
        self.registrator.set_initial_transformation()
        self.registrator.registration_method.Execute(self.registrator.fixed_image,
         self.registrator.moving_image)
        self.registrator.applier.transform = self.registrator.transform
        transformed_volume = self.registrator.applier.transform_np_array(moving_volume)
        return transformed_volume
    
    def refine_align_volumes(self,volumes):
        gradient_descent_setting = dict(
                learningRate=5,
                numberOfIterations=10000,
                convergenceMinimumValue=1e-6,
                convergenceWindowSize=50)
        volumes_to_align = [1,2]
        for volumei in volumes_to_align:
            transformed_volume = self.fine_tune_volume_position(volumes[0],volumes[volumei],gradient_descent_setting,
                sampling_percentage = 1)
            self.plotter.plot_3d_image_stack(transformed_volume-volumes[0],2)
            self.plotter.plot_3d_image_stack(transformed_volume,2)
            self.plotter.plot_3d_image_stack(volumes[0],2)
            self.plotter.plot_3d_image_stack(volumes[1],2)
            self.plotter.plot_3d_image_stack(volumes[2],2)
            volumes[volumei] = transformed_volume
        return volumes

    def get_merged_landmark_probability(self, structure, sigma=2.0):
        force_symmetry=(structure in singular_structures)
        volumes = self.volumes_to_merge[structure]
        origins = self.origins_to_merge[structure]
        bounding_boxes = [(x, x+volume.shape[0]-1, y, y+volume.shape[1]-1, z, z+volume.shape[2]-1) 
            for volume,(x,y,z) in zip(volumes, origins)]
        merged_bounding_box = np.floor(find_merged_bounding_box(bounding_boxes)).astype(int)
        volumes = crop_and_pad_volumes(merged_bounding_box, bounding_box_volume=list(zip(volumes, bounding_boxes)))
        volumes = list([(v > 0).astype(np.int32) for v in volumes])
        self.refine_align_volumes(volumes)
        merged_volume = np.sum(volumes, axis=0)
        merged_volume_prob = merged_volume / float(np.max(merged_volume))
        if force_symmetry:
            merged_volume_prob = symmetricalize_volume(merged_volume_prob)
        merged_volume_prob = gaussian(merged_volume_prob, sigma) 
        merged_origin = np.array(merged_bounding_box)[[0,2,4]]
        merged_origin = merged_origin - np.array(list(self.origins_to_merge.values())).min()+1
        return merged_volume_prob, merged_origin
    
    def load_data(self,brains):
        for braini in brains:
            braini.load_origins()
            braini.load_volumes()
            braini.load_com()

    def get_transform_to_align_brain(self,brain):
        resolution = brain.get_resolution()*32
        um_to_pixel = np.array([resolution,resolution,20])
        moving_com = (brain.get_com_array()/um_to_pixel).T
        fixed_com = (self.fixed_brain.get_com_array()/um_to_pixel).T
        r, t = umeyama(moving_com,fixed_com)
        return r,t

    def load_data_from_fixed_and_moving_brains(self):
        self.load_data([self.fixed_brain]+self.moving_brains)
        for structure in self.fixed_brain.origins:
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
        self.get_merged_landmark_probability('6N_R', sigma=2.0)
        for structure in self.volumes_to_merge:
            print(structure)
            if 'SC' in structure or 'IC' in structure:
                sigma = 5.0
            else:
                sigma = 2.0
            self.volumes[structure], self.origins[structure] = self.get_merged_landmark_probability(structure, sigma=sigma)
            
if __name__ == '__main__':
    merger = BrainMerger()
    merger.create_average_com_and_volume()
    merger.save_mesh_files()
    merger.save_origins()
    merger.save_volumes()