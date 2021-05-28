"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs the files in sequence through elastix
    3. parses the results from the elastix output file
    4. Sends those results to the Imagemagick convert program with the correct offsets and crop
    5. The location of elastix is hardcoded below which is a typical linux install location.
"""
import os, sys
import argparse
import numpy as np
import pandas as pd
from collections import OrderedDict
from concurrent.futures.process import ProcessPoolExecutor
from timeit import default_timer as timer

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_alignment import (load_consecutive_section_transform,
                                         convert_resolution_string_to_um, process_image)
from utilities.utilities_process import test_dir, get_cpus, CHUNKSIZE

def parse_elastix(animal):
    """
    After the elastix job is done, this goes into each subdirectory and parses the Transformation.0.txt file
    Args:
        animal: the animal
    Returns: a dictionary of key=filename, value = coordinates
    """
    fileLocationManager = FileLocationManager(animal)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
    error = test_dir(animal, INPUT, downsample=True, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    files = sorted(os.listdir(INPUT))
    midpoint_index = len(files) // 2
    transformation_to_previous_section = {}

    for i in range(1, len(files)):
        fixed_index = os.path.splitext(files[i - 1])[0]
        moving_index = os.path.splitext(files[i])[0]
        transformation_to_previous_section[i] = load_consecutive_section_transform(animal, moving_index, fixed_index)

    transformation_to_anchor_section = {}
    # Converts every transformation
    for moving_index in range(len(files)):
        if moving_index == midpoint_index:
            transformation_to_anchor_section[files[moving_index]] = np.eye(3)
        elif moving_index < midpoint_index:
            T_composed = np.eye(3)
            for i in range(midpoint_index, moving_index, -1):
                T_composed = np.dot(np.linalg.inv(transformation_to_previous_section[i]), T_composed)
            transformation_to_anchor_section[files[moving_index]] = T_composed
        else:
            T_composed = np.eye(3)
            for i in range(midpoint_index + 1, moving_index + 1):
                T_composed = np.dot(transformation_to_previous_section[i], T_composed)
            transformation_to_anchor_section[files[moving_index]] = T_composed


    return transformation_to_anchor_section

def convert_2d_transform_forms(arr):
    """
    Puts array into correct dimensions
    :param arr: array to transform
    :return: corrected array
    """
    return np.vstack([arr, [0,0,1]])

def create_warp_transforms(animal, transforms, transforms_resol, downsample):
    """
    Changes the dictionary of transforms to the correct resolution
    :param animal: prep_id of animal we are working on
    :param transforms: dictionary of filename:array of transforms
    :param transforms_resol:
    :param downsample; either true or false
    :return: corrected dictionary of filename: array  of transforms
    """
    transforms_scale_factor = convert_resolution_string_to_um(animal, downsample=transforms_resol) / convert_resolution_string_to_um(animal, downsample=downsample)
    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])
    transforms_to_anchor = {
        img_name:
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor) for
        img_name, tf in transforms.items()}

    return transforms_to_anchor


def run_offsets(animal, transforms, channel, downsample, masks, create_csv, allen):
    """
    This gets the dictionary from the above method, and uses the coordinates
    to feed into the Imagemagick convert program. This method also uses a Pool to spawn multiple processes.
    Args:
        animal: the animal
        transforms: the dictionary of file, coordinates
        limit: number of jobs
    Returns: nothing
    """
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep,  channel_dir, 'thumbnail_cleaned')
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')

    if not downsample:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
        OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')

    error = test_dir(animal, INPUT, downsample=downsample, same_size=True)
    if len(error) > 0 and not create_csv:
        print(error)
        sys.exit()

    if masks:
        INPUT = os.path.join(fileLocationManager.prep, 'rotated_masked')
        error = test_dir(animal, INPUT, full=False, same_size=True)
        if len(error) > 0:
            print(error)
            sys.exit()
        OUTPUT = os.path.join(fileLocationManager.prep, 'rotated_aligned_masked')

    os.makedirs(OUTPUT, exist_ok=True)
    progress_id = sqlController.get_progress_id(downsample, channel, 'ALIGN')
    sqlController.set_task(animal, progress_id)

    warp_transforms = create_warp_transforms(animal, transforms, 'thumbnail', downsample)
    ordered_transforms = OrderedDict(sorted(warp_transforms.items()))
    file_keys = []
    r90 = np.array([[0,-1,0],[1,0,0],[0,0,1]])
    for i, (file, T) in enumerate(ordered_transforms.items()):
        if allen:
            ROT_DIR = os.path.join(fileLocationManager.root, animal, 'rotations')
            rotfile = file.replace('tif', 'txt')
            rotfile = os.path.join(ROT_DIR, rotfile)
            R_cshl = np.loadtxt(rotfile)
            R_cshl[0,2] = R_cshl[0,2] / 32
            R_cshl[1,2] = R_cshl[1,2] / 32
            R_cshl = R_cshl @ r90
            R_cshl = np.linalg.inv(R_cshl)
            R = T @ R_cshl
        infile = os.path.join(INPUT, file)
        outfile = os.path.join(OUTPUT, file)
        if os.path.exists(outfile) and not create_csv:
            continue

        file_keys.append([i,infile, outfile, T])

    
    if create_csv:
        create_csv_data(animal, file_keys)
    else:
        start = timer()
        workers, _ = get_cpus()
        print(f'Working on {len(file_keys)} files with {workers} cpus')
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(process_image, sorted(file_keys), chunksize=workers*CHUNKSIZE)
            executor.shutdown(wait=True)

        end = timer()
        print(f'Create aligned files took {end - start} seconds')
        # set task as completed


    
    print('Finished')
        


def create_csv_data(animal, file_keys):
    data = []
    for index, infile, outfile, T in file_keys:
        T = np.linalg.inv(T)
        file = os.path.basename(infile)

        data.append({
            'i': index,
            'infile': file,
            'sx': T[0, 0],
            'sy': T[1, 1],
            'rx': T[1, 0],
            'ry': T[0, 1],
            'tx': T[0, 2],
            'ty': T[1, 2],
        })
    df = pd.DataFrame(data)
    df.to_csv(f'/tmp/{animal}.section2sectionalignments.csv', index=False)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--masks', help='Enter True for running masks', required=False, default=False)
    parser.add_argument('--csv', help='Enter true or false', required=False, default='false')
    parser.add_argument('--allen', help='Enter true or false', required=False, default='false')

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    create_csv = bool({'true': True, 'false': False}[str(args.csv).lower()])
    allen = bool({'true': True, 'false': False}[str(args.allen).lower()])
    masks = args.masks

    transforms = parse_elastix(animal)
    run_offsets(animal, transforms, channel, downsample, masks, create_csv, allen)
