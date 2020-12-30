#!/usr/bin/env python

import argparse
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""Align consecutive images. Possible bad alignment pairs are written into a separate file.
Usage 1: align.py in.ini --prep_id alignedPadded
Usage 2: align.py in.ini --elastix_output_dir DEMO998_elastix_output/ --param_fp params.txt
Usage 3: align.py in.ini --op from_none_to_aligned
"""
)

parser.add_argument("input_spec", type=str, help="input specifier. ini")
parser.add_argument("--op", type=str, help="operation id")
parser.add_argument("--prep_id", type=str, help="Prep id of the warp operation.")
parser.add_argument("--elastix_output_dir", type=str, help="output dir. Files for each pairwise transform are stored in sub-folder <currImageName>_to_<prevImageName>.")
parser.add_argument("--param_fp", type=str, help="elastix parameter file path")
#parser.add_argument("-r", help="re-generate even if already exists", action='store_true')

args = parser.parse_args()

import os
import sys
import json
import re

sys.path.append(os.environ['REPO_DIR'] + '/utilities')
from utilities2015 import *
from data_manager import *
from metadata import *
from distributed_utilities import *

input_spec = load_ini(args.input_spec)
print input_spec
stack = input_spec['stack']
prep_id = input_spec['prep_id']
if prep_id == 'None':
    prep_id = None
resol = input_spec['resol']
version = input_spec['version']
if version == 'None':
    version = None
image_name_list = input_spec['image_name_list']
if image_name_list == 'all':
    image_name_list = map(lambda x: x[0], sorted(DataManager.load_sorted_filenames(stack=stack)[0].items(), key=lambda x: x[1]))
    #image_name_list = DataManager.load_sorted_filenames(stack=stack)[0].keys()

if args.op is not None:
    op = load_ini(os.path.join(DATA_ROOTDIR, 'CSHL_data_processed', stack, 'operation_configs', args.op + '.ini'))
    assert op['type'] == 'warp', "Op must be a warp"
    elastix_output_dir = op['elastix_output_dir']
    params_fp = op['elastix_parameter_fp']

    assert op['base_prep_id'] == input_spec['prep_id'], "Op has base prep %s, but input has prep %s." % (op['base_prep_id'], input_spec['prep_id'])

else:
    assert args.elastix_output_dir is not None, "Must provide elastix_output_dir"
    assert args.param_fp is not None, "Must provide param_fp"
    elastix_output_dir = args.elastix_output_dir
    params_fp = args.param_fp


run_distributed("python %(script)s \"%(output_dir)s\" \'%%(kwargs_str)s\' -p %(param_fp)s -r" % \
                {'script': os.path.join(os.getcwd(), 'align_sequential.py'),
                'output_dir': elastix_output_dir,
                 'param_fp': params_fp
                },
                kwargs_list=[{'prev_img_name': image_name_list[i-1],
                              'curr_img_name': image_name_list[i],
                              'prev_fp': DataManager.get_image_filepath_v2(stack=stack, fn=image_name_list[i-1], prep_id=prep_id, resol=resol, version=version),
                              'curr_fp': DataManager.get_image_filepath_v2(stack=stack, fn=image_name_list[i], prep_id=prep_id, resol=resol, version=version)
                             }
                            for i in range(1, len(image_name_list))],
                argument_type='list',
                jobs_per_node=8,
               local_only=True)
