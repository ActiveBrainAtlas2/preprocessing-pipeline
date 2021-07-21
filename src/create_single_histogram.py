import argparse
import os
from matplotlib import pyplot as plt
from skimage import io

HOME = os.path.expanduser("~")
from lib.file_location import FileLocationManager
COLORS = {1: 'b', 2: 'r', 3: 'g'}


def create_histogram(animal, channel, section):

    fileLocationManager = FileLocationManager(animal)
    channel_dir = f'CH{channel}/thumbnail_cleaned'

    filename = str(section).zfill(3) + '.tif'
    filepath = os.path.join(fileLocationManager.prep, channel_dir, filename)
    #maskpath = os.path.join(fileLocationManager.prep, 'thumbnail_masked', filename)
    outputpath = os.path.join(HOME, filename)

    img = io.imread(filepath, img_num=0)
    #mask = io.imread(maskpath)

    #img = cv2.bitwise_and(img, img, mask=mask)


    flat = img.flatten()

    fig = plt.figure()
    plt.rcParams['figure.figsize'] = [10, 6]
    plt.hist(flat, flat.max(), [0, 65535], color=COLORS[channel])
    plt.style.use('ggplot')
    plt.yscale('log')
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title(f'CH{channel} {filename} @{img.dtype}')
    plt.close()
    fig.savefig(outputpath, bbox_inches='tight')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--section', help='Enter section', required=True)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    section = int(args.section)
    create_histogram(animal, channel, section)


