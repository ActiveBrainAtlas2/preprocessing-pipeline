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
from concurrent.futures.process import ProcessPoolExecutor
from timeit import default_timer as timer

from sql_setup import CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK
from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.utilities_mask import rotate_image, place_image, scaled, equalized
from utilities.utilities_process import test_dir, SCALING_FACTOR
from utilities.utilities_cvat_neuroglancer import get_cpus


def fix_ntb(file_keys):
    """
    This method clean all NTB images in the specified channel. For channel one it also scales
    and does an adaptive histogram equalization.
    file_keys is a tuple of the following:
        :param infile: file path of image to read
        :param outpath: file path of image to write
        :param mask: binary mask image of the image
        :param rotation: amount of rotation. 1 = rotate by 90degrees
        :param flip: either flip or flop
        :param max_width: width of image
        :param max_height: height of image
        :param scale: used in scaling. Gotten from the histogram
    :return: nothing. we write the image to disk
    """
    infile, outpath, mask, rotation, flip, max_width, max_height, scale = file_keys
    try:
        img = io.imread(infile)
    except:
        print(f'Could not open {infile}')

    fixed = cv2.bitwise_and(img, img, mask=mask)
    del img
    if channel == 1:
        fixed = scaled(fixed, mask, scale, epsilon=0.01)
        fixed = equalized(fixed)
    if rotation > 0:
        fixed = rotate_image(fixed, infile, rotation)
    if flip == 'flip':
        fixed = np.flip(fixed)
    if flip == 'flop':
        fixed = np.flip(fixed, axis=1)

    fixed = place_image(fixed, infile, max_width, max_height, 0)

    cv2.imwrite(outpath, fixed)




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
    progress_id = sqlController.get_progress_id(downsample, channel, 'CLEAN')
    sqlController.set_task(animal, progress_id)

    file_keys = []
    for file in files:
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(CLEANED, file)
        if os.path.exists(outpath):
            continue
        maskfile = os.path.join(MASKS, file)
        mask = io.imread(maskfile)

        if 'thion' in stain.lower():
            print('Not implemented.')
            #fixed = fix_thion(infile, mask, maskfile, logger, rotation, flip, max_width, max_height)
        else:
            file_keys.append([infile, outpath, mask, rotation, flip, max_width, max_height, scale])

    start = timer()
    workers, _ = get_cpus()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(fix_ntb, sorted(file_keys), chunksize=workers)
        executor.shutdown(wait=True)

    end = timer()
    print(f'Create cleaned files took {end - start} seconds')


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

