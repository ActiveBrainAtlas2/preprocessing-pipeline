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

from utilities.utilities_process import SCALING_FACTOR

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_cpus
from utilities.sqlcontroller import SqlController

def run_neuroglancer(animal, channel, downsample, suffix=None):

    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    channel_dir = 'CH{}'.format(channel)
    channel_outdir = 'C{}T'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, '{}'.format(channel_outdir))
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    limit = 25
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)
    resolution = sqlController.scan_run.resolution
    resolution = int(resolution * 1000 / SCALING_FACTOR)

    #files = files[midpoint-limit:midpoint+limit]
    file_keys = []
    scales = (resolution, resolution, 20000)
    chunk_size = [256, 256, 1]
    volume_size = (width, height, len(files))

    ng = NumpyToNeuroglancer(None, scales, 'image', np.uint16, chunk_size)
    ng.init_precomputed(OUTPUT_DIR, volume_size)

    for i, f in enumerate(tqdm(files)):
        filepath = os.path.join(INPUT, f)
        file_keys.append([i,filepath])
        ng.process_slice((i, filepath))

    #with ProcessPoolExecutor(max_workers=1) as executor:
    #    executor.map(ng.process_pillow_slice, file_keys)
    #    ng.precomputed_vol.cache.flush()

    ng.add_downsampled_volumes()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=False, default='thumbnail')
    parser.add_argument('--suffix', help='Enter suffix to add to the output dir', required=False, default=None)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    resolution = args.resolution
    suffix = args.suffix
    run_neuroglancer(animal, channel, resolution, suffix)

