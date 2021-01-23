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
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids, get_cpus


def create_mesh(animal, chunk):
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/downsampled_cropped')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'mesh_chunk_{chunk}')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)
    limit = 2
    #files = files[midpoint-limit:midpoint+limit]

    file_keys = []
    scales = (2000, 2000, 1000)
    ng = NumpyToNeuroglancer(None, scales)
    chunk_size = [chunk, chunk, 1]
    ng.init_mesh(OUTPUT_DIR, (height, width, len(files)), chunk_size)

    for i, f in enumerate(tqdm(files)):
        filepath = os.path.join(INPUT, f)
        file_keys.append([i,filepath])

    workers = get_cpus()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_slice, file_keys)
        ng.precomputed_vol.cache.flush()

    fake_volume = np.zeros(3) + 255
    ng.add_segment_properties(get_segment_ids(fake_volume))
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--chunk', help='Enter the chunk', required=False, default=256)
    args = parser.parse_args()
    animal = args.animal
    chunk = int(args.chunk)
    create_mesh(animal, chunk)

