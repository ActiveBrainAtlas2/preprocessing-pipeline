import numpy as np
global image_scale , atlas_scale

image_scale=(0.325, 0.325, 20)
atlas_scale=(10, 10, 20)
atlas_scale = np.diag(atlas_scale)
image_scale = np.diag(image_scale)

def get_column_vector(vector):
    return np.array(vector).reshape(3, 1)

def image_to_physical_coord(image_coord):
    global image_scale
    image_coord_column_vector = get_column_vector(image_coord)
    physical_coord = image_scale @ image_coord_column_vector
    return physical_coord.reshape(3)

def physical_to_atlas_coord(coord_phys):
    global atlas_scale
    atlas_coord = np.linalg.inv(atlas_scale) @ get_column_vector(coord_phys)
    return atlas_coord.reshape(3)

def atlas_to_physical_coord(atlas_coord):
    global atlas_scale
    atlas_coord_column_vector = get_column_vector(atlas_coord)
    physical_coord = atlas_scale@atlas_coord_column_vector
    return physical_coord.reshape(3)

def physical_to_image_coord(coord_phys):
    global image_scale
    image_coord = np.linalg.inv(image_scale) @ get_column_vector(coord_phys)
    return image_coord.reshape(3)

def atlas_to_image_coord(atlas_coord):
    global atlas_scale,image_scale
    coord_phys = atlas_to_physical_coord(atlas_coord)
    image_coord = physical_to_image_coord(coord_phys)
    return image_coord.reshape(3)

def image_to_atlas_coord(image_coord):
    physical_coordinate = image_to_physical_coord(image_coord)
    return physical_to_atlas_coord(physical_coordinate)

def image_to_thumbnail_coord(image_coord):
    return np.array(image_coord)/np.array([32,32,1])

def thumbnail_to_image_coord(thumb_nail_coord):
    return np.array(thumb_nail_coord)*np.array([32,32,1])

def atlas_to_thumbnail_coord(atlas_coord):
    image_coord = atlas_to_image_coord(atlas_coord)
    return image_to_thumbnail_coord(image_coord)

def physical_to_thumbnail_coord(physical_coord):
    image_coord = physical_to_image_coord(physical_coord)
    return image_to_thumbnail_coord(image_coord)

def thumbnail_to_atlas_coord(thumbnail_coord):
    image_coord = thumbnail_to_image_coord(thumbnail_coord)
    return image_to_atlas_coord(image_coord)

def thumbnail_to_atlas_coord(thumbnail_coord):
    image_coord = thumbnail_to_image_coord(thumbnail_coord)
    return image_to_atlas_coord(image_coord)