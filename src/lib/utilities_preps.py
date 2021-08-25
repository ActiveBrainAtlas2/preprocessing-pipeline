import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from concurrent.futures.process import ProcessPoolExecutor
from timeit import default_timer as timer

from tqdm import tqdm
from shutil import copyfile
from lib.sql_setup import CREATE_CHANNEL_3_FULL_RES, \
    CREATE_CHANNEL_2_FULL_RES, CREATE_CHANNEL_3_THUMBNAILS, CREATE_CHANNEL_2_THUMBNAILS
from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_process import resize_tif, get_cpus, test_dir, get_image_size, SCALING_FACTOR

def set_task_preps(animal,channel):
    sqlController = SqlController(animal)
    if channel == 1:
        sqlController.update_scanrun(sqlController.scan_run.id)
    progress_id = sqlController.get_progress_id(True, channel, 'TIF')
    sqlController.set_task(animal, progress_id)
    progress_id = sqlController.get_progress_id(False, channel, 'TIF')
    sqlController.set_task(animal, progress_id)


def make_full_resolution(animal, channel):
    """
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
        compress: Use the default LZW compression, otherwise just copy the file with the correct name
    Returns:
        list of commands
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)

    if 'thion' in sqlController.histology.counterstain:
        sqlController.set_task(animal, CREATE_CHANNEL_2_FULL_RES)
        sqlController.set_task(animal, CREATE_CHANNEL_3_FULL_RES)

    INPUT = os.path.join(fileLocationManager.tif)
    ##### Check if files in dir are valid
    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'full')
    os.makedirs(OUTPUT, exist_ok=True)

    sections = sqlController.get_sections(animal, channel)
    for section_number, section in enumerate(tqdm(sections)):
        input_path = os.path.join(INPUT, section.file_name)
        output_path = os.path.join(OUTPUT, str(
            section_number).zfill(3) + '.tif')

        if not os.path.exists(input_path):
            #print('Input tif does not exist', input_path)
            continue

        if os.path.exists(output_path):
            continue

        copyfile(input_path, output_path)
        width, height = get_image_size(input_path)
        sqlController.update_tif(section.id, width, height)

def make_low_resolution(animal, channel):
    """
    Args:
        takes the full resolution tifs and downsamples them.
        animal: the prep id of the animal
        channel: the channel of the stack to process
    Returns:
        list of commands
    """
    sqlController = SqlController(animal)

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
    tifs = sorted(os.listdir(INPUT))
    print(tifs)
    for tif in tifs:
        infile = os.path.join(INPUT, tif)
        outpath = os.path.join(OUTPUT, tif)

        if os.path.exists(outpath):
            continue

        try:
            width, height = get_image_size(infile)
        except:
            print(f'Could not open {infile}')
        size = int(int(width)*SCALING_FACTOR), int(int(height)*SCALING_FACTOR)
        file_keys.append([infile, outpath, size])

    start = timer()        
    workers, _ = get_cpus()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(resize_tif, file_keys)
    end = timer()
    print(f'Create thumbnails took {end - start} seconds')
