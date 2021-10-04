"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""

from sqlalchemy import func
import numpy as np
import os
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama
from skimage.filters import gaussian

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from model.structure import Structure
from model.layer_data import LayerData
from lib.sql_setup import session
from lib.file_location import DATA_PATH
from lib.utilities_atlas import singular_structures
from lib.sqlcontroller import SqlController
from lib.utilities_atlas_lite import  symmetricalize_volume, volume_to_polygon, save_mesh, \
    find_merged_bounding_box,crop_and_pad_volumes

MANUAL = 1
CORRECTED = 2
DETECTED = 3

"""
    The provided r, t is the affine transformation from brain to atlas such that:
        t_phys = atlas_scale @ t
        atlas_coord_phys = r @ brain_coord_phys + t_phys

    The corresponding reverse transformation is:
        brain_coord_phys = r_inv @ atlas_coord_phys - r_inv @ t_phys
"""

class BrainMerger:

    def __init__(self,threshold = 0.6):
        self.ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', 'atlasV8')
        self.fixed_brain = 'MD589'
        self.sqlController = SqlController(self.fixed_brain)
        width = self.sqlController.scan_run.width // 32
        height = self.sqlController.scan_run.height // 32
        self.fixed_brain_center = np.array([width//2, height//2, 440//2])
        self.moving_brains = ['MD589', 'MD585']
        self.threshold = threshold

    def get_merged_landmark_probability(self,volume_and_com, force_symmetry=False, sigma=2.0):
        """
        Compute the mean shape based on many co-registered volumes.

        Args:
            force_symmetric (bool): If True, force the resulting volume and mesh to be symmetric wrt z.
            sigma (float): sigma of gaussian kernel used to smooth the probability values.

        Returns:
            average_volume_prob (3D ndarray):
            common_mins ((3,)-ndarray): coordinate of the volume's origin
        """
        volumes, origins = list(map(list, list(zip(*volume_and_com))))
        bounding_boxes = [(x, x+volume.shape[1]-1, y, y+volume.shape[0]-1, z, z+volume.shape[2]-1) 
            for volume,(x,y,z) in zip(volumes, origins)]
        merged_bounding_box = np.round(find_merged_bounding_box(bounding_boxes)).astype(np.int)
        volumes = crop_and_pad_volumes(merged_bounding_box, bounding_box_volume=list(zip(volumes, bounding_boxes)))
        volumes = list([(v > 0).astype(np.int32) for v in volumes])
        merged_volume = np.sum(volumes, axis=0)
        merged_volume_prob = merged_volume / float(np.max(merged_volume))
        if force_symmetry:
            merged_volume_prob = symmetricalize_volume(merged_volume_prob)
        merged_volume_prob = gaussian(merged_volume_prob, sigma) # Smooth the probability
        merged_origin = np.array(merged_bounding_box)[[0,2,4]]
        return merged_volume_prob, merged_origin

    def get_centers_from_data_base(self,animal):
        rows = session.query(LayerData).filter(
            LayerData.active.is_(True))\
                .filter(LayerData.prep_id == animal)\
                .filter(LayerData.person_id == 2)\
                .filter(LayerData.layer == 'COM')\
                .filter(LayerData.input_type_id == MANUAL)\
                .order_by(LayerData.structure_id)\
                .all()
        data = []
        for row in rows:
            data.append( [row.x, row.y, row.section] )
        return np.array(data)

    def add_layer_data_row(self,abbrev, origin):
        structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
        x,y,z = origin
        com = LayerData(
            prep_id='Atlas', structure=structure, x=x, y=y, section=z
            , layer='COM',
            created=datetime.utcnow(), active=True, person_id=16, input_type_id=MANUAL
        )
        try:
            session.add(com)
            session.commit()
        except Exception as e:
            print(f'No merge {e}')
            session.rollback()

    def get_volumn_and_com_per_structure(self):
        volume_and_com = defaultdict(list)
        fixed_data = self.get_centers_from_data_base(self.fixed_brain)
        ORIGIN_PATH = os.path.join(self.ATLAS_PATH, self.fixed_brain, 'origin')
        origin_files = sorted(os.listdir(ORIGIN_PATH))
        VOLUME_PATH = os.path.join(self.ATLAS_PATH, self.fixed_brain, 'structure')
        volume_files = sorted(os.listdir(VOLUME_PATH))
        for volume_filename, origin_filename in zip(volume_files, origin_files):
            structure = os.path.splitext(origin_filename)[0]    
            origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
            volume = np.load(os.path.join(VOLUME_PATH, volume_filename))
            volume_and_com[structure].append((volume, origin))
        for brain in self.moving_brains:
            moving_data = self.get_centers_from_data_base(brain)
            r, t = umeyama(moving_data.T, fixed_data.T)
            ORIGIN_PATH = os.path.join(self.ATLAS_PATH, brain, 'origin')
            origin_files = sorted(os.listdir(ORIGIN_PATH))
            VOLUME_PATH = os.path.join(self.ATLAS_PATH, brain, 'structure')
            volume_files = sorted(os.listdir(VOLUME_PATH))
            for volume_filename, origin_filename in zip(volume_files, origin_files):
                structure = os.path.splitext(origin_filename)[0]    
                origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
                volume = np.load(os.path.join(VOLUME_PATH, volume_filename))
                aligned_origin = brain_to_atlas_transform(origin, r, t)                
                volume_and_com[structure].append((volume, aligned_origin))
        return volume_and_com

    def save_mesh_file(self,origin,volume,structure):
        centered_origin = origin - self.fixed_brain_center
        threshold_volume = volume >= self.threshold
        aligned_volume = (threshold_volume, centered_origin)
        aligned_structure = volume_to_polygon(volume=aligned_volume,num_simplify_iter=3, smooth=False,return_vertex_face_list=False)
        filepath = os.path.join(self.ATLAS_PATH, 'mesh', f'{structure}.stl')
        save_mesh(aligned_structure, filepath)

    def save_origin_and_volume(self,origin,volume,structure):
        volume_outpath = os.path.join(self.ATLAS_PATH, 'structure', f'{structure}.npy')
        com_outpath = os.path.join(self.ATLAS_PATH, 'origin', f'{structure}.txt')
        np.save(volume_outpath, volume)
        np.savetxt(com_outpath, origin)
        print(structure, volume.shape, volume.dtype, np.mean(volume), np.amax(volume), origin)
        self.add_layer_data_row(structure, origin)

    def create_average_com_and_volumn(self):
        volume_and_com_per_structure = self.get_volumn_and_com_per_structure()
        for structure, volumn_and_com in volume_and_com_per_structure.items():
            if 'SC' in structure or 'IC' in structure:
                sigma = 5.0
            else:
                sigma = 2.0
            volume, origin = self.get_merged_landmark_probability(volume_and_com=volumn_and_com,
            force_symmetry=(structure in singular_structures), sigma=sigma)
            # self.save_mesh_file(self,origin,volume,structure)
            # self.save_origin_and_volume(self,origin,volume,structure)
            
if __name__ == '__main__':
    merger = BrainMerger()
    merger.create_average_com_and_volumn()
