"""
This file does the following operations:
    1. Queries the sections view to get active tifs to be created.
    2. Runs the bfconvert bioformats command to yank the tif out of the czi and place
    it in the correct directory with the correct name
    3. If you  want jp2 files, the bioformats tool will die as the memory requirements are too high.
    To create jp2, first create uncompressed tif files and then use Matlab to create the jp2 files.
    The Matlab script is in registration/tif2jp2.sh
"""
import argparse

from utilities.utilities_process import make_tifs, make_scenes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)

    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = int(args.channel)

    make_tifs(animal, channel, njobs)
    if channel == 1:
        make_scenes(animal)
