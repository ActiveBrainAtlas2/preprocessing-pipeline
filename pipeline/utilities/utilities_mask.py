import sys
import cv2
import numpy as np
from lib.pipeline_utilities import convert_size, read_image
import os
from timeit import default_timer as timer

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
    new_img = np.zeros([max_height, max_width]).astype(dt) + bgcolor
    if img.ndim == 2:
        try:
            new_img[startr:endr, startc:endc] = img
        except:
            print(f'Could not place 2DIM {file} with width:{img.shape[1]}, height:{img.shape[0]} in {max_width}x{max_height}')
    if img.ndim == 3:
        try:
            new_img = np.zeros([max_height, max_width, 3]) + bgcolor
            new_img[startr:endr, startc:endc,0] = img[:,:,0]
            new_img[startr:endr, startc:endc,1] = img[:,:,1]
            new_img[startr:endr, startc:endc,2] = img[:,:,2]
        except:
            print(f'Could not place 3DIM {file} with width:{img.shape[1]}, height:{img.shape[0]} in {max_width}x{max_height}')
    del img
    return new_img.astype(dt)

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
    print(f'get bg color for {file}')
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
    print('padding')
    new_img = np.zeros([ max_width,max_height]) + bgcolor
    print('putting image 2d')
    if img.ndim == 2:
        try:
            new_img[startr:endr,startc:endc] = img
        except:
            print('Could not place {} with width:{}, height:{} in {}x{}'
                  .format(file, img.shape[0], img.shape[1], max_width, max_height))
    print('putting image 3d')
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
    often less than 30000 for channel 1.
    One of the reasons this takes so much RAM is a large float64 array is being
    multiplied by another large array. That is WHERE all the RAM is going!!!!!
    The scale is hardcoded to 45000 which was a good value from Yoav
    :param img: image we are working on.
    :param mask: binary mask file
    :param epsilon:
    :param limit: max value we wish to scale to
    :return: scaled image in 16bit format
    """
    scale = 45000
    _max = np.quantile(img[mask > 0], 1 - epsilon) # gets almost the max value of img
    if img.dtype == np.uint8:
        _range = 2 ** 8 - 1 # 8bit
        data_type = np.uint8        
    else:
        _range = 2 ** 16 - 1 # 16bit
        data_type = np.uint16

    scaled = (img * (scale // _max)).astype(data_type) # scale the image from original values to e.g., 30000/10000
    del img
    scaled[scaled > _range] = _range # if values are > 16bit, set to 16bit
    scaled = scaled * (mask > 0) # just work on the non masked values. This is where all the RAM goes!!!!!!!
    del mask
    return scaled

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


def clean_and_rotate_image(file_key):
    """The main function that uses the User edited mask to crop out the tissue from surrounding debre. and rotates the image to
           a usual orientation (where the olfactory bulb is facing left and the cerebellum is facing right.
           The hippocampus is facing up and the brainstem is facing down)
    file_keys is a tuple of the following:
        :param infile: file path of image to read
        :param outpath: file path of image to write
        :param mask: binary mask image of the image
        :param rotation: number of 90 degree rotations
        :param flip: either flip or flop
        :param max_width: width of image
        :param max_height: height of image
        :param scale: used in scaling. Gotten from the histogram
    :return: nothing. we write the image to disk

    Args:
        file_key (list): List of arguments parsed to the cropping algorithm.  includes:
        1. str: path to the tiff file being cropped
        2. str: path to store the cropped tiff image
        3. str: path to the mask file used to crop the image
        4. int: Number of rotations to be applied .  The rotation is user defined and was used to make sure the brain is
                in a usual orientation that makes sense. each rotation is 90 degree
                eg: a rotation of 3 is a 270 degree rotation
        5. int:
    """
    infile, outpath, maskfile, rotation, flip, max_width, max_height, channel = file_key

    img = read_image(infile)
    #print(f"MEM SIZE OF img {infile}: {convert_size(sys.getsizeof(img))}")
    mask = read_image(maskfile)
    #print(f"MEM SIZE OF mask {maskfile}: {convert_size(sys.getsizeof(mask))}")
    cleaned = apply_mask(img, mask, infile)
    #print(f"MEM SIZE OF cleaned: {convert_size(sys.getsizeof(cleaned))}")
    #print(f"TOTAL MEMORY SIZE FOR AGGREGATE (img, mask, cleaned): {convert_size(sys.getsizeof(img)+sys.getsizeof(mask)+sys.getsizeof(cleaned))}")
    del img
    if channel == 1:
        cleaned = scaled(cleaned, mask, epsilon=0.01)
        cleaned = equalized(cleaned)

    # cropped = crop_image(cleaned, mask)
    del mask
    if rotation > 0:
        cleaned = rotate_image(cleaned, infile, rotation)
    if flip == "flip":
        cleaned = np.flip(cleaned)
    if flip == "flop":
        cleaned = np.flip(cleaned, axis=1)
    cleaned = place_image(cleaned, infile, max_width, max_height, 0)

    try:
        cv2.imwrite(outpath, cleaned)
    except Exception as e:
        print(f'Error in saving {outpath} with shape {cleaned.shape} img type {cleaned.dtype}')
        print(f'Error is {e}')
        print("Unexpected error:", sys.exc_info()[0])
        raise
        
    return



def crop_image(cleaned, mask):
    BUFFER = 2
    mask = np.array(mask)
    mask[mask > 0] = 255
    ret, thresh = cv2.threshold(mask, 200, 255, 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    areas = [cv2.contourArea(contour) for contour in contours]
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if area > 100:
            xmin = int(round(x))
            ymin = int(round(y))
            xmax = int(round(x + w))
            ymax = int(round(y + h))
            boxes.append([xmin, ymin, xmax, ymax])
    x1 = min(x[0] for x in boxes) - BUFFER
    y1 = min(x[1] for x in boxes) - BUFFER
    x2 = max(x[2] for x in boxes) + BUFFER
    y2 = max(x[3] for x in boxes) + BUFFER
    box = np.array([x1, y1, x2, y2])
    box[box < 0] = 0
    x1, y1, x2, y2 = box
    cleaned = np.ascontiguousarray(cleaned, dtype=np.uint16)
    cropped = cleaned[y1:y2, x1:x2]
    return cropped


def apply_mask(img, mask, infile):
    try:
        cleaned = cv2.bitwise_and(img, img, mask=mask)
    except:
        print(
            f"Error in masking {infile} with mask shape {mask.shape} img shape {img.shape}"
        )
        print("Are the shapes exactly the same?")
        print("Unexpected error:", sys.exc_info()[0])
        raise
    return cleaned



def process_image(n, queue, uuid):
    my_pid = os.getpid()
    queue.put((uuid, my_pid))
    file_key = ['/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK78/preps/CH1/full/194.tif', '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK78/preps/CH1/full_cleaned/194.tif', '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK78/preps/full_masked/194.tif', 3, 'none', 30000, 60000, 1]
    infile, outpath, maskfile, rotation, flip, max_width, max_height, channel = file_key
    print("load image")
    img = read_image(infile)
    print("load mask")
    mask = read_image(maskfile)
    print("apply mask")
    cleaned = apply_mask(img, mask, infile)
    print("scale")
    cleaned = scaled(cleaned, mask, epsilon=0.01)
    print("equalize")
    cleaned = equalized(cleaned)
    del img
    del mask
    print("image and masks deleted")
    print("rotate")
    cleaned = rotate_image(cleaned, infile, rotation)
    print("flip")
    cleaned = np.flip(cleaned)
    print("pad")
    cropped = pad_image(cleaned, infile, max_width, max_height, 0)
    del cropped
    print("cropped deleted")