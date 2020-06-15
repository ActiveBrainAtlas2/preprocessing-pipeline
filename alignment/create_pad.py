"""
This only centers and padds an image
Its used for creating the global masks
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
from utilities.alignment_utility import place_image, get_last_2d


def padder(animal, channel, bgcolor):

    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    #INPUT = os.path.join(DIR,  channel_dir, 'thumbnail')
    INPUT = os.path.join(DIR,  'masked')
    OUTPUT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/{}/prealigned'.format(animal)
    files = sorted(os.listdir(INPUT))

    max_width = 1400
    max_height = 900

    files = ['0125.tif']
    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        try:
            img = io.imread(infile)
        except:
            print('Could not open', infile)
            continue
        img = get_last_2d(img)
        fixed = place_image(img, file, max_width, max_height, bgcolor)
        outpath = os.path.join(OUTPUT, file)
        cv2.imwrite(outpath, fixed.astype('uint8'))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--bgcolor', help='pixel value of background', required=True, default=0)
    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    bgcolor = int(args.bgcolor)
    padder(animal, channel, bgcolor)
