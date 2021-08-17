"""
This will create a precomputed volume of the Active Brain Atlas which
you can import into neuroglancer
"""
import argparse
import os
import sys
import numpy as np
from timeit import default_timer as timer
import shutil
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)

from lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_properties
from lib.sqlcontroller import SqlController

RESOLUTION = 0.325
OUTPUT_DIR = '../atlas_ng/'


def create_atlas(create):
    start = timer()
    atlas_name = 'atlasV8'
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
    surface_threshold = 0.8
    SCALE = (10 / resolution)

    structure_volume_origin = {}
    for volume_filename, origin_filename in zip(volume_files, origin_files):
        structure = os.path.splitext(volume_filename)[0]
        if structure not in origin_filename:
            print(structure, origin_filename)
            break

        color = sqlController.get_structure_color(structure)

        origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
        volume = np.load(os.path.join(VOLUME_PATH, volume_filename))

        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)
        volume[volume > surface_threshold] = color
        volume = volume.astype(np.uint8)

        structure_volume_origin[structure] = (volume, origin)

    col_length = 1000
    row_length = 1000
    z_length = 300
    atlas_volume = np.zeros(( int(row_length), int(col_length), z_length), dtype=np.uint8)
    print('atlas volume shape', atlas_volume.shape)

    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        print(str(structure).ljust(7),end=": ")
        x, y, z = origin
        x_start = int( round(x + col_length / 2))
        y_start = int( round(y + row_length / 2))
        z_start = int(z) // 2 + z_length // 2
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) // 2

        print('Row range',
              str(y_start).rjust(4),
              str(y_end).rjust(4),
              'col range',
              str(x_start).rjust(4),
              str(x_end).rjust(4),
              'z range',
              str(z_start).rjust(4),
              str(z_end).rjust(4),
              end=" ")


        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        #volume = np.swapaxes(volume, 0, 1)

        try:
            atlas_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume
        except ValueError as ve:
            print(ve, end=" ")

        print()

    resolution = int(resolution * 1000 * SCALE)
    print('Shape of downsampled atlas volume', atlas_volume.shape)
    print('Resolution at', resolution)

    if create:
        #offset =  [21959.308659539533, 6238.690939678455, 66.74432595997823]
        #atlasV7_volume = np.rot90(atlasV7_volume, axes=(0, 1))
        #atlasV7_volume = np.fliplr(atlasV7_volume)
        #atlasV7_volume = np.flipud(atlasV7_volume)
        #atlasV7_volume = np.fliplr(atlasV7_volume)


        offset = [0,0,0]
        ng = NumpyToNeuroglancer(animal='atlasV8', volume=atlas_volume,
                             scales=[resolution, resolution, 20000], 
                             layer_type='segmentation', data_type=np.uint8, offset=offset)
        ng.init_volume(OUTPUT_DIR)
        ng.add_segment_properties(get_segment_properties())
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()

    outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.npz')
    np.savez(outpath, atlas_volume.astype(np.uint8))

    end = timer()
    print(f'Finito! Program took {end - start} seconds')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Atlas')
    parser.add_argument('--create', required=False, default='false')
    args = parser.parse_args()
    create = bool({'true': True, 'false': False}[args.create.lower()])    
    create_atlas(create)
    



    