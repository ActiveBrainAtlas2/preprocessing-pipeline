from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from utilities.alignment.align_point_sets import align_point_sets
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_demons_transform
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_point_demons
import numpy as np
from notebooks.Will.toolbox.rough_alignment.diagnostics import get_atlas_com,get_reference_com

def get_atlas_com_aligned_to_DK52():
    DK52_com = get_reference_com('DK52')
    atlas_com = get_atlas_com()
    rotation,translation = align_point_sets(atlas_com.T,DK52_com.T)
    transformed_coms = []
    for com in atlas_com:
        transformed_coms.append(rotation@com.reshape(3)+ translation.reshape(3))
    return np.array(transformed_coms)

def get_demons_diagonastics():
    prep_list_for_rough_alignment = get_prep_list_for_rough_alignment_test()
    atlas_com_aligned_to_DK52 = get_atlas_com_aligned_to_DK52()
    reference_coms = []
    transformed_coms = []
    for prepi in prep_list_for_rough_alignment:
        print('loading demons transformation for prep: '+prepi)
        demons_transform = get_demons_transform(prepi)
        reference_com = get_reference_com(prepi)
        transformed_com =  transform_point_demons(demons_transform,atlas_com_aligned_to_DK52)
        transformed_coms.append(transformed_com)
        reference_coms.append(reference_com)
    transformed_coms = np.array(transformed_coms)
    reference_coms = np.array(reference_coms)
    return reference_coms,transformed_coms,atlas_com_aligned_to_DK52



