"""
William, this is the last script for creating the atlas

This will create a precomputed volume of the Active Brain Atlas which
you can import into neuroglancer
"""
import os
import numpy as np
from timeit import default_timer as timer
import shutil
from cloudvolume import CloudVolume
from atlas.Atlas import Atlas
from lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer
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

    def create_neuroglancer_files(self,output_dir,segment_properties):
        self.init_precomputed(output_dir)
        self.add_segment_properties(segment_properties)
        self.add_downsampled_volumes()
        self.add_segmentation_mesh()
            
class NgSegmentMaker:
    def __init__(self, debug = False,out_folder = 'atlas_test',offset = None):
        self.offset = offset
        self.start = timer()
        self.OUTPUT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures/'+out_folder
        self.reset_output_path()
        self.debug = debug

    def get_atlas_resolution(self):
        self.fixed_brain = BrainStructureManager('MD589')
        resolution = self.fixed_brain.get_resolution()
        SCALE = 32
        return int(resolution * SCALE * 1000)
    
    def get_animal_resolution(self):
        resolution = self.get_resolution()
        return int(resolution * self.DOWNSAMPLE_FACTOR * 1000)
    
    def reset_output_path(self):
        if os.path.exists(self.OUTPUT_DIR):
            shutil.rmtree(self.OUTPUT_DIR)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def get_segment_properties(self):
        db_structure_infos = self.sqlController.get_structures_dict()
        segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
        return segment_properties

class AtlasNgMaker(Atlas,NgSegmentMaker):
    def __init__(self,atlas_name,debug = False,out_folder = 'atlas_test',threshold = 0.9,sigma = 3.0,offset = None):
        Atlas.__init__(self,atlas_name)
        NgSegmentMaker.__init__(self, debug,out_folder=out_folder,offset=offset)
        self.assembler = AtlasAssembler(atlas_name, threshold=threshold,sigma = sigma)
        self.resolution = self.get_atlas_resolution()
    
    def create_atlas_neuroglancer(self):
        self.volume = self.assembler.combined_volume
        segment_properties = self.get_segment_properties()
        self.create_neuroglancer_files(self.OUTPUT_DIR,segment_properties)

class BrainNgMaker(BrainStructureManager,NgSegmentMaker):
    def __init__(self,animal,debug = False,out_folder = 'animal_folder',threshold = 0.9, *args, **kwargs):
        BrainStructureManager.__init__(self,animal)
        NgSegmentMaker.__init__(self, debug,out_folder=out_folder, *args, **kwargs)
        self.assembler = BrainAssembler(animal,threshold = threshold)
        self.resolution = self.get_animal_resolution()
    
    def create_brain_neuroglancer(self):
        self.volume = self.assembler.combined_volume
        segment_properties = self.get_segment_properties()
        self.create_neuroglancer_files(self.OUTPUT_DIR,segment_properties)

if __name__ == '__main__':
    atlas = 'atlasV8'
    debug = False
    maker = AtlasNgMaker(atlas,debug,threshold=0.9,out_folder = 'new_atlas',sigma = 3.0)
    maker.assembler.assemble_all_structure_volume()
    maker.create_atlas_neuroglancer()