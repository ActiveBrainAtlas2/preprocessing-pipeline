import argparse
import subprocess
from multiprocessing.pool import Pool

import numpy as np
import matplotlib
import matplotlib.figure
from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os, sys
import cv2
import pandas as pd

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import get_last_2d, place_image
from utilities.file_location import FileLocationManager


def find_threshold(src):
    fig = matplotlib.figure.Figure()
    ax = matplotlib.axes.Axes(fig, (0,0,0,0))
    n,bins,patches=ax.hist(src.flatten(),360);
    del ax, fig
    min_point=np.argmin(n[:5])
    min_point = int(max(2, min_point))
    thresh=min_point * 20
    return min_point, thresh


def find_main_blob(stats, image):
    height, width = image.shape
    df = pd.DataFrame(stats)
    df.columns = ['Left', 'Top', 'Width', 'Height', 'Area']
    df['blob_label'] = df.index
    df = df.sort_values(by='Area', ascending=False)
    for row in df.iterrows():
        Left = row[1]['Left']
        Top = row[1]['Top']
        Width = row[1]['Width']
        Height = row[1]['Height']
        corners = int(Left == 0) + int(Top == 0) + int(Width == width) + int(Height == height)
        if corners <= 2:
            return row

def get_index(array, list_of_arrays):
    for j, a in enumerate(list_of_arrays):
        if np.array_equal(array, a):
            return j
    return None

def workershell(cmd):
    """
    Set up an shell command. That is what the shell true is for.
    Args:
        cmd:  a command line program with arguments in a string
    Returns: nothing
    """
    p = subprocess.Popen(cmd, shell=True, stderr=None, stdout=None)
    p.wait()

def mask_thionin(animal, resolution='thumbnail'):

    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    OUTPUT = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    files = os.listdir(INPUT)


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
            height, width = src.shape
            del src
            cmd = "convert {} -resize {}x{}! -compress lzw -depth 8 {}".format(thumbfile, width, height, outfile)
            commands.append(cmd)

        with Pool(10) as p:
            p.map(workershell, commands)

    else:
        for i, file in enumerate(tqdm(files)):
            infile = os.path.join(INPUT, file)
            try:
                src = io.imread(infile)
            except:
                print('Could not open', infile)
                continue
            src = get_last_2d(src)

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
            ## for dark background h, im_th = cv2.threshold(h_src, bgcolor, 255, cv2.THRESH_BINARY)
            # Copy the thresholded image.
            im_floodfill = im_th.copy()
            # Mask used to flood filling.
            h, w = im_th.shape[:2]
            mask = np.zeros((h + 2, w + 2), np.uint8)
            # Floodfill from point (0, 0)
            cv2.floodFill(im_floodfill, mask, (0, 0), 255)
            # Invert floodfilled image
            im_floodfill_inv = cv2.bitwise_not(im_floodfill)
            # Combine the two images to get the foreground.
            im_out = im_th | im_floodfill_inv
            stencil = np.zeros(src.shape).astype('uint8')
            contours, hierarchy = cv2.findContours(im_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

            lc = []
            c1 = max(contours, key=cv2.contourArea)
            lc.append(c1)
            area1 = cv2.contourArea(c1)
            area2 = 0
            idx = get_index(c1, contours)  # 1
            contours.pop(idx)
            if len(contours) > 0:
                c2 = max(contours, key=cv2.contourArea)
                area2 = cv2.contourArea(c2)
                if area2 > 610:
                    lc.append(c2)
            cv2.fillPoly(stencil, lc, 255)

            if area1 > 2000:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
                # (thresh, binRed) = cv2.threshold(stencil, 128, 255, cv2.THRESH_BINARY)
                finished = cv2.morphologyEx(stencil, cv2.MORPH_OPEN, kernel, iterations=3)
            else:
                finished = stencil


            outpath = os.path.join(OUTPUT, file)
            cv2.imwrite(outpath, finished.astype('uint8'))


if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--resolution', help='full or thumbnail', required=False, default='thumbnail')
    args = parser.parse_args()
    animal = args.animal
    resolution = args.resolution
    mask_thionin(animal, resolution)
