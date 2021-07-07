import sys
sys.path.append('/home/zhw272/programming/pipeline_utility/')
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_dict_affine
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_point_demons
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
from notebooks.Will.toolbox.IOs.get_bilis_json_file import *
# from notebooks.Will.toolbox.IOs.get_bilis_coms import *
from utilities.alignment.align_point_sets import align_point_sets,apply_affine_transform_to_com
import notebooks.Will.experimental.get_coms_from_pickle as getcom
import notebooks.Will.toolbox.plotting.plot_com_offset as offsetplotter
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens
def apply_DK52_alignment_to_atlas_to_com_dict(com_dict,affine_transformation):
    for landmark,com in com_dict.values():
        com_dict[landmark] = apply_affine_transform_to_com(com,affine_transformation)
    return com_dict

def get_DK52_rigid_transformation():
    DK52_com = getcom.get_dk52_com()
    atlas_com = getcom.get_atlas_com()
    common_landmarks = (set(DK52_com.keys()).intersection(set(atlas_com.keys())))
    DK52_com = np.array([DK52_com[landmark] for landmark in common_landmarks])
    atlas_com = np.array([atlas_com[landmark] for landmark in common_landmarks])
    rigid_transformation = align_point_sets(DK52_com,atlas_com)
    return rigid_transformation

def get_itk_affine_transformed_coms():
    prep_list = getcom.get_prep_list_for_rough_alignment_test()
    transformed_com_list = []
    for prepi in prep_list:
        affine_transform = get_affine_transform(prepi)
        prepicom = getcom.get_prepi_com(prepi)
        transformed_com = transform_dict_affine(affine_transform,prepicom)
        transformed_com_list.append(transformed_com)
    return transformed_com_list

def apply_airlab_transformation_to_com_dict(com_dict,transform):
    for landmark,com in com_dict.values():
        com = np.array(com, dtype=float)/np.array([0.325,0.325,20])
        com_dict[landmark] = transform.forward_point(com)*np.array([0.325,0.325,20])
    return com_dict

if __name__ == '__main__':
    prep_coms = getcom.get_prep_coms()
    rigid_transformation = get_DK52_rigid_transformation()
    itk_transformed_coms = get_itk_affine_transformed_coms()
    # airlab_transformed_coms = [apply_airlab_transformation_to_com_dict(comi) for comi in prep_coms]
    prep_list_function = getcom.get_prep_list_for_rough_alignment_test
    landmark_list_function = get_all_landmarks_in_specimens
    title = 'DK52 annotation to transformed coms'
    offsetplotter.plot_offset_between_two_com_sets(prep_coms,itk_transformed_coms,
    prep_list_function = prep_list_function,
    landmark_list_function = landmark_list_function,
    title = title)