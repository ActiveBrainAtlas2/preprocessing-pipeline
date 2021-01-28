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

from dask_image.imread import imread
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
    COPY_FROM = os.path.join(fileLocationManager.prep, 'CH1/downsampled_cropped')
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/small')
    if os.path.exists(INPUT):
        shutil.rmtree(INPUT)
    os.makedirs(INPUT, exist_ok=True)
    scale = 2
    allfiles = sorted(os.listdir(COPY_FROM))
    for i, f in enumerate(allfiles):
        if i % scale == 0:
            source = os.path.join(COPY_FROM, f)
            dest = os.path.join(INPUT, f)
            shutil.copy(source, dest)
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(allfiles) // 2
    midfilepath = os.path.join(COPY_FROM, allfiles[midpoint])
    width, height = imagesize.get(midfilepath)
    file_keys = []

    resolution = 1000
    scales = (resolution*scale, resolution*scale, resolution*scale)
    chunk_size = [64, 64, 64]
    volume_size = (width, height, len(files))
    usedask = True
    if usedask:
        bigdask = imread(f'{INPUT}/*.tif')
        outpath = os.path.join(fileLocationManager.prep, 'bigarray.npy')
        bigarray = np.memmap(outpath, dtype=np.uint8, mode="w+", shape=(len(files), height, width))
        bigarray[:] = bigdask
        bigarray = np.swapaxes(bigarray, 0, 2)
        ng = NumpyToNeuroglancer(bigarray, scales, 'segmentation', np.uint8, chunk_size)
        ng.init_volume(OUTPUT_DIR)
        del bigarray
    else:
        for i, f in enumerate(files):
            filepath = os.path.join(INPUT, f)
            file_keys.append([i, filepath])
        ng.init_precomputed(OUTPUT_DIR, volume_size)

        with ProcessPoolExecutor(max_workers=1) as executor:
            executor.map(ng.process_slice, file_keys)
            ng.precomputed_vol.cache.flush()

    fake_volume = np.zeros(3) + 255
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

