"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
import numpy as np
from timeit import default_timer as timer
import shutil
from skimage import io
from tqdm import tqdm

HOME = os.path.expanduser("~")
#PATH = os.path.join(HOME, 'programming/pipeline_utility')
#sys.path.append(PATH)
from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from lib.utilities_cvat_neuroglancer import mask_to_shell, NumpyToNeuroglancer
from lib.utilities_process import test_dir, SCALING_FACTOR


def create_shell(animal):
    start = timer()
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'rotated_aligned_masked')
    error = test_dir(animal, INPUT, full=False, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'shell')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))

    volume = []
    for file in tqdm(files):
        tif = io.imread(os.path.join(INPUT, file))
        tif = mask_to_shell(tif)
        volume.append(tif)
    volume = np.array(volume).astype('uint8')
    volume = np.swapaxes(volume, 0, 2)

    resolution = sqlController.scan_run.resolution
    resolution = int(resolution * 1000 / SCALING_FACTOR)
    print('Resolution at', resolution)

    ng = NumpyToNeuroglancer(volume, [resolution, resolution, 20000], offset=[0,0,0])
    ng.init_precomputed(OUTPUT_DIR)
    #ng.add_segment_properties(get_segment_properties())
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()

    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_shell(animal)

