<<<<<<< HEAD
from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from utilities.brain_specimens.get_com import get_atlas_com_dict,get_manual_annotation_from_beth
from utilities.alignment.align_point_sets import align_point_sets
import numpy as np
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_demons_transform
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_shared_landmarks_between_specimens

def get_common_com_from_dict(com_dict): 
    prep_list = get_prep_list_for_rough_alignment_test()
    prep_list.append('DK52')
    common_landmarks = get_shared_landmarks_between_specimens(prep_list)
    return np.array([com_dict[landmarki] for landmarki in common_landmarks])

def get_reference_com(prepi):
    reference_coms_dict = get_manual_annotation_from_beth(prepi)
    reference_com = get_common_com_from_dict(reference_coms_dict)
    return reference_com

def get_atlas_com():
    atlas_coms_dict = get_atlas_com_dict()
    atlas_com = get_common_com_from_dict(atlas_coms_dict)
    return atlas_com

def get_atlas_com_aligned_to_DK52():
    DK52_com = get_reference_com('DK52')
    atlas_com = get_atlas_com()
    rotation,translation = align_point_sets(atlas_com.T,DK52_com.T)
    transformed_coms = []
    for com in atlas_com:
        transformed_coms.append(com@rotation + translation.reshape(3))
    return np.array(transformed_coms)

def phys_to_thumbnail_coord(com):
    origin = np.array([31.2, 26, 40])
    spacing = np.array([41.6, 41.6, 80])
    return np.array(com)/spacing+origin

def thumbnail_to_phys_coord(com):
    origin = np.array([31.2, 26, 40])
    spacing = np.array([41.6, 41.6, 80])
    return np.array(com-origin)*spacing

def transform_point_demons(demons_transform,all_com):
    all_transformed_com = []
    for com in all_com:
        com_thumbnail_coord = phys_to_thumbnail_coord(com)
        transformed_com = demons_transform.TransformPoint(com_thumbnail_coord)
        transformed_com_phys = thumbnail_to_phys_coord(transformed_com)
        all_transformed_com.append(transformed_com_phys)
        print(com_thumbnail_coord - transformed_com)
    return np.array(all_transformed_com)

def get_demons_diagonastics():
    prep_list_for_rough_alignment = get_prep_list_for_rough_alignment_test()
    atlas_com_aligned_to_DK52 = get_atlas_com_aligned_to_DK52()
    transformation_displacement = []
    deviation_from_Beth_annotation = []
    for prepi in prep_list_for_rough_alignment:
        print('loading demons transformation for prep: '+prepi)
        demons_transform = get_demons_transform(prepi)
        reference_com = get_reference_com(prepi)
        transformed_com =  transform_point_demons(demons_transform,atlas_com_aligned_to_DK52)
        total_displacement = transformed_com - atlas_com_aligned_to_DK52
        deviation_from_manual = transformed_com - reference_com
        transformation_displacement.append(total_displacement)
        deviation_from_Beth_annotation.append(deviation_from_manual)
    transformation_displacement = np.array(transformation_displacement)
    deviation_from_Beth_annotation = np.array(deviation_from_Beth_annotation)
    return transformation_displacement,deviation_from_Beth_annotation
=======
from utilities.atlas.center_of_mass import align_atlas
from utilities.sqlcontroller import get_centers_dict
>>>>>>> 15c0d28f2be48a48d7dd5e04dbb796ced5d1f407
