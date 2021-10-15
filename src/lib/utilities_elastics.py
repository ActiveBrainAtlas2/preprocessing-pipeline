import os

from lib.utilities_registration import register_simple
from lib.sqlcontroller import SqlController

def create_elastix(animal):

    DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps'
    INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
    sqlController = SqlController(animal)
    files = sorted(os.listdir(INPUT))
    for i in range(1, len(files)):
        fixed_index = os.path.splitext(files[i-1])[0]
        moving_index = os.path.splitext(files[i])[0]        
        if not sqlController.check_elastix_row(animal,moving_index):
            rotation, xshift, yshift = register_simple(INPUT, fixed_index, moving_index)
            sqlController.add_elastix_row(animal, moving_index, rotation, xshift, yshift)