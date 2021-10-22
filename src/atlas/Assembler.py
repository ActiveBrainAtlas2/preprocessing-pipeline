import numpy as np

from atlas.BrainStructureManager import BrainStructureManager,Atlas

class Assembler:
    def __init__(self):
        self.check_attributes(['volumes','structures','origins'])
        self.origins = np.array(list(self.origins.values()))
        self.volumes = list(self.volumes.values())

    def calculate_structure_boundary(self):
        shapes = np.array([str.shape for str in self.volumes])
        self.max_bonds = np.round(self.origins + shapes-self.origins.min(0)).astype(int)
        self.min_bonds = np.round(self.origins-self.origins.min(0)).astype(int)

    def get_bounding_box(self):
        self.calculate_structure_boundary()
        size = np.round(np.max(self.max_bonds,axis=0))+np.array([1,1,1])
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
    def __init__(self,atlas):
        Atlas.__init__(self,atlas)
        self.threshold = 0.9
        self.threshold_volumes()
        self.volumes = self.thresholded_volumes
        Assembler.__init__(self)
    