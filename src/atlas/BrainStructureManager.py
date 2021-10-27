import os
import json
from lib.file_location import DATA_PATH,FileLocationManager
from lib.utilities_atlas import ATLAS
import numpy as np
from lib.utilities_atlas_lite import volume_to_polygon, save_mesh
from Brain import Brain

class BrainStructureManager(Brain):
    def __init__(self,animal):
        super().__init__(animal)
        self.origins = {}
        self.COM = {}
        self.volumes = {}
        self.aligned_contours = {}
        self.thresholded_volumes = {}
        self.set_path_and_create_folders()
        self.attribute_functions = dict(
            origins = self.load_origins,
            COM = self.load_com,
            volumes = self.load_volumes,
            aligned_contours = self.load_aligned_contours,
            structures = self.set_structure)

    def set_structure(self):
        possible_attributes_with_structure_list = ['origins','COM','volumes','thresholded_volumes','aligned_contours']
        loaded_attributes = []
        for attributei in possible_attributes_with_structure_list:
            if hasattr(self,attributei) and getattr(self,attributei) != {}:
                if not hasattr(self,'structures'):
                    structures = self.get_structures_from_attribute(attributei)
                    self.structures = structures
                loaded_attributes.append(attributei)
        for attributei in loaded_attributes:
            assert(self.structures==self.get_structures_from_attribute(attributei))
        if loaded_attributes == []:
            self.load_origins()
            self.structures = self.origins.keys()
    
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
        self.check_attributes(['volumes','structures'])
        for structurei in self.structures:
            volume = self.volumes[structurei]
            volume_filepath = os.path.join(self.volume_path, f'{structurei}.npy')
            np.save(volume_filepath, volume)
    
    def save_mesh_files(self):
        self.check_attributes(['volumes','origins','structures'])
        for structurei in self.structures:
            origin,volume = self.origins[structurei],self.volumes[structurei]
            centered_origin = origin - self.fixed_brain_center
            aligned_structure = volume_to_polygon(volume=volume,origin = centered_origin ,times_to_simplify=3)
            filepath = os.path.join(self.animal_directory, 'mesh', f'{structurei}.stl')
            save_mesh(aligned_structure, filepath)

    def save_origins(self):
        self.check_attributes(['origins','structures'])
        for structurei in self.structures:
            x, y, z = self.origins[structurei]
            origin_filepath = os.path.join(self.origin_path, f'{structurei}.txt')
            np.savetxt(origin_filepath, (x,y,z))
    
    def get_structures_from_attribute(self,attribute):
        return list(getattr(self,attribute).keys())
    
    def save_coms(self):
        self.check_attributes(['COM','structures'])
        for structurei in self.structures:
            coordinates = self.COM[structurei]
            self.sqlController.add_com(prep_id = self.animal,abbreviation = structurei,coordinates= coordinates)

    def get_contour_list(self,structurei):
        return list(self.aligned_contours[structurei].values())

    def get_com_array(self):
        self.check_attributes(['COM'])
        return np.array(list(self.COM.values()))
    
    def get_origin_array(self):
        self.check_attributes(['origins'])
        return np.array(list(self.origins.values()))
    
    def get_volume_list(self):
        self.check_attributes(['volumes'])
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

    def plot_contours_for_all_structures(self):
        self.check_attributes(['aligned_contours'])
        self.set_structure()
        all_structures = []
        for structurei in self.structures:
            contour = self.aligned_contours[structurei]
            data = self.plotter.get_contour_data(contour,down_sample_factor=100)
            all_structures.append(data)
        all_structures = np.vstack(all_structures)
        self.plotter.plot_3d_scatter(all_structures,marker=dict(size=3,opacity=0.5),title = self.animal)

class Atlas(BrainStructureManager):
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
        self.check_attributes(['volumes','structures'])
        assert(hasattr(self,'threshold'))
        self.get_structures_from_attribute('volumes')
        for structurei in self.structures:
            volume = self.volumes[structurei]
            if not volume[volume > 0].size == 0:
                threshold = np.quantile(volume[volume > 0], self.threshold)
            else:
                threshold = 0.5
            self.thresholded_volumes[structurei] = volume > threshold