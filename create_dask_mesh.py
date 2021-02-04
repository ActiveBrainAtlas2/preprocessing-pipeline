"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys

import imageio
import numpy as np
import shutil

from dask_image.imread import imread
from skimage import io
from tqdm import tqdm
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids


def create_mesh(animal, limit):
    scale = 3
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned')
    """you might want to change the output dir"""
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'meshX')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = imageio.imread(midfilepath)
    height, width = midfile.shape

    ## take a sample from the middle of the stack
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]

    resolution = 1000
    scales = (resolution*scale, resolution*scale, resolution*scale)
    chunk_size = [64, 64, 64]
    volume_size = (width, height, len(files))
    dask = False
    if dask:
        volume = imread(f'{INPUT}/*.tif')
    else:
        """Bili, this is what creates a volume that is passed to CloudVolume.
        It works fine if you can fit the data in RAM, otherwise it won't work."""
        volume = np.zeros((volume_size), dtype=np.uint8)
        for i, f in enumerate(tqdm(files)):
            filepath = os.path.join(INPUT, f)
            img = io.imread(filepath)
            img = np.rot90(img, 1)
            volume[:,:,i] = img

    """The hard part is getting the volume set. Maybe if it were a dask array it might work.
    This creates the CloudVolume from the NumpyToNeuroglancer class"
    """
    ng = NumpyToNeuroglancer(volume, scales, 'segmentation', np.uint8, chunk_size)
    ng.init_volume(OUTPUT_DIR)

    """Don't worry about anything below"""
    fake_volume = np.zeros((1,1), dtype='uint8') + 255
    ng.add_segment_properties(get_segment_ids(fake_volume))
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    create_mesh(animal, limit)

