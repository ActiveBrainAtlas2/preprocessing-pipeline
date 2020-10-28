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
from utilities.utilities_affine import rigid_transform_3D, ralign, affine_fit, superalign, umeyama


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
    print(SCALE)

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

    #### a mouse's brain measures about 14000um in width
    #### and about 6000um in height from a sagittal view
    #### so 14000 should be equal to the col_length below
    #### and 6000 should be equal to the row_length below
    col_length = sqlController.scan_run.width / SCALE
    row_length = sqlController.scan_run.height / SCALE
    col_length = 1690
    row_length = 1160
    z_length = len(os.listdir(THUMBNAIL_DIR))
    atlasV7_volume = np.zeros((int(row_length), int(col_length), z_length), dtype=np.uint8)
    print('atlas volume shape', atlasV7_volume.shape)

    DK52_centers = {'12N': [46488, 18778, 242],
                    '5N_L': [38990, 20019, 172],
                    '5N_R': [39184, 19027, 315],
                    '7N_L': [42425, 23190, 166],
                    '7N_R': [42286, 22901, 291]}
    centers = OrderedDict(DK52_centers)
    centers_list = []
    for value in centers.values():
        centers_list.append((value[1] / SCALE, value[0] / SCALE, value[2]))
    COM = np.array(centers_list)
    atlas_com_centers = OrderedDict()
    atlas_all_centers = {}
    ##### get all the COMs for the ATLAS
    ##### the origin starts in the middle of the virtual 3D space
    ##### so 0,0,0 is the entire volume centroid
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
        ##### If the keys from the animal coincide with ATLAS, add them
        if structure in centers.keys():
            atlas_com_centers[structure] = [midrow, midcol, midz]
        atlas_all_centers[structure] = [midrow, midcol, midz]
    ATLAS_centers = OrderedDict(atlas_com_centers)
    ATLAS = np.array(list(ATLAS_centers.values()))
    pprint(COM)
    pprint(ATLAS)
    #####Steps
    R, t = rigid_transform_3D(ATLAS.T, COM.T) # close visual fit, translation is most accurate
    ## below is Yoav's manual alignment rotation matrix and translation
    #s, R, t = umeyama(ATLAS, COM)
    #R = np.array([
    #    [0.8879282700452737, 0.5297064165901834, -0.0656862661295595],
    #    [-0.35874630775873184, 1.3064870877277086, 0.047808994348642005],
    #    [0.06696621479436028, -0.024547949485823613, 1.1270756915581706]
    #])
    s = 1
    #t = np.array([18917.2/SCALE, 6900/SCALE, 48.674])
    if t.shape[0] == 3:
        t = np.reshape(t, (1, 3))

    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        print(str(structure).ljust(6), end=": ")
        x, y, z = origin
        arr = np.array([y, x, z])
        input = arr + t
        results = np.dot(s*R, input.T).reshape(3,1)
        y = results[0][0]
        x = results[1][0]
        z = results[2][0]
        x_start = int(round(x + col_length / 2))
        y_start = int(round(y + row_length / 2))
        z_start = int(round(z / 2 + z_length / 2))
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = int(z_start + (volume.shape[2] + 1) / 2)

        print('Y', str(y_start).rjust(4),  str(y_end).rjust(4),
              'X',  str(x_start).rjust(4), str(x_end).rjust(4),
              'Z',  str(z_start).rjust(4), str(z_end).rjust(4),
              end=" ")


        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        volume = np.swapaxes(volume, 0, 1)

        try:
            atlasV7_volume[y_start:y_end, x_start:x_end, z_start:z_end] += volume
        except ValueError as ve:
            print(ve, end=" ")

        print()


    resolution = int(resolution * 1000 * SCALE)
    print('Shape of downsampled atlas volume after swapping'.ljust(60), atlasV7_volume.shape)
    resolution = 10000
    print('Resolution at', resolution)

    if create:
        atlasV7_volume = np.rot90(atlasV7_volume, axes=(0, 1))
        atlasV7_volume = np.fliplr(atlasV7_volume)
        atlasV7_volume = np.flipud(atlasV7_volume)
        atlasV7_volume = np.fliplr(atlasV7_volume)
        print('Shape of downsampled atlas volume after rotating/flipping'.ljust(60), atlasV7_volume.shape)

        offset =  [0,0,0]
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
    parser.add_argument('--animal', help='Enter the animal', required=False, default='MD589')
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_atlas(animal, create)

