import argparse

import numpy as np
import matplotlib
import matplotlib.figure
from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os
import cv2


def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)


def place_image(img, max_width, max_height):
    zmidr = max_height // 2
    zmidc = max_width // 2
    startr = zmidr - (img.shape[0] // 2)
    endr = startr + img.shape[0]
    startc = zmidc - (img.shape[1] // 2)
    endc = startc + img.shape[1]
    new_img = np.zeros([max_height, max_width])
    try:
        new_img[startr:endr, startc:endc] = img
    except:
        print('could not create new img', file)

    return new_img.astype('uint16')


def masker(animal, channel):

    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    INPUT = os.path.join(DIR,  channel_dir, 'input')
    CLEANED = os.path.join(DIR, channel_dir, 'cleaned')

    MASKS = os.path.join(DIR, 'masked')
    files = sorted(os.listdir(INPUT))

    max_width = 55700
    max_height = 33600
    #max_width = 1740
    #max_height = 1050

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
        fixed = place_image(fixed, max_width, max_height)
        outpath = os.path.join(CLEANED, file)
        cv2.imwrite(outpath, fixed.astype('uint16'))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    masker(animal, channel)
