"""
William, this is the last script for creating the atlas

This will create a precomputed volume of the Active Brain Atlas which
you can import into neuroglancer
"""
import os
import sys
import numpy as np
from timeit import default_timer as timer
import shutil
from cloudvolume import CloudVolume
from pathlib import Path
from Brain import Atlas,Brain
from src.lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer
PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
from lib.sqlcontroller import SqlController



class NgConverter(NumpyToNeuroglancer):

    def __init__(self, volume, scales, offset=[0, 0, 0], layer_type='segmentation'):
        self.volume = volume
        self.scales = scales
        self.offset = offset
        self.layer_type = layer_type
        self.precomputed_vol = None

    def init_precomputed(self, path):
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[3] if len(self.volume.shape) > 3 else 1,
            layer_type = self.layer_type,
            data_type = str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',                    # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset,          # x,y,z offset in voxels from the origin
            chunk_size = [64,64,64],           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=True)
        self.precomputed_vol.commit_info()
        self.precomputed_vol[:, :, :] = self.volume[:, :, :]

class NgSegmentMaker(Atlas):
    def __init__(self,atlas_name,debug):
        super().__init__(atlas_name)
        self.start = timer()
        self.threshold = 0.9
        self.OUTPUT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures/atlas_test'
        self.reset_output_path()
        self.load_origins()
        self.load_volumes()
        self.resolution = self.get_resolution()
        self.set_structure()
        self.center_origins()
        self.threshold_volumes()
        self.volumes = list(self.thresholded_volumes.values())
        self.debug = debug
    
    def reset_output_path(self):
        if os.path.exists(self.OUTPUT_DIR):
            shutil.rmtree(self.OUTPUT_DIR)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def center_origins(self):
        self.origins = self.get_origin_array()
        self.origins = self.origins - self.origins.min(0)

    def get_resolution(self):
        self.fixed_brain = Brain('MD589')
        resolution = self.fixed_brain.get_resolution()
        SCALE = 32
        return int(resolution * SCALE * 1000)

    def get_db_structure_infos(self):
        sqlController = SqlController('MD589')
        db_structures = sqlController.get_structures_dict()
        structures = {}
        for structure, v in db_structures.items():
            if '_' in structure:
                structure = structure[0:-2]
            structures[structure] = v
        return structures

    def get_structure_dictionary(self):
        db_structure_infos = self.get_db_structure_infos()
        structure_to_id = {}
        for structure, (_, number) in db_structure_infos.items():
            structure_to_id[structure] = number
        return structure_to_id

    def get_segment_properties(self):
        db_structure_infos = self.get_db_structure_infos()
        segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
        return segment_properties

    def get_bounding_box(self,origins,volumes):
        shapes = np.array([str.shape for str in volumes])
        max_bonds = origins + shapes
        size_max = np.round(np.max(max_bonds,axis=0))+np.array([1,1,1])
        size_min = origins.min(0)
        size = size_max-size_min
        size = size.astype(int)
        return size

    def center_origins(self,structure_volume_origin):
        coms = np.array([ str[1] for _,str in structure_volume_origin.items()])
        return coms - coms.min(0)

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


    def create_atlas_volume(self,atlas_name, debug):
        structure_to_id = self.get_structure_dictionary()
        size = self.get_bounding_box(self.origins,self.volumes)
        self.atlas_volume = np.zeros(size, dtype=np.uint8)
        print(f'{atlas_name} volume shape', self.atlas_volume.shape)
        print()
        for i in range(len(self.structures)):
            structure = self.structures[i]
            volume = self.volumes[i]
            row_start,col_start,z_start,row_end,col_end,z_end = self.get_structure_boundary(structure,i)
            try:
                structure_id = structure_to_id[structure.split('_')[0]]
                self.atlas_volume[row_start:row_end, col_start:col_end, z_start:z_end] += volume.astype(np.uint8)*structure_id
            except ValueError as ve:
                print(structure, ve, volume.shape)
        print('Shape of downsampled atlas volume', self.atlas_volume.shape)
        print('Resolution at', self.resolution)
    
    def create_neuroglancer_files(self):
        segment_properties = self.get_segment_properties()
        if not self.debug:
            offset = (self.atlas_volume.shape/2).astype(int)
            ng = NgConverter(self.atlas_volume, [self.resolution, self.resolution, 20000], offset=offset)
            ng.init_precomputed(self.OUTPUT_DIR)
            ng.add_segment_properties(segment_properties)
            ng.add_downsampled_volumes()
            ng.add_segmentation_mesh()
        print()
        end = timer()
        print(f'Finito! Program took {end - self.start} seconds')

if __name__ == '__main__':
    atlas = 'atlasV8'
    debug = False
    maker = NgSegmentMaker(atlas,debug)
    maker.create_atlas_volume()
    maker.create_neuroglancer_files()