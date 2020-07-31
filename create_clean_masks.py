"""
This is for cleaning/masking channel 2 and channel 3 from the mask created
on channel 1. It works on channel one also, but since that is already cleaned and
normalized, it will just to the rotation and flip
"""
import argparse
import os

import cv2
import numpy as np
from skimage import io
from tqdm import tqdm

from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.alignment_utility import get_last_2d, SCALING_FACTOR
from utilities.utilities_mask import rotate_image, place_image


def clean_mask(animal, rotation, flip):
    logger = get_logger(animal)
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    OUTPUT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/{}/prealigned'.format(animal)

    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)
    bgcolor = 0

    files = sorted(os.listdir(INPUT))

    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(OUTPUT, file)
        if os.path.exists(outpath):
            continue
        try:
            img = io.imread(infile)
        except:
            logger.warning(f'Could not open {infile}')
            continue
        fixed = get_last_2d(img)

        if rotation > 0:
            fixed = rotate_image(fixed, file, rotation)

        if flip == 'flip':
            fixed = np.flip(fixed)
        if flip == 'flop':
            fixed = np.flip(fixed, axis=1)

        # fixed = fill_spots(fixed)

        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        cv2.imwrite(outpath, fixed.astype(np.uint8))
    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--rotation', help='Enter rotation', required=False, default=0)
    parser.add_argument('--flip', help='flip or flop', required=False)

    args = parser.parse_args()
    animal = args.animal
    rotation = int(args.rotation)
    flip = args.flip


    clean_mask(animal, rotation, flip)
