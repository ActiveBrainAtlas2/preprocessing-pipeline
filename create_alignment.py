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
from concurrent.futures.process import ProcessPoolExecutor
from timeit import default_timer as timer

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_alignment import (load_consecutive_section_transform,
                                         convert_resolution_string_to_um)
from utilities.utilities_process import workernoshell, test_dir
from utilities.utilities_cvat_neuroglancer import get_cpus

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
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
    error = test_dir(animal, INPUT, downsample=True, same_size=True)
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


def run_offsets(animal, transforms, channel, downsample, njobs, masks):
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

    #error = test_dir(animal, INPUT, downsample=downsample, same_size=True)
    error = ""
    if len(error) > 0:
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

    warp_transforms = create_warp_transforms(animal, transforms, 'thumbnail', downsample)
    ordered_transforms = OrderedDict(sorted(warp_transforms.items()))
    file_keys = []
    for i, (file, T) in enumerate(ordered_transforms.items()):

        infile = os.path.join(INPUT, file)
        outfile = os.path.join(OUTPUT, file)
        if os.path.exists(outfile):
            continue

        file_keys.append([i,infile, outfile, T])
        #process_image([i,infile, outfile, T])

    
    start = timer()
    workers, _ = get_cpus()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(process_image, sorted(file_keys), chunksize=workers)
        executor.shutdown(wait=True)

    end = timer()
    print(f'Create aligned files took {end - start} seconds')
    # set task as completed
    progress_id = sqlController.get_progress_id(downsample, channel, 'ALIGN')
    sqlController.set_task(animal, progress_id)
    
    print('Finished')
        


def process_image(file_key):
    index, infile, outfile, T = file_key
    im1 = Image.open(infile)
    im2 = im1.transform((im1.size), Image.AFFINE, T.flatten()[:6], resample=Image.NEAREST)
    im2.save(outfile, compression=None, quality=100)

    del im1, im2
    return



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--masks', help='Enter True for running masks', required=False, default=False)

    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = args.channel
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    masks = args.masks

    run_elastix(animal, njobs)
    transforms = parse_elastix(animal)
    run_offsets(animal, transforms, channel, downsample, njobs, masks)
