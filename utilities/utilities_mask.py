import cv2
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.figure


def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m, n = data.shape[-2:]
    return data.flat[:m * n].reshape(m, n)


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


def make_mask(img):
    img = get_last_2d(img)
    no_strip, fe = remove_strip(img)

    # Threshold it so it becomes binary
    min_value, threshold = find_threshold(img)
    # threshold = 272
    ret, threshed = cv2.threshold(no_strip, threshold, 255, cv2.THRESH_BINARY)
    threshed = np.uint8(threshed)

    # Find connected elements
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
        img[:, fe:] = 0  # mask the strip
    # scale and mask
    scaled, _max = scale_and_mask(img, closing)

    return closing, scaled


def remove_strip(src):
    strip_max = 70;
    strip_min = 5  # the range of width for the stripe

    projection = np.sum(src, axis=0) / 10000.
    diff = projection[1:] - projection[:-1]
    loc, = np.nonzero(diff[-strip_max:-strip_min] > 50)
    mval = np.max(diff[-strip_max:-strip_min])
    no_strip = np.copy(src)
    fe = 0
    if loc.shape[0] > 0:
        loc = np.min(loc)
        from_end = strip_max - loc
        fe = -from_end - 2
        no_strip[:, fe:] = 0  # mask the strip
    return no_strip, fe


def place_image(img, max_width, max_height, bgcolor=None):
    zmidr = max_height // 2
    zmidc = max_width // 2
    startr = zmidr - (img.shape[0] // 2)
    endr = startr + img.shape[0]
    startc = zmidc - (img.shape[1] // 2)
    endc = startc + img.shape[1]
    dt = img.dtype
    if bgcolor == None:
        start_bottom = img.shape[0] - 5
        bottom_rows = img[start_bottom:img.shape[0], :]
        avg = np.mean(bottom_rows)
        bgcolor = int(round(avg))
    new_img = np.zeros([max_height, max_width]) + bgcolor
    new_img[startr:endr, startc:endc] = img

    return new_img.astype(dt)


def rotate_image(img, rotation):
    img = np.rot90(img, rotation)
    return img


def apply_mask(img, mask, stain, rotation, flip):
    max_width = 1400
    max_height = 900

    img = get_last_2d(img)
    dt = img.dtype

    start_bottom = img.shape[0] - 5
    bottom_rows = img[start_bottom:img.shape[0], :]
    avg = np.mean(bottom_rows)
    bgcolor = int(round(avg))

    if dt == np.dtype('uint16'):
        limit = 2 ** 16 - 1
        mask16 = np.copy(mask).astype(dt)
        mask16[mask16 > 0] = limit
        mask = mask16
    else:
        limit = 2 ** 8 - 1
        limit = bgcolor
        mask[mask > 0] = limit
        mask = limit - mask
        mask = place_image(mask, max_width, max_height, bgcolor)

    if stain == 'NTB':
        fixed = cv2.bitwise_and(img, mask)
    else:
        fixed = cv2.bitwise_or(img, mask)

    if rotation > 0:
        fixed = rotate_image(fixed, rotation)

    if flip == 'flip':
        fixed = np.flip(fixed)
    elif flip == 'flop':
        fixed = np.flip(fixed, axis=1)
    fixed = place_image(fixed, max_width, max_height, bgcolor)

    return fixed
