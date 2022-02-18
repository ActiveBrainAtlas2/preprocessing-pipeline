"""
This file does the following operations:
    1. Convert the thumbnails from TIF to PNG format from the preps/CH1 dir
"""
import argparse
from lib.utilities_web import make_web_thumbnails


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    args = parser.parse_args()
    animal = args.animal

    make_web_thumbnails(animal)
