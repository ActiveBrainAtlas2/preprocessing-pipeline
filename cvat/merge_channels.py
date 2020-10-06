import os, sys
import argparse
from tqdm import tqdm
import cv2
import numpy as np

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)

from utilities.file_location import FileLocationManager



def merge_channels(animal):
    fileLocationManager = FileLocationManager(animal)

    CH1 = os.path.join(fileLocationManager.prep, 'CH1', '16_aligned')
    CH3 = os.path.join(fileLocationManager.prep, 'CH3', '16_aligned')
    OUTPUT = os.path.join(fileLocationManager.prep, 'CH1_CH3', '16_aligned')
    ch1_files = sorted(os.listdir(CH1))
    ch3_files = sorted(os.listdir(CH3))

    os.makedirs(OUTPUT, exist_ok=True)

    low_clahe = cv2.createCLAHE(clipLimit=8.0, tileGridSize=(18, 18))
    high_clahe = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(18, 18))

    for ch1_file, ch3_file in tqdm(zip(ch1_files, ch3_files)):
        outpath = os.path.join(OUTPUT, ch1_file)
        if os.path.exists(outpath):
            continue


        ch1_infile = os.path.join(CH1, ch1_file)
        ch3_infile = os.path.join(CH3, ch3_file)
        ch1_img = cv2.imread(ch1_infile, cv2.IMREAD_UNCHANGED)
        ch3_img = cv2.imread(ch3_infile, cv2.IMREAD_UNCHANGED)
        ch1_img = low_clahe.apply(ch1_img)
        ch1_img = ch1_img * 0.25

        ch1_img8 = (ch1_img / 256).astype('uint8')
        ch3_img8 = (ch3_img / 256).astype('uint8')
        ch3_img8 = high_clahe.apply(ch3_img8)
        r = np.zeros(ch1_img8.shape).astype(np.uint8)
        bgr_uint8 = np.dstack((ch1_img8, ch3_img8, r)).astype(np.uint8)
        cv2.imwrite(outpath, bgr_uint8)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal
    merge_channels(animal)

