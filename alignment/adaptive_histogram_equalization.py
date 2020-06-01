"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs the files in sequence through elastix
    3. parses the results from the elastix output file
    4. Sends those results to the Imagemagick convert program with the correct offsets and crop
"""
import os, sys
import argparse
import cv2
from tqdm import tqdm
sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager



def adapt(stack):
    fileLocationManager = FileLocationManager(stack)
    INPUT = fileLocationManager.aligned
    OUTPUT = fileLocationManager.normalized
    image_name_list = sorted(os.listdir(INPUT))

    tilesize = 16
    for i, file in enumerate(tqdm(image_name_list)):
        infile = os.path.join(INPUT, file)
        img = cv2.imread(infile, -1)
        clahe = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(tilesize, tilesize))
        img = clahe.apply(img)
        outpath = os.path.join(OUTPUT, file)
        cv2.imwrite(outpath, img.astype('uint16'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    adapt(animal)
