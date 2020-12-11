from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os, sys
import numpy as np
from collections import OrderedDict
import subprocess
import pickle

PATH = '/home/eddyod/programming/pipeline_utility'
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.utilities_registration import create_warp_transforms, register_correlation
from utilities.alignment_utility import SCALING_FACTOR


animal = 'DK39'
DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps'
INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
OUTPUT = os.path.join(DIR, 'CH1', 'thumbnail_aligned')
STORAGE = os.path.join(DIR, 'elastix')

rotation_storage = os.path.join(STORAGE, 'rotations.pickle')
rotations = pickle.load( open( rotation_storage, "rb" ) )

transformation_to_previous_section = OrderedDict()
for rf, R in rotations.items():
    transformation_to_previous_section[rf] = R

files = sorted(os.listdir(INPUT))

anchor_index = len(files) // 2 # middle section of the brain
transformation_to_anchor_section = {}
# Converts every transformation
for moving_index in range(len(files)):
    if moving_index == anchor_index:
        transformation_to_anchor_section[files[moving_index]] = np.eye(3)
    elif moving_index < anchor_index:
        T_composed = np.eye(3)
        for i in range(anchor_index, moving_index, -1):
            T_composed = np.dot(np.linalg.inv(transformation_to_previous_section[files[i]]), T_composed)
        transformation_to_anchor_section[files[moving_index]] = T_composed
    else:
        T_composed = np.eye(3)
        for i in range(anchor_index + 1, moving_index + 1):
            T_composed = np.dot(transformation_to_previous_section[files[i]], T_composed)
        transformation_to_anchor_section[files[moving_index]] = T_composed



resolution = 'thumbnail'
warp_transforms = create_warp_transforms(animal, transformation_to_anchor_section, 'thumbnail', resolution)
sqlController = SqlController(animal)
width = sqlController.scan_run.width
height = sqlController.scan_run.height
max_width = int(width * SCALING_FACTOR)
max_height = int(height * SCALING_FACTOR)
bgcolor = 'black' # this should be black, but white lets you see the rotation and shift

#OUTPUT = "setme to some place where you can write files"
ordered_transforms = OrderedDict(sorted(warp_transforms.items()))
for file, arr in tqdm(ordered_transforms.items()):
    T = np.linalg.inv(arr)
    sx = T[0, 0]
    sy = T[1, 1]
    rx = T[1, 0]
    ry = T[0, 1]
    tx = T[0, 2]
    ty = T[1, 2]
    # sx, rx, ry, sy, tx, ty
    op_str = f" +distort AffineProjection '{sx},{rx},{ry},{sy},{tx},{ty}'"
    op_str += f' -crop {max_width}x{max_height}+0.0+0.0!'
    input_fp = os.path.join(INPUT, file)
    output_fp = os.path.join(OUTPUT, file)
    if os.path.exists(output_fp):
        continue

    cmd = f"convert {input_fp} -define white-point=0x0 +repage -virtual-pixel background -background {bgcolor} {op_str} -flatten -compress lzw {output_fp}"
    subprocess.run(cmd, shell=True)
