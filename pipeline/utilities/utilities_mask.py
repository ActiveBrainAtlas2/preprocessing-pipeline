"""Simple methods to help in manipulating images.
"""

import sys
import cv2
import numpy as np

from utilities.utilities_process import read_image, write_image


def rotate_image(img, file: str, rotation: int):
    """Rotate the image by the number of rotation(s)

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


def place_image(img, file: str, max_width, max_height, bgcolor=None):
    """Places the image in a padded one size container with the correct background

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
            print(f'Could not place 2DIM {file} with width:{img.shape[1]}, height:{img.shape[0]} in {max_width}x{max_height} - rotate image?')
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


def scaled(img, mask, epsilon=0.01):
    """This scales the image to the limit specified. You can get this value
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
    """Takes an image that has already been scaled and uses opencv adaptive histogram
    equalization. This cases uses 10 as the clip limit and splits the image into 8 rows
    and 8 columns

    :param fixed: image we are working on
    :return: a better looking image
    """
    
    clahe = cv2.createCLAHE(clipLimit=10.0, tileGridSize=(8, 8))
    fixed = clahe.apply(fixed)
    return fixed


def merge_mask(image, mask):
    """Merge image with mask [so user can edit]
    stack 3 channels on single image (black background, image, then mask)

    :param image: numpy array of the image
    :param mask: numpy array of the mask
    :return: merged numpy array
    """

    b = mask
    g = image
    r = np.zeros_like(image).astype(np.uint8)
    merged = np.stack([r, g, b], axis=2)
    return merged


def combine_dims(a):
    """Combines dimensions of a numpy array

    :param a: numpy array
    :return: numpy array
    """
    
    if a.shape[0] > 0:
        a1 = a[0,:,:]
        a2 = a[1,:,:]
        a3 = np.add(a1,a2)
    else:
        a3 = np.zeros([a.shape[1], a.shape[2]]) + 255
    return a3


def clean_and_rotate_image(file_key):
    """The main function that uses the user edited mask to crop out the tissue from 
    surrounding debris. It also rotates the image to
    a usual orientation (where the olfactory bulb is facing left and the cerebellum is facing right.
    The hippocampus is facing up and the brainstem is facing down)

    :param file_key: is a tuple of the following:

    - infile file path of image to read
    - outpath file path of image to write
    - mask binary mask image of the image
    - rotation number of 90 degree rotations
    - flip either flip or flop
    - max_width width of image
    - max_height height of image
    - scale used in scaling. Gotten from the histogram

    :return: nothing. we write the image to disk
    """

    infile, outpath, maskfile, rotation, flip, max_width, max_height, channel = file_key

    img = read_image(infile)
    mask = read_image(maskfile)
    cleaned = apply_mask(img, mask, infile)
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

    message = f'Error in saving {outpath} with shape {cleaned.shape} img type {cleaned.dtype}'
    write_image(outpath, cleaned, message=message)
        
    return


def apply_mask(img, mask, infile):
    """Apply image mask to image.

    :param img: numpy array of image
    :param mask: numpy array of mask
    :param infile: path to file
    :return: numpy array of cleaned image
    """

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