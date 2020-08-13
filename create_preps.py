"""
This file does the following operations:
    1. Copy TIF full or thumbnails to preps/full or preps/thumbnails folders.
"""
import argparse
import os
import subprocess
from shutil import copyfile
from multiprocessing.pool import Pool

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController


def make_preps(animal, channel, full):
    """
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
        full: whether to copy full or thumbnail directory

    Returns:
        nothing
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    if full:
        INPUT = os.path.join(fileLocationManager.tif)
        OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'full')
    else:
        INPUT = os.path.join(fileLocationManager.thumbnail)
        OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'thumbnail')
    tifs = sqlController.get_sections(animal, channel)
    for section_number, tif in tqdm(enumerate(tifs)):
        input_path = os.path.join(INPUT, tif.file_name)
        output_path = os.path.join(OUTPUT, str(section_number).zfill(3) + '.tif')

        if not os.path.exists(input_path):
            print('Input tif does not exist', input_path)
            continue

        if os.path.exists(output_path):
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if full:
            cmd = ['convert', input_path, '-compress', 'lzw', output_path]
            subprocess.run(cmd)
        else:
            copyfile(input_path, output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=False, default='thumbnail')

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    full = bool({'full': True, 'thumbnail': False}[args.resolution])

    make_preps(animal, channel, full)
