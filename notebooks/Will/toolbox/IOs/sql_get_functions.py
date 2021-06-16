from utilities.sqlcontroller import SqlController
import sys
from pathlib import Path
PIPELINE_ROOT = Path('.').absolute().parents[2]
sys.path.append(PIPELINE_ROOT.as_posix())
from sql_setup import session
import numpy as np
from utilities.model.center_of_mass import CenterOfMass

def get_atlas_centers():
    sqlController = SqlController('Atlas')
    lauren_person_id = 16
    input_type_manual = 1
    atlas_centers = sqlController.get_centers_dict('Atlas',
                                                   input_type_id=input_type_manual,
                                                   person_id=lauren_person_id)
    return atlas_centers

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