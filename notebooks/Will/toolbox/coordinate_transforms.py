import numpy as np
global image_scale , atlas_scale

image_scale=(0.325, 0.325, 20),
atlas_scale=(10, 10, 20)

def get_column_vector(vector):
    return np.array(vector).reshape(3, 1)

def image_to_physical_coord(image_coord):
    global image_scale
    image_scale = np.diag(image_scale)
    image_coord_column_vector = get_column_vector(image_coord)
    physical_coord = image_scale @ image_coord_column_vector
    return physical_coord

def physical_to_atlas_coord(coord_phys):
    global atlas_scale
    atlas_scale = np.diag(atlas_scale)
    atlas_coord = np.linalg.inv(atlas_scale) @ get_column_vector((coord_phys))
    return atlas_coord

def atlas_to_physical_coord(atlas_coord):
    global atlas_scale
    atlas_coord_column_vector = get_column_vector(atlas_coord)
    physical_coord = atlas_scale@atlas_coord_column_vector
    return physical_coord

def physical_to_image_coord(coord_phys):
    global image_scale
    image_scale = np.diag(image_scale)
    image_coord = np.linalg.inv(image_scale) @ get_column_vector((coord_phys)
    return image_coord

def atlas_to_image_coord(atlas_coord):
    global atlas_scale,image_scale
    coord_phys = atlas_to_physical_coord(atlas_coord)
    image_coord = physical_to_image_coord(coord_phys)
    return image_coord
