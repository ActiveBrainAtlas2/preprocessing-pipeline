"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor

from skimage import io
import numpy as np
from timeit import default_timer as timer

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, calculate_chunks, get_cpus
from utilities.sqlcontroller import SqlController
from sql_setup import CREATE_NEUROGLANCER_TILES_CHANNEL_1_THUMBNAILS, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_1_FULL_RES, \
    RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES
from utilities.utilities_process import test_dir, SCALING_FACTOR

def create_neuroglancer(animal, channel, downsample, suffix, debug=False):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = f'CH{channel}'
    channel_outdir = f'C{channel}T_rechunkme'
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    sqlController.set_task(animal, CREATE_NEUROGLANCER_TILES_CHANNEL_1_THUMBNAILS)
    db_resolution = sqlController.scan_run.resolution
    resolution = int(db_resolution * 1000 / SCALING_FACTOR)
    workers, _ = get_cpus()
    chunks = calculate_chunks(downsample, -1)

    if not downsample:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
        workers = workers // 2
        channel_outdir = f'C{channel}_rechunkme'
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

    error = test_dir(animal, INPUT, downsample, same_size=True)
    if len(error) > 0 and not debug:
        print(error)
        sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
    height = midfile.shape[0]
    width = midfile.shape[1]
    num_channels = midfile.shape[3] if len(midfile.shape) > 3 else 1

    file_keys = []
    scales = (resolution, resolution, 20000)
    volume_size = (width, height, len(files))
    print('Volume shape:', volume_size)

    ng = NumpyToNeuroglancer(None, scales, 'image', midfile.dtype, chunk_size=chunks)
    ng.init_precomputed(OUTPUT_DIR, volume_size, num_channels=num_channels, progress_dir=PROGRESS_DIR)

    for i, f in enumerate(files):
        filepath = os.path.join(INPUT, f)
        file_keys.append([i,filepath])

    start = timer()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_image, sorted(file_keys), chunksize=workers)
        executor.shutdown(wait=True)

    ng.precomputed_vol.cache.flush()

    end = timer()
    print(f'Create volume method took {end - start} seconds')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--suffix', help='Enter suffix to add to the output dir', required=False)
    parser.add_argument('--debug', help='Enter debug True|False', required=False, default='false')

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    suffix = args.suffix
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])

    create_neuroglancer(animal, channel, downsample, suffix, debug)

