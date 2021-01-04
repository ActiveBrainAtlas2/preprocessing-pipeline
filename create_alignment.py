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
import subprocess
from multiprocessing.pool import Pool
import numpy as np
from collections import OrderedDict
from tqdm import tqdm

from sql_setup import ALIGN_CHANNEL_1_THUMBNAILS_WITH_ELASTIX, ALIGN_CHANNEL_1_FULL_RES, ALIGN_CHANNEL_2_FULL_RES, \
    ALIGN_CHANNEL_3_FULL_RES

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_alignment import (load_consecutive_section_transform,
                                         convert_resolution_string_to_um)
from utilities.utilities_process import workernoshell, workershell, test_dir, SCALING_FACTOR

ELASTIX_BIN = '/usr/bin/elastix'

def run_elastix(animal, njobs):
    """
    Sets up the arguments for running elastix in a sequence. Each file pair
    creates a sub directory with the results. Uses a pool to spawn multiple processes
    Args:
        animal: the animal
        limit:  how many jobs you want to run.
    Returns: nothing, just creates a lot of subdirs in the elastix directory.
    """
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    sqlController.set_task(animal, ALIGN_CHANNEL_1_THUMBNAILS_WITH_ELASTIX)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
    error = test_dir(animal, INPUT, full=False, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    files = sorted(os.listdir(INPUT))
    elastix_output_dir = fileLocationManager.elastix_dir
    os.makedirs(elastix_output_dir, exist_ok=True)

    param_file = os.path.join(os.getcwd(), 'utilities/alignment', "Parameters_Rigid.txt")
    commands = []
    # previous file is the fixed image
    # current file is the moving image
    for i in range(1, len(files)):
        prev_img_name = os.path.splitext(files[i - 1])[0]
        curr_img_name = os.path.splitext(files[i])[0]
        prev_fp = os.path.join(INPUT, files[i - 1])
        curr_fp = os.path.join(INPUT, files[i])

        new_dir = '{}_to_{}'.format(curr_img_name, prev_img_name)
        output_subdir = os.path.join(elastix_output_dir, new_dir)

        if os.path.exists(output_subdir) and 'TransformParameters.0.txt' in os.listdir(output_subdir):
            continue


        command = ['rm', '-rf', output_subdir]
        subprocess.run(command)
        os.makedirs(output_subdir, exist_ok=True)
        cmd = [ELASTIX_BIN, '-f', prev_fp, '-m', curr_fp, '-p', param_file, '-out', output_subdir]
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
    error = test_dir(animal, INPUT, full=False, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    files = sorted(os.listdir(INPUT))
    anchor_index = len(files) // 2
    transformation_to_previous_section = {}

    for i in range(1, len(files)):
        fixed_index = os.path.splitext(files[i - 1])[0]
        moving_index = os.path.splitext(files[i])[0]
        transformation_to_previous_section[i] = load_consecutive_section_transform(animal, moving_index, fixed_index)

    transformation_to_anchor_section = {}
    # Converts every transformation
    for moving_index in range(len(files)):
        if moving_index == anchor_index:
            transformation_to_anchor_section[files[moving_index]] = np.eye(3)
        elif moving_index < anchor_index:
            T_composed = np.eye(3)
            for i in range(anchor_index, moving_index, -1):
                T_composed = np.dot(np.linalg.inv(transformation_to_previous_section[i]), T_composed)
            transformation_to_anchor_section[files[moving_index]] = T_composed
        else:
            T_composed = np.eye(3)
            for i in range(anchor_index + 1, moving_index + 1):
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

def create_warp_transforms(animal, transforms, transforms_resol, resolution):
    """
    Changes the dictionary of transforms to the correct resolution
    :param animal: prep_id of animal we are working on
    :param transforms: dictionary of filename:array of transforms
    :param transforms_resol:
    :param resolution: either full or thumbnail
    :return: corrected dictionary of filename: array  of transforms
    """
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
    error = test_dir(animal, INPUT, full=False, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    bgcolor = 'black'
    stain = sqlController.histology.counterstain
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)

    if 'thion' in stain.lower():
        bgcolor = 'white'

    if 'full' in resolution.lower():
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
        error = test_dir(animal, INPUT, full=True, same_size=True)
        if len(error) > 0:
            print(error)
            sys.exit()
        OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
        max_width = width
        max_height = height
        if channel == 3:
            sqlController.set_task(animal, ALIGN_CHANNEL_3_FULL_RES)
        elif channel == 2:
            sqlController.set_task(animal, ALIGN_CHANNEL_2_FULL_RES)
        else:
            sqlController.set_task(animal, ALIGN_CHANNEL_1_FULL_RES)

    if masks:
        INPUT = os.path.join(fileLocationManager.prep, 'rotated_masked')
        error = test_dir(animal, INPUT, full=False, same_size=True)
        if len(error) > 0:
            print(error)
            sys.exit()
        OUTPUT = os.path.join(fileLocationManager.prep, 'rotated_aligned_masked')
        bgcolor = 'black'

    os.makedirs(OUTPUT, exist_ok=True)

    warp_transforms = create_warp_transforms(animal, transforms, 'thumbnail', resolution)
    ordered_transforms = OrderedDict(sorted(warp_transforms.items()))
    commands = []
    for file, arr in tqdm(ordered_transforms.items()):
        T = np.linalg.inv(arr)
        #op_str = " +distort AffineProjection %(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f " % {
        #    'sx': T[0, 0], 'sy': T[1, 1], 'rx': T[1, 0], 'ry': T[0, 1], 'tx': T[0, 2], 'ty': T[1, 2]}

        #op_str += ' -crop {}x{}+0.0+0.0!'.format(max_width, max_height)

        sx = T[0, 0]
        sy = T[1, 1]
        rx = T[1, 0]
        ry = T[0, 1]
        tx = T[0, 2]
        ty = T[1, 2]
        # sx, rx, ry, sy, tx, ty
        op_str = f" +distort AffineProjection '{sx},{rx},{ry},{sy},{tx},{ty}'"
        op_str += f' -crop {max_width}x{max_height}+0.0+0.0!'

        input_fp = os.path.join(INPUT, file)
        output_fp = os.path.join(OUTPUT, file)
        if os.path.exists(output_fp):
            continue

        #cmd = "convert {}  +repage -virtual-pixel background -background {} {} -flatten -compress lzw {}"\
        #    .format(input_fp, bgcolor, op_str, output_fp)
        cmd = f"convert {input_fp} -define white-point=0x0 +repage -virtual-pixel background -background {bgcolor} {op_str} -flatten -compress lzw {output_fp}"
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workershell, commands)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
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
