"""
Use pytest to run tests in this directory.
Just go into this directory and run:
pytest

You'll want this in your virtualenv
pip install pytest


"""
import os, sys
import argparse

sys.path.append(os.path.join(os.getcwd(), '..'))

from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from controller.preprocessor import SlideProcessor, make_tif
from sql_setup import session



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
        source_files.append(file['destination'])
    files = os.listdir(dir)
    return (list(set(source_files) - set(files)))

def fix_tifs(animal):
    sqlController = SqlController()
    fileLocationManager = FileLocationManager(animal)
    dir = fileLocationManager.tif
    db_files = sqlController.get_valid_sections(animal)
    slideProcessor = SlideProcessor(animal, session)

    source_files = []
    source_keys = []
    for key, file in db_files.items():
        source_files.append(file['destination'])
        source_keys.append(key)
    files = os.listdir(dir)
    missing_files =  (list(set(source_files) - set(files)))
    for i,missing in enumerate(missing_files):
        #pass
        file_id =  source_keys[source_files.index(missing)]
        print(i, missing, file_id)
        section = sqlController.get_section(file_id)
        make_tif(session, animal, section.tif_id, file_id, testing=False)

def fix_prep_thumbnail(animal):
    sqlController = SqlController()
    fileLocationManager = FileLocationManager(animal)
    dir = fileLocationManager.thumbnail_prep
    db_files = sqlController.get_valid_sections(animal)
    slideProcessor = SlideProcessor(animal, session)

    source_files = []
    source_keys = []
    for key, file in db_files.items():
        source_files.append(file['destination'])
        source_keys.append(key)
    files = os.listdir(dir)
    missing_files =  (list(set(source_files) - set(files)))
    print(len(missing_files))
    for i,missing in enumerate(missing_files):
        file_id =  source_keys[source_files.index(missing)]
        print(i, missing, file_id)
        slideProcessor.make_thumbnail(file_id, missing, testing=False)
        slideProcessor.make_web_thumbnail(file_id, missing, testing=False)


def test_tif(animal):
    sqlController = SqlController()
    stack_metadata = sqlController.generate_stack_metadata()
    animals = list(stack_metadata.keys())
    checks = ['tif', 'histogram', 'prep_thumbnail', 'web thumbnail']
    fileLocationManager = FileLocationManager(animal)
    # tifs
    for name, dir in zip(checks, [fileLocationManager.tif,
                                  fileLocationManager.histogram,
                                  fileLocationManager.thumbnail_prep,
                                  fileLocationManager.thumbnail_web]):
        db_files = sqlController.get_valid_sections(animal)
        valid_file_length = len(db_files)
        dir_exists, lfiles, badsize = directory_filled(dir)

        if not dir_exists:
            print("{} does not exist.".format(dir))

        print("There are {} {} entries in the database and we found {} {}s on the server"\
                .format(animal, valid_file_length, lfiles, name))

        if name == 'tif':
            missings = find_missing(dir, db_files)
            print(missings)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--prep_id', help='Enter the animal prep_id', required=True)
    args = parser.parse_args()
    prep_id = args.prep_id
    test_tif(prep_id)
    fix_tifs(prep_id)
    fix_prep_thumbnail(prep_id)
    test_tif(prep_id)
