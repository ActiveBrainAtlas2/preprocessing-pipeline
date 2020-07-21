"""
This file does the following operations:
    1. Convert the thumbnails from TIF to PNG format.
    2. Note: only the channel 1 for each animal is needed for PNG format
"""
import argparse
import os
from collections import Counter
from matplotlib import pyplot as plt
from skimage import io
from tqdm import tqdm
import numpy as np
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from sql_setup import CREATE_CHANNEL_1_HISTOGRAMS, CREATE_CHANNEL_2_HISTOGRAMS, CREATE_CHANNEL_3_HISTOGRAMS

COLORS = {1: 'b', 2: 'r', 3: 'g'}


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


def make_combined(animal, channel):
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.thumbnail)
    OUTPUT = os.path.join(fileLocationManager.brain_info)
    files = os.listdir(INPUT)
    lfiles = len(files)
    hist_dict = Counter({})
    for file in tqdm(files):
        filepath = os.path.join(INPUT,file)
        try:
            img = io.imread(filepath)
        except:
            print('cannot read file',file)
            lfiles -= 1
            break
        try:
            flat = img.flatten()
            #flat = np.random.choice(flat, 1000)
            del img
        except:
            print('cannot flatten file',file)
            lfiles -= 1
            break
        try:
            #hist,bins = np.histogram(flat, bins=nbins)
            img_counts = np.bincount(flat)
        except:
            print('could not create counts',file)
            lfiles -= 1
            break
        try:
            img_dict = Counter(dict(zip(np.unique(flat), img_counts[img_counts.nonzero()])))
        except:
            print('could not create counter',file)
            lfiles -= 1
            break
        try:
            hist_dict = hist_dict + img_dict
        except:
            print('could not add files',file)
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
    outpath = os.path.join(OUTPUT, outfile)
    fig.savefig(outpath, bbox_inches='tight')
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
