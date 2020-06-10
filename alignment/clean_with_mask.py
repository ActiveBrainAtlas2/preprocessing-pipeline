"""
This is for cleaning/masking channel 2 and channel 3 from the mask created
on channel 1
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
from utilities.alignment_utility import get_last_2d, rotate_image, place_image


def masker(animal, channel, flip=False, rotation=0):

    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    INPUT = os.path.join(DIR,  channel_dir, 'thumbnail')
    CLEANED = os.path.join(DIR, channel_dir, 'cleaned')

    MASKS = os.path.join(DIR, 'CH1', 'masked')
    files = sorted(os.listdir(INPUT))

    #max_width = 55700
    #max_height = 33600
    max_width = 1740
    max_height = 1050

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
        mask16 = np.copy(mask).astype('uint16')
        mask16[mask16 > 0] = 2**16-1
        fixed = cv2.bitwise_and(img, mask16)

        if rotation > 0:
            fixed = rotate_image(fixed, file, rotation)

        if flip == 'flip':
            fixed = np.flip(fixed)

        if flip == 'flop':
            fixed = np.flip(fixed, axis=1)

        fixed = place_image(fixed, file, max_width, max_height)
        outpath = os.path.join(CLEANED, file)
        cv2.imwrite(outpath, fixed.astype('uint16'))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--rotation', help='Enter rotation', required=False)
    parser.add_argument('--flip', help='flip or flop', required=False)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    flip = args.flip
    rotation = int(args.rotation)
    masker(animal, channel, flip, rotation)
