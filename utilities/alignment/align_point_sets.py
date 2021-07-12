import numpy as np
import copy

def align_point_sets(moving_points, still_points, with_scaling=True):
    assert moving_points.shape == still_points.shape
    assert len(moving_points.shape) == 2
    n_dim, n_points = moving_points.shape
    moving_points_mean = np.mean(moving_points, axis=1).reshape(-1, 1)
    still_points_mean = np.mean(still_points, axis=1).reshape(-1, 1)
    moving_points_centered = moving_points - moving_points_mean
    still_points_centered = still_points - still_points_mean
    u, s, vh = np.linalg.svd(still_points_centered @ moving_points_centered.T / n_points)
    e = np.ones(n_dim)
    there_is_reflection = lambda u,vh : np.linalg.det(u) * np.linalg.det(vh) < 0
    if there_is_reflection:
        print('reflection detected')
        e[-1] = -1
    rotation = u @ np.diag(e) @ vh
    if with_scaling:
        moving_points_var = (moving_points_centered ** 2).sum(axis=0).mean()
        c = sum(s * e) / moving_points_var
        rotation *= c
    translation = still_points_mean - rotation @ moving_points_mean
    return rotation, translation

def get_rigid_transformation_from_dicts(com_dict1,com_dict2):
    common_landmarks = (set(com_dict1.keys()).intersection(set(com_dict2.keys())))
    com_dict1 = np.array([com_dict1[landmark] for landmark in common_landmarks])
    com_dict2 = np.array([com_dict2[landmark] for landmark in common_landmarks])
    rigid_transformation = align_point_sets(com_dict1.T,com_dict2.T)
    return rigid_transformation

def get_and_apply_transform(moving_com,still_com):
    affine_transform = align_point_sets(moving_com.T,still_com.T)
    transformed_coms = apply_rigid_transform_to_points(moving_com,affine_transform)
    return transformed_coms,affine_transform

def apply_rigid_transformation_to_com(com,rigid_transformation):
    rotation,translation = rigid_transformation
    return rotation@np.array(com).reshape(3)+ translation.reshape(3)

def apply_rigid_transform_to_points(coms,rigid_transform):
    transformed_com_list = []
    for com in coms:
        transformed_com = apply_rigid_transformation_to_com(com,rigid_transform)
        transformed_com_list.append(transformed_com)
    return np.array(transformed_com_list)

def apply_rigid_transformation_to_com_dict(com_dict,rigid_transformation):
    for landmark,com in com_dict.items():
        com_dict[landmark] = apply_rigid_transformation_to_com(com,rigid_transformation)
    return com_dict

def apply_rigid_transformation_to_com_dict_list(com_dict_list,rigid_transformation):
    com_dict_list_copy = copy.deepcopy(com_dict_list)
    rigid_transformed_com_dicts = [apply_rigid_transformation_to_com_dict(com_dict,rigid_transformation) for com_dict in com_dict_list_copy]
    return rigid_transformed_com_dicts