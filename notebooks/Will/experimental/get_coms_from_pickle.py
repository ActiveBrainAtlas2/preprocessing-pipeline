from bdb import Breakpoint
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_point_demons
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
from notebooks.Will.toolbox.IOs.get_bilis_json_file import *
# from notebooks.Will.toolbox.IOs.get_bilis_coms import *
from utilities.alignment.align_point_sets import get_and_apply_transform
import os
import pickle

save_dict = pickle.load(open(os.path.join(sys.path[0], 'com_save_7-1-2021.p'),'rb'))
#dict_keys(['atlas_com', 'beth_coms', 'beth_corrected_coms', 'bili_aligned_coms', 'bili_aligned_corrected_coms', 'kui_airlab_coms'])
for key,value in save_dict.items():
    exec("%s = value" % (key))

def get_prep_list_for_rough_alignment_test():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']

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

# def get_kui_transformed():
#     prep_list = get_prep_list_for_rough_alignment_test()
#     kui_transformed_com = []
#     for prepi in prep_list:
#         kui_transformed_com.append(get_transformed_com_dict(prepi))
#     return kui_transformed_com

# def get_kui_airlab():
#     kui_airlab_com = [convert_com_dict_units(com_dict,neuroglancer_atlas_to_physical) for name,com_dict in kui_airlab_coms.items() if name!='DK52']
#     return kui_airlab_com

def get_atlas_com():
    atlas_com_phys = convert_com_dict_units(atlas_com,atlas_to_physical)
    return atlas_com_phys

def get_prepi_com(prepi):
    prepi_com = convert_com_dict_units(beth_coms[prepi],image_to_physical) 
    return prepi_com

def get_dk52_com():
    return get_prepi_com('DK52')
    
def get_prep_coms():
    prep_coms = [convert_com_dict_units(com_dict,image_to_physical) for name,com_dict in beth_coms.items() if name!='DK52']
    return prep_coms

def get_shared_landmarks_between_dk52_and_atlas():
    DK52_com = get_dk52_com()
    atlas_com = get_atlas_com()
    DK52_com_landmarks = set(DK52_com.keys())
    atlas_landmarks = set(atlas_com.keys())
    shared_landmarks = list(DK52_com_landmarks&atlas_landmarks)
    return shared_landmarks

def get_itk_affine_transformed_coms():
    shared_landmarks = get_shared_landmarks_between_dk52_and_atlas()
    atlas_com_dict = get_atlas_com()
    DK52_com_dict = get_dk52_com()
    atlas_com = np.array([atlas_com_dict[landmark] for landmark in shared_landmarks])
    DK52_com = np.array([DK52_com_dict[landmark] for landmark in shared_landmarks])
    prep_list = get_prep_list_for_rough_alignment_test()
    itk_transformed_coms = []
    itk_aligned_coms = []
    for prepi in prep_list:
        affine_transform = get_affine_transform(prepi)
        DK52_com_transformed =  transform_point_affine(affine_transform,DK52_com)
        DK52_com_aligned,_ = get_and_apply_transform(DK52_com_transformed,atlas_com)
        DK52_com_transformed = dict(zip(shared_landmarks,DK52_com_transformed))
        DK52_com_aligned = dict(zip(shared_landmarks,DK52_com_aligned))
        itk_transformed_coms.append(DK52_com_transformed)
        itk_aligned_coms.append(DK52_com_aligned)
    return itk_transformed_coms,itk_aligned_coms

def get_itk_demons_transformed_coms():
    shared_landmarks = get_shared_landmarks_between_dk52_and_atlas()
    atlas_com_dict = get_atlas_com()
    DK52_com_dict = get_dk52_com()
    atlas_com = np.array([atlas_com_dict[landmark] for landmark in shared_landmarks])
    DK52_com = np.array([DK52_com_dict[landmark] for landmark in shared_landmarks])
    prep_list = get_prep_list_for_rough_alignment_test()
    itk_transformed_coms = []
    itk_aligned_coms = []
    for prepi in prep_list:
        demons_transform = get_demons_transform(prepi)
        DK52_com_transformed =  transform_point_demons(demons_transform,DK52_com)
        DK52_com_aligned,_ = get_and_apply_transform(DK52_com_transformed,atlas_com)
        DK52_com_transformed = dict(zip(shared_landmarks,DK52_com_transformed))
        DK52_com_aligned = dict(zip(shared_landmarks,DK52_com_aligned))
        itk_transformed_coms.append(DK52_com_transformed)
        itk_aligned_coms.append(DK52_com_aligned)
    return itk_transformed_coms,itk_aligned_coms

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
    air_lab_aligned_list = []
    for prepi in prep_list:
        airlab_aligned_coms = {}
        transform = get_tranformation(prepi)
        airlab_transformed_coms = {}
        for name, com in DK52_com_shared.items():
            com = np.array(com, dtype=float)/np.array([0.325,0.325,20])
            airlab_transformed_coms[name] = (transform.forward_point(com)*np.array([0.325,0.325,20])).tolist()
        aligned_com,_ = get_and_apply_transform(np.array(list(airlab_transformed_coms.values())),atlas_com)
        for i in range(len(aligned_com)):
            name = list(airlab_transformed_coms.keys())[i]
            airlab_aligned_coms[name] = aligned_com[i]
        air_lab_transformed_list.append(airlab_transformed_coms)
        air_lab_aligned_list.append(airlab_aligned_coms)
    return air_lab_transformed_list,air_lab_aligned_list
