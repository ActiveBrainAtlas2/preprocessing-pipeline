from utilities.SqlController import SqlController
import numpy as np
from utilities.model.center_of_mass import CenterOfMass
from sql_setup import session

def query_brain_coms(brain, person_id=28, input_type_id=4):
    rows = session.query(CenterOfMass)\
        .filter(CenterOfMass.active.is_(True))\
        .filter(CenterOfMass.prep_id == brain)\
        .filter(CenterOfMass.person_id == person_id)\
        .filter(CenterOfMass.input_type_id == input_type_id)\
        .all()
    row_dict = {}
    for row in rows:
        structure = row.structure.abbreviation
        row_dict[structure] = np.array([row.x, row.y, row.section])*np.array([10,10,20])
    return row_dict

def get_atlas_centers(
        atlas_box_size=(1000, 1000, 300),
        atlas_box_scales=(10, 10, 20),
        atlas_raw_scale=10):
    atlas_box_scales = np.array(atlas_box_scales)
    atlas_box_size = np.array(atlas_box_size)
    atlas_box_center = atlas_box_size / 2
    sqlController = SqlController('Atlas')
    atlas_centers = sqlController.get_centers_dict('Atlas', input_type_id=1, person_id=16)
    for structure, center in atlas_centers.items():
        center = (atlas_box_center + np.array(center) * atlas_raw_scale / atlas_box_scales)*atlas_box_scales
        atlas_centers[structure] = center
    return atlas_centers

def get_brain_coms( person_id, input_type_id):
    brains_to_extract_common_structures = ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']
    brain_coms = {}
    for brain in brains_to_extract_common_structures:
        brain_coms[brain] = query_brain_coms(
            brain,
            person_id=person_id,
            input_type_id=input_type_id)
        if (brain, input_type_id) == ('DK55', 2):
            brain_coms[brain] = query_brain_coms(
                brain,
                person_id=person_id,
                input_type_id=4)
    return brain_coms

def get_bili_prep_list():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']

def get_bili_structure_list(no_prep_list_needed):
    brains_to_extract_common_structures = ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']
    common_structures = set()
    for brain in brains_to_extract_common_structures:
        common_structures = common_structures | set(query_brain_coms(brain).keys())
    common_structures = list(sorted(common_structures))
    return common_structures