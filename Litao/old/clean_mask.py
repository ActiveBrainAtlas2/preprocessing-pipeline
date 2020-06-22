"""
This is for cleaning/masking channel 2 and channel 3 from the mask created
on channel 1. It works on channel one also, but since that is already cleaned and
normalized, it will just to the rotation and flip
"""
import os
import argparse
import cv2
import numpy as np
from skimage import io
from tqdm import tqdm

from utilities.file_location import FileLocationManager
from Litao.utilities_mask import get_last_2d, place_image, rotate_image


def apply_mask(img, mask, stain, rotation, flip):
    max_width = 1400
    max_height = 900

    img = get_last_2d(img)
    dt = img.dtype

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
        fixed = rotate_image(fixed, rotation)

    if flip == 'flip':
        fixed = np.flip(fixed)
    elif flip == 'flop':
        fixed = np.flip(fixed, axis=1)
    fixed = place_image(fixed, max_width, max_height, bgcolor)

    return fixed


def apply_mask_file(input_path, masked_path, cleaned_path, stain, rotation, flip):
    try:
        img = io.imread(input_path)
    except:
        print('Could not open', input_path)
        return False

    try:
        mask = io.imread(masked_path)
    except:
        print('Could not open', input_path)
        return False

    fixed = apply_mask(img, mask, stain, rotation, flip)

    try:
        os.makedirs(os.path.dirname(cleaned_path), exist_ok=True)
        cv2.imwrite(cleaned_path, fixed.astype('uint16'))
    except:
        print('Could not write', cleaned_path)
        return False

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--stain', help='Enter stain', required=False, default='NTB')
    parser.add_argument('--rotation', help='Enter rotation', required=False)
    parser.add_argument('--flip', help='flip or flop', required=False)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    stain = str(args.stain)
    flip = str(args.flip)
    rotation = int(args.rotation)

    file_location_manager = FileLocationManager(animal)
    input_dir = os.path.join(file_location_manager.prep, 'CH' + str(channel), 'thumbnail')
    masked_dir = os.path.join(file_location_manager.prep, 'masked')
    cleaned_dir = os.path.join(file_location_manager.prep, 'CH' + str(channel), 'cleaned')

    for file_name in tqdm(sorted(os.listdir(input_dir))):
        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(masked_dir, file_name)
        cleaned_path = os.path.join(cleaned_dir, file_name)

        apply_mask_file(input_path, masked_path, cleaned_path, stain, rotation, flip)
