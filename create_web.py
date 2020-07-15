"""
This file does the following operations:
    1. Convert the thumbnails from TIF to PNG format.
    2. Note: only the channel 1 for each animal is needed for PNG format
"""
import argparse
import os
from multiprocessing.pool import Pool

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workershell


def make_web_thumbnails(animal, channel, njobs):
    """
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
        njobs: number of jobs for parallel computing

    Returns:
        nothing
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = os.path.join(fileLocationManager.thumbnail)
    OUTPUT = os.path.join(fileLocationManager.thumbnail_web)
    tifs = sqlController.get_sections(animal, channel)

    commands = []
    for tif in tqdm(tifs):
        input_path = os.path.join(INPUT, tif.file_name)
        output_path = os.path.join(OUTPUT, os.path.splitext(tif.file_name)[0] + '.png')

        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = "convert {} {}".format(input_path, output_path)
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workershell, commands)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = int(args.channel)
    make_web_thumbnails(animal, channel, njobs)
