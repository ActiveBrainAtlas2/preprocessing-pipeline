import numpy as np

def brain_to_physical_coord(brain_coord, brain_scale):
    brain_scale = np.diag(brain_scale)
    brain_coord_column_vector = np.array(brain_coord).reshape(3, 1)
    physical_coord = brain_scale @ brain_coord_column_vector
    return physical_coord

def get_translation_in_physical_scale(brain_scale,translation):
    brain_scale = np.diag(brain_scale)
    physical_translation = brain_scale @ translation
    return physical_translation

def physical_to_atlas_coord(coord_phys,atlas_scale):
    atlas_scale = np.diag(atlas_scale)
    atlas_coord = np.linalg.inv(atlas_scale) @ coord_phys
    return atlas_coord

def brain_to_atlas_transform(
        brain_coord, rotation, translation,
        brain_scale=(0.325, 0.325, 20),
        atlas_scale=(10, 10, 20)
):
    physical_coord = brain_to_physical_coord(brain_coord, brain_scale)
    physical_translation = get_translation_in_physical_scale(brain_scale,translation)
    transformed_physical_coord = rotation @ physical_coord + physical_translation
    atlas_coord = physical_to_atlas_coord(transformed_physical_coord,atlas_scale)
    return atlas_coord.T[0]