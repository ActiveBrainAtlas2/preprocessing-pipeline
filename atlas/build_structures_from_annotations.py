import argparse
import os
import sys
import ast
import json
from cloudvolume import CloudVolume
from collections import defaultdict

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm
from skimage import io
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.alignment_utility import SCALING_FACTOR, load_consecutive_section_transform, create_warp_transforms, \
    transform_create_alignment
from utilities.contour_utilities import get_contours_from_annotations


def create_structures(animal):


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
    keys = [k for k in structure_dict.keys()]
    missing_sections = {k:[117] for k in keys}


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


    warp_transforms = create_warp_transforms(animal, transformation_to_anchor_sec, 'thumbnail', 'thumbnail')
    ordered_transforms = sorted(warp_transforms.items())
    section_transform = {}

    for section, transform in ordered_transforms:
        section_num = int(section.split('.')[0])
        transform = np.linalg.inv(transform)
        section_transform[section_num] = transform

    ##### Alignment of annotation coordinates
    keys = [k for k in structure_dict.keys()]
    # Litao, this missing_sections will need to be manually built up from Beth's spreadhsheet
    missing_sections = {k: [117] for k in keys}
    fill_sections = defaultdict(dict)
    other_structures = set()
    volume = np.zeros((aligned_shape[1], aligned_shape[0], num_section), dtype=np.uint8)
    for section in section_structure_vertices:
        template = np.zeros((aligned_shape[1], aligned_shape[0]), dtype=np.uint8)
        for structure in section_structure_vertices[section]:
            points = np.array(section_structure_vertices[section][structure])
            points = points // 32
            points = points + section_offset[section]  # create_clean offset
            points = transform_create_alignment(points, section_transform[section])  # create_alignment transform
            points = points.astype(np.int32)

            try:
                missing_list = missing_sections[structure]
            except:
                missing_list = []

            if section in missing_list:
                fill_sections[structure][section] = points

            try:
                # color = colors[structure.upper()]
                color = structure_dict[structure][1]  # structure dict returns a list of [description, color]
                # for each key
            except:
                color = 255
                other_structures.add(structure)

            cv2.polylines(template, [points], True, color, 2, lineType=cv2.LINE_AA)
        volume[:, :, section - 1] = template

    # fill up missing sections
    template = np.zeros((aligned_shape[1], aligned_shape[0]), dtype=np.uint8)
    for structure, v in fill_sections.items():
        color = structure_dict[structure][1]
        for section, points in v.items():
            cv2.polylines(template, [points], True, color, 2, lineType=cv2.LINE_AA)
            volume[:, :, section] = template
    volume_filepath = os.path.join(CSV_PATH, f'{animal}_annotations.npy')
    with open(volume_filepath, 'wb') as file:
        np.save(file, volume)

    print('Finished going through sections and structures')

    # now use 9-1 notebook to convert to a precomputed.
    # Voxel resolution in nanometer (how much nanometer each element in numpy array represent)
    resol = (14464, 14464, 20000)
    # Voxel offset
    offset = (0, 0, 0)
    # Layer type
    layer_type = 'segmentation'
    # number of channels
    num_channels = 1
    # segmentation properties in the format of [(number1, label1), (number2, label2) ...]
    # where number is an integer that is in the volume and label is a string that describes that segmenetation

    segmentation_properties = [(number, f'{structure}: {label}') for structure, (label, number) in structure_dict.items()]
    extra_structures = ['Pr5', 'VTg', 'DRD', 'IF', 'MPB', 'Op', 'RPC', 'LSO', 'MVe', 'CnF',
                        'pc', 'DTgC', 'LPB', 'Pr5DM', 'DTgP', 'RMC', 'VTA', 'IPC', 'DRI', 'LDTg',
                        'IPA', 'PTg', 'DTg', 'IPL', 'SuVe', 'Sol', 'IPR', '8n', 'Dk', 'IO',
                        'Cb', 'Pr5VL', 'APT', 'Gr', 'RR', 'InC', 'X', 'EW']
    segmentation_properties += [(len(structure_dict) + index + 1, structure) for index, structure in enumerate(extra_structures)]

    precompute_path = f'/net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations/{animal}'
    cloudpath = f'file://{precompute_path}'
    info = CloudVolume.create_new_info(
        num_channels = num_channels,
        layer_type = layer_type,
        data_type = str(volume.dtype), # Channel images might be 'uint8'
        encoding = 'raw', # raw, jpeg, compressed_segmentation, fpzip, kempressed
        resolution = resol, # Voxel scaling, units are in nanometers
        voxel_offset = offset, # x,y,z offset in voxels from the origin
        chunk_size = [64, 64, 64], # units are voxels
        volume_size = volume.shape, # e.g. a cubic millimeter dataset
    )
    vol = CloudVolume(cloudpath, mip=0, info=info, compress=False)
    vol.commit_info()
    vol[:, :, :] = volume[:, :, :]

    vol.info['segment_properties'] = 'names'
    vol.commit_info()

    segment_properties_path = os.path.join(precompute_path, 'names')
    os.makedirs(segment_properties_path, exist_ok=True)

    info = {
        "@type": "neuroglancer_segment_properties",
        "inline": {
            "ids": [str(number) for number, label in segmentation_properties],
            "properties": [{
                "id": "label",
                "description": "Name of structures",
                "type": "label",
                "values": [str(label) for number, label in segmentation_properties]
            }]
        }
    }
    print('Creating names in', segment_properties_path)
    with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
        json.dump(info, file, indent=2)


    tq = LocalTaskQueue(parallel=3)
    tasks = tc.create_downsampling_tasks(cloudpath, compress=False) # Downsample the volumes
    tq.insert(tasks)
    tq.execute()
    print('Finished')
    # delete tasks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_structures(animal)

