import numpy as np
def align_point_sets(moving_points, still_points, with_scaling=True):
    assert moving_points.shape == still_points.shape
    assert len(moving_points.shape) == 2
    m, n = moving_points.shape  # dimension, number of points

    moving_points_mean = np.mean(moving_points, axis=1).reshape(-1, 1)
    still_points_mean = np.mean(still_points, axis=1).reshape(-1, 1)

    moving_points_centered = moving_points - moving_points_mean
    still_points_centered = still_points - still_points_mean

    u, s, vh = np.linalg.svd(still_points_centered @ moving_points_centered.T / n)

    # deal with reflection
    e = np.ones(m)
    if np.linalg.det(u) * np.linalg.det(vh) < 0:
        print('reflection detected')
        e[-1] = -1

    rotation = u @ np.diag(e) @ vh

    if with_scaling:
        moving_points_var = (moving_points_centered ** 2).sum(axis=0).mean()
        c = sum(s * e) / moving_points_var
        rotation *= c

    translation = still_points_mean - rotation @ moving_points_mean

    return rotation, translation

def get_and_apply_transform(moving_com,still_com):
    affine_transform = align_point_sets(moving_com.T,still_com.T)
    transformed_coms = apply_affine_transform_to_points(moving_com,affine_transform)
    return transformed_coms,affine_transform

def apply_affine_transform_to_points(coms,affine_transform):
    rotation,translation = affine_transform
    transformed_coms = []
    for com in coms:
        transformed_coms.append(rotation@com.reshape(3)+ translation.reshape(3))
    return np.array(transformed_coms)