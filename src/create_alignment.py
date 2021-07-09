"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs the files in sequence through elastix
    3. parses the results from the elastix output file
    4. Sends those results to the PIL affine with the rotation and translation matrix
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

from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_alignment import (create_warp_transforms,   parse_elastix, process_image)
from lib.utilities_process import test_dir, get_cpus


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

    warp_transforms = create_warp_transforms(animal, transforms, downsample)
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
            executor.map(process_image, sorted(file_keys))

        end = timer()
        print(f'Create cleaned files took {end - start} seconds total', end="\t")
        if len(file_keys) > 0:
            print(f' { (end - start)/len(file_keys)} per file')
        else:
            print("No files were processed")


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
