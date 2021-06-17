from notebooks.Will.toolbox.IOs.get_center_of_mass import  get_com_for_multiple_brains

def get_all_landmarks():
    ...

def get_shared_landmarks_between_specimens(list_of_brains, person_id=28, input_type_id=2):
    coms = get_com_for_multiple_brains(brains=list_of_brains,person_id = person_id,
                                input_type_id = input_type_id)
    shared_landmarks = set()
    for com in coms.values():
        shared_landmarks = shared_landmarks | set(com.keys())
    shared_landmarks = list(sorted(shared_landmarks))
    return shared_landmarks
