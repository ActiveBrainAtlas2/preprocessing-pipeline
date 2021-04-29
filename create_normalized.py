"""
This script will do a histogram equalization and rotation.
No masking or cleaning. This is to view the images as they are
for comparison purposes.
"""
import argparse
import os

import cv2
import numpy as np
from skimage import io
from tqdm import tqdm
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_mask import rotate_image, equalized


def fix_image(infile, rotation, flip):
    """
    This method does an adaptive histogram equalization and rotates if necessary.
    :param infile: file path of image
    :param logger: logger to keep track of things
    :param rotation: amount of rotation. 1 = rotate by 90degrees
    :param flip: either flip or flop
    :return: normalized and rotated image
    """
    try:
        img = io.imread(infile)
    except:
        print(f'Could not open {infile}')

    fixed = equalized(img)

    if rotation > 0:
        fixed = rotate_image(fixed, infile, rotation)

    if flip == 'flip':
        fixed = np.flip(fixed)
    if flip == 'flop':
        fixed = np.flip(fixed, axis=1)

    return fixed


def create_normalization(animal, channel):
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.thumbnail
    CLEANED = os.path.join(fileLocationManager.prep, f'CH{channel}', 'normalized')
    os.makedirs(CLEANED, exist_ok=True)
    sqlController = SqlController(animal)
    rotation = sqlController.scan_run.rotation
    flip = sqlController.scan_run.flip

    files = sorted(os.listdir(INPUT))

    for file in tqdm(files):
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(CLEANED, file)
        if os.path.exists(outpath):
            print(outpath)
            continue

        fixed = fix_image(infile, rotation, flip)
        cv2.imwrite(outpath, fixed)

    # set task as completed
    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)

    create_normalization(animal, channel)

