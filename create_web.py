"""
This file does the following operations:
    1. Convert the thumbnails from TIF to PNG format.
    2. Note: only the channel 1 for each animal is needed for PNG format
"""
import argparse
import os
import subprocess

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController


def make_web_thumbnails(animal, channel):
    """
    This was originally getting the thumbnails from the preps/thumbnail dir but they aren't usuable.
    The ones in the preps/CHX/thumbnail_cleaned are much better
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
        njobs: number of jobs for parallel computing

    Returns:
        nothing
    """
    channel_dir = 'CH{}'.format(channel)
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    # test if there ane aligned files, if not use the cleaned ones
    len_files = len(os.listdir(INPUT))
    if len_files < 10:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_cleaned')

    OUTPUT = fileLocationManager.thumbnail_web
    tifs = sqlController.get_sections(animal, channel)

    commands = []
    for i, tif in enumerate(tqdm(tifs)):
        input_path = os.path.join(INPUT, str(i).zfill(3) + '.tif')
        output_path = os.path.join(OUTPUT, os.path.splitext(tif.file_name)[0] + '.png')

        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = "convert {} {}".format(input_path, output_path)
        subprocess.run(cmd, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)

    make_web_thumbnails(animal, channel)
