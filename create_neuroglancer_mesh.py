"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor
from skimage import io
from timeit import default_timer as timer
import imagesize
import numpy as np
import shutil

from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_cpus

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def create_mesh(animal, limit):
    scale = 10
    chunk = 256
    zchunk = 128
    data_type = np.uint8
    resolution = 1000 * scale
    scales = (resolution, resolution, resolution)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/full_aligned')
    files = sorted(os.listdir(INPUT))
    channel_outdir = 'mesh'
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, channel_outdir)
    PROGRESS_DIR = os.path.join(fileLocationManager.prep, 'progress', f'{channel_outdir}')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)

    if scale > 1:
        INPUT = os.path.join(fileLocationManager.prep, 'CH1/downsampled_10')
        files = sorted(os.listdir(INPUT))
        files = [f for i,f in enumerate(files) if i % scale == 0]
        chunk = 64
        zchunk = chunk
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
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
    volume_size = (height, width, len(files))
    print('volume size', volume_size)
    ng = NumpyToNeuroglancer(None, scales, layer_type='segmentation', data_type=data_type, chunk_size=[chunk, chunk, 1])
    ng.init_precomputed(OUTPUT_DIR, volume_size, starting_points=starting_points, progress_dir=PROGRESS_DIR)

    filekeys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        filekeys.append([i, infile])

    start = timer()
    workers = min(get_cpus(), 2)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_coronal_slice, filekeys)

    end = timer()

    print(f'simple slice Method took {end - start} seconds')
    dir_count = len(next(os.walk(OUTPUT_DIR))[1])
    if dir_count < 2:
        ids = [(255, '255: 255')]
        ng.add_segment_properties(ids)
        ng.add_downsampled_volumes(chunk_size=[chunk, chunk, zchunk])
        ng.add_segmentation_mesh()
    else:
        print('Already calculated downsamples.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    create_mesh(animal, limit)

