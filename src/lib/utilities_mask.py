import cv2
import numpy as np
import pandas as pd
import matplotlib.figure
from skimage import exposure, io

from lib.utilities_process import get_last_2d

font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 1
thickness = 2

"""
def create_xcf(tif_path,mask_path,xcf_path):
    interface = GimpInterface()
    gimp_tool_path = os.path.join(os.getcwd(),'src','lib')
    interface.import_custome_library(gimp_tool_path,'gimp_tools')
    interface.create_xcf(tif_path,mask_path,xcf_path)
    interface.add_batch_script()
    report = interface.execute()
    return report

def save_mask_after_edit(modsav,xcf_path):
    interface = GimpInterface()
    gimp_tool_path = os.path.join(os.getcwd(),'src','lib')
    interface.import_custome_library(gimp_tool_path,'gimp_tools')
    interface.save_mask(modsav,xcf_path)
    interface.add_batch_script()
    report = interface.execute()
    return report
"""

def rotate_image(img, file, rotation):
    """
    Rotate the image by the number of rotation
    :param img: image to work on
    :param file: file name and path
    :param rotation: number of rotations, 1 = 90degrees clockwise
    :return: rotated image
    """
    try:
        img = np.rot90(img, rotation, axes=(1,0))
    except:
        print('Could not rotate', file)
    return img

def remove_strip(src):
    strip_max = 150;
    strip_min = 5  # the range of width for the stripe
    projection=np.sum(src,axis=0)/10000.
    diff=projection[1:]-projection[:-1]
    loc,=np.nonzero(diff[-strip_max:-strip_min]>50)
    no_strip=np.copy(src)
    fe = 0
    if loc.shape[0]>0:
        loc=np.min(loc)
        from_end=strip_max-loc
        fe = -from_end - 2
        no_strip[:,fe:]=0 # mask the strip
    return no_strip, fe

def find_threshold(src):
    """
    from Yoav
    :param src:
    :return:
    """
    fig = matplotlib.figure.Figure()
    ax = matplotlib.axes.Axes(fig, (0,0,0,0))
    n,bins,patches=ax.hist(src.flatten(),160);
    del ax, fig
    min_point=np.argmin(n[:5])
    thresh=min_point*64000/160+1000
    return thresh


def find_main_blob(stats,image):
    """
    from Yoav
    :param src:
    :return:
    """
    height,width=image.shape
    df=pd.DataFrame(stats)
    df.columns=['Left','Top','Width','Height','Area']
    df['blob_label']=df.index
    df=df.sort_values(by='Area',ascending=False)

    for row in df.iterrows():
        Left=row[1]['Left']
        Top=row[1]['Top']
        Width=row[1]['Width']
        Height=row[1]['Height']
        corners= int(Left==0)+int(Top==0)+int(Width==width)+int(Height==height)
        if corners<=2:
            return row


def scale_and_mask(src, mask, epsilon=0.01):
    """
    from Yoav
    :param src:
    :return:
    """
    vals = np.array(sorted(src[mask > 10]))
    ind = int(len(vals) * (1 - epsilon))
    _max = vals[ind]
    # print('thr=%d, index=%d'%(vals[ind],index))
    _range = 2 ** 16 - 1
    scaled = src * (45000. / _max)
    scaled[scaled > _range] = _range
    scaled = scaled * (mask > 10)
    return scaled, _max


def fix_with_blob(img):
    """
    Yoav's algorithmn for finding the blob and creating mask. Taken from the loop
    :param img: 16 bit channel 1 image
    :return:
    """
    no_strip, _ = remove_strip(img)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(12, 12))
    no_strip = clahe.apply(no_strip)
    #no_strip = img.copy()
    ###### Threshold it so it becomes binary
    threshold = find_threshold(no_strip)
    ret, threshed = cv2.threshold(no_strip,threshold,255,cv2.THRESH_BINARY)
    threshed=np.uint8(threshed)
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
    row=find_main_blob(stats,img)
    blob_label=row[1]['blob_label']

    #extract the blob
    blob=np.uint8(labels==blob_label)*255

    #Perform morphological closing
    kernel10 = np.ones((10,10),np.uint8)
    mask = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)
    return mask


def make_mask(img):
    img = get_last_2d(img)
    no_strip, fe = remove_strip(img)

    # Threshold it so it becomes binary
    threshold = find_threshold(img)
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


def place_image(img, file, max_width, max_height, bgcolor=None):
    """
    Places the image in a padded one size container with the correct background
    :param img: image we are working on.
    :param file: file name and path location
    :param max_width: width to pad
    :param max_height: height to pad
    :param bgcolor: background color of image, 0 for NTB, white for thionin
    :return: placed image centered in the correct size.
    """
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
    if img.ndim == 2:
        try:
            new_img[startr:endr, startc:endc] = img
        except:
            print('Could not place {} with width:{}, height:{} in {}x{}'
                  .format(file, img.shape[1], img.shape[0], max_width, max_height))
    if img.ndim == 3:
        try:
            new_img = np.zeros([max_height, max_width, 3]) + bgcolor
            new_img[startr:endr, startc:endc,0] = img[:,:,0]
            new_img[startr:endr, startc:endc,1] = img[:,:,1]
            new_img[startr:endr, startc:endc,2] = img[:,:,2]
        except:
            print('Could not place 3DIM image {} with width:{}, height:{} in {}x{}'
                  .format(file, img.shape[1], img.shape[0], max_width, max_height))
    del img
    return new_img.astype(dt)


def pad_with_black(img):
    r,c = img.shape
    pad = 12
    img[0:pad,:] = 0 # top
    img[:,c-5:c] = 0 # right
    img[r-pad:r,:] = 0 # bottom
    img[:,0:5] = 0 # left
    return img


def get_index(array, list_of_arrays):
    for j, a in enumerate(list_of_arrays):
        if np.array_equal(array, a):
            return j
    return None


def check_contour(contours, area, lc):
    if len(contours) > 0:
        cX = max(contours, key=cv2.contourArea)
        areaX = cv2.contourArea(cX)
        if areaX > (area * 0.05):
            lc.append(cX)
            idx = get_index(cX, contours)
            contours.pop(idx)
        return contours, lc


def scaled(img, mask, epsilon=0.05, scale=45000):
    """
    This scales the image to the limit specified. You can get this value
    by looking at the combined histogram of the image stack. It is quite
    often less than 30000 for channel 1
    The scale is hardcoded to 45000 which was a good value from Yoav
    :param img: image we are working on.
    :param mask: binary mask file
    :param epsilon:
    :param limit: max value we wish to scale to
    :return: scaled image in 16bit format
    """
    _max = np.quantile(img[mask > 0], 1 - epsilon) # gets almost the max value of img
    # print('thr=%d, index=%d'%(vals[ind],index))
    if scale > 255:
        _range = 2 ** 16 - 1 # 16bit
        data_type = np.uint16
    else:
        _range = 2 ** 8 - 1 # 8bit
        data_type = np.uint8        
    scaled = img * (scale / _max) # scale the image from original values to e.g., 30000/10000
    scaled[scaled > _range] = _range # if values are > 16bit, set to 16bit
    scaled = scaled * (mask > 10) # just work on the non masked values
    del img
    return scaled.astype(data_type)


def trim_edges(img):
    """
    Trim the edges of the image and fill in with the background color. Only used with NTB images.
    The threshold value below was found to work best. If the mean value of the row/column
    is equal or below that threshold, the row/column is filled with the background color. For NTB
    images the background color is black: 0.
    :param img: image to work on
    :return: returns the image with trimmed edges
    """
    no_strip, fe  = remove_strip(img)
    img_shape = img.shape
    if fe != 0:
        img[:, fe:] = 0  # mask the strip
    img = (img / 256).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=30.0, tileGridSize=(120, 120))
    img = clahe.apply(img)
    h_src = img.copy()
    limit = img_shape[1] // 12
    thresh1 = np.quantile(img[img > 0], 0.75)
    thresh2 = np.median(img)
    threshold = int(min(thresh1, thresh2))

    # trim left
    """
    for i in range(0,limit//2):
        b = h_src[:,i]
        m = np.mean(b)
        if m <= threshold:
            h_src[:,i] = 0
    """
    # trim right
    for i in range(img_shape[1]-limit,img_shape[1]):
        b = h_src[:,i]
        m = np.mean(b)
        if m <= threshold:
            h_src[:,i] = 0

    # trim top
    limit = limit // 2
    for i in range(0,limit):
        b = h_src[i,:]
        m = np.mean(b)
        if m <= threshold:
            h_src[i,:] = 0

    # trim bottom
    limit = limit // 2
    for i in range(img_shape[0]-limit,img_shape[0]):
        b = h_src[i,:]
        m = np.mean(b)
        if m <= threshold:
            h_src[i,:] = 0

    return h_src

def create_mask_pass1(img):
    """
    This is the first pass in creating a mask. The skimage.exposure is used as it helps to get rid
    of the glue around the tissue. This also calls the compute_mask method which is part
    of the nipy package which you will need to install from github
    :param img: the raw image
    :return:  the 1st pass of the image
    """
    pass
    """
    img = exposure.adjust_log(img, 1)
    img = exposure.adjust_gamma(img, 2)

    mask = compute_mask(img, m=0.2, M=0.9, cc=False, opening=2, exclude_zeros=True)
    mask = mask.astype(int)
    mask[mask==0] = 0
    mask[mask==1] = 255
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask.astype(np.uint8), kernel, iterations=2)
    mask = mask.astype(np.uint8)
    return mask
    """


def fix_with_fill(img, debug=False):
    """
    This is the 2nd pass of the create mask. This removes the bar strip
    on the right and finds the blobs near the center of the slide.
    It sets everything that is not a blob of tissue to black.
    The critical value is the threshold value below. Instead of using
    the median value, a better way might be to get a value from the histogram????
    :param img: 8bit image that has already been cleaned from the 1st pass
    :param debug: shows more info
    :return: the final mask
    """
    no_strip, fe = remove_strip(img)
    img_shape = img.shape
    if fe != 0:
        img[:, fe:] = 0  # mask the strip
    img = linnorm(img, 200)
    h_src = img.copy()
    del no_strip
    threshold = np.median(h_src)
    lowVal = threshold + 4 # threshold + 2 in the debug function
    highVal = 200
    im_th = cv2.inRange(h_src, lowVal, highVal)
    im_floodfill = im_th.copy()
    h, w = im_th.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
    del im_floodfill
    im_out = im_th | im_floodfill_inv
    stencil = np.zeros(h_src.shape).astype('uint8')
    del im_th
    del im_floodfill_inv
    big_kernel = np.ones((16, 16), np.uint8)
    contours, hierarchy = cv2.findContours(im_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    del im_out

    lc = []
    c1 = max(contours, key=cv2.contourArea)
    areaPrev = cv2.contourArea(c1)
    lc.append(c1)
    idx = get_index(c1, contours)
    contours.pop(idx)

    if debug:
        areas = []
        coords = []
        mX = cv2.moments(c1) # get center of mass of each contour and make sure it is not on an edge
        m00 = mX['m00']
        cx = mX['m10'] // m00
        cy = mX['m01'] // m00
        org = (int(cx), int(cy))
        coords.append(org)
        areas.append(str(areaPrev))

    midrow = img_shape[0] // 2
    topbound = midrow - (midrow * 0.85)
    bottombound = midrow + (midrow * 0.98)
    midcolumn = img_shape[1] // 2
    leftbound = midcolumn - (midcolumn * 0.75)
    rightbound = midcolumn + (midcolumn * 0.5)
    AREA_THRESHOLD = 0.01

    for x in range(1,5):
        if len(contours) > 0:
            cX = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(cX)
            mX = cv2.moments(cX)
            m00 = mX['m00']
            if m00 > 0:
                cx = mX['m10'] // m00
                cy = mX['m01'] // m00
                if (area > (areaPrev * AREA_THRESHOLD * x * x)
                        and cx > leftbound and cx < rightbound) and cy > topbound and cy < bottombound:
                    lc.append(cX)
                    idx = get_index(cX, contours)
                    contours.pop(idx)
                    areaPrev = area
                    if debug:
                        org = (int(cx), int(cy))
                        coords.append(org)
                        area_str = '{}, {}'.format(x, str(area))
                        areas.append(area_str)

        else:
            break

    cv2.fillPoly(stencil, lc, 255)
    dilation = cv2.dilate(stencil, big_kernel, iterations=3)

    if debug:
        del stencil
        for a,c in zip(areas, coords):
            cv2.putText(dilation, a, c, font,
                        fontScale, 2, thickness, cv2.LINE_AA)
        return dilation, lowVal, highVal, threshold

    return dilation


def fix_thionin(img, debug=False, dilation_itr=1, bg_mask=False, threshold_range=35, clip_limit=2.0):
    """
    Used for the thionin create masks script
    :param img: input image
    :return: a black and white mask image
    """
    # Junjie: I changed the background sampling area from bottom to top rows,
    # since for some of the images the bottom rows contain some foreground.
    # start_bottom = img.shape[0] - 5 # get mean background color from bottom rows
    # bottom_rows = img[start_bottom:img.shape[0], :]
    top_rows = img[0:5, :]
    avg = np.mean(top_rows)
    bgcolor = int(round(avg))
    if bg_mask:
        lower = bgcolor - 8
        upper = bgcolor + 4
        bgmask = (img >= lower) & (img <= upper)
        img[bgmask] = 255
    # -10 too much
    # -70 pretty good
    # -90 missing stuff
    bgcolor = int(round(avg)) - threshold_range # -45 in the debug version
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    img = clahe.apply(img)

    h, im_th = cv2.threshold(img, bgcolor, 255, cv2.THRESH_BINARY_INV)
    im_floodfill = im_th.copy()
    h, w = im_th.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
    im_out = im_th | im_floodfill_inv
    kernel = np.ones((4, 4), np.uint8)
    im_out = cv2.dilate(im_out, kernel, iterations=1)

    stencil = np.zeros(img.shape).astype('uint8')
#     contours, hierarchy = cv2.findContours(im_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours, hierarchy = cv2.findContours(im_out, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # get the contours and make the good ones all white, everything else black
    lc = [] # list of good contours
    c1 = max(contours, key=cv2.contourArea) # 1st biggest contour
    areaPrev = cv2.contourArea(c1) # area of biggest contour
    lc.append(c1) # add to list of good contours to make white
    idx = get_index(c1, contours) # pop that one out and test the rest of the contours
    contours.pop(idx)

    # find contours in the middle
    midrow = img.shape[0] // 2
    topbound = midrow - (midrow * 0.65)
    bottombound = midrow + (midrow * 0.5)
    midcolumn = img.shape[1] // 2
    leftbound = midcolumn - (midcolumn * 0.95)
    rightbound = midcolumn + (midcolumn * 0.85)
    AREA_THRESHOLD = 0.01

    if debug:
        areas = []
        coords = []
        mX = cv2.moments(c1) # get center of mass of each contour and make sure it is not on an edge
        m00 = mX['m00']
        cx = mX['m10'] // m00
        cy = mX['m01'] // m00
        org = (int(cx), int(cy))
        coords.append(org)
        areas.append(str(areaPrev))

    for x in range(1,5):
        if len(contours) > 0:
            cX = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(cX)
            mX = cv2.moments(cX) # gets center of mass
            m00 = mX['m00']
            if m00 > 0:
                cx = mX['m10'] // m00
                cy = mX['m01'] // m00
                if (area > (areaPrev * AREA_THRESHOLD * x * x)
                        and cx > leftbound and cx < rightbound) and cy > topbound and cy < bottombound:
                    lc.append(cX)
                    idx = get_index(cX, contours)
                    contours.pop(idx)
                    areaPrev = area
                    if debug:
                        org = (int(cx), int(cy))
                        coords.append(org)
                        area_str = '{}, {}'.format(x, str(area))
                        areas.append( area_str )
        else:
            break

    cv2.fillPoly(stencil, lc, 255) # turn all junk to white
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
    dilation = cv2.dilate(stencil, morph_kernel, iterations=dilation_itr)

    if debug:
        for a,c in zip(areas, coords):
            cv2.putText(dilation, a, c, font,
                        fontScale, 2, thickness, cv2.LINE_AA)

    return dilation

def fix_thionin_debug(img, dilation_itr=1):
    return fix_thionin(img, debug=True, dilation_itr=dilation_itr)

def fix_with_fill_debug(img):
    return fix_with_fill(img, debug=True)


def lognorm(img, limit):
    lxf = np.log(img + 0.005)
    lxf = np.where(lxf < 0, 0, lxf)
    xmin = min(lxf.flatten())
    xmax = max(lxf.flatten())
    return -lxf * limit / (xmax - xmin) + xmax * limit / (xmax - xmin)  # log of data and stretch 0 to limit


def linnorm(img, limit, mask=None):
    if mask is not None:
        img = img * (mask > 10)
    flat = img.flatten()
    hist, bins = np.histogram(flat, limit + 1)
    cdf = hist.cumsum()  # cumulative distribution function
    cdf = limit * cdf / cdf[-1]  # normalize
    # use linear interpolation of cdf to find new pixel values
    img_norm = np.interp(flat, bins[:-1], cdf)
    img_norm = np.reshape(img_norm, img.shape)
    if mask is not None:
        img_norm = img_norm * (mask > 10)
    return img_norm

def equalize(f):
    h = np.histogram(f, bins=np.arange(2**16))[0]
    H = np.cumsum(h) / float(np.sum(h))
    e = np.floor(H[f.flatten().astype(np.uint16)]*2**16-1)
    return e.reshape(f.shape)

def normalize(img):
    lmin = float(img.min())
    lmax = float(img.max())
    return np.floor(img-lmin)/(lmax-lmin) * 2**16-1

def find_contour_count(img):
    contours, hierarchy = cv2.findContours(img.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    return len(contours)


def equalized(fixed):
    """
    Takes an image that has already been scaled and uses opencv adaptive histogram
    equalization. This cases uses 10 as the clip limit and splits the image into 8 rows
    and 8 columns
    :param fixed: image we are working on
    :return: a better looking image
    """
    clahe = cv2.createCLAHE(clipLimit=10.0, tileGridSize=(8, 8))
    fixed = clahe.apply(fixed)
    return fixed


def get_binary_mask(img):
    '''
    img: numpy 8 bit 2 dimension array
    1. blur img
    2. get opencv OTSUs threshold,
    3. open/close with opencv
    '''
    #normed = exposure.adjust_gamma(normed, 2)
    #normed = exposure.adjust_log(normed)
    # get rid of glue and normalize
    thresh1 = np.quantile(img[img > 0], 0.75)
    thresh2 = np.median(img)
    thresh = int(min(thresh1, thresh2))
    #img[img < 20] = 0
    # size of 121 gives smooth outline and also captures almost
    # all the detail
    kernel_size = (21, 21) 
    img = cv2.GaussianBlur(img, kernel_size, 250)
    thresh = 80  # initial value, but OTSU calculates it
    ret, otsu = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    ksize = 100
    kernel = np.ones((ksize, ksize), np.uint8)
    closed_mask = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)

    return closed_mask



def fix_thion(infile, mask, maskfile, logger, rotation, flip, max_width, max_height):
    """
    This method clean all thionin images. Note that the thionin have 3 channels combined into one.
    :param infile: file path of image
    :param mask: binary mask image of the image
    :param maskfile: file path of mask
    :param ROTATED_MASKS: location of rotated masks
    :param logger: logger to keep track of things
    :param rotation: amount of rotation. 1 = rotate by 90degrees
    :param flip: either flip or flop
    :param max_width: width of image
    :param max_height: height of image
    :return: cleaned and rotated image
    """
    try:
        imgfull = io.imread(infile)
    except:
        logger.warning(f'Could not open {infile}')

    img_ch1 = imgfull[:, :, 0]
    img_ch2 = imgfull[:, :, 1]
    img_ch3 = imgfull[:, :, 2]
    fixed1 = cv2.bitwise_and(img_ch1, img_ch1, mask=mask)
    fixed2 = cv2.bitwise_and(img_ch2, img_ch2, mask=mask)
    fixed3 = cv2.bitwise_and(img_ch3, img_ch3, mask=mask)
    del img_ch1
    del img_ch2
    del img_ch3

    if rotation > 0:
        fixed1 = rotate_image(fixed1, infile, rotation)
        fixed2 = rotate_image(fixed2, infile, rotation)
        fixed3 = rotate_image(fixed3, infile, rotation)
        mask = rotate_image(mask, maskfile, rotation)

    if flip == 'flip':
        fixed1 = np.flip(fixed1)
        fixed2 = np.flip(fixed2)
        fixed3 = np.flip(fixed3)
        mask = np.flip(mask)
    if flip == 'flop':
        fixed1 = np.flip(fixed1, axis=1)
        fixed2 = np.flip(fixed2, axis=1)
        fixed3 = np.flip(fixed3, axis=1)
        mask = np.flip(mask, axis=1)

    fixed = np.dstack((fixed1, fixed2, fixed3))
    return fixed
