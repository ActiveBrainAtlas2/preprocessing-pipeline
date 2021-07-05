import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.IOs.get_bilis_json_file import *
from notebooks.Will.toolbox.plotting.plot_com_offset import *
from notebooks.Will.toolbox.plotting.plot_coms import *
from notebooks.Will.toolbox.IOs.pickle_io import load_pickle
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from notebooks.Will.toolbox.IOs.get_bilis_coms import *
from utilities.alignment.align_point_sets import get_and_apply_transform
from matplotlib.backends.backend_pdf import PdfPages
import os

save_dict = load_pickle(file_name='com_save_7-1-2021',folder='com_saves')
#dict_keys(['atlas_com', 'beth_coms', 'beth_corrected_coms', 'bili_aligned_coms', 'bili_aligned_corrected_coms', 'kui_airlab_coms'])
for key,value in save_dict.items():
    exec("%s = value" % (key))

def atlas_to_physical(com):
    com_physical = (np.array(com)*10/np.array([10,10,20])+np.array([500,500,150]))*np.array([10,10,20])
    return com_physical

def image_to_physical(com):
    com_physical = np.array(com)*np.array([0.325,0.325,20])
    return com_physical

def neuroglancer_atlas_to_physical(com):
    com_physical = np.array(com)*np.array([10,10,20])
    return com_physical

def conversion_identity(com):
    return com

def convert_com_dict_units(com_dict,conversion_function):
    com_dict_converted = {}
    for landmark,com in com_dict.items():
        com_dict_converted[landmark] = conversion_function(com)
    return com_dict_converted

def get_kui_transformed():
    prep_list = get_prep_list_for_rough_alignment_test()
    kui_transformed_com = []
    for prepi in prep_list:
        kui_transformed_com.append(get_transformed_com_dict(prepi))
    return kui_transformed_com