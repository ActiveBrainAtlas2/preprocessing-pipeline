import os
import json
from lib.file_location import DATA_PATH
from lib.utilities_atlas import ATLAS
import numpy as np
from lib.utilities_atlas_lite import volume_to_polygon, save_mesh
from Brain import Brain
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama
from abakit.registration.utilities import get_similarity_transformation_from_dicts
from atlas.VolumeUtilities import VolumeUtilities
class BrainStructureManager(Brain,VolumeUtilities):
    def __init__(self,animal):
        Brain.__init__(self,animal)
        VolumeUtilities.__init__(self)
        self.origins = {}
        self.COM = {}
        self.volumes = {}
        self.aligned_contours = {}
        self.thresholded_volumes = {}
        self.set_path_and_create_folders()
        to_um = 32 * self.get_resolution()
        self.pixel_to_um = np.array([to_um,to_um,20])
        self.um_to_pixel = 1/self.pixel_to_um
        self.attribute_functions = dict(
            origins = self.load_origins,
            volumes = self.load_volumes,
            aligned_contours = self.load_aligned_contours,
            structures = self.set_structure,**self.attribute_functions)

    def set_structure(self):
        possible_attributes_with_structure_list = ['origins','COM','volumes','thresholded_volumes','aligned_contours']
        self.set_structure_from_attribute(possible_attributes_with_structure_list)
    
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
        os.makedirs(self.volume_path, exist_ok=True)
        for structurei in self.structures:
            volume = self.volumes[structurei]
            volume_filepath = os.path.join(self.volume_path, f'{structurei}.npy')
            np.save(volume_filepath, volume)
    
    def save_mesh_files(self):
        self.check_attributes(['volumes','origins','structures'])
        filepath = os.path.join(self.animal_directory, 'mesh')
        os.makedirs(filepath, exist_ok=True)
        for structurei in self.structures:
            origin,volume = self.origins[structurei],self.volumes[structurei]
            centered_origin = origin - self.fixed_brain_center
            aligned_structure = volume_to_polygon(volume=volume,origin = centered_origin ,times_to_simplify=3)
            outfile = os.path.join(filepath, f'{structurei}.stl')
            save_mesh(aligned_structure, outfile)

    def save_origins(self):
        self.check_attributes(['origins','structures'])
        os.makedirs(self.origin_path, exist_ok=True)
        for structurei in self.structures:
            x, y, z = self.origins[structurei]
            origin_filepath = os.path.join(self.origin_path, f'{structurei}.txt')
            np.savetxt(origin_filepath, (x,y,z))
    
    def save_coms(self):
        self.check_attributes(['COM','structures'])
        for structurei in self.structures:
            if structurei in self.COM:
                coordinates = self.COM[structurei]
                self.sqlController.add_com(prep_id = self.animal,abbreviation = structurei,\
                        coordinates= coordinates)
                print(f'adding com from {self.animal}')
            else:
                print(f'{structurei} not in self.COM')

    def get_contour_list(self,structurei):
        return list(self.aligned_contours[structurei].values())

    
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
        self.check_attributes(['aligned_contours','structures'])
        all_structures = []
        for structurei in self.structures:
            contour = self.aligned_contours[structurei]
            data = self.plotter.get_contour_data(contour,down_sample_factor=100)
            all_structures.append(data)
        all_structures = np.vstack(all_structures)
        self.plotter.plot_3d_scatter(all_structures,marker=dict(size=3,opacity=0.5),title = self.animal)
    
    def turn_volume_into_boolean(self):
        for structure, volume in self.volumes.items():
            self.volumes[structure] = volume.astype(np.bool8)

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
    
    def save_mesh_files(self):
        self.check_attributes(['volumes'])
        self.origins = self.get_average_coms()
        self.convert_unit_of_com_dictionary(self.origins, self.um_to_pixel)
        for structurei in self.structures:
            origin,volume = self.origins[structurei],self.volumes[structurei]
            centered_origin = origin - self.fixed_brain_center
            aligned_structure = volume_to_polygon(volume=volume,origin = centered_origin ,times_to_simplify=3)
            filepath = os.path.join(self.animal_directory, 'mesh', f'{structurei}.stl')
            save_mesh(aligned_structure, filepath)
    
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