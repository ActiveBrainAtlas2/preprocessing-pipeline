import cv2
import numpy as np

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

def pad_image(img, file, max_width, max_height, bgcolor=None):
    """
    Places the image in a padded one size container with the correct background
    :param img: image we are working on.
    :param file: file name and path location
    :param max_width: width to pad
    :param max_height: height to pad
    :param bgcolor: background color of image, 0 for NTB, white for thionin
    :return: placed image centered in the correct size.
    """
    half_max_width = max_width // 2
    half_max_height = max_height // 2
    startr = half_max_width - (img.shape[0] // 2)
    endr = startr + img.shape[0]
    startc = half_max_height - (img.shape[1] // 2)
    endc = startc + img.shape[1]
    dt = img.dtype
    if bgcolor == None:
        start_bottom = img.shape[0] - 5
        bottom_rows = img[start_bottom:img.shape[0], :]
        avg = np.mean(bottom_rows)
        bgcolor = int(round(avg))
    new_img = np.zeros([ max_width,max_height]) + bgcolor
    if img.ndim == 2:
        try:
            new_img[startr:endr,startc:endc] = img
        except:
            print('Could not place {} with width:{}, height:{} in {}x{}'
                  .format(file, img.shape[0], img.shape[1], max_width, max_height))
    if img.ndim == 3:
        try:
            new_img = np.zeros([max_height, max_width, 3]) + bgcolor
            new_img[startr:endr, startc:endc,0] = img[:,:,0]
            new_img[startr:endr, startc:endc,1] = img[:,:,1]
            new_img[startr:endr, startc:endc,2] = img[:,:,2]
        except:
            print('Could not place {} with width:{}, height:{} in {}x{}'
                  .format(file, img.shape[0], img.shape[1], max_width, max_height))
    del img
    return new_img.astype(dt)

def scaled(img, mask, epsilon=0.01):
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
    scale = 45000
    _max = np.quantile(img[mask > 10], 1 - epsilon) # gets almost the max value of img
    # print('thr=%d, index=%d'%(vals[ind],index))
    if scale > 255:
        _range = 2 ** 16 - 1 # 16bit
        data_type = np.uint16
    else:
        _range = 2 ** 256 - 1 # 8bit
        data_type = np.uint8        
    scaled = img * (scale / _max) # scale the image from original values to e.g., 30000/10000
    scaled[scaled > _range] = _range # if values are > 16bit, set to 16bit
    scaled = scaled * (mask > 10) # just work on the non masked values
    del img
    return scaled.astype(data_type)

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

def merge_mask(image, mask):
    b = mask
    g = image
    r = np.zeros_like(image).astype(np.uint8)
    merged = np.stack([r, g, b], axis=2)
    return merged

def combine_dims(a):
    if a.shape[0] > 0:
        a1 = a[0,:,:]
        a2 = a[1,:,:]
        a3 = np.add(a1,a2)
    else:
        a3 = np.zeros([a.shape[1], a.shape[2]]) + 255
    return a3