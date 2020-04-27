#!/usr/bin/env python

import sys
import os
import argparse
from collections import defaultdict
from itertools import chain
import numpy as np

from utilities.data_manager_v2 import DataManager
from utilities.distributed_utilities import run_distributed
from utilities.metadata import DATA_ROOTDIR, orientation_argparse_str_to_imagemagick_str
from utilities.utilities2015 import csv_to_dict, convert_2d_transform_forms, convert_cropbox_fmt, load_ini, \
    create_parent_dir_if_not_exists, execute_command
from utilities.sqlcontroller import SqlController

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""A versatile warp/crop script. 
Usage 1: warp_crop.py --input_spec in.ini --op_id align1crop1
This is the high-level usage. The operations are defined as ini files in the operation_configs/ folder.

Usage 2: warp_crop.py --input_fp in.tif --output_fp out.tif --op warp 0.99,0,0,0,1.1,0 --op crop 100,100,20,10
This is the low-level usage. Note that the user must ensure the warp parameters and crop coordinates are consistent with the resolution of the input image.
"""
)

parser.add_argument("--input_spec", type=str, help="input specifier. ini")
parser.add_argument("--op_id", type=str, help="operation id")
parser.add_argument("--op", action='append', nargs=2,
    #metavar=('op_type', 'op_params'),
    help="operation list")
parser.add_argument("--input_fp", type=str, help="input filepath")
parser.add_argument("--output_fp", type=str, help="output filepath")
parser.add_argument("--pad_color", type=str, help="background color (black or white)", default='auto')
parser.add_argument("--njobs", type=int, help="Number of parallel jobs", default=1)
parser.add_argument("-r", "--init_rotate", type=str, help="escaped imagemagick convert option string for initial flipping and rotation", default='')

args = parser.parse_args()

def convert_operation_to_arr(op, resol, inverse=False, return_str=False, stack=None):
    """
    If op is warp, return {image_name: (3,3)-array}.
    If op is crop, return {image_name: (x,y,w,h)}.
    """
    assert 'type' in op, "Operation spec must provide type."
    if op['type'] == 'warp':
        tf_csv = op['transforms_csv']
        assert tf_csv.endswith('.csv'), "transforms_csv is not a csv file."
        #print(tf_csv)
        transforms_to_anchor = csv_to_dict(tf_csv)

        transforms_resol = op['resolution']
        transforms_scale_factor = DataManager.convert_resolution_string_to_um(stack=stack, resolution=transforms_resol) / DataManager.sqlController.convert_resolution_string_to_um(stack=stack, resolution=resol)
        tf_mat_mult_factor = np.array([[1,1,transforms_scale_factor],[1,1,transforms_scale_factor]])
        if inverse:
            transforms_to_anchor = {img_name: convert_2d_transform_forms(np.linalg.inv(np.reshape(tf, (3,3)))[:2] * tf_mat_mult_factor, out_form='str') for img_name, tf in transforms_to_anchor.iteritems()}
        else:
            transforms_to_anchor = {img_name: convert_2d_transform_forms(np.reshape(tf, (3,3))[:2] * tf_mat_mult_factor, out_form='str') for img_name, tf in transforms_to_anchor.iteritems()}

        return transforms_to_anchor

    elif op['type'] == 'crop':
        cropbox_resol = op['resolution']

        if 'cropboxes_csv' in op: # each image has a different cropbox
            cropboxes_all = csv_to_dict(op['cropboxes_csv'])

            cropboxes = {}
            for img_name in image_name_list:
                arr_xxyy = convert_cropbox_fmt(data=cropboxes_all[img_name], in_fmt='arr_xywh', out_fmt='arr_xxyy')
                if inverse:
                    arr_xxyy = np.array([-arr_xxyy[0], arr_xxyy[1], -arr_xxyy[2], arr_xxyy[3]])
                cropboxes[img_name] = convert_cropbox_fmt(data=arr_xxyy, in_fmt='arr_xxyy', out_fmt='str_xywh' if return_str else 'arr_xywh', in_resol=cropbox_resol, out_resol=resol, stack=stack)

#               cropboxes = {img_name: convert_cropbox_fmt(data=cropboxes_all[img_name], in_fmt='arr_xywh', out_fmt='str_xywh' if return_str else 'arr_xywh', in_resol=cropbox_resol, out_resol=resol, stack=stack) for img_name in image_name_list}

        else: # a single cropbox for all images
            arr_xxyy = convert_cropbox_fmt(data=op, in_fmt='dict', out_fmt='arr_xxyy', in_resol=cropbox_resol, out_resol=resol, stack=stack)
            if inverse:
                arr_xxyy = np.array([-arr_xxyy[0], arr_xxyy[1], -arr_xxyy[2], arr_xxyy[3]])
            cropbox = convert_cropbox_fmt(data=arr_xxyy, in_fmt='arr_xxyy', out_fmt='str_xywh' if return_str else 'arr_xywh', stack=stack)
            cropboxes = {img_name: cropbox for img_name in image_name_list}

        return cropboxes

    elif op['type'] == 'rotate':
        return {img_name: op['how'] for img_name in image_name_list}

    else:
        raise Exception("Operation type specified by ini must be either warp, crop or rotate.")


def parse_operation_sequence(op_name, resol, return_str=False, stack=None):
    inverse = op_name.startswith('-')
    if inverse:
        op_name = op_name[1:]

    #op = load_ini(os.path.join(DATA_ROOTDIR, 'CSHL_data_processed', stack, 'operation_configs', op_name + '.ini'))
    op_path = os.path.join( DATA_ROOTDIR,'CSHL_data_processed',stack, 'operation_configs', op_name + '.ini')
    op = load_ini(op_path)
    #print op
    if op is None:
        raise Exception("Cannot load %s.ini" % op_name)
    if 'operation_sequence' in op: # composite operation

        assert not inverse, "Inverse composite operation is not implemented."
        op_seq = list(chain(*map(lambda o: parse_operation_sequence(o, resol=resol, return_str=return_str, stack=stack), op['operation_sequence'])))
        assert all([op_seq[i][3] == op_seq[i+1][2] for i in range(0, len(op_seq)-1)]), "In and out domains are not consistent along the composite operation chain. %s" % [(o[2], o[3]) for o in op_seq]

    else: # single operation
        op_arr = convert_operation_to_arr(op, resol=resol, inverse=inverse, return_str=return_str, stack=stack)
        if inverse:
            op_seq = [(op['type'], op_arr, op['dest_prep_id'], op['base_prep_id'])]
        else:
            op_seq = [(op['type'], op_arr, op['base_prep_id'], op['dest_prep_id'])]
    #print op_seq
    return op_seq


init_rotate = args.init_rotate
pad_color = args.pad_color


if args.op_id is not None:

    #print 'args.op_id'
    #print args.op_id

    input_spec = load_ini(args.input_spec)
    stack = input_spec['stack']
    prep_id = input_spec['prep_id']
    version = input_spec['version']
    resol = input_spec['resol']
    sqlController = SqlController()
    image_name_list = input_spec['image_name_list']
    if image_name_list == 'all':
        #image_name_list = DataManager.load_sorted_filenames(stack=stack)[0].keys()
        pass

    image_name_list = sqlController.get_image_list(stack, 'destination')

    op_seq = parse_operation_sequence(args.op_id, resol=resol, return_str=True, stack=stack)

    ops_in_prep_id = op_seq[0][2]
    out_prep_id = op_seq[-1][3]

    #print op_seq
    #print ops_in_prep_id
    #print out_prep_id

    if prep_id==None:
        prep_id = "None"
    if ops_in_prep_id==None:
        ops_in_prep_id = "None"

    if version=="None":
        version = None

    # Choose pad color
    if version=="NtbNormalized":
        pad_color = 'black'
    elif version=="NtbNormalizedAdaptiveInvertedGamma":
        pad_color = 'white'
    elif version=="gray":
        pad_color = 'white'

    assert ops_in_prep_id == prep_id, "Input prep according to operation configs is %s, but the provided input_spec is %s." % (ops_in_prep_id, prep_id)

    ops_str_all_images = defaultdict(str)
    for op_type, op_params_str_all_images, _, _ in op_seq:
        for img_name, op_params_str in op_params_str_all_images.items():
            # replace leading minus sign with ^ to satisfy argparse
            if op_params_str.startswith('-'):
                op_params_str = '^' + op_params_str[1:]

            ops_str_all_images[img_name] += ' --op %s %s ' % (op_type, op_params_str)

    # sequantial_dispatcher argument cannot be too long, so we must limit the number of images processed each time
    batch_size = 100
    for batch_id in range(0, len(image_name_list), batch_size):

        #print '_____________________________________________'
        #print batch_id
        #print '_____________________________________________'

        # Removes stderr and stdout
        run_distributed('python %(script)s --input_fp \"%%(input_fp)s\" \
        --output_fp \"%%(output_fp)s\" %%(ops_str)s --pad_color %%(pad_color)s' % \
        {'script':  os.path.join(os.getcwd(), 'warp_crop_v3.py'),},
        kwargs_list=[{'ops_str': ops_str_all_images[img_name],
        'input_fp': DataManager.get_image_filepath_v2(stack=stack, fn=img_name, prep_id=prep_id, version=version, resol=resol),
        'output_fp': DataManager.get_image_filepath_v2(stack=stack, fn=img_name, prep_id=out_prep_id, version=version, resol=resol),
        'pad_color': pad_color}
            for img_name in image_name_list[batch_id:batch_id+batch_size]],
        argument_type='single',
        jobs_per_node=args.njobs,
        local_only=True)

elif args.op is not None:
# Usage 1

    op_str = ''
    for op_type, op_params in args.op: # args.op is a list

        # revert the leading minus sign hack
        if op_params.startswith('^'):
            op_params = '-' + op_params[1:]

        if op_type == 'warp':
            T = np.linalg.inv(convert_2d_transform_forms(transform=op_params, out_form=(3,3)))
            op_str += " +distort AffineProjection '%(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f' " % {
                    'sx':T[0,0],
                     'sy':T[1,1],
                     'rx':T[1,0],
                    'ry':T[0,1],
                     'tx':T[0,2],
                     'ty':T[1,2] }
        elif op_type == 'crop':
            x, y, w, h = convert_cropbox_fmt(data=op_params, out_fmt='arr_xywh', in_fmt='str_xywh')
            op_str += ' -crop %(w)sx%(h)s%(x)s%(y)s\! ' % {
                             'x': '+' + str(x) if int(x) >= 0 else str(x),
                             'y': '+' + str(y) if int(y) >= 0 else str(y),
                             'w': str(w),
                             'h': str(h)}


        elif op_type == 'rotate':
            #print op_params
            #print orientation_argparse_str_to_imagemagick_str.keys()
            #print orientation_argparse_str_to_imagemagick_str[op_params]
            #print op_str
            op_str += ' ' + orientation_argparse_str_to_imagemagick_str[op_params]

        else:
            raise Exception("Op_id must be either warp or crop.")


    assert args.input_fp is not None and args.output_fp is not None
    input_fp = args.input_fp
    output_fp = args.output_fp

    create_parent_dir_if_not_exists(output_fp)

    try:
        execute_command("convert \"%(input_fp)s\"  +repage -virtual-pixel background -background %(bg_color)s %(op_str)s -flatten -compress lzw \"%(output_fp)s\"" % \
                {'op_str': op_str,
                 'input_fp': input_fp,
                 'output_fp': output_fp,
                 'bg_color': pad_color})
    except Exception as e:
        sys.stderr.write("ImageMagick convert failed for input_fp %s: %s\n" % (input_fp, e.message))


