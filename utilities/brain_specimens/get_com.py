import numpy as np
from utilities.model.layer_data import LayerData 
from sql_setup import session

def pixel_to_physical_coord(com):
    return com*np.array([0.325,0.325,20])

def atlas_to_physical_coord(com):
    return (com*10/np.array([10,10,20])+np.array([500,500,150]))*np.array([10,10,20])

def get_com_dict(prep_id,person_id,input_type_id,scale_function):
    query_results = session.query(LayerData)\
        .filter(LayerData.active.is_(True))\
        .filter(LayerData.prep_id == prep_id)\
        .filter(LayerData.person_id == person_id)\
        .filter(LayerData.input_type_id == input_type_id)\
        .filter(LayerData.layer == 'COM')\
        .all()
    center_of_mass = {}
    for row in query_results:
        structure = row.structure.abbreviation
        com = np.array([row.x, row.y, row.section])
        center_of_mass[structure] = scale_function(com)
    return center_of_mass

def get_atlas_com_dict():
    PERSON_ID_LAUREN = 16
    INPUT_TYPE_MANUAL = 1
    center_of_mass = get_com_dict('Atlas',PERSON_ID_LAUREN,INPUT_TYPE_MANUAL,atlas_to_physical_coord)
    return center_of_mass

def get_manual_annotation_from_beth(prep_id):
    PERSON_ID_BETH = 2
    INPUT_TYPE_MANUAL = 1
    center_of_mass = get_com_dict(prep_id,PERSON_ID_BETH,INPUT_TYPE_MANUAL,pixel_to_physical_coord)
    return center_of_mass

def pixel_to_physcial_coord(coordinate):
    return(np.array(coordinate)*np.array([0.325,0.325,20]))