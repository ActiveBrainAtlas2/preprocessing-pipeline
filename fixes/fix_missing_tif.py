"""
Use pytest to run tests in this directory.
Just go into this directory and run:
pytest

You'll want this in your virtualenv
pip install pytest


"""
import os, sys
import argparse
from pathlib import Path

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())

from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.preprocessor import SlideProcessor
from utilities.utilities_process import make_tif
from sql_setup import session



def directory_filled(dir, channel):
    MINSIZE = 1000
    FAILED = 'FAILED'
    badsize = False
    file_status = []
    dir_exists = os.path.isdir(dir)
    files = os.listdir(dir)
    files = [file for file in files if 'C{}.tif'.format(channel) in file]

    for file in files:
        size = os.path.getsize(os.path.join(dir, file))
        if size < MINSIZE:
            file_status.append(FAILED)

    if FAILED in file_status:
        badsize = True
    return dir_exists, len(files), badsize

def find_missing(dir, db_files):
    source_files = []
    for section in db_files:
        source_files.append(section.file_name)
    files = os.listdir(dir)
    return (list(set(source_files) - set(files)))

def fix_tifs(animal, channel):
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    dir = fileLocationManager.tif
    db_files = sqlController.get_sections(animal, channel)

    source_files = []
    source_keys = []
    for tif in db_files:
        source_files.append(tif.file_name)
        source_keys.append(tif.id)
    files = os.listdir(dir)
    files = [file for file in files if 'C{}.tif'.format(channel) in file]
    missing_files =  list(set(source_files) - set(files))

    for i,missing in enumerate(missing_files):
        #pass
        file_id =  source_keys[source_files.index(missing)]
        section = sqlController.get_section(file_id)
        print(i, missing, file_id, section.id, section.file_name)
        make_tif(animal, section.tif_id, file_id, testing=False)

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


def test_tif(animal, channel):
    sqlController = SqlController(animal)
    checks = ['tif']
    fileLocationManager = FileLocationManager(animal)
    # tifs
    for name, dir in zip(checks, [fileLocationManager.tif]):
        db_files = sqlController.get_distinct_section_filenames(animal, channel)
        valid_file_length = db_files.count()
        dir_exists, lfiles, badsize = directory_filled(dir, channel)

        if not dir_exists:
            print("{} does not exist.".format(dir))

        missings = find_missing(dir, db_files)
        if len(missings) > 0:
            print("Missing files:")
            count = 1
            for missing in missings:
                print(count, missing)
                count += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal ID', required=True)
    parser.add_argument('--fix', help='Enter True to fix', required=False, default='False')
    parser.add_argument('--channel', help='Enter channel (1,2,3)', required=False, default=1)
    args = parser.parse_args()
    animal = args.animal
    fix = bool({'true': True, 'false': False}[args.fix.lower()])
    channel = int(args.channel)
    test_tif(animal, channel)
    if fix:
        fix_tifs(animal, channel)
        test_tif(animal, channel)
