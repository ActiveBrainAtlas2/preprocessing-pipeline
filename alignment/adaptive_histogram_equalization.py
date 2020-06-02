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
from skimage import io

def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)


def adapt(stack):
    fileLocationManager = FileLocationManager(stack)
    INPUT = fileLocationManager.cleaned
    OUTPUT = fileLocationManager.normalized

    DIR = '/data2/edward/DK39'
    INPUT = os.path.join(DIR, 'cleaned')
    OUTPUT = os.path.join(DIR, 'normalized')


    image_name_list = sorted(os.listdir(INPUT))

    tilesize = 16
    for i, file in enumerate(tqdm(image_name_list)):
        infile = os.path.join(INPUT, file)

        try:
            img = io.imread(infile)
        except:
            print('Could not open', infile)
            return 0

        img = get_last_2d(img)
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
