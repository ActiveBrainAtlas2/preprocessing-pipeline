import numpy as np
from utilities.model.center_of_mass import CenterOfMass
from sql_setup import session

def get_atlas_center_of_mass():
    com = get_center_of_mass("Atlas", person_id=1, input_type_id=4)
    return com

def get_center_of_mass(brain, person_id=28, input_type_id=4):
    query_results = session.query(CenterOfMass)\
        .filter(CenterOfMass.active.is_(True))\
        .filter(CenterOfMass.prep_id == brain)\
        .filter(CenterOfMass.person_id == person_id)\
        .filter(CenterOfMass.input_type_id == input_type_id)\
        .all()
    center_of_mass = {}
    for row in query_results:
        structure = row.structure.abbreviation
        center_of_mass[structure] = np.array([row.x, row.y, row.section])
    return center_of_mass

def get_com_for_multiple_brains(brains, person_id, input_type_id):
    brain_coms = {}
    for brain in brains:
        brain_coms[brain] = get_center_of_mass(
            prep_id = brain,
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
