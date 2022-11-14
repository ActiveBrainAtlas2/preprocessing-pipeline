def get_shared_elements_among_lists(lists):
    shared_elements = set(lists[0])
    for listi in lists:
        shared_elements.intersection_update(listi)
    shared_elements = list(sorted(shared_elements))
    return shared_elements

def get_shared_coms(com1,com2):
    landmarks = [list(com1.keys()),list(com2.keys())]
    shared_landmarks = get_shared_elements_among_lists(landmarks)
    com1_shared = [com1[landmarki] for landmarki in shared_landmarks]
    com2_shared = [com2[landmarki] for landmarki in shared_landmarks]
    return(com1_shared,com2_shared,shared_landmarks)