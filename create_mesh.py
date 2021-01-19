"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys

import imagesize
import numpy as np
from timeit import default_timer as timer
import shutil
from skimage import io
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids
from utilities.utilities_mask import rotate_image


def create_shell(animal):
    start = timer()
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    rows, columns = imagesize.get(midfilepath)
    files = files[midpoint-3000: midpoint+3000]
    volume = np.empty((columns, rows, len(files)))
    bigarray_path = os.path.join(fileLocationManager.prep, 'bigarray.npy')
    volume = np.memmap(bigarray_path, mode='w+', shape=volume.shape)

    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        tif = io.imread(infile)
        # tif = np.flip(tif, axis=1)
        # tif = rotate_image(tif, infile, 1)
        volume[:,:,i] = tif

    print(volume.shape)
    ng = NumpyToNeuroglancer(volume.astype(np.uint8), [10000, 10000, 1000], offset=[0,0,0])
    ng.init_precomputed(OUTPUT_DIR)
    fake_volume = np.zeros(3) + 255
    del volume
    ng.add_segment_properties(get_segment_ids(fake_volume))

    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()

    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_shell(animal)

