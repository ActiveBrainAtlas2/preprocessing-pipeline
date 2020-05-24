"""
This was formerly compose_v3.py
This gets the transformation results from the elastix output.
"""
import os
import sys
import argparse
import numpy as np

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import load_consecutive_section_transform, dict_to_csv
from utilities.file_location import FileLocationManager


def setup(stack):
    fileLocationManager = FileLocationManager(stack)
    filepath = fileLocationManager.masked
    image_name_list = sorted(os.listdir(filepath))
    midpoint = len(image_name_list) // 2
    toanchor_transforms_fp = os.path.join(fileLocationManager.brain_info,  'transforms_to_anchor.csv')
    anchor_idx = midpoint
    transformation_to_previous_sec = {}

    for i in range(1, len(image_name_list)):
        transformation_to_previous_sec[i] = load_consecutive_section_transform(moving_fn=image_name_list[i],
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
