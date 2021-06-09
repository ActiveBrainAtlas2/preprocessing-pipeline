import argparse
import os, sys
from skimage import io
import numpy as np
from tqdm import tqdm
import cv2

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
COLORS = {1: 'b', 2: 'r', 3: 'g'}

def crop_color(img):
    high = np.quantile(img, 0.995)
    img[img < high] = 0
    return img

def create_cvat(animal, channel, start, end):

    fileLocationManager = FileLocationManager(animal)
    channel_dir = f'CH{channel}'

    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'cvat')
    os.makedirs(OUTPUT, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    files = files[200:221]
    print(f'found {len(files)} files')

    for file in tqdm(files):
        infile = os.path.join(INPUT, file)
        img = io.imread(infile, img_num=0)
        fixed = crop_color(img)
        outpath = os.path.join(OUTPUT, file)
        cv2.imwrite(outpath, fixed)






if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--start', help='Enter starting section', required=True)
    parser.add_argument('--end', help='Enter ending section', required=True)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    start = int(args.start)
    end = int(args.end)
    end += 1
    if end > start:
        create_cvat(animal, channel, start, end)
    else:
        print('End must be greater than start')


