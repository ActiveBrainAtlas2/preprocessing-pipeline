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


Image.MAX_IMAGE_PIXELS = None
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import SCALING_FACTOR
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids, get_cpus


def create_layer(animal, limit, channel, layer_type, resolution):
    fileLocationManager = FileLocationManager(animal)

    scale = 1
    destination = 'mesh'
    data_type = np.uint8
    source = f'CH{channel}/{resolution}_aligned'
    sqlController = SqlController(animal)
    planar_resolution = sqlController.scan_run.resolution
    planar_resolution = int(planar_resolution * 1000 / SCALING_FACTOR)
    voxel_resolution = (1000*scale, 1000*scale, 1000*scale)
    if layer_type == 'image':
        source = f'CH{channel}/{resolution}_aligned'
        destination = f'C{channel}_{resolution}'
        layer_type = 'image'
        data_type = np.uint16
        voxel_resolution = [planar_resolution, planar_resolution, 20000]
    print(voxel_resolution)
    INPUT = os.path.join(fileLocationManager.prep, source)
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, destination)
    if os.path.exists(OUTPUT_DIR):
        print(f'Directory: {OUTPUT_DIR} exists.')
        print('You need to manually delete it. Exiting ...')
        sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)
    if limit > 0:
        midpoint = len(files) // 2
        files = files[midpoint-limit:midpoint+limit]

    chunk_size = [64, 64, 1]
    if layer_type == 'segmentation':
        volume_size = (height, width, len(files))
    else:
        volume_size = (width, height, len(files))

    ng = NumpyToNeuroglancer(None, voxel_resolution, layer_type, data_type, chunk_size)
    ng.init_precomputed(OUTPUT_DIR, volume_size)

    filekeys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        filekeys.append([i, infile])
        #ng.process_slice([i, infile])

    workers = get_cpus()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_slice, filekeys)
        ng.precomputed_vol.cache.flush()


    if layer_type == 'segmentation':
        fake_volume = io.imread(midfilepath)
        ng.add_segment_properties(get_segment_ids(fake_volume))

    ng.add_downsampled_volumes()

    if 'seg' in layer_type:
        ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the chunk', required=False, default=0)
    parser.add_argument('--channel', help='Enter the channel', required=False, default=1)
    parser.add_argument('--layer_type', help='Enter the layer type', required=False, default='image')
    parser.add_argument('--resolution', help='Enter resolution', required=False, default='thumbnail')

    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    channel = int(args.channel)
    layer_type = str(args.layer_type).strip().lower()
    resolution = str(args.resolution).strip().lower()
    create_layer(animal, limit, channel, layer_type, resolution)

