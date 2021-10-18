import numpy as np

from src.atlas.Brain import Brain,Atlas

class Assembler:

    def get_bounding_box(self):
        shapes = np.array([str.shape for str in self.volumes])
        max_bonds = self.origins + shapes
        size_max = np.round(np.max(max_bonds,axis=0))+np.array([1,1,1])
        size_min = self.origins.min(0)
        size = size_max-size_min
        size = size.astype(int)
        return size

    def get_structure_boundary(self,structure,structure_id):
        origin = self.origins[structure_id]
        volume = self.volumes[structure_id]
        minrow,mincol, z = origin
        row_start = int( round(minrow))
        col_start = int( round(mincol))
        z_start = int( round(z))
        row_end = row_start + volume.shape[0]
        col_end = col_start + volume.shape[1]
        z_end = z_start + volume.shape[2]
        if self.debug and 'SC' in structure:
            print(str(structure).ljust(7),end=": ")
            print('Start',
                str(row_start).rjust(4),
                str(col_start).rjust(4),
                str(z_start).rjust(4),
                'End',
                str(row_end).rjust(4),
                str(col_end).rjust(4),
                str(z_end).rjust(4))
        return row_start,col_start,z_start,row_end,col_end,z_end
    
    def print(self):
        print(self.a)

    def assemble_all_structure_volume(self):
        self.check_attributes(['volumes','structures','origins'])
        structure_to_id = self.sqlController.get_structures_dict()
        size = self.get_bounding_box()
        self.combined_volume = np.zeros(size, dtype=np.uint8)
        print(f'{self.atlas} volume shape', self.combined_volume.shape)
        print()
        for i in range(len(self.structures)):
            structure = self.structures[i]
            volume = self.volumes[i]
            row_start,col_start,z_start,row_end,col_end,z_end = self.get_structure_boundary(structure,i)
            try:
                structure_id = structure_to_id[structure.split('_')[0]]
                self.combined_volume[row_start:row_end, col_start:col_end, z_start:z_end] += volume.astype(np.uint8)*structure_id
            except ValueError as ve:
                print(structure, ve, volume.shape)
        print('Shape of downsampled atlas volume', self.combined_volume.shape)
        print('Resolution at', self.resolution)
    

class BrainAssembler(Brain,Assembler):
    ...

class AtlasAssembler(Atlas,Assembler):
    ...
    