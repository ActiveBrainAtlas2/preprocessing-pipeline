import numpy as np
from atlas.BrainStructureManager import BrainStructureManager,Atlas
from skimage.filters import gaussian

class Assembler:
    def __init__(self):
        self.check_attributes(['volumes','structures','origins'])
        self.origins = np.array(list(self.origins.values()))
        self.gaussian_filter_volumes(sigma = 3.0)
        self.volumes = list(self.volumes.values())
        margin = np.array([s.shape for s in self.volumes]).max()+100
        self.origins = self.origins - self.origins.min() + margin
    
    def gaussian_filter_volumes(self,sigma):
        for structure, volume in self.volumes.items():
            self.volumes[structure] = gaussian(volume,sigma)

    def calculate_structure_boundary(self):
        shapes = np.array([str.shape for str in self.volumes])
        self.max_bonds = (np.floor(self.origins -self.origins.min(0))+ shapes).astype(int)
        self.min_bonds = np.floor(self.origins-self.origins.min(0)).astype(int)

    def get_bounding_box(self):
        self.calculate_structure_boundary()
        size = np.floor(np.max(self.max_bonds,axis=0))+np.array([1,1,1])
        size = size.astype(int)
        return size

    def get_structure_boundary(self,structure_id):
        assert(hasattr(self,'max_bonds'))
        assert(hasattr(self,'min_bonds'))
        row_start,col_start, z_start = self.min_bonds[structure_id]
        row_end,col_end,z_end = self.max_bonds[structure_id]
        return row_start,col_start,z_start,row_end,col_end,z_end
    
    def get_structure_dictionary(self):
        db_structure_infos =self.sqlController.get_structures_dict()
        structure_to_id = {}
        for structure, (_, number) in db_structure_infos.items():
            structure_to_id[structure] = number
        return structure_to_id

    def assemble_all_structure_volume(self):
        structure_to_id = self.get_structure_dictionary()
        size = self.get_bounding_box()
        size = size +np.array([10,10,10])
        self.combined_volume = np.zeros(size, dtype=np.uint8)
        for i in range(len(self.structures)):
            structure = self.structures[i]
            volume = self.volumes[i]
            row_start,col_start,z_start,row_end,col_end,z_end = self.get_structure_boundary(i)
            try:
                structure_id = structure_to_id[structure.split('_')[0]]
            except KeyError:
                structure_id = structure_to_id[structure]
            try:
                self.combined_volume[row_start:row_end, col_start:col_end, z_start:z_end] += volume.astype(np.uint8)*structure_id
            except ValueError as ve:
                print(structure, ve, volume.shape)
                breakpoint()
        print('Shape of downsampled atlas volume', self.combined_volume.shape)
    
    def plot_combined_volume(self):
        if not hasattr(self,'combined_volume'):
            self.assemble_all_structure_volume()
        self.plotter.plot_3d_image_stack(self.combined_volume,2)

class BrainAssembler(BrainStructureManager,Assembler):
    def __init__(self,animal):
        BrainStructureManager.__init__(self,animal)
        Assembler.__init__(self)


class AtlasAssembler(Atlas,Assembler):
    def __init__(self,atlas,threshold = 0.9):
        Atlas.__init__(self,atlas)
        self.threshold = threshold
        self.threshold_volumes()
        self.volumes = self.thresholded_volumes
        self.COM = self.get_average_coms()
        self.convert_unit_of_com_dictionary(self.COM,self.fixed_brain.um_to_pixel)
        self.standardize_atlas()
        self.origins = self.get_origin_from_coms()
        Assembler.__init__(self)
    
    def standardize_atlas(self):
        mid_point = self.find_mid_point_from_midline_structures()
        self.mirror_COMs(mid_point)
        self.center_mid_line_structures(mid_point)
        self.mirror_volumes_of_paired_structures()

    def find_mid_point_from_paired_structures(self):
        self.check_attributes(['origins'])
        mid_points = []
        for structure,origin in self.origins.items():
            if '_L' in structure:
                right_structure = structure.split('_')[0]+'_R' 
                structure_width = self.volumes[right_structure].shape[2]
                mid_point = (self.origins[structure][2] +self.origins[right_structure][2])/2
                mid_points.append(mid_point+structure_width/2)
        mid_point = np.mean(mid_points)
        return mid_point

    def center_mid_line_structures(self,mid_point):
        self.check_attributes(['COM'])
        for structure, origin in self.COM.items():
            if not '_' in structure:
                self.COM[structure][2] = mid_point

    def find_mid_point_from_midline_structures(self):
        self.check_attributes(['COM'])
        mid_points = []
        for structure, origin in self.COM.items():
            if not '_' in structure:
                structure_width = self.volumes[structure].shape[2]
                mid_point = self.COM[structure][2]
                mid_points.append(mid_point)
        mid_point = np.mean(mid_points)
        return mid_point
    
    def mirror_COMs(self,mid_point):
        self.check_attributes(['COM'])
        for structure,com_z_right in self.COM.items():
            if '_L' in structure:
                right_structure = structure.split('_')[0]+'_R'
                com_z_right = self.COM[right_structure][2]
                distance = com_z_right - mid_point
                com_z_left = com_z_right - distance *2
                self.COM[structure][2] = com_z_left
                self.COM[structure][:2] = self.COM[right_structure][:2]
    
    def mirror_volumes_of_paired_structures(self):
        for structure in self.volumes:
            if '_L' in structure:
                structure_right = structure.split('_')[0]+'_R'
                self.volumes[structure] = self.volumes[structure_right][:,:,::-1]

