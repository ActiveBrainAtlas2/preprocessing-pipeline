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
from atlas.BrainStructureManager import Atlas,BrainStructureManager
from lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer
PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
from atlas.Assembler import AtlasAssembler, BrainAssembler
from atlas.BrainStructureManager import BrainStructureManager

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

class NgSegmentMaker:
    def get_atlas_resolution(self):
        self.fixed_brain = BrainStructureManager('MD589')
        resolution = self.fixed_brain.get_resolution()
        SCALE = 32
        return int(resolution * SCALE * 1000)
    
    def get_animal_resolution(self):
        resolution = self.get_resolution()
        SCALE = 32
        return int(resolution * SCALE * 1000)
    
    def reset_output_path(self):
        if os.path.exists(self.OUTPUT_DIR):
            shutil.rmtree(self.OUTPUT_DIR)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def get_segment_properties(self):
        db_structure_infos = self.sqlController.get_structures_dict()
        segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
        return segment_properties
    
    def create_neuroglancer_files(self,atlas_volume):
        segment_properties = self.get_segment_properties()
        if not self.debug:
            offset = (np.array(atlas_volume.shape)/2).astype(int)
            ng = NgConverter(atlas_volume, [self.resolution, self.resolution, 20000], offset=offset)
            ng.init_precomputed(self.OUTPUT_DIR)
            ng.add_segment_properties(segment_properties)
            ng.add_downsampled_volumes()
            ng.add_segmentation_mesh()
        print()
        end = timer()
        print(f'Finito! Program took {end - self.start} seconds')

class AtlasNgMaker(Atlas,NgSegmentMaker):
    def __init__(self,atlas_name,debug,out_folder = 'atlas_test',threshold = 0.9):
        Atlas.__init__(self,atlas_name)
        self.assembler = AtlasAssembler(atlas_name, threshold=threshold)
        self.start = timer()
        self.OUTPUT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures/'+out_folder
        self.reset_output_path()
        self.debug = debug
        self.resolution = self.get_atlas_resolution()

class BrainNgMaker(BrainStructureManager,NgSegmentMaker):
    def __init__(self,animal,debug,out_folder = 'animal_folder'):
        BrainStructureManager.__init__(self,animal)
        self.assembler = BrainAssembler(animal)
        self.start = timer()
        self.OUTPUT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures/'+out_folder
        self.reset_output_path()
        self.debug = debug
        self.resolution = self.get_animal_resolution()

if __name__ == '__main__':
    atlas = 'atlasV8'
    debug = False
    maker = AtlasNgMaker(atlas,debug,threshold=0.9)
    maker.assembler.assemble_all_structure_volume()
    atlas_volume = maker.assembler.combined_volume
    maker.create_neuroglancer_files(atlas_volume)