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
from scipy.ndimage import affine_transform
from superpose3d import Superpose3D
from scipy import linalg
from pymicro.view.vol_utils import compute_affine_transform
from pprint import pprint
start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties


def ralign(from_points, to_points):
    assert len(from_points.shape) == 2, \
        "from_points must be a m x n array"
    assert from_points.shape == to_points.shape, \
        "from_points and to_points must have the same shape"

    N, m = from_points.shape

    mean_from = from_points.mean(axis=0)
    mean_to = to_points.mean(axis=0)

    delta_from = from_points - mean_from  # N x m
    delta_to = to_points - mean_to  # N x m

    sigma_from = (delta_from * delta_from).sum(axis=1).mean()
    sigma_to = (delta_to * delta_to).sum(axis=1).mean()

    cov_matrix = delta_to.T.dot(delta_from) / N

    U, d, V_t = np.linalg.svd(cov_matrix, full_matrices=True)
    cov_rank = np.linalg.matrix_rank(cov_matrix)
    S = np.eye(m)

    if cov_rank >= m - 1 and np.linalg.det(cov_matrix) < 0:
        S[m - 1, m - 1] = -1
    elif cov_rank < m - 1:
        raise ValueError("colinearility detected in covariance matrix:\n{}".format(cov_matrix))

    R = U.dot(S).dot(V_t)
    c = (d * S.diagonal()).sum() / sigma_from
    t = mean_to - c * R.dot(mean_from)

    return c, R, t


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
    #resolution = 0.452  # thionin - 0.452mm per pixel
    #resolution = 0.325 # NTB - 0.325mm per pixel
    # the atlas uses a 10mm per pixel
    SCALE = (10 / resolution)
    #SCALE = 32

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
        volume[volume > 0.8] = color
        volume = volume.astype(np.uint8)

        structure_volume_origin[structure] = (volume, origin)
    #w = 43700
    #h = 32400
    aligned_shape = np.array((sqlController.scan_run.width, sqlController.scan_run.height))
    print('aligned shape', aligned_shape)
    #aligned_shape = np.array((43700, 32400))
    z_length = len(os.listdir(THUMBNAIL_DIR))
    #z_length = 447
    downsampled_aligned_shape = np.round(aligned_shape // SCALE).astype(int)
    x_length = downsampled_aligned_shape[1] + 0
    y_length = downsampled_aligned_shape[0] + 0

    atlasV7_volume = np.zeros((x_length, y_length, z_length), dtype=np.uint32)
    print('Shape of volume', atlasV7_volume.shape)
    DK52_centers = {'12N': [46488, 18778, 242],
                    '5N_L': [38990, 20019, 172],
                    '5N_R': [39184, 19027, 315],
                    '7N_L': [42425, 23190, 166],
                    '7N_R': [42286, 22901, 291]}
    ##### actual data for both sets of points, pixel coordinates
    MD589_centers = {'10N_L': [30928.49438599714, 12939.677824158094, 210],
     '10N_R': [29284.49554866147, 13339.540536054074, 242],
     '4N_L': [24976.742385259997, 9685.320856475, 210],
     '4N_R': [24516.55179962143, 9154.861612245713, 236],
     '5N_L': [23789.984501544375, 13025.174081591875, 160],
     '5N_R': [20805.414639021943, 14163.355691957777, 298],
     '7N_L': [23184.71446623, 15964.358564491615, 174],
     '7N_R': [23525.73793603972, 15117.485091564571, 296],
     '7n_L': [20987.553460092142, 18404.810023741426, 177],
     '7n_R': [24554.23633658875, 13910.6602304075, 284],
     'Amb_L': [25777.11256108571, 15152.709144375, 167],
     'Amb_R': [25184.94247019933, 14794.196115586003, 296],
     'DC_L': [24481.971490631582, 11984.58023668316, 134],
     'DC_R': [20423.754452355664, 11736.014030692337, 330],
     'LC_L': [25290.18582962385, 11749.672587382307, 180],
     'LC_R': [24894.30149961837, 12078.56676300372, 268],
     'Pn_L': [20986.433685970915, 14907.131608333335, 200],
     'Pn_R': [19142.43337585326, 14778.245969858139, 270],
     'SC': [24226.115900506382, 6401.250694575117, 220],
     'Tz_L': [25322.11246646844, 15750.426156366877, 212],
     'Tz_R': [20560.370568873335, 18257.503270669335, 262]}

    centers = OrderedDict(MD589_centers)
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
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
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
    #####Steps, Bili, check my math!
    # add translation
    # rotate by U
    # scale with S
    # rotate by V
    # done
    centroid = np.mean(COM, axis=0)
    atlas_centroid = np.mean(ATLAS, axis=0)
    print(f'{animal} centroid', centroid)
    print('Atlas centroid', atlas_centroid)
    t = centroid - atlas_centroid
    print('translation', t)
    print('translation', t[0], t[1], t[2])
    print('atlas shape', atlas_centers.keys())
    print('DK52 shape', centers.keys())
    #X = np.linalg.inv(MD589.T @ MD589) @ MD589.T @ ATLAS
    X = np.linalg.inv(COM.T @ COM) @ COM.T @ ATLAS
    U, S, V = np.linalg.svd(X)
    #RXXX = V @ U.T
    Ur = np.array([[np.cos(U[0][0]), -np.sin(U[0][1]), 0],
                   [np.sin(U[1][0]), np.cos(U[1][1]), 0],
                   [0, 0, 1]])
    Vr = np.array([[np.cos(V[0][0]), -np.sin(V[0][1]), 0],
                   [np.sin(V[1][0]), np.cos(V[1][1]), 0],
                   [0, 0, 1]])
    cx = S[0]
    cy = S[1]
    cy = 1

    Sc = np.array([[cx, 0, 0], [0, cy, 0], [0, 0, 1]])
    print('scaling array from SVD')
    pprint(S)

    Tx = np.array([[1, 0, t[0]], [0, 1, t[1]], [0, 0, t[2]]])
    mat = Ur@Vr@Sc + Tx
    R = np.dot(Ur, Vr)
    cRA, RRA, tRA = ralign(ATLAS, COM)
    print('scaling array from ralign')
    pprint(cRA)

    atlas_minmax = []
    trans_minmax = []
    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        x, y, z = origin # 10 micrometer/micron scale

        x_start = x + x_length / 2
        y_start = y + y_length / 2
        z_start = z / 2 + z_length / 2
        atlas_minmax.append((x_start, y_start))
        print(str(structure).ljust(8), x_start, 'y', y_start, 'z', z_start, end="\t")

        arr = np.array([x_start, y_start, z_start])
        arr = np.reshape(arr, (3,1))
        results = arr + t # shift according to mean of centroid
        results = np.dot(Ur, results)# rotate by U matrix from SVD
        #results = np.dot(RRA, arr)
        results = results * S # scale by S matrix from SVD
        results = np.dot(Vr, results)# rotate by V matrix from SVD
        #x_start = int(round(results[0]))
        #y_start = int(round(results[1]))
        #z_start = int(round(results[2]))
        x_start = int(round(results[0][0]))
        y_start = int(round(results[1][0]))
        z_start = int(round(z_start + t[2]))
        #z_start = int(round(results[2][0]))
        # Bili, i didn't rotate or scale the z axis, only shifted it.
        #x_start = int(round(x_start + t[0]))
        #y_start = int(round(y_start + t[1]))
        #z_start = int(round(z_start + t[2]))
        print('Translated: x', round(x_start), 'y', round(y_start), 'z', round(z_start), end="\t")
        trans_minmax.append((x_start, y_start))

        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) // 2
        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]

        print(volume.shape)



        try:
            atlasV7_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume
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
    resolution = int(resolution * 1000 * 32)
    resolution = 10000
    print('Resolution at', resolution)

    if create:
        ng = NumpyToNeuroglancer(atlasV7_volume, [resolution, resolution, 20000], offset=[0,0,0])
        ng.init_precomputed(OUTPUT_DIR)
        ng.add_segment_properties(get_segment_properties())
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()


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

