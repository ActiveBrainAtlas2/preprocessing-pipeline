"""
This file does the following operations:
    1. Converts regular filename from main tif dir to CHX/full or
    2. Converts and downsamples CHX/full to CHX/thumbnail
    When creating the full sized images, the LZW compression is used
"""
import argparse
from skimage import io
import numpy as np
import cv2

def change_roi(img, brightness, area):
    med = np.median(img[img > 0])
    mn = np.mean(img[img > 0])
    a = img.copy()
    b = get_roi(a, area)
    b[b > brightness] = mn + 150
    return a

def get_roi(img, area):
    endr, endc = img.shape
    midr = endr // 2
    midc = endc // 2
    if 'lr' in area:
        b = img[midr:endr,midc:endc]
    else:
        b = img[0:midr, 0:endc]
    return b


def change_brightness(filename, brightness, fix, area):
    img = io.imread(filename)

    if fix:
        fixed = change_roi(img, brightness, area)
        cv2.imwrite('fixed.tif', fixed)


    else:
        levels = [6,7,8,9,9.5,9.99]
        a = img.copy()
        roi = get_roi(a, area)
        print('mean', np.mean(roi[roi > 0]))
        print('median', np.median(roi[roi > 0]))
        for l in levels:
            l *= 0.1
            print(round(l,2), np.quantile(roi, l))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--file', help='Enter the animal animal', required=True)
    parser.add_argument('--fix', help='Enter channel', required=True)
    parser.add_argument('--brightness', help='Enter channel', required=True)
    parser.add_argument('--area', help='Enter area {ul,lr}', required=False, default='lr')

    args = parser.parse_args()
    filename = args.file
    fix = bool({'true': True, 'false': False}[args.fix.lower()])
    brightness = int(args.brightness)
    area = args.area

    change_brightness(filename, brightness, fix, area)
