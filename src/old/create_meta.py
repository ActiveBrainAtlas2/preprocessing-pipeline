"""
This is the first script run in the pipeline process.
It goes through the czi directory and gets the biggest
4 files with the bioformats tool: showinf. It then
populates the database with this meta information. The user
then validates the data with the ActiveAtlasAdmin database portal
"""
from lib.utilities_meta import make_meta
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--remove', help='Enter true or false', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    remove = bool({'true': True, 'false': False}[str(args.remove).lower()])
    make_meta(animal, remove)
    