import os, sys
from PIL import Image
from tqdm import tqdm

from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_process import test_dir


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
    channel_dir = 'CH1'
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    len_files = len(os.listdir(INPUT))
    if len_files < 10:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_cleaned')
    ##### Check if files in dir are valid
    error = test_dir(animal, INPUT, downsample=True, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    OUTPUT = fileLocationManager.thumbnail_web
    os.makedirs(OUTPUT, exist_ok=True)
    tifs = sqlController.get_sections(animal, 1)

    for i, tif in enumerate(tqdm(tifs)):
        input_path = os.path.join(INPUT, str(i).zfill(3) + '.tif')
        output_path = os.path.join(OUTPUT, os.path.splitext(tif.file_name)[0] + '.png')

        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue

        original = Image.open(input_path)
        original.save(output_path, format="png")