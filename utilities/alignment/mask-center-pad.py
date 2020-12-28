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

DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK43/preps'
INPUT = os.path.join(DIR, 'CH1', 'thumbnail')
OUTPUT = os.path.join(DIR, 'CH1', 'cleaned')
MASKED = os.path.join(DIR, 'masked')
files = sorted(os.listdir(INPUT))
lfiles = len(files)
print(len(files))
if lfiles < 1:
    sys.exit()

print('Input dir', INPUT)
print('output dir', OUTPUT)
print('mask dir', MASKED)


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
    thresh = (min_point * 64000 / 360) + 300
    return min_point, thresh

strip_max=70; strip_min=5   # the range of width for the stripe
def remove_strip(src):
    projection=np.sum(src,axis=0)/10000.
    diff=projection[1:]-projection[:-1]
    loc,=np.nonzero(diff[-strip_max:-strip_min]>50)
    mval=np.max(diff[-strip_max:-strip_min])
    #print('  ',mval,i,end=' ')
    no_strip=np.copy(src)
    fe = 0
    if loc.shape[0]>0:
        loc=np.min(loc)
        from_end=strip_max-loc
        #print(from_end,diff[-from_end-2:-from_end+2])
        fe = -from_end-2
        no_strip[:,-from_end-2:]=0 # mask the strip
    return no_strip, fe

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
    no_strip, fe = remove_strip(img)

    min_value, threshold = find_threshold(img)
    ###### Threshold it so it becomes binary
    # threshold = 272
    ret, threshed = cv2.threshold(no_strip, threshold, 255, cv2.THRESH_BINARY)
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
    if fe != 0:
        img[:,fe:]=0 # mask the strip
    # scale and mask
    try:
        scaled, _max = scale_and_mask(img, closing)
    except:
        print(min_value, threshold, file)

    outpath = os.path.join(MASKED, file)
    cv2.imwrite(outpath, closing.astype('uint8'))
    continue

    del closing
    try:
        img = place_image(scaled, file, max_width, max_height)
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

