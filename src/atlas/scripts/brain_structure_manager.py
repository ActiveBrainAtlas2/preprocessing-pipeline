import os
import json
import numpy as np
from collections import defaultdict
import cv2
from scipy.ndimage.measurements import center_of_mass


from library.utilities.utilities_contour import check_dict
from library.utilities.atlas import volume_to_polygon, save_mesh
from library.registration.utilities_registration import SCALING_FACTOR
from library.controller.sql_controller import SqlController
from library.registration.affine_registration import AffineRegistration
from library.utilities.atlas import singular_structures, symmetricalize_volume
from library.controller.structure_com_controller import StructureCOMController
from library.image_manipulation.filelocation_manager import data_path
from library.utilities.volume2contour import average_masks
from library.utilities.algorithm import brain_to_atlas_transform, umeyama



atlas = 'atlasV8'
data_path = '/net/birdstore/Active_Atlas_Data/data_root'

class BrainStructureManager():

    def __init__(self, animal, atlas = atlas, downsample_factor = SCALING_FACTOR):
        self.DOWNSAMPLE_FACTOR = downsample_factor
        self.animal = animal
        
        self.coms = {}
        self.origins = {}
        self.COM = {}
        self.volumes = {}
        self.structures = []
        self.aligned_contours = {}
        self.thresholded_volumes = {}
        self.atlas = atlas
        self.fixed_brain = None
        self.moving_brains = []
        self.sqlController = SqlController('MD589')
        to_um = self.DOWNSAMPLE_FACTOR * self.sqlController.scan_run.resolution
        self.pixel_to_um = np.array([to_um, to_um, 20])
        self.um_to_pixel = 1 / self.pixel_to_um
        self.threshold = 0.8
        self.volumes_to_merge = defaultdict(list)
        self.origins_to_merge = defaultdict(list)
        self.registrator = AffineRegistration()
        self.symmetry_list = singular_structures
        self.data_path = os.path.join(data_path, 'atlas_data')
        self.animal_directory = os.path.join(self.data_path, self.animal)
        self.aligned_and_padded_contour_path = os.path.join(self.animal_directory, 'aligned_padded_structures.json')
        self.volume_path = os.path.join(self.data_path, atlas, 'structure')
        self.origin_path = os.path.join(self.data_path, atlas, 'origin')
        self.mesh_path = os.path.join(self.data_path, atlas, 'mesh')

    def get_com_array(self):
        """Get the center of mass values for this brain as an array

        Returns:
            np array: COM of the brain
        """
        #self.load_com()
        controller = StructureCOMController(self.animal)
        self.COM = controller.get_COM(self.animal)
        return np.array(list(self.COM.values()))

    def get_transform_to_align_brain(self, brain):
        """Used in aligning data to fixed brain
        """
        
        moving_com = (brain.get_com_array()*self.um_to_pixel).T
        fixed_com = (self.fixed_brain.get_com_array()*self.um_to_pixel).T
        
        print(f'moving brain={brain.animal} data={moving_com.shape}')
        print(f'fixed brain={self.fixed_brain.animal} data={fixed_com.shape}')
        r, t = umeyama(moving_com, fixed_com)
        return r, t

    def load_aligned_contours(self):
        """load aligned contours
        """       
        
        print(f'Loading JSON data from {self.aligned_and_padded_contour_path}')
        with open(self.aligned_and_padded_contour_path) as f:
            self.aligned_contours = json.load(f)
            self.set_structures(list(self.aligned_contours.keys()))

    def set_structures(self, structures):
        """set structures from origins or volumes
        """
        
        self.structures = structures

    def get_contour_list(self, structurei):
        return list(self.aligned_contours[structurei].values())
    
    def get_origin_array(self):
        self.load_origins()
        return np.array(list(self.origins.values()))
    
    def get_volume_list(self):
        self.load_volumes()
        return np.array(list(self.volumes.values()))

    def plot_volume_3d(self, structure='10N_L'):
        volume = self.volumes[structure]
        self.plotter.plot_3d_boolean_array(volume)

    def plot_volume_stack(self, structure='10N_L'):
        volume = self.volumes[structure]
        self.plotter.plot_3d_image_stack(volume, 2)
    
    def compare_structure_vs_contour(self, structure='10N_L'):
        self.plotter.set_show_as_false()
        volume = self.volumes[structure]
        contour = self.get_contour_list(structure)
        self.plotter.compare_contour_and_stack(contour, volume)
        self.plotter.show()
        self.plotter.set_show_as_true()

    def plot_contours_for_all_structures(self):
        self.load_aligned_contours()
        all_structures = []
        for structurei in self.structures:
            contour = self.aligned_contours[structurei]
            data = self.plotter.get_contour_data(contour, down_sample_factor=100)
            all_structures.append(data)
        all_structures = np.vstack(all_structures)
        self.plotter.plot_3d_scatter(all_structures, marker=dict(size=3, opacity=0.5), title=self.animal)
    
    def turn_volume_into_boolean(self):
        for structure, volume in self.volumes.items():
            self.volumes[structure] = volume.astype(np.bool8)

    def get_segment_properties(self,structures_to_include = None):
        db_structure_infos = self.sqlController.get_structure_description_and_color()
        if structures_to_include is None:
            segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
        else:
            segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items() if structure in structures_to_include]
        return segment_properties


    def load_data(self, brains):
        """Loads origins, volumes and COMs from all brains
        """

        for brain in brains:
            self.load_origins(brain)
            self.load_volumes(brain)
            self.load_com(brain)


    def load_origins(self, brain):
        """Load origins
        """
        origin_path = os.path.join(self.data_path, brain.animal, 'origin')
        print(f'load_origins from {origin_path}')
        assert(os.path.exists(origin_path))
        origin_files = sorted(os.listdir(origin_path))
        for f in origin_files:
            structure = os.path.splitext(f)[0]    
            brain.origins[structure] = np.loadtxt(os.path.join(origin_path, f))
            brain.set_structures(list(self.origins.keys()))
        
    def load_volumes(self, brain):
        """load volumes
        """
        volume_path = os.path.join(self.data_path, brain.animal, 'structure')
        print(f'load volumes from {volume_path}')
        assert(os.path.exists(volume_path))


        if not hasattr(self,'volumes'):
            self.volumes = {}
        assert(os.path.exists(volume_path))
        volume_files = sorted(os.listdir(volume_path))
        for f in volume_files:
            structure = os.path.splitext(f)[0]
            #if structure not in self.volumes:
            brain.volumes[structure] = np.load(os.path.join(volume_path, f))
        brain.set_structures(list(self.volumes.keys()))

    def load_com(self, brain):
        """load the com attribute of this brain indexed by each region
        imported from brain.py
        """

        # if not hasattr(self, "COM"):
        #self.COM = self.sqlController.get_COM(self.animal, 2)
        controller = StructureCOMController(brain.animal)
        brain.COM = controller.get_COM(brain.animal)


    def load_data_from_fixed_and_moving_brains(self):
        """Loads data from the 3 foundation brains
        """

        for structure in self.fixed_brain.origins:            
            if structure == 'RtTg':
                braini = self.moving_brains[0]
                origin = braini.origins[structure]
                volume = braini.volumes[structure]
                r, t = self.get_transform_to_align_brain(braini)
                origin = brain_to_atlas_transform(origin, r, t)
            else:
                origin = self.fixed_brain.origins[structure]
                volume = self.fixed_brain.volumes[structure]
            if 'SC' in structure:
                print(f'SC origin in load fixed brain is {origin}')
            self.volumes_to_merge[structure].append(volume)
            self.origins_to_merge[structure].append(origin)
        for brain in self.moving_brains:
            brain.transformed_origins = {}
            r, t = self.get_transform_to_align_brain(brain)
            for structure in brain.origins:
                origin, volume = brain.origins[structure], brain.volumes[structure]
                if 'SC' in structure:
                    print(f'SC origin in load moving brain is {origin}')
                aligned_origin = brain_to_atlas_transform(origin, r, t)
                brain.transformed_origins[structure] = aligned_origin
                brain.transformed_origins[structure] = origin
                self.volumes_to_merge[structure].append(volume)
                self.origins_to_merge[structure].append(aligned_origin)
                #self.origins_to_merge[structure].append(origin)
        print(f'load_data_from_fixed_and_moving_brains len={len(self.origins_to_merge)}')
    
    ##### import from volume maker
    def calculate_origin_and_volume_for_one_segment(self, segment, interpolate=0):
        """Gets called every segment
        """

        segment_contours = self.aligned_contours[segment]
        segment_contours = self.sort_contours(segment_contours)
        origin, section_size = self.get_origin_and_section_size(segment_contours)
        volume = []
        for _, contour_points in segment_contours.items():
            vertices = np.array(contour_points) - origin[:2]
            contour_points = (vertices).astype(np.int32)
            volume_slice = np.zeros(section_size, dtype=np.uint8)
            volume_slice = cv2.polylines(volume_slice, [contour_points], isClosed=True, color=1, thickness=1)
            volume_slice = cv2.fillPoly(volume_slice, pts=[contour_points], color=1)
            volume.append(volume_slice)
        volume = np.array(volume).astype(np.bool8)
        volume = np.swapaxes(volume,0,2)
        for i in range(interpolate):
            print(f'interpolate {i}')
            volume, origin = self.interpolate_volumes(volume,origin)
        self.origins[segment] = origin 
        self.volumes[segment] = volume

    def test_origin_and_volume_for_one_segment(self, segment):
        """testing segment
        SC thumbnail_aligned should be x=760, y=350, z=128
        SC thumbnail should be x=590, y=220  
        """
        if 'SC' in segment:

            segment_contours = self.aligned_contours[segment]
            segment_contours = self.sort_contours(segment_contours)
            origin, section_size = self.get_origin_and_section_size(segment_contours)
            volume = []
            for _, contour_points in segment_contours.items():
                vertices = np.array(contour_points) - origin[:2]
                contour_points = (vertices).astype(np.int32)
                volume_slice = np.zeros(section_size, dtype=np.uint8)
                volume_slice = cv2.polylines(volume_slice, [contour_points], isClosed=True, color=1, thickness=1)
                volume_slice = cv2.fillPoly(volume_slice, pts=[contour_points], color=1)
                volume.append(volume_slice)
            volume = np.array(volume).astype(np.bool8)
            volume = np.swapaxes(volume,0,2)
            ids, counts = np.unique(volume, return_counts=True)
            print(f'SC dtype={volume.dtype} ids={ids} counts={counts}')
            print(f'SC shape={volume.shape}')
            print(f'COM={center_of_mass(volume)} {origin}')


    def get_origin_and_section_size(self, segment_contours):
        """Gets the origin and section size
        Set the pad to make sure we get all the volume
        """
        pad = 50
        section_mins = []
        section_maxs = []
        for _, contour_points in segment_contours.items():
            contour_points = np.array(contour_points)
            section_mins.append(np.min(contour_points, axis=0))
            section_maxs.append(np.max(contour_points, axis=0))
        min_z = min([int(i) for i in segment_contours.keys()])
        min_x, min_y = np.min(section_mins, axis=0)
        max_x, max_y = np.max(section_maxs, axis=0)
        max_x += pad
        max_y += pad
        xspan = max_x - min_x
        yspan = max_y - min_y
        origin = np.array([min_x, min_y, min_z])
        section_size = np.array([xspan, yspan]).astype(int)
        return origin, section_size

    def compute_origins_and_volumes_for_all_segments(self, interpolate=0):
        """compute_origins_and_volumes_for_all_segments
        """
        
        self.origins = {}
        self.volumes = {}
        self.segments = self.aligned_contours.keys()
        for segment in self.segments:
            self.calculate_origin_and_volume_for_one_segment(segment, interpolate=interpolate)

    def test_origins_and_volumes_for_all_segments(self, interpolate=0):
        """compute_origins_and_volumes_for_all_segments
        """
        
        self.origins = {}
        self.volumes = {}
        self.segments = self.aligned_contours.keys()
        for segment in self.segments:
            self.test_origin_and_volume_for_one_segment(segment)

    def save_atlas_origins_and_volumes_and_meshes(self):
        """Saves everything to disk
        """
        os.makedirs(self.origin_path, exist_ok=True)    
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.mesh_path, exist_ok=True)

        #width = self.sqlController.scan_run.width // 32
        #height = self.sqlController.scan_run.height // 32
        #depth = self.sqlController.get_section_count(self.fixed_brain)
        #fixed_brain_center = np.array([width // 2, height // 2, depth // 2])
        
        #self.COM = self.get_average_coms()
        #self.convert_unit_of_com_dictionary(self.COM, fixed_brain.um_to_pixel)
        #####self.origins = self.get_origin_from_coms()
        self.origins = {structure:np.mean(origin, axis=0) for structure, origin in self.origins_to_merge.items() }
        assert hasattr(self, 'origins')
        self.set_structures(list(self.origins.values()))
        origin_keys = self.origins.keys()
        volume_keys = self.volumes.keys()
        shared_structures = set(origin_keys).intersection(volume_keys)
        for structure in shared_structures:
            if structure in origin_keys and structure in volume_keys:
                x, y, z = self.origins[structure]
                volume = self.volumes[structure]
                #centered_origin = (x,y,z) - self.get_origin_array().mean(0)
                centered_origin = (x,y,z)
                aligned_structure = volume_to_polygon(volume=volume, origin=centered_origin , times_to_simplify=3)
                origin_filepath = os.path.join(self.origin_path, f'{structure}.txt')
                volume_filepath = os.path.join(self.volume_path, f'{structure}.npy')
                mesh_filepath = os.path.join(self.mesh_path, f'{structure}.stl')
                if 'SC' in structure:
                    print(origin_filepath)
                    print(volume_filepath)
                    print(mesh_filepath)
                np.savetxt(origin_filepath, (x, y, z))
                np.save(volume_filepath, volume)
                save_mesh(aligned_structure, mesh_filepath)
            else:
                print(f'structure={structure} is not in self.origins or self.volumes')

    def save_brain_origins_and_volumes_and_meshes(self):
        """Saves brain data to disk
        """
        origin_path = os.path.join(self.data_path, self.animal, 'origin')
        os.makedirs(origin_path, exist_ok=True)
        print(f'saving origins to {origin_path}')
        
        volume_path = os.path.join(self.data_path, self.animal, 'structure')
        os.makedirs(volume_path, exist_ok=True)
        print(f'saving volumes to {volume_path}')
        
        mesh_path = os.path.join(self.data_path, self.animal, 'mesh')
        os.makedirs(mesh_path, exist_ok=True)
        print(f'saving meshes to {mesh_path}')

        assert hasattr(self, 'origins')
        assert hasattr(self, 'volumes')
        self.set_structures(list(self.origins.values()))
        origin_keys = self.origins.keys()
        volume_keys = self.volumes.keys()
        shared_structures = set(origin_keys).intersection(volume_keys)
        for structure in shared_structures:
            x, y, z = self.origins[structure]
            volume = self.volumes[structure]
            centered_origin = (x,y,z)
            aligned_structure = volume_to_polygon(volume=volume, origin=centered_origin , times_to_simplify=3)
            origin_filepath = os.path.join(origin_path, f'{structure}.txt')
            volume_filepath = os.path.join(volume_path, f'{structure}.npy')
            mesh_filepath = os.path.join(mesh_path, f'{structure}.stl')
            if 'SC' in structure:
                print(origin_filepath)
                print(volume_filepath)
                print(mesh_filepath)
            np.savetxt(origin_filepath, (x, y, z))
            np.save(volume_filepath, volume)
            save_mesh(aligned_structure, mesh_filepath)
        else:
            print(f'structure={structure} is not in self.origins or self.volumes')


    def save_coms(self):
        """save COMs to DB
        """
        
        self.load_com()
        self.set_structures(list(self.COM.values()))
        check_dict(self.COM, 'self.COM')
        return
        for structure in self.structures:
            if structure in self.COM.keys():
                coordinates = self.COM[structure]
                self.sqlController.add_com(prep_id=self.animal, abbreviation=structure, \
                        coordinates=coordinates)
            else:
                print(f'{structure} not in self.COM keys')

    
    def get_COM_in_pixels(self,structurei):
        com = np.array(center_of_mass(self.volumes[structurei]))
        return (com+self.origins[structurei])
    
    def sort_contours(self,contour_for_segmenti):
        sections = [int(section) for section in contour_for_segmenti]
        section_order = np.argsort(sections)
        keys = np.array(list(contour_for_segmenti.keys()))[section_order]
        values = np.array(list(contour_for_segmenti.values()), dtype=object)[section_order]
        return dict(zip(keys,values))

    
    def interpolate_volumes(self,volume,origin):
        nsections = volume.shape[2]
        origin = np.array(origin)
        origin = origin*np.array([1,1,2])
        interpolated = np.zeros((volume.shape[0],volume.shape[1],2*nsections))
        for sectioni in range(nsections):
            interpolated[:,:,sectioni*2] = volume[:,:,sectioni]
            if sectioni > 0:
                next = interpolated[:,:,sectioni*2]
                last = interpolated[:,:,sectioni*2-2]
                interpolated[:,:,sectioni*2-1] = average_masks(next,last)
        return interpolated,origin    
    
   