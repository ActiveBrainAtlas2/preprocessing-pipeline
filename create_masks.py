import argparse
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
from utilities.alignment_utility import get_last_2d, linnorm
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workershell
from utilities.utilities_mask import get_index, pad_with_black, remove_strip


def fix_with_fill(img, limit, dt):
    no_strip, fe = remove_strip(img)
    if fe != 0:
        img[:, fe:] = 0  # mask the strip
    img = pad_with_black(img)
    img = (img / 256).astype(dt)
    h_src = linnorm(img, limit, dt)
    med = np.median(h_src)
    h, im_th = cv2.threshold(h_src, med, limit, cv2.THRESH_BINARY)
    im_floodfill = im_th.copy()
    h, w = im_th.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
    im_out = im_th | im_floodfill_inv
    stencil = np.zeros(img.shape).astype('uint8')

    # dilation = cv2.dilate(stencil,kernel,iterations = 2)
    kernel = np.ones((10, 10), np.uint8)
    eroded = cv2.erode(im_out, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    lc = []
    c1 = max(contours, key=cv2.contourArea)
    lc.append(c1)
    area1 = cv2.contourArea(c1)

    idx = get_index(c1, contours)  # 2
    contours.pop(idx)
    if len(contours) > 0:
        cX = max(contours, key=cv2.contourArea)
        area2 = cv2.contourArea(cX)
        if area2 > (area1 * 0.05):
            lc.append(cX)
            # cv2.fillPoly(stencil, lc, 255)
        idx = get_index(cX, contours)  # 2
        contours.pop(idx)

    if len(contours) > 0:
        cX = max(contours, key=cv2.contourArea)
        area3 = cv2.contourArea(cX)
        if area3 > (area1 * 0.15):
            lc.append(cX)
            # cv2.fillPoly(stencil, lc, 100)
        idx = get_index(cX, contours)  # 2
        contours.pop(idx)
    if len(contours) > 0:
        cX = max(contours, key=cv2.contourArea)
        area4 = cv2.contourArea(cX)
        if area4 > (area3 * 0.5):
            lc.append(cX)
            # cv2.fillPoly(stencil, lc, 100)
        idx = get_index(cX, contours)  # 2
        contours.pop(idx)

    cv2.fillPoly(stencil, lc, 255)

    if len(contours) > 0:
        cv2.fillPoly(stencil, contours, 0)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    mask = cv2.dilate(stencil, kernel, iterations=2)
    return mask


def create_mask(animal, resolution):

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
        for i, file in enumerate(tqdm(files)):
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

        with Pool(4) as p:
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
    args = parser.parse_args()
    animal = args.animal
    resolution = args.resolution
    create_mask(animal, resolution)


