import numpy as np

def transform_list_affine(affine_transform,all_com):
    """apply sitk affine transform on a list of coms"""
    all_transformed_com = []
    for com in all_com:
        transformed_com = affine_transform.TransformPoint(com)
        all_transformed_com.append(transformed_com)
    return np.array(all_transformed_com)

def transform_dict_affine(affine_transform,com_dict):
    """transform_dict_affine [apply sitk affine transform on a dictionay of coms]

    :param affine_transform: [sitk affine transform object]
    :type affine_transform: [sitk affine transform object]
    :param com_dict: [com dictionary, keys are structure names values are tuple,list or np.array of len 3]
    :type com_dict: [diction]
    :return: [description]
    :rtype: [type]
    """
    transformed_com = {}
    for structure,com in com_dict.items():
        com_dict[structure] = affine_transform.TransformPoint(com)
    return com_dict
