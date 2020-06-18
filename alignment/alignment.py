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

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager
from utilities.alignment_utility import create_if_not_exists, load_consecutive_section_transform, convert_cropbox_fmt, \
    convert_resolution_string_to_um

ELASTIX_BIN = '/usr/bin/elastix'


def workershell(cmd):
    """
    Set up an shell command. That is what the shell true is for.
    Args:
        cmd:  a command line program with arguments in a string
    Returns: nothing
    """
    stderr_template = os.path.join(os.getcwd(), 'alignment.err.log')
    stdout_template = os.path.join(os.getcwd(), 'alignment.log')
    stdout_f = open(stdout_template, "w")
    stderr_f = open(stderr_template, "w")
    p = subprocess.Popen(cmd, shell=True, stderr=stderr_f, stdout=stdout_f)
    p.wait()


def run_elastix(stack, limit):
    """
    Sets up the arguments for running elastix in a sequence. Each file pair
    creates a sub directory with the results. Uses a pool to spawn multiple processes
    Args:
        stack: the animal
        limit:  how many jobs you want to run.
    Returns: nothing, just creates a lot of subdirs
    """
    fileLocationManager = FileLocationManager(stack)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'cleaned')

    image_name_list = sorted(os.listdir(INPUT))
    elastix_output_dir = fileLocationManager.elastix_dir
    param_file = "Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt"
    commands = []
    for i in range(1, len(image_name_list)):
        prev_img_name = os.path.splitext(image_name_list[i - 1])[0]
        curr_img_name = os.path.splitext(image_name_list[i])[0]
        prev_fp = os.path.join(INPUT, image_name_list[i - 1])
        curr_fp = os.path.join(INPUT, image_name_list[i])

        new_dir = '{}_to_{}'.format(curr_img_name, prev_img_name)
        output_subdir = os.path.join(elastix_output_dir, new_dir)

        if os.path.exists(output_subdir) and 'TransformParameters.0.txt' in os.listdir(output_subdir):
            # print('{} to {} already exists and so skipping.'.format(curr_img_name, prev_img_name))
            continue


        command = ['rm', '-rf', output_subdir]
        subprocess.run(command)
        create_if_not_exists(output_subdir)
        param_fp = os.path.join(os.getcwd(), param_file)
        command = '{} -f {} -m {} -p {} -out {}'\
            .format(ELASTIX_BIN, prev_fp, curr_fp, param_fp, output_subdir)
        commands.append(command)

    with Pool(limit) as p:
        p.map(workershell, commands)


def parse_elastix(stack):
    """
    After the elastix job is done, this goes into each subdirectory and parses the Transformation.0.txt file
    Args:
        stack: the animal
    Returns: a dictionary of key=filename, value = coordinates
    """
    fileLocationManager = FileLocationManager(stack)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'cleaned')

    image_name_list = sorted(os.listdir(INPUT))
    midpoint = len(image_name_list) // 2
    anchor_idx = midpoint
    # anchor_idx = len(image_name_list) - 1
    transformation_to_previous_sec = {}

    for i in range(1, len(image_name_list)):
        fixed_fn = os.path.splitext(image_name_list[i - 1])[0]
        moving_fn = os.path.splitext(image_name_list[i])[0]
        transformation_to_previous_sec[i] = load_consecutive_section_transform(stack, moving_fn, fixed_fn)

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

def create_warp_transforms(stack, transforms, transforms_resol, resol):
    #transforms_resol = op['resolution']
    transforms_scale_factor = convert_resolution_string_to_um(stack, resolution=transforms_resol) / convert_resolution_string_to_um(stack, resolution=resol)
    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])
    transforms_to_anchor = {
        img_name:
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor) for
        img_name, tf in transforms.items()}

    return transforms_to_anchor


def run_offsets(stack, transforms, channel, bgcolor):
    """
    This gets the dictionary from the above method, and uses the coordinates
    to feed into the Imagemagick convert program. This method also uses a Pool to spawn multiple processes.
    Args:
        stack: the animal
        transforms: the dictionary of file, coordinates
        limit: number of jobs
    Returns: nothing
    """
    channel_dir = 'CH{}'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps'.format(animal)
    INPUT = os.path.join(DIR,  channel_dir, 'cleaned')
    OUTPUT = os.path.join(DIR, channel_dir, 'aligned')

    warp_transforms = create_warp_transforms(stack, transforms, 'thumbnail', 'thumbnail')
    ordered_transforms = OrderedDict(sorted(warp_transforms.items()))
    for file, arr in tqdm(ordered_transforms.items()):
        T = np.linalg.inv(arr)
        op_str = " +distort AffineProjection '%(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f' " % {
            'sx': T[0, 0], 'sy': T[1, 1], 'rx': T[1, 0], 'ry': T[0, 1], 'tx': T[0, 2], 'ty': T[1, 2]}

        max_width = 1400
        max_height = 900
        op_str += ' -crop {}x{}+0.0+0.0\!'.format(max_width, max_height)

        input_fp = os.path.join(INPUT, file)
        output_fp = os.path.join(OUTPUT, file)
        cmd = "convert %(input_fp)s  +repage -virtual-pixel background -background %(bg_color)s %(op_str)s -flatten -compress lzw \"%(output_fp)s\"" % \
                {'op_str': op_str, 'input_fp': input_fp, 'output_fp': output_fp, 'bg_color': bgcolor}

        stderr_template = os.path.join(os.getcwd(), 'alignment.err.log')
        stdout_template = os.path.join(os.getcwd(), 'alignment.log')
        stdout_f = open(stdout_template, "w")
        stderr_f = open(stderr_template, "w")
        p = subprocess.Popen(cmd, shell=True, stderr=stderr_f, stdout=stdout_f)
        p.wait()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--color', help='Enter background color', required=True)
    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = args.channel
    bgcolor = args.color
    run_elastix(animal, njobs)
    transforms = parse_elastix(animal)
    run_offsets(animal, transforms, channel, bgcolor)
