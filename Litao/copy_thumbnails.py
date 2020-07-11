"""
This file will copy the thumbnails of a stack to their designed channel folder
The section number, channel and path are read from the database.
"""
import os, sys
import argparse
from shutil import copyfile
from tqdm import tqdm


sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager


def copy_images_to_dir(animal, channel, resolution):
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.thumbnail_prep
    if 'full' in resolution:
        INPUT = fileLocationManager.tif

    tifs = sqlController.get_sections(animal, channel)



    for i, tif in enumerate(tqdm(tifs)):
        src_file = os.path.join(INPUT, tif.file_name)
        channel_dir = 'CH{}'.format(channel)
        dst_file = os.path.join(fileLocationManager.prep, channel_dir,
                                resolution, str(i).zfill(3) + '.tif')

        if os.path.exists(dst_file):
            continue

        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        copyfile(src_file, dst_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=True, default='thumbnail')
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    resolution = args.resolution
    if resolution == 'full' or resolution == 'thumbnail':
        copy_images_to_dir(animal, channel, resolution)

