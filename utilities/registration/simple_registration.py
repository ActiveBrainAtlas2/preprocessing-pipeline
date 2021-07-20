import numpy as np
from os.path import expanduser
HOME = expanduser("~")
import os, sys
import SimpleITK as sitk


animal = 'DK55'
DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps'
INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
ELASTIX = os.path.join(DIR, 'elastix')
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.registration.utilities_registration import register_test, register, register_simple


fixed_index = str(9).zfill(3)
moving_index = str(10).zfill(3)

test_transform = register_simple(INPUT, fixed_index, moving_index)
print(type(test_transform))
