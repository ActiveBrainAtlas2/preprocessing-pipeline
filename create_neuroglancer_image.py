"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor
from skimage import io

import imagesize
import numpy as np
import shutil

from PIL import Image


from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import SCALING_FACTOR, test_dir
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids, get_cpus
from sql_setup import CREATE_NEUROGLANCER_TILES_CHANNEL_1_THUMBNAILS, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES, \
    RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_1_FULL_RES


def create_layer(animal, channel, full, limit, suffix=None):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    channel_outdir = 'C{}T'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    sqlController.set_task(animal, CREATE_NEUROGLANCER_TILES_CHANNEL_1_THUMBNAILS)
    resolution = sqlController.scan_run.resolution
    resolution = int(resolution * 1000 / SCALING_FACTOR)

    if full:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
        channel_outdir = 'C{}'.format(channel)
        if channel == 3:
            sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES)
        elif channel == 2:
            sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES)
        else:
            sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_1_FULL_RES)

        if 'thion' in sqlController.histology.counterstain:
            sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES)
            sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES)

        resolution = sqlController.scan_run.resolution
        resolution = int(resolution * 1000)

    voxel_resolution = (resolution, resolution, 20000)

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, '{}'.format(channel_outdir))
    if suffix is not None:
        OUTPUT_DIR += suffix
    if os.path.exists(OUTPUT_DIR):
        print(f'Directory: {OUTPUT_DIR} exists.')
        print('You need to manually delete it. Exiting ...')
        sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    error = test_dir(animal, INPUT, full, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()


    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    sample_img = io.imread((midfilepath))
    height, width = sample_img.shape
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]

    chunk_size = [64, 64, 1]
    volume_size = (width, height, len(files))

    ng = NumpyToNeuroglancer(None, voxel_resolution, 'image', sample_img.dtype, chunk_size)
    ng.init_precomputed(OUTPUT_DIR, volume_size)
    del sample_img

    filekeys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        filekeys.append([i, infile])
        #ng.process_slice([i, infile])

    workers = get_cpus()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_slice, filekeys)
        ng.precomputed_vol.cache.flush()


    ng.add_downsampled_volumes()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--limit', help='Enter limit', required=False, default=0)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=False, default='thumbnail')
    parser.add_argument('--suffix', help='Enter suffix to add to the output dir', required=False, default=None)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    limit = int(args.limit)
    full = bool({'full': True, 'thumbnail': False}[args.resolution])
    suffix = args.suffix
    create_layer(animal, channel, full, limit, suffix)


