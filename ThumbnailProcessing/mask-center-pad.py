import numpy as np
import matplotlib
from skimage import io
from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os
import cv2 as cv
import pandas as pd



DIR = os.path.join(HOME, 'DL39')
#DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39'
CH1 = os.path.join(DIR, 'CH1')
MASKED = os.path.join(DIR, 'masked')
INPUT = CH1
OUTPUT = MASKED
files = sorted(os.listdir(INPUT))


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
    n, bins, patches = ax.hist(src.flatten(), 160);
    del ax, fig
    min_point = np.argmin(n[:5])
    thresh = (min_point * 64000 / 180)
    # v = np.median(src)
    # thresh = int(max(min_point, (1.0 - sigma) * v))
    # thresh = min_point * 136 + 100
    # thresh = int(max(min_point, (1.0 - sigma) * v))
    thresh1 = int(min(400, thresh))
    return min_point, thresh1


max_width = 50100
max_height = 28000

for i, file in enumerate(tqdm(files)):
    infile = os.path.join(INPUT, file)
    img = io.imread(infile)
    min_value, threshold = find_threshold(img)
    ###### Threshold it so it becomes binary
    # threshold = 272
    ret, threshed = cv.threshold(img, threshold, 255, cv.THRESH_BINARY)
    threshed = np.uint8(threshed)
    ###### Find connected elements
    # You need to choose 4 or 8 for connectivity type
    connectivity = 4
    output = cv.connectedComponentsWithStats(threshed, connectivity, cv.CV_32S)
    # Get the results
    # The first cell is the number of labels
    num_labels = output[0]
    # The second cell is the label matrix
    labels = output[1]
    # The third cell is the stat matrix
    stats = output[2]
    # The fourth cell is the centroid matrix
    centroids = output[3]
    # Find the blob that corresponds to the section.
    row = find_main_blob(stats, img)
    blob_label = row[1]['blob_label']
    # extract the blob
    blob = np.uint8(labels == blob_label) * 255
    # Perform morphological closing
    kernel10 = np.ones((10, 10), np.uint8)
    closing = cv.morphologyEx(blob, cv.MORPH_CLOSE, kernel10, iterations=5)
    del blob
    # scale and mask
    scaled, _max = scale_and_mask(img, closing)
    del closing
    img = place_image(scaled, max_width, max_height)
    del scaled
    # img_outputs.append(img)
    outpath = os.path.join(OUTPUT, file)
    cv.imwrite(outpath, img.astype('uint16'))

