"""
This gets the CSV data of the 3 foundation brains' annotations.
These annotations were done by Lauren, Beth, Yuncong and Harvey (i'm not positive about this)
The annotations are full scale vertices.
"""
import argparse
from collections import defaultdict
import os, sys

import numpy as np
import pandas as pd
import ast
from tqdm import tqdm


HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)

from lib.utilities_contour import get_contours_from_annotations, create_volume
from lib.sqlcontroller import SqlController
from lib.file_location import DATA_PATH, FileLocationManager
from lib.utilities_alignment import parse_elastix, transform_create_alignment
from lib.utilities_atlas import ATLAS
from abakit.utilities.shell_tools import get_image_size


DOWNSAMPLE_FACTOR = 32

def create_clean_transform(animal):
    sqlController = SqlController(animal)
    fixed_width = sqlController.scan_run.width
    fixed_height = sqlController.scan_run.height
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    files = sorted(os.listdir(INPUT))
    section_offset = {}
    for file_name in tqdm(files):
        filepath = os.path.join(INPUT, file_name)

        # Use imread is too slow for full res images
        width, height = get_image_size(filepath)
        xshift = (int(fixed_width) - int(height)) / 2 
        yshift = (int(fixed_height) - int(width)) / 2
        shifts = np.array([xshift, yshift])
        section = int(file_name.split('.')[0])
        section_offset[section] = shifts
    return section_offset

def save_volume_origin(atlas_name, animal, structure, volume, xyz_offsets):
    x, y, z = xyz_offsets
    x = xy_neuroglancer2atlas(x)
    y = xy_neuroglancer2atlas(y)
    z = section_neuroglancer2atlas(z)

    origin = [x,y,z]
    volume = np.swapaxes(volume, 0, 2)
    volume = np.rot90(volume, axes=(0, 1))
    volume = np.flip(volume, axis=0)
    OUTPUT_DIR = os.path.join(DATA_PATH, 'atlas_data', atlas_name, animal)
    volume_filepath = os.path.join(OUTPUT_DIR, 'structure', f'{structure}.npy')
    os.makedirs(os.path.join(OUTPUT_DIR, 'structure'), exist_ok=True)
    np.save(volume_filepath, volume)
    origin_filepath = os.path.join(OUTPUT_DIR, 'origin', f'{structure}.txt')
    os.makedirs(os.path.join(OUTPUT_DIR, 'origin'), exist_ok=True)
    np.savetxt(origin_filepath, origin)


def create_warp_transforms(transforms, downsample_factor=32):
    def convert_2d_transform_forms(arr):
        return np.vstack([arr, [0, 0, 1]])

    transforms_scale_factor = 32 / downsample_factor
    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])
    transforms_to_anchor = {}
    for img_name, tf in transforms.items():
        transforms_to_anchor[img_name] = convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor)

    return transforms_to_anchor


def create_volumes(animal, create):

    sqlController = SqlController(animal)
    section_structure_vertices = defaultdict(dict)
    csvfile = os.path.join(DATA_PATH, 'atlas_data/foundation_brain_annotations',  f'{animal}_annotation.csv')
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
        contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations, densify=4)
        for section in contour_annotations:
            section_structure_vertices[section][structure] = contour_annotations[section][structure]

    section_offset = create_clean_transform(animal)

    transforms = parse_elastix(animal)
    warp_transforms = create_warp_transforms(transforms, DOWNSAMPLE_FACTOR)
    ordered_transforms = sorted(warp_transforms.items())

    section_transform = {}
    for section, transform in ordered_transforms:
        section_num = int(section.split('.')[0])
        transform = np.linalg.inv(transform)
        section_transform[section_num] = transform

    aligned_section_structure_polygons = defaultdict(dict)
    for section in section_structure_vertices:
        for structure in section_structure_vertices[section]:
            #points = np.array(section_structure_vertices[section][structure]) // DOWNSAMPLE_FACTOR
            points = np.array(section_structure_vertices[section][structure]) 
            points = points + section_offset[section]  # create_clean offset
            points = transform_create_alignment(points, section_transform[section])  # create_alignment transform
            aligned_section_structure_polygons[section][structure] = points



    structure_section_vertices = defaultdict(dict)

    for section,v in aligned_section_structure_polygons.items():
        for structure, vertices in v.items():
            structure_section_vertices[structure][section] = vertices


    for structure, values in structures.items():
        color = values[1]
        try:
            volume, xyz_offsets = create_volume(structure_section_vertices[structure], structure, color)
        except Exception as e:
            print(structure, e)
            continue
        x,y,z = xyz_offsets
        #x = xy_neuroglancer2atlas(x)
        #y = xy_neuroglancer2atlas(y)
        #z = section_neuroglancer2atlas(z)
        print(animal, structure, volume.shape, x,y,z)
        if create:
            save_volume_origin(ATLAS, animal, structure, volume, xyz_offsets)

def xy_neuroglancer2atlas(xy_neuroglancer):
    """
    TODO
    0.325 is the scale for Neurotrace brains
    This converts the atlas coordinates to neuroglancer XY coordinates
    :param x: x or y coordinate
    :return: rounded xy integer that is in atlas scale
    """
    COL_LENGTH = 1000
    ATLAS_RAW_SCALE = 10

    atlas_box_center = COL_LENGTH / 2
    xy_atlas = (xy_neuroglancer - atlas_box_center) / (ATLAS_RAW_SCALE / 0.452)
    return xy_atlas


def section_neuroglancer2atlas(section):
    """
    TODO
    scales the z (section) to atlas coordinates
    :param section:
    :return: rounded integer of section in atlas coordinates
    """
    Z_LENGTH = 300
    ATLAS_Z_BOX_SCALE = 20
    ATLAS_RAW_SCALE = 10
    atlas_box_center = Z_LENGTH / 2
    result = atlas_box_center + section * ATLAS_RAW_SCALE/ATLAS_Z_BOX_SCALE
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=False)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    if animal is None:
        animals = ['MD585', 'MD589', 'MD594']
    else:
        animals = [animal]

    for animal in animals:
        create_volumes(animal, create)

