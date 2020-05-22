"""
This was formerly compose_v3.py
"""
import os
import sys
import argparse


sys.path.append(os.environ['REPO_DIR'] + '/utilities/')
from metadata import *
from preprocess_utilities import *
from data_manager import DataManager

def setup(stack):
    filepath = '/mnt/data/CSHL_data_processed/{}/thumbnail'.format(stack)
    image_name_list = sorted(os.listdir(filepath))
    midpoint = len(image_name_list) // 2
    toanchor_transforms_fp = '/mnt/data/CSHL_data_processed/{}/transforms_to_anchor.csv'.format(stack)
    anchor_idx = midpoint
    transformation_to_previous_sec = {}

    for i in range(1, len(image_name_list)):
        transformation_to_previous_sec[i] = DataManager.load_consecutive_section_transform(moving_fn=image_name_list[i],
                                                                                           fixed_fn=image_name_list[i - 1],
                                                                                           stack=stack)
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

        print(moving_idx, image_name_list[moving_idx], transformation_to_anchor_sec[image_name_list[moving_idx]])

    dict_to_csv(transformation_to_anchor_sec, toanchor_transforms_fp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    setup(animal)
