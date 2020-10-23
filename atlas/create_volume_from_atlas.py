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
import collections
import cv2
import pandas as pd
from _collections import OrderedDict
import shutil
from skimage import io
#from scipy.ndimage import affine_transform
#from superpose3d import Superpose3D
#from scipy import linalg
#from pymicro.view.vol_utils import compute_affine_transform
from pprint import pprint
start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.imported_atlas_utilities import volume_to_polydata, save_mesh_stl
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties


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
    csvfile = os.path.join(DATA_PATH, 'atlas_data', 'DK39.PM.Nucleus.csv')
    DK39_df = pd.read_csv(csvfile)
    DK39_df = DK39_df.loc[DK39_df['Layer'] == 'premotor']
    csvfile = os.path.join(DATA_PATH, 'atlas_data', 'DK52.PM.Nucleus.csv')
    DK52_df = pd.read_csv(csvfile)
    DK52_df = DK52_df.loc[DK52_df['Layer'] == 'PM nucleus']

    #resolution = 0.452  # thionin - 0.452mm per pixel
    #resolution = 0.325 # NTB - 0.325mm per pixel
    # the atlas uses a 10mm per pixel
    SCALE = (10 / resolution)
    #SCALE = 32
    x_position = 0
    y_position = 1

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
        volume[volume > surface_threshold] = color * 10
        volume = volume.astype(np.uint8)

        structure_volume_origin[structure] = (volume, origin)
    #w = 43700
    #h = 32400
    aligned_shape = np.array((sqlController.scan_run.height,sqlController.scan_run.width))
    print('aligned shape', aligned_shape)
    #aligned_shape = np.array((43700, 32400))
    z_length = len(os.listdir(THUMBNAIL_DIR))
    #z_length = 447
    downsampled_aligned_shape = np.round(aligned_shape // SCALE).astype(int)
    x_length = downsampled_aligned_shape[x_position] + 0
    y_length = downsampled_aligned_shape[y_position] + 0
    #x_length = 2000
    #y_length = 2000

    atlasV7_volume = np.zeros((y_length, x_length, z_length), dtype=np.uint8)
    print('Shape of atlas volume', atlasV7_volume.shape)
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
    centers = OrderedDict(DK52_centers)
    centers_list = []
    for value in centers.values():
        centers_list.append((value[1] / SCALE, value[0] / SCALE, value[2]))
    COM = np.array(centers_list)
    atlas_centers = OrderedDict()
    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        x, y, z = origin
        x_start = x + x_length / 2
        y_start = y + y_length / 2
        z_start = z / 2 + z_length / 2
        x_end = x_start + volume.shape[x_position]
        y_end = y_start + volume.shape[y_position]
        z_end = z_start + (volume.shape[2] + 1) / 2
        midx = (x_end + x_start) / 2
        midy = (y_end + y_start) / 2
        midz = (z_end + z_start) / 2
        if structure in centers.keys():
            atlas_centers[structure] = [midx, midy, midz]

    ATLAS_centers = OrderedDict(atlas_centers)
    ATLAS = np.array(list(ATLAS_centers.values()))
    pprint(COM)
    pprint(ATLAS)
    #####Steps
    # Get SVD from the two sets of centers of mass
    # get matrix R1 from dot product of U and V
    # get rotation matrix R from R1
    # scale rotation by R by S and get RS
    # get new points by dot product of RS and original points + t
    # done
    animal_centroid = np.mean(COM, axis=0)
    atlas_centroid = np.mean(ATLAS, axis=0)
    t = animal_centroid - atlas_centroid
    X = np.linalg.inv(COM.T @ COM) @ COM.T @ ATLAS
    U, S, V = np.linalg.svd(X)
    R1 = np.dot(U, V)
    R = np.array([[np.cos(R1[0][0]), -np.sin(R1[0][1]), 0],
                  [np.sin(R1[1][0]), np.cos(R1[1][1]), 0],
                  [0, 0, 1]])
    cx = S[0]
    cy = S[1]
    Sc = np.array([[cx, 0, 0], [0, cy, 0], [0, 0, 1]])
    RS = Sc * R

    # this is the transformation matrix Yoav created in Neuroglancer
    rNeuro = np.array([
        [0.89, 0.475, -0.024],
        [-0.3596, 1.173566, -0.0858],
        [-0.0083, 0.09963,1.12647]
    ])
    tNeuro = np.array([18917.2, 6900, 48.674])

    atlas_minmax = []
    trans_minmax = []
    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        x, y, z = origin # 10 micrometer/micron scale

        x_start = x + x_length / 2
        y_start = y + y_length / 2
        z_start = z / 2 + z_length / 2
        atlas_minmax.append((x_start, y_start))
        print(str(structure).ljust(8), x_start, 'y', y_start, 'z', z_start, end="\t")

        if x_position < y_position:
            arr = np.array([x_start, y_start, z_start])
        else:
            arr = np.array([y_start, x_start, z_start])

        results = np.dot(rNeuro, arr + 0)
        x_start = int(round(results[0]))
        y_start = int(round(results[1]))
        z_start = int(round(z_start))
        #z_start = int(round(results[2]))
        print('Translated: x', round(x_start), 'y', round(y_start), 'z', round(z_start), end="\t")
        trans_minmax.append((x_start, y_start))

        x_end = x_start + volume.shape[x_position]
        y_end = y_start + volume.shape[y_position]
        z_end = z_start + (volume.shape[2] + 1) // 2
        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]

        if create and False:
            midx = (x_end + x_start) / 2
            midy = (y_end + y_start) / 2
            midz = (z_end + z_start) / 2
            #print(str(structure).ljust(8), origin, end="\n")
            print(structure,",",origin[0],",", origin[1],",", origin[2], end="\n")
            results = np.dot(RS, origin + 0)
            #x = results[0] - x_start
            #y = results[1] - y_start
            #z = results[2] - z_start
            #print(str(structure).ljust(8), results)
            align_volume = (volume, np.array([midx, midy, midz]))
            aligned_structure = volume_to_polydata(volume=align_volume,
                                                   num_simplify_iter=3, smooth=True,
                                                   return_vertex_face_list=False)
            filepath = os.path.join(ATLAS_PATH, 'mesh', '{}.stl'.format(structure))
            save_mesh_stl(aligned_structure, filepath)
        else:
            print()


        try:
            if x_position < y_position:
                atlasV7_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume
            else:
                atlasV7_volume[y_start:y_end, x_start:x_end, z_start:z_end] += volume
        except:
            print('could not add', structure, x_start,y_start, z_start)

    #atlasV7_volume = affine_transform(atlasV7_volume, mat)

    # check range of x and y
    if len(trans_minmax) > 0:
        print('min,max x for atlas', np.min([x[0] for x in atlas_minmax]),np.max([x[0] for x in atlas_minmax]))
        print('min,max y for atlas', np.min([x[1] for x in atlas_minmax]),np.max([x[1] for x in atlas_minmax]))

        print('min,max x for trans', np.min([x[0] for x in trans_minmax]),np.max([x[0] for x in trans_minmax]))
        print('min,max y for trans', np.min([x[1] for x in trans_minmax]),np.max([x[1] for x in trans_minmax]))


    # resolution at 10000 or 14464 is still off, 22123 is very off
    resolution = int(resolution * 1000 * SCALE)
    resolution = 10000
    print('Resolution at', resolution)

    if create and False:
        offset = [0,0,0]
        ng = NumpyToNeuroglancer(atlasV7_volume, [resolution, resolution, 20000], offset=offset)
        ng.init_precomputed(OUTPUT_DIR)
        ng.add_segment_properties(get_segment_properties())
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()

    outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.tif')
    #with open(outpath, 'wb') as file:
    #    np.save(file, atlasV7_volume)

    #cv2.imwrite(outpath, atlasV7_volume, )
    io.imsave(outpath, atlasV7_volume.astype(np.uint8))
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

