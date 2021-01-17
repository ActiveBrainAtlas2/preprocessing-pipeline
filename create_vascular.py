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
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import section_to_points, NumpyToNeuroglancer


def create_shell(animal):
    start = timer()
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned')

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'shell')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))

    volume = []
    for file in tqdm(files):
        tif = io.imread(os.path.join(INPUT, file))
        #tif = section_to_points(tif)
        volume.append(tif)
    volume = np.array(volume).astype('uint8')
    #volume = np.swapaxes(volume, 0, 2)

    ng = NumpyToNeuroglancer(volume, [10000, 10000, 1000], offset=[0,0,0])
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

