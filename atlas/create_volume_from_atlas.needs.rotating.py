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
from utilities.utilities_affine import rigid_transform_3D, ralign, affine_fit


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
    SCALE = (10 / 0.46)

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

    DK52_centers = {'12N': [46488, 18778, 242],
                    '5N_L': [38990, 20019, 172],
                    '5N_R': [39184, 19027, 315],
                    '7N_L': [42425, 23190, 166],
                    '7N_R': [42286, 22901, 291]}
    ##### actual data for both sets of points, pixel coordinates
    MD589_centers = {'10N_L': [31002.069009677187, 17139.273764067697, 210],
                     '10N_R': [30851.821452912456, 17026.27799914138, 242],
                     '4N_L': [25238.351916435207, 13605.972626040299, 210],
                     '4N_R': [25231.77274616, 13572.152382002621, 236],
                     '5N_L': [25863.93885802854, 16448.49802904827, 160],
                     '5N_R': [25617.920248719453, 16089.048882550318, 298],
                     '7N_L': [27315.217906796195, 18976.4921239128, 174],
                     '7N_R': [27227.134448911638, 18547.6538128018, 296],
                     '7n_L': [26920.538205417844, 16996.292850204114, 177],
                     '7n_R': [26803.347723222105, 16688.23325135847, 284],
                     'Amb_L': [29042.974021303286, 18890.218579368557, 167],
                     'Amb_R': [28901.503217056554, 18291.072163747285, 296],
                     'DC_L': [28764.5378815116, 15560.1247992853, 134],
                     'DC_R': [28519.240424058273, 14960.063579837733, 330],
                     'LC_L': [26993.749068166835, 15146.987356709138, 180],
                     'LC_R': [26951.610128773387, 14929.363532303963, 268],
                     'Pn_L': [23019.18002537938, 17948.490571838032, 200],
                     'Pn_R': [23067.16403704933, 17945.89008778571, 270],
                     'SC': [24976.373217129738, 10136.880464106176, 220],
                     'Tz_L': [25210.29041867189, 18857.20817842522, 212],
                     'Tz_R': [25142.520897455783, 18757.457820947686, 262]}
    centers = OrderedDict(MD589_centers)
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
    R, t = rigid_transform_3D(ATLAS.T, COM.T)

    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        print(str(structure).ljust(7),end=": ")

        # transformed atlas
        arr = np.array(atlas_all_centers[structure])
        #results = trn.Transform(arr)
        #results = np.dot(R, arr + t)
        #midrow = results[0]
        #midcol = results[1]
        #midz = results[2]
        input = arr + t
        results = np.dot(R, input.T)
        midrow = results[0][0]
        midcol = results[1][0]
        midz = results[2][0]

        row_start = int(round(midrow - volume.shape[1] / 2))
        col_start = int(round(midcol - volume.shape[0] / 2))
        sec_start = int(round(midz - (volume.shape[2] / 2) / 2))
        row_end = row_start + volume.shape[1]
        col_end = col_start + volume.shape[0]
        sec_end = int(round(sec_start + (volume.shape[2] + 1) // 2))

        ## generic atlas
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

        print('Trans range: row',
              str(round(row_start,1)).rjust(4),
              str(round(row_end,1)).rjust(4),
              'col',
              str(round(col_start,1)).rjust(4),
              str(round(col_end,1)).rjust(4),
              'z',
              str(round(z_start,1)).rjust(4),
              str(round(z_end,1)).rjust(4),
              end=" ")

        if structure in centers.keys():
            xo,yo,zo = MD589_centers[structure]
            print('COM off by:',
                  round(midrow*SCALE-yo, 2),
                  round(midcol*SCALE-xo, 2),
                  round(midz - zo, 2),
                  end=" ")

        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        #volume = np.swapaxes(volume, 0, 1)
        volume = np.rot90(volume, axes=(0,1))
        try:
            atlasV7_volume[row_start:row_end, col_start:col_end, sec_start:sec_end] += volume
            #atlasV7_volume[y_start:y_end, x_start:x_end, z_start:z_end] += volume
        except ValueError as ve:
            print(ve, end=" ")

        print()

    resolution = int(resolution * 1000 * SCALE)
    print('Shape of downsampled atlas volume', atlasV7_volume.shape)

    print('Resolution at', resolution)

    if create:
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
    parser.add_argument('--animal', help='Enter the animal', required=False, default='MD589')
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_atlas(animal, create)

