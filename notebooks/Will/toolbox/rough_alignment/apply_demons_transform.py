import numpy as np

def phys_to_thumbnail_coord(com):
    origin = np.array([31.2, 26, 40])
    return np.array(com)+origin

def thumbnail_to_phys_coord(com):
    origin = np.array([31.2, 26, 40])
    return np.array(com)-origin

def transform_point_demons(demons_transform,all_com):
    all_transformed_com = []
    for com in all_com:
        com_thumbnail_coord = phys_to_thumbnail_coord(com)
        transformed_com = np.array(demons_transform.TransformPoint(com_thumbnail_coord))
        transformed_com_phys = thumbnail_to_phys_coord(transformed_com)
        all_transformed_com.append(transformed_com_phys)
    return np.array(all_transformed_com)

def transform_dict_demons(demons_transform,com_dict):
    for structure,com in com_dict.items():
        com_thumbnail_coord = phys_to_thumbnail_coord(com)
        transformed_com = np.array(demons_transform.TransformPoint(com_thumbnail_coord))
        transformed_com_phys = thumbnail_to_phys_coord(transformed_com)
        com_dict[structure] = transformed_com_phys
    return com_dict