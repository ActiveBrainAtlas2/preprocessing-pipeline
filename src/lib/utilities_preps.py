import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from concurrent.futures.process import ProcessPoolExecutor

from shutil import copyfile
from lib.sql_setup import CREATE_CHANNEL_3_FULL_RES, \
    CREATE_CHANNEL_2_FULL_RES, CREATE_CHANNEL_3_THUMBNAILS, CREATE_CHANNEL_2_THUMBNAILS
from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_process import create_downsample, test_dir, \
    get_image_size, resize_and_save_tif

def set_task_preps(animal,channel):
    sqlController = SqlController(animal)
    if channel == 1:
        sqlController.update_scanrun(sqlController.scan_run.id)
    progress_id = sqlController.get_progress_id(True, channel, 'TIF')
    sqlController.set_task(animal, progress_id)
    progress_id = sqlController.get_progress_id(False, channel, 'TIF')
    sqlController.set_task(animal, progress_id)


def make_full_resolution(animal, channel,workers = 10):
    """
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
    Returns:
        list of commands
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    if sqlController.histology.counterstain:
        if 'thion' in sqlController.histology.counterstain:
            sqlController.set_task(animal, CREATE_CHANNEL_2_FULL_RES)
            sqlController.set_task(animal, CREATE_CHANNEL_3_FULL_RES)

    INPUT = os.path.join(fileLocationManager.tif)
    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'full')
    os.makedirs(OUTPUT, exist_ok=True)
    input_paths = []
    output_paths = []
    sections = sqlController.get_sections(animal, channel)
    for section_number, section in enumerate(sections):
        input_path = os.path.join(INPUT, section.file_name)
        output_path = os.path.join(OUTPUT, str(section_number).zfill(3) + '.tif')
        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue
        input_paths.append(input_path)
        output_paths.append(output_path)
        width, height = get_image_size(input_path)
        sqlController.update_tif(section.id, width, height)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = executor.map(copyfile, input_paths,output_paths)


def make_low_resolution(animal, channel, debug,workers = 10):
    """
    Args:
        takes the full resolution tifs and downsamples them.
        animal: the prep id of the animal
        channel: the channel of the stack to process
    Returns:
        list of commands
    """
    sqlController = SqlController(animal)
    if sqlController.histology.counterstain:
        if 'thion' in sqlController.histology.counterstain:
            sqlController.set_task(animal, CREATE_CHANNEL_2_THUMBNAILS)
            sqlController.set_task(animal, CREATE_CHANNEL_3_THUMBNAILS)
    fileLocationManager = FileLocationManager(animal)
    file_keys = []
    INPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'full')
    error = test_dir(animal, INPUT, downsample=False, same_size=False)
    if len(error) > 0:
        print(error)
        sys.exit()
    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'thumbnail')
    os.makedirs(OUTPUT, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    for file in files:
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(OUTPUT, file)

        if os.path.exists(outpath):
            continue

        file_keys.append([infile, outpath])

    if debug:
        for file_key in file_keys:
            resize_and_save_tif(file_key)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(create_downsample, file_keys)
