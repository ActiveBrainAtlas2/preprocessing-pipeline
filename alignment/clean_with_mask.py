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


def masker(animal, channel, flip=False, rotation=0, stain='NTB', resolution='thumbnail'):

    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    CLEANED = os.path.join(DIR, channel_dir, 'thumbnail_cleaned')
    INPUT = os.path.join(DIR,  channel_dir, 'thumbnail')
    MASKS = os.path.join(DIR, 'thumbnail_masked')
    max_width = 1400
    max_height = 900

    if 'full' in resolution.lower():
        CLEANED = os.path.join(DIR, channel_dir, 'full_cleaned')
        INPUT = os.path.join(DIR, channel_dir, 'full')
        MASKS = os.path.join(DIR, 'full_masked')
        max_width = 44000
        max_height = 28000

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

        limit = 2**16-1
        mask16 = np.copy(mask.astype('uint16'))
        mask16[mask16 > 0] = limit
        # mask_inv = cv2.bitwise_not(mask16)

        img = np.int16(img)
        mask = np.int8(mask16)
        fixed = cv2.bitwise_and(img, img, mask=mask)
        del mask

        start_bottom = img.shape[0] - 5
        bottom_rows = img[start_bottom:img.shape[0], :]
        avg = np.mean(bottom_rows)
        bgcolor = int(round(avg))
        if 'thi' in stain.lower():
            bgcolor = 228

        if rotation > 0:
            fixed = rotate_image(fixed, file, rotation)

        if flip == 'flip':
            fixed = np.flip(fixed)

        if flip == 'flop':
            fixed = np.flip(fixed, axis=1)
        #TODO dtype needs to come from the sql
        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        fixed[fixed == 0] = bgcolor
        outpath = os.path.join(CLEANED, file)
        cv2.imwrite(outpath, fixed.astype('uint16'))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--rotation', help='Enter rotation', required=False, default=0)
    parser.add_argument('--stain', help='Enter stain', required=False, default='NTB')
    parser.add_argument('--flip', help='flip or flop', required=False)
    parser.add_argument('--resolution', help='full or thumbnail', required=False, default='thumbnail')

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    flip = args.flip
    rotation = int(args.rotation)
    stain = args.stain
    resolution = args.resolution
    masker(animal, channel, flip, rotation, stain, resolution)
