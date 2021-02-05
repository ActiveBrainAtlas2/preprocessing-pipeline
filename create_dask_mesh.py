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
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_sagittal')
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

    resolution = 1000
    scales = (resolution*scale, resolution*scale, resolution*scale)
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
        img = io.imread(filepath)
        #img = np.rot90(img, 1)
        if 'bool' in str(img.dtype):
            img = (img * 255).astype(data_type)
        img = img[:, left:right]
        if debug:
            print(img.dtype, np.amin(img), np.amax(img), np.unique(img, return_counts=True))
            continue
        #img = img.reshape(img.shape[0], 1, img.shape[1])
        volume[:,:,i] = img

    volume = np.rot90(volume, axes=(2, 1))
    volume = np.rot90(volume, 3)
    volume = np.flip(volume, axis=1)
    midpoint = volume.shape[2] // 2
    #volume = volume[:,:,midpoint-50:midpoint+50]
    if debug:
        print('volume shape', volume.shape)
        sys.exit()
    """The hard part is getting the volume set. Maybe if it were a dask array it might work.
    This creates the CloudVolume from the NumpyToNeuroglancer class"
    """

    ids = [(255, '255: 255')]
    ng = NumpyToNeuroglancer(volume, scales,
                             layer_type='segmentation', data_type=np.uint8, chunk_size=[128, 128, 16])
    ng.init_volume(OUTPUT_DIR)
    ng.add_segment_properties(ids)
    ng.add_downsampled_volumes()
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

