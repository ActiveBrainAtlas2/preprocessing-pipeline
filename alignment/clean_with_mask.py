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


def masker(animal, channel, flip=False, rotation=0, stain='NTB'):

    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    CLEANED = os.path.join(DIR, channel_dir, 'cleaned')
    # channel one is already cleaned from the mask process
    INPUT = os.path.join(DIR,  channel_dir, 'thumbnail')


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
        dt = img.dtype
        maskfile = os.path.join(MASKS, file)
        mask = io.imread(maskfile)
        start_bottom = img.shape[0] - 5
        bottom_rows = img[start_bottom:img.shape[0], :]
        avg = np.mean(bottom_rows)
        bgcolor = int(round(avg))

        if dt == np.dtype('uint16'):
            limit = 2**16-1
            mask16 = np.copy(mask).astype(dt)
            mask16[mask16 > 0] = limit
            mask = mask16
        else:
            limit = 2**8-1
            limit = bgcolor
            mask[mask > 0] = limit
            mask = limit - mask
            mask = place_image(mask, max_width, max_height, bgcolor)

        if stain == 'NTB':
            fixed = cv2.bitwise_and(img, mask)
        else:
            fixed = cv2.bitwise_or(img, mask)


        if rotation > 0:
            fixed = rotate_image(fixed, file, rotation)

        if flip == 'flip':
            fixed = np.flip(fixed)

        if flip == 'flop':
            fixed = np.flip(fixed, axis=1)
        #TODO dtype needs to come from the sql
        fixed = place_image(fixed, file, max_width, max_height, bgcolor)
        outpath = os.path.join(CLEANED, file)
        cv2.imwrite(outpath, fixed.astype(dt))
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
