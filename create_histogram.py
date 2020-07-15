"""
This file does the following operations:
    1. Convert the thumbnails from TIF to PNG format.
    2. Note: only the channel 1 for each animal is needed for PNG format
"""
import argparse
import os

from matplotlib import pyplot as plt
from skimage import io
from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from sql_setup import CREATE_CHANNEL_1_HISTOGRAMS, CREATE_CHANNEL_2_HISTOGRAMS, CREATE_CHANNEL_3_HISTOGRAMS


def make_histogram(animal, channel):
    """
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process

    Returns:
        nothing
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = os.path.join(fileLocationManager.thumbnail)
    OUTPUT = os.path.join(fileLocationManager.histogram)
    tifs = sqlController.get_sections(animal, channel)

    if channel == 1:
        sqlController.set_task(animal, CREATE_CHANNEL_1_HISTOGRAMS)
    elif channel == 2:
        sqlController.set_task(animal, CREATE_CHANNEL_2_HISTOGRAMS)
    else:
        sqlController.set_task(animal, CREATE_CHANNEL_3_HISTOGRAMS)

    for tif in tqdm(tifs):
        input_path = os.path.join(INPUT, tif.file_name)
        output_path = os.path.join(OUTPUT, os.path.splitext(tif.file_name)[0] + '.png')

        try:
            img = io.imread(input_path)
        except:
            continue

        if img.shape[0] * img.shape[1] > 1000000000:
            scale = 1 / float(2)
            img = img[::int(1. / scale), ::int(1. / scale)]

        try:
            flat = img.flatten()
        except:
            continue

        COLORS = {1: 'b', 2: 'r', 3: 'g'}
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

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, bbox_inches='tight')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    make_histogram(animal, channel)
