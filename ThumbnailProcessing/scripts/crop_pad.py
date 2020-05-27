import numpy as np
from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os
import cv2 as cv

DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39'
CLEANED = os.path.join(DIR, 'preps', 'cleaned')
INPUT = os.path.join(DIR, 'preps', 'CH1')
OUTPUT = CLEANED
files = sorted(os.listdir(INPUT))

def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)

def crop_rows(img,cropy):
    img = get_last_2d(img)
    y,x = img.shape
    starty = y + cropy
    return img[0:starty,:]


def is_barcode(rect, min_width, min_height):
    x, y, w, h = rect
    area = w * h
    result = ((x + y > 0) and w > min_width and h > min_height and area > 1000)
    return result


def crop_brain(input, min_width, min_height):
    #new_img = np.zeros([max_height, max_width])
    copied = np.copy(input)
    lowStart = 12
    highStart = 23000
    v = np.median(input)
    sigma = 0.33
    lowVal = int(max(lowStart, (1.0 - sigma) * v))
    hist = np.histogram(input.flatten(), bins=10)
    #highVal = 19660
    highVal = int(hist[1][5])
    # creation of mask
    img_mask = cv.inRange(input, lowVal, highVal)
    contours, hierarchy = cv.findContours(img_mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    contour_sizes = [(cv.contourArea(contour), contour) for contour in contours]
    contours_poly = [None]*len(contours)
    boundRect = [None]*len(contours)
    #centers = [None]*len(contours)
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
    return copied, lowVal, highVal


def place_image(img, max_width, max_height):
    zmidr = max_height // 2
    zmidc = max_width // 2
    startr = zmidr - (img.shape[0] // 2)
    endr = startr + img.shape[0]
    startc = zmidc - (img.shape[1] // 2)
    endc = startc + img.shape[1]
    new_img = np.zeros([max_height, max_width])
    try:
        new_img[startr:endr, startc:endc] = img
    except:
        print('could not create new img', file)

    return new_img.astype('uint16')

def get_mins(shape, section_number):
    min_size = 50
    rows = shape[0]
    cols = shape[1]
    min_width = (cols // 8) + section_number + min_size
    min_height = (rows // 12) + section_number + min_size
    return min_width, min_height


max_width = 1740
max_height = 1050

# get oriented for comparison
img_inputs = []
img_outputs = []
file_inputs = []
titles = []
masks = []
section_number = 0
midpoint = len(files) // 2
# tmp_img = files[67]
# tfiles = [tmp_img]
dels = os.listdir(OUTPUT)
for d in dels:
    os.unlink(os.path.join(OUTPUT, d))

for i, file in enumerate(tqdm(files)):
    infile = os.path.join(INPUT, file)
    img = io.imread(infile)
    # img = cv.imread(infile, -1)
    img_inputs.append(img)
    file_inputs.append(file)
    img = crop_rows(img, 30)
    min_width, min_height = get_mins(img.shape, section_number)
    img, low, high = crop_brain(img, min_width, min_height)
    img = place_image(img, max_width, max_height)
    outpath = os.path.join(OUTPUT, file)
    cv.imwrite(outpath, img.astype('uint16'))
    if i <= midpoint:
        section_number += 2
    else:
        section_number -= 2
    del img
