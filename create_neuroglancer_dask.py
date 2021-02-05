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


def create_mesh(animal, limit):
    fileLocationManager = FileLocationManager(animal)

    scale = 10
    data_type = np.uint8
    voxel_resolution = (1000*scale, 1000*scale, 1000*scale)
    INPUT = os.path.join(fileLocationManager.prep, f'CH1/downsampled_10')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_10')
    if os.path.exists(OUTPUT_DIR):
        print(f'Directory: {OUTPUT_DIR} exists.')
        shutil.rmtree(OUTPUT_DIR)
        #sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)
    files = [f for i,f in enumerate(files) if i % scale == 0]
    if limit > 0:
        midpoint = len(files) // 2
        files = files[midpoint-limit:midpoint+limit]
        #files = files[-limit:]
    volume_size = (width, height, len(files))

    ng = NumpyToNeuroglancer(None, voxel_resolution, 'segmentation', data_type, volume_size)
    ng.init_delayed_mesh(OUTPUT_DIR, volume_size)

    filekeys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        filekeys.append([i, infile])
        #ng.process_slice([i, infile])

    workers = get_cpus()
    start = timer()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_slice, filekeys)
    end = timer()

    print(f'Finito! Method took {end - start} seconds')

    ids = [(255, '255: 255')]
    ng.add_segment_properties(ids)
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the limit', required=False, default=0)

    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    create_mesh(animal, limit)

