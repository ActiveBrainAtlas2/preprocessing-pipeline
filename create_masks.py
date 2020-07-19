import argparse
import subprocess
from multiprocessing.pool import Pool
import numpy as np
from skimage import io
from os.path import expanduser
from tqdm import tqdm

from sql_setup import CREATE_THUMBNAIL_MASKS

HOME = expanduser("~")
import os, sys
import cv2

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import get_last_2d
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_mask import fix_with_fill, linnorm
from utilities.utilities_process import workershell



def create_mask(animal, resolution, njobs):

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    sqlController.set_task(animal, CREATE_THUMBNAIL_MASKS)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    MASKED = os.path.join(fileLocationManager.prep, 'thumbnail_masked')

    if 'full' in resolution.lower():
        INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full')
        THUMBNAIL = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
        MASKED = os.path.join(fileLocationManager.prep, 'full_masked')
        files = sorted(os.listdir(INPUT))
        commands = []
        for i, file in enumerate(files):
            infile = os.path.join(INPUT, file)
            thumbfile = os.path.join(THUMBNAIL, file)
            outfile = os.path.join(MASKED, file)
            try:
                src = io.imread(infile)
            except:
                print('Could not open', infile)
                continue
            src = get_last_2d(src)
            height, width = src.shape
            del src
            cmd = "convert {} -resize {}x{}! -compress lzw -depth 8 {}".format(thumbfile, width, height, outfile)
            commands.append(cmd)

        with Pool(njobs) as p:
            p.map(workershell, commands)


    else:

        files = sorted(os.listdir(INPUT))

        for i, file in enumerate(tqdm(files)):
            infile = os.path.join(INPUT, file)
            try:
                img = io.imread(infile)
            except:
                print('Could not open', infile)
                continue
            img = get_last_2d(img)
            mask = fix_with_fill(img, 250, np.uint8)
            # save the mask
            outpath = os.path.join(MASKED, file)
            cv2.imwrite(outpath, mask.astype('uint8'))

if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--resolution', help='full or thumbnail', required=False, default='thumbnail')
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    args = parser.parse_args()
    animal = args.animal
    resolution = args.resolution
    njobs = int(args.njobs)
    create_mask(animal, resolution, njobs)


