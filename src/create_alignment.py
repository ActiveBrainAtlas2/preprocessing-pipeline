"""
This file does the following operations:
    1. fetches the files needed to process.
    2. runs the files in sequence through elastix
    3. parses the results from the elastix output file
    4. Sends those results to the PIL affine with the rotation and translation matrix
    5. The location of elastix is hardcoded below which is a typical linux install location.
"""
import argparse
from lib.utilities_create_alignment import parse_elastix, run_offsets

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--masks', help='Enter True for running masks', required=False, default=False)
    parser.add_argument('--csv', help='Enter true or false', required=False, default='false')
    parser.add_argument('--allen', help='Enter true or false', required=False, default='false')
    parser.add_argument('--scale', help='Enter scaling', required=False, default=45000)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    create_csv = bool({'true': True, 'false': False}[str(args.csv).lower()])
    allen = bool({'true': True, 'false': False}[str(args.allen).lower()])
    masks = args.masks
    scale = int(args.scale)
    transforms = parse_elastix(animal)
    run_offsets(animal, transforms, channel, downsample, masks, create_csv, allen)
