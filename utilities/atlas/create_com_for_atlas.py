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
        x,y,z = (origin + ndimage.measurements.center_of_mass(volume))
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

