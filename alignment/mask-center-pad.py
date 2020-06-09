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

DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK43/preps'
INPUT = os.path.join(DIR, 'CH1', 'thumbnail')
OUTPUT = os.path.join(DIR, 'CH1', 'cleaned')
MASKED = os.path.join(DIR, 'CH1', 'masked')
files = sorted(os.listdir(INPUT))
lfiles = len(files)
print(len(files))
if lfiles < 1:
    sys.exit()

print('Input dir', INPUT)
print('output dir', OUTPUT)
print('mask dir', MASKED)



def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)


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
    n, bins, patches = ax.hist(src.flatten(), 360);
    del ax, fig
    min_point = np.argmin(n[:5])
    min_point = int(max(2, min_point))
    thresh = (min_point * 64000 / 360)
    return min_point, thresh

def crop_bar(img):
    r,c = img.shape
    fill = c - ( c // 14)
    img[:, fill:c] = 0
    return img

#max_width = 55700
#max_height = 33600
max_width = 1050
max_height = 1740
tilesize = 16

for i, file in enumerate(tqdm(files)):
    infile = os.path.join(INPUT, file)
    try:
        img = io.imread(infile)
    except:
        print('Could not open', infile)
        continue
    img = get_last_2d(img)
    img = crop_bar(img)

    min_value, threshold = find_threshold(img)
    ###### Threshold it so it becomes binary
    # threshold = 272
    ret, threshed = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    threshed = np.uint8(threshed)
    ###### Find connected elements
    # You need to choose 4 or 8 for connectivity type
    connectivity = 4
    output = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_32S)
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
    closing = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)
    del blob
    # scale and mask
    scaled, _max = scale_and_mask(img, closing)
    outpath = os.path.join(MASKED, file)
    closing = place_image(closing, max_width, max_height)
    cv2.imwrite(outpath, closing.astype('uint8'))
    del closing
    try:
        img = place_image(scaled, max_width, max_height)
    except:
        print('Could not place image', infile, img.shape)
        continue

    del scaled

    # img_outputs.append(img)
    # adaptive histogram equalization
    #####clahe = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(tilesize, tilesize))
    #####img = clahe.apply(img)

    outpath = os.path.join(OUTPUT, file)
    cv2.imwrite(outpath, img.astype('uint16'))

