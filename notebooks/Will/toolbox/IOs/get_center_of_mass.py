import numpy as np
from notebooks.Will.toolbox.IOs.get_specimen_lists import get_list_of_brains_to_align
from notebooks.Will.toolbox.IOs.sql_get_functions import get_atlas_centers,get_center_of_mass


def get_atlas_centers_in_physical_coord():
    atlas_centers_physical_coord  = get_atlas_centers
    atlas_centers = transform_atlas_centers_to_neuroglancer_coord(atlas_centers_physical_coord)
    return atlas_centers

def transform_atlas_centers_to_neuroglancer_coord(atlas_centers,
              atlas_origin=np.array([500, 500, 150]),
              atlas_to_neuroglancer = np.array([1, 1, 0.5])):
    for structure, center in atlas_centers.items():
        transformed_center = atlas_origin + np.array(center) * atlas_to_neuroglancer
        atlas_centers[structure] = transformed_center
    return atlas_centers


def get_com_for_multiple_brains(brains, person_id, input_type_id):
    brain_coms = {}
    for brain in brains:
        brain_coms[brain] = get_center_of_mass(
            brain,
            person_id=person_id,
            input_type_id=input_type_id
        )
        if (brain, input_type_id) == ('DK55', 2):
            brain_coms[brain] = get_center_of_mass(
                brain,
                person_id=person_id,
                input_type_id=4
            )
    return brain_coms
