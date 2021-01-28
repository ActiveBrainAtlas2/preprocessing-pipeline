"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor

import imageio
import imagesize
import numpy as np
import shutil

from dask_image.imread import imread
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import dask
import dask.array as da
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids, get_cpus


def create_mesh(animal):
    fileLocationManager = FileLocationManager(animal)
    COPY_FROM = os.path.join(fileLocationManager.prep, 'CH1/downsampled_33')
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/small')
    allfiles = sorted(os.listdir(COPY_FROM))
    scale = 3
    if os.path.exists(INPUT):
        shutil.rmtree(INPUT)
    os.makedirs(INPUT, exist_ok=True)
    for i, f in enumerate(allfiles):
        if i % scale == 0:
            source = os.path.join(COPY_FROM, f)
            dest = os.path.join(INPUT, f)
            shutil.copy(source, dest)
    sys.exit()
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(allfiles) // 2
    midfilepath = os.path.join(COPY_FROM, allfiles[midpoint])
    midfile = imageio.imread(midfilepath)
    height, width = midfile.shape
    print('shape', height, width)

    resolution = 1000
    scales = (resolution*scale, resolution*scale, resolution*scale)
    chunk_size = [64, 64, 64]
    volume_size = (width, height, len(files))
    bigdask = imread(f'{INPUT}/*.tif')
    outpath = os.path.join(fileLocationManager.prep, 'bigarray.npy')
    bigarray = np.memmap(outpath, dtype=np.uint8, mode="w+", shape=(len(files), height, width))
    bigarray[:] = bigdask
    bigarray = np.swapaxes(bigarray, 0, 2)
    ng = NumpyToNeuroglancer(bigarray, scales, 'segmentation', np.uint8, chunk_size)
    ng.init_volume(OUTPUT_DIR)
    del bigarray

    fake_volume = np.zeros(3) + 255
    ng.add_segment_properties(get_segment_ids(fake_volume))
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_mesh(animal)

