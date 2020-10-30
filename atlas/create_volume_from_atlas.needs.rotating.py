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
from _collections import OrderedDict
import shutil
from pprint import pprint
start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties
from utilities.utilities_affine import align_point_sets, DK52_centers, rigid_transform_3D, ralign


def create_atlas(animal, create):

    fileLocationManager = FileLocationManager(animal)
    atlas_name = 'atlasV7'
    DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
    ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
    THUMBNAIL_DIR = os.path.join(ROOT_DIR, animal, 'preps', 'CH1', 'thumbnail')
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
    ORIGIN_PATH = os.path.join(ATLAS_PATH, 'origin')
    VOLUME_PATH = os.path.join(ATLAS_PATH, 'structure')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'atlas')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    origin_files = sorted(os.listdir(ORIGIN_PATH))
    volume_files = sorted(os.listdir(VOLUME_PATH))
    sqlController = SqlController(animal)
    resolution = sqlController.scan_run.resolution
    surface_threshold = 0.8
    SCALE = (10 / resolution)

    structure_volume_origin = {}
    for volume_filename, origin_filename in zip(volume_files, origin_files):
        structure = os.path.splitext(volume_filename)[0]
        if structure not in origin_filename:
            print(structure, origin_filename)
            break

        color = get_structure_number(structure.replace('_L', '').replace('_R', ''))

        origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
        volume = np.load(os.path.join(VOLUME_PATH, volume_filename))

        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)
        volume[volume > surface_threshold] = color
        volume = volume.astype(np.uint8)

        structure_volume_origin[structure] = (volume, origin)

    col_length = sqlController.scan_run.width/SCALE
    row_length = sqlController.scan_run.height/SCALE
    z_length = len(os.listdir(THUMBNAIL_DIR))
    atlasV7_volume = np.zeros(( int(row_length), int(col_length), z_length), dtype=np.uint8)
    print('atlas volume shape', atlasV7_volume.shape)

    ##### actual data for both sets of points, pixel coordinates
    centers = OrderedDict(DK52_centers)
    centers_list = []
    for value in centers.values():
        centers_list.append((value[1]/SCALE, value[0]/SCALE, value[2]))
    COM = np.array(centers_list)
    atlas_com_centers = OrderedDict()
    atlas_all_centers = {}
    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        midcol, midrow, midz = origin
        row_start = midrow + row_length / 2
        col_start = midcol + col_length / 2
        z_start = midz / 2 + z_length / 2
        row_end = row_start + volume.shape[0]
        col_end = col_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) / 2
        midcol = (col_end + col_start) / 2
        midrow = (row_end + row_start) / 2
        midz = (z_end + z_start) / 2
        if structure in centers.keys():
            atlas_com_centers[structure] = [midrow, midcol, midz]
        atlas_all_centers[structure] = [midrow, midcol, midz]
    ATLAS_centers = OrderedDict(atlas_com_centers)
    ATLAS = np.array(list(ATLAS_centers.values()))
    pprint(COM)
    pprint(ATLAS)
    #####Steps
    #trn = Affine_Fit(ATLAS, COM)
    # source is atlas, output is animal
    r_auto, t_auto = align_point_sets(ATLAS.T, COM.T)
    debug = False

    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        print(str(structure).ljust(7),end=": ")

        # transformed atlas
        source_point = np.array(atlas_all_centers[structure])
        results = (r_auto @ source_point + t_auto.T).reshape(1,3)
        y = results[0][0]
        x = results[0][1]
        z = results[0][2]
        y = y - volume.shape[1]/2
        x = x - volume.shape[0]/2
        z = z - volume.shape[2]/2
        #x_start = int( round(x + col_length / 2))
        #y_start = int( round(y + row_length / 2))
        #z_start = int(z) // 2 + z_length // 2
        x_start = int( round(x))
        y_start = int( round(y))
        z_start = int(z)
        x_end = int( round(x_start + volume.shape[0]))
        y_end = int( round(y_start + volume.shape[1]))
        z_end = int( round(z_start + (volume.shape[2] + 1) // 2))

        if debug:
            print('Midpoints row',
                  str(int(y*SCALE)).rjust(4),
                  'mid col',
                  str(int(x*SCALE)).rjust(4),
                  'mid z',
                  str(int(z)).rjust(4),
                  end=" ")
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

        if structure in centers.keys():
            xo,yo,zo = DK52_centers[structure]
            print('COM off by:',
                  round(x*SCALE - xo, 2),
                  round(y*SCALE - yo, 2),
                  round(z - zo, 2),
                  end=" ")

        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        volume = np.swapaxes(volume, 0, 1)
        try:
            atlasV7_volume[y_start:y_end, x_start:x_end, z_start:z_end] += volume
            #atlasV7_volume[col_start:col_end, row_start:row_end, z_start:z_end] += volume
        except ValueError as ve:
            print(ve, end=" ")

        print()

    resolution = int(resolution * 1000 * SCALE)
    print('Shape of downsampled atlas volume', atlasV7_volume.shape)

    print('Resolution at', resolution)

    if create:
        atlasV7_volume = np.rot90(atlasV7_volume, axes=(0, 1))
        atlasV7_volume = np.fliplr(atlasV7_volume)
        atlasV7_volume = np.flipud(atlasV7_volume)
        atlasV7_volume = np.fliplr(atlasV7_volume)

        offset = [0,0,0]
        ng = NumpyToNeuroglancer(atlasV7_volume, [resolution, resolution, 20000], offset=offset)
        ng.init_precomputed(OUTPUT_DIR)
        ng.add_segment_properties(get_segment_properties())
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()

        #outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.tif')
        #io.imsave(outpath, atlasV7_volume.astype(np.uint8))
    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=False, default='DK52')
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_atlas(animal, create)

