"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor

import imagesize
import numpy as np
import shutil

from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids, get_cpus


def create_mesh(animal, limit):
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/downsampled_33')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    scale = 3
    allfiles = sorted(os.listdir(INPUT))
    files = [f for i,f in enumerate(allfiles) if i % scale == 0]
    midpoint = len(allfiles) // 2
    midfilepath = os.path.join(INPUT, allfiles[midpoint])
    width, height = imagesize.get(midfilepath)
    if limit > 0:
        midpoint = len(files) // 2
        files = files[midpoint-limit:midpoint+limit]

    resolution = 1000 * scale
    scales = (resolution, resolution, resolution)
    chunk_size = [64, 64, 64]
    volume_size = (width, height, len(files))
    volume = np.zeros(volume_size, dtype=np.uint8)
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        image = Image.open(infile)
        width, height = image.size
        array = np.array(image, dtype=np.uint8, order='F')
        array = array.reshape((height, width,1)).T
        volume[:, :, i] = array
        image.close()

    ng = NumpyToNeuroglancer(volume.astype(np.uint8), scales, 'segmentation', np.uint8, chunk_size)
    del volume
    ng.init_volume(OUTPUT_DIR)

    fake_volume = np.zeros(3, dtype=np.uint8) + 255
    ng.add_segment_properties(get_segment_ids(fake_volume))
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the chunk', required=False, default=0)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    create_mesh(animal, limit)

