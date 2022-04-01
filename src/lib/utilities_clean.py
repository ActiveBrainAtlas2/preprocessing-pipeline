import os, sys
import cv2
import numpy as np
from skimage import io
from concurrent.futures.process import ProcessPoolExecutor
from lib.sql_setup import CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK
from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_mask import rotate_image, place_image, scaled, equalized
from lib.utilities_process import test_dir, SCALING_FACTOR, get_cpus
import tifffile as tiff
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
def fix_ntb(file_key):
    """
    This method clean all NTB images in the specified channel. For channel one it also scales
    and does an adaptive histogram equalization.
    The masks have 3 dimenions since we are using the torch process.
    The 3rd channel has what we want for the mask.
    file_keys is a tuple of the following:
        :param infile: file path of image to read
        :param outpath: file path of image to write
        :param mask: binary mask image of the image
        :param rotation: amount of rotation. 1 = rotate by 90degrees
        :param flip: either flip or flop
        :param max_width: width of image
        :param max_height: height of image
        :param scale: used in scaling. Gotten from the histogram
    :return: nothing. we write the image to disk
    """
    infile, outpath, maskfile, rotation, flip, max_width, max_height, channel = file_key
    try:
        img = io.imread(infile)
    except IOError as e:
        errno, strerror = e.args
        print(f'Could not open {infile} {errno} {strerror}')

    try:
        mask = io.imread(maskfile)
    except IOError as e:
        errno, strerror = e.args
        print(f'Could not open {maskfile} {errno} {strerror}')

    try:
        fixed = cv2.bitwise_and(img, img, mask=mask)
    except:
        print(f'Error in masking {infile} with mask shape {mask.shape} img shape {img.shape}')
        print('Are the shapes exactly the same?')
        print("Unexpected error:", sys.exc_info()[0])
        raise
        sys.exit()
        
    del img
    if channel == 1:
        fixed = scaled(fixed, mask)
        fixed = equalized(fixed)
    del mask
    if rotation > 0:
        fixed = rotate_image(fixed, infile, rotation)
    if flip == 'flip':
        fixed = np.flip(fixed)
    if flip == 'flop':
        fixed = np.flip(fixed, axis=1)

    fixed = place_image(fixed, infile, max_width, max_height, 0)
    # cv2.imwrite(outpath, fixed)
    try:
        tiff.imsave(outpath, fixed)
    except Exception as e:
        print(f'Error in saving {outpath} with shape {fixed.shape} img type {type(fixed)}')
        print(f'Error is {e}')
        print("Unexpected error:", sys.exc_info()[0])
        raise
        sys.exit()
        
    # im = Image.fromarray(fixed)
    # im.save(outpath)
    del fixed
    return

def masker(animal, channel, downsample, debug):
    """
    Main method that starts the cleaning/rotating process.
    :param animal:  prep_id of the animal we are working on.
    :param channel:  channel {1,2,3}
    :param flip:  flip or flop or nothing
    :param rotation: usually 1 for rotating 90 degrees
    :param full:  resolution, either full or thumbnail
    :return: nothing, writes to disk the cleaned image
    """
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    channel_dir = 'CH{}'.format(channel)
    CLEANED = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_cleaned')
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail')
    MASKS = os.path.join(fileLocationManager.prep, 'masks', 'thumbnail_masked')
    os.makedirs(CLEANED, exist_ok=True)
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    rotation = sqlController.scan_run.rotation
    flip = sqlController.scan_run.flip
    max_width = int(width * SCALING_FACTOR+500)
    max_height = int(height * SCALING_FACTOR+500)
    stain = sqlController.histology.counterstain
    if channel == 1:
        sqlController.set_task(animal, CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK)
    if not downsample:
        CLEANED = os.path.join(fileLocationManager.prep, channel_dir, 'full_cleaned')
        os.makedirs(CLEANED, exist_ok=True)
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full')
        MASKS = os.path.join(fileLocationManager.prep, 'masks', 'full_masked')
        max_width = width
        max_height = height
    error = test_dir(animal, INPUT, downsample, same_size=False)
    if len(error) > 0:
        print(error)
        sys.exit()
    files = sorted(os.listdir(INPUT))
    progress_id = sqlController.get_progress_id(downsample, channel, 'CLEAN')
    sqlController.set_task(animal, progress_id)
    file_keys = []
    if debug:
        print(f'debugging and working with {len(files)} files')
    for file in files:
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(CLEANED, file)
        if os.path.exists(outpath):
            continue
        maskfile = os.path.join(MASKS, file)
        if stain and 'thion' in stain.lower():
            print('Not implemented.')
        else:
            file_keys.append([infile, outpath, maskfile, rotation, flip, max_width, max_height, channel])
    workers, _ = get_cpus() 
    if debug:
        print(f'debugging with single core with {len(file_keys)} file keys')
        for file_key in file_keys:
            fix_ntb(file_key)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(fix_ntb, sorted(file_keys))

