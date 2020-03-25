import numpy as np
from metadata import planar_resolution, windowing_settings
from data_manager_v2 import metadata_cache

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

    if stack in metadata_cache['image_shape']:
        w_px, h_px = metadata_cache['image_shape'][stack]
    else:
        assert image_shape is not None
        w_px, h_px = image_shape

    grid_spec = (patch_size_px, spacing_px, w_px, h_px)
    return grid_spec
