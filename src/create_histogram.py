"""
This program creates histograms for each tif file or creates a combined histogram of all files.
"""
import argparse
from lib.utilities_histogram import make_combined,make_histogram

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--single', help='Enter true or false', required=False, default='true')

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    single = bool({'true': True, 'false': False}[str(args.single).lower()])

    if single:
        make_histogram(animal, channel)
    else:
        make_combined(animal, channel)
