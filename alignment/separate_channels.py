"""
This file does the following operations:
    1. Gets the full 3 channel tif from the main tif dir
    2. uses skimage to read the file as a regular 3d array
    3. splits that array into it's separate 3 channels
    4. uses opencv to write to the correct output dir
"""
import os, sys
import argparse
import cv2
from skimage import io
from tqdm import tqdm

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    fileLocationManager = FileLocationManager(animal)
    DIR = fileLocationManager.prep
    INPUT = fileLocationManager.tif
    CH1 = os.path.join(DIR, 'CH1', 'full')
    CH2 = os.path.join(DIR, 'CH2', 'full')
    CH3 = os.path.join(DIR, 'CH3', 'full')

    image_name_list = sorted(os.listdir(INPUT))
    for file in tqdm(image_name_list):
        ch1path = os.path.join(CH1, file)
        ch2path = os.path.join(CH2, file)
        ch3path = os.path.join(CH3, file)
        if os.path.exists(ch1path):
            continue

        infile = os.path.join(INPUT, file)
        img = io.imread(infile)
        ch1 = img[:, :, 0]
        ch2 = img[:, :, 1]
        ch3 = img[:, :, 2]

        cv2.imwrite(ch1path, ch1.astype('uint8'))
        cv2.imwrite(ch2path, ch2.astype('uint8'))
        cv2.imwrite(ch3path, ch3.astype('uint8'))
