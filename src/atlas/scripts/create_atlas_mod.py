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
        self.VOLUME_PATH = os.path.join(self.ATLAS_PATH, 'structure')
        self.OUTPUT_DIR = f'/home/httpd/html/data/{atlas}'
        if os.path.exists(self.OUTPUT_DIR):
            shutil.rmtree(self.OUTPUT_DIR)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self.sqlController = SqlController(self.fixed_brain)
        self.to_um = 32 * 0.452
    
    def create_atlasXXX(self):
        # origin is in animal scan_run.resolution coordinates
        # volume is in 10um coo
        volume_files = sorted(os.listdir(self.VOLUME_PATH))
        SCALE = 10
        resolution = np.array([SCALE, SCALE, 20])
        controller = StructureCOMController('Atlas')        
        com_dict_um = controller.get_annotation_dict('Atlas', annotator_id=16)
        width = (self.sqlController.scan_run.width * 0.452) / SCALE
        height = (self.sqlController.scan_run.height * 0.452) / SCALE
        z_length = len(os.listdir(self.INPUT))
        atlas_volume = np.zeros(( int(height), int(width), z_length), dtype=np.uint8)
        color = 100
        for volume_filename in volume_files:
            structure = os.path.splitext(volume_filename)[0]
            try:
                com_um = com_dict_um[structure]
            except:
                print(f'{structure} not in dictionary')
                continue
            
            com_ng = (com_um / resolution)
            volumepath = os.path.join(self.VOLUME_PATH, volume_filename)
            volume = np.load(volumepath)
            color += 2
            max_quantile = 0.8
            threshold = np.quantile(volume[volume > 0], max_quantile)

            volume[volume >= threshold] = color
            volume[volume != color] = 0
            volume = volume.astype(np.uint8)
            z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
            volume = volume[:, :, z_indices]

            ndcom = center_of_mass(volume)
            colshift = ndcom[1]
            rowshift = ndcom[0]
            zshift = ndcom[2]
            com_shift = np.array([colshift, rowshift, zshift])
            #com_shift = np.array([0, 0, 0])
            mincol, minrow, minz = (com_ng - com_shift) 
            row_start = int( round(minrow) ) 
            col_start = int( round(mincol) )
            z_start = int( round(minz) )
            row_end = row_start + volume.shape[0]
            col_end = col_start + volume.shape[1]
            z_end = z_start + volume.shape[2]
            print(structure, mincol, minrow, minz, com_um, com_ng, color)                
            try:
                atlas_volume[row_start:row_end, col_start:col_end, z_start:z_end,] += volume
            except ValueError as ve:
                print(f'Error adding {structure} to atlas: {ve}')
        print()
        print('Resolution', resolution)
        ids, counts = np.unique(atlas_volume, return_counts=True)
        outpath = f'/net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/{atlas}.tif'
        print(f'Shape of atlas volume {atlas_volume.shape} dtype={atlas_volume.dtype}')
        atlas_volume = np.swapaxes(atlas_volume, 0, 2)
        print(f'Shape of atlas volume {atlas_volume.shape} after swapping 0 and 2')
        atlas_volume = np.swapaxes(atlas_volume, 1, 2)
        print(f'Shape of atlas volume {atlas_volume.shape} after swapping 1 and 2')
        ng = NumpyToNeuroglancer(atlas_volume, [10000, 10000, 20000], offset=[0,0,0])
        ng.init_precomputed(self.OUTPUT_DIR)
        ng.add_segment_properties(ids)
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()

    
    def create_atlas(self):
        # origin is in animal scan_run.resolution coordinates
        # volume is in 10um coo
        volume_files = sorted(os.listdir(self.VOLUME_PATH))
        SCALE = 10
        resolution = np.array([SCALE, SCALE, 20])
        controller = StructureCOMController('Atlas')        
        com_dict_um = controller.get_annotation_dict('Atlas', annotator_id=16)
        width = (self.sqlController.scan_run.width * 0.452) / SCALE
        height = (self.sqlController.scan_run.height * 0.452) / SCALE
        z_length = len(os.listdir(self.INPUT))
        atlas_volume = np.zeros(( int(height), int(width), z_length), dtype=np.uint8)
        color = 100
        atlas_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/atlas_data/Atlas')
        origin_dir = atlas_dir / 'origin'
        volume_dir = atlas_dir / 'structure'
        size = 1000
        atlas_box_size=(size, size, 300)
        
        atlas_box_scales=[10000, 10000, 20000]
        atlas_box_scales = np.array(atlas_box_scales)
        atlas_box_size = np.array(atlas_box_size)
        atlas_box_center = atlas_box_size / 2
        atlas_volume = np.zeros( atlas_box_size, dtype=np.uint8)
        color = 100
        print(f'box center {atlas_box_center}')

        for origin_file, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
            assert origin_file.stem == volume_file.stem
            name = origin_file.stem
            color += 2

            origin = np.loadtxt(origin_file)
            volume = np.load(volume_file)

            volume = np.rot90(volume, axes=(0,1))
            volume = np.flip(volume, axis=0)
            volume[volume > 0.8] = color
            volume = volume.astype(np.uint8)
            x, y, z = origin
            x_start = int(x) + size//2
            y_start = int(y) + size//2
            z_start = int(z) // 2 + atlas_box_size[2] // 2
            x_end = x_start + volume.shape[0]
            y_end = y_start + volume.shape[1]
            z_end = z_start + (volume.shape[2] + 1) // 2
            z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
            volume = volume[:, :, z_indices]
            print(name,x_start, y_start, z_start)

            try:
                atlas_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume
            except ValueError as ve:
                print(f'Error adding {name} to atlas: {ve}')
        print()
        
        ids, counts = np.unique(atlas_volume, return_counts=True)
        print(f'Shape of atlas volume {atlas_volume.shape} dtype={atlas_volume.dtype}')
        #save_volume = np.swapaxes(atlas_volume, 0, 2)
        #print(f'Shape of atlas volume {atlas_volume.shape} after swapping 0 and 2')
        #save_volume = np.swapaxes(save_volume, 1, 2)
        #outpath = f'/net/birdstore/Active_Atlas_Data/data_root/brains_info/registration/{atlas}.tif'
        #io.imsave(outpath, save_volume)
        #return
        print(f'Shape of atlas volume {atlas_volume.shape} after swapping 1 and 2')
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