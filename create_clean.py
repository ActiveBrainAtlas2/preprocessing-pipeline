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
from utilities.alignment_utility import get_last_2d, SCALING_FACTOR
from utilities.utilities_mask import rotate_image, place_image, linnorm


def masker(animal, channel, flip=False, rotation=0, resolution='thumbnail'):

    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    channel_dir = 'CH{}'.format(channel)
    CLEANED = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_cleaned')
    INPUT = os.path.join(fileLocationManager.prep,  channel_dir, 'thumbnail')
    MASKS = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)
    bgcolor = 0
    dt = 'uint16'
    limit = 2 ** 16 - 1
    stain = sqlController.histology.counterstain
    if channel == 1:
        sqlController.set_task(animal, CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK)


    if 'full' in resolution.lower():
        CLEANED = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full')
        MASKS = os.path.join(fileLocationManager.prep, 'full_masked')
        max_width = width
        max_height = height
        if channel == 1:
            sqlController.set_task(animal, CLEAN_CHANNEL_1_FULL_RES_WITH_MASK)
        elif channel == 2:
            sqlController.set_task(animal, CLEAN_CHANNEL_2_FULL_RES_WITH_MASK)
        else:
            sqlController.set_task(animal, CLEAN_CHANNEL_3_FULL_RES_WITH_MASK)


    if 'thion' in stain.lower():
        bgcolor = 230
        dt = 'uint8'
        limit = 2 ** 8 - 1


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
        img = get_last_2d(img)
        if channel == 1 and 'ntb' in stain.lower():
            #pass
            img = linnorm(img, 25000 , dt)
        maskfile = os.path.join(MASKS, file)
        mask = io.imread(maskfile)

        mask16 = np.copy(mask.astype(dt))
        mask16[mask16 > 0] = limit

        ##img = np.int16(img)
        mask = np.int8(mask16)
        fixed = cv2.bitwise_and(img, img, mask=mask)
        del mask

        if rotation > 0:
            fixed = rotate_image(fixed, file, rotation)

        if flip == 'flip':
            fixed = np.flip(fixed)

        if flip == 'flop':
            fixed = np.flip(fixed, axis=1)

        if channel == 1 and 'ntb' in stain.lower():
            #pass
            clahe = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(8, 8))
            fixed = clahe.apply(fixed.astype(dt))
            #fixed = fill_spots(fixed)


        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        fixed = place_image(fixed, file, max_height, max_width, bgcolor)
        fixed[fixed == 0] = bgcolor
        cv2.imwrite(outpath, fixed.astype(dt))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--rotation', help='Enter rotation', required=False, default=0)
    parser.add_argument('--flip', help='flip or flop', required=False)
    parser.add_argument('--resolution', help='full or thumbnail', required=False, default='thumbnail')

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    flip = args.flip
    rotation = int(args.rotation)
    resolution = args.resolution
    masker(animal, channel, flip, rotation, resolution)
