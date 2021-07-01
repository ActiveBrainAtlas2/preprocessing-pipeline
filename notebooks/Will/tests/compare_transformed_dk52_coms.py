#%%
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.IOs.get_bilis_json_file import *
from notebooks.Will.toolbox.plotting.plot_com_offset import *
from notebooks.Will.toolbox.IOs.pickle_io import load_pickle
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from notebooks.Will.toolbox.IOs.get_bilis_coms import *
from utilities.alignment.align_point_sets import get_and_apply_transform
#%%
save_dict = load_pickle(file_name='com_save_7-1-2021',folder='com_saves')
#dict_keys(['atlas_com', 'beth_coms', 'beth_corrected_coms', 'bili_aligned_coms', 'bili_aligned_corrected_coms', 'kui_airlab_coms'])
for key,value in save_dict.items():
    exec("%s = value" % (key))
#%%

def atlas_to_physical(com):
    com_physical = (np.array(com)*10/np.array([10,10,20])+np.array([500,500,150]))*np.array([10,10,20])
    return com_physical

def image_to_physical(com):
    com_physical = np.array(com)*np.array([0.325,0.325,20])
    return com_physical

def convert_com_dict_units(com_dict,conversion_function):
    com_dict_converted = {}
    for landmark,com in com_dict.items():
        com_dict_converted[landmark] = conversion_function(com)
    return com_dict_converted

def get_atlas_com():
    atlas_com_phys = convert_com_dict_units(atlas_com,atlas_to_physical)
    return atlas_com_phys

def get_dk52_com():
    DK52_com = convert_com_dict_units(beth_coms['DK52'],image_to_physical) 
    return DK52_com
    
def get_prep_coms():
    prep_coms = [convert_com_dict_units(com_dict,image_to_physical) for com_dict in beth_coms.values()]
    return prep_coms

def get_shared_landmarks_between_dk52_and_atlas():
    DK52_com = get_dk52_com()
    atlas_com = get_atlas_com()
    DK52_com_landmarks = set(DK52_com.keys())
    atlas_landmarks = set(atlas_com.keys())
    shared_landmarks = list(DK52_com_landmarks&atlas_landmarks)
    return shared_landmarks

def get_itk_transformed_coms():
    shared_landmarks = get_shared_landmarks_between_dk52_and_atlas()
    atlas_com_dict = get_atlas_com()
    DK52_com_dict = get_dk52_com()
    DK52_landmarks = list(DK52_com_dict.keys())
    atlas_com = np.array([atlas_com_dict[landmark] for landmark in shared_landmarks])
    DK52_com = np.array([DK52_com_dict[landmark] for landmark in shared_landmarks])
    prep_list = get_prep_list_for_rough_alignment_test()
    itk_transformed_coms = []
    for prepi in prep_list:
        affine_transform = get_affine_transform(prepi)
        DK52_com_transformed =  transform_point_affine(affine_transform,DK52_com)
        DK52_com_transformed,_ = get_and_apply_transform(DK52_com_transformed,atlas_com)
        DK52_com_transformed = dict(zip(DK52_landmarks,DK52_com_transformed))
        itk_transformed_coms.append(DK52_com_transformed)
    return itk_transformed_coms

def get_airlab_transformed_coms():
    shared_landmarks = get_shared_landmarks_between_dk52_and_atlas()
    atlas_com_dict = get_atlas_com()
    DK52_com_dict = get_dk52_com()
    atlas_com = np.array([atlas_com_dict[landmark] for landmark in shared_landmarks])
    DK52_com_shared = {}
    for landmark in shared_landmarks:
        DK52_com_shared[landmark] = DK52_com_dict[landmark]
    prep_list = get_prep_list_for_rough_alignment_test()
    air_lab_transformed_list = []
    for prepi in prep_list:
        transform = get_tranformation(prepi)
        airlab_transformed_coms = {}
        for name, com in DK52_com_shared.items():
            com = np.array(com, dtype=float)
            airlab_transformed_coms[name] = transform.forward_point(com).tolist()
        transformed_coms,_ = get_and_apply_transform(np.array(list(airlab_transformed_coms.values())),atlas_com)
        for i in range(len(transformed_coms)):
            name = list(airlab_transformed_coms.keys())[i]
            airlab_transformed_coms[name] = transformed_coms[i]
        air_lab_transformed_list.append(airlab_transformed_coms)
    return air_lab_transformed_list
#%%
dk52_com = get_dk52_com()
prep_coms = get_prep_coms()
#%%
transformed_coms_itk = get_itk_transformed_coms()
transformed_coms_airlab = get_airlab_transformed_coms()
#%%
fig = []
fig.append(plot_offset_between_two_com_sets(DK52_com,prepi_com,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'Beth annotation DK52 to DK39 offset'))

fig.append(plot_offset_between_two_com_sets(kui_dk52_dict_physical,prepi_com,
                            get_prep_list_for_rough_alignment_test,get_all_landmarks_in_specimens,
                            'Kui DK52 to Beth DK39 offset'))