"""
This is for cleaning/masking channel 2 and channel 3 from the mask created
on channel 1. It works on channel one also, but since that is already cleaned and
normalized, it will just to the rotation and flip
"""
import argparse

import numpy as np
from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os, sys
import cv2

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.sqlcontroller import SqlController
from utilities.alignment_utility import get_last_2d, rotate_image, place_image, SCALING_FACTOR, linnorm

def get_average_color(INPUT,files):
    averages = []
    for file in files:
        infile = os.path.join(INPUT, file)
        img = io.imread(infile)
        start_bottom = img.shape[0] - 5
        bottom_rows = img[start_bottom:img.shape[0], :]
        avg = np.mean(bottom_rows)
        averages.append(avg)
    return int(round(np.mean(averages)))


def masker(animal, channel, flip=False, rotation=0, resolution='thumbnail'):

    sqlController = SqlController()
    sqlController.get_animal_info(animal)
    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    CLEANED = os.path.join(DIR, channel_dir, 'thumbnail_cleaned')
    INPUT = os.path.join(DIR,  channel_dir, 'thumbnail')
    MASKS = os.path.join(DIR, 'thumbnail_masked')
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)
    bgcolor = 0
    dt = 'uint16'
    limit = 2 ** 16 - 1
    stain = sqlController.histology.counterstain

    if 'full' in resolution.lower():
        CLEANED = os.path.join(DIR, channel_dir, 'full_cleaned')
        INPUT = os.path.join(DIR, channel_dir, 'full')
        MASKS = os.path.join(DIR, 'full_masked')
        max_width = width
        max_height = height


    if 'thion' in stain.lower():
        bgcolor = 230
        dt = 'uint8'
        limit = 2 ** 8 - 1


    files = sorted(os.listdir(INPUT))


    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        try:
            img = io.imread(infile)
        except:
            print('Could not open', infile)
            continue
        img = get_last_2d(img)
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
            #fixed = linnorm(fixed, limit , dt)
            fixed = clahe.apply(fixed.astype(dt))

        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        fixed[fixed == 0] = bgcolor
        outpath = os.path.join(CLEANED, file)
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
