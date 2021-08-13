"""
This gets the CSV data of the 3 foundation brains' annotations.
These annotations were done by Lauren, Beth, Yuncong and Harvey
(i'm not positive about this)
The annotations are full scale vertices.
MD585 section 160,181,222,230,252 annotations are too far south
MD589 section 296 too far north
MD594 all good
"""
import argparse
from collections import defaultdict
import os
import sys
import numpy as np
import pandas as pd
import ast
import json
from tqdm import tqdm
from abakit.utilities.shell_tools import get_image_size
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
from lib.utilities_contour import get_contours_from_annotations
from lib.sqlcontroller import SqlController
from lib.file_location import DATA_PATH, FileLocationManager
from lib.utilities_alignment import parse_elastix, \
    transform_create_alignment, create_warp_transforms
from lib.utilities_atlas import ATLAS

DOWNSAMPLE_FACTOR = 32


def create_clean_transform(animal):
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    aligned_shape = np.array((sqlController.scan_run.width, 
                              sqlController.scan_run.height))
    downsampled_aligned_shape = np.round(aligned_shape / DOWNSAMPLE_FACTOR).astype(int)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    files = sorted(os.listdir(INPUT))
    section_offsets = {}
    for file in tqdm(files):
        filepath = os.path.join(INPUT, file)
        width, height = get_image_size(filepath)
        width = int(width)
        height = int(height)
        downsampled_shape = np.array((width, height))
        section = int(file.split('.')[0])
        section_offsets[section] = (downsampled_aligned_shape - downsampled_shape) / 2
    return section_offsets


def create_volumes(animal):

    sqlController = SqlController(animal)
    section_offsets = create_clean_transform(animal)
    transforms = parse_elastix(animal)
    warp_transforms = create_warp_transforms(animal, transforms, downsample=True)
    ordered_transforms = sorted(warp_transforms.items())
    section_structure_vertices = defaultdict(dict)
    csvfile = os.path.join(DATA_PATH, 'atlas_data/foundation_brain_annotations',\
        f'{animal}_annotation.csv')
    hand_annotations = pd.read_csv(csvfile)
    hand_annotations['vertices'] = hand_annotations['vertices'] \
        .apply(lambda x: x.replace(' ', ',')) \
        .apply(lambda x: x.replace('\n', ',')) \
        .apply(lambda x: x.replace(',]', ']')) \
        .apply(lambda x: x.replace(',,', ',')) \
        .apply(lambda x: x.replace(',,', ',')) \
        .apply(lambda x: x.replace(',,', ',')).apply(lambda x: x.replace(',,', ','))

    hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))
    structures = sqlController.get_structures_dict()
    for structure, values in structures.items():
        contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations, densify=0)
        for section in contour_annotations:
            section_structure_vertices[section][structure] = contour_annotations[section][structure]

    section_transform = {}
    for section, transform in ordered_transforms:
        section_num = int(section.split('.')[0])
        transform = np.linalg.inv(transform)
        section_transform[section_num] = transform

    aligned_structures = defaultdict(dict)
    for section in section_structure_vertices:
        section = int(section)
        for structure in section_structure_vertices[section]:
            points = np.array(section_structure_vertices[section][structure]) / DOWNSAMPLE_FACTOR
            points = points + section_offsets[section]  # create_clean offset
            points = transform_create_alignment(points, section_transform[section])  # create_alignment transform
            aligned_structures[structure][section] = points.tolist()
            
                            
    OUTPUT_DIR = os.path.join(DATA_PATH, 'atlas_data', ATLAS, animal)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    jsonpath = os.path.join(OUTPUT_DIR,  'aligned_structure_sections.json')
    with open(jsonpath, 'w') as f:
        json.dump(aligned_structures, f, sort_keys=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=False)
    args = parser.parse_args()
    animal = args.animal
    if animal is None:
        animals = ['MD585', 'MD589', 'MD594']
    else:
        animals = [animal]

    for animal in animals:
        create_volumes(animal)
