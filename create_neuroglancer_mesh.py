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
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids, get_cpus


def create_mesh(animal, limit, debug):
    scale = 1
    chunk = 256
    zchunk = 128
    data_type = np.uint8
    resolution = 1000 * scale
    scales = (resolution, resolution, resolution)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/full_aligned')
    """you might want to change the output dir"""
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_midsagittal')
    if os.path.exists(OUTPUT_DIR) and not debug:
        print(f'DIR {OUTPUT_DIR} exists, removing.')
        shutil.rmtree((OUTPUT_DIR))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    if scale > 1:
        files = [f for i,f in enumerate(files) if i % scale == 0]
        chunk = 64
        zchunk = chunk
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
    height, width = midfile.shape
    startx = 0
    endx = width // 2
    starty = height // 2
    endy = midfile.shape[0]
    height = endy - starty
    width = endx - startx
    starting_points = [starty,endy, startx,endx]
    volume_size = (height, width, len(files))
    print('volume size', height, width, len(files))
    ng = NumpyToNeuroglancer(None, scales, layer_type='segmentation', data_type=data_type, chunk_size=[chunk, chunk, 1])
    ng.init_precomputed(OUTPUT_DIR, volume_size, starting_points)

    filekeys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        filekeys.append([i, infile])

    start = timer()
    with ProcessPoolExecutor(max_workers=2) as executor:
        executor.map(ng.process_coronal_slice, filekeys)
        ng.precomputed_vol.cache.flush()
    end = timer()

    print(f'Finito! Method took {end - start} seconds')
    print(ng.precomputed_vol.shape)

    ids = [(255, '255: 255')]
    ng.add_segment_properties(ids)
    ng.add_downsampled_volumes(chunk_size=[chunk, chunk, zchunk])
    ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--debug', help='debug?', required=True)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    debug = bool({'true': True, 'false': False}[args.debug.lower()])
    create_mesh(animal, limit, debug)

