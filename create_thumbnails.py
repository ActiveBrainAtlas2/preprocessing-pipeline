"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs ImageMagick convert to scale files
"""
import os, sys
import argparse
import subprocess
from multiprocessing.pool import Pool
from tqdm import tqdm

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workershell
from sql_setup import CREATE_CHANNEL_1_THUMBNAILS, CREATE_CHANNEL_2_THUMBNAILS, CREATE_CHANNEL_3_THUMBNAILS


def make_thumbnails(animal, channel, njobs):
    """
    Args:
        stack: the animal
        limit: number of jobs
    Returns: nothing
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    INPUT = os.path.join(fileLocationManager.prep,  channel_dir, 'full')
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail')
    files = os.listdir(INPUT)
    if channel == 1:
        sqlController.set_task(animal, CREATE_CHANNEL_1_THUMBNAILS)
    elif channel == 2:
        sqlController.set_task(animal, CREATE_CHANNEL_2_THUMBNAILS)
    else:
        sqlController.set_task(animal, CREATE_CHANNEL_3_THUMBNAILS)


    commands = []
    for file in tqdm(files):
        inputfile = os.path.join(INPUT, file)
        outputfile = os.path.join(OUTPUT, file)

        if os.path.exists(outputfile):
            continue

        cmd = "convert {} -resize 3.125% -compress lzw {}".format(inputfile, outputfile)

        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workershell, commands)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    parser.add_argument('--channel', help='Enter channel', required=True)
    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = args.channel
    make_thumbnails(animal, channel, njobs)
