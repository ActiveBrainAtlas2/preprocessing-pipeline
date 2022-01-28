"""
Creates a shell from  aligned masks
"""
import argparse
import os
import sys
import numpy as np
import shutil
from skimage import io
from tqdm import tqdm
from atlas.NgSegmentMaker import NgConverter
from lib.utilities_cvat_neuroglancer import mask_to_shell
from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from lib.utilities_process import test_dir, SCALING_FACTOR
from lib.utilities_create_alignment import parse_elastix, align_section_masks

def align_masks(animal):
    transforms = parse_elastix(animal)
    align_section_masks(animal,transforms)

def create_shell(animal, DEBUG=False):
    '''
    Gets some info from the database used to create the numpy volume from
    the masks. It then turns that numpy volume into a neuroglancer precomputed
    mesh
    :param animal:
    :param DEBUG:
    '''
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'masks', 'rotated_aligned_masked')
    error = test_dir(animal, INPUT, downsample=True, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'shell')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    len_files = len(files)
    midpoint = len_files // 2
    if DEBUG:
        limit = 50
        start = midpoint - limit
        end = midpoint + limit
        files = files[start:end]
    volume = []
    for file in tqdm(files):
        tif = io.imread(os.path.join(INPUT, file))
        tif = mask_to_shell(tif)
        volume.append(tif)
    volume = np.array(volume).astype('uint8')
    volume = np.swapaxes(volume, 0, 2)
    ids = np.unique(volume)
    ids = [(i,i) for i in ids]
    resolution = sqlController.scan_run.resolution
    resolution = int(resolution * 1000 / SCALING_FACTOR)
    ng = NgConverter(volume, [resolution, resolution, 20000], offset=[0,0,0])
    ng.create_neuroglancer_files(OUTPUT_DIR,ids)


if __name__ == '__main__':
    animal = 'DK55'
    align_masks(animal)
    create_shell(animal)

