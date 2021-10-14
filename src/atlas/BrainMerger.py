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
MANUAL = 1
CORRECTED = 2
DETECTED = 3

class BrainMerger(Atlas):

    def __init__(self,threshold = 0.6,moving_brains = ['MD589', 'MD585']):
        super().__init__()
        self.fixed_brain = Brain('MD589')
        self.moving_brains = [Brain(braini) for braini in moving_brains]
        self.sqlController = SqlController(self.fixed_brain.animal)
        width = self.sqlController.scan_run.width // 32
        height = self.sqlController.scan_run.height // 32
        self.fixed_brain_center = np.array([width//2, height//2, 440//2])
        self.threshold = threshold
        self.volumes_to_merge = defaultdict(list)
        self.origins_to_merge = defaultdict(list)

    def get_merged_landmark_probability(self, structure, sigma=2.0):
        if structure == 'SC' or structure == 'IC':
            breakpoint()
        force_symmetry=(structure in singular_structures)
        volumes = self.volumes_to_merge[structure]
        origins = self.origins_to_merge[structure]
        bounding_boxes = [(x, x+volume.shape[1]-1, y, y+volume.shape[0]-1, z, z+volume.shape[2]-1) 
            for volume,(x,y,z) in zip(volumes, origins)]
        merged_bounding_box = np.round(find_merged_bounding_box(bounding_boxes)).astype(int)
        volumes = crop_and_pad_volumes(merged_bounding_box, bounding_box_volume=list(zip(volumes, bounding_boxes)))
        volumes = list([(v > 0).astype(np.int32) for v in volumes])
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
            braini.load_com()
            braini.load_origins()
            braini.load_volumes()

    def load_data_from_fixed_and_moving_brains(self):
        self.load_data([self.fixed_brain]+self.moving_brains)
        for structure in self.fixed_brain.COM:
            origin,volume = self.fixed_brain.origins[structure],self.fixed_brain.volumes[structure]
            self.volumes_to_merge[structure].append(volume)
            self.origins_to_merge[structure].append(origin)
        for brain in self.moving_brains:
            r, t = umeyama(self.fixed_brain.get_com_array().T, brain.get_com_array().T)
            for structure in brain.COM:
                origin,volume = brain.origins[structure],brain.volumes[structure]
                aligned_origin = brain_to_atlas_transform(origin, r, t)                
                self.volumes_to_merge[structure].append(volume)
                self.origins_to_merge[structure].append(aligned_origin)

    def create_average_com_and_volume(self):
        self.load_data_from_fixed_and_moving_brains()
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