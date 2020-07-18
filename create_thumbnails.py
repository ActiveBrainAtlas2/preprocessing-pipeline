"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs ImageMagick convert to scale files
"""
import argparse
import os
from multiprocessing.pool import Pool

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workershell
from sql_setup import CREATE_CHANNEL_1_THUMBNAILS, CREATE_CHANNEL_2_THUMBNAILS, CREATE_CHANNEL_3_THUMBNAILS


def make_thumbnails(animal, channel, njobs):
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
    INPUT = fileLocationManager.tif
    OUTPUT = fileLocationManager.thumbnail
    tifs = sqlController.get_distinct_section_filenames(animal, channel)

    if channel == 1:
        sqlController.set_task(animal, CREATE_CHANNEL_1_THUMBNAILS)
    elif channel == 2:
        sqlController.set_task(animal, CREATE_CHANNEL_2_THUMBNAILS)
    else:
        sqlController.set_task(animal, CREATE_CHANNEL_3_THUMBNAILS)

    commands = []
    for tif in tqdm(tifs):
        input_path = os.path.join(INPUT, tif.file_name)
        output_path = os.path.join(OUTPUT, tif.file_name)

        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = "convert {} -resize 3.125% -compress lzw {}".format(input_path, output_path)
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
    make_thumbnails(animal, channel, njobs)
