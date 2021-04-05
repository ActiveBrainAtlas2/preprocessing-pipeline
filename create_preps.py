"""
This file does the following operations:
    1. Converts regular filename from main tif dir to CHX/full or
    2. Converts and downsamples CHX/full to CHX/thumbnail
    When creating the full sized images, the LZW compression is used
"""
import argparse
import os
import sys
from multiprocessing.pool import Pool
from tqdm import tqdm
from shutil import copyfile
import imagesize

from sql_setup import CREATE_CHANNEL_1_THUMBNAILS, CREATE_CHANNEL_1_FULL_RES, CREATE_CHANNEL_3_FULL_RES, \
    CREATE_CHANNEL_2_FULL_RES, CREATE_CHANNEL_3_THUMBNAILS, CREATE_CHANNEL_2_THUMBNAILS
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workernoshell, test_dir


def make_full_resolution(animal, channel):
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

    if 'thion' in sqlController.histology.counterstain:
        sqlController.set_task(animal, CREATE_CHANNEL_1_FULL_RES)
        sqlController.set_task(animal, CREATE_CHANNEL_2_FULL_RES)
        sqlController.set_task(animal, CREATE_CHANNEL_3_FULL_RES)

    INPUT = os.path.join(fileLocationManager.tif)
    ##### Check if files in dir are valid
    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'full')
    os.makedirs(OUTPUT, exist_ok=True)

    sections = sqlController.get_sections(animal, channel)
    for section_number, section in enumerate(tqdm(sections)):
        input_path = os.path.join(INPUT, section.file_name)
        output_path = os.path.join(OUTPUT, str(
            section_number).zfill(3) + '.tif')

        if not os.path.exists(input_path):
            #print('Input tif does not exist', input_path)
            continue

        if os.path.exists(output_path):
            continue

        copyfile(input_path, output_path)
        width, height = imagesize.get(input_path)
        sqlController.update_tif(section.id, width, height)


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

    if 'thion' in sqlController.histology.counterstain:
        sqlController.set_task(animal, CREATE_CHANNEL_1_THUMBNAILS)
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
    OUTPUT = os.path.join(fileLocationManager.prep,
                          f'CH{channel}', 'thumbnail')
    os.makedirs(OUTPUT, exist_ok=True)
    tifs = sorted(os.listdir(INPUT))
    for tif in tifs:
        input_path = os.path.join(INPUT, tif)
        output_path = os.path.join(OUTPUT, tif)

        if os.path.exists(output_path):
            continue

        cmd = ['convert', input_path, '-resize',
               '3.125%', '-compress', 'lzw', output_path]
        commands.append(cmd)
    return commands


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument(
        '--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument(
        '--downsample', help='Enter true or false', required=False, default='true')

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    downsample = bool({'true': True, 'false': False}
                      [str(args.downsample).lower()])
    sqlController = SqlController(animal)
    commands = []
    if downsample:
        commands = make_low_resolution(animal, channel)
    else:
        make_full_resolution(animal, channel)
        if channel == 1:
            sqlController.update_scanrun(sqlController.scan_run.id)

    with Pool(4) as p:
        p.map(workernoshell, commands)

    progress_id = sqlController.get_progress_id(downsample, channel, 'TIF')
    if progress_id > 0:
        sqlController.set_task(animal, progress_id)
        print('Finished')
    else:
        print(
            f'Bad progress ID for downsample: {downsample}, channel: {channel}, TIF')
