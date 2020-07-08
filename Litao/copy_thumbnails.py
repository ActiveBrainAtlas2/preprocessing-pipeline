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
    sql_controller = SqlController()

    file_location_manager = FileLocationManager(animal)
    INPUT = file_location_manager.thumbnail_prep
    if 'full' in resolution:
        INPUT = file_location_manager.tif

    valid_sections = sql_controller.get_raw_sections(animal, channel)
    for section in tqdm(valid_sections):
        src_file = os.path.join(INPUT, section.destination_file)
        channel_dir = 'CH{}'.format(channel)
        dst_file = os.path.join(file_location_manager.prep, channel_dir,
                                resolution, str(section.section_number).zfill(3) + '.tif')

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

