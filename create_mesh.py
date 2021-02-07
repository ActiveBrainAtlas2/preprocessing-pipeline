"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys

import imageio
import numpy as np
import shutil

from skimage import io
from tqdm import tqdm
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer


def create_mesh(animal, limit, debug):
    scale = 1
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/full_aligned')
    """you might want to change the output dir"""
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_sagittal_200')
    if os.path.exists(OUTPUT_DIR):
        print(f'DIR {OUTPUT_DIR} exists, exiting.')
        sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = imageio.imread(midfilepath)
    height, width = midfile.shape
    if scale > 1:
        files = [f for i,f in enumerate(files) if i % scale == 0]
    ## take a sample from the middle of the stack
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]

    resolution = 1000*scale
    scales = (resolution, resolution, resolution)
    center = width // 2
    limit = 100
    left = center - limit
    right = center + limit
    width = right - left

    volume_size = (height, width, len(files))
    data_type = np.uint8
    volume = np.zeros((volume_size), dtype=data_type)

    for i, f in enumerate(tqdm(files)):
        filepath = os.path.join(INPUT, f)
        if debug:
            print(img.dtype, np.amin(img), np.amax(img), np.unique(img, return_counts=True))
            continue
        img = io.imread(filepath)
        if 'bool' in str(img.dtype):
            img = (img * 255).astype(data_type)
        img = img[:, left:right]
        volume[:,:,i] = img

    volume = np.rot90(volume, axes=(2, 1))
    volume = np.rot90(volume, 3)
    volume = np.flip(volume, axis=1)
    if debug:
        print('volume shape', volume.shape)
        sys.exit()

    ids = [(255, '255: 255')]
    ng = NumpyToNeuroglancer(volume, scales,
                             layer_type='segmentation', data_type=np.uint8, chunk_size=[16, 16, 1])
    ng.init_volume(OUTPUT_DIR)
    del volume
    ng.add_segment_properties(ids)
    ng.add_segmentation_mesh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--debug', help='debug?', required=True)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    debug = bool({'true': True, 'false': False}[args.debug.lower()])
    create_mesh(animal, limit, debug)

