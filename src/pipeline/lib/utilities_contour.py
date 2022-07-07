import numpy as np
def get_contours_from_annotations(prep_id, target_structure, hand_annotations, densify=0):
    num_annotations = len(hand_annotations)
    contours_for_structurei = {}
    for i in range(num_annotations):
        structure = hand_annotations['name'][i]
        side = hand_annotations['side'][i]
        section = hand_annotations['section'][i]
        first_section = 0
        last_section = 0
        if side == 'R' or side == 'L':
            structure = structure + '_' + side
        if structure == target_structure:
            vertices = hand_annotations['vertices'][i]
            for _ in range(densify):
                vertices = get_dense_coordinates(vertices)
            if is_bad_section_for_MD585(prep_id,section):
                continue
            contours_for_structurei[section] = vertices
    try:
        first_section = np.min(list(contours_for_structurei.keys()))
        last_section = np.max(list(contours_for_structurei.keys()))
    except:
        pass
    return contours_for_structurei, first_section, last_section

def is_bad_section_for_MD585(stack,section):
    # Skip sections before the 22nd prep2 section for MD585 as there are clear errors
    MD585_ng_section_min = 83
    return stack == 'MD585XXX' and section < MD585_ng_section_min + 22

def get_dense_coordinates(coor_list):
    dense_coor_list = []
    for i in range(len(coor_list) - 1):
        x, y = coor_list[i]
        x_next, y_next = coor_list[i + 1]
        x_mid = (x + x_next) / 2
        y_mid = (y + y_next) / 2
        dense_coor_list.append([x, y])
        dense_coor_list.append([x_mid, y_mid])
        if i == len(coor_list) - 2:
            dense_coor_list.append([x_next, y_next])
            x, y = coor_list[0]
            x_mid = (x + x_next) / 2
            y_mid = (y + y_next) / 2
            dense_coor_list.append([x_mid, y_mid])
    return dense_coor_list