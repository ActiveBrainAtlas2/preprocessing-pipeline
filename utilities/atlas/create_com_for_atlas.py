"""
The x,y,z coordinates for the atlas need to be added to the center of mass of each volume
before entered into the database. This will make the data consistent with the other
entries and the algorithm.
"""
import argparse

from scipy import ndimage
from pathlib import Path
import numpy as np
import os, sys

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)
from utilities.sqlcontroller import SqlController
from utilities.utilities_neuroglancer import ATLAS_Z_BOX_SCALE, COL_LENGTH, ATLAS_RAW_SCALE, Z_LENGTH

def atlas_scale_xy(x):
    """
    0.325 is the scale for Neurotrace brains
    This converts the atlas coordinates to neuroglancer XY coordinates
    :param x: x or y coordinate
    :return: an integer that is in neuroglancer scale
    """
    atlas_box_center = COL_LENGTH // 2
    result = (atlas_box_center + x) * (ATLAS_RAW_SCALE / 0.325)
    return int(round(result))


def atlas_scale_section(section):
    """
    scales the z (section) to neuroglancer coordinates
    :param section:
    :return:
    """
    atlas_box_center = Z_LENGTH // 2
    result = atlas_box_center + section * ATLAS_RAW_SCALE/ATLAS_Z_BOX_SCALE
    return int(round(result))

def calc_com(x,y,z, volume):
    origin = np.array([x,y,z])
    atlas_box_size=(1000, 1000, 300),
    atlas_box_scales=(10, 10, 20),
    atlas_raw_scale=10
    atlas_box_scales = np.array(atlas_box_scales)
    atlas_box_size = np.array(atlas_box_size)
    atlas_box_center = atlas_box_size / 2
    #xn,yn,zn = (origin + ndimage.measurements.center_of_mass(volume))
    xn, yn, zn = origin + volume.shape
    center = atlas_box_center + np.array([xn,yn,zn]) * atlas_raw_scale / atlas_box_scales
    return center


def insert_origins(atlas, create):
    sqlController = SqlController(atlas)
    # unzip your structure and origin zip files in this path, or create your own path
    atlas_dir = Path(f'/net/birdstore/Active_Atlas_Data/data_root/atlas_data/{atlas}')
    origin_dir = atlas_dir / 'origin'
    volume_dir = atlas_dir / 'structure'


    for origin_file, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        assert origin_file.stem == volume_file.stem
        structure = origin_file.stem
        origin = np.loadtxt(origin_file)
        volume = np.load(volume_file)
        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)
        x, y, z = origin

        x_start = x + 1000 / 2
        y_start = y + 1000 / 2
        z_start = z / 2 + 300 / 2
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) / 2
        x = ((x_start + x_end) / 2)
        y = ((y_start + y_end) / 2)
        z = (z_start + z_end) / 2


        if create:
            input_type = 'aligned'
            person_id = 1
            sqlController.add_center_of_mass(structure, atlas, x,y,z, person_id, input_type)
        else:
            center = calc_com(origin[0], origin[1], origin[2], volume)
            if '3N' in structure:
                print(structure, atlas, x,y,z, center)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Atlas')
    parser.add_argument('--atlas', help='Enter the atlas', required=True)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    atlas = args.atlas
    create = bool({'true': True, 'false': False}[args.create.lower()])
    insert_origins(atlas, create)

