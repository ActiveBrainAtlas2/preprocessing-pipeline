"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs the files from the cleaned/masked dir through opencv adaptive histogram equalization method
"""
import os, sys
import argparse
import cv2
from tqdm import tqdm
sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager
from skimage import io

def get_last_2d(data):
    """
    Some of the tifs are in a shape of (1,1,R,C). This method just works on the rows
    and columns and gets those last two dimensions.
    Args:
        data: incoming tif file

    Returns: a numpy array with 2 dimensions
    """
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)


def adapt(stack):
    """
    This method takes a tif file and runs it through opencv's adaptive equalization method.
    Currently just working on the counter stain channel.
    Args:
        stack: the animal ID
    Returns: nothing, but writes the new image to disk. To the normalized directory
    """
    fileLocationManager = FileLocationManager(stack)
    INPUT = fileLocationManager.cleaned
    OUTPUT = fileLocationManager.normalized
    image_name_list = sorted(os.listdir(INPUT))

    tilesize = 16
    for i, file in enumerate(tqdm(image_name_list)):
        infile = os.path.join(INPUT, file)
        cv2.imread(infile, cv2.)

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
