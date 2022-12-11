"""
This takes the a stack of tifs and creates a numpy array
3D (volume)
"""
import argparse
import os
import sys
import numpy as np
from pathlib import Path
from skimage import io
from tqdm import tqdm

PIPELINE_ROOT = Path('./src/pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from image_manipulation.filelocation_manager import FileLocationManager

def get_file_information(INPUT):
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath, img_num=0)
    rows = midfile.shape[0]
    columns = midfile.shape[1]
    volume_size = (rows, columns, len(files))
    return files, volume_size



def create_volume(animal):
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_aligned')
    OUTPUT = os.path.join(fileLocationManager.prep, 'CH1', 'image_stack.tif')
    files, volume_size = get_file_information(INPUT)
    image_stack = np.zeros(volume_size)
    for i in tqdm(range(len(files))):
        ffile = str(i).zfill(3) + '.tif'
        fpath = os.path.join(INPUT, ffile)
        farr = io.imread(fpath)
        image_stack[:,:,i] = farr
    io.imsave(OUTPUT, image_stack.astype(np.uint16))




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal
    create_volume(animal)
