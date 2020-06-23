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


def copy_thumbnails_to_dir(stack):
    sql_controller = SqlController()
    valid_sections = sql_controller.get_valid_sections(stack)

    file_location_manager = FileLocationManager(stack)

    for section in valid_sections.values():
        src_file = os.path.join(file_location_manager.thumbnail_prep, section['destination'])
        dst_file = os.path.join(file_location_manager.prep, 'CH' + str(section['channel']),
                                'thumbnail', str(section['section_number']).zfill(3) + '.tif')

        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        copyfile(src_file, dst_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal

    copy_thumbnails_to_dir(animal)

