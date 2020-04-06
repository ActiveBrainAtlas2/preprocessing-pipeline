#! /usr/bin/env python

import sys
import os
import time

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg') # https://stackoverflow.com/a/3054314
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.path.join(os.environ['REPO_DIR'], 'utilities'))
from utilities2015 import *
from registration_utilities import *
from annotation_utilities import *
from metadata import *
from data_manager import *
from learning_utilities import *

import argparse

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='')

parser.add_argument("input_spec", type=str, help="Input image name")
#parser.add_argument("brain_name", type=str, help="Brain name")
#parser.add_argument("--section", type=int, help="Section number. If specified, do detection on this one section; otherwise, use all valid sections.")
#parser.add_argument("--version", type=str, help="Image version")
parser.add_argument("--win_id", type=int, help="Window id (Default: %(default)s).", default=7)
args = parser.parse_args()

input_spec = load_ini(args.input_spec)
stack = input_spec['stack']
prep_id = input_spec['prep_id']
if prep_id == 'None':
    prep_id = None
#resol = input_spec['resol']
version = input_spec['version']
if version == 'None':
    version = None

image_name_list = input_spec['image_name_list']
if image_name_list == 'all':
    image_name_list = DataManager.load_sorted_filenames(stack=stack)[0].keys()

#stack = args.brain_name
#if hasattr(args, 'section') and args.section is not None:
#    sections = [args.section]
#else:
#    sections = metadata_cache['valid_sections'][stack]

win_id = args.win_id
#version = args.version
    
batch_size = 256
model_dir_name = 'inception-bn-blue'
model_name = 'inception-bn-blue'
model, mean_img = load_mxnet_model(model_dir_name=model_dir_name, 
                                   model_name=model_name, 
                                   num_gpus=1, 
                                   batch_size=batch_size)

for image_name in image_name_list:
#for sec in sections:
#for sec in range(220, 260):
#     try:
#         compute_and_save_features_one_section(
#                                 version=version,
# #                                 scheme='normalize_mu_region_sigma_wholeImage_(-1,5)', 
#                                 scheme='none', 
# #                             bbox=(11217, 16886, 13859, 18404),
# #                                 method='glcm',
#                             method='cnn',
#                             win_id=win_id, prep_id=prep_id,
#                             stack=stack, sec=metadata_cache['filenames_to_sections'][stack][image_name], 
#                             model=model, model_name=model_name,
#                              mean_img=mean_img, 
#                              batch_size=batch_size, 
#         attach_timestamp=False, 
#         recompute=True)
#     except Exception as e:
#         sys.stderr.write("Failed to compute and save patch features for image %s: %s\n" % (image_name, e.message))
#         continue

    compute_and_save_features_one_section(
                        version=version,
#                       scheme='normalize_mu_region_sigma_wholeImage_(-1,5)', 
                        scheme='none', 
#                       bbox=(11217, 16886, 13859, 18404),
#                       method='glcm',
                        method='cnn',
                        win_id=win_id, prep_id=prep_id,
                        stack=stack, sec=metadata_cache['filenames_to_sections'][stack][image_name], 
                        model=model, model_name=model_name,
                        mean_img=mean_img, 
                        batch_size=batch_size, 
                        attach_timestamp=False, 
                        recompute=False)