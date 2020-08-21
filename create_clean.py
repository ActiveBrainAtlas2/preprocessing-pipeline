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

from sql_setup import CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK, CLEAN_CHANNEL_1_FULL_RES_WITH_MASK, \
    CLEAN_CHANNEL_2_FULL_RES_WITH_MASK, CLEAN_CHANNEL_3_FULL_RES_WITH_MASK
from utilities.alignment_utility import get_last_2d, SCALING_FACTOR
from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.utilities_mask import rotate_image, place_image, linnorm, lognorm, scaled


def fix_ntb(infile, mask, logger, rotation, flip):
    try:
        img = io.imread(infile)
    except:
        logger.warning(f'Could not open {infile}')
    img = get_last_2d(img)
    fixed = cv2.bitwise_and(img, img, mask=mask)
    if channel == 1:
        fixed = scaled(fixed, mask)
        clahe = cv2.createCLAHE(clipLimit=20.0, tileGridSize=(8, 8))
        fixed = clahe.apply(fixed.astype(np.uint16))

    if rotation > 0:
        fixed = rotate_image(fixed, infile, rotation)

    if flip == 'flip':
        fixed = np.flip(fixed)
    if flip == 'flop':
        fixed = np.flip(fixed, axis=1)


    return fixed


def fix_thion(infile, mask, logger, rotation, flip):
    try:
        #imgfull = cv2.imread(infile, cv2.IMREAD_UNCHANGED)
        imgfull = io.imread(infile)
    except:
        logger.warning(f'Could not open {infile}')

    img_ch1 = imgfull[:, :, 0]
    img_ch2 = imgfull[:, :, 1]
    img_ch3 = imgfull[:, :, 2]
    fixed1 = cv2.bitwise_and(img_ch1, img_ch1, mask=mask)
    fixed2 = cv2.bitwise_and(img_ch2, img_ch2, mask=mask)
    fixed3 = cv2.bitwise_and(img_ch3, img_ch3, mask=mask)

    if rotation > 0:
        fixed1 = rotate_image(fixed1, infile, rotation)
        fixed2 = rotate_image(fixed2, infile, rotation)
        fixed3 = rotate_image(fixed3, infile, rotation)

    if flip == 'flip':
        fixed1 = np.flip(fixed1)
        fixed2 = np.flip(fixed2)
        fixed3 = np.flip(fixed3)
    if flip == 'flop':
        fixed1 = np.flip(fixed1, axis=1)
        fixed2 = np.flip(fixed2, axis=1)
        fixed3 = np.flip(fixed3, axis=1)

    fixed = np.dstack((fixed1, fixed2, fixed3))
    #fixed = fixed3
    return fixed


def masker(animal, channel, flip, rotation=0, full=False):
    logger = get_logger(animal)
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    channel_dir = 'CH{}'.format(channel)
    CLEANED = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_cleaned')
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail')
    MASKS = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)
    bgcolor = 0
    dt = 'uint16'
    stain = sqlController.histology.counterstain
    if channel == 1:
        sqlController.set_task(animal, CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK)

    if full:
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
        bgcolor = 255
        dt = 'uint8'

    files = sorted(os.listdir(INPUT))

    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(CLEANED, file)
        if os.path.exists(outpath):
            continue
        maskfile = os.path.join(MASKS, file)
        mask = io.imread(maskfile)

        if 'thion' in stain.lower():
            fixed = fix_thion(infile, mask, logger, rotation, flip)
        else:
            fixed = fix_ntb(infile, mask, logger, rotation, flip)






        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        # below is for testing to mimic the mask
        #fixed = place_image(fixed, file, max_height, max_width, bgcolor)
        fixed[fixed == 0] = bgcolor
        io.imsave(outpath, fixed.astype(dt), check_contrast=False)
        #cv2.imwrite(outpath, fixed.astype(dt))

    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--rotation', help='Enter rotation', required=False, default=0)
    parser.add_argument('--flip', help='Enter flip or flop', required=False)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=False, default='thumbnail')

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    rotation = int(args.rotation)
    flip = args.flip
    full = bool({'full': True, 'thumbnail': False}[args.resolution])

    masker(animal, channel, flip, rotation, full)

