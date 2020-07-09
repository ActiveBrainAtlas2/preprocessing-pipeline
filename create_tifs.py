"""
This file does the following operations:
    1. Queries the sections view to get active tifs to be created.
    2. Runs the bfconvert bioformats command to yank the tif out of the czi and place
    it in the correct directory with the correct name
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
from sql_setup import QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1


def make_tifs(animal, channel, njobs):
    """
    Args:
        stack: the animal
        limit: number of jobs
    Returns: nothing
    """
    assert channel in [1,2,3]
    assert animal is not None
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = 'CH{}'.format(channel)
    INPUT = os.path.join(fileLocationManager.czi)
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full')

    tifs = sqlController.get_sections(animal, channel)
    sqlController.set_task(animal, QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN)
    sqlController.set_task(animal, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1)

    commands = []
    for i, tif in enumerate(tqdm(tifs)):
        inputfile = os.path.join(INPUT, tif.czi_file)
        outputfile = str(i).zfill(3) + '.tif'
        outputpath = os.path.join(OUTPUT, outputfile)

        if os.path.exists(outputpath):
            continue

        os.makedirs(os.path.dirname(outputpath), exist_ok=True)

        cmd = '/usr/local/share/bftools/bfconvert -bigtiff -compression LZW -separate -series {} -channel {} -nooverwrite {} {}'.format(
            tif.scene_index, tif.channel_index, inputfile, outputpath)

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
    channel = int(args.channel)
    make_tifs(animal, channel, njobs)

