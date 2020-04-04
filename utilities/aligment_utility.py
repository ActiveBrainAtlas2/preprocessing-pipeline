import os
import cv2
import numpy as np
import math

from data_manager_v2 import DataManager
from sqlcontroller import SqlController
from metadata import stain_to_metainfo, ROOT_DIR
from utilities2015 import execute_command

sqlController = SqlController()

def get_padding_color(stack):
    sqlController.get_animal_info(stack)
    stain = sqlController.histology.counterstain
    if stain.lower() == 'ntb':
        return 'black'
    elif stain.lower() == 'thionin':
        return 'white'
    else:
        return 'auto'


def get_version(stack):
    sqlController.get_animal_info(stack)
    stain = sqlController.histology.counterstain
    return stain_to_metainfo[stain.lower()]['img_version_1']


def apply_transform(stack, T, input_tif, output_fp=None):
    """
    Applies transform T onto the image at img_fp and return the result
    """
    version = get_version(stack)
    #img_fp = DataManager.get_image_filepath(stack=stack, section=DataManager.metadata_cache['filenames_to_sections'][stack][fn],resol='thumbnail', version=version)
    img_fp = os.path.join(ROOT_DIR, stack, 'preps', 'thumbnail', input_tif)
    op_str = ''
    op_str += " +distort AffineProjection '%(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f' " % {
        'sx': T[0, 0],
        'sy': T[1, 1],
        'rx': T[1, 0],
        'ry': T[0, 1],
        'tx': T[0, 2],
        'ty': T[1, 2], }

    x = 0
    y = 0
    w = 2000
    h = 1000
    op_str += ' -crop %(w)sx%(h)s%(x)s%(y)s\! ' % {
        'x': '+' + str(x) if int(x) >= 0 else str(x),
        'y': '+' + str(y) if int(y) >= 0 else str(y),
        'w': str(w),
        'h': str(h)}

    if output_fp == None:
        output_fp_root = os.path.join(ROOT_DIR, stack, 'preps', 'CSHL_data_processed', 'tmp')
        if not os.path.exists(output_fp_root):
            os.makedirs(output_fp_root)
        output_fp = os.path.join(output_fp_root, input_tif)
        delete_after = True
    else:
        if not os.path.exists(os.path.dirname(output_fp)):
            os.makedirs(os.path.dirname(output_fp))
        delete_after = False

    try:
        bg_color = get_padding_color(stack)

        execute_command(
            "convert \"%(input_fp)s\"  +repage -virtual-pixel background -background %(bg_color)s %(op_str)s -flatten -compress lzw \"%(output_fp)s\"" % \
            {'op_str': op_str,
             'input_fp': img_fp,
             'output_fp': output_fp,
             'bg_color': bg_color})

        img = cv2.imread(output_fp)
        if delete_after:
            os.remove(output_fp)
            pass
        return img
    except Exception as e:
        print(e)
        return None


def get_anchor_transform(stack, input_tif):
    T = DataManager.load_transforms(stack, downsample_factor=32, use_inverse=True)[input_tif]
    return T


def get_pairwise_transform(stack, fn, prev_fn):
    T = DataManager.load_consecutive_section_transform(
        moving_fn=fn,
        fixed_fn=prev_fn,
        stack=stack)
    T = np.linalg.inv(T)
    return T


def get_comulative_pairwise_transform(stack, fn):
    T = np.zeros((3, 3))  # [[0,0,0],[0,0,0],[0,0,1]]
    T[2, 2] = 1

    # valid_fn_prev = DataManager.metadata_cache['valid_filenames_all'][stack][0]
    # for valid_fn in DataManager.metadata_cache['valid_filenames_all'][stack][1:]:
    #    if valid_fn == fn:
    #        break
    #    T_i = DataManager.load_consecutive_section_transform(
    #                moving_fn=valid_fn,
    #                fixed_fn=valid_fn_prev,
    #                stack=stack)

    valid_sections = DataManager.metadata_cache['valid_sections_all'][stack]
    valid_sections.sort()
    valid_sections.reverse()

    valid_sec = valid_sections[0]
    for valid_sec_prev in valid_sections[1:]:
        valid_fn = DataManager.metadata_cache['sections_to_filenames'][stack][valid_sec]
        valid_fn_prev = DataManager.metadata_cache['sections_to_filenames'][stack][valid_sec_prev]

        if valid_fn == fn:
            break

        T_i = DataManager.load_consecutive_section_transform(
            moving_fn=valid_fn,
            fixed_fn=valid_fn_prev,
            stack=stack)

        T_i = np.linalg.inv(T_i)

        T[0, 0] = math.cos(math.acos(T[0, 0]) + math.acos(T_i[0, 0]))
        T[1, 1] = math.cos(math.acos(T[1, 1]) + math.acos(T_i[1, 1]))
        T[0, 1] = -math.sin(math.asin(-T[0, 1]) + math.asin(-T_i[0, 1]))
        T[1, 0] = math.sin(math.asin(T[1, 0]) + math.asin(T_i[1, 0]))
        T[0, 2] += T_i[0, 2]
        T[1, 2] += T_i[1, 2]

        # valid_fn_prev = valid_fn
        valid_sec = valid_sec_prev

    # T[0,2] = 0
    # T[1,2] = 0
    return T


def get_transformed_image(stack, section, transformation='anchor', prev_section=-1):
    assert transformation in ['anchor', 'pairwise']

    input_tif = SqlController.metadata_cache['sections_to_filenames'][stack][section]
    #img_fp = DataManager.get_image_filepath(stack=stack, section=section, resol='thumbnail', version='NtbNormalized')

    img_fp = os.path.join(ROOT_DIR, stack, 'preps', 'thumbnail', input_tif)



    if transformation == 'anchor':
        T = get_anchor_transform(stack, input_tif)
    elif transformation == 'pairwise':
        assert prev_section != -1
        prev_fn = DataManager.metadata_cache['sections_to_filenames'][stack][prev_section]
        T = get_pairwise_transform(stack, input_tif, prev_fn)

    img_transformed = apply_transform(stack, T, input_tif)

    return img_transformed, T


def apply_pairwise_transform(img):
    pass
