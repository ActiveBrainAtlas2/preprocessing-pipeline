import os, sys
import numpy as np
from pathlib import Path

from scipy import ndimage

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager



# Adapted from https://github.com/libigl/eigen/blob/master/Eigen/src/Geometry/Umeyama.h
def align_point_sets(src, dst, with_scaling=True):
    assert src.shape == dst.shape
    assert len(src.shape) == 2
    m, n = src.shape  # dimension, number of points

    src_mean = np.mean(src, axis=1).reshape(-1, 1)
    dst_mean = np.mean(dst, axis=1).reshape(-1, 1)

    src_demean = src - src_mean
    dst_demean = dst - dst_mean

    u, s, vh = np.linalg.svd(dst_demean @ src_demean.T / n)

    # deal with reflection
    e = np.ones(m)
    if np.linalg.det(u) * np.linalg.det(vh) < 0:
        print('reflection detected')
        e[-1] = -1

    r = u @ np.diag(e) @ vh

    if with_scaling:
        src_var = (src_demean ** 2).sum(axis=0).mean()
        c = sum(s * e) / src_var
        r *= c

    t = dst_mean - r @ src_mean

    return r, t


def get_atlas_centers_hardcodeddata(
        atlas_box_size=(1000, 1000, 300),
        atlas_box_scales=(10, 10, 20),
        atlas_raw_scale=10):
    atlas_box_scales = np.array(atlas_box_scales)
    atlas_box_size = np.array(atlas_box_size)
    atlas_box_center = atlas_box_size / 2

    atlas_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV7')
    origin_dir = atlas_dir / 'origin'
    volume_dir = atlas_dir / 'structure'

    atlas_centers = {}

    for origin_file, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        assert origin_file.stem == volume_file.stem
        name = origin_file.stem

        origin = np.loadtxt(origin_file)

        volume = np.load(volume_file)
        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)

        # computer volume center of mass in raw array coordinates
        center = (origin + ndimage.measurements.center_of_mass(volume))

        # transform into the atlas box coordinates that neuroglancer assumes
        center = atlas_box_center + center * atlas_raw_scale / atlas_box_scales

        atlas_centers[name] = (center, volume)

    return atlas_centers

def get_atlas_centers(
        atlas_box_size=(1000, 1000, 300),
        atlas_box_scales=(10, 10, 20),
        atlas_raw_scale=10):
    atlas_box_scales = np.array(atlas_box_scales)
    atlas_box_size = np.array(atlas_box_size)
    atlas_box_center = atlas_box_size / 2
    sqlController = SqlController('Atlas')
    atlas_centers = sqlController.get_centers_dict('Atlas')

    for structure, origin in atlas_centers.items():
        # transform into the atlas box coordinates that neuroglancer assumes
        center = atlas_box_center + np.array(origin) * atlas_raw_scale / atlas_box_scales
        atlas_centers[structure] = center

    return atlas_centers

def align_atlas(
        reference_centers,
        reference_scales=(0.325, 0.325, 20),
        atlas_box_size=(1000, 1000, 300),
        atlas_box_scales=(10, 10, 20),
        atlas_raw_scale=10):
    atlas_centers = get_atlas_centers(atlas_box_size, atlas_box_scales, atlas_raw_scale)

    structures = sorted(reference_centers.keys())

    src_point_set = np.array([atlas_centers[s] for s in structures]).T
    src_point_set = np.diag(atlas_box_scales) @ src_point_set

    dst_point_set = np.array([reference_centers[s] for s in structures]).T
    dst_point_set = np.diag(reference_scales) @ dst_point_set

    r, t = align_point_sets(src_point_set, dst_point_set)

    print('Please type the following numbers into neuroglancer to align the atlas structures.')
    print()
    print('Rotation:')
    print(r)
    print()
    print('Translation:')
    print(t / np.array([reference_scales]).T)
    t = t / np.array([reference_scales]).T
    return r, t


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

    return c * R, t


DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'

DK52_centers = {'12N': [46488, 18778, 242],
                '5N_L': [38990, 20019, 172],
                '5N_R': [39184, 19027, 315],
                '7N_L': [42425, 23190, 166],
                '7N_R': [42286, 22901, 291]}

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
