"""
This file does the following operations:
    1. Queries the sections view to get active tifs to be updated.
    2. updates the files with the correct size. also updates the processing_duration
"""
import os
import sys
import argparse

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController


def update_tifs(animal, channel):
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
    tifs = sqlController.get_distinct_section_filenames(animal, channel)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full')
    # Update TIFs' size
    try:
        os.listdir(INPUT)
    except OSError as e:
        print(e)
        sys.exit()

    for i, tif in enumerate(tqdm(tifs)):
        print(tif.file_name)
        input_path = os.path.join(INPUT, str(i).zfill(3) + '.tif')
        if os.path.exists(input_path):
            print(input_path)
            tif.file_size = os.path.getsize(input_path)
            sqlController.update_row(tif)
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)

    # TEST loggers
    logger = get_logger(animal)
    logger.info('Update channel {} tifs'.format(channel))

    update_tifs(animal, channel)
