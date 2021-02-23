"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor

import imagesize
import numpy as np
from tqdm import tqdm
from timeit import default_timer as timer

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_cpus
from utilities.sqlcontroller import SqlController
from sql_setup import CREATE_NEUROGLANCER_TILES_CHANNEL_1_THUMBNAILS, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_1_FULL_RES, \
    RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES
from utilities.utilities_process import test_dir, SCALING_FACTOR

def create_neuroglancer(animal, channel, downsample, mips, suffix):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    channel_outdir = 'C{}T'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, f'{downsample}_aligned')
    sqlController.set_task(animal, CREATE_NEUROGLANCER_TILES_CHANNEL_1_THUMBNAILS)
    db_resolution = sqlController.scan_run.resolution
    resolution = int(db_resolution * 1000 / SCALING_FACTOR)
    downsample_bool = False
    chunk = 64
    zchunk = chunk

    if downsample == 'full':
        chunk = 128
        zchunk = 64
        downsample_bool = True
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

        resolution = int(db_resolution * 1000)

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')
    PROGRESS_DIR = os.path.join(fileLocationManager.prep, 'progress', f'{channel_outdir}')
    if suffix is not None:
        OUTPUT_DIR += suffix

    error = test_dir(animal, INPUT, downsample_bool, same_size=True)
    #error = ""
    if len(error) > 0:
        print(error)
        sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)

    file_keys = []
    scales = (resolution, resolution, 20000)
    volume_size = (width, height, len(files))
    print('vol size', volume_size)

    ng = NumpyToNeuroglancer(None, scales, 'image', np.uint16, chunk_size=[chunk, chunk, 1])
    ng.init_precomputed(OUTPUT_DIR, volume_size, progress_dir=PROGRESS_DIR)

    for i, f in enumerate(tqdm(files)):
        filepath = os.path.join(INPUT, f)
        file_keys.append([i,filepath])

    start = timer()
    workers, _ = get_cpus()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_image, sorted(file_keys))
        ng.precomputed_vol.cache.flush()

    end = timer()
    print(f'Create volume method took {end - start} seconds')

    if mips > 0:
        start = timer()
        ng.add_downsampled_volumes(chunk_size=[chunk, chunk, zchunk], num_mips=mips)
        end = timer()
        print(f'Finito! Downsampling method took {end - start} seconds')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--mips', help='Enter mips', required=False, default=0)
    parser.add_argument('--downsample', help='Enter full or thumbnail', required=False, default='thumbnail')
    parser.add_argument('--suffix', help='Enter suffix to add to the output dir', required=False)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    mips = int(args.mips)
    downsample = args.downsample
    suffix = args.suffix
    create_neuroglancer(animal, channel, downsample, mips, suffix)

