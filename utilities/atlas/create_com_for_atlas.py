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

        #x,y,z = (origin + ndimage.measurements.center_of_mass(volume))

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
            sqlController.add_center_of_mass(structure, atlas, x,y,z)
        else:
            print(structure, atlas, x,y,z)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Atlas')
    parser.add_argument('--atlas', help='Enter the atlas', required=True)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    atlas = args.atlas
    create = bool({'true': True, 'false': False}[args.create.lower()])
    insert_origins(atlas, create)

