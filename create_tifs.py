"""
This file does the following operations:
    1. Queries the sections view to get active tifs to be created.
    2. Runs the bfconvert bioformats command to yank the tif out of the czi and place
    it in the correct directory with the correct name
"""
import os
import sys
import argparse
from multiprocessing.pool import Pool

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workershell
from sql_setup import QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1


def make_tifs(animal, channel, njobs):
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
    INPUT = fileLocationManager.czi
    OUTPUT = fileLocationManager.tif
    tifs = sqlController.get_distinct_section_filenames(animal, channel)

    sqlController.set_task(animal, QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN)
    sqlController.set_task(animal, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1)

    commands = []
    for tif in tqdm(tifs):
        input_path = os.path.join(INPUT, tif.czi_file)
        output_path = os.path.join(OUTPUT, tif.file_name)
        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = '/usr/local/share/bftools/bfconvert -bigtiff -compression LZW -separate -series {} -channel {} -nooverwrite {} {}'.format(
            tif.scene_index, tif.channel_index, input_path, output_path)
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workershell, commands)

    # Update TIFs' size
    try:
        os.listdir(fileLocationManager.tif)
    except OSError as e:
        print(e)
        sys.exit()

    slide_czi_to_tifs = sqlController.get_slide_czi_to_tifs(channel)
    for slide_czi_to_tif in slide_czi_to_tifs:
        tif_path = os.path.join(fileLocationManager.tif, slide_czi_to_tif.file_name)
        if os.path.exists(tif_path):
            slide_czi_to_tif.file_size = os.path.getsize(tif_path)
            sqlController.update_row(slide_czi_to_tif)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = int(args.channel)

    # TEST loggers
    logger = get_logger(animal)
    logger.info('TEST: START make_tifs')

    make_tifs(animal, channel, njobs)
