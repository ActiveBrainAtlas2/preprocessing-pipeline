"""
Creates a shell from  aligned thumbnails
"""
import argparse
from lib.utilities_neuroglancer_image import create_neuroglancer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--debug', help='Enter debug True|False', required=False, default='false')

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_neuroglancer(animal, channel, downsample, debug)

