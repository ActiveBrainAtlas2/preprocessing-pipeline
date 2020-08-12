from collections import defaultdict
from itertools import groupby
import os, sys
import numpy as np
from shapely.geometry import Polygon
from skimage.measure import grid_points_in_poly

XY_PIXEL_DISTANCE_LOSSLESS = 0.46 # This is the spec for Nanozoomer
XY_PIXEL_DISTANCE_TB = XY_PIXEL_DISTANCE_LOSSLESS * 32 # in um, thumbnail

# def images_to_volume(images, voxel_size, first_sec=None, last_sec=None):
#     """
#     Assume section 1 is at z = 0.

#     Args:
#         images (dict of 2D images): key is section index. First section has index 1.
#         voxel_size ((3,)-array): (xdim,ydim,zdim) in unit of pixel size.
#         firse_sec (int): the beginning section of the bounding box.  Default is the the smallest key of `images`.
#         last_sec (int): the ending section of the bounding box. Default is the the largest key of `images`.

#     Returns:
#         (volume, bbox): bbox is wrt to wholebrainXYcropped.
#     """

#     if isinstance(images, dict):
#         ydim, xdim = images.values()[0].shape[:2]
#         sections = images.keys()
#         if last_sec is None:
#             last_sec = np.max(sections)
#         if first_sec is None:
#             first_sec = np.min(sections)
#     elif callable(images):
#         try:
#             ydim, xdim = images(100).shape[:2]
#         except:
#             ydim, xdim = images(200).shape[:2]
#         assert last_sec is not None
#         assert first_sec is not None
#     else:
#         raise Exception('images must be dict or function.')

#     voxel_z_size = voxel_size[2]

#     z_end = int(np.ceil(last_sec*voxel_z_size))
#     z_begin = int(np.floor((first_sec-1)*voxel_z_size))
#     zdim = z_end + 1 - z_begin

#     # print 'Volume shape:', xdim, ydim, zdim

#     volume = np.zeros((ydim, xdim, zdim), images.values()[0].dtype)

#     for i in range(len(images.keys())-1):
#         z1 = int(np.floor((sections[i]-1) * voxel_z_size))
#         z2 = int(np.ceil(sections[i+1] * voxel_z_size))
#         if isinstance(images, dict):
#             im = images[sections[i]]
#         elif callable(images):
#             im = images(sections[i])
#         volume[:, :, z1-z_begin:z2+1-z_begin] = im[..., None]

#     volume_bbox = np.array([0,xdim-1,0,ydim-1,z_begin,z_end])
#     return volume, volume_bbox
from .imported_atlas_utilities import convert_section_to_z


def points2d_to_points3d(pts2d_grouped_by_section, pts2d_downsample, pts3d_downsample, stack, pts3d_origin=(0,0,0)):
    """
    Args:
        pts2d_downsample ((n,2)-ndarray): 2D point (x,y) coordinates on cropped images, in pts2d_downsample resolution.
        pts3d_origin (3-tuple): xmin, ymin, zmin in pts3d_downsample resolution.

    Returns:
        ((n,3)-ndarray)
    """

    pts3d = {}
    for sec, pts2d in list(pts2d_grouped_by_section.items()):
        z_down = np.mean(convert_section_to_z(stack=stack, sec=sec, downsample=pts3d_downsample))
        n = len(pts2d)
        xys_down = np.array(pts2d) * pts2d_downsample / pts3d_downsample
        pts3d[sec] = np.c_[xys_down, z_down*np.ones((n,))] - pts3d_origin

    return pts3d


def contours_to_volume(contours_grouped_by_label=None, label_contours_tuples=None, interpolation_direction='z',
                      return_shell=False, len_interval=20):
    """
    Return volume as 3D array, and origin (xmin,xmax,ymin,ymax,zmin,zmax)

    Args:
        contours_grouped_by_label ({int: list of (3,n)-arrays}):

    """

    if label_contours_tuples is not None:
        contours_grouped_by_label = {}
        for label, contours in groupby(label_contours_tuples, key=lambda l, cnts: l):
            contours_grouped_by_label[label] = contours
    else:
        assert contours_grouped_by_label is not None

    if isinstance(list(contours_grouped_by_label.values())[0], dict):
        # dict value is contours grouped by z
        if interpolation_direction == 'z':
            contours_xyz_grouped_by_label = {label: [(x,y,z) for z, (x,y) in list(contours_grouped.items())]
                            for label, contours_grouped in list(contours_grouped_by_label.items())}
        elif interpolation_direction == 'y':
            contours_xyz_grouped_by_label = {label: [(x,y,z) for y, (x,z) in list(contours_grouped.items())]
                            for label, contours_grouped in list(contours_grouped_by_label.items())}
        elif interpolation_direction == 'x':
            contours_xyz_grouped_by_label = {label: [(x,y,z) for x, (y,z) in list(contours_grouped.items())]
                            for label, contours_grouped in list(contours_grouped_by_label.items())}

    else:
        contours_xyz_grouped_by_label = contours_grouped_by_label
        # dict value is list of (x,y,z) tuples
#         contours_grouped_by_label = {groupby(contours_xyz, lambda x,y,z: z)
#                                      for label, contours_xyz in contours_grouped_by_label.iteritems()}
#         pass

    xyz_max = [0, 0, 0]
    xyz_min = [np.inf, np.inf, np.inf]
    for label, contours in list(contours_xyz_grouped_by_label.items()):
        xyz_max = np.maximum(xyz_max, np.max(np.vstack(contours), axis=0))
        xyz_min = np.minimum(xyz_min, np.min(np.vstack(contours), axis=0))

    xmin, ymin, zmin = np.floor(xyz_min).astype(np.int)
    xmax, ymax, zmax = np.ceil(xyz_max).astype(np.int)
    xdim, ydim, zdim = xmax+1-xmin, ymax+1-ymin, zmax+1-zmin


    volume = np.zeros((ydim, xdim, zdim), np.uint8)

    if return_shell:

        for label, contours in list(contours_grouped_by_label.items()):

            voxels_grouped = interpolate_contours_to_volume(interpolation_direction=interpolation_direction,
                                                            contours_xyz=contours, return_contours=True,
                                                            len_interval=len_interval)

            if interpolation_direction == 'z':
                for z, xys in list(voxels_grouped.items()):
                    volume[xys[:,1]-ymin, xys[:,0]-xmin, z-zmin] = label
            elif interpolation_direction == 'y':
                for y, xzs in list(voxels_grouped.items()):
                    volume[y-ymin, xzs[:,0]-xmin, xzs[:,1]-zmin] = label
            elif interpolation_direction == 'x':
                for x, yzs in list(voxels_grouped.items()):
                    volume[yzs[:,0]-ymin, x-xmin, yzs[:,1]-zmin] = label

        return volume, (xmin,xmax,ymin,ymax,zmin,zmax)

    else:

        for label, contours in list(contours_grouped_by_label.items()):

            voxels_grouped = interpolate_contours_to_volume(interpolation_direction=interpolation_direction,
                                                                 contours_xyz=contours, return_voxels=True)

            if interpolation_direction == 'z':
                for z, xys in list(voxels_grouped.items()):
                    volume[xys[:,1]-ymin, xys[:,0]-xmin, z-zmin] = label
            elif interpolation_direction == 'y':
                for y, xzs in list(voxels_grouped.items()):
                    volume[y-ymin, xzs[:,0]-xmin, xzs[:,1]-zmin] = label
            elif interpolation_direction == 'x':
                for x, yzs in list(voxels_grouped.items()):
                    volume[yzs[:,0]-ymin, x-xmin, yzs[:,1]-zmin] = label

        return volume, (xmin,xmax,ymin,ymax,zmin,zmax)



def volume_to_images(volume, voxel_size, cut_dimension, pixel_size=None):

    volume_shape = volume.shape

    if pixel_size is None:
        pixel_size = min(voxel_size)

    if cut_dimension == 0:
        volume_shape01 = volume_shape[1], volume_shape[2]
        voxel_size01 = voxel_size[1], voxel_size[2]
    elif cut_dimension == 1:
        volume_shape01 = volume_shape[0], volume_shape[2]
        voxel_size01 = voxel_size[0], voxel_size[2]
    elif cut_dimension == 2:
        volume_shape01 = volume_shape[0], volume_shape[1]
        voxel_size01 = voxel_size[0], voxel_size[1]

    volume_dim01 = volume_shape01[0] * voxel_size01[0], volume_shape01[1] * voxel_size01[1]
    sample_voxels_0 = np.arange(0, volume_dim01[0], pixel_size) / voxel_size01[0]
    sample_voxels_1 = np.arange(0, volume_dim01[1], pixel_size) / voxel_size01[1]

    if cut_dimension == 0:
        images = volume[:, sample_voxels_0[:,None], sample_voxels_1]
    elif cut_dimension == 1:
        images = volume[sample_voxels_0[:,None], :, sample_voxels_1]
    elif cut_dimension == 2:
        images = volume[sample_voxels_0[:,None], sample_voxels_1, :]

    return images

## imported functions

def interpolate_contours_to_volume(contours_grouped_by_pos=None, interpolation_direction=None, contours_xyz=None, return_voxels=False,
                                    return_contours=False, len_interval=20, fill=True, return_origin_instead_of_bbox=False):
    """Interpolate a stack of 2-D contours to create 3-D volume.

    Args:
        return_contours (bool): If true, only return resampled contours \{int: (n,2)-ndarrays\}. If false, return (volume, bbox) tuple.
        return_voxels (bool): If true, only return points inside contours.
        fill (bool): If true, the volume is just the shell. Otherwise, the volume is filled.

    Returns:
        If default, return (volume, bbox).
        volume (3d binary array):
        bbox (tuple): (xmin, xmax, ymin, ymax, zmin, zmax)

        If interpolation_direction == 'z', the points should be (x,y)
        If interpolation_direction == 'x', the points should be (y,z)
        If interpolation_direction == 'y', the points should be (x,z)
    """

    if contours_grouped_by_pos is None:
        assert contours_xyz is not None
        contours_grouped_by_pos = defaultdict(list)
        all_points = np.concatenate(contours_xyz)
        if interpolation_direction == 'z':
            for x,y,z in all_points:
                contours_grouped_by_pos[z].append((x,y))
        elif interpolation_direction == 'y':
            for x,y,z in all_points:
                contours_grouped_by_pos[y].append((x,z))
        elif interpolation_direction == 'x':
            for x,y,z in all_points:
                contours_grouped_by_pos[x].append((y,z))
    else:
        # all_points = np.concatenate(contours_grouped_by_z.values())
        if interpolation_direction == 'z':
            all_points = np.array([(x,y,z) for z, xys in contours_grouped_by_pos.items() for x,y in xys])
        elif interpolation_direction == 'y':
            all_points = np.array([(x,y,z) for y, xzs in contours_grouped_by_pos.items() for x,z in xzs])
        elif interpolation_direction == 'x':
            all_points = np.array([(x,y,z) for x, yzs in contours_grouped_by_pos.items() for y,z in yzs])

    xmin, ymin, zmin = np.floor(all_points.min(axis=0)).astype(np.int)
    xmax, ymax, zmax = np.ceil(all_points.max(axis=0)).astype(np.int)

    interpolated_contours = get_interpolated_contours(contours_grouped_by_pos, len_interval)

    if return_contours:

        # from skimage.draw import polygon_perimeter
        # dense_contour_points = {}
        # for i, contour_pts in interpolated_contours.iteritems():
        #     xs = contour_pts[:,0]
        #     ys = contour_pts[:,1]
        #     dense_contour_points[i] = np.array(polygon_perimeter(ys, xs)).T[:, ::-1]
        # return dense_contour_points

        return {i: contour_pts.astype(np.int) for i, contour_pts in interpolated_contours.items()}

    if fill:

        interpolated_interior_points = {i: points_inside_contour(contour_pts.astype(np.int)) for i, contour_pts in interpolated_contours.items()}
        if return_voxels:
            return interpolated_interior_points

        volume = np.zeros((ymax-ymin+1, xmax-xmin+1, zmax-zmin+1), np.bool)
        for i, pts in interpolated_interior_points.items():
            if interpolation_direction == 'z':
                volume[pts[:,1]-ymin, pts[:,0]-xmin, i-zmin] = 1
            elif interpolation_direction == 'y':
                volume[i-ymin, pts[:,0]-xmin, pts[:,1]-zmin] = 1
            elif interpolation_direction == 'x':
                volume[pts[:,0]-ymin, i-xmin, pts[:,1]-zmin] = 1

    else:
        volume = np.zeros((ymax-ymin+1, xmax-xmin+1, zmax-zmin+1), np.bool)
        for i, pts in interpolated_contours.items():
            pts = pts.astype(np.int)
            if interpolation_direction == 'z':
                volume[pts[:,1]-ymin, pts[:,0]-xmin, i-zmin] = 1
            elif interpolation_direction == 'y':
                volume[i-ymin, pts[:,0]-xmin, pts[:,1]-zmin] = 1
            elif interpolation_direction == 'x':
                volume[pts[:,0]-ymin, i-xmin, pts[:,1]-zmin] = 1

    if return_origin_instead_of_bbox:
        return volume, np.array((xmin,ymin,zmin))
    else:
        return volume, np.array((xmin,xmax,ymin,ymax,zmin,zmax))


def points_inside_contour(cnt, num_samples=None):
    xmin, ymin = cnt.min(axis=0)
    xmax, ymax = cnt.max(axis=0)
    h, w = (ymax-ymin+1, xmax-xmin+1)
    inside_ys, inside_xs = np.where(grid_points_in_poly((h, w), cnt[:, ::-1]-(ymin,xmin)))

    if num_samples is None:
        inside_points = np.c_[inside_xs, inside_ys] + (xmin, ymin)
    else:
        n = inside_ys.size
        random_indices = np.random.choice(list(range(n)), min(1000, n), replace=False)
        inside_points = np.c_[inside_xs[random_indices], inside_ys[random_indices]]

    return inside_points


def get_interpolated_contours(contours_grouped_by_pos, len_interval, level_interval=1):
    """
    Interpolate contours at integer levels.
    Snap minimum z to the minimum integer .
    Snap maximum z to the maximum integer.

    Args:
        contours_grouped_by_pos (dict of (n,2)-ndarrays):
        len_interval (int):

    Returns:
        contours at integer levels (dict of (n,2)-ndarrays):
    """

    contours_grouped_by_adjusted_pos = {}
    for i, (pos, contour) in enumerate(sorted(contours_grouped_by_pos.items())):
        if i == 0:
            contours_grouped_by_adjusted_pos[int(np.ceil(pos))] = contour
        elif i == len(contours_grouped_by_pos)-1:
            contours_grouped_by_adjusted_pos[int(np.floor(pos))] = contour
        else:
            contours_grouped_by_adjusted_pos[int(np.round(pos))] = contour

    zs = sorted(contours_grouped_by_adjusted_pos.keys())
    n = len(zs)

    interpolated_contours = {}

    for i in range(n):
        z0 = zs[i]
        interpolated_contours[z0] = np.array(contours_grouped_by_adjusted_pos[z0])
        if i + 1 < n:
            z1 = zs[i+1]
            interp_cnts = interpolate_contours(contours_grouped_by_adjusted_pos[z0], contours_grouped_by_adjusted_pos[z1], nlevels=z1-z0+1, len_interval_0=len_interval)
            for zi, z in enumerate(range(z0+1, z1)):
                interpolated_contours[z] = interp_cnts[zi+1]

    return interpolated_contours


def interpolate_contours(cnt1, cnt2, nlevels, len_interval_0=20):
    '''
    Interpolate additional contours between (including) two contours cnt1 and cnt2.

    Args:
        cnt1 ((n,2)-ndarray): contour 1
        cnt2 ((n,2)-ndarray): contour 2
        nlevels (int): number of resulting contours, including contour 1 and contour 2.
        len_interval_0 (int): ?

    Returns:
        contours (list of (n,2)-ndarrays):
            resulting contours including the first and last contours.
    '''

    # poly1 = Polygon(cnt1)
    # poly2 = Polygon(cnt2)
    #
    # interpolated_cnts = np.empty((nlevels, len(cnt1), 2))
    # for i, p in enumerate(cnt1):
    #     proj_point = closest_to(Point(p), poly2)
    #     interpolated_cnts[:, i] = (np.column_stack([np.linspace(p[0], proj_point[0], nlevels),
    #                      np.linspace(p[1], proj_point[1], nlevels)]))
    #
    # print cnt1
    # print cnt2

    l1 = Polygon(cnt1).length
    l2 = Polygon(cnt2).length
    n1 = len(cnt1)
    n2 = len(cnt2)
    len_interval_1 = l1 / n1
    len_interval_2 = l2 / n2
    len_interval_interpolated = np.linspace(len_interval_1, len_interval_2, nlevels)

    # len_interval_0 = 20
    n_points = max(int(np.round(max(l1, l2) / len_interval_0)), n1, n2)

    s1 = resample_polygon(cnt1, n_points=n_points)
    s2 = resample_polygon(cnt2, n_points=n_points)

    # Make sure point sets are both clockwise or both anti-clockwise.

    # c1 = np.mean(s1, axis=0)
    # c2 = np.mean(s2, axis=0)
    # d1 = (s1 - c1)[0]
    # d1 = d1 / np.linalg.norm(d1)
    # d2s = s2 - c2
    # d2s = d2s / np.sqrt(np.sum(d2s**2, axis=1))[:,None]
    # s2_start_index = np.argmax(np.dot(d1, d2s.T))
    # print s2_start_index
    # s2 = np.r_[np.atleast_2d(s2[s2_start_index:]), np.atleast_2d(s2[:s2_start_index])]

    # s2i = np.r_[[s2[0]], s2[1:][::-1]]

    s2i = s2[::-1]

    # curv1, xp1, yp1 = signed_curvatures(s1)
    # curv2, xp2, yp2 = signed_curvatures(s2)
    # curv2i, xp2i, yp2i = signed_curvatures(s2i)

    d = 7
    xp1 = np.gradient(s1[:, 0], d)
    yp1 = np.gradient(s1[:, 1], d)
    xp2 = np.gradient(s2[:, 0], d)
    yp2 = np.gradient(s2[:, 1], d)
    xp2i = np.gradient(s2i[:, 0], d)
    yp2i = np.gradient(s2i[:, 1], d)

    # using correlation over curvature values directly is much better than using correlation over signs
    # sign1 = np.sign(curv1)
    # sign2 = np.sign(curv2)
    # sign2i = np.sign(curv2i)

    # conv_curv_1_2 = np.correlate(np.r_[curv2, curv2], curv1, mode='valid')
    conv_xp_1_2 = np.correlate(np.r_[xp2, xp2], xp1, mode='valid')
    conv_yp_1_2 = np.correlate(np.r_[yp2, yp2], yp1, mode='valid')

    # conv_1_2 = np.correlate(np.r_[sign2, sign2], sign1, mode='valid')

    # top, second = conv_1_2.argsort()[::-1][:2]
    # d2_top = (s2 - c2)[top]
    # d2_top = d2_top / np.linalg.norm(d2_top)
    # d2_second = (s2 - c2)[second]
    # d2_second = d2_second / np.linalg.norm(d2_second)
    # s2_start_index = [top, second][np.argmax(np.dot([d2_top, d2_second], d1))]

    # conv_curv_1_2i = np.correlate(np.r_[curv2i, curv2i], curv1, mode='valid')
    conv_xp_1_2i = np.correlate(np.r_[xp2i, xp2i], xp1, mode='valid')
    conv_yp_1_2i = np.correlate(np.r_[yp2i, yp2i], yp1, mode='valid')

    # conv_1_2i = np.correlate(np.r_[sign2i, sign2i], sign1, mode='valid')
    # top, second = conv_1_2i.argsort()[::-1][:2]
    # if xp1[top] * xp2i[top] + yp1[top] * yp2i[top] > xp1[top] * xp2i[top] + yp1[top] * yp2i[top] :
    #     s2i_start_index = top
    # else:
    #     s2i_start_index = second

    # d2_top = (s2i - c2)[top]
    # d2_top = d2_top / np.linalg.norm(d2_top)
    # d2_second = (s2i - c2)[second]
    # d2_second = d2_second / np.linalg.norm(d2_second)
    # s2i_start_index = [top, second][np.argmax(np.dot([d2_top, d2_second], d1))]

    # if conv_1_2[s2_start_index] > conv_1_2i[s2i_start_index]:
    #     s3 = np.r_[np.atleast_2d(s2[s2_start_index:]), np.atleast_2d(s2[:s2_start_index])]
    # else:
    #     s3 = np.r_[np.atleast_2d(s2i[s2i_start_index:]), np.atleast_2d(s2i[:s2i_start_index])]

    # from scipy.spatial import KDTree
    # tree = KDTree(s1)
    # nn_in_order_s2 = np.count_nonzero(np.diff(tree.query(s2)[1]) > 0)
    # nn_in_order_s2i = np.count_nonzero(np.diff(tree.query(s2i)[1]) > 0)

    # overall_s2 = conv_curv_1_2 / conv_curv_1_2.max() + conv_xp_1_2 / conv_xp_1_2.max() + conv_yp_1_2 / conv_yp_1_2.max()
    # overall_s2i = conv_curv_1_2i / conv_curv_1_2i.max() + conv_xp_1_2i / conv_xp_1_2i.max() + conv_yp_1_2i / conv_yp_1_2i.max()

    # overall_s2 =  conv_xp_1_2 / conv_xp_1_2.max() + conv_yp_1_2 / conv_yp_1_2.max()
    # overall_s2i =  conv_xp_1_2i / conv_xp_1_2i.max() + conv_yp_1_2i / conv_yp_1_2i.max()

    overall_s2 =  conv_xp_1_2 + conv_yp_1_2
    overall_s2i =  conv_xp_1_2i + conv_yp_1_2i

    if overall_s2.max() > overall_s2i.max():
        s2_start_index = np.argmax(overall_s2)
        s3 = np.roll(s2, -s2_start_index, axis=0)
    else:
        s2i_start_index = np.argmax(overall_s2i)
        s3 = np.roll(s2i, -s2i_start_index, axis=0)

    # plt.plot(overall)
    # plt.show();

    interpolated_contours = [(1-r) * s1 + r * s3 for r in np.linspace(0, 1, nlevels)]
    resampled_interpolated_contours = [resample_polygon(cnt, len_interval=len_interval_interpolated[i]) for i, cnt in enumerate(interpolated_contours)]

    return resampled_interpolated_contours


def resample_polygon(cnt, n_points=None, len_interval=20):

    polygon = Polygon(cnt)

    if n_points is None:
        contour_length = polygon.exterior.length
        n_points = max(3, int(np.round(contour_length / len_interval)))

    resampled_cnt = np.empty((n_points, 2))
    for i, p in enumerate(np.linspace(0, 1, n_points+1)[:-1]):
        pt = polygon.exterior.interpolate(p, normalized=True)
        resampled_cnt[i] = (pt.x, pt.y)
    return resampled_cnt
