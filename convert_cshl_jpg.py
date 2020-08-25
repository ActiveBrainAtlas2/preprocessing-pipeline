"""
This file does the following operations:
    1. Convert the thumbnails from TIF to PNG format from the preps/CH1 dir
"""
import argparse
import os
import subprocess

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController


def make_web_thumbnails(animal):
    """
    This was originally getting the thumbnails from the preps/thumbnail dir but they aren't usuable.
    The ones in the preps/CH1/thumbnail_aligned are much better
    But we need to test if there ane aligned files, if not use the cleaned ones.
    Thumbnails are always created from CH1
    Args:
        animal: the prep id of the animal
        njobs: number of jobs for parallel computing

    Returns:
        nothing
    """
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = '/home/eodonnell/DK39/cshl/jpg'
    len_files = len(os.listdir(INPUT))

    OUTPUT = os.path.join(fileLocationManager.root, animal, 'cshl/jpg')
    tifs = sqlController.get_sections(animal, 1)

    for i, tif in enumerate(tqdm(tifs)):
        input_path = os.path.join(INPUT, os.path.splitext(tif.file_name)[0] + '.jpg')
        output_path = os.path.join(OUTPUT, str(i).zfill(3) + '.jpg')

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
    args = parser.parse_args()
    animal = args.animal

    make_web_thumbnails(animal)
