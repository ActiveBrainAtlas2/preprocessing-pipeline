import argparse
import os
import subprocess
from multiprocessing.pool import Pool

import cv2
import numpy as np
from skimage import io
from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.utilities_mask import get_index, fill_spots


def workershell(cmd):
    """
    Set up an shell command. That is what the shell true is for.
    Args:
        cmd:  a command line program with arguments in a list
    Returns: nothing
    """
    p = subprocess.Popen(cmd, shell=False, stderr=None, stdout=None)
    p.wait()


def mask_thionin(animal, full):
    logger = get_logger(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    OUTPUT = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    files = os.listdir(INPUT)

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
            height, width = src.shape
            del src
            resize = '{}x{}!'.format(width, height)
            cmd = ['convert', thumbfile, '-resize', resize, '-compress', 'lzw', '-depth', '8', outfile]
            commands.append(cmd)

        with Pool(4) as p:
            p.map(workershell, commands)

    else:
        big_kernel = np.ones((8, 8), np.uint8)
        for i, file in enumerate(tqdm(files)):
            infile = os.path.join(INPUT, file)
            #src = io.imread(infile)
            src = cv2.imread(infile, cv2.IMREAD_GRAYSCALE)

            start_bottom = src.shape[0] - 5
            bottom_rows = src[start_bottom:src.shape[0], :]
            avg = np.mean(bottom_rows)
            bgcolor = int(round(avg))
            lower = bgcolor - 8
            upper = bgcolor + 4
            bgmask = (src >= lower) & (src <= upper)
            src[bgmask] = bgcolor

            clahe = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(16, 16))
            h_src = clahe.apply(src)
            start_bottom = h_src.shape[0] - 5
            bottom_rows = h_src[start_bottom:h_src.shape[0], :]
            avg = np.mean(bottom_rows)
            bgcolor = int(round(avg)) - 50

            h, im_th = cv2.threshold(h_src, bgcolor, 255, cv2.THRESH_BINARY_INV)
            im_floodfill = im_th.copy()
            h, w = im_th.shape[:2]
            mask = np.zeros((h + 2, w + 2), np.uint8)
            cv2.floodFill(im_floodfill, mask, (0, 0), 255)
            im_floodfill_inv = cv2.bitwise_not(im_floodfill)
            im_out = im_th | im_floodfill_inv

            stencil = np.zeros(src.shape).astype('uint8')
            contours, hierarchy = cv2.findContours(im_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

            lc = []
            c1 = max(contours, key=cv2.contourArea)
            lc.append(c1)
            area1 = cv2.contourArea(c1)

            idx = get_index(c1, contours)  # 2
            contours.pop(idx)
            if len(contours) > 0:
                c2 = max(contours, key=cv2.contourArea)
                area2 = cv2.contourArea(c2)
                if area2 > 610:
                    lc.append(c2)
            cv2.fillPoly(stencil, lc, 255)

            if area1 > 3000:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
                opening = cv2.morphologyEx(stencil, cv2.MORPH_OPEN, kernel, iterations=3)
            else:
                opening = stencil

            dilation1 = cv2.erode(opening, big_kernel, iterations=1)
            dilation2 = cv2.dilate(dilation1, big_kernel, iterations=3)
            dilation3 = fill_spots(dilation2)

            outpath = os.path.join(OUTPUT, file)
            cv2.imwrite(outpath, dilation3.astype('uint8'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=False, default='thumbnail')

    args = parser.parse_args()
    animal = args.animal
    full = bool({'full': True, 'thumbnail': False}[args.resolution])

    mask_thionin(animal, full)
