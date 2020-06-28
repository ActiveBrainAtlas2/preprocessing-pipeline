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

DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps'
INPUT = os.path.join(DIR, 'CH1', 'thumbnail')
OUTPUT = os.path.join(DIR, 'CH1', 'cleaned')
MASKED = os.path.join(DIR, 'masked')
files = sorted(os.listdir(INPUT))
lfiles = len(files)
if lfiles < 1:
    sys.exit()

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


    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}'.format(animal)
    INPUT = os.path.join(DIR, 'preps', 'CH1', 'thumbnail')
    MASKED = os.path.join(DIR, 'preps', 'thumbnail_masked')

    if 'full' in resolution.lower():
        INPUT = os.path.join(DIR, 'preps', 'CH1', 'full')
        THUMBNAIL = os.path.join(DIR, 'preps', 'thumbnail_masked')
        MASKED = os.path.join(DIR, 'preps', 'full_masked')
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
        files = sorted(os.listdir(INPUT))
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
            min_value, threshold = find_threshold(h_src)
            ret, threshed = cv2.threshold(h_src, threshold, 255, cv2.THRESH_BINARY)
            threshed = np.uint8(threshed)
            connectivity = 4
            output = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_32S)
            num_labels = output[0]
            labels = output[1]
            stats = output[2]
            centroids = output[3]
            row = find_main_blob(stats, h_src)
            blob_label = row[1]['blob_label']
            blob = np.uint8(labels == blob_label) * 255
            kernel10 = np.ones((10, 10), np.uint8)
            closing = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)

            outpath = os.path.join(MASKED, file)
            cv2.imwrite(outpath, closing.astype('uint8'))





if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--resolution', help='full or thumbnail', required=False, default='thumbnail')
    args = parser.parse_args()
    animal = args.animal
    resolution = args.resolution
    mask_thionin(animal, resolution)
