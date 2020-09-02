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
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)


from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.alignment_utility import (convert_resolution_string_to_um, SCALING_FACTOR)
from utilities.utilities_process import workernoshell, workershell

ELASTIX_BIN = '/usr/bin/elastix'


def parameter_elastix_parameter_file_to_dict(filename):
    d = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            if line.startswith('('):
                tokens = line[1:-2].split(' ')
                key = tokens[0]
                if len(tokens) > 2:
                    value = []
                    for v in tokens[1:]:
                        try:
                            value.append(float(v))
                        except ValueError:
                            value.append(v)
                else:
                    v = tokens[1]
                    try:
                        value = (float(v))
                    except ValueError:
                        value = v
                d[key] = value
        return d


def load_consecutive_section_transform(stack, moving_fn, fixed_fn, jobname):
    """
    Load pairwise transform.

    Returns:
        (3,3)-array.
    """
    OUTPUT = os.path.join(HOME, 'elastix_test', jobname)
    param_fp = os.path.join(OUTPUT, moving_fn + '_to_' + fixed_fn, 'TransformParameters.0.txt')
    #sys.stderr.write('Load elastix-computed transform: %s\n' % param_fp)
    if not os.path.exists(param_fp):
        raise Exception('Transform file does not exist: %s to %s, %s' % (moving_fn, fixed_fn, param_fp))
    transformation_to_previous_sec = parse_elastix_parameter_file(param_fp)

    return transformation_to_previous_sec


def parse_elastix_parameter_file(filepath):
    """
    Parse elastix parameter result file.
    """

    d = parameter_elastix_parameter_file_to_dict(filepath)

    # For alignment composition script
    rot_rad, x_mm, y_mm = d['TransformParameters']
    center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])
    # center[1] = d['Size'][1] - center[1]

    xshift = x_mm / d['Spacing'][0]
    yshift = y_mm / d['Spacing'][1]

    R = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                  [np.sin(rot_rad), np.cos(rot_rad)]])
    shift = center + (xshift, yshift) - np.dot(R, center)
    T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
    return T


def run_elastix(animal, jobname, tests):
    fileLocationManager = FileLocationManager(animal)
    DIR = fileLocationManager.prep
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
    MASKPATH = os.path.join(fileLocationManager.prep, 'rotated_masked')


    image_name_list = sorted(os.listdir(INPUT))
    mask_name_list = sorted(os.listdir(MASKPATH))
    OUTPUT = os.path.join(HOME, 'elastix_test', jobname)

    midstack = len(image_name_list) // 2
    start, finish = (midstack - tests, midstack + tests)
    image_name_list = image_name_list[start:finish]
    mask_name_list = mask_name_list[start:finish]
    anchor_idx = len(image_name_list) // 2

    os.makedirs(OUTPUT, exist_ok=True)

    param_file = os.path.join(os.getcwd(), "Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt")
    commands = []
    for i in range(1, len(image_name_list)):
        prev_img_name = os.path.splitext(image_name_list[i - 1])[0]
        curr_img_name = os.path.splitext(image_name_list[i])[0]
        prev_fp = os.path.join(INPUT, image_name_list[i - 1])
        curr_fp = os.path.join(INPUT, image_name_list[i])

        prev_mask = os.path.join(MASKPATH, mask_name_list[i - 1])
        curr_mask = os.path.join(MASKPATH, mask_name_list[i])

        new_dir = '{}_to_{}'.format(curr_img_name, prev_img_name)
        output_subdir = os.path.join(OUTPUT, new_dir)

        if os.path.exists(output_subdir) and 'TransformParameters.0.txt' in os.listdir(output_subdir):
            continue


        command = ['rm', '-rf', output_subdir]
        subprocess.run(command)
        os.makedirs(output_subdir, exist_ok=True)
        #cmd = '{} -f {} -m {} -p {} -out {}'.format(ELASTIX_BIN, prev_fp, curr_fp, param_file, )
        cmd = [ELASTIX_BIN, '-f', prev_fp, '-m', curr_fp, '-p', param_file, '-out', output_subdir]
        #cmd = [ELASTIX_BIN, '-f', prev_mask, '-m', curr_mask, '-p', param_file, '-out', output_subdir]
        commands.append(cmd)

    with Pool(10) as p:
        p.map(workernoshell, commands)

    return image_name_list, anchor_idx

def parse_elastix(animal, image_name_list, anchor_idx):
    """
    After the elastix job is done, this goes into each subdirectory and parses the Transformation.0.txt file
    Args:
        animal: the animal
    Returns: a dictionary of key=filename, value = coordinates
    """
    # anchor_idx = len(image_name_list) - 1
    transformation_to_previous_sec = {}

    for i in range(1, len(image_name_list)):
        fixed_fn = os.path.splitext(image_name_list[i - 1])[0]
        moving_fn = os.path.splitext(image_name_list[i])[0]
        transformation_to_previous_sec[i] = load_consecutive_section_transform(animal, moving_fn, fixed_fn, jobname)

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


def run_offsets(animal, transforms, jobname, bgcolor):
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
    channel_dir = 'CH{}'.format(1)
    INPUT = os.path.join(fileLocationManager.prep,  channel_dir, 'thumbnail_cleaned')
    OUTPUT = os.path.join(HOME, 'elastix_test', jobname, 'thumbnail_aligned')
    os.makedirs(OUTPUT, exist_ok=True)
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    max_width = int(width * SCALING_FACTOR)
    max_height = int(height * SCALING_FACTOR)

    warp_transforms = create_warp_transforms(animal, transforms, 'thumbnail', 'thumbnail')
    ordered_transforms = OrderedDict(sorted(warp_transforms.items()))
    commands = []
    for file, arr in tqdm(ordered_transforms.items()):
        T = np.linalg.inv(arr)
        op_str = " +distort AffineProjection %(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f " % {
            'sx': T[0, 0], 'sy': T[1, 1], 'rx': T[1, 0], 'ry': T[0, 1], 'tx': T[0, 2], 'ty': T[1, 2]}

        op_str += ' -crop {}x{}+0.0+0.0!'.format(max_width, max_height)
        input_fp = os.path.join(INPUT, file)
        output_fp = os.path.join(OUTPUT, file)

        if os.path.exists(output_fp):
            continue

        cmd = "convert {}  +repage -virtual-pixel background -background {} {} -flatten -compress lzw {}"\
            .format(input_fp, bgcolor, op_str, output_fp)
        commands.append(cmd)

    with Pool(10) as p:
        p.map(workershell, commands)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--jobname', help='job name', required=True)
    parser.add_argument('--bgcolor', help='Enter color', required=True)
    parser.add_argument('--count', help='Enter test count',default=20, required=False)


    args = parser.parse_args()
    animal = args.animal
    jobname = args.jobname
    bgcolor = args.bgcolor
    count = int(args.count)

    image_name_list, anchor_idx = run_elastix(animal, jobname, count)
    transforms = parse_elastix(animal, image_name_list, anchor_idx)
    run_offsets(animal, transforms, jobname, bgcolor)
