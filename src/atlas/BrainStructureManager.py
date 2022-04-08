import os
import json
from lib.utilities_atlas import ATLAS
import numpy as np
from Brain import Brain
from atlas.VolumeUtilities import VolumeUtilities
from lib.utilities_atlas_lite import volume_to_polygon
from lib.utilities_atlas_lite import save_mesh
import xml.etree.ElementTree as ET
from collections import defaultdict
from lib.FileLocationManager import DATA_PATH
class BrainStructureManager(Brain, VolumeUtilities):

    def __init__(self, animal,atlas = ATLAS,downsample_factor = 32):
        Brain.__init__(self, animal)
        self.origins = {}
        self.COM = {}
        self.volumes = {}
        self.aligned_contours = {}
        self.thresholded_volumes = {}
        self.atlas = atlas
        self.set_path_and_create_folders()
        self.attribute_functions = dict(
            origins=self.load_origins,
            volumes=self.load_volumes,
            aligned_contours=self.load_aligned_contours,
            structures=self.set_structure, **self.attribute_functions)
        self.DOWNSAMPLE_FACTOR = downsample_factor
        to_um = self.DOWNSAMPLE_FACTOR * self.get_resolution()
        self.pixel_to_um = np.array([to_um, to_um, 20])
        self.um_to_pixel = 1 / self.pixel_to_um

    def set_structure(self):
        possible_attributes_with_structure_list = ['origins', 'COM', 'volumes', 'thresholded_volumes', 'aligned_contours']
        self.set_structure_from_attribute(possible_attributes_with_structure_list)
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(DATA_PATH, 'atlas_data', self.atlas, self.animal)
        self.original_contour_path = os.path.join(self.animal_directory, 'original_structures.json')
        self.padded_contour_path = os.path.join(self.animal_directory, 'unaligned_padded_structures.json')
        self.align_and_padded_contour_path = os.path.join(self.animal_directory, 'aligned_padded_structures.json')
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
            self.set_aligned_contours(json.load(f))

    def set_aligned_contours(self,contours):
        self.aligned_contours = contours
        self.structures = list(self.aligned_contours.keys())  

    def save_contours(self):
        assert(hasattr(self, 'original_structures'))
        assert(hasattr(self, 'centered_structures'))
        assert(hasattr(self, 'aligned_structures'))
        with open(self.original_contour_path, 'w') as f:
            json.dump(self.original_structures, f, sort_keys=True)
        with open(self.padded_contour_path, 'w') as f:
            json.dump(self.centered_structures, f, sort_keys=True)
        with open(self.align_and_padded_contour_path, 'w') as f:
            json.dump(self.aligned_structures, f, sort_keys=True)

    def save_volumes(self):
        self.check_attributes(['volumes', 'structures'])
        os.makedirs(self.volume_path, exist_ok=True)
        for structurei in self.structures:
            volume = self.volumes[structurei]
            volume_filepath = os.path.join(self.volume_path, f'{structurei}.npy')
            np.save(volume_filepath, volume)
    
    def save_mesh_files(self):
        self.check_attributes(['volumes'])
        self.calculate_fixed_brain_center()
        self.COM = self.get_average_coms()
        self.convert_unit_of_com_dictionary(self.COM, self.fixed_brain.um_to_pixel)
        self.origins = self.get_origin_from_coms()
        for structurei in self.structures:
            origin, volume = self.origins[structurei], self.volumes[structurei]
            centered_origin = origin - self.get_origin_array().mean(0)
            aligned_structure = volume_to_polygon(volume=volume, origin=centered_origin , times_to_simplify=3)
            filepath = os.path.join(self.animal_directory, 'mesh', f'{structurei}.stl')
            save_mesh(aligned_structure, filepath)

    def save_origins(self):
        self.check_attributes(['origins', 'structures'])
        os.makedirs(self.origin_path, exist_ok=True)
        for structurei in self.structures:
            x, y, z = self.origins[structurei]
            origin_filepath = os.path.join(self.origin_path, f'{structurei}.txt')
            np.savetxt(origin_filepath, (x, y, z))
    
    def save_coms(self):
        self.check_attributes(['COM', 'structures'])
        for structurei in self.structures:
            if structurei in self.COM:
                coordinates = self.COM[structurei]
                self.sqlController.add_com(prep_id=self.animal, abbreviation=structurei, \
                        coordinates=coordinates)
            else:
                print(f'{structurei} not in self.COM')

    def get_contour_list(self, structurei):
        return list(self.aligned_contours[structurei].values())
    
    def get_origin_array(self):
        self.check_attributes(['origins'])
        return np.array(list(self.origins.values()))
    
    def get_volume_list(self):
        self.check_attributes(['volumes'])
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
        self.check_attributes(['aligned_contours', 'structures'])
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
    
    def calculate_fixed_brain_center(self):
        width = self.sqlController.scan_run.width // 32
        height = self.sqlController.scan_run.height // 32
        depth = self.sqlController.get_section_count(self.fixed_brain.animal)
        self.fixed_brain_center = np.array([width // 2, height // 2, depth // 2])
    
    def load_contours_from_cvat_xml(self,xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        image_layers = [childi for childi in root if childi.tag =='image']
        contours = defaultdict(dict)
        for imagei in image_layers:
            section_name = imagei.attrib['name'].split('.')[0]
            section_contour = defaultdict(list)
            polygons = [childi for childi in imagei if childi.tag =='polygon']
            for polygoni in polygons:
                if polygoni.tag == 'polygon':
                    structure = polygoni.attrib['label']
                    points = polygoni.attrib['points'].split(';')
                    points = np.array([pointi.split(',') for pointi in points]).astype(float)
                    section_contour[structure].append(points)
            for structurei in section_contour:
                contours[structurei][section_name] = np.vstack(section_contour[structurei])
        return contours

