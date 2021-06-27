from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.rough_alignment.diagnostics import get_atlas_com,get_reference_com
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from utilities.alignment.align_point_sets import align_point_sets,get_and_apply_transform
import numpy as np 

def get_DK52_com_aligned_to_prepi(prepi):
    DK52_com = get_reference_com('DK52')
    print('loading demons transformation for prep: '+prepi)
    affine_transform = get_affine_transform(prepi)
    DK52_com_aligned =  transform_point_affine(affine_transform,DK52_com)
    return DK52_com_aligned

def get_transformed_coms():
    prep_list_for_rough_alignment = get_prep_list_for_rough_alignment_test()
    atlas_com = get_atlas_com()
    transformed_coms = []
    for prepi in prep_list_for_rough_alignment:
        DK52_com_aligned_to_prep = get_DK52_com_aligned_to_prepi(prepi)
        DK52_com_aligned_to_atlas,_= get_and_apply_transform(DK52_com_aligned_to_prep,atlas_com)
        transformed_coms.append(DK52_com_aligned_to_atlas)
    transformed_coms = np.array(transformed_coms)
    return transformed_coms

def get_deviation_from_atlas_com():
    transformed_coms = get_transformed_coms()
    atlas_com = get_atlas_com()
    nprep = transformed_coms.shape[0]
    com_diff = []
    for prepi in range(nprep):
        difference = transformed_coms[prepi]-atlas_com
        com_diff.append(difference)
    return np.array(com_diff)