"""
Scale with 32 looks better.
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

    return c*R, t


def rigid_transform_3D(A, B):
    assert A.shape == B.shape

    num_rows, num_cols = A.shape
    if num_rows != 3:
        raise Exception(f"matrix A is not 3xN, it is {num_rows}x{num_cols}")

    num_rows, num_cols = B.shape
    if num_rows != 3:
        raise Exception(f"matrix B is not 3xN, it is {num_rows}x{num_cols}")

    # find mean column wise
    centroid_A = np.mean(A, axis=1)
    centroid_B = np.mean(B, axis=1)

    # ensure centroids are 3x1
    centroid_A = centroid_A.reshape(-1, 1)
    centroid_B = centroid_B.reshape(-1, 1)

    # subtract mean
    Am = A - centroid_A
    Bm = B - centroid_B

    H = Am @ np.transpose(Bm)

    # sanity check
    #if linalg.matrix_rank(H) < 3:
    #    raise ValueError("rank of H = {}, expecting 3".format(linalg.matrix_rank(H)))

    # find rotation
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    # special reflection case
    if np.linalg.det(R) < 0:
        print("det(R) < R, reflection detected!, correcting for it ...")
        Vt[2,:] *= -1
        R = Vt.T @ U.T

    t = -R@centroid_A + centroid_B

    return R, t

def create_atlas(animal):

    fileLocationManager = FileLocationManager(animal)
    atlas_name = 'atlasV7'
    DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
    ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
    THUMBNAIL_DIR = os.path.join(ROOT_DIR, animal, 'preps', 'CH1', 'thumbnail')
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
    ORIGIN_PATH = os.path.join(ATLAS_PATH, 'origin')
    VOLUME_PATH = os.path.join(ATLAS_PATH, 'structure')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'atlas_affine')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    origin_files = sorted(os.listdir(ORIGIN_PATH))
    volume_files = sorted(os.listdir(VOLUME_PATH))
    sqlController = SqlController(animal)
    resolution = sqlController.scan_run.resolution
    resolution = 0.452
    # the atlas uses a 10um scale
    #SCALE = (10 / resolution)
    SCALE = 32

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
    #aligned_shape = np.array((43700, 32400))
    z_length = len(os.listdir(THUMBNAIL_DIR))
    #z_length = 447
    downsampled_aligned_shape = np.round(aligned_shape // SCALE).astype(int)
    x_length = downsampled_aligned_shape[1] + 0
    y_length = downsampled_aligned_shape[0] + 0

    atlasV7_volume = np.zeros((x_length, y_length, z_length), dtype=np.uint32)

    ##### actual data for both sets of points, pixel coordinates
    MD589_centers = {'5N_L': [23790, 13025, 160],
                     '5N_R': [20805, 14163, 298],
                     '7n_L': [20988, 18405, 177],
                     '7n_R': [24554, 13911, 284],
                     'DC_L': [24482, 11985, 134],
                     'DC_R': [20424, 11736, 330],
                     'LC_L': [25290, 11750, 180],
                     'LC_R': [24894, 12079, 268],
                     'SC': [24226, 6401, 220]}
    MD589_centers = OrderedDict(MD589_centers)
    MD589_list = []
    for value in MD589_centers.values():
        MD589_list.append((value[1] / SCALE, value[0] / SCALE, value[2]))
    MD589 = np.array(MD589_list)
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
        if structure in MD589_centers.keys():
            atlas_centers[structure] = [midx, midy, midz]

    ATLAS_centers = OrderedDict(atlas_centers)
    ATLAS = np.array(list(ATLAS_centers.values()))
    pprint(MD589)
    pprint(ATLAS)

    md589_centroid = np.mean(MD589, axis=0)
    atlas_centroid = np.mean(ATLAS, axis=0)
    print('MD589 centroid', md589_centroid)
    print('Atlas centroid', atlas_centroid)
    #R, t = ralign(MD589, ATLAS)
    t = md589_centroid - atlas_centroid
    X = np.linalg.inv(MD589.T @ MD589) @ MD589.T @ ATLAS
    U, S, V = np.linalg.svd(X)
    RXXX = V @ U.T
    Sp = np.array([1.21175728, 0.86116328, 1])
    Ur = np.array([[np.cos(U[0][0]), -np.sin(U[0][1]), 0],
                   [np.sin(U[1][0]), np.cos(U[1][1]), 0],
                   [0, 0, 1]])
    Vr = np.array([[np.cos(V[0][0]), -np.sin(V[0][1]), 0],
                   [np.sin(V[1][0]), np.cos(V[1][1]), 0],
                   [0, 0, 1]])
    #####Steps
    # add translation
    # rotate by U
    # scale with S
    # rotate by V
    # done


    atlas_minmax = []
    trans_minmax = []
    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        x, y, z = origin # 10 micrometer/micron scale

        x_start = int(round(x + x_length / 2))
        y_start = int(round(y + y_length / 2))
        z_start = int(round(z / 2 + z_length / 2))
        atlas_minmax.append((x_start, y_start))
        print(str(structure).ljust(8), x_start, 'y', y_start, 'z', z_start, end="\t")
        arr = np.array([x_start, y_start, z_start])
        arr = np.reshape(arr, (3,1))
        results = arr + t
        results = Ur @ results
        results = results * Sp
        results = Vr @ results
        #results = R @ arr + t
        #results = arr
        x_start = int(round(results[0][0]))
        y_start = int(round(results[1][0]))
        #z_start = int(round(results[2][0]))

        z_start = int(round(z_start + t[2]))
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

    #atlasV7_volume = affine_transform(atlasV7_volume, R, t)

    # check range of x and y
    if len(trans_minmax) > 0:
        print('min,max x for atlas', np.min([x[0] for x in atlas_minmax]),np.max([x[0] for x in atlas_minmax]))
        print('min,max y for atlas', np.min([x[1] for x in atlas_minmax]),np.max([x[1] for x in atlas_minmax]))

        print('min,max x for trans', np.min([x[0] for x in trans_minmax]),np.max([x[0] for x in trans_minmax]))
        print('min,max y for trans', np.min([x[1] for x in trans_minmax]),np.max([x[1] for x in trans_minmax]))


    # resolution at 10000 or 14464 is still off, 22123 is very off
    resolution = int(resolution * 1000 * SCALE)
    resolution = 10000
    ng = NumpyToNeuroglancer(atlasV7_volume, [resolution, resolution, 20000], offset=[1000,130,0])
    ng.init_precomputed(OUTPUT_DIR)
    ng.add_segment_properties(get_segment_properties())
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()


    end = timer()
    print(f'Finito! Program took {end - start} seconds')

    #outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.npy')
    #with open(outpath, 'wb') as file:
    #    np.save(file, atlasV7_volume)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=False, default='MD589')
    args = parser.parse_args()
    animal = args.animal
    create_atlas(animal)

