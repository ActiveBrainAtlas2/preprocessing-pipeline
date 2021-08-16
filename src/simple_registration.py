import argparse

from tqdm import tqdm
import os

from lib.utilities_registration import register_simple
from lib.sqlcontroller import SqlController

def create_elastix(animal):

    DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps'
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
    sqlController = SqlController(animal)
    files = sorted(os.listdir(INPUT))
    sqlController.clear_elastix(animal)

    for i in tqdm(range(1, len(files))):
        fixed_index = os.path.splitext(files[i-1])[0]
        moving_index = os.path.splitext(files[i])[0]        
        if not sqlController.check_elastix_row(animal,moving_index):
            rotation, xshift, yshift = register_simple(INPUT, fixed_index, moving_index)
            sqlController.add_elastix_row(animal, moving_index, rotation, xshift, yshift)


if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_elastix(animal)

