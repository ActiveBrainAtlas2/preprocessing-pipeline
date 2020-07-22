"""
This file does the following operations:
    1. Queries the sections view to get active tifs to be updated.
    2. updates the files with the correct size. also updates the processing_duration
"""
import os
import sys
import argparse
import time
from multiprocessing.pool import Pool

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workershell
from sql_setup import QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1


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
    # Update TIFs' size
    try:
        os.listdir(fileLocationManager.tif)
    except OSError as e:
        print(e)
        sys.exit()

    for tif in tqdm(tifs):
        tif_path = os.path.join(fileLocationManager.tif, tif.file_name)
        print(tif_path)
        if os.path.exists(tif_path):
            tif.file_size = os.path.getsize(tif_path)
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
