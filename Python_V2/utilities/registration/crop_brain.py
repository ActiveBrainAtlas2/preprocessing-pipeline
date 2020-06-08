import numpy as np
from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os
import cv2 as cv

#DIR = os.path.join(HOME, 'programming', 'dk39')
DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39'
ORIENTED = os.path.join(DIR, 'preps', 'oriented')
RESIZED = os.path.join(DIR, 'preps', 'resized')
THUMBNAIL = os.path.join(DIR, 'preps', 'thumbnail')
CH1 = os.path.join(DIR, 'CH1_change')
INPUT = CH1
files = sorted(os.listdir(INPUT))


def get_max_size(INPUT):
    widths = []
    heights = []
    files = os.listdir(INPUT)
    #midpoint = len(files)
    #files = files[midpoint - 5:midpoint + 5]
    #files = files[-5:-1]
    for file in files:
        img = io.imread(os.path.join(INPUT, file))
        heights.append(img.shape[0])
        widths.append(img.shape[1])

    max_width = max(widths)
    max_height = max(heights)

    return max_width, max_height


def is_barcode(rect, min_width, min_height):
    x, y, w, h = rect
    area = w * h
    result = (x >= 0 and w > min_width and h > min_height and area > 1000)
    return result

def crop_brain(input, min_width, min_height, max_width, max_height):
    #new_img = np.zeros([max_height, max_width])
    copied = np.copy(input)
    lowVal = 0
    highVal = 250
    # creation of mask
    img_mask = cv.inRange(input, lowVal, highVal)
    contours, hierarchy = cv.findContours(img_mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    contours_poly = [None]*len(contours)
    boundRect = [None]*len(contours)
    #centers = [None]*len(contours)
    found = False
    areas = []
    rects = []
    for i, c in enumerate(contours):
        contours_poly[i] = cv.approxPolyDP(c, 3, True)
        boundRect[i] = cv.boundingRect(contours_poly[i])
        if is_barcode(boundRect[i], min_width, min_height):
            rect = boundRect[i]
            x,y,w,h = rect
            areas.append(w*h)
            rects.append(rect)
    if len(rects) > 0:
        big_rect = rects[areas.index(max(areas))]
        x,y,w,h = big_rect
        copied = copied[y:y+h,x:x+w]
        found = True
    return copied, found

def get_mins(shape, section_number):
    min_size = 50
    rows = shape[0]
    cols = shape[1]
    min_width = (cols // 8) + section_number + min_size
    min_height = (rows // 12) + section_number + min_size
    return min_width, min_height



#max_width, max_height = get_max_size(INPUT)
max_width = 39030
max_height = 26100
zmidr = max_height // 2
zmidc = max_width // 2

print(max_width, max_height)

#files = files[0:9]


OUTPUT = RESIZED
section_number = 0
for i, file in enumerate(tqdm(files)):
    infile = os.path.join(INPUT, file)
    try:
        #img = cv.imread(infile, cv.IMREAD_GRAYSCALE)
        img = io.imread(infile)
    except:
        print('file died at reading', file)
    #min_width, min_height = get_mins(img.shape, i)
    #img, found = crop_brain(img, min_width, min_height, max_width, max_height)
    # img = get_last_2d(img)
    startr = zmidr - (img.shape[0] // 2)
    endr = startr + img.shape[0]
    startc = zmidc - (img.shape[1] // 2)
    endc = startc + img.shape[1]
    new_img = np.zeros([max_height, max_width])
    try:
        new_img[startr:endr, startc:endc] = img
    except:
        print('file died at new image creation', file)

    img = None
    flat = new_img.flatten()
    fmax = int(flat.max())
    fmin = int(flat.min())
    flat = flat + abs(fmin)
    new_img = np.reshape(flat, new_img.shape)
    flat = None

    new_img = new_img.astype('uint16')
    #outfile = '{}.tif'.format(str(i).zfill(4))
    #outfile = '{}.tif'.format(str(i).zfill(4))
    outpath = os.path.join(OUTPUT, file)
    cv.imwrite(outpath, new_img)

    new_img = None
    section_number += 2

