import os, sys
from subprocess import call

import numpy as np
import pandas as pd
import configparser
import json
import pickle
import bloscpack as bp
import joblib

from skimage.io import imsave
from skimage.measure import find_contours, regionprops

from vis3d_utilities import save_mesh_stl
from metadata import ROOT_DIR
#from utilities.metadata import all_known_structures, singular_structures, convert_to_left_name, convert_to_right_name
#from distributed_utilities import upload_to_s3
#from data_manager_v2 import DataManager

def crop_volume_to_minimal(vol, origin=(0,0,0), margin=0, return_origin_instead_of_bbox=True):
    """
    Returns:
        (nonzero part of volume, origin of cropped volume)
    """
    xmin, xmax, ymin, ymax, zmin, zmax = bbox_3d(vol)
    xmin = max(0, xmin - margin)
    ymin = max(0, ymin - margin)
    zmin = max(0, zmin - margin)
    xmax = min(vol.shape[1]-1, xmax + margin)
    ymax = min(vol.shape[0]-1, ymax + margin)
    zmax = min(vol.shape[2]-1, zmax + margin)

    if return_origin_instead_of_bbox:
        return vol[ymin:ymax+1, xmin:xmax+1, zmin:zmax+1], np.array(origin) + (xmin,ymin,zmin)
    else:
        return vol[ymin:ymax+1, xmin:xmax+1, zmin:zmax+1], np.array(origin)[[0,0,1,1,2,2]] + (xmin,xmax,ymin,ymax,zmin,zmax)



def bbox_3d(img):

    r = np.any(img, axis=(1, 2))
    c = np.any(img, axis=(0, 2))
    z = np.any(img, axis=(0, 1))

    try:
        rmin, rmax = np.where(r)[0][[0, -1]]
        cmin, cmax = np.where(c)[0][[0, -1]]
        zmin, zmax = np.where(z)[0][[0, -1]]
    except:
        raise Exception('Input is empty.\n')

    return cmin, cmax, rmin, rmax, zmin, zmax



def load_hdf_v2(fn, key='data'):
    return pd.read_hdf(fn, key)


def one_liner_to_arr(line, func):
    return np.array(map(func, line.strip().split()))



def load_ini(fp, split_newline=True, convert_none_str=True, section='DEFAULT'):
    """
    Value of string None will be converted to Python None.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(fp):
        raise Exception("ini file %s does not exist." % fp)
    config.read(fp)
    input_spec = dict(config.items(section))
    input_spec = {k: v.split('\n') if '\n' in v else v for k, v in input_spec.items()}
    for k, v in input_spec.items():
        if not isinstance(v, list):
            if '.' not in v and v.isdigit():
                input_spec[k] = int(v)
            elif v.replace('.','',1).isdigit():
                input_spec[k] = float(v)
        elif v == 'None':
            if convert_none_str:
                input_spec[k] = None
    assert len(input_spec) > 0, "Failed to read data from ini file."
    return input_spec


def save_json(obj, fp):
    with open(fp, 'w') as f:
        # numpy array is not JSON serializable; have to convert them to list.
        if isinstance(obj, dict):
            obj = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in obj.items()}
        json.dump(obj, f)


def create_if_not_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            sys.stderr.write('%s\n' % e)

    return path


def load_pickle(fp):
    with open(fp, 'r') as f:
        obj = pickle.load(f)

    return obj


def convert_volume_forms(volume, out_form):
    """
    Convert a (volume, origin) tuple into a bounding box.
    """

    if isinstance(volume, np.ndarray):
        vol = volume
        ori = np.zeros((3,))
    elif isinstance(volume, tuple):
        assert len(volume) == 2
        vol = volume[0]
        if len(volume[1]) == 3:
            ori = volume[1]
        elif len(volume[1]) == 6:
            ori = volume[1][[0,2,4]]
        else:
            raise

    bbox = np.array([ori[0], ori[0] + vol.shape[1]-1, ori[1], ori[1] + vol.shape[0]-1, ori[2], ori[2] + vol.shape[2]-1])

    if out_form == ("volume", 'origin'):
        return (vol, ori)
    elif out_form == ("volume", 'bbox'):
        return (vol, bbox)
    elif out_form == "volume":
        return vol
    else:
        raise Exception("out_form %s is not recognized.")

def save_data(data, fp, upload_s3=True):

    create_parent_dir_if_not_exists(fp)

    if fp.endswith('.bp'):
        try:
            bp.pack_ndarray_file(np.ascontiguousarray(data), fp)
            # ascontiguousarray is important, without which sometimes the loaded array will be different from saved.
        except:
            fp = fp.replace('.bp', '.npy')
            np.save(fp, np.ascontiguousarray(data))
    elif fp.endswith('.npy'):
        np.save(fp, np.ascontiguousarray(data))
    elif fp.endswith('.json'):
        save_json(data, fp)
    elif fp.endswith('.pkl'):
        save_pickle(data, fp)
    elif fp.endswith('.hdf'):
        save_hdf(data, fp)
    elif fp.endswith('.stl'):
        save_mesh_stl(data, fp)
    elif fp.endswith('.txt'):
        if isinstance(data, np.ndarray):
            np.savetxt(fp, data)
        else:
            raise
    elif fp.endswith('.dump'):  # sklearn classifiers
        joblib.dump(data, fp)
    elif fp.endswith('.png') or fp.endswith('.tif') or fp.endswith('.jpg'):
        imsave(fp, data)
    else:
        raise

    #if ENABLE_UPLOAD_S3 and upload_s3:  # in the future, use only one flag.
    #    upload_to_s3(fp)


def create_parent_dir_if_not_exists(fp):
    create_if_not_exists(os.path.dirname(fp))


def save_pickle(obj, fp):
    with open(fp, 'w') as f:
        pickle.dump(obj, f)


def save_hdf(data, fn, key='data', mode='w'):
    """
    Save data as a hdf file.
    If data is dict of dict, convert to DataFrame before saving as hdf.
    If data is dict of elementary items, convert to pandas.Series before saving as hdf.
    Args:
        data (pandas.DataFrame, dict or dict of dict)
        mode (str): if 'w', overwrite original content. If 'a', append.
    """

    create_parent_dir_if_not_exists(fn)
    if isinstance(data, pd.DataFrame):
        data.to_hdf(fn, key=key, mode=mode) # important to set mode='w', default is 'a' (append)
    elif isinstance(data, dict):
        if isinstance(data.values()[0], dict): # dict of dict
            pd.DataFrame(data).T.to_hdf(fn, key=key, mode='w')
        else:
            pd.Series(data=data).to_hdf(fn, key, mode='w')


def execute_command(cmd, stdout=None, stderr=None):
    sys.stderr.write(cmd + '\n')
    # retcode = os.system(cmd)
    retcode = call(cmd, shell=True, stdout=stdout, stderr=stderr)
    sys.stderr.write('return code: %d\n' % retcode)


def rescale_by_resampling(v, scaling=None, new_shape=None):
    """
    Args:
        new_shape: width, height
    """

    # print v.shape, scaling

    if new_shape is not None:
        return v[np.meshgrid(np.floor(np.linspace(0, v.shape[0]-1, new_shape[1])).astype(np.int),
                  np.floor(np.linspace(0, v.shape[1]-1, new_shape[0])).astype(np.int), indexing='ij')]
    else:
        if scaling == 1:
            return v

        if v.ndim == 3:
            if v.shape[-1] == 3: # RGB image
                return v[np.meshgrid(np.floor(np.arange(0, v.shape[0], 1./scaling)).astype(np.int),
                  np.floor(np.arange(0, v.shape[1], 1./scaling)).astype(np.int), indexing='ij')]
            else: # 3-d volume
                return v[np.meshgrid(np.floor(np.arange(0, v.shape[0], 1./scaling)).astype(np.int),
                  np.floor(np.arange(0, v.shape[1], 1./scaling)).astype(np.int),
                  np.floor(np.arange(0, v.shape[2], 1./scaling)).astype(np.int), indexing='ij')]
        elif v.ndim == 2:
            return v[np.meshgrid(np.floor(np.arange(0, v.shape[0], 1./scaling)).astype(np.int),
                  np.floor(np.arange(0, v.shape[1], 1./scaling)).astype(np.int), indexing='ij')]
        else:
            raise


def convert_vol_bbox_dict_to_overall_vol(vol_bbox_dict=None, vol_bbox_tuples=None, vol_origin_dict=None):
    """
    Must provide exactly one of the three choices of arguments.
    `bbox` or `origin` can be provided as float, but will be casted as integer before cropping and padding.
    Args:
        vol_bbox_dict (dict {key: 3d-array of float32, 6-tuple of float}): represents {name_s: (vol, bbox)}
        vol_origin_dict (dict {key: 3d-array of float32, 3-tuple of float}): represents {name_s: (vol, origin)}
    Returns:
        (list or dict of 3d arrays, (6,)-ndarray of int): (volumes in overall coordinate system, the common overall bounding box)
    """

    if vol_origin_dict is not None:
        vol_bbox_dict = {k: (v, (o[0], o[0]+v.shape[1]-1, o[1], o[1]+v.shape[0]-1, o[2], o[2]+v.shape[2]-1)) for k,(v,o) in vol_origin_dict.iteritems()}

    if vol_bbox_dict is not None:
        volume_bbox = np.round(get_overall_bbox(vol_bbox_tuples=vol_bbox_dict.values())).astype(np.int)
        volumes = crop_and_pad_volumes(out_bbox=volume_bbox, vol_bbox_dict=vol_bbox_dict)
    else:
        volume_bbox = np.round(get_overall_bbox(vol_bbox_tuples=vol_bbox_tuples)).astype(np.int)
        volumes = crop_and_pad_volumes(out_bbox=volume_bbox, vol_bbox_tuples=vol_bbox_tuples)
    return volumes, np.array(volume_bbox)


def get_overall_bbox(vol_bbox_tuples=None, bboxes=None):
    if bboxes is None:
        bboxes = np.array([b for v, b in vol_bbox_tuples])
    xmin, ymin, zmin = np.min(bboxes[:, [0,2,4]], axis=0)
    xmax, ymax, zmax = np.max(bboxes[:, [1,3,5]], axis=0)
    bbox = xmin, xmax, ymin, ymax, zmin, zmax
    return bbox



def crop_and_pad_volume(in_vol, in_bbox=None, in_origin=(0,0,0), out_bbox=None):
    """
    Crop and pad an volume.
    in_vol and in_bbox together define the input volume in a underlying space.
    out_bbox then defines how to crop the underlying space, which generates the output volume.
    Args:
        in_bbox ((6,) array): the bounding box that the input volume is defined on. If None, assume origin is at (0,0,0) of the input volume.
        in_origin ((3,) array): the input volume origin coordinate in the space. Used only if in_bbox is not specified. Default is (0,0,0), meaning the input volume is located at the origin of the underlying space.
        out_bbox ((6,) array): the bounding box that the output volume is defined on. If not given, each dimension is from 0 to the max reach of any structure.
    Returns:
        3d-array: cropped/padded volume
    """

    if in_bbox is None:
        assert in_origin is not None
        in_xmin, in_ymin, in_zmin = in_origin
        in_xmax = in_xmin + in_vol.shape[1] - 1
        in_ymax = in_ymin + in_vol.shape[0] - 1
        in_zmax = in_zmin + in_vol.shape[2] - 1
    else:
        in_bbox = np.array(in_bbox).astype(np.int)
        in_xmin, in_xmax, in_ymin, in_ymax, in_zmin, in_zmax = in_bbox
    #FIXME what is this code doing below?
    in_xdim = in_xmax - in_xmin + 1
    in_ydim = in_ymax - in_ymin + 1
    in_zdim = in_zmax - in_zmin + 1
        # print 'in', in_xdim, in_ydim, in_zdim

    if out_bbox is None:
        out_xmin = 0
        out_ymin = 0
        out_zmin = 0
        out_xmax = in_xmax
        out_ymax = in_ymax
        out_zmax = in_zmax
    elif isinstance(out_bbox, np.ndarray) and out_bbox.ndim == 3:
        out_xmin, out_xmax, out_ymin, out_ymax, out_zmin, out_zmax = (0, out_bbox.shape[1]-1, 0, out_bbox.shape[0]-1, 0, out_bbox.shape[2]-1)
    else:
        out_bbox = np.array(out_bbox).astype(np.int)
        out_xmin, out_xmax, out_ymin, out_ymax, out_zmin, out_zmax = out_bbox
    out_xdim = out_xmax - out_xmin + 1
    out_ydim = out_ymax - out_ymin + 1
    out_zdim = out_zmax - out_zmin + 1

    # print out_xmin, out_xmax, out_ymin, out_ymax, out_zmin, out_zmax

    if out_xmin > in_xmax or out_xmax < in_xmin or out_ymin > in_ymax or out_ymax < in_ymin or out_zmin > in_zmax or out_zmax < in_zmin:
        return np.zeros((out_ydim, out_xdim, out_zdim), np.int)

    if out_xmax > in_xmax:
        in_vol = np.pad(in_vol, pad_width=[(0,0),(0, out_xmax-in_xmax),(0,0)], mode='constant', constant_values=0)
        # print 'pad x'
    if out_ymax > in_ymax:
        in_vol = np.pad(in_vol, pad_width=[(0, out_ymax-in_ymax),(0,0),(0,0)], mode='constant', constant_values=0)
        # print 'pad y'
    if out_zmax > in_zmax:
        in_vol = np.pad(in_vol, pad_width=[(0,0),(0,0),(0, out_zmax-in_zmax)], mode='constant', constant_values=0)
        # print 'pad z'

    out_vol = np.zeros((out_ydim, out_xdim, out_zdim), in_vol.dtype)
    ymin = max(in_ymin, out_ymin)
    xmin = max(in_xmin, out_xmin)
    zmin = max(in_zmin, out_zmin)
    ymax = out_ymax
    xmax = out_xmax
    zmax = out_zmax
    # print 'in_vol', np.array(in_vol.shape)[[1,0,2]]
    # print xmin, xmax, ymin, ymax, zmin, zmax
    # print xmin-in_xmin, xmax+1-in_xmin
    # assert ymin >= 0 and xmin >= 0 and zmin >= 0
    out_vol[ymin-out_ymin:ymax+1-out_ymin,
            xmin-out_xmin:xmax+1-out_xmin,
            zmin-out_zmin:zmax+1-out_zmin] = in_vol[ymin-in_ymin:ymax+1-in_ymin, xmin-in_xmin:xmax+1-in_xmin, zmin-in_zmin:zmax+1-in_zmin]

    assert out_vol.shape[1] == out_xdim
    assert out_vol.shape[0] == out_ydim
    assert out_vol.shape[2] == out_zdim

    return out_vol


def crop_and_pad_volumes(out_bbox=None, vol_bbox_dict=None, vol_bbox_tuples=None, vol_bbox=None):
    """
    Args:
        out_bbox ((6,)-array): the output bounding box, must use the same reference system as the vol_bbox input.
        vol_bbox_dict (dict {key: (vol, bbox)})
        vol_bbox_tuples (list of (vol, bbox) tuples)
    Returns:
        list of 3d arrays or dict {structure name: 3d array}
    """

    if vol_bbox is not None:
        if isinstance(vol_bbox, dict):
            vols = {l: crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for l, (v, b) in volumes.items()}
        elif isinstance(vol_bbox, list):
            vols = [crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for (v, b) in volumes]
        else:
            raise
    else:
        if vol_bbox_tuples is not None:
            vols = [crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for (v, b) in vol_bbox_tuples]
        elif vol_bbox_dict is not None:
            vols = {l: crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for l, (v, b) in vol_bbox_dict.items()}
        else:
            raise

    return vols


def find_contour_points(labelmap, sample_every=10, min_length=0):
    """
    Find contour coordinates.
    Args:
        labelmap (2d array of int): integer-labeled 2D image
        sample_every (int): can be interpreted as distance between points.
        min_length (int): contours with fewer vertices are discarded.
        This argument is being deprecated because the vertex number does not
        reliably measure actual contour length in microns.
        It is better to leave this decision to calling routines.
    Returns:
        a dict of lists: {label: list of contours each consisting of a list of (x,y) coordinates}
    """

    padding = 5

    if np.count_nonzero(labelmap) == 0:
        # sys.stderr.write('No contour can be found because the image is blank.\n')
        return {}

    regions = regionprops(labelmap.astype(np.int))
    contour_points = {}

    for r in regions:

        (min_row, min_col, max_row, max_col) = r.bbox

        padded = np.pad(r.filled_image, ((padding,padding),(padding,padding)),
                        mode='constant', constant_values=0)

        contours = find_contours(padded, level=.5, fully_connected='high')
        contours = [cnt.astype(np.int) for cnt in contours if len(cnt) > min_length]
        if len(contours) > 0:
#             if len(contours) > 1:
#                 sys.stderr.write('%d: region has more than one part\n' % r.label)

            contours = sorted(contours, key=lambda c: len(c), reverse=True)
            contours_list = [c-(padding, padding) for c in contours]
            contour_points[r.label] = sorted([c[np.arange(0, c.shape[0], sample_every)][:, ::-1] + (min_col, min_row)
                                for c in contours_list], key=lambda c: len(c), reverse=True)

        elif len(contours) == 0:
#             sys.stderr.write('no contour is found\n')
            continue

    #         viz = np.zeros_like(r.filled_image)
    #         viz[pts_sampled[:,0], pts_sampled[:,1]] = 1
    #         plt.imshow(viz, cmap=plt.cm.gray);
    #         plt.show();

    return contour_points


def bbox_2d(img):
    """
    Returns:
        (xmin, xmax, ymin, ymax)
    """

    if np.count_nonzero(img) == 0:
        raise Exception('bbox2d: Image is empty.')
    rows = np.any(img, axis=1)
    cols = np.any(img, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    return cmin, cmax, rmin, rmax

def create_thumbnails(stack):
    ## Downsample and normalize images in the "_raw" folder
    raw_folder = os.path.join(ROOT_DIR, stack, 'raw')
    for img_name in os.listdir(raw_folder):
        input_fp = os.path.join(raw_folder, img_name)
        output_fp = os.path.join(ROOT_DIR, stack, 'preps', 'thumbnail', img_name)

        # Create thumbnails
        execute_command("convert \"" + input_fp + "\" -resize 3.125% -auto-level -normalize \
                        -compress lzw \"" + output_fp + "\"")
