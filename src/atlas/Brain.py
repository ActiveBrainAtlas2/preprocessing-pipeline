import os
import json
from lib.file_location import DATA_PATH
from lib.utilities_atlas import ATLAS
from lib.sqlcontroller import SqlController
import numpy as np
from lib.utilities_atlas_lite import volume_to_polygon, save_mesh
from lib.file_location import FileLocationManager
from Plotter import Plotter
class Brain:
    def __init__(self,animal):
        self.animal = animal
        self.sqlController = SqlController(self.animal)
        self.origins = {}
        self.COM = {}
        self.volumes = {}
        self.aligned_contours = {}
        self.thresholded_volumes = {}
        self.set_path_and_create_folders()
        self.plotter = Plotter()
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(DATA_PATH, 'atlas_data', ATLAS, self.animal)
        self.original_contour_path = os.path.join(self.animal_directory,  'original_structures.json')
        self.padded_contour_path = os.path.join(self.animal_directory,  'unaligned_padded_structures.json')
        self.align_and_padded_contour_path = os.path.join(self.animal_directory,  'aligned_padded_structures.json')
        self.volume_path = os.path.join(self.animal_directory, 'structure')
        self.origin_path = os.path.join(self.animal_directory, 'origin')
        os.makedirs(self.animal_directory, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.origin_path, exist_ok=True)

    def load_com(self):
        self.COM = self.sqlController.get_centers_dict(self.animal)

    def load_origins(self):
        assert(os.path.exists(self.origin_path))
        origin_files = sorted(os.listdir(self.origin_path))
        for filei in origin_files:
            structure = os.path.splitext(filei)[0]    
            self.origins[structure] = np.loadtxt(os.path.join(self.origin_path, filei))
    
    def load_volumes(self):
        assert(os.path.exists(self.volume_path))
        volume_files = sorted(os.listdir(self.volume_path))
        for filei in volume_files:
            structure = os.path.splitext(filei)[0]    
            self.volumes[structure] = np.load(os.path.join(self.volume_path, filei))
    
    def load_aligned_contours(self):
        with open(self.align_and_padded_contour_path) as f:
            self.aligned_contours = json.load(f)
        self.structures = list(self.aligned_contours.keys())        
    
    def save_contours(self):
        assert(hasattr(self,'original_structures'))
        assert(hasattr(self,'centered_structures'))
        assert(hasattr(self,'aligned_structures'))
        with open(self.original_contour_path, 'w') as f:
            json.dump(self.original_structures, f, sort_keys=True)
        with open(self.padded_contour_path, 'w') as f:
            json.dump(self.centered_structures, f, sort_keys=True)
        with open(self.align_and_padded_contour_path, 'w') as f:
            json.dump(self.aligned_structures, f, sort_keys=True)

    def save_volumes(self):
        assert(hasattr(self,'volumes'))
        self.set_structures_from_attribute('volumes')
        for structurei in self.structures:
            volume = self.volumes[structurei]
            volume_filepath = os.path.join(self.volume_path, f'{structurei}.npy')
            np.save(volume_filepath, volume)
    
    def save_mesh_files(self):
        assert(hasattr(self,'volumes'))
        assert(hasattr(self,'origins'))
        self.set_structures_from_attribute('volumes')
        self.threshold_volumes()
        for structurei in self.structures:
            origin,volume = self.origins[structurei],self.thresholded_volumes[structurei]
            centered_origin = origin - self.fixed_brain_center
            aligned_structure = volume_to_polygon(volume=volume,origin = centered_origin ,times_to_simplify=3)
            filepath = os.path.join(self.animal_directory, 'mesh', f'{structurei}.stl')
            save_mesh(aligned_structure, filepath)

    def save_origins(self):
        assert(hasattr(self,'origins'))
        self.set_structures_from_attribute('origins')
        for structurei in self.structures:
            x, y, z = self.origins[structurei]
            origin_filepath = os.path.join(self.origin_path, f'{structurei}.txt')
            np.savetxt(origin_filepath, (x,y,z))
    
    def set_structures_from_attribute(self,attribute):
        if not hasattr(self,'structures'):
            self.structures = getattr(self,attribute).keys()
    
    def save_coms(self):
        assert(hasattr(self,'COM'))
        self.set_structures_from_attribute('COM')
        for structurei in self.structures:
            coordinates = self.COM[structurei]
            self.sqlController.add_com(prep_id = self.animal,abbreviation = structurei,coordinates= coordinates)

    def get_contour_list(self,structurei):
        return list(self.aligned_contours[structurei].values())

    def get_com_array(self):
        assert(hasattr(self,'COM'))
        return np.array(list(self.COM.values()))
    
    def get_origin_array(self):
        assert(hasattr(self,'origins'))
        return np.array(list(self.origins.values()))
    
    def get_resolution(self):
        return self.sqlController.scan_run.resolution
    
    def get_image_dimension(self):
        width = self.sqlController.scan_run.width
        height = self.sqlController.scan_run.height
        return np.array([width,height])
    
    def get_volume_list(self):
        assert(hasattr(self,'volumes'))
        return np.array(list(self.volumes.values()))

    def plot_volume_3d(self,structure='10N_L'):
        volume = self.volumes[structure]
        self.plotter.plot_3d_boolean_array(volume)

    def plot_volume_stack(self,structure='10N_L'):
        volume = self.volumes[structure]
        self.plotter.plot_3d_image_stack(volume,2)
    
    def compare_structure_vs_contour(self,structure='10N_L'):
        self.plotter.set_show_as_false()
        volume = self.volumes[structure]
        contour = self.get_contour_list(structure)
        self.plotter.compare_contour_and_stack(contour,volume)
        self.plotter.show()
        self.plotter.set_show_as_true()

class Atlas(Brain):
    def __init__(self,atlas = ATLAS):
        self.atlas = atlas
        self.fixed_brain = FileLocationManager('MD589')
        super().__init__('Atlas')
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(DATA_PATH, 'atlas_data', self.atlas)
        self.volume_path = os.path.join(self.animal_directory, 'structure')
        self.origin_path = os.path.join(self.animal_directory, 'origin')
        os.makedirs(self.animal_directory, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.origin_path, exist_ok=True)
    
    def create_atlas_contours(self):
        ...
    
    def display_atlas_contours(self):
        ...

    def load_atlas(self):
        self.load_origins()
        self.load_volumes()
    
    def threshold_volumes(self):
        assert(hasattr(self,'volumes'))
        assert(hasattr(self,'threshold'))
        self.set_structures_from_attribute('volumes')
        for structurei in self.structures:
            volume = self.volumes[structurei]
            if not volume[volume > 0].size == 0:
                threshold = np.quantile(volume[volume > 0], self.threshold)
            else:
                threshold = 0.5
            self.thresholded_volumes[structurei] = volume > threshold