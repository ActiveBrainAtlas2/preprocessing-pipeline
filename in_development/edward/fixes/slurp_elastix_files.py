"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""

import argparse
from tqdm import tqdm
from pprint import pprint
import os
import sys
from datetime import datetime

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(DIR)
from pipeline.Controllers.SqlController import SqlController
from pipeline.lib.FileLocationManager import FileLocationManager
from pipeline.utilities.utilities_alignment import parameter_elastix_parameter_file_to_dict

def slurp(animal):
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    sqlController.clear_elastix(animal)


    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_cleaned')
    if not os.path.exists(INPUT):
        print(f'{INPUT} does not exist')
        sys.exit()
    ELASTIX = fileLocationManager.elastix_dir
    files = sorted(os.listdir(INPUT))
    for i in range(1, len(files)):
        fixed_index = os.path.splitext(files[i - 1])[0]
        moving_index = os.path.splitext(files[i])[0]

        new_dir = '{}_to_{}'.format(moving_index, fixed_index)
        output_subdir = os.path.join(ELASTIX, new_dir)
        filepath = os.path.join(output_subdir, 'TransformParameters.0.txt')

        if os.path.exists(filepath):
            d = parameter_elastix_parameter_file_to_dict(filepath)
            rotation, xshift, yshift = d['TransformParameters']
            sqlController.add_elastix_row(animal, moving_index, rotation, xshift, yshift)
        else:
            print(f'{filepath} does not exist')





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter animal', required=True)
    parser.add_argument('--debug', help='Enter true of false', required=False, default='true')
    

    args = parser.parse_args()
    animal = args.animal
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])

    slurp(animal)    

