"""
This is for cleaning/masking all channels from the mask created
on channel 1. It also does the rotating and flip/flop if necessary.
On channel one it scales and does an adaptive histogram equalization.
Note, the scaled method takes 45000 as the default. This is usually
a good value for 16bit images. Note, opencv uses lzw compression by default
to save files.
"""
import argparse
from lib.utilities_clean import create_cleaned_images

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--scale', help='Enter scaling', required=False, default=45000)
    parser.add_argument('--debug', help='Enter true or false', required=False, default='false')


    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    scale = int(args.scale)
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_cleaned_images(animal, channel, downsample, debug)

