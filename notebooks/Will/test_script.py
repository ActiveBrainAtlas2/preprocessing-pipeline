
import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from toolbox.sitk.registration_method_util import *
from notebooks.Will.toolbox.sitk.utility import *
import json
import numpy as np
from notebooks.Will.toolbox.coordinate_transforms import atlas_to_image_coord,atlas_to_thumbnail_coord

coord = [100,100,100]
atlas_to_thumbnail_coord(coord)


def get_atlas_com(braini):
    with open('/home/zhw272/programming/pipeline_utility/notebooks/Bili/data/DK52_coms_kui_detected.json', 'r') as f:
        atlas_coms = json.load(f)
    return atlas_coms


def get_demons_transform(braini):
    save_path = '/net/birdstore/Active_Atlas_Data/data_root/tfm'
    transform = sitk.ReadTransform(save_path + '/demons/' + braini + '_demons.tfm')
    return transform


def transform_atlas_com(atlas_com):
    transform = get_demons_transform(braini)
    estimated_target_coms = {}
    for name, com in atlas_com.items():
        transformed_coms[name] = transform.TransformPoint(com)
    return estimated_target_coms

braini = 'DK39'
atlas_coms = get_atlas_com(braini)
atlas_com = atlas_coms['10N_L']
image_com = atlas_to_image_coord(atlas_com)
estimated_target_coms = transform_atlas_com(image_com)
image_com,estimated_target_coms

com_diff = {}
for structure in atlas_coms.keys():
    moving_com = atlas_coms[structure]
    fixed_com = estimated_target_coms[structure]
    com_diffi= np.array(moving_com)-np.array(fixed_com)
    com_diff[structure] = com_diffi

np.linalg.inv(np.diag([1,2,3]))