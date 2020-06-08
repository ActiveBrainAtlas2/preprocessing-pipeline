#!/usr/bin/env python

import argparse

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Creates "original_image_crop.csv" file which contains the dimensions of every thumbnail (32x downsampled) image. Applies reverse prep1 transforms on all masks and saves these unaligned masks in the original orientation of the images. Applies a local adaptive intensity normalization algorithm on NTB images.')

parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("stain", type=str, help="Either \'NTB\' or \'Thionin\'.")
args = parser.parse_args()
stack = args.stack
stain = args.stain

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


def create_crop_orig():
    DATA_ROOTDIR = os.environ['DATA_ROOTDIR'] # THUMBNAIL_DATA_DIR

    # Creating 'crop_orig.ini'
    fn = 'crop_orig.ini'
    crop_orig_fp = os.path.join(DataManager.get_images_root_folder(stack), 'operation_configs', fn)

    file_content = '[DEFAULT]\n\
type = crop\n\
base_prep_id = None\n\
dest_prep_id = None\n\
cropboxes_csv = '+DataManager.get_images_root_folder(stack)+'/'+stack+'_original_image_crop.csv\n\
resolution = thumbnail'

    f = open( crop_orig_fp , "w")
    f.write( file_content ) 
    f.close()
create_crop_orig()


if stain == 'NTB':
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='None', version='NtbNormalized', resol='thumbnail')
    # Creates STACK_original_image_crop.csv in data directory. x,y,width,height
    #  In this file each row is x,y,width,height in thumbnail resolution.
    command = ['python', 'generate_original_image_crop_csv.py', 'input_spec.ini']
    completion_message = 'Finished generating CSV file.'
    #call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedPadded', version='mask', resol='thumbnail')
    # Transforms generated masks to fit the original image orientations
    command = ['python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', 'from_padded_to_none','--pad_color','black']
    completion_message = 'Transforming masks back into orientation of original raw images finished.'
    #call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='None', version='Ntb', resol='raw')
    # Local adaptive intensity normalization
    command = ['python', 'normalize_intensity_adaptive.py', 'input_spec.ini', 'NtbNormalizedAdaptiveInvertedGamma']
    completion_message = 'Local adaptive intensity normalization finished.'
    call_and_time( command, completion_message=completion_message)
    
if stain == 'Thionin':
    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='None', version='gray', resol='thumbnail')
    # Creates STACK_original_image_crop.csv in data directory. x,y,width,height
    #  In this file each row is x,y,width,height in thumbnail resolution.
    command = ['python', 'generate_original_image_crop_csv.py', 'input_spec.ini']
    completion_message = 'Finished generating CSV file.'
    call_and_time( command, completion_message=completion_message)

    create_input_spec_ini_all( name='input_spec.ini', stack=stack, \
                prep_id='alignedPadded', version='mask', resol='thumbnail')
    # Transforms generated masks to fit the original image orientations
    command = ['python', 'warp_crop_v3.py', '--input_spec', 'input_spec.ini', '--op_id', 'from_padded_to_none','--pad_color','white']
    completion_message = 'Transforming masks back into orientation of original raw images finished.'
    call_and_time( command, completion_message=completion_message)
    
print('\nFinished generating image crop csv file, transformating masks, and performing adaptive intensity normalization on images.')



###################################################################################################
# Running script 5 automatically
###################################################################################################
# The user step is outdated and can be performed automatically here.

# This next line replaces the user step for  manually finding this cropbox
#rostral_lim, caudal_lim, dorsal_lim, ventral_lim = get_prep5_limits_from_prep1_thumbnail_masks(stack)

#command = ['python', 'a_script_preprocess_5.py', stack, stain, '-l', 
#           str(rostral_lim), str(caudal_lim), str(dorsal_lim), str(ventral_lim)]
#call_and_time( command, completion_message='')
