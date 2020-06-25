"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs ImageMagick convert to scale files
"""
import os, sys
import argparse
import subprocess
from multiprocessing.pool import Pool
from tqdm import tqdm

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager


def workershell(cmd):
    """
    Set up an shell command. That is what the shell true is for.
    Args:
        cmd:  a command line program with arguments in a string
    Returns: nothing
    """
    proc = subprocess.Popen(cmd, shell=True, stderr=None, stdout=None)
    proc.wait()

def make_thumbnails(animal, channel, njobs):
    """
    Args:
        stack: the animal
        limit: number of jobs
    Returns: nothing
    """
    channel_find = '{}.tif'
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.tif
    OUTPUT = fileLocationManager.thumbnail_prep
    files = [file for file in os.listdir(INPUT) if file.endswith(channel_find)]
    commands = []
    for file in tqdm(files):
        inputfile = os.path.join(INPUT, file)
        outputfile = os.path.join(OUTPUT, file)

        if os.path.exists(outputfile):
            print('outfile exists', file)
            continue
        else:
            print('outfile does not exist', file)

        continue


        cmd = "convert {} -resize 3.125% -compress lzw {}".format(inputfile, outputfile)

        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workershell, commands)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    parser.add_argument('--channel', help='Enter channel', required=True)
    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = args.channel
    make_thumbnails(animal, channel, njobs)
