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
        # com_thumbnail_coord = phys_to_thumbnail_coord(com)
        transformed_com = affine_transform.TransformPoint(com)
        # transformed_com_phys = thumbnail_to_phys_coord(transformed_com)
        all_transformed_com.append(transformed_com)
    return np.array(all_transformed_com)