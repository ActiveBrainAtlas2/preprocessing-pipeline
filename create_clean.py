"""
This is for cleaning/masking all channels from the mask created
on channel 1. It also does the rotating and flip/flop if necessary.
On channel one it scales and does an adaptive histogram equalization.
Note, the scaled method takes 45000 as the default. This is usually
a good value for 16bit images. Note, opencv uses lzw compression by default
to save files.
"""
import argparse
import os, sys

import cv2
import numpy as np
from skimage import io
from tqdm import tqdm
from sql_setup import CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK
from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.utilities_mask import rotate_image, place_image, scaled, equalized
from utilities.utilities_process import test_dir, SCALING_FACTOR


def fix_ntb(infile, mask, maskfile, logger, rotation, flip, max_width, max_height, scale):
    """
    This method clean all NTB images in the specified channel. For channel one it also scales
    and does an adaptive histogram equalization.
    :param infile: file path of image
    :param mask: binary mask image of the image
    :param maskfile: file path of mask
    :param ROTATED_MASKS: location of rotated masks
    :param logger: logger to keep track of things
    :param rotation: amount of rotation. 1 = rotate by 90degrees
    :param flip: either flip or flop
    :param max_width: width of image
    :param max_height: height of image
    :param scale: used in scaling. Gotten from the histogram
    :return: cleaned and rotated image
    """
    try:
        img = io.imread(infile, img_num=0)
    except:
        logger.warning(f'Could not open {infile}')

    fixed = cv2.bitwise_and(img, img, mask=mask)
    del img
    if channel == 1:
        fixed = scaled(fixed, mask, scale, epsilon=0.01)
        fixed = equalized(fixed)
    if rotation > 0:
        fixed = rotate_image(fixed, infile, rotation)
        #mask = rotate_image(mask, maskfile, rotation)

    if flip == 'flip':
        fixed = np.flip(fixed)
        #mask = np.flip(mask)
    if flip == 'flop':
        fixed = np.flip(fixed, axis=1)
        #mask = np.flip(mask, axis=1)

    return fixed


def fix_thion(infile, mask, maskfile, logger, rotation, flip, max_width, max_height):
    """
    This method clean all thionin images. Note that the thionin have 3 channels combined into one.
    :param infile: file path of image
    :param mask: binary mask image of the image
    :param maskfile: file path of mask
    :param ROTATED_MASKS: location of rotated masks
    :param logger: logger to keep track of things
    :param rotation: amount of rotation. 1 = rotate by 90degrees
    :param flip: either flip or flop
    :param max_width: width of image
    :param max_height: height of image
    :return: cleaned and rotated image
    """
    try:
        imgfull = io.imread(infile)
    except:
        logger.warning(f'Could not open {infile}')

    img_ch1 = imgfull[:, :, 0]
    img_ch2 = imgfull[:, :, 1]
    img_ch3 = imgfull[:, :, 2]
    fixed1 = cv2.bitwise_and(img_ch1, img_ch1, mask=mask)
    fixed2 = cv2.bitwise_and(img_ch2, img_ch2, mask=mask)
    fixed3 = cv2.bitwise_and(img_ch3, img_ch3, mask=mask)
    del img_ch1
    del img_ch2
    del img_ch3

    if rotation > 0:
        fixed1 = rotate_image(fixed1, infile, rotation)
        fixed2 = rotate_image(fixed2, infile, rotation)
        fixed3 = rotate_image(fixed3, infile, rotation)
        mask = rotate_image(mask, maskfile, rotation)

    if flip == 'flip':
        fixed1 = np.flip(fixed1)
        fixed2 = np.flip(fixed2)
        fixed3 = np.flip(fixed3)
        mask = np.flip(mask)
    if flip == 'flop':
        fixed1 = np.flip(fixed1, axis=1)
        fixed2 = np.flip(fixed2, axis=1)
        fixed3 = np.flip(fixed3, axis=1)
        mask = np.flip(mask, axis=1)

    fixed = np.dstack((fixed1, fixed2, fixed3))
    return fixed


def masker(animal, channel, downsample, scale):
    """
    Main method that starts the cleaning/rotating process.
    :param animal:  prep_id of the animal we are working on.
    :param channel:  channel {1,2,3}
    :param flip:  flip or flop or nothing
    :param rotation: usually 1 for rotating 90 degrees
    :param full:  resolution, either full or thumbnail
    :return: nothing, writes to disk the cleaned image
    """
    logger = get_logger(animal)
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    channel_dir = 'CH{}'.format(channel)
    CLEANED = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_cleaned')
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail')

    MASKS = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    os.makedirs(CLEANED, exist_ok=True)
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    rotation = sqlController.scan_run.rotation
    flip = sqlController.scan_run.flip
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)
    bgcolor = 0
    stain = sqlController.histology.counterstain
    if channel == 1:
        sqlController.set_task(animal, CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK)



    if not downsample:
        CLEANED = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
        os.makedirs(CLEANED, exist_ok=True)
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full')
        MASKS = os.path.join(fileLocationManager.prep, 'full_masked')
        max_width = width
        max_height = height

    if 'thion' in stain.lower():
        bgcolor = 255

    error = test_dir(animal, INPUT, downsample, same_size=False)
    if len(error) > 0:
        print(error)
        sys.exit()
    files = sorted(os.listdir(INPUT))

    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(CLEANED, file)
        if os.path.exists(outpath):
            continue
        maskfile = os.path.join(MASKS, file)
        mask = io.imread(maskfile)

        if 'thion' in stain.lower():
            fixed = fix_thion(infile, mask, maskfile, logger, rotation, flip, max_width, max_height)
        else:
            fixed = fix_ntb(infile, mask, maskfile, logger, rotation, flip, max_width, max_height, scale)

        fixed = place_image(fixed, file, max_width, max_height, bgcolor)

        fixed[fixed == 0] = bgcolor
        cv2.imwrite(outpath, fixed)

    # set task as completed
    progress_id = sqlController.get_progress_id(downsample, channel, 'CLEAN')
    sqlController.set_task(animal, progress_id)
    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--scale', help='Enter scaling', required=False, default=45000)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    scale = int(args.scale)
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])

    masker(animal, channel, downsample, scale)

