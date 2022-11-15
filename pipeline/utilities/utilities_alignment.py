import numpy as np
import pandas as pd
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from utilities.utilities_process import SCALING_FACTOR



def create_downsampled_transforms(transforms: dict, downsample: bool) -> dict:
    """Changes the dictionary of transforms to the correct resolution


    :param animal: prep_id of animal we are working on
    :type animal: str
    :param transforms: dictionary of filename:array of transforms
    :type transforms:
    :param downsample: either true for thumbnails, false for full resolution images
    :type downsample: bool
    :return: corrected dictionary of filename: array  of transforms
    :rtype: dict
    """

    if downsample:
        transforms_scale_factor = 1
    else:
        transforms_scale_factor = SCALING_FACTOR

    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])

    transforms_to_anchor = {}
    for img_name, tf in transforms.items():
        transforms_to_anchor[img_name] = \
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor)
    return transforms_to_anchor


def convert_2d_transform_forms(arr):
    """Helper method used by create_downsampled_transforms

    :param arr: an array of data to vertically stack
    :return: a numpy array
    """

    return np.vstack([arr, [0, 0, 1]])


def align_image_to_affine(file_key):
    """This is the method that takes the rigid transformation and uses
    PIL to align the image.
    This method takes about 20 seconds to run as compared to scikit's version 
    which takes 220 seconds to run on a full scale image.

    :param file_key: tuple of file input and output
    :return: nothing
    """
    _, infile, outfile, T = file_key
    im1 = Image.open(infile)
    im2 = im1.transform((im1.size), Image.AFFINE, T.flatten()[:6], resample=Image.NEAREST)
    im2.save(outfile)
    del im1, im2
    return



