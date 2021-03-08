"""
Creates a 3D Mesh
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor
from skimage import io
from timeit import default_timer as timer
import numpy as np
from taskqueue.taskqueue import LocalTaskQueue
import igneous.task_creation as tc

from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, calculate_chunks, get_cpus, get_segment_ids

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def create_mesh(animal, limit):
    chunks = calculate_chunks('full', -1)
    data_type = np.uint8
    resolution = 1000 
    scales = (resolution, resolution, resolution)
    fileLocationManager = FileLocationManager(animal)
    #INPUT = "/net/birdstore/Vessel/WholeBrain/ML_2018_08_15/visualization/Neuroglancer_cc"
    INPUT = os.path.join(fileLocationManager.prep, 'CH2', 'full_aligned')
    files = sorted(os.listdir(INPUT))
    OUTPUT1_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_input')
    OUTPUT2_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    PROGRESS_DIR = os.path.join(fileLocationManager.prep, 'progress', 'mesh_input')

    os.makedirs(OUTPUT1_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)

    len_files = len(files)
    midpoint = len_files // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
    ids = [  0,   8,  16,  24,  32,  40,  48,  56,  64,  72,  80,  88,  96,
       104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 200,
       208, 216, 224, 232, 240, 248, 255]
    ids = [(number, f'{number}: {number}') for number in ids]

    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]
    height, width = midfile.shape
    startx = 0
    endx = midfile.shape[1]
    starty = 0
    endy = midfile.shape[0]
    height = endy - starty
    width = endx - startx
    starting_points = [starty,endy, startx,endx]
    volume_size = (width, height, len(files)) # neuroglancer is width, height
    print('volume size', volume_size)
    ng = NumpyToNeuroglancer(None, scales, layer_type='segmentation', data_type=data_type, chunk_size=chunks)
    ng.init_precomputed(OUTPUT1_DIR, volume_size, starting_points=starting_points, progress_dir=PROGRESS_DIR)

    file_keys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        file_keys.append([i, infile])

    start = timer()
    workers, cpus = get_cpus()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_mesh, sorted(file_keys), chunksize=workers)
        executor.shutdown(wait=True)

    volume = ng.precomputed_vol
    ng.precomputed_vol.cache.flush()


    end = timer()
    print(f'Create volume method took {end - start} seconds')

    chunks = [256,256,128]
    ng = NumpyToNeuroglancer(volume, scales, layer_type='segmentation', 
        data_type=data_type, chunk_size=chunks)
    ng.init_volume(OUTPUT2_DIR)

    ng.add_segment_properties(ids)

    start = timer()
    ng.add_rechunking(OUTPUT2_DIR, downsample='full', chunks=chunks)

    ng.add_segmentation_mesh()

    end = timer()
    print(f'Downsampling took {end - start} seconds')


    print('Finished')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    create_mesh(animal, limit)

