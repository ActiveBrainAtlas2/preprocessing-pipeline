"""
William, this is the last script for creating the atlas

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
from scipy.ndimage.measurements import center_of_mass


PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())


from lib.SqlController import SqlController

RESOLUTION = 0.325


def get_db_structure_infos():
    sqlController = SqlController('MD589')
    db_structures = sqlController.get_structures_dict()
    structures = {}
    for structure, v in db_structures.items():
        if '_' in structure:
            structure = structure[0:-2]
        structures[structure] = v
    return structures

def get_known_foundation_structure_names():
    known_foundation_structures = ['MVePC', 'DTgP', 'VTA', 'Li', 'Op', 'Sp5C', 'RPC', 'MVeMC', 'APT', 'IPR',
                                   'Cb', 'pc', 'Amb', 'SolIM', 'Pr5VL', 'IPC', '8n', 'MPB', 'Pr5', 'SNR',
                                   'DRD', 'PBG', '10N', 'VTg', 'R', 'IF', 'RR', 'LDTg', '5TT', 'Bar',
                                   'Tz', 'IO', 'Cu', 'SuVe', '12N', '6N', 'PTg', 'Sp5I', 'SNC', 'MnR',
                                   'RtTg', 'Gr', 'ECu', 'DTgC', '4N', 'IPA', '3N', '7N', 'LC', '7n',
                                   'SC', 'LPB', 'EW', 'Pr5DM', 'VCA', '5N', 'Dk', 'DTg', 'LVe', 'SpVe',
                                   'MVe', 'LSO', 'InC', 'IC', 'Sp5O', 'DC', 'Pn', 'LRt', 'RMC', 'PF',
                                   'VCP', 'CnF', 'Sol', 'IPL', 'X', 'AP', 'MiTg', 'DRI', 'RPF', 'VLL']
    return known_foundation_structures

def get_segment_properties(all_known=False):
    db_structure_infos = get_db_structure_infos()
    known_foundation_structure_names = get_known_foundation_structure_names()
    non_db_structure_names = [structure for structure in known_foundation_structure_names if structure not in db_structure_infos.keys()]

    segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
    if all_known:
        segment_properties += [(len(db_structure_infos) + index + 1, structure) for index, structure in enumerate(non_db_structure_names)]

    return segment_properties

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

    def add_segment_properties(self, segment_properties):
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

class AtlasCreater:
    def __init__(self, atlas_name, debug):
        self.atlas_name = atlas_name
        self.debug = debug
        self.DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
        self.fixed_brain = 'MD589'
        self.INPUT = os.path.join(f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{self.fixed_brain}/preps/CH1/thumbnail')
        self.ATLAS_PATH = os.path.join(self.DATA_PATH, 'atlas_data', atlas_name)
        self.VOLUME_PATH = os.path.join(self.ATLAS_PATH, 'structure')
        #self.OUTPUT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures/atlas_test'
        self.OUTPUT_DIR = '/home/httpd/html/data/atlas'
        if os.path.exists(self.OUTPUT_DIR):
            shutil.rmtree(self.OUTPUT_DIR)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self.sqlController = SqlController(self.fixed_brain)
        self.to_um = 32 * 0.452
    
    def create_atlas(self):
        # origin is in animal scan_run.resolution coordinates
        # volume is in 10um coo
        volume_files = sorted(os.listdir(self.VOLUME_PATH))
        SCALE = 10
        resolution = np.array([SCALE, SCALE, 20])
        
        com_dict_um = self.sqlController.get_centers_dict('Atlas', input_type_id=1, person_id=16)
        width = (self.sqlController.scan_run.width * 0.452) / SCALE
        height = (self.sqlController.scan_run.height * 0.452) / SCALE
        z_length = len(os.listdir(self.INPUT))
        atlas_volume = np.zeros(( int(height), int(width), z_length), dtype=np.uint8)
        
        for volume_filename in volume_files:
            structure = os.path.splitext(volume_filename)[0]
            try:
                com_um = com_dict_um[structure]
            except:
                print(f'{structure} not in dictionary')
                continue
            
            com_ng = (com_um / resolution)
            volume = np.load(os.path.join(self.VOLUME_PATH, volume_filename))
            try:
                color = self.sqlController.get_structure_color(structure)
            except:
                color = 100
            max_quantile = 0.8
            threshold = np.quantile(volume[volume > 0], max_quantile)

            volume[volume >= threshold] = color
            volume[volume < color] = 0
            volume = volume.astype(np.uint8)
            z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
            volume = volume[:, :, z_indices]

            ndcom = center_of_mass(volume)
            colshift = ndcom[1]
            rowshift = ndcom[0]
            zshift = ndcom[2]
            com_shift = np.array([colshift, rowshift, zshift])
            com_shift = np.array([0, 0, 0])
            mincol, minrow, minz = (com_ng - com_shift) 
            row_start = int( round(minrow) ) 
            col_start = int( round(mincol) )
            z_start = int( round(minz) )
            row_end = row_start + volume.shape[0]
            col_end = col_start + volume.shape[1]
            z_end = z_start + volume.shape[2]
            
            print(structure, mincol, minrow, minz, com_um, com_ng)
            
            if debug and 'SC' in structure:
                print(str(structure).ljust(7),end=": ")
                print('Start',
                      str(row_start).rjust(4),
                      str(col_start).rjust(4),
                      str(z_start).rjust(4),
                      'End',
                      str(row_end).rjust(4),
                      str(col_end).rjust(4),
                      str(z_end).rjust(4))
                
            try:
                atlas_volume[row_start:row_end, col_start:col_end, z_start:z_end] += volume
            except ValueError as ve:
                print(structure, ve)
        print()
        print('Shape of downsampled atlas volume', atlas_volume.shape)
        print('Resolution', resolution)
        if not self.debug:
            atlas_volume = np.rot90(atlas_volume, axes=(0, 1))
            atlas_volume = np.fliplr(atlas_volume)
            atlas_volume = np.flipud(atlas_volume)
            atlas_volume = np.fliplr(atlas_volume)
            ng = NumpyToNeuroglancer(atlas_volume, [10000, 10000, 20000], offset=[0,0,0])
            ng.init_precomputed(self.OUTPUT_DIR)
            ng.add_segment_properties(get_segment_properties())
            ng.add_downsampled_volumes()
            ng.add_segmentation_mesh()
        print()
        print(f'Finito!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Atlas')
    parser.add_argument('--atlas', required=False, default='atlasV8')
    parser.add_argument('--debug', required=False, default='true')
    args = parser.parse_args()
    debug = bool({'true': True, 'false': False}[args.debug.lower()])    
    atlas = args.atlas
    #atlas = 'atlasV8'
    #debug = False
    atlasCreator = AtlasCreater(atlas, debug)
    atlasCreator.create_atlas()