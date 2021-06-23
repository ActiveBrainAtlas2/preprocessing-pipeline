from utilities.model.layer_data import LayerData
from sql_setup import session

def get_shared_landmarks_between_specimens(prep_ids):
    last_prep = prep_ids.pop()
    shared_landmarks = set(get_list_of_landmarks_in_prep(last_prep))
    for prepi in prep_ids:
        landmarks_in_prepi = get_list_of_landmarks_in_prep(prepi)
        shared_landmarks.intersection_update(landmarks_in_prepi)
    shared_landmarks = list(sorted(shared_landmarks))
    return shared_landmarks

def get_list_of_landmarks_in_prep(prepid):
    query_result = session.query(LayerData)\
            .filter(LayerData.active.is_(True))\
            .filter(LayerData.prep_id == prepid)\
            .filter(LayerData.input_type_id == 1)\
            .filter(LayerData.person_id == 2)\
            .all()
    landmarks = [entryi.structure.abbreviation for entryi in query_result]
    return landmarks
