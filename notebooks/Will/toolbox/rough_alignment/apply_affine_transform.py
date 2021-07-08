import numpy as np
import SimpleITK as sitk

def phys_to_thumbnail_coord(com):
    spacing = np.array([10,10,20])
    return np.array(com)/spacing

def thumbnail_to_phys_coord(com):
    spacing = np.array([10,10,20])
    return np.array(com)*spacing

def transform_point_affine(affine_transform,all_com):
    all_transformed_com = []
    for com in all_com:
        transformed_com = affine_transform.TransformPoint(com)
        all_transformed_com.append(transformed_com)
    return np.array(all_transformed_com)

def transform_dict_affine(affine_transform,com_dict):
    for structure,com in com_dict.items():
        com_dict[structure] = affine_transform.TransformPoint(com)
    return com_dict
