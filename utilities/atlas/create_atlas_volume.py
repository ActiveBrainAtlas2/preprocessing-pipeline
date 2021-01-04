"""
Scale with 32 on DK52, x is 1125, y is 2031
SCALE with 10/resolution  on DK52, x is 1170, y 2112
scale with 10/resolution on MD589, x is 1464, y 1975
"""
import argparse
import os
import sys
import numpy as np
from timeit import default_timer as timer
import shutil

from scipy.ndimage import affine_transform

start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import DATA_PATH, ROOT_DIR
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties


def create_atlas(animal, create):

    atlas_name = 'atlasV8'
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
    ORIGIN_PATH = os.path.join(ATLAS_PATH, 'origin')
    VOLUME_PATH = os.path.join(ATLAS_PATH, 'structure')
    OUTPUT_DIR = os.path.join(ROOT_DIR, 'structures', 'atlas')
    if os.path.exists(OUTPUT_DIR) and create:
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    origin_files = sorted(os.listdir(ORIGIN_PATH))
    volume_files = sorted(os.listdir(VOLUME_PATH))
    sqlController = SqlController(animal)
    surface_threshold = 0.8
    resolution = sqlController.scan_run.resolution
    SCALE = (10 / resolution)
    resolution = int(resolution * 1000 * SCALE)
    print('Resolution at', resolution)

    structure_volume_origin = {}
    for volume_filename, origin_filename in zip(volume_files, origin_files):
        structure = os.path.splitext(volume_filename)[0]
        if structure not in origin_filename:
            print(structure, origin_filename)

        color = get_structure_number(structure.replace('_L', '').replace('_R', ''))
        origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
        volume_path = os.path.join(VOLUME_PATH, volume_filename)
        if not os.path.exists(volume_path):
            print('Error, file does not exist', volume_path)

        volume = np.load(volume_path)


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

    print('Shape of downsampled atlas volume', atlas_volume.shape)

    if create:
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

        #outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.npz')
        #np.savez(outpath, atlasV7_volume.astype(np.uint8))

    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_atlas(animal, create)

