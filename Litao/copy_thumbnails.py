"""
This file will copy the thumbnails of a stack to their designed channel folder
The section number, channel and path are read from the database.
"""
import os, sys
import argparse
from shutil import copyfile

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager


def copy_thumbnails_to_dir(animal):
    sql_controller = SqlController()

    file_location_manager = FileLocationManager(animal)

    channels = [1,2,3]

    for channel in channels:
        valid_sections = sql_controller.get_raw_sections(animal, channel)
        for section in valid_sections:
            src_file = os.path.join(file_location_manager.thumbnail_prep, section.destination)
            channel_dir = 'CH{}'.format(channel)
            dst_file = os.path.join(file_location_manager.prep, channel_dir,
                                    'thumbnail', str(section.section_number).zfill(3) + '.tif')

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            copyfile(src_file, dst_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal

    copy_thumbnails_to_dir(animal)

