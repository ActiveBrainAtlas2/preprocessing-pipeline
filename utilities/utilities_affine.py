import os, sys
import numpy as np
from pathlib import Path
import requests
from requests.exceptions import HTTPError

from scipy import ndimage

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager


DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'


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

def get_transformation_matrix(animal):
    try:
        url = f'https://activebrainatlas.ucsd.edu/activebrainatlas/alignatlas?animal={animal}'
        response = requests.get(url)
        response.raise_for_status()
        # access JSOn content
        transformation_matrix = response.json()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    return transformation_matrix

