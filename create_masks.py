"""
This program loops through all the thumbnail images and creates a mask for each section.
The edges of the image are trimmed by filling in with the background color. The edges
are only filled if the average of the rows is below a threshold. The a good threshold
value of 44 was found to be useful.
2 masking methods are used, the first one uses nipy to create the first pass. The 2nd pass
uses the fix_with_fill method. This works 95% of the time. There are some cases
where the tissue gets missed due to low intensity values. There is a balancing act
going between getting all the tissue and getting rid of the junk outside the tissue, like
the barcode and glue
"""
import argparse
import os, sys
from multiprocessing.pool import Pool
import imagesize

import cv2
import numpy as np
from skimage import io
from tqdm import tqdm

from sql_setup import CREATE_THUMBNAIL_MASKS, CREATE_FULL_RES_MASKS
from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.utilities_mask import fix_with_fill, fix_thionin, trim_edges, create_mask_pass1
from utilities.utilities_process import get_last_2d, test_dir, workernoshell


def create_mask(animal, downsample, njobs):
    """
    This method decides if we are working on either full or downsampled image, and also
    if we are using thionin or NTB stains. The masking process is different depending on the stain.
    The 1st pass is creating masks for the downsampled images. Once they are made, we can just resize
    the downsampled masks to the larger ones since they are just binary images.
    :param animal: prep_id of animal
    :param full: type of resolution, either full or downsampled.
    :param njobs: number of jobs to send to subprocess. 4 is default. You don't need to adjust for downsampled images
    :return: nothing, the mask and rotated mask are written to disk in each loop
    """
    logger = get_logger(animal)
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    stain = sqlController.histology.counterstain
    sqlController.set_task(animal, CREATE_THUMBNAIL_MASKS)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    MASKED = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    os.makedirs(MASKED, exist_ok=True)
    if not downsample:
        sqlController.set_task(animal, CREATE_FULL_RES_MASKS)
        INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full')
        ##### Check if files in dir are valid
        error = test_dir(animal, INPUT, downsample, same_size=False)
        if len(error) > 0:
            print(error)
            sys.exit()

        THUMBNAIL = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
        ##### Check if files in dir are valid
        ##error = test_dir(animal, THUMBNAIL, full=False, same_size=False)
        MASKED = os.path.join(fileLocationManager.prep, 'full_masked')
        os.makedirs(MASKED, exist_ok=True)
        files = sorted(os.listdir(INPUT))
        commands = []
        for i, file in enumerate(tqdm(files)):
            infile = os.path.join(INPUT, file)
            thumbfile = os.path.join(THUMBNAIL, file)
            outpath = os.path.join(MASKED, file)
            if os.path.exists(outpath):
                continue
            try:
                width, height = imagesize.get(infile)
            except:
                logger.warning(f'Could not open {infile}')
                continue
            size = '{}x{}!'.format(width, height)
            cmd = ['convert', thumbfile, '-resize', size, '-compress', 'lzw', '-depth', '8', outpath]
            commands.append(cmd)

        with Pool(njobs) as p:
            p.map(workernoshell, commands)
    else:
        error = test_dir(animal, INPUT, downsample, same_size=False)
        if len(error) > 0:
            print(error)
            sys.exit()
        files = sorted(os.listdir(INPUT))

        for i, file in enumerate(tqdm(files)):
            infile = os.path.join(INPUT, file)
            outpath = os.path.join(MASKED, file)
            if os.path.exists(outpath):
                continue
            if 'thion' in stain.lower():
                try:
                    img = cv2.imread(infile, cv2.IMREAD_GRAYSCALE)
                except:
                    logger.warning(f'Could not open {infile}')
                    continue
                mask = fix_thionin(img)
            else:
                try:
                    img = io.imread(infile)
                    img = get_last_2d(img)
                except:
                    logger.warning(f'Could not open {infile}')
                    continue
                # perform 2 pass masking
                img = trim_edges(img)
                mask1 = create_mask_pass1(img)
                pass1 = cv2.bitwise_and(img, img, mask=mask1)
                ## pass2
                pass1 = cv2.GaussianBlur(pass1,(33,33),0)
                mask = fix_with_fill(pass1)

            # save the mask
            cv2.imwrite(outpath, mask.astype(np.uint8))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)

    args = parser.parse_args()
    animal = args.animal
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    njobs = int(args.njobs)

    create_mask(animal, downsample, njobs)
