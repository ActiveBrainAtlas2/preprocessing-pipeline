import numpy as np
from atlas.Atlas import BrainStructureManager
from atlas.VolumeUtilities import VolumeUtilities
from lib.Brain import Brain
from atlas.Atlas import AtlasInitiator,Atlas
from scipy.ndimage import center_of_mass
from skimage.filters import gaussian
from Controllers.SqlController import SqlController

class Assembler(BrainStructureManager):

    def __init__(self,check = True,*arg,**kwarg):
        if check:
            self.load_volumes()
            self.load_origins()

    def initialize_origins_and_volumes(self):
        if not self.origins == {}:
            self.origins = np.array(list(self.origins.values()))
            self.volumes = list(self.volumes.values())

    def calculate_structure_boundary(self):
        shapes = np.array([s.shape for s in self.volumes])
        self.max_bonds = (np.floor(self.origins) + shapes).astype(int)
        self.min_bonds = np.floor(self.origins).astype(int)

    def get_bounding_box(self):
        self.calculate_structure_boundary()
        size = np.floor(np.max(self.max_bonds, axis=0)) + np.array([1, 1, 1])
        size = size.astype(int)
        return size

    def get_structure_boundary(self, structure_id):
        assert(hasattr(self, 'max_bonds'))
        assert(hasattr(self, 'min_bonds'))
        row_start, col_start, z_start = self.min_bonds[structure_id]
        row_end, col_end, z_end = self.max_bonds[structure_id]
        return row_start, col_start, z_start, row_end, col_end, z_end
    
    def get_segment_to_id_where_segment_are_brain_regions(self):
        db_structure_infos = self.sqlController.get_structures_dict()
        segment_to_id = {}
        for structure, (_, number) in db_structure_infos.items():
            segment_to_id[structure] = number
        return segment_to_id

    def assemble_all_structure_volume(self,segment_to_id):
        self.initialize_origins_and_volumes()
        size = self.get_bounding_box()
        size = size + np.array([10, 10, 10])
        self.combined_volume = np.zeros(size, dtype=np.uint8)
        for i in range(len(self.structures)):
            structure = self.structures[i]
            volume = self.volumes[i]
            row_start, col_start, z_start, row_end, col_end, z_end = self.get_structure_boundary(i)
            try:
                structure_id = segment_to_id[structure.split('_')[0]]
            except KeyError:
                structure_id = segment_to_id[structure]
            try:
                self.combined_volume[row_start:row_end, col_start:col_end, z_start:z_end] += volume.astype(np.uint8) * structure_id
            except ValueError as ve:
                print(structure, ve, volume.shape)
        print('Shape of downsampled atlas volume', self.combined_volume.shape)
    
    def plot_combined_volume(self):
        if not hasattr(self, 'combined_volume'):
            self.assemble_all_structure_volume()
        self.plotter.plot_3d_image_stack(self.combined_volume, 2)
    
    def standardize_volumes(self):
        mid_point = self.find_mid_point_from_midline_structures()
        if not np.isnan(mid_point):
            self.mirror_COMs(mid_point)
            self.center_mid_line_structures(mid_point)
        self.mirror_volumes_of_paired_structures()

    def find_mid_point_from_paired_structures(self):
        self.load_origins()
        mid_points = []
        for structure, origin in self.origins.items():
            if '_L' in structure:
                right_structure = structure.split('_')[0] + '_R' 
                structure_width = self.volumes[right_structure].shape[2]
                mid_point = (self.origins[structure][2] + self.origins[right_structure][2]) / 2
                mid_points.append(mid_point + structure_width / 2)
        mid_point = np.mean(mid_points)
        return mid_point

    def center_mid_line_structures(self, mid_point):
        self.load_com()
        for structure, origin in self.COM.items():
            if not '_' in structure:
                self.COM[structure][2] = mid_point

    def find_mid_point_from_midline_structures(self):
        self.load_com()
        mid_points = []
        for structure, origin in self.COM.items():
            if not '_' in structure:
                structure_width = self.volumes[structure].shape[2]
                mid_point = self.COM[structure][2]
                mid_points.append(mid_point)
        mid_point = np.mean(mid_points)
        return mid_point
    
    def mirror_COMs(self, mid_point):
        self.load_com()
        for structure, com_z_right in self.COM.items():
            if '_L' in structure:
                right_structure = structure.split('_')[0] + '_R'
                com_z_right = self.COM[right_structure][2]
                distance = com_z_right - mid_point
                com_z_left = com_z_right - distance * 2
                self.COM[structure][2] = com_z_left
                self.COM[structure][:2] = self.COM[right_structure][:2]
    
    def mirror_volumes_of_paired_structures(self):
        for structure in self.volumes:
            if '_L' in structure:
                structure_right = structure.split('_')[0] + '_R'
                if structure_right in self.volumes:
                    self.volumes[structure] = self.volumes[structure_right][:,:,::-1]


class CustomAssembler(Assembler):

    def __init__(self, animal,*arg,**kwarg):
        Brain.__init__(self, animal,*arg,**kwarg)
        identity = lambda: {}
        self.volumes = {}
        self.origins = {}
        Assembler.__init__(self,*arg,**kwarg)

class BrainAssembler(Assembler):

    def __init__(self, animal, threshold, *args, **kwargs):
        BrainStructureManager.__init__(self, animal, *args, **kwargs)
        self.load_volumes()

        Assembler.__init__(self)


class AtlasAssembler(AtlasInitiator, Assembler):

    def __init__(self, atlas, com_function=None, threshold=0.9, sigma=3.0, conversion_factor=None):
        AtlasInitiator.__init__(self, com_function=com_function, threshold=threshold, sigma=sigma, conversion_factor=conversion_factor)
        self.standardize_volumes()
        self.origins = self.get_origin_from_coms()
        Assembler.__init__(self)    

def get_v7_volume_and_origin():
    atlas = Atlas(atlas = 'atlasV7')
    atlas.load_volumes()
    atlas.load_com()
    volume_coms = np.array([center_of_mass(atlas.volumes[si]) for si in atlas.COM.keys()]).astype(int)
    average_com = np.array(list(atlas.COM.values()))/np.array([10,10,20])
    origins = average_com - volume_coms
    atlas.origins = dict(zip(atlas.COM.keys(),origins))
    sorted_keys = sorted(atlas.volumes.keys())
    for key,value in atlas.volumes.items():
        if key in ['SC','IC']:
            atlas.volumes[key] = gaussian(value,2)>0.1
        else:
            atlas.volumes[key] = gaussian(value,2)>0.5
    atlas.volumes  = dict(zip(sorted_keys,[atlas.volumes[keyi] for keyi in sorted_keys]))
    atlas.origins  = dict(zip(sorted_keys,[atlas.origins[keyi] for keyi in sorted_keys]))
    return atlas.volumes,atlas.origins


def get_assembled_atlas_v7():
    controller = SqlController('DK39')
    atlas = Atlas(atlas = 'atlasV7')
    atlas.get_com_array()
    assembler = Assembler(check=False,side = '_R')
    assembler.volumes,assembler.origins = get_v7_volume_and_origin()
    assembler.sqlController = atlas.sqlController
    assembler.structures = list(assembler.volumes.keys())
    segment_to_id = controller.get_segment_to_id_where_segment_are_brain_regions()
    assembler.assemble_all_structure_volume(segment_to_id)
    return assembler