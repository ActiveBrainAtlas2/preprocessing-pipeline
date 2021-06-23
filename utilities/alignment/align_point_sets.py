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