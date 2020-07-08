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
from utilities.alignment_utility import get_last_2d, linnorm
from utilities.file_location import FileLocationManager


def find_contour_area(mask):
    area2 = 0
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    c1 = max(contours, key=cv2.contourArea)
    area1 = cv2.contourArea(c1)
    idx = get_index(c1, contours)  # 2
    contours.pop(idx)
    if len(contours) > 0:
        c2 = max(contours, key=cv2.contourArea)
        area2 = cv2.contourArea(c2)
    return area1 + area2


def get_index(array, list_of_arrays):
    for j, a in enumerate(list_of_arrays):
        if np.array_equal(array, a):
            return j
    return None


def fix_with_fill(img):
    limit = 250
    dt = np.uint8
    no_strip, fe = remove_strip(img)
    if fe != 0:
        img[:, fe:] = 0  # mask the strip

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
    contours, hierarchy = cv2.findContours(im_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    lc = []
    c1 = max(contours, key=cv2.contourArea)
    lc.append(c1)
    area1 = cv2.contourArea(c1)
    idx = get_index(c1, contours)  # 2
    contours.pop(idx)
    if len(contours) > 0:
        cX = max(contours, key=cv2.contourArea)
        area2 = cv2.contourArea(cX)
        if area2 > (area1 * 0.125):
            lc.append(cX)
        idx = get_index(cX, contours)  # 2
        contours.pop(idx)
    if len(contours) > 0:
        cX = max(contours, key=cv2.contourArea)
        area3 = cv2.contourArea(cX)
        if area3 > (area1 * 0.125):
            lc.append(cX)
        idx = get_index(cX, contours)  # 2
        contours.pop(idx)
    cv2.fillPoly(stencil, lc, 255)

    if len(contours) > 0:
        cv2.fillPoly(stencil, contours, 0)

    #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    #dilation = cv2.dilate(stencil, kernel, iterations=2)
    return stencil


def fix_with_blob(img):
    no_strip, fe = remove_strip(img)
    min_value, threshold = find_threshold(img)
    ret, threshed = cv2.threshold(no_strip, threshold, 255, cv2.THRESH_BINARY)
    threshed = np.uint8(threshed)
    connectivity = 4
    output = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_32S)
    labels = output[1]
    stats = output[2]
    # Find the blob that corresponds to the section.
    if fe != 0:
        img[:, fe:] = 0  # mask the strip
    row = find_main_blob(stats, img)
    blob_label = row[1]['blob_label']
    # extract the blob
    blob = np.uint8(labels == blob_label) * 255
    # Perform morphological closing
    kernel10 = np.ones((10, 10), np.uint8)
    mask = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)
    return mask


def workershell(cmd):
    """
    Set up an shell command. That is what the shell true is for.
    Args:
        cmd:  a command line program with arguments in a string
    Returns: nothing
    """
    p = subprocess.Popen(cmd, shell=True, stderr=None, stdout=None)
    p.wait()


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


def scale_and_mask(src, mask, epsilon=0.01):
    vals = np.array(sorted(src[mask > 10]))
    ind = int(len(vals) * (1 - epsilon))
    _max = vals[ind]
    # print('thr=%d, index=%d'%(vals[ind],index))
    _range = 2 ** 16 - 1
    scaled = src * (45000. / _max)
    scaled[scaled > _range] = _range
    scaled = scaled * (mask > 10)
    return scaled, _max

def find_threshold(src):
    fig = matplotlib.figure.Figure()
    ax = matplotlib.axes.Axes(fig, (0, 0, 0, 0))
    n, bins, patches = ax.hist(src.flatten(), 360);
    del ax, fig
    min_point = np.argmin(n[:5])
    min_point = int(min(2, min_point))
    thresh = (min_point * 64000 / 360) + 100
    return min_point, thresh

strip_max=70; strip_min=5   # the range of width for the stripe
def remove_strip(src):
    projection=np.sum(src,axis=0)/10000.
    diff=projection[1:]-projection[:-1]
    loc,=np.nonzero(diff[-strip_max:-strip_min]>50)
    mval=np.max(diff[-strip_max:-strip_min])
    no_strip=np.copy(src)
    fe = 0
    if loc.shape[0]>0:
        loc=np.min(loc)
        from_end=strip_max-loc
        fe = -from_end - 2
        no_strip[:,fe:]=0 # mask the strip
    return no_strip, fe

def create_mask(animal, resolution):

    file_location_manager = FileLocationManager(animal)
    INPUT = os.path.join(file_location_manager.prep, 'CH1', 'thumbnail')
    MASKED = os.path.join(file_location_manager.prep, 'thumbnail_masked')

    if 'full' in resolution.lower():
        INPUT = os.path.join(file_location_manager.prep, 'CH1', 'full')
        THUMBNAIL = os.path.join(file_location_manager.prep, 'thumbnail_masked')
        MASKED = os.path.join(file_location_manager.prep, 'full_masked')
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
            mask = fix_with_fill(img)
            """
            area = find_contour_area(mask)
            areas.append(area)
            if i > 0 and area < (areas[i - 1] * 0.90):
                mask, area = fix_with_fill(img)
            areas.append(area)
            """
            # save the mask
            outpath = os.path.join(MASKED, file)
            cv2.imwrite(outpath, mask.astype('uint8'))

            # save the good scaled as CH1
            #outpath = os.path.join(OUTPUT, file)
            #cv2.imwrite(outpath, scaled.astype('uint16'))

if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--resolution', help='full or thumbnail', required=False, default='thumbnail')
    args = parser.parse_args()
    animal = args.animal
    resolution = args.resolution
    create_mask(animal, resolution)


