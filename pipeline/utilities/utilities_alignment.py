import os, sys
import numpy as np
import pandas as pd
from skimage import io
from PIL import Image
import pickle
import re
import cv2
from timeit import default_timer as timer
from scipy.ndimage import affine_transform
from controller.sql_controller import SqlController
from lib.FileLocationManager import FileLocationManager
from utilities.utilities_process import SCALING_FACTOR

# MOVE 'LOOKUP'/CONSTANT VARIABLES TO ENV VARIABLES? (10-NOV-2022 COMMENT)
Image.MAX_IMAGE_PIXELS = None
orientation_argparse_str_to_imagemagick_str = {'transpose': '-transpose',
                                               'transverse': '-transverse',
                                               'rotate90': '-rotate 90',
                                               'rotate180': '-rotate 180',
                                               'rotate270': '-rotate 270',
                                               'rotate45': '-rotate 45',
                                               'rotate135': '-rotate 135',
                                               'rotate225': '-rotate 225',
                                               'rotate315': '-rotate 315',
                                               'flip': '-flip',
                                               'flop': '-flop'
                                               }


def load_transforms(stack, downsample_factor: float = None, resolution: str = None, use_inverse: bool = True,
                    anchor_filepath=None):
    '''Unknown - loads tranforms? Needs more info

    :param stack:
    :type stack:
    :param downsample_factor: the downsample factor of images that the output transform will be applied to.
    :type downsample_factor: float
    :param resolution: resolution of the image that the output transform will be applied to.
    :type resolution: str
    :param use_inverse: If True, load the 2-d rigid transforms that when multiplied
                        to a point on original space converts it to on aligned space.
                        In preprocessing, set to False, which means simply parse the transform files as they are.
    :type use_inverse: bool
    :param anchor_filepath:
    :type anchor_filepath:
    :return:
    :rtype:
    '''

    sqlController = SqlController(stack)
    planar_resolution = sqlController.scan_run.resolution
    string_to_voxel_size = convert_resolution_string_to_um(stack, resolution)

    if resolution is None:
        assert downsample_factor is not None
        resolution = 'down%d' % downsample_factor

    fp = get_transforms_filename(stack, anchor_filepath=anchor_filepath)
    Ts_downsampled = load_data(fp)
    if isinstance(Ts_downsampled.values()[0], list):
        Ts_downsampled = {k: np.reshape(v, (3, 3)) for k, v in Ts_downsampled.items()}

    if use_inverse:
        Ts_inv_rescaled = {}
        for fn, T_downsampled in sorted(Ts_downsampled.items()):
            T_rescaled = T_downsampled.copy()
            T_rescaled[:2, 2] = T_downsampled[:2, 2] * SCALING_FACTOR * planar_resolution / string_to_voxel_size
            T_rescaled_inv = np.linalg.inv(T_rescaled)
            Ts_inv_rescaled[fn] = T_rescaled_inv
        return Ts_inv_rescaled
    else:
        Ts_rescaled = {}
        for fn, T_downsampled in sorted(Ts_downsampled.items()):
            T_rescaled = T_downsampled.copy()
            T_rescaled[:2, 2] = T_downsampled[:2, 2] * SCALING_FACTOR * planar_resolution / string_to_voxel_size
            Ts_rescaled[fn] = T_rescaled

        return Ts_rescaled


def get_transforms_filename(stack: str, anchor_filepath=None) -> str:
    '''Accepts generic filepath, appends filename for storage of transforms data and return resultant complete/absolute filepath

    MOVE TO lib.FileocationManager CLASS (10-NOV-2022 COMMENT)

    :param stack:
    :type stack: str
    :param anchor_filepath:
    :type anchor_filepath:
    :rtype: str
    '''
    fileLocationManager = FileLocationManager(stack)
    fp = os.path.join(fileLocationManager.brain_info, 'transforms_to_anchor.csv')
    return fp


def load_data(filepath: str, filetype: str = None):
    '''Unknown - loads data? Needs more info

    :param filepath:
    :type filepath: str
    :param filetype:
    :type filetype: str
    :return:
    :rtype:
    '''
    if not os.path.exists(filepath):
        sys.stderr.write('File does not exist: %s\n' % filepath)

    if filetype == 'npy':
        return np.load(filepath)
    elif filetype == 'image':
        return io.imread(filepath)
    elif filetype == 'hdf':
        return load_hdf(filepath)
    elif filetype == 'bbox':
        return np.loadtxt(filepath).astype(np.int)
    elif filetype == 'annotation_hdf':
        contour_df = pd.read_hdf(filepath, 'contours')
        return contour_df
    elif filetype == 'pickle':
        return pickle.load(open(filepath, 'r'))
    elif filetype == 'file_section_map':
        with open(filepath, 'r') as f:
            fn_idx_tuples = [line.strip().split() for line in f.readlines()]
            filename_to_section = {fn: int(idx) for fn, idx in fn_idx_tuples}
            section_to_filename = {int(idx): fn for fn, idx in fn_idx_tuples}
        return filename_to_section, section_to_filename
    elif filetype == 'label_name_map':
        label_to_name = {}
        name_to_label = {}
        with open(filepath, 'r') as f:
            for line in f.readlines():
                name_s, label = line.split()
                label_to_name[int(label)] = name_s
                name_to_label[name_s] = int(label)
        return label_to_name, name_to_label
    elif filetype == 'anchor':
        with open(filepath, 'r') as f:
            anchor_filepath = f.readline().strip()
        return anchor_filepath
    elif filetype == 'transform_params':
        with open(filepath, 'r') as f:
            lines = f.readlines()

            global_params = one_liner_to_arr(lines[0], float)
            centroid_m = one_liner_to_arr(lines[1], float)
            xdim_m, ydim_m, zdim_m = one_liner_to_arr(lines[2], int)
            centroid_f = one_liner_to_arr(lines[3], float)
            xdim_f, ydim_f, zdim_f = one_liner_to_arr(lines[4], int)

        return global_params, centroid_m, centroid_f, xdim_m, ydim_m, zdim_m, xdim_f, ydim_f, zdim_f
    else:
        sys.stderr.write('File type %s not recognized.\n' % filetype)


def load_hdf(fn, key='data'):
    '''Unknown - loads_hdf? Needs more info

    prior comment: Used by loading features.
    DELETE AS EVERYTHING IN FUNCTION IS COMMENTED OUT (10-NOV-2022 COMMENT)

    :param fn:
    :type fn:
    :param key:
    :type key:
    :return:
    :rtype:
    '''

    """
    with tables.open_file(fn, mode="r") as f:
        data = f.get_node('/'+key).read()
    return data
    """


def one_liner_to_arr(line, func):
    '''Unknown - one_liner_to_arr? Needs more info

    :param line:
    :type line:
    :param func:
    :type func:
    :return:
    :rtype:
    '''
    return np.array(list(map(func, line.strip().split())))


def load_consecutive_section_transform(animal: str, moving_filepath: str, fixed_filepath: str):
    '''Load pairwise transform

    :param animal:
    :type animal: str
    :param moving_filepath:
    :type moving_filepath: str
    :param fixed_filepath:
    :type fixed_filepath: str
    :return: (3,3)-array
    :rtype:
    '''
    assert animal is not None
    fileLocationManager = FileLocationManager(animal)
    ELASTIX_DIR = fileLocationManager.elastix_dir
    param_file = os.path.join(ELASTIX_DIR, moving_filepath + '_to_' + fixed_filepath, 'TransformParameters.0.txt')
    if not os.path.exists(param_file):
        raise Exception('Transform file does not exist: %s to %s, %s' % (moving_filepath, fixed_filepath, param_file))
    return parse_elastix_parameter_file(param_file)


def load_transforms_of_prepi(prepi: str):
    '''Unknown - load_transforms_of_prepi? Needs more info

    :param prepi:
    :type prepi: str
    :return:
    :rtype:
    '''
    path = FileLocationManager(prepi)
    transform_files = os.listdir(path.elastix_dir)
    transforms = {}
    for filei in transform_files:
        file_path = os.path.join(path.elastix_dir, filei, 'TransformParameters.0.txt')
        section = int(filei.split('_')[0])
        transforms[section] = parse_elastix_parameter_file(file_path)
    return transforms


def parse_elastix_parameter_file(filepath: str):
    '''Parse elastix parameter result file.

    :param filepath:
    :type filepath: str
    :return:
    :rtype:
    '''
    d = parameter_elastix_parameter_file_to_dict(filepath)
    rot_rad, x_mm, y_mm = d['TransformParameters']
    center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])

    xshift = x_mm / d['Spacing'][0]
    yshift = y_mm / d['Spacing'][1]

    R = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                  [np.sin(rot_rad), np.cos(rot_rad)]])
    shift = center + (xshift, yshift) - np.dot(R, center)
    T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
    return T


def parameter_elastix_parameter_file_to_dict(filename: str) -> dict:
    '''Unknown - parses elastix parameter file and returns dictionary? Needs more info

    :param filename:
    :type filename: str
    :return:
    :rtype: dict
    '''
    d = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            if line.startswith('('):
                tokens = line[1:-2].split(' ')
                key = tokens[0]
                if len(tokens) > 2:
                    value = []
                    for v in tokens[1:]:
                        try:
                            value.append(float(v))
                        except ValueError:
                            value.append(v)
                else:
                    v = tokens[1]
                    try:
                        value = (float(v))
                    except ValueError:
                        value = v
                d[key] = value
        return d


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


def convert_resolution_string_to_um(animal: str, downsample) -> float:
    '''Unknown - converts a resolution string to micrometers? Needs more info

    Thionin brains are ususally 0.452 and NtB are usually 0.325

    :param animal:
    :type animal: str
    :param downsample:
    :type downsample:
    :return: voxel/pixel size in micrometers.
    :rtype: float
    '''
    try:
        sqlController = SqlController(animal)
        planar_resolution = sqlController.scan_run.resolution
    except:
        planar_resolution = 0.325

    if downsample:
        return planar_resolution * SCALING_FACTOR
    else:
        return planar_resolution


def transform_points(points, transform):
    '''Unknown - points transformation? Needs more info

    :param points:
    :type points:
    :param transform:
    :type transform:
    :return:
    :rtype:
    '''
    a = np.hstack((points, np.ones((points.shape[0], 1))))
    b = transform.T[:, 0:2]
    c = np.matmul(a, b)
    return c


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


def convert_2d_transform_formsXXX(transform: str, out_form):
    '''Unknown - convert 2D transforms? Needs more info

    :param transform:
    :type transform: str
    :param out_form:
    :type out_form:
    :return:
    :rtype:
    '''
    if isinstance(transform, str):
        if out_form == (2, 3):
            return np.reshape(list(map(np.float, transform.split(','))), (2, 3))
        elif out_form == (3, 3):
            return np.vstack([np.reshape(list(map(np.float, transform.split(','))), (2, 3)), [0, 0, 1]])
    else:
        transform = np.array(transform)
        if transform.shape == (2, 3):
            if out_form == (3, 3):
                transform = np.vstack([transform, [0, 0, 1]])
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))
        elif transform.shape == (3, 3):
            if out_form == (2, 3):
                transform = transform[:2]
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))
    return transform


def convert_cropbox_from_arr_xywh_1um(data, out_fmt: str, out_resol: float, stack):
    '''Unknown - converts cropbox from array to something in micrometers? Needs more info

    :param data:
    :type data:
    :param out_fmt:
    :type out_fmt: str
    :param out_resol:
    :type out_resol: float
    :param stack:
    :type stack:
    :return:
    :rtype:
    '''
    sqlController = SqlController(stack)
    string_to_um_out_resolution = sqlController.convert_resolution_string_to_um(stack, out_resol)

    data = data / string_to_um_out_resolution
    if out_fmt == 'str_xywh':
        return ','.join(map(str, data))
    elif out_fmt == 'dict':
        raise Exception("too lazy to implement")
    elif out_fmt == 'arr_xywh':
        return data
    elif out_fmt == 'arr_xxyy':
        return np.array([data[0], data[0] + data[2] - 1, data[1], data[1] + data[3] - 1])
    else:
        raise


def convert_cropbox_to_arr_xywh_1um(data, in_fmt: str, in_resol, stack):
    '''Unknown - converts cropbox to array from something in micrometers? Needs more info

    :param data:
    :type data:
    :param in_fmt:
    :type in_fmt: str
    :param in_resol:
    :type in_resol:
    :param stack:
    :type stack:
    :return:
    :rtype:
    '''
    sqlController = SqlController(stack)
    if isinstance(data, dict):
        data['rostral_limit'] = float(data['rostral_limit'])
        data['caudal_limit'] = float(data['caudal_limit'])
        data['dorsal_limit'] = float(data['dorsal_limit'])
        data['ventral_limit'] = float(data['ventral_limit'])
        arr_xywh = np.array(
            [data['rostral_limit'], data['dorsal_limit'], data['caudal_limit'] - data['rostral_limit'] + 1,
             data['ventral_limit'] - data['dorsal_limit'] + 1])
    elif isinstance(data, str):
        if in_fmt == 'str_xywh':
            d = re.sub('[!@#$cropwarp\]\[\']', '', data)
            l = d.split(',')
            a = [float(v) for v in l]
            arr_xywh = np.array(a)
        elif in_fmt == 'str_xxyy':
            arr_xxyy = np.array(list(map(np.round, list(map(eval, data.split(','))))))
            arr_xywh = np.array(
                [arr_xxyy[0], arr_xxyy[2], arr_xxyy[1] - arr_xxyy[0] + 1, arr_xxyy[3] - arr_xxyy[2] + 1])
        else:
            raise
    else:
        if in_fmt == 'arr_xywh':
            arr_xywh = data
        elif in_fmt == 'arr_xxyy':
            arr_xywh = np.array([data[0], data[2], data[1] - data[0] + 1, data[3] - data[2] + 1])
        else:
            print(in_fmt, data)
            raise

    string_to_um_in_resolution = sqlController.convert_resolution_string_to_um(stack, in_resol)
    arr_xywh_1um = arr_xywh * string_to_um_in_resolution
    print('arr_xywh_1um', arr_xywh_1um)
    return arr_xywh_1um


def convert_cropbox_fmt(out_fmt, data, in_fmt=None, in_resol: str='1um', out_resol: str='1um', stack=None):
    '''Unknown - converts cropbox format? Needs more info

    :param out_fmt:
    :type out_fmt:
    :param data:
    :type data:
    :param in_fmt:
    :type in_fmt: str
    :param in_resol:
    :type in_resol:
    :param out_resol:
    :type out_resol: str
    :param stack:
    :type stack:
    :return:
    :rtype:
    '''
    if in_resol == out_resol:
        in_resol = '1um'
        out_resol = '1um'
    arr_xywh_1um = convert_cropbox_to_arr_xywh_1um(data=data, in_fmt=in_fmt, in_resol=in_resol, stack=stack)
    data_out = convert_cropbox_from_arr_xywh_1um(data=arr_xywh_1um, out_fmt=out_fmt, out_resol=out_resol, stack=stack)
    print('data out', data_out)
    return data_out


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


def transform_points(points, transform):
    '''Unknown - alignment transformation? Needs more info

    :param points:
    :type points:
    :param transform:
    :type transform:
    :return:
    :rtype:
    '''
    a = np.hstack((points, np.ones((points.shape[0], 1))))
    b = transform.T[:, 0:2]
    c = np.matmul(a, b)
    return c
