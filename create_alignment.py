"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs the files in sequence through elastix
    3. parses the results from the elastix output file
    4. Sends those results to the Imagemagick convert program with the correct offsets and crop
"""
import os, sys
import argparse
import subprocess
from multiprocessing.pool import Pool
import numpy as np
from collections import OrderedDict
from tqdm import tqdm

from sql_setup import ALIGN_CHANNEL_1_THUMBNAILS_WITH_ELASTIX, ALIGN_CHANNEL_1_FULL_RES, ALIGN_CHANNEL_2_FULL_RES, \
    ALIGN_CHANNEL_3_FULL_RES

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.alignment_utility import (create_if_not_exists, load_consecutive_section_transform,
                                         convert_resolution_string_to_um, SCALING_FACTOR)
from utilities.utilities_process import workernoshell

ELASTIX_BIN = '/usr/bin/elastix'

def run_elastix(animal, njobs):
    """
    Sets up the arguments for running elastix in a sequence. Each file pair
    creates a sub directory with the results. Uses a pool to spawn multiple processes
    Args:
        animal: the animal
        limit:  how many jobs you want to run.
    Returns: nothing, just creates a lot of subdirs
    """
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    sqlController.set_task(animal, ALIGN_CHANNEL_1_THUMBNAILS_WITH_ELASTIX)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')

    image_name_list = sorted(os.listdir(INPUT))
    elastix_output_dir = fileLocationManager.elastix_dir

    os.makedirs(elastix_output_dir, exist_ok=True)

    param_file = os.path.join(os.getcwd(), 'alignment', "Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt")
    commands = []
    for i in range(1, len(image_name_list)):
        prev_img_name = os.path.splitext(image_name_list[i - 1])[0]
        curr_img_name = os.path.splitext(image_name_list[i])[0]
        prev_fp = os.path.join(INPUT, image_name_list[i - 1])
        curr_fp = os.path.join(INPUT, image_name_list[i])

        new_dir = '{}_to_{}'.format(curr_img_name, prev_img_name)
        output_subdir = os.path.join(elastix_output_dir, new_dir)

        if os.path.exists(output_subdir) and 'TransformParameters.0.txt' in os.listdir(output_subdir):
            continue


        command = ['rm', '-rf', output_subdir]
        subprocess.run(command)
        create_if_not_exists(output_subdir)
        param_fp = os.path.join(os.getcwd(), param_file)
        cmd = [ELASTIX_BIN, '-f', prev_fp, '-m', curr_fp, '-p', param_fp, '-out', elastix_output_dir]
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workernoshell, commands)


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

    image_name_list = sorted(os.listdir(INPUT))
    midpoint = len(image_name_list) // 2
    anchor_idx = midpoint
    # anchor_idx = len(image_name_list) - 1
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


    return transformation_to_anchor_sec

def convert_2d_transform_forms(arr):
    return np.vstack([arr, [0,0,1]])

def create_warp_transforms(animal, transforms, transforms_resol, resolution):
    #transforms_resol = op['resolution']
    transforms_scale_factor = convert_resolution_string_to_um(animal, resolution=transforms_resol) / convert_resolution_string_to_um(animal, resolution=resolution)
    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])
    transforms_to_anchor = {
        img_name:
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor) for
        img_name, tf in transforms.items()}

    return transforms_to_anchor


def run_offsets(animal, transforms, channel, resolution, njobs, masks):
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
    bgcolor = '#000000'
    stain = sqlController.histology.counterstain
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)

    if 'thion' in stain.lower():
        bgcolor = '#E6E6E6'

    if 'full' in resolution.lower():
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
        OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
        max_width = width
        max_height = height
        if channel == 1:
            sqlController.set_task(animal, ALIGN_CHANNEL_1_FULL_RES)
        elif channel == 2:
            sqlController.set_task(animal, ALIGN_CHANNEL_2_FULL_RES)
        else:
            sqlController.set_task(animal, ALIGN_CHANNEL_3_FULL_RES)

    if masks:
        INPUT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/{}/prealigned'.format(animal)
        OUTPUT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/{}/aligned'.format(animal)
        bgcolor = '#000000'

    warp_transforms = create_warp_transforms(animal, transforms, 'thumbnail', resolution)
    ordered_transforms = OrderedDict(sorted(warp_transforms.items()))
    commands = []
    for file, arr in tqdm(ordered_transforms.items()):
        T = np.linalg.inv(arr)
        op_str = " +distort AffineProjection '%(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f' " % {
            'sx': T[0, 0], 'sy': T[1, 1], 'rx': T[1, 0], 'ry': T[0, 1], 'tx': T[0, 2], 'ty': T[1, 2]}

        op_str += ' -crop {}x{}+0.0+0.0\!'.format(max_width, max_height)

        input_fp = os.path.join(INPUT, file)
        output_fp = os.path.join(OUTPUT, file)

        if os.path.exists(output_fp):
            continue

        cmd = "convert {}  +repage -virtual-pixel background -background \"{}\" {} -flatten -compress lzw {}"\
            .format(input_fp, bgcolor, op_str, output_fp)
        bgcolor = '\"{}\"'.format(bgcolor)

        cmd = ['convert', input_fp, '+regpage', '-virtual-pixel', 'background', '-background',
               bgcolor, op_str, '-flatten', '-compress', 'lzw', output_fp]
        print(" ".join(cmd))
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workernoshell, commands)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--resolution', help='full or thumbnail', required=False, default='thumbnail')
    parser.add_argument('--masks', help='Enter True for running masks', required=False, default=False)
    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = args.channel
    resolution = args.resolution
    masks = args.masks
    run_elastix(animal, njobs)
    transforms = parse_elastix(animal)
    run_offsets(animal, transforms, channel, resolution, njobs, masks)
