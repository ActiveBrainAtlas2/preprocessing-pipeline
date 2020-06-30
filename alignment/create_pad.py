"""
This only centers and padds an image
Its used for creating the global masks
"""
import argparse

from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os, sys
import cv2

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import place_image, SCALING_FACTOR
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager

def padder(animal, bgcolor):

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController()
    sqlController.get_animal_info(animal)
    INPUT = os.path.join(fileLocationManager.prep,  'thumbnail_masked')
    OUTPUT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/{}/prealigned'.format(animal)
    files = sorted(os.listdir(INPUT))
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)


    for i, file in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, file)
        try:
            img = io.imread(infile)
        except:
            print('Could not open', infile)
            continue
        fixed = place_image(img, file, max_width, max_height, bgcolor)
        outpath = os.path.join(OUTPUT, file)
        cv2.imwrite(outpath, fixed.astype('uint8'))
    print('Finished')



if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--bgcolor', help='pixel value of background', required=True, default=0)
    args = parser.parse_args()
    animal = args.animal
    bgcolor = int(args.bgcolor)
    padder(animal, bgcolor)
