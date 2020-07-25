import argparse
import os
from multiprocessing.pool import Pool

import cv2
import numpy as np
from skimage import io
from tqdm import tqdm

from sql_setup import CREATE_THUMBNAIL_MASKS
from utilities.alignment_utility import get_last_2d
from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.utilities_mask import fix_with_fill
from utilities.utilities_process import workernoshell


def create_mask(animal, full, njobs):
    logger = get_logger(animal)
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    sqlController.set_task(animal, CREATE_THUMBNAIL_MASKS)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    MASKED = os.path.join(fileLocationManager.prep, 'thumbnail_masked')

    if full:
        INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full')
        THUMBNAIL = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
        MASKED = os.path.join(fileLocationManager.prep, 'full_masked')
        files = sorted(os.listdir(INPUT))
        commands = []
        for i, file in enumerate(tqdm(files)):
            infile = os.path.join(INPUT, file)
            thumbfile = os.path.join(THUMBNAIL, file)
            outfile = os.path.join(MASKED, file)
            try:
                src = io.imread(infile)
            except:
                logger.warning(f'Could not open {infile}')
                continue
            src = get_last_2d(src)
            height, width = src.shape
            size = '{}x{}!'.format(width, height)
            del src
            #cmd = "convert {} -resize {}x{}! -compress lzw -depth 8 {}".format(thumbfile, width, height, outfile)
            cmd = ['convert', thumbfile, '-resize', size, '-compress', 'lzw', '-depth', '8', outfile]
            commands.append(cmd)

        with Pool(njobs) as p:
            p.map(workernoshell, commands)
    else:
        files = sorted(os.listdir(INPUT))

        for i, file in enumerate(tqdm(files)):
            infile = os.path.join(INPUT, file)
            try:
                img = io.imread(infile)
            except:
                logger.warning(f'Could not open {infile}')
                continue
            img = get_last_2d(img)
            mask = fix_with_fill(img, 250, np.uint8)
            # save the mask
            outpath = os.path.join(MASKED, file)
            cv2.imwrite(outpath, mask.astype('uint8'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=False, default='thumbnail')
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)

    args = parser.parse_args()
    animal = args.animal
    full = bool({'full': True, 'thumbnail': False}[args.resolution])
    njobs = int(args.njobs)

    create_mask(animal, full, njobs)
