"""
This gets the CSV data of the 3 foundation brains' annotations.
These annotations were done by Lauren, Beth, Yuncong and Harvey
(i'm not positive about this)
The annotations are full scale vertices.
"""
import argparse
from collections import defaultdict
import os
import sys
import numpy as np
import pandas as pd
import ast
from tqdm import tqdm
from abakit.utilities.shell_tools import get_image_size
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
from lib.utilities_contour import get_contours_from_annotations, create_volume
from lib.sqlcontroller import SqlController
from lib.file_location import DATA_PATH, FileLocationManager
from lib.utilities_alignment import parse_elastix, \
    transform_create_alignment, create_warp_transforms
from lib.utilities_atlas import ATLAS

DOWNSAMPLE_FACTOR = 1

def draw_numpy(section_structure_polygons, section_start, section_end):
    volume = np.zeros((downsampled_aligned_shape[1], downsampled_aligned_shape[0], section_end - section_start), dtype=np.uint8)
    for section in tqdm(range(section_start, section_end)):
        if section in section_structure_polygons:
            template = np.zeros((downsampled_aligned_shape[1], downsampled_aligned_shape[0]), dtype=np.uint8)
            for structure in section_structure_polygons[section]:
                polygons = section_structure_polygons[section][structure]
                for polygon in polygons:
                    #color = get_structure_number(structure)
                    color = 10
#                     cv2.polylines(template, [polygon.astype(np.int32)], True, color, 1)
                    for point in polygon:
                        cv2.circle(template, tuple(point.astype(np.int32)), 0, color, -1)

            volume[:, :, section - section_start - 1] = template
        
    volume = np.swapaxes(volume, 0, 1)
    return volume




def save_volume_origin(atlas_name, animal, structure, volume, xyz_offsets):
    x, y, z = xyz_offsets
    x = xy_neuroglancer2atlas(x)
    y = xy_neuroglancer2atlas(y)
    z = section_neuroglancer2atlas(z)
    origin = [x, y, z]
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


def create_volumes(animal, create):

    sqlController = SqlController(animal)
    aligned_annotations = pd.read_csv(csvfile)


    hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))
    structures = sqlController.get_structures_dict()
    for structure, values in structures.items():
        contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations, densify=0)
        for section in contour_annotations:
            section_structure_vertices[section][structure] = contour_annotations[section][structure]


def create_numpy_volume(contour_annotations, structure):
    volume = []
    for section in list(contour_annotations.keys())[:2]:
        print(section)
        vertices = np.array(contour_annotations[section][structure])
        print(vertices.shape)
        vertices = (vertices * 460) / 452

        volume_slice = np.zeros(PADDED_SIZE, dtype=np.uint8)
        points = (vertices + np.array(original_offsets[section])).astype(np.int32)
        volume_slice = cv2.polylines(volume_slice, [points], True, 1, 10, lineType=cv2.LINE_AA)
        volume.append(volume_slice)

    volume = np.array(volume).sum(axis=0)
    return volume


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
