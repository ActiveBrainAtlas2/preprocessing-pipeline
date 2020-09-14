import os
import sys
import ast
import json
from collections import defaultdict

import cv2
import numpy as np
import pandas as pd
import neuroglancer
from tqdm import tqdm
from skimage import io


sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.alignment_utility import SCALING_FACTOR, load_consecutive_section_transform, create_warp_transforms, \
    transform_create_alignment
from utilities.contour_utilities import get_dense_coordinates, get_contours_from_annotations

animal = 'MD589'
sqlController = SqlController(animal)
fileLocationManager = FileLocationManager(animal)
width = sqlController.scan_run.width
height = sqlController.scan_run.height
width = int(width * SCALING_FACTOR)
height = int(height * SCALING_FACTOR)
aligned_shape = np.array((width, height))
THUMBNAIL_PATH = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
THUMBNAILS = sorted(os.listdir(THUMBNAIL_PATH))
num_section = len(THUMBNAILS)
structure_dict = sqlController.get_structures_dict()

CSV_PATH = '/net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations'
csvfile = os.path.join(CSV_PATH, f'{animal}_annotation.csv')
hand_annotations = pd.read_csv(csvfile)
hand_annotations['vertices'] = hand_annotations['vertices'] \
    .apply(lambda x: x.replace(' ', ','))\
    .apply(lambda x: x.replace('\n',','))\
    .apply(lambda x: x.replace(',]',']'))\
    .apply(lambda x: x.replace(',,', ','))\
    .apply(lambda x: x.replace(',,', ','))\
    .apply(lambda x: x.replace(',,', ',')).apply(lambda x: x.replace(',,', ','))
hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))

structures = list(hand_annotations['name'].unique())
section_structure_vertices = defaultdict(dict)
for structure in tqdm(structures):
    contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations, densify=4)
    for section in contour_annotations:
        section_structure_vertices[section][structure] = contour_annotations[section][structure][1]


##### Reproduce create_clean transform
section_offset = {}
for file_name in tqdm(THUMBNAILS):
    filepath = os.path.join(THUMBNAIL_PATH, file_name)
    img = io.imread(filepath)
    section = int(file_name.split('.')[0])
    section_offset[section] = (aligned_shape - img.shape[:2][::-1]) // 2


##### Reproduce create_alignment transform
CLEANED = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_cleaned')

image_name_list = sorted(os.listdir(CLEANED))
anchor_idx = len(image_name_list) // 2
transformation_to_previous_sec = {}

for i in range(1, len(image_name_list)):
    fixed_fn = os.path.splitext(image_name_list[i - 1])[0]
    moving_fn = os.path.splitext(image_name_list[i])[0]
    transformation_to_previous_sec[i] = load_consecutive_section_transform(animal, moving_fn, fixed_fn)

transformation_to_anchor_sec = {}
# Converts every transformation
for moving_idx in range(len(image_name_list)):
    if moving_idx == anchor_idx:
        transformation_to_anchor_sec[image_name_list[moving_idx]] = np.eye(3)
    elif moving_idx < anchor_idx:
        T_composed = np.eye(3)
        for i in range(anchor_idx, moving_idx, -1):
            T_composed = np.dot(np.linalg.inv(transformation_to_previous_sec[i]), T_composed)
        transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed
    else:
        T_composed = np.eye(3)
        for i in range(anchor_idx + 1, moving_idx + 1):
            T_composed = np.dot(transformation_to_previous_sec[i], T_composed)
        transformation_to_anchor_sec[image_name_list[moving_idx]] = T_composed




transforms = transformation_to_anchor_sec
warp_transforms = create_warp_transforms(animal, transforms, 'thumbnail', 'thumbnail')
ordered_transforms = sorted(warp_transforms.items())


section_transform = {}
for section, transform in ordered_transforms:
    section_num = int(section.split('.')[0])
    transform = np.linalg.inv(transform)
    section_transform[section_num] = transform

##### Alignment of annotation coordinates
other_structures = set()
other_color = 255
volume = np.zeros((aligned_shape[1], aligned_shape[0], num_section), dtype=np.uint8)
other_volume = np.zeros((aligned_shape[1], aligned_shape[0], num_section), dtype=np.uint8)
for section in section_structure_vertices:
    template = np.zeros((aligned_shape[1], aligned_shape[0]), dtype=np.uint8)
    for structure in section_structure_vertices[section]:
        points = np.array(section_structure_vertices[section][structure])
        points = points // 32
        points = points + section_offset[section]  # create_clean offset
        points = transform_create_alignment(points, section_transform[section])  # create_alignment transform
        points = points.astype(np.int32)

        try:
            #color = colors[structure.upper()]
            color = structure_dict[structure][1] # structure dict returns a list of [description, color]
            # for each key
        except:
            color = 255
            other_structures.add(structure)

        cv2.polylines(template, [points], True, color, 2, lineType=cv2.LINE_AA)
    volume[:, :, section - 1] = template

print('Other structures')
i = 1
for s in sorted(list(other_structures)):
    print(i,s)
    i += 1

volume_filepath = os.path.join(CSV_PATH, f'{animal}_annotations.npy')
with open(volume_filepath, 'wb') as file:
    np.save(file, volume)
