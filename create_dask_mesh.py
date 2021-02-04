"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys

import imageio
import numpy as np
import shutil

from dask_image.imread import imread
from skimage import io
from tqdm import tqdm
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids


def create_mesh(animal, limit, chunk, debug):
    scale = 3
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned')
    """you might want to change the output dir"""
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'mesh_chunk_{chunk}')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = imageio.imread(midfilepath)
    height, width = midfile.shape

    ## take a sample from the middle of the stack
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]

    resolution = 1000
    scales = (resolution*scale, resolution*scale, resolution*scale)
    chunk_size = [chunk, chunk, chunk]
    volume_size = (width, height, len(files))
    data_type = np.uint8
    volume = np.zeros((volume_size), dtype=data_type)
    for i, f in enumerate(tqdm(files)):
        filepath = os.path.join(INPUT, f)
        img = io.imread(filepath)
        img = np.rot90(img, 1)
        if debug:
            print(img.dtype, np.amin(img), np.amax(img))
            continue
        volume[:,:,i] = img

    if debug:
        sys.exit()
    """The hard part is getting the volume set. Maybe if it were a dask array it might work.
    This creates the CloudVolume from the NumpyToNeuroglancer class"
    """
    ng = NumpyToNeuroglancer(volume, scales, 'segmentation', data_type, chunk_size)
    ng.init_volume(OUTPUT_DIR)

    """Don't worry about anything below"""
    fake_volume = np.zeros((1,1), dtype=data_type) + 255
    ng.add_segment_properties(get_segment_ids(fake_volume))
    ng.add_downsampled_volumes(chunk_size=chunk_size)
    ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--chunk', help='Enter the chunk size', required=True)
    parser.add_argument('--debug', help='debug?', required=True)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    chunk = int(args.chunk)
    debug = bool({'true': True, 'false': False}[args.debug.lower()])
    create_mesh(animal, limit, chunk, debug)

