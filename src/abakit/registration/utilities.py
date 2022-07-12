from .algorithm import umeyama
import numpy as np
import copy

def make_common_dictionary_entry_into_array(com_dict1,com_dict2):
    common_landmarks = (set(com_dict1.keys()).intersection(set(com_dict2.keys())))
    com_dict1 = np.array([com_dict1[landmark] for landmark in common_landmarks])
    com_dict2 = np.array([com_dict2[landmark] for landmark in common_landmarks])
    return com_dict1,com_dict2,common_landmarks

def get_similarity_transformation_from_dicts(moving,fixed):
    moving,fixed,_ = make_common_dictionary_entry_into_array(moving,fixed)
    similarity_transformation = umeyama(moving.T,fixed.T)
    return similarity_transformation

def get_and_apply_similarity_transform_to_dictionaries(moving,fixed):
    moving,fixed,common_landmarks = make_common_dictionary_entry_into_array(moving,fixed)
    transformed_coms,_= get_and_apply_similarity_transform(moving,fixed)
    return dict(zip(common_landmarks,transformed_coms))

def get_and_apply_similarity_transform(moving_com,fixed_com):
    similarity_transform = umeyama(moving_com.T,fixed_com.T)
    transformed_coms = apply_similarity_transform_to_points(moving_com,similarity_transform)
    return transformed_coms,similarity_transform

def apply_similarity_transformation_to_com(com,similarity_transformation):
    rotation,translation = similarity_transformation
    return rotation@np.array(com).reshape(3)+ translation.reshape(3)

def apply_similarity_transform_to_points(coms,similarity_transform):
    transformed_com_list = []
    for com in coms:
        transformed_com = apply_similarity_transformation_to_com(com,similarity_transform)
        transformed_com_list.append(transformed_com)
    return np.array(transformed_com_list)

def apply_similarity_transformation_to_com_dict(com_dict,similarity_transformation):
    for landmark,com in com_dict.items():
        com_dict[landmark] = apply_similarity_transformation_to_com(com,similarity_transformation)
    return com_dict

def apply_similarity_transformation_to_com_dict_list(com_dict_list,similarity_transformation):
    com_dict_list_copy = copy.deepcopy(com_dict_list)
    similarity_transformed_com_dicts = [apply_similarity_transformation_to_com_dict(com_dict,similarity_transformation) for com_dict in com_dict_list_copy]
    return similarity_transformed_com_dicts