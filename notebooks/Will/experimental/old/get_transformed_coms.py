from bdb import Breakpoint
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_dict_affine
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_dict_demons
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
from utilities.alignment.align_point_sets import get_rigid_transformation_from_dicts,apply_rigid_transformation_to_com_dict

import notebooks.Will.experimental.get_coms_from_pickle as getcom
# import notebooks.Will.experimental.get_coms_from_database as getcom

from notebooks.Will.toolbox.IOs.get_bilis_json_file import get_tranformation

def get_DK52_rigid_transformation():
    DK52_com = getcom.get_dk52_com()
    atlas_com = getcom.get_atlas_com()
    rigid_transformation = get_rigid_transformation_from_dicts(DK52_com,atlas_com)
    return rigid_transformation

def get_itk_affine_transformed_coms(com_getter):
    prep_list = getcom.get_prep_list_for_rough_alignment_test()
    transformed_com_list = []
    for prepi in prep_list:
        affine_transform = get_affine_transform(prepi)
        prepicom = com_getter(prepi)
        transformed_com = transform_dict_affine(affine_transform,prepicom)
        transformed_com_list.append(transformed_com)
    return transformed_com_list

def get_itk_demons_transformed_coms(com_getter):
    prep_list = getcom.get_prep_list_for_rough_alignment_test()
    transformed_com_list = []
    for prepi in prep_list:
        print('loading demons '+prepi)
        demons_transform = get_demons_transform(prepi)
        prepicom = com_getter(prepi)
        transformed_com = transform_dict_demons(demons_transform,prepicom)
        transformed_com_list.append(transformed_com)
    return transformed_com_list

def get_airlab_transformed_coms():
    prep_list = getcom.get_prep_list_for_rough_alignment_test()
    transformed_com_list = []
    for prepi in prep_list:
        affine_transform = get_tranformation(prepi)
        prepicom = getcom.get_prepi_com(prepi)
        transformed_com = apply_airlab_transformation_to_com_dict(prepicom,affine_transform)
        transformed_com_list.append(transformed_com)
    return transformed_com_list
 
def apply_airlab_transformation_to_com_dict(com_dict,transform):
    for landmark,com in com_dict.items():
        com = np.array(com, dtype=float)/np.array([0.325,0.325,20])
        com_dict[landmark] = transform.forward_point(com)*np.array([0.325,0.325,20])
    return com_dict

def get_beth_coms_aligned_to_atlas(com_getter):
    prep_list = getcom.get_prep_list_for_rough_alignment_test()
    prep_list.append('DK52')
    transformed_com_list = []
    atlas_com = getcom.get_atlas_com()
    for prepi in prep_list:
        prepicom = com_getter(prepi)
        # print(prepi)
        # if prepi =='DK55':
        #     Breakpoint()
        rigid_transformation = get_rigid_transformation_from_dicts(prepicom,atlas_com)
        transformed_com = apply_rigid_transformation_to_com_dict(prepicom,rigid_transformation)
        transformed_com_list.append(transformed_com)
    return transformed_com_list