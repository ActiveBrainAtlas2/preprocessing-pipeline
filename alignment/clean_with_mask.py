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
from utilities.alignment_utility import get_last_2d, rotate_image, place_image


def masker(animal, channel, flip=False, rotation=0, stain='NTB'):

    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    CLEANED = os.path.join(DIR, channel_dir, 'cleaned')
    # channel one is already cleaned from the mask process
    if channel > 1:
        INPUT = os.path.join(DIR,  channel_dir, 'thumbnail')
    else:
        INPUT = CLEANED


    MASKS = os.path.join(DIR, 'masked')
    files = sorted(os.listdir(INPUT))

    #max_width = 55700
    #max_height = 33600
    max_width = 1400
    max_height = 900

    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        try:
            img = io.imread(infile)
        except:
            print('Could not open', infile)
            continue
        img = get_last_2d(img)
        if channel > 1:
            maskfile = os.path.join(MASKS, file)
            mask = io.imread(maskfile)
            if img.dtype == np.dtype('uint16'):
                limit = 2**16-1
                dtype = 'uint16'
                mask16 = np.copy(mask).astype(dtype)
                mask16[mask16 > 0] = limit
                mask = mask16
            else:
                dtype = 'uint8'
                limit = 2**8-1
                mask[mask > 0] = limit
                mask = 255 - mask

            if stain == 'NTB':
                bgcolor = 0
                fixed = cv2.bitwise_and(img, mask)
            else:
                bgcolor = 255
                fixed = cv2.bitwise_or(img, mask)

        else:
            fixed = np.copy(img)
            del img

        if rotation > 0:
            fixed = rotate_image(fixed, file, rotation)

        if flip == 'flip':
            fixed = np.flip(fixed)

        if flip == 'flop':
            fixed = np.flip(fixed, axis=1)

        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        outpath = os.path.join(CLEANED, file)
        cv2.imwrite(outpath, fixed.astype(dtype))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--rotation', help='Enter rotation', required=False, default=0)
    parser.add_argument('--stain', help='Enter stain', required=False, default='NTB')
    parser.add_argument('--flip', help='flip or flop', required=False)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    flip = args.flip
    rotation = int(args.rotation)
    stain = args.stain
    masker(animal, channel, flip, rotation, stain)
