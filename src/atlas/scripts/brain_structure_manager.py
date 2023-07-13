import os
import numpy as np
from collections import defaultdict
import cv2
import json

from library.controller.polygon_sequence_controller import PolygonSequenceController
from library.registration.utilities_registration import SCALING_FACTOR
from library.controller.sql_controller import SqlController
from library.controller.structure_com_controller import StructureCOMController
from library.image_manipulation.filelocation_manager import data_path
from library.utilities.algorithm import brain_to_atlas_transform, umeyama
from library.utilities.atlas import volume_to_polygon, save_mesh


class BrainStructureManager():

    def __init__(self, animal = 'MD589', atlas = 'atlasV8', downsample_factor = SCALING_FACTOR):
        self.DOWNSAMPLE_FACTOR = downsample_factor
        self.animal = animal
        
        self.fixed_brain = None
        self.sqlController = SqlController(animal)
        to_um = self.DOWNSAMPLE_FACTOR * self.sqlController.scan_run.resolution
        self.pixel_to_um = np.array([to_um, to_um, 20])
        self.um_to_pixel = 1 / self.pixel_to_um
        self.data_path = os.path.join(data_path, 'atlas_data')
        self.volume_path = os.path.join(self.data_path, animal, 'structure')
        self.origin_path = os.path.join(self.data_path, animal, 'origin')
        self.mesh_path = os.path.join(self.data_path, animal, 'mesh')
        self.aligned_contours = {}

    def load_aligned_contours(self):
        """load aligned contours
        """       
        aligned_and_padded_contour_path = os.path.join(self.data_path, self.animal, 'aligned_padded_structures.json')
        print(f'Loading JSON data from {aligned_and_padded_contour_path}')
        with open(aligned_and_padded_contour_path) as f:
            self.aligned_contours = json.load(f)



    def get_coms(self):
        """Get the center of mass values for this brain as an array

        Returns:
            np array: COM of the brain
        """
        #self.load_com()
        controller = StructureCOMController(self.animal)
        coms = controller.get_COM(self.animal)
        return coms

    def get_transform_to_align_brain(self, brain):
        """Used in aligning data to fixed brain
        """
        if brain.animal == self.fixed_brain.animal:
            return np.eye(3), np.zeros((3,1))


        moving_coms = brain.get_coms()
        fixed_coms = self.fixed_brain.get_coms()
        common_keys = fixed_coms.keys() & moving_coms.keys()
        brain_regions = sorted(moving_coms.keys())
        fixed_points = np.array([fixed_coms[s] for s in brain_regions if s in common_keys])
        moving_points = np.array([moving_coms[s] for s in brain_regions if s in common_keys])

        if fixed_points.shape != moving_points.shape or len(fixed_points.shape) != 2 or fixed_points.shape[0] < 3:
            return None, None


        sfactor = self.DOWNSAMPLE_FACTOR
        f_scale_xy = self.fixed_brain.sqlController.scan_run.resolution
        f_z_scale = self.fixed_brain.sqlController.scan_run.zresolution
        f_scales = np.array([f_scale_xy, f_scale_xy, f_z_scale])
        sfactor = np.array([sfactor, sfactor, 1])
        fixed_com_set = fixed_points / f_scales / sfactor

        m_scale_xy = self.sqlController.scan_run.resolution
        m_z_scale = self.sqlController.scan_run.zresolution
        m_scales = np.array([m_scale_xy, m_scale_xy, m_z_scale])
        moving_com_set = moving_points / m_scales / sfactor



        #moving_com = (moving_com_set * self.um_to_pixel).T
        #fixed_com = (fixed_com_set * self.fixed_brain.um_to_pixel).T       
        r, t = umeyama(moving_com_set.T, fixed_com_set.T)
        return r, t


    def get_origin_and_section_size(self, structure_contours):
        """Gets the origin and section size
        Set the pad to make sure we get all the volume
        """
        pad = 50
        section_mins = []
        section_maxs = []
        for section, contour_points in structure_contours.items():
            contour_points = np.array(contour_points)
            section_mins.append(np.min(contour_points, axis=0))
            section_maxs.append(np.max(contour_points, axis=0))
        min_z = min([int(i) for i in structure_contours.keys()])
        min_x, min_y = np.min(section_mins, axis=0)
        max_x, max_y = np.max(section_maxs, axis=0)
        max_x += pad
        max_y += pad
        xspan = max_x - min_x
        yspan = max_y - min_y
        origin = np.array([min_x, min_y, min_z])
        section_size = np.array([xspan, yspan]).astype(int)
        return origin, section_size


    def compute_origin_and_volume_for_brain_structures(self, brainManager, brainMerger, annotator_id):
        animal = brainManager.animal
        polygon = PolygonSequenceController(animal=animal)
        controller = StructureCOMController(animal)
        structures = controller.get_structures()
        removes = []
        for structure in structures:
            df = polygon.get_volume(animal, annotator_id, structure.id)
            if df.empty:
                continue;
            
            scale_xy = self.sqlController.scan_run.resolution
            z_scale = self.sqlController.scan_run.zresolution        
            polygons = defaultdict(list)
            
            
            for _, row in df.iterrows():
                x = row['coordinate'][0]
                y = row['coordinate'][1]
                z = row['coordinate'][2]
                xy = (x/scale_xy/self.DOWNSAMPLE_FACTOR, y/scale_xy/self.DOWNSAMPLE_FACTOR)
                section = int(np.round(z/z_scale))
                polygons[section].append(xy)
                
            color = 1 # on/off
            origin, section_size = self.get_origin_and_section_size(polygons)
            r, t = self.get_transform_to_align_brain(brainManager)
            if r is None:
                continue

            volume = []
            for _, contour_points in polygons.items():
                vertices = np.array(contour_points) - origin[:2]
                contour_points = (vertices).astype(np.int32)
                volume_slice = np.zeros(section_size, dtype=np.uint8)
                volume_slice = cv2.polylines(volume_slice, [contour_points], isClosed=True, color=color, thickness=1)
                volume_slice = cv2.fillPoly(volume_slice, pts=[contour_points], color=color)
                volume.append(volume_slice)
            volume = np.array(volume).astype(np.bool8)
            volume = np.swapaxes(volume,0,2)
            ids, counts = np.unique(volume, return_counts=True)
            new_origin = brain_to_atlas_transform(origin, r, t)
            print(annotator_id, animal, structure.abbreviation, origin, new_origin, section_size, end="\t")
            print(volume.dtype, volume.shape, end="\t")
            print(ids, counts)

            brainMerger.volumes_to_merge[structure.abbreviation].append(volume)
            brainMerger.origins_to_merge[structure.abbreviation].append(new_origin)
            self.save_brain_origins_and_volumes_and_meshes(structure.abbreviation, new_origin, volume)

    def save_brain_origins_and_volumes_and_meshes(self, structure ,origin, volume):
        """Saves everything to disk
        """
        os.makedirs(self.origin_path, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.mesh_path, exist_ok=True)

        aligned_structure = volume_to_polygon(
            volume=volume, origin=origin, times_to_simplify=3)
        origin_filepath = os.path.join(
            self.origin_path, f'{structure}.txt')
        volume_filepath = os.path.join(
            self.volume_path, f'{structure}.npy')
        mesh_filepath = os.path.join(self.mesh_path, f'{structure}.stl')
        np.savetxt(origin_filepath, origin)
        np.save(volume_filepath, volume)
        save_mesh(aligned_structure, mesh_filepath)
