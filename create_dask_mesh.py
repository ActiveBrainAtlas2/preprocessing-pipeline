import os, sys
import argparse
import shutil

import imagesize
import numpy as np
import dask.array as da
import dask.array
from skimage import io
from tqdm import tqdm
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager



def add_dask_layer(animal, limit, orientation, debug):
    """Adds a lazily-computed data source backed by dask."""
    # https://docs.dask.org/en/latest/array-creation.html#using-dask-delayed
    scale = 1
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/full_aligned')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    data_type = np.uint8
    files = sorted(os.listdir(INPUT))
    if scale > 1:
        files = [f for i, f in enumerate(files) if i % scale == 0]
    ## limit files for testing
    midpoint = len(files) // 2
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]
    lazy_chunks = []

    if 'coronal' in orientation:
        for f in tqdm(files):
            filepath = os.path.join(INPUT, f)
            img = io.imread(filepath)
            if 'bool' in str(img.dtype):
                img = (img * 255).astype(data_type)
            img = np.rot90(img, 2)
            img = np.flip(img)
            lazy_chunks.append(dask.delayed(img.reshape(1, img.shape[0],img.shape[1])))
        img0 = lazy_chunks[0].compute()  # load the first chunk (assume rest are same shape/dtype)
        arrays = [
            dask.array.from_delayed(lazy_chunk, dtype=data_type, shape=img0.shape)
            for lazy_chunk in lazy_chunks
        ]
        volume = dask.array.concatenate(arrays)
        volume = dask.array.swapaxes(volume, 0, 2)

    else:
        files = files[midpoint:-1] # creates the x width in neuroglancer
        filepath = os.path.join(INPUT, files[0])
        width, height = imagesize.get(filepath)
        center = width // 2
        limit = 250 # creates the z (sections) in neuroglancer
        left = center - limit
        right = center + limit
        for f in tqdm(files):
            filepath = os.path.join(INPUT, f)
            img = io.imread(filepath)
            if 'bool' in str(img.dtype):
                img = (img * 255).astype(data_type)
            img = img[:,left:right]
            lazy_chunks.append(dask.delayed(img.reshape(1, img.shape[0],img.shape[1])))

        img0 = lazy_chunks[0].compute()  # load the first chunk (assume rest are same shape/dtype)
        arrays = [
            dask.array.from_delayed(lazy_chunk, dtype=data_type, shape=img0.shape)
            for lazy_chunk in lazy_chunks
        ]
        volume = dask.array.concatenate(arrays)

    if debug:
        print('img0',type(img0), np.shape(img0))
        print('dask',type(volume), np.shape(volume))
        #sys.exit()
    resolution = 1000 * scale
    ids = [(255, '255: 255')]

    scales = (resolution, resolution, resolution)
    ng = NumpyToNeuroglancer(volume.compute(), scales,
                             layer_type='segmentation', data_type=np.uint8, chunk_size=[512, 512, 16])
    del volume
    ng.init_volume(OUTPUT_DIR)
    ng.add_segment_properties(ids)
    ng.add_segmentation_mesh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--orientation', help='Enter orientation {coronal|sagittal}', required=False, default='coronal')
    parser.add_argument('--debug', help='debug?', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    orientation = args.orientation
    limit = int(args.limit)
    debug = bool({'true': True, 'false': False}[args.debug.lower()])
    add_dask_layer(animal, limit, orientation, debug)
