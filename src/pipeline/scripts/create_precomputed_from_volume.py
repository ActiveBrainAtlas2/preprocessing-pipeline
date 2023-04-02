"""
Creates a 3D Mesh
"""
import argparse
import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import shutil
from pathlib import Path
import numpy as np
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.image_manipulation.filelocation_manager import FileLocationManager
from library.image_manipulation.neuroglancer_manager import NumpyToNeuroglancer
from library.utilities.utilities_process import get_hostname, read_image

def create_precomputed(animal, volume_file):
    chunk = 64
    chunks = (chunk, chunk, chunk)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'registered')
    outpath = os.path.basename(volume_file)
    outpath = outpath.split('.')[0]
    IMAGE_INPUT = os.path.join(fileLocationManager.neuroglancer_data, f'input_{outpath}')
    scales = (20000, 20000, 20000)
    if 'godzilla' in get_hostname():
        print(f'Cleaning {IMAGE_INPUT}')
        if os.path.exists(IMAGE_INPUT):
            shutil.rmtree(IMAGE_INPUT)


    os.makedirs(IMAGE_INPUT, exist_ok=True)
    midfilepath = os.path.join(INPUT, volume_file)
    volume = read_image(midfilepath)
    volume = np.swapaxes(volume, 0, 2)
    #num_channels = volume.shape[2] if len(volume.shape) > 2 else 1
    num_channels = 1
    volume_size = volume.shape

    ng = NumpyToNeuroglancer(
        animal,
        None,
        scales,
        "image",
        volume.dtype,
        num_channels=num_channels,
        chunk_size=chunks,
    )

    ng.init_precomputed(IMAGE_INPUT, volume_size)
    ng.precomputed_vol[:, :, :] = volume
    ng.precomputed_vol.cache.flush()
    tq = LocalTaskQueue(parallel=4)
    cloudpath = f"file://{IMAGE_INPUT}"
    tasks = tc.create_downsampling_tasks(cloudpath, num_mips=2)
    tq.insert(tasks)
    tq.execute()


    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--volume', help='Enter the name of the volume file', required=False, default='downsampled_standard.tiff')
    args = parser.parse_args()
    animal = args.animal
    volume = args.volume
    
    create_precomputed(animal, volume)

