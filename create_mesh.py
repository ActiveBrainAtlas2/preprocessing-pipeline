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
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/downsampled_cropped')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'mesh_{limit}')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]

    file_keys = []
    scales = (2000, 2000, 1000)
    chunk_size = [64, 64, 64]
    volume_size = (width, height, len(files))
    usememmap = True
    ng = NumpyToNeuroglancer(scales, 'segmentation', np.uint8, chunk_size)
    if usememmap:
        outpath = os.path.join(fileLocationManager.prep, 'bigarray.npy')
        bigarray = np.memmap(outpath, dtype=np.uint8, mode="w+", shape=volume_size)
        for i,f in enumerate(files):
            infile = os.path.join(INPUT, f)
            image = Image.open(infile)
            width, height = image.size
            array = np.array(image, dtype=np.uint8, order='F')
            #array = array.reshape((1, height, width)).T
            array = array.reshape((height, width)).T
            print(infile, array.shape, bigarray.shape)
            bigarray[:, :, i] = array
            image.close()



        ng.volume = bigarray
        ng.init_volume(OUTPUT_DIR)
    else:
        ng.init_precomputed(OUTPUT_DIR, volume_size)
        for i in range(0, len(files)):
            filepath = os.path.join(INPUT, files[i])
            file_keys.append([i,filepath])

        workers = get_cpus()
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

