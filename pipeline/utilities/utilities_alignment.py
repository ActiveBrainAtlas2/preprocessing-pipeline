import numpy as np
import pandas as pd
from skimage import io
from PIL import Image
import cv2
from timeit import default_timer as timer
from scipy.ndimage import affine_transform
from utilities.utilities_process import SCALING_FACTOR

# MOVE 'LOOKUP'/CONSTANT VARIABLES TO ENV VARIABLES? (10-NOV-2022 COMMENT)
Image.MAX_IMAGE_PIXELS = None


def create_downsampled_transforms(animal: str, transforms: dict, downsample: bool) -> dict:
    '''Changes the dictionary of transforms to the correct resolution

    REMOVE animal ARGUMENT; NOT USED (10-NOV-2022 COMMENT)

    :param animal: prep_id of animal we are working on
    :type animal: str
    :param transforms: dictionary of filename:array of transforms
    :type transforms:
    :param downsample: either true for thumbnails, false for full resolution images
    :type downsample: bool
    :return: corrected dictionary of filename: array  of transforms
    :rtype: dict
    '''
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
    '''Unknown - converts a 2D tranform? Needs more info

    :param arr:
    :type arr:
    :return:
    :rtype:
    '''
    return np.vstack([arr, [0, 0, 1]])

def dict_to_csv(d: dict, fp: str):
    '''Unknown - converts a dictionary to csv and stores in filepath 'fp'? Needs more info

    :param d:
    :type d: dict
    :param fp:
    :type fp: str
    :return:
    :rtype:
    '''
    df = pd.DataFrame.from_dict({k: np.array(v).flatten() for k, v in d.items()}, orient='index')
    df.to_csv(fp, header=False)


def csv_to_dict(fp: str) -> dict:
    '''Unknown - loads data from csv filepath 'fp' into dictionary? Needs more info

    First column contains keys.

    :param fp:
    :type fp: str
    :return:
    :rtype: dict
    '''
    df = pd.read_csv(fp, index_col=0, header=None)
    d = df.to_dict(orient='index')
    d = {k: v.values() for k, v in d.items()}
    return d




def align_image_to_affine(file_key):
    '''Unknown - image stack alignment using affine transformations? Needs more info

    This method takes about 20 seconds to run. use this one

    :param file_key:
    :type file_key:
    :return:
    :rtype:
    '''
    _, infile, outfile, T = file_key
    im1 = Image.open(infile)
    im2 = im1.transform((im1.size), Image.AFFINE, T.flatten()[:6], resample=Image.NEAREST)
    im2.save(outfile)
    del im1, im2
    return


def align_image_to_affineXXX(file_key):
    '''Unknown - image stack alignment using affine transformations? Needs more info

    This method takes about 220 seconds to complete

    # REMOVE FUNCTION IF REDUNDANT (AND SLOWER) COMPARED TO align_image_to_affine() (10-NOV-2022 COMMENT)

    :param file_key:
    :type file_key:
    :return:
    :rtype:
    '''
    _, infile, outfile, T = file_key
    start = timer()
    image = io.imread(infile)
    matrix = T[:2, :2]
    offset = T[:2, 2]
    offset = np.flip(offset)
    image1 = affine_transform(image, matrix.T, offset)
    end = timer()
    print(f'align image with Scikit took {end - start} seconds.')
    cv2.imwrite(outfile, image1)
    del image, image1
    return


def reverse_transform_create_alignment(points, transform):
    '''Unknown - reverses the alignment transformation? Needs more info

    This reverses the transformation process

    :param points:
    :type points:
    :param transform:
    :type transform:
    :return:
    :rtype:
    '''
    c = np.hstack((points, np.ones((points.shape[0], 1))))
    b = transform.copy()[:, 0:2]  # Reverse rotation matrix by doing R^-1 = R^T
    b[2:, 0:2] = -transform[0:2, 2]  # Reverse translation matrix by doing -T
    a = np.matmul(c, b)
    return a

