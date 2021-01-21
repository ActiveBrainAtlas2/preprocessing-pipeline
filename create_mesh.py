"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
import imagesize
import numpy as np
import shutil
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_ids


def create_mesh(animal):
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/full_aligned')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh2')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)

    ## limit
    files = files[midpoint-2000:midpoint+2000]

    file_keys = []
    scales = (1000, 1000, 1000)
    #volume = np.empty((height, width, len(files)))
    ng = NumpyToNeuroglancer(None, scales)
    ng.init_mesh(OUTPUT_DIR, (height, width, len(files)))

    #with ProcessPoolExecutor(max_workers=2) as executor:
    #    executor.map(ng.process_slice, file_keys)
    #    #ng.volume.cache.flush()
    #for file_key in file_keys:
    for i, f in enumerate(tqdm(files)):
        filepath = os.path.join(INPUT, f)
        #file_keys.append([i,filepath])
        ng.process_slice((i,filepath))

    fake_volume = np.zeros(3) + 255
    ng.add_segment_properties(get_segment_ids(fake_volume))
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_mesh(animal)

