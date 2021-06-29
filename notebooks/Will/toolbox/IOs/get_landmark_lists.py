from utilities.model.layer_data import LayerData
from sql_setup import session
from utilities.brain_specimens.get_com import get_atlas_com_dict,get_manual_annotation_from_beth

def get_shared_landmarks_between_specimens(prep_ids):
    last_prep = prep_ids.pop()
    shared_landmarks = set(get_list_of_landmarks_in_prep(last_prep))
    for prepi in prep_ids:
        landmarks_in_prepi = get_list_of_landmarks_in_prep(prepi)
        shared_landmarks.intersection_update(landmarks_in_prepi)
    shared_landmarks = list(sorted(shared_landmarks))
    return shared_landmarks

def get_all_landmarks_in_specimens(prep_ids):
    last_prep = prep_ids.pop()
    shared_landmarks = set(get_list_of_landmarks_in_prep(last_prep))
    for prepi in prep_ids:
        landmarks_in_prepi = set(get_list_of_landmarks_in_prep(prepi))
        shared_landmarks = shared_landmarks|landmarks_in_prepi
    shared_landmarks = list(sorted(shared_landmarks))
    return shared_landmarks

def get_list_of_landmarks_in_prep(prepid):
    query_result = session.query(LayerData)\
            .filter(LayerData.active.is_(True))\
            .filter(LayerData.prep_id == prepid)\
            .filter(LayerData.input_type_id == 2)\
            .filter(LayerData.person_id == 2)\
            .all()
    landmarks = [entryi.structure.abbreviation for entryi in query_result]
    return landmarks

def get_shared_landmark_with_atlas(prepid):
    atlas_landmarks = set(get_atlas_landmarks())
    prep_landmarks = set(get_list_of_landmarks_in_prep(prepid))
    return list(atlas_landmarks & prep_landmarks)

def get_atlas_landmarks():
    atlas_com_dict = get_atlas_com_dict()
    landmarks = list(atlas_com_dict.keys())
    return landmarks

def get_union_landmark_with_atlas(prepid):
    atlas_landmarks = set(get_atlas_landmarks())
    prep_landmarks = set(get_list_of_landmarks_in_prep(prepid))
    return list(atlas_landmarks | prep_landmarks)