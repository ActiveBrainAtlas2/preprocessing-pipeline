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

from utilities.file_location import FileLocationManager
from utilities.utilities_process import workernoshell, test_dir

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



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)

    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)

    run_elastix(animal, njobs)
