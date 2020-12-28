"""
This file does the following operations:
    1. Converts regular filename from main tif dir to CHX/full or
    2. Converts and downsamples CHX/full to CHX/thumbnail
    When creating the full sized images, the LZW compression is used
"""
import argparse
import os, sys
from multiprocessing.pool import Pool
from tqdm import tqdm
from shutil import copyfile

from sql_setup import CREATE_CHANNEL_1_THUMBNAILS, CREATE_CHANNEL_1_FULL_RES, CREATE_CHANNEL_3_FULL_RES, \
    CREATE_CHANNEL_2_FULL_RES, CREATE_CHANNEL_3_THUMBNAILS, CREATE_CHANNEL_2_THUMBNAILS
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workernoshell, test_dir


def make_full_resolution(animal, channel, compress=True):
    """
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
        compress: Use the default LZW compression, otherwise just copy the file with the correct name
    Returns:
        list of commands
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    if channel == 3:
        sqlController.set_task(animal, CREATE_CHANNEL_3_FULL_RES)
    elif channel == 2:
        sqlController.set_task(animal, CREATE_CHANNEL_2_FULL_RES)
    else:
        sqlController.set_task(animal, CREATE_CHANNEL_1_FULL_RES)

    if 'thion' in sqlController.histology.counterstain:
        sqlController.set_task(animal, CREATE_CHANNEL_2_FULL_RES)
        sqlController.set_task(animal, CREATE_CHANNEL_3_FULL_RES)

    commands = []
    INPUT = os.path.join(fileLocationManager.tif)
    ##### Check if files in dir are valid
    error = test_dir(animal, INPUT, full=True, same_size=False)
    if len(error) > 0:
        print(error)
        sys.exit()

    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'full')
    os.makedirs(OUTPUT, exist_ok=True)

    tifs = sqlController.get_sections(animal, channel)
    for section_number, tif in tqdm(enumerate(tifs)):
        input_path = os.path.join(INPUT, tif.file_name)
        output_path = os.path.join(OUTPUT, str(section_number).zfill(3) + '.tif')

        if not os.path.exists(input_path):
            print('Input tif does not exist', input_path)
            continue

        if os.path.exists(output_path):
            continue

        if compress:
            cmd = ['convert', input_path, '-compress', 'lzw', output_path]
            commands.append(cmd)
        else:
            copyfile(input_path, output_path)


    return commands


def make_low_resolution(animal, channel):
    """
    Args:
        takes the full resolution tifs and downsamples them.
        animal: the prep id of the animal
        channel: the channel of the stack to process
    Returns:
        list of commands
    """
    sqlController = SqlController(animal)
    if channel == 3:
        sqlController.set_task(animal, CREATE_CHANNEL_3_THUMBNAILS)
    elif channel == 2:
        sqlController.set_task(animal, CREATE_CHANNEL_2_THUMBNAILS)
    else:
        sqlController.set_task(animal, CREATE_CHANNEL_1_THUMBNAILS)

    if 'thion' in sqlController.histology.counterstain:
        sqlController.set_task(animal, CREATE_CHANNEL_2_THUMBNAILS)
        sqlController.set_task(animal, CREATE_CHANNEL_3_THUMBNAILS)
    fileLocationManager = FileLocationManager(animal)
    commands = []
    INPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'full')
    ##### Check if files in dir are valid
    error = test_dir(animal, INPUT, full=False, same_size=False)
    if len(error) > 0:
        print(error)
        sys.exit()
    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'thumbnail')
    os.makedirs(OUTPUT, exist_ok=True)
    tifs = sorted(os.listdir(INPUT))
    for tif in tqdm(tifs):
        input_path = os.path.join(INPUT, tif)
        output_path = os.path.join(OUTPUT, tif)

        if os.path.exists(output_path):
            continue

        cmd = ['convert', input_path, '-resize', '3.125%', '-compress', 'lzw', output_path]
        commands.append(cmd)
    return commands


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=False, default='thumbnail')
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    parser.add_argument('--compress', help='Compress?', default='true', required=False)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    full = bool({'full': True, 'thumbnail': False}[args.resolution])
    compress = bool({'true': True, 'false': False}[args.compress.lower()])
    njobs = int(args.njobs)

    if full:
        commands = make_full_resolution(animal, channel, compress)
    else:
        commands = make_low_resolution(animal, channel)

    with Pool(njobs) as p:
        p.map(workernoshell, commands)
