import numpy as np
from skimage.measure import grid_points_in_poly

def contours_to_mask(contours, img_shape):
    """
    img_shape: h,w
    """

    final_masks = []

    for cnt in contours:

        bg = np.zeros(img_shape, bool)
        xys = points_inside_contour(cnt.astype(np.int))
        bg[np.minimum(xys[:,1], bg.shape[0]-1), np.minimum(xys[:,0], bg.shape[1]-1)] = 1

        final_masks.append(bg)

    final_mask = np.any(final_masks, axis=0)
    return final_mask


def points_inside_contour(cnt, num_samples=None):
    xmin, ymin = cnt.min(axis=0)
    xmax, ymax = cnt.max(axis=0)
    h, w = (ymax-ymin+1, xmax-xmin+1)
    inside_ys, inside_xs = np.where(grid_points_in_poly((h, w), cnt[:, ::-1]-(ymin,xmin)))

    if num_samples is None:
        inside_points = np.c_[inside_xs, inside_ys] + (xmin, ymin)
    else:
        n = inside_ys.size
        random_indices = np.random.choice(range(n), min(1000, n), replace=False)
        inside_points = np.c_[inside_xs[random_indices], inside_ys[random_indices]]

    return inside_points
