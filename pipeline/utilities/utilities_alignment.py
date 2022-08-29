import os, sys
import numpy as np
import pandas as pd
from skimage import io
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import pickle
import re
from timeit import default_timer as timer

from Controllers.SqlController import SqlController
from lib.FileLocationManager import FileLocationManager
import cv2
from scipy.ndimage import affine_transform
def load_transforms(stack, downsample_factor=None, resolution=None, use_inverse=True, anchor_filepath=None):
    """
    Args:
        use_inverse (bool): If True, load the 2-d rigid transforms that when multiplied
                            to a point on original space converts it to on aligned space.
                            In preprocessing, set to False, which means simply parse the transform files as they are.
        downsample_factor (float): the downsample factor of images that the output transform will be applied to.
        resolution (str): resolution of the image that the output transform will be applied to.
    """
    sqlController = SqlController(stack)
    planar_resolution = sqlController.scan_run.resolution
    string_to_voxel_size = convert_resolution_string_to_um(stack, resolution)

    if resolution is None:
        assert downsample_factor is not None
        resolution = 'down%d' % downsample_factor

    fp = get_transforms_filename(stack, anchor_filepath=anchor_filepath)
    Ts_down32 = load_data(fp)
    if isinstance(Ts_down32.values()[0], list): 
        Ts_down32 = {k: np.reshape(v, (3,3)) for k, v in Ts_down32.items()}

    if use_inverse:
        Ts_inv_rescaled = {}
        for fn, T_down32 in sorted(Ts_down32.items()):
            T_rescaled = T_down32.copy()
            T_rescaled[:2, 2] = T_down32[:2, 2] * 32. * planar_resolution / string_to_voxel_size
            T_rescaled_inv = np.linalg.inv(T_rescaled)
            Ts_inv_rescaled[fn] = T_rescaled_inv
        return Ts_inv_rescaled
    else:
        Ts_rescaled = {}
        for fn, T_down32 in sorted(Ts_down32.items()):
            T_rescaled = T_down32.copy()
            T_rescaled[:2, 2] = T_down32[:2, 2] * 32. * planar_resolution / string_to_voxel_size
            Ts_rescaled[fn] = T_rescaled

        return Ts_rescaled


def get_transforms_filename(stack, anchor_filepath=None):
    fileLocationManager = FileLocationManager(stack)
    fp = os.path.join(fileLocationManager.brain_info, 'transforms_to_anchor.csv')
    return fp

def load_data(filepath, filetype=None):

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
            xdim_m, ydim_m, zdim_m  = one_liner_to_arr(lines[2], int)
            centroid_f = one_liner_to_arr(lines[3], float)
            xdim_f, ydim_f, zdim_f  = one_liner_to_arr(lines[4], int)

        return global_params, centroid_m, centroid_f, xdim_m, ydim_m, zdim_m, xdim_f, ydim_f, zdim_f
    else:
        sys.stderr.write('File type %s not recognized.\n' % filetype)


def load_hdf(fn, key='data'):
    """
    Used by loading features.
    """
    """
    with tables.open_file(fn, mode="r") as f:
        data = f.get_node('/'+key).read()
    return data
    """


def one_liner_to_arr(line, func):
    return np.array(list(map(func, line.strip().split())))


def load_consecutive_section_transform(animal, moving_filepath, fixed_filepath):
    """
    Load pairwise transform.

    Returns:
        (3,3)-array.
    """
    assert animal is not None
    fileLocationManager = FileLocationManager(animal)
    ELASTIX_DIR = fileLocationManager.elastix_dir
    param_file = os.path.join(ELASTIX_DIR, moving_filepath + '_to_' + fixed_filepath, 'TransformParameters.0.txt')
    if not os.path.exists(param_file):
        raise Exception('Transform file does not exist: %s to %s, %s' % (moving_filepath, fixed_filepath, param_file))
    return parse_elastix_parameter_file(param_file)

def load_transforms_of_prepi(prepi):
    path = FileLocationManager(prepi)
    transform_files = os.listdir(path.elastix_dir)
    transforms = {}
    for filei in transform_files:
        file_path = os.path.join(path.elastix_dir,filei,'TransformParameters.0.txt')
        section = int(filei.split('_')[0])
        transforms[section] = parse_elastix_parameter_file(file_path)
    return transforms

def parse_elastix_parameter_file(filepath):
    """
    Parse elastix parameter result file.
    """

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


def parameter_elastix_parameter_file_to_dict(filename):
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



def create_downsampled_transforms(animal, transforms, downsample):
    """
    Changes the dictionary of transforms to the correct resolution
    :param animal: prep_id of animal we are working on
    :param transforms: dictionary of filename:array of transforms
    :param transforms_resol:
    :param downsample; either true for thumbnails, false for full resolution images
    :return: corrected dictionary of filename: array  of transforms
    """

    if downsample:
        transforms_scale_factor = 1
    else:
        transforms_scale_factor = 32

    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])

    transforms_to_anchor = {}
    for img_name, tf in transforms.items():
        transforms_to_anchor[img_name] = \
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor) 
    return transforms_to_anchor

def convert_2d_transform_forms(arr):
    return np.vstack([arr, [0, 0, 1]])


def convert_resolution_string_to_um(animal, downsample):
    """
    Thionin brains are ususally 0.452 and NtB are usually 0.325
    Args:
        resolution (str):
    Returns:
        voxel/pixel size in micrometers.
    """
    try:
        sqlController = SqlController(animal)
        planar_resolution = sqlController.scan_run.resolution
    except:
        planar_resolution = 0.325

    if downsample:
        return planar_resolution * 32.
    else:
        return planar_resolution


def transform_points(points, transform):
    a = np.hstack((points, np.ones((points.shape[0], 1))))
    b = transform.T[:, 0:2]
    c = np.matmul(a, b)
    return c


def dict_to_csv(d, fp):
    df = pd.DataFrame.from_dict({k: np.array(v).flatten() for k, v in d.items()}, orient='index')
    df.to_csv(fp, header=False)


def csv_to_dict(fp):
    """
    First column contains keys.
    """
    df = pd.read_csv(fp, index_col=0, header=None)
    d = df.to_dict(orient='index')
    d = {k: v.values() for k, v in d.items()}
    return d


def convert_2d_transform_formsXXX(transform, out_form):
    if isinstance(transform, str):
        if out_form == (2,3):
            return np.reshape(list(map(np.float, transform.split(','))), (2, 3))
        elif out_form == (3,3):
            return np.vstack([np.reshape(list(map(np.float, transform.split(','))), (2, 3)), [0, 0, 1]])
    else:
        transform = np.array(transform)
        if transform.shape == (2,3):
            if out_form == (3,3):
                transform = np.vstack([transform, [0,0,1]])
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))
        elif transform.shape == (3,3):
            if out_form == (2,3):
                transform = transform[:2]
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))

    return transform


def convert_cropbox_from_arr_xywh_1um(data, out_fmt, out_resol, stack):
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
        return np.array([data[0], data[0]+data[2]-1, data[1], data[1]+data[3]-1])
    else:
        raise

def convert_cropbox_to_arr_xywh_1um(data, in_fmt, in_resol, stack):
    sqlController = SqlController(stack)
    if isinstance(data, dict):
        data['rostral_limit'] = float(data['rostral_limit'])
        data['caudal_limit'] = float(data['caudal_limit'])
        data['dorsal_limit'] = float(data['dorsal_limit'])
        data['ventral_limit'] = float(data['ventral_limit'])
        arr_xywh = np.array([data['rostral_limit'], data['dorsal_limit'], data['caudal_limit'] - data['rostral_limit'] + 1, data['ventral_limit'] - data['dorsal_limit'] + 1])
    elif isinstance(data, str):
        if in_fmt == 'str_xywh':
            d = re.sub('[!@#$cropwarp\]\[\']', '', data)
            l = d.split(',')
            a = [float(v) for v in l]
            arr_xywh = np.array(a)
        elif in_fmt == 'str_xxyy':
            arr_xxyy = np.array(list(map(np.round, list(map(eval, data.split(','))))))
            arr_xywh = np.array([arr_xxyy[0], arr_xxyy[2], arr_xxyy[1] - arr_xxyy[0] + 1, arr_xxyy[3] - arr_xxyy[2] + 1])
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


def convert_cropbox_fmt(out_fmt, data, in_fmt=None, in_resol='1um', out_resol='1um', stack=None):
    if in_resol == out_resol: 
        in_resol = '1um'
        out_resol = '1um'
    arr_xywh_1um = convert_cropbox_to_arr_xywh_1um(data=data, in_fmt=in_fmt, in_resol=in_resol, stack=stack)
    data_out = convert_cropbox_from_arr_xywh_1um(data=arr_xywh_1um, out_fmt=out_fmt, out_resol=out_resol, stack=stack)
    print('data out', data_out)
    return data_out


orientation_argparse_str_to_imagemagick_str =     {'transpose': '-transpose',
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


def align_image_to_affine(file_key):
    """This method takes about 20 seconds to run. use this one
    """
    _, infile, outfile, T = file_key
    im1 = Image.open(infile)
    im2 = im1.transform((im1.size), Image.AFFINE, T.flatten()[:6], resample=Image.NEAREST)
    im2.save(outfile)
    del im1, im2
    return

def align_image_to_affineXXX(file_key):
    """This method takes about 220 seconds to complete
    """
    _, infile, outfile, T = file_key
    start = timer()
    image = io.imread(infile)
    matrix = T[:2,:2]
    offset = T[:2,2]
    offset = np.flip(offset)
    image1 = affine_transform(image,matrix.T,offset)
    end = timer()
    print(f'align image with Scikit took {end - start} seconds.')    
    cv2.imwrite(outfile, image1)
    del image,image1
    return


def reverse_transform_create_alignment(points, transform):
    """
    This reverses the transformation process
    """
    c = np.hstack((points, np.ones((points.shape[0], 1))))
    b = transform.copy()[:, 0:2] # Reverse rotation matrix by doing R^-1 = R^T
    b[2:, 0:2] = -transform[0:2, 2] # Reverse translation matrix by doing -T
    a = np.matmul(c, b)
    return a

def transform_points(points, transform):
    a = np.hstack((points, np.ones((points.shape[0], 1))))
    b = transform.T[:, 0:2]
    c = np.matmul(a, b)
    return c
