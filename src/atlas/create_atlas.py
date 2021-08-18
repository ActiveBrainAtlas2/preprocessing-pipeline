"""
This will create a precomputed volume of the Active Brain Atlas which
you can import into neuroglancer
"""
import argparse
import os
import sys
import json
import numpy as np
from timeit import default_timer as timer
import shutil
import neuroglancer
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)

# from lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_properties
from lib.sqlcontroller import SqlController

RESOLUTION = 0.325
OUTPUT_DIR = '../atlas_ng/'


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

    def preview(self, layer_name=None, clear_layer=False):
        if self.viewer is None:
            self.viewer = neuroglancer.Viewer()

        if layer_name is None:
            layer_name = f'{self.layer_type}_{self.scales}'

        source = neuroglancer.LocalVolume(
            data=self.volume,
            dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='nm', scales=self.scales),
            voxel_offset=self.offset
        )

        if self.layer_type == 'segmentation':
            layer = neuroglancer.SegmentationLayer(source=source)
        else:
            layer = neuroglancer.ImageLayer(source=source)

        with self.viewer.txn() as s:
            if clear_layer:
                s.layers.clear()
            s.layers[layer_name] = layer

        print(f'A new layer named {layer_name} is added to:')
        print(self.viewer)

    def init_precomputed(self, path):
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[3] if len(self.volume.shape) > 3 else 1,
            layer_type = self.layer_type,
            data_type = str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',                    # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset,          # x,y,z offset in voxels from the origin
            chunk_size = [64, 64, 64],           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=False, progress=False)
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

        tq = LocalTaskQueue(parallel=4)
        tasks = tc.create_downsampling_tasks(self.precomputed_vol.layer_cloudpath, compress=False)
        tq.insert(tasks)
        tq.execute()

    def add_segmentation_mesh(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        tq = LocalTaskQueue(parallel=4)
        tasks = tc.create_meshing_tasks(self.precomputed_vol.layer_cloudpath, mip=0, compress=False) # The first phase of creating mesh
        tq.insert(tasks)
        tq.execute()

        # It should be able to incoporated to above tasks, but it will give a weird bug. Don't know the reason
        tasks = tc.create_mesh_manifest_tasks(self.precomputed_vol.layer_cloudpath) # The second phase of creating mesh
        tq.insert(tasks)
        tq.execute()


def create_atlas(create, atlas_name):
    start = timer()
    DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
    ORIGIN_PATH = os.path.join(ATLAS_PATH, 'origin')
    VOLUME_PATH = os.path.join(ATLAS_PATH, 'structure')
    OUTPUT_DIR = os.path.join(ATLAS_PATH, 'atlas')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    origin_files = sorted(os.listdir(ORIGIN_PATH))
    volume_files = sorted(os.listdir(VOLUME_PATH))
    sqlController = SqlController('MD589')
    resolution = sqlController.scan_run.resolution
    surface_threshold = 0.01
    SCALE = (10 / resolution)

    structure_volume_origin = {}
    for volume_filename, origin_filename in zip(volume_files, origin_files):
        structure = os.path.splitext(volume_filename)[0]
        if structure not in origin_filename:
            print(structure, origin_filename)
            break

        try:
            color = sqlController.get_structure_color(structure)
        except:
            color = 100

        origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
        volume = np.load(os.path.join(VOLUME_PATH, volume_filename))

        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)
        volume[volume > 0] = color
        volume = volume.astype(np.uint8)
        print(volume.dtype, np.amax(volume), np.mean(volume), np.median(volume))

        structure_volume_origin[structure] = (volume, origin)

    col_length = 1000
    row_length = 1000
    z_length = 300
    atlas_volume = np.zeros(( int(row_length), int(col_length), z_length), dtype=np.uint8)
    print(f'{atlas_name} volume shape', atlas_volume.shape)

    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        x, y, z = origin
        x_start = int( round(x + col_length / 2))
        y_start = int( round(y + row_length / 2))
        z_start = int(z) // 2 + z_length // 2
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) // 2

        if not create and 'SC' in structure:
            print(str(structure).ljust(7),end=": ")
            print('Origin',
                  str(round(x)).rjust(4),
                  str(round(y)).rjust(4),
                  str(round(z)).rjust(4),
                  'start',
                  str(x_start).rjust(4),
                  str(y_start).rjust(4),
                  str(z_start).rjust(4),
                  'end',
                  str(x_end).rjust(4),
                  str(y_end).rjust(4),
                  str(z_end).rjust(4))


        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        #volume = np.swapaxes(volume, 0, 1)

        try:
            atlas_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume
        except ValueError as ve:
            print(ve, end=" ")


    resolution = int(resolution * 1000 * SCALE)
    #print('Shape of downsampled atlas volume', atlas_volume.shape)
    #print('Resolution at', resolution)

    if create:
        #offset =  [21959.308659539533, 6238.690939678455, 66.74432595997823]
        #atlasV7_volume = np.rot90(atlasV7_volume, axes=(0, 1))
        #atlasV7_volume = np.fliplr(atlasV7_volume)
        #atlasV7_volume = np.flipud(atlasV7_volume)
        #atlasV7_volume = np.fliplr(atlasV7_volume)


        offset = [0,0,0]
        
        ng = NumpyToNeuroglancer(atlas_volume, [resolution, resolution, 20000], offset=offset)
        ng.init_precomputed(OUTPUT_DIR)
        
        ng.add_segment_properties(get_segment_properties())
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()

    outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.npz')
    np.savez(outpath, atlas_volume.astype(np.uint8))

    end = timer()
    #print(f'Finito! Program took {end - start} seconds')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Atlas')
    parser.add_argument('--atlas', required=True)
    parser.add_argument('--create', required=False, default='false')
    args = parser.parse_args()
    create = bool({'true': True, 'false': False}[args.create.lower()])    
    atlas = args.atlas
    create_atlas(create, atlas)
    



    