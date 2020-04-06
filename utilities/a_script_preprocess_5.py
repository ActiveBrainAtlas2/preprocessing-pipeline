#!/usr/bin/env python

import argparse

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Using the user specified whole brain cropbox, cropped images are generated and saved as raw "prep5" images. Thumbnails are then generated.')

parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("stain", type=str, help="Either \'NTB\' or \'Thionin\'.")
parser.add_argument('-l','--list', nargs='+', help='<Required> Set flag', required=True)
args = parser.parse_args()
stack = args.stack
stain = args.stain
rostral_limit, caudal_limit, dorsal_limit, ventral_limit = args.list
rostral_limit = float(rostral_limit)
caudal_limit = float(caudal_limit)
dorsal_limit = float(dorsal_limit)
ventral_limit = float(ventral_limit)

# Import other modules and packages
import os
import subprocess
import numpy as np
import sys
import json
import time
sys.path.append(os.path.join(os.environ['REPO_DIR'], 'utilities'))
from metadata import *
from preprocess_utilities import *
from data_manager_v2 import DataManager
from a_driver_utilities import *

# Create from_aligned_to_wholeslice.ini
make_from_x_to_y_ini( stack, x='aligned', y='wholeslice',\
                     rostral_limit=rostral_limit,caudal_limit=caudal_limit,\
                     dorsal_limit=dorsal_limit,ventral_limit=ventral_limit)
# Create from_padded_to_wholeslice.ini
make_from_x_to_y_ini( stack, x='padded', y='wholeslice',\
                     rostral_limit=rostral_limit,caudal_limit=caudal_limit,\
                     dorsal_limit=dorsal_limit,ventral_limit=ventral_limit)

if stain == 'NTB':
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='None', version='NtbNormalizedAdaptiveInvertedGamma', resol='raw')
    fp = os.path.join(DATA_ROOTDIR, 'CSHL_data_processed',stack, 'operation_configs', 'from_none_to_wholeslice')
    # Generates prep5 raw images
    command = [ 'python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', fp]
    completion_message = 'Finished transformed images into wholeslice format (prep5).'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedWithMargin', version='NtbNormalizedAdaptiveInvertedGamma', resol='raw')
    command = [ 'python', 'rescale.py', 'input_spec.ini', 'thumbnail', '-f', '0.03125']
    # Generates prep5 thumbnail images
    completion_message = 'Finished rescaling prep5 images into thumbnail format.'
    call_and_time( command, completion_message=completion_message)

if stain == 'Thionin':
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='None', version='gray', resol='raw')
    fp = os.path.join(DATA_ROOTDIR, 'CSHL_data_processed',stack, 'operation_configs', 'from_none_to_wholeslice')
    # Generates prep5 raw images
    command = [ 'python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', fp]
    completion_message = 'Finished transformed images into wholeslice format (prep5).'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedWithMargin', version='gray', resol='raw')
    command = [ 'python', 'rescale.py', 'input_spec.ini', 'thumbnail', '-f', '0.03125']
    # Generates prep5 thumbnail images
    completion_message = 'Finished rescaling prep5 images into thumbnail format.'
    call_and_time( command, completion_message=completion_message)