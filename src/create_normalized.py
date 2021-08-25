"""
This script will do a histogram equalization and rotation.
No masking or cleaning. This is to view the images as they are
for comparison purposes.
"""
import argparse
from lib.utilities_normalized import create_normalization


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=False,default=1)
    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    create_normalization(animal, channel)

