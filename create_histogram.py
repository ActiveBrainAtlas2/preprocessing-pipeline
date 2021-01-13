"""
This program creates histograms for each tif file or creates a combined histogram of all files.
"""
import argparse
import os, sys
from collections import Counter
from matplotlib import pyplot as plt
from skimage import io
from tqdm import tqdm
import numpy as np
import cv2
from utilities.file_location import FileLocationManager
from utilities.logger import get_logger
from utilities.sqlcontroller import SqlController
from sql_setup import CREATE_CHANNEL_1_HISTOGRAMS, CREATE_CHANNEL_2_HISTOGRAMS, CREATE_CHANNEL_3_HISTOGRAMS
from utilities.utilities_process import test_dir

COLORS = {1: 'b', 2: 'r', 3: 'g'}


def make_histogram(animal, channel):
    """
    This method creates an individual histogram for each tif file by channel.
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process  {1,2,3}
    Returns:
        nothing
    """

    logger = get_logger(animal)
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'thumbnail')
    MASK_INPUT = fileLocationManager.thumbnail_masked
    tifs = sqlController.get_sections(animal, channel)
    error = test_dir(animal, INPUT, full=False, same_size=False)
    if len(tifs) == 0:
        error += " No sections in the database"
    if len(error) > 0:
        print(error)
        sys.exit()
    OUTPUT = os.path.join(fileLocationManager.histogram)
    os.makedirs(OUTPUT, exist_ok=True)

    if channel == 3:
        sqlController.set_task(animal, CREATE_CHANNEL_3_HISTOGRAMS)
    elif channel == 2:
        sqlController.set_task(animal, CREATE_CHANNEL_2_HISTOGRAMS)
    else:
        sqlController.set_task(animal, CREATE_CHANNEL_1_HISTOGRAMS)

    for i, tif in enumerate(tqdm(tifs)):
        filename = str(i).zfill(3) + '.tif'
        input_path = os.path.join(INPUT, filename)
        mask_path = os.path.join(MASK_INPUT, filename)
        output_path = os.path.join(OUTPUT, os.path.splitext(tif.file_name)[0] + '.png')
        if not os.path.exists(input_path):
            print('Input tif does not exist', input_path)
            continue

        if os.path.exists(output_path):
            continue

        try:
            img = io.imread(input_path)
        except:
            logger.warning(f'Could not open {input_path}')
            continue
        try:
            mask = io.imread(mask_path)
        except:
            logger.warning(f'Could not open {mask_path}')
            continue

        img = cv2.bitwise_and(img, img, mask=mask)


        if img.shape[0] * img.shape[1] > 1000000000:
            scale = 1 / float(2)
            img = img[::int(1. / scale), ::int(1. / scale)]



        try:
            flat = img.flatten()
        except:
            logger.warning(f'Could not flat {input_path}')
            continue

        fig = plt.figure()
        plt.rcParams['figure.figsize'] = [10, 6]
        plt.hist(flat, flat.max(), [0, flat.max()], color=COLORS[channel])
        plt.style.use('ggplot')
        plt.yscale('log')
        plt.grid(axis='y', alpha=0.75)
        plt.xlabel('Value')
        plt.ylabel('Frequency')
        plt.title(f'{tif.file_name} @16bit')
        plt.close()
        fig.savefig(output_path, bbox_inches='tight')


def make_combined(animal, channel):
    """
    This method takes all tif files by channel and creates a histogram of the combined image space.
    :param animal: the prep_id of the animal we are working with
    :param channel: the channel {1,2,3}
    :return: nothing
    """
    logger = get_logger(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'thumbnail')
    MASK_INPUT = fileLocationManager.thumbnail_masked
    OUTPUT = os.path.join(fileLocationManager.brain_info)
    os.makedirs(OUTPUT, exist_ok=True)
    tifs = os.listdir(INPUT)
    lfiles = len(tifs)
    hist_dict = Counter({})

    for i, tif in enumerate(tqdm(tifs)):
        filename = str(i).zfill(3) + '.tif'
        input_path = os.path.join(INPUT, filename)
        mask_path = os.path.join(MASK_INPUT, filename)

        try:
            img = io.imread(input_path)
        except:
            logger.error(f'Could not read {input_path}')
            lfiles -= 1
            break

        try:
            mask = io.imread(mask_path)
        except:
            logger.warning(f'Could not open {mask_path}')
            continue

        # mask image
        img = cv2.bitwise_and(img, img, mask=mask)

        try:
            flat = img.flatten()
            #flat = np.random.choice(flat, 1000)
            del img
        except:
            logger.error(f'Could not flatten file {input_path}')
            lfiles -= 1
            break
        try:
            #hist,bins = np.histogram(flat, bins=nbins)
            img_counts = np.bincount(flat)
        except:
            logger.error(f'Could not create counts {input_path}')
            lfiles -= 1
            break
        try:
            img_dict = Counter(dict(zip(np.unique(flat), img_counts[img_counts.nonzero()])))
        except:
            logger.error(f'Could not create counter {input_path}')
            lfiles -= 1
            break
        try:
            hist_dict = hist_dict + img_dict
        except:
            logger.error(f'Could not add files {input_path}')
            lfiles -= 1
            break


    hist_dict = dict(hist_dict)
    hist_values = [i/lfiles for i in hist_dict.values()]

    fig = plt.figure()
    plt.rcParams['figure.figsize'] = [10, 6]
    plt.bar(list(hist_dict.keys()), hist_values, color = COLORS[channel])
    plt.yscale('log')
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('{} channel {} @16bit with {} tif files'.format(animal, channel, lfiles))
    outfile = '{}_C{}.histogram.png'.format(animal, channel)
    output_path = os.path.join(OUTPUT, outfile)
    fig.savefig(output_path, bbox_inches='tight')
    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--single', help='Enter single or combined', required=True, default='single')

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    single = bool({'single': True, 'combined': False}[args.single])

    if single:
        make_histogram(animal, channel)
    else:
        make_combined(animal, channel)
