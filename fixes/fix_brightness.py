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

def change_lower_right(img, brightness):
    med = np.median(img[img > 0])
    endr, endc = img.shape
    midr = endr // 2
    midc = endc // 2
    a = img.copy()
    b = a[midr:endr,midc:endc]
    b[b > brightness] = med
    return a


def change_brightness(filename, brightness, fix):
    img = io.imread(filename)

    if fix:
        fixed = change_lower_right(img, brightness)
        cv2.imwrite('fixed.tif', fixed)


    else:
        levels = [6,7,8,9,9.5,9.99]
        endr, endc = img.shape
        midr = endr // 2
        midc = endc // 2
        a = img.copy()
        lower_right = a[midr:endr, midc:endc]
        print('mean', np.mean(lower_right[lower_right > 0]))
        print('median', np.median(lower_right[lower_right > 0]))
        for l in levels:
            l *= 0.1
            print(round(l,2), np.quantile(lower_right, l))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--file', help='Enter the animal animal', required=True)
    parser.add_argument('--fix', help='Enter channel', required=True)
    parser.add_argument('--brightness', help='Enter channel', required=True)

    args = parser.parse_args()
    filename = args.file
    fix = bool({'true': True, 'false': False}[args.fix.lower()])
    brightness = int(args.brightness)

    change_brightness(filename, brightness, fix)
