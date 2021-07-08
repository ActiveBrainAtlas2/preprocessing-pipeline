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
from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_mask import equalized


def create_normalization(animal, channel):
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.thumbnail
    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'normalized')
    os.makedirs(OUTPUT, exist_ok=True)
    sqlController = SqlController(animal)

    files = sorted(os.listdir(INPUT))

    for file in tqdm(files):
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(OUTPUT, file)
        if os.path.exists(outpath):
            continue

        img = io.imread(infile)

        if img.dtype == np.uint16:
            img = (img/256).astype(np.uint8)

        fixed = equalized(img)
        cv2.imwrite(outpath, fixed.astype(np.uint8))

    # set task as completed
    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=False,default=1)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)

    create_normalization(animal, channel)

