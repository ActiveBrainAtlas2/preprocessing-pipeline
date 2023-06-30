"""
This is the last script for creating the atlas
This will create a precomputed volume of the Active Brain Atlas which
you can import into neuroglancer
"""
import argparse
import os
import sys
import json
import numpy as np
import shutil
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
from pathlib import Path
from scipy.ndimage import center_of_mass
from skimage import io

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.controller.sql_controller import SqlController
from library.controller.structure_com_controller import StructureCOMController

RESOLUTION = 0.325

class NumpyToNeuroglancer():
    viewer = None

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

    def add_segment_properties(self, ids):
        segment_properties = [(number, f'{number}: {number}') for number in ids]

        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')
        self.precomputed_vol.info['segment_properties'] = 'names'
        self.precomputed_vol.commit_info()
        segment_properties_path = os.path.join(self.precomputed_vol.layer_cloudpath.replace('file://', ''), 'names')
        os.makedirs(segment_properties_path, exist_ok=True)
        info = {
            "@type": "neuroglancer_segment_properties",
            "inline": {
                "ids": [str(number) for number, label in segment_properties],
                "properties": [{
                    "id": "label",
                    "type": "label",
                    "values": [str(label) for number, label in segment_properties]
                }]
            }
        }
        with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
            json.dump(info, file, indent=2)

    def add_downsampled_volumes(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')
        tq = LocalTaskQueue(parallel=2)
        tasks = tc.create_downsampling_tasks(self.precomputed_vol.layer_cloudpath, compress=True)
        tq.insert(tasks)
        tq.execute()

    def add_segmentation_mesh(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        tq = LocalTaskQueue(parallel=2)
        tasks = tc.create_meshing_tasks(self.precomputed_vol.layer_cloudpath, mip=0, compress=True) # The first phase of creating mesh
        tq.insert(tasks)
        tq.execute()

        # It should be able to incoporated to above tasks, but it will give a weird bug. Don't know the reason
        tasks = tc.create_mesh_manifest_tasks(self.precomputed_vol.layer_cloudpath) # The second phase of creating mesh
        tq.insert(tasks)
        tq.execute()

class AtlasCreator:
    def __init__(self, atlas_name, debug):
        self.atlas_name = atlas_name
        self.debug = debug
        self.DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
        self.fixed_brain = 'MD589'
        self.INPUT = os.path.join(f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{self.fixed_brain}/preps/CH1/thumbnail_aligned')
        self.ATLAS_PATH = os.path.join(self.DATA_PATH, 'atlas_data', atlas_name)
        self.OUTPUT_DIR = f'/home/httpd/html/data/{atlas}'
        if os.path.exists(self.OUTPUT_DIR):
            shutil.rmtree(self.OUTPUT_DIR)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self.sqlController = SqlController(self.fixed_brain)
        self.to_um = 32 * 0.452
    
    def create_atlas(self):
        # origin is in animal scan_run.resolution coordinates
        # volume is in 10um coo
        SCALE = 10
        width = (self.sqlController.scan_run.width * 0.452) / SCALE
        height = (self.sqlController.scan_run.height * 0.452) / SCALE
        z_length = len(os.listdir(self.INPUT))
        atlas_volume = np.zeros(( int(height), int(width), z_length), dtype=np.uint8)
        color = 100
        origin_dir = os.path.join(self.ATLAS_PATH, 'origin')
        volume_dir = os.path.join(self.ATLAS_PATH, 'structure')
        y_length = 800
        x_length = 1320
        z_length = 1140
        atlas_box_size=(x_length, y_length, z_length)
        
        atlas_box_scales=[10000, 10000, 10000]
        atlas_box_scales = np.array(atlas_box_scales)
        atlas_box_size = np.array(atlas_box_size)
        atlas_box_center = atlas_box_size / 2
        atlas_volume = np.zeros( atlas_box_size, dtype=np.uint8)
        color = 100
        print(f'origin dir {origin_dir}')
        print(f'origin dir {volume_dir}')
        print(f'box center {atlas_box_center}')
        print(f'Using data from {self.ATLAS_PATH}')
        origins = sorted(os.listdir(origin_dir))
        volumes = sorted(os.listdir(volume_dir))
        print(f'Working with {len(origins)} origins and {len(volumes)} volumes.')

        for origin_file, volume_file in zip(origins, volumes):
            assert Path(origin_file).stem == Path(volume_file).stem
            structure = Path(origin_file).stem
            color += 2

            origin = np.loadtxt(os.path.join(origin_dir, origin_file))
            volume = np.load(os.path.join(volume_dir, volume_file))

            volume = np.rot90(volume, axes=(0,1))
            volume = np.flip(volume, axis=0)
            volume[volume > 0.8] = color
            volume = volume.astype(np.uint8)
            x, y, z = origin
            x_start = int(round(x + x_length/2))
            y_start = int(round(y + y_length/2))
            #z_start = int(z) // 2 + atlas_box_size[2] // 2
            z_start = int(round(z + z_length/2))
            x_end = x_start + volume.shape[0]
            y_end = y_start + volume.shape[1]
            #z_end = z_start + (volume.shape[2] + 1) // 2
            z_end = z_start + volume.shape[2]
            #z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
            #volume = volume[:, :, z_indices]
            print(structure, x_start, y_start, z_start)
            
            try:
                atlas_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume
            except ValueError as ve:
                print(f'Error adding {structure} to atlas: {ve}')
        print()
        #ids, counts = np.unique(atlas_volume, return_counts=True)
        print(f'Shape of atlas volume {atlas_volume.shape} dtype={atlas_volume.dtype}')
        save_volume = np.swapaxes(atlas_volume, 0, 2)
        #atlas_volume = np.rot90(atlas_volume, axes=(0, 1))
        print(f'Shape of atlas volume {atlas_volume.shape} after swapping 0 and 2')
        #save_volume = np.swapaxes(save_volume, 1, 2)
        #print(f'Shape of atlas volume {atlas_volume.shape} after swapping 1 and 2')
        outpath = f'/net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/{atlas}.tif'
        io.imsave(outpath, save_volume)
        return
        ng = NumpyToNeuroglancer(atlas_volume, atlas_box_scales, offset=[0,0,0])
        ng.init_precomputed(self.OUTPUT_DIR)
        ng.add_segment_properties(ids)
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Atlas')
    parser.add_argument('--atlas', required=False, default='atlasV8')
    parser.add_argument('--debug', required=False, default='true', type=str)
    args = parser.parse_args()
    debug = bool({'true': True, 'false': False}[args.debug.lower()])    
    atlas = args.atlas
    #atlas = 'atlasV8'
    #debug = False
    atlasCreator = AtlasCreator(atlas, debug)
    atlasCreator.create_atlas()