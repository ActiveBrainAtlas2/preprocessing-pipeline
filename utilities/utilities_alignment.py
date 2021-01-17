import os, sys
import numpy as np
import pandas as pd
from skimage import io
import pickle
import re
from six.moves import map
from pathlib import Path

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())

from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager


def load_transforms(stack, downsample_factor=None, resolution=None, use_inverse=True, anchor_fn=None):
    """
    Args:
        use_inverse (bool): If True, load the 2-d rigid transforms that when multiplied
                            to a point on original space converts it to on aligned space.
                            In preprocessing, set to False, which means simply parse the transform files as they are.
        downsample_factor (float): the downsample factor of images that the output transform will be applied to.
        resolution (str): resolution of the image that the output transform will be applied to.
    """
    # set the animal info

    sqlController = SqlController(stack)
    planar_resolution = sqlController.scan_run.resolution
    string_to_voxel_size = convert_resolution_string_to_um(stack, resolution)

    if resolution is None:
        assert downsample_factor is not None
        resolution = 'down%d' % downsample_factor

    fp = get_transforms_filename(stack, anchor_fn=anchor_fn)
    # download_from_s3(fp, local_root=THUMBNAIL_DATA_ROOTDIR)
    Ts_down32 = load_data(fp)
    if isinstance(Ts_down32.values()[0], list): # csv, the returned result are dict of lists
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


def get_transforms_filename(stack, anchor_fn=None):
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
            anchor_fn = f.readline().strip()
        return anchor_fn
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
    #####UPGRADE 2 -> 3 return np.array(map(func, line.strip().split()))
    return np.array(list(map(func, line.strip().split())))


def load_consecutive_section_transform(stack, moving_fn, fixed_fn):
    """
    Load pairwise transform.

    Returns:
        (3,3)-array.
    """
    assert stack is not None
    fileLocationManager = FileLocationManager(stack)
    elastix_output_dir = fileLocationManager.elastix_dir
    param_fp = os.path.join(elastix_output_dir, moving_fn + '_to_' + fixed_fn, 'TransformParameters.0.txt')
    #sys.stderr.write('Load elastix-computed transform: %s\n' % param_fp)
    if not os.path.exists(param_fp):
        raise Exception('Transform file does not exist: %s to %s, %s' % (moving_fn, fixed_fn, param_fp))
    transformation_to_previous_sec = parse_elastix_parameter_file(param_fp)

    return transformation_to_previous_sec


def parse_elastix_parameter_file(filepath, tf_type=None):
    """
    Parse elastix parameter result file.
    """

    d = parameter_elastix_parameter_file_to_dict(filepath)


    if tf_type == 'rigid3d':
        p = np.array(d['TransformParameters'])
        center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])
        shift = p[3:] / np.array(d['Spacing'])

        thetax, thetay, thetaz = p[:3]
        # Important to use the negative angle.
        cx = np.cos(-thetax)
        cy = np.cos(-thetay)
        cz = np.cos(-thetaz)
        sx = np.sin(-thetax)
        sy = np.sin(-thetay)
        sz = np.sin(-thetaz)
        Rx = np.array([[1, 0, 0], [0, cx, sx], [0, -sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, sz, 0], [-sz, cz, 0], [0, 0, 1]])

        R = np.dot(np.dot(Rz, Ry), Rx)
        # R = np.dot(np.dot(Rx, Ry), Rz)
        # The order could be Rx,Ry,Rz - not sure.

        return R, shift, center

    elif tf_type == 'affine3d':
        p = np.array(d['TransformParameters'])
        L = p[:9].reshape((3, 3))
        shift = p[9:] / np.array(d['Spacing'])
        center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])
        # shift = center + shift - np.dot(L, center)
        # T = np.column_stack([L, shift])
        return L, shift, center
    elif tf_type is None:
        # For alignment composition script
        rot_rad, x_mm, y_mm = d['TransformParameters']
        center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])
        # center[1] = d['Size'][1] - center[1]

        xshift = x_mm / d['Spacing'][0]
        yshift = y_mm / d['Spacing'][1]

        R = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                      [np.sin(rot_rad), np.cos(rot_rad)]])
        shift = center + (xshift, yshift) - np.dot(R, center)
        T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
        return T
    else:
        print('Nothing to do')


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

def parse_elastix(animal):
    """
    After the elastix job is done, this goes into each subdirectory and parses the Transformation.0.txt file
    Args:
        animal: the animal
    Returns: a dictionary of key=filename, value = coordinates
    """
    fileLocationManager = FileLocationManager(animal)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')

    image_name_list = sorted(os.listdir(INPUT))
    anchor_idx = len(image_name_list) // 2
    # anchor_idx = len(image_name_list) - 1
    transformation_to_previous_sec = {}

    for i in range(1, len(image_name_list)):
        fixed_fn = os.path.splitext(image_name_list[i - 1])[0]
        moving_fn = os.path.splitext(image_name_list[i])[0]
        transformation_to_previous_sec[i] = load_consecutive_section_transform(animal, moving_fn, fixed_fn)

    transformation_to_anchor_sec = {}
    # Converts every transformation
    for moving_idx in range(len(image_name_list)):
        if moving_idx == anchor_idx:
            transformation_to_anchor_sec[image_name_list[moving_idx]] = np.eye(3)
        elif moving_idx < anchor_idx:
            T_composed = np.eye(3)
            for i in range(anchor_idx, moving_idx, -1):
                T_composed = np.dot(np.linalg.inv(transformation_to_previous_sec[i]), T_composed)
            transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed
        else:
            T_composed = np.eye(3)
            for i in range(anchor_idx + 1, moving_idx + 1):
                T_composed = np.dot(transformation_to_previous_sec[i], T_composed)
            transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed

    return transformation_to_anchor_sec


def create_warp_transforms(animal, transforms, transforms_resol, resolution):
    def convert_2d_transform_forms(arr):
        return np.vstack([arr, [0, 0, 1]])

    # transforms_resol = op['resolution']
    transforms_scale_factor = convert_resolution_string_to_um(animal,
                                                              resolution=transforms_resol) / convert_resolution_string_to_um(
        animal, resolution=resolution)
    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])
    transforms_to_anchor = {
        img_name:
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor) for
        img_name, tf in transforms.items()}

    return transforms_to_anchor

def transform_create_alignment(points, transform):
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


def convert_2d_transform_forms(transform, out_form):
    if isinstance(transform, str):
        if out_form == (2,3):
            #return np.reshape(map(np.float, transform.split(',')), (2,3))
            return np.reshape(list(map(np.float, transform.split(','))), (2, 3))
        elif out_form == (3,3):
            #return np.vstack([np.reshape(map(np.float, transform.split(',')), (2,3)), [0,0,1]])
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

##### cropbox methods

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
    #print('data', data, 'in_fmt', in_fmt)
    sqlController = SqlController(stack)
    if isinstance(data, dict):
        data['rostral_limit'] = float(data['rostral_limit'])
        data['caudal_limit'] = float(data['caudal_limit'])
        data['dorsal_limit'] = float(data['dorsal_limit'])
        data['ventral_limit'] = float(data['ventral_limit'])
        arr_xywh = np.array([data['rostral_limit'], data['dorsal_limit'], data['caudal_limit'] - data['rostral_limit'] + 1, data['ventral_limit'] - data['dorsal_limit'] + 1])
        # Since this does not check for wrt, the user needs to make sure the cropbox is relative to the input prep (i.e. the wrt attribute is the same as input prep)
    elif isinstance(data, str):
        if in_fmt == 'str_xywh':
            d = re.sub('[!@#$cropwarp\]\[\']', '', data)
            l = d.split(',')
            a = [float(v) for v in l]
            arr_xywh = np.array(a)
        elif in_fmt == 'str_xxyy':
            #####UPGRADE from 2 to 3arr_xxyy = np.array(map(np.round, map(eval, data.split(','))))
            arr_xxyy = np.array(list(map(np.round, list(map(eval, data.split(','))))))
            arr_xywh = np.array([arr_xxyy[0], arr_xxyy[2], arr_xxyy[1] - arr_xxyy[0] + 1, arr_xxyy[3] - arr_xxyy[2] + 1])
        else:
            raise
    else:
        if in_fmt == 'arr_xywh':
            arr_xywh = data
            #arr_xywh = np.array(data)
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
    if in_resol == out_resol: # in this case, stack is not required/ Arbitrarily set both to 1um
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


def convert_resolution_string_to_um(stack, resolution):
    """
    Args:
        resolution (str):
    Returns:
        voxel/pixel size in microns.
    """
    try:
        sqlController = SqlController(stack)
        planar_resolution = sqlController.scan_run.resolution
    except:
        planar_resolution = 0.452
    #planar_resolution =  0.452
    assert resolution is not None, 'Resolution argument cannot be None.'

    if resolution in ['down32', 'thumbnail']:
        assert stack is not None
        return planar_resolution * 32.
    elif resolution == 'lossless' or resolution == 'down1' or resolution == 'raw' or resolution == 'full':
        assert stack is not None
        return planar_resolution
    elif resolution.startswith('down'):
        assert stack is not None
        return planar_resolution * int(resolution[4:])
    elif resolution == 'um':
        return 1.
    elif resolution.endswith('um'):
        return float(resolution[:-2])
    else:
        print(resolution)
        raise Exception("Unknown resolution string %s" % resolution)


