# Add all annotated brains to the viewer
import argparse
from collections import defaultdict, OrderedDict
import os, sys

import imagesize
import numpy as np
from scipy import ndimage
import pandas as pd
import ast
from tqdm import tqdm


HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.atlas.utilities_contour import get_contours_from_annotations, create_volume
from utilities.sqlcontroller import SqlController
from utilities.file_location import DATA_PATH, FileLocationManager
from utilities.utilities_neuroglancer import xy_neuroglancer2atlas, section_neuroglancer2atlas
from utilities.utilities_alignment import parse_elastix, transform_create_alignment

DOWNSAMPLE_FACTOR = 1


def create_clean_transform(animal):
    sqlController = SqlController(animal)
    aligned_shape = np.array((sqlController.scan_run.width, sqlController.scan_run.height))
    downsampled_aligned_shape = np.round(aligned_shape / DOWNSAMPLE_FACTOR).astype(int)
    fileLocationManager = FileLocationManager(animal)
    IMAGE_DIR_PATH = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail')
    files = sorted(os.listdir(IMAGE_DIR_PATH))
    section_offset = {}
    for file_name in tqdm(files):
        filepath = os.path.join(IMAGE_DIR_PATH, file_name)

        # Use imread is too slow for full res images
        width, height = imagesize.get(filepath)
        downsampled_shape = np.round(np.array((width*32, height*32)) / DOWNSAMPLE_FACTOR)

        section = int(file_name.split('.')[0])
        section_offset[section] = (downsampled_aligned_shape - downsampled_shape) // 2
    return section_offset

def save_volume_origin(animal, structure, volume, xyz_offsets):
    x, y, z = xyz_offsets
    x = xy_neuroglancer2atlas(x)
    y = xy_neuroglancer2atlas(y)
    origin = [x,y,z]
    atlas_name = 'atlasV9'
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
    #csvfile = os.path.join(DATA_PATH, 'atlas_data', f'{animal}_corrected_vertices.csv')
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
            points = np.array(section_structure_vertices[section][structure]) // DOWNSAMPLE_FACTOR
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
        x = xy_neuroglancer2atlas(x)
        y = xy_neuroglancer2atlas(y)
        z = section_neuroglancer2atlas(z)
        print(structure, volume.shape, x,y,z, xyz_offsets)
        save_volume_origin(animal, structure, volume, xyz_offsets)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_volumes(animal, create)
