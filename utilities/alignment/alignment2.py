"""
This was formerly compose_v3.py
"""
import os
import sys


sys.path.append(os.environ['REPO_DIR'] + '/utilities/')
from metadata import *
from preprocess_utilities import *
from data_manager import DataManager


stack = 'DK43'
prep_id = None
resol = 'thumbnail'
version = 'NtbNormalized'
filepath = os.path.join('/mnt/data/CSHL_data_processed/DK43/DK43_thumbnail_NtbNormalized')
image_name_list = sorted(os.listdir(filepath))
midpoint = len(image_name_list) // 2
elastix_output_dir = "/mnt/data/CSHL_data_processed/DK43/DK43_elastix_output"

custom_output_dir = '/mnt/data/CSHL_data_processed/DK43/DK43_custom_output'
toanchor_transforms_fp = '/mnt/data/CSHL_data_processed/DK43/DK43_transforms_to_anchor.csv'
anchor_img_name = image_name_list[midpoint]
base_prep_id = None
anchor_idx = midpoint


#################################################


transformation_to_previous_sec = {}

for i in range(1, len(image_name_list)):
    transformation_to_previous_sec[i] = DataManager.load_consecutive_section_transform(moving_fn=image_name_list[i],
                                                                                       fixed_fn=image_name_list[i - 1],
                                                                                       stack=stack)
    # transformation_to_previous_sec[i] = DataManager.load_consecutive_section_transform(moving_fn=image_name_list[i], fixed_fn=image_name_list[i-1], elastix_output_dir=elastix_output_dir, custom_output_dir=custom_output_dir)

transformation_to_anchor_sec = {}

# Converts every transformation
for moving_idx in range(len(image_name_list)):

    if moving_idx == anchor_idx:
        # transformation_to_anchor_sec[moving_idx] = np.eye(3)
        transformation_to_anchor_sec[image_name_list[moving_idx]] = np.eye(3)

    elif moving_idx < anchor_idx:
        T_composed = np.eye(3)
        for i in range(anchor_idx, moving_idx, -1):
            T_composed = np.dot(np.linalg.inv(transformation_to_previous_sec[i]), T_composed)
        # transformation_to_anchor_sec[moving_idx] = T_composed
        transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed

    else:
        T_composed = np.eye(3)
        for i in range(anchor_idx + 1, moving_idx + 1):
            T_composed = np.dot(transformation_to_previous_sec[i], T_composed)
        # transformation_to_anchor_sec[moving_idx] = T_composed
        transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed

    print
    moving_idx, image_name_list[moving_idx], transformation_to_anchor_sec[image_name_list[moving_idx]]

#################################################

dict_to_csv(transformation_to_anchor_sec, toanchor_transforms_fp)
