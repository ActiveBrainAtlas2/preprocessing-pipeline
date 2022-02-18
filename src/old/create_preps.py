"""
This file does the following operations:
    1. Converts regular filename from main tif dir to CHX/full or
    2. Converts and downsamples CHX/full to CHX/thumbnail
    When creating the full sized images, the LZW compression is used
"""
import argparse
from lib.utilities_preps import make_full_resolution,make_low_resolution,set_task_preps

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--debug', help='debugmode', required=False,default=False)


    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])    
    
    make_full_resolution(animal, channel)
    make_low_resolution(animal, channel, debug)
    set_task_preps(animal, channel)
    
