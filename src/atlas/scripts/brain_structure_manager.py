import os
import json
import numpy as np
import xml.etree.ElementTree as ET
from collections import defaultdict

from library.utilities.brain import Brain
from library.utilities.utilities_contour import check_dict
from library.utilities.volume_utilities import VolumeUtilities
from library.utilities.atlas import volume_to_polygon, save_mesh
from library.registration.utilities_registration import SCALING_FACTOR

atlas = 'atlasV8'
data_path = '/net/birdstore/Active_Atlas_Data/data_root'

class BrainStructureManager(Brain, VolumeUtilities):

    def __init__(self, animal, atlas = atlas, downsample_factor = SCALING_FACTOR, check_path = True):
        self.DOWNSAMPLE_FACTOR = downsample_factor
        Brain.__init__(self,animal)
        to_um = self.DOWNSAMPLE_FACTOR * self.get_resolution()
        self.pixel_to_um = np.array([to_um, to_um, 20])
        self.um_to_pixel = 1 / self.pixel_to_um
        self.origins = {}
        self.COM = {}
        self.volumes = {}
        self.structures = []
        self.aligned_contours = {}
        self.thresholded_volumes = {}
        self.atlas = atlas
        if check_path:
            self.set_path_and_create_folders()        
    
    def set_path_and_create_folders(self):
        self.animal_directory = os.path.join(data_path, 'atlas_data', self.atlas, self.animal)
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
            self.set_structures(list(self.origins.keys()))
        
    def load_volumes(self):
        if not hasattr(self,'volumes'):
            self.volumes = {}
        assert(os.path.exists(self.volume_path))
        volume_files = sorted(os.listdir(self.volume_path))
        for filei in volume_files:
            structure = os.path.splitext(filei)[0]    
            if structure not in self.volumes:
                self.volumes[structure] = np.load(os.path.join(self.volume_path, filei))
        self.set_structures(list(self.volumes.keys()))
        
        
    def load_aligned_contours(self):        
        print(self.align_and_padded_contour_path)
        with open(self.align_and_padded_contour_path) as f:
            self.set_aligned_contours(json.load(f))
            self.set_structures(list(self.aligned_contours.keys()))

    def set_aligned_contours(self, contours):
        self.aligned_contours = contours

    def set_structures(self, structures):
        self.structures = structures

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
        assert hasattr(self, 'volumes')
        assert hasattr(self, 'structures')
        os.makedirs(self.volume_path, exist_ok=True)
        for structurei in self.structures:
            volume = self.volumes[structurei]
            volume_filepath = os.path.join(self.volume_path, f'{structurei}.npy')
            print(volume_filepath)
            np.save(volume_filepath, volume)

    def save_mesh_files(self):
        assert hasattr(self,'volumes')
        self.calculate_fixed_brain_center()
        self.COM = self.get_average_coms()
        self.convert_unit_of_com_dictionary(self.COM, self.fixed_brain.um_to_pixel)
        self.origins = self.get_origin_from_coms()

        for structure in self.volumes.keys():
            if structure in self.origins:
                #print('save mesh',structurei)
                #if structurei in self.origins:
                origin = self.origins[structure]
                volume = self.volumes[structure]
                centered_origin = origin - self.get_origin_array().mean(0)
                aligned_structure = volume_to_polygon(volume=volume, origin=centered_origin , times_to_simplify=3)
                filepath = os.path.join(self.animal_directory, 'mesh', f'{structure}.stl')
                print(filepath)
                save_mesh(aligned_structure, filepath)
            else:
                print(f'structure={structure} is not in self.origins')

    def save_origins(self):
        self.origins = self.get_origin_from_coms()
        print('save origins', len(self.origins), type(self.origins))
        assert hasattr(self, 'origins')
        self.set_structures(list(self.origins.values()))
        os.makedirs(self.origin_path, exist_ok=True)

        
        for structure in self.origins.keys():
            x, y, z = self.origins[structure]
            origin_filepath = os.path.join(self.origin_path, f'{structure}.txt')
            if 'SC' in structure:
                print(origin_filepath)
            np.savetxt(origin_filepath, (x, y, z))
    
    def save_coms(self):
        self.load_com()
        self.set_structures(list(self.COM.values()))
        check_dict(self.COM, 'self.COM')
        
        for structure in self.structures:
            if structure in self.COM.keys():
                coordinates = self.COM[structure]
                self.sqlController.add_com(prep_id=self.animal, abbreviation=structure, \
                        coordinates=coordinates)
            else:
                print(f'{structure} not in self.COM keys')

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

    def get_segment_properties(self,structures_to_include = None):
        db_structure_infos = self.sqlController.get_structure_description_and_color()
        if structures_to_include is None:
            segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
        else:
            segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items() if structure in structures_to_include]
        return segment_properties