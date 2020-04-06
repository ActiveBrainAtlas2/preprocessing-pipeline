import os
import numpy as np
import mxnet as mx

from utilities.data_manager_v2 import DataManager
from utilities.distributed_utilities import download_from_s3
from utilities.metadata import MXNET_MODEL_ROOTDIR, windowing_settings


def gpu_device(gpu_number=0):
    try:
        _ = mx.nd.array([1, 2, 3], ctx=mx.gpu(gpu_number))
    except mx.MXNetError:
        return None
    return mx.gpu(gpu_number)


def grid_parameters_to_sample_locations(grid_spec=None, patch_size=None, stride=None, w=None, h=None, win_id=None, stack=None):
    """
    Provide either one of the following combination of arguments:
    - `win_id` and `stack`
    - `grid_spec`
    - `patch_size`, `stride`, `w` and `h`

    Args:
        win_id (int):

    Returns:
        2d-array of int: the list of all grid locations.
    """
    if win_id is not None:
        grid_spec = win_id_to_gridspec(win_id, stack=stack)

    if grid_spec is not None:
        patch_size, stride, w, h = grid_spec

    half_size = patch_size/2
    ys, xs = np.meshgrid(np.arange(half_size, h-half_size, stride), np.arange(half_size, w-half_size, stride),
                     indexing='xy')
    sample_locations = np.c_[xs.flat, ys.flat]
    return sample_locations


def win_id_to_gridspec(win_id, stack=None, image_shape=None):
    """
    Derive a gridspec from window id.

    Args:
        stack (str): stack is needed because different stacks have different span width and height, and may have different planar resolution.
        image_shape (2-tuple): (width, height) in pixel

    Returns:
        4-tuple: a gridspec tuple (patch size in pixel, spacing in pixel, span width in pixel, span height in pixel)
    """


    windowing_properties = windowing_settings[win_id]
    if 'patch_size' in windowing_properties:
        patch_size_px = windowing_properties['patch_size']
    elif 'patch_size_um' in windowing_properties:
        patch_size_um = windowing_properties['patch_size_um']
        patch_size_px = int(np.round(patch_size_um / planar_resolution[stack]))

    if 'spacing' in windowing_properties:
        spacing_px = windowing_properties['spacing']
    elif 'spacing_um' in windowing_properties:
        spacing_um = windowing_properties['spacing_um']
        spacing_px = int(np.round(spacing_um / planar_resolution[stack]))

    if stack in DataManager.metadata_cache['image_shape']:
        w_px, h_px = DataManager.metadata_cache['image_shape'][stack]
    else:
        assert image_shape is not None
        w_px, h_px = image_shape

    grid_spec = (patch_size_px, spacing_px, w_px, h_px)
    return grid_spec

def load_mxnet_model(model_dir_name, model_name, num_gpus=8, batch_size = 256, output_symbol_name='flatten_output'):
    download_from_s3(os.path.join(MXNET_MODEL_ROOTDIR, model_dir_name), is_dir=True)
    model_iteration = 0
    # output_symbol_name = 'flatten_output'
    output_dim = 1024
    mean_img = np.load(os.path.join(MXNET_MODEL_ROOTDIR, model_dir_name, 'mean_224.npy'))

    # Reference on how to predict with mxnet model:
    # https://github.com/dmlc/mxnet-notebooks/blob/master/python/how_to/predict.ipynb
    model0, arg_params, aux_params = mx.model.load_checkpoint(os.path.join(MXNET_MODEL_ROOTDIR, model_dir_name, model_name), 0)
    flatten_output = model0.get_internals()[output_symbol_name]
    # if HOST_ID == 'workstation':
    # model = mx.mod.Module(context=[mx.gpu(i) for i in range(1)], symbol=flatten_output)
    # else:

    if not gpu_device():
        print('No GPU device found! Use CPU for mxnet feature extraction.')
        model = mx.mod.Module(context=mx.cpu(), symbol=flatten_output)
    else:
        model = mx.mod.Module(context=[mx.gpu(i) for i in range(num_gpus)], symbol=flatten_output)

    # Increase batch_size to 500 does not save any time.
    model.bind(data_shapes=[('data', (batch_size,1,224,224))], for_training=False)
    model.set_params(arg_params=arg_params, aux_params=aux_params, allow_missing=True)
    return model, mean_img

