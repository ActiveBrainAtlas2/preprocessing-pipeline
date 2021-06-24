import numpy as np

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