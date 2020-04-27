"""
Use pytest to run tests in this directory.
Just go into this directory and run:
pytest

You'll want this in your virtualenv
pip install pytest


"""
import os, sys
sys.path.append(os.path.join(os.getcwd(), '..'))

from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager

def directory_filled(dir):
    MINSIZE = 1000
    FAILED = 'FAILED'
    badsize = False
    file_status = []
    dir_exists = os.path.isdir(dir)
    files = os.listdir(dir)
    for file in files:
        size = os.path.getsize(os.path.join(dir, file))
        if size < MINSIZE:
            file_status.append(FAILED)

    if FAILED in file_status:
        badsize = True
    return dir_exists, len(files), badsize

def find_missing(dir, db_files):
    source_files = []
    for key, file in db_files.items():
        #print(file['source'])
        source_files.append(file['destination'])
    files = os.listdir(dir)
    return (list(set(source_files) - set(files)))





def test_tif():
    sqlController = SqlController()
    stack_metadata = sqlController.generate_stack_metadata()
    animals = list(stack_metadata.keys())
    checks = ['tif', 'histogram', 'prep_thumbnail', 'web thumbnail']
    checks = ['prep_thumbnail']
    animals = ['DK39']
    for animal in animals:
        fileLocationManager = FileLocationManager(animal)
        # tifs
        for name, dir in zip(checks, [fileLocationManager.thumbnail_prep]):
            db_files = sqlController.get_valid_sections(animal)
            valid_file_length = len(db_files)
            dir_exists, lfiles, badsize = directory_filled(dir)

            if not dir_exists:
                print("{} does not exist.".format(dir))

            missings = find_missing(dir, db_files)
            print("There are {} {} entries in the database and we found {} {}s on the server"\
                    .format(animal, valid_file_length, lfiles, name))
            if name in ['tif', 'prep_thumbnail']:
                print('Missing {} {}'.format(name, missings))


if __name__ == '__main__':
    test_tif()
