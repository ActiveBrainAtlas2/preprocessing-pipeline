"""
This is for cleaning/masking channel 2 and channel 3 from the mask created
on channel 1. It works on channel one also, but since that is already cleaned and
normalized, it will just to the rotation and flip
"""
import argparse

import numpy as np
from skimage import io
from tqdm import tqdm
import os, sys
import cv2

from sql_setup import CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK, CLEAN_CHANNEL_1_FULL_RES_WITH_MASK, \
    CLEAN_CHANNEL_2_FULL_RES_WITH_MASK, CLEAN_CHANNEL_3_FULL_RES_WITH_MASK

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.alignment_utility import get_last_2d, rotate_image, place_image, SCALING_FACTOR
from utilities.utilities_mask import fill_spots


def clean_mask(animal, flip=False, rotation=0):

    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    CLEANED = os.path.join(fileLocationManager.prep, 'mask_cleaned')
    INPUT = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)
    bgcolor = 0

    files = sorted(os.listdir(INPUT))


    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(CLEANED, file)
        if os.path.exists(outpath):
            continue
        try:
            img = io.imread(infile)
        except:
            print('Could not open', infile)
            continue
        fixed = get_last_2d(img)

        if rotation > 0:
            fixed = rotate_image(fixed, file, rotation)

        if flip == 'flip':
            fixed = np.flip(fixed)

        if flip == 'flop':
            fixed = np.flip(fixed, axis=1)

        #fixed = fill_spots(fixed)


        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        cv2.imwrite(outpath, fixed.astype(np.uint8))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--rotation', help='Enter rotation', required=False, default=0)
    parser.add_argument('--flip', help='flip or flop', required=False)

    args = parser.parse_args()
    animal = args.animal
    flip = args.flip
    rotation = int(args.rotation)
    clean_mask(animal, flip, rotation)
