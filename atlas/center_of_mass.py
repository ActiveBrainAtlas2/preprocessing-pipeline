"""
This file will create a rotation matrix and a translation vector you can use to add to neuroglancer
to align the atlas to your stack of images
"""
import sys
import numpy as np
from scipy import ndimage
from pathlib import Path

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())



def get_atlas_centers(atlas_box_size=(1000, 1000, 300), atlas_box_scales=(10, 10, 20),
                      atlas_raw_scale=10):
    """

    :param atlas_box_size: a virtual rectangle used to create a layer in neuroglancer
    :param atlas_box_scales: scales in micrometers for x,y,z coordinates in neuroglancer
    :param atlas_raw_scale: scale used to define the units of the atlas numpy arrays
    :return: a dictionary of centers for each structure
    """
    atlas_box_scales = np.array(atlas_box_scales)
    atlas_box_size = np.array(atlas_box_size)
    atlas_box_center = atlas_box_size / 2

    # unzip your structure and origin zip files in this path, or create your own path
    atlas_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV7')
    origin_dir = atlas_dir / 'origin'
    volume_dir = atlas_dir / 'structure'

    atlas_centers = {}

    for origin_file, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        assert origin_file.stem == volume_file.stem
        name = origin_file.stem
        origin = np.loadtxt(origin_file)
        volume = np.load(volume_file)
        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)

        # computer volume center of mass in raw array coordinates
        center = (origin + ndimage.measurements.center_of_mass(volume))

        # transform into the atlas box coordinates that neuroglancer assumes
        center = atlas_box_center + center * atlas_raw_scale / atlas_box_scales

        atlas_centers[name] = center

    return atlas_centers


# Adapted from https://github.com/libigl/eigen/blob/master/Eigen/src/Geometry/Umeyama.h
def align_point_sets(src, dst, with_scaling=True):
    assert src.shape == dst.shape
    assert len(src.shape) == 2
    m, n = src.shape  # dimension, number of points

    src_mean = np.mean(src, axis=1).reshape(-1, 1)
    dst_mean = np.mean(dst, axis=1).reshape(-1, 1)

    src_demean = src - src_mean
    dst_demean = dst - dst_mean

    u, s, vh = np.linalg.svd(dst_demean @ src_demean.T / n)

    # deal with reflection
    e = np.ones(m)
    if np.linalg.det(u) * np.linalg.det(vh) < 0:
        print('reflection detected')
        e[-1] = -1

    r = u @ np.diag(e) @ vh

    if with_scaling:
        src_var = (src_demean ** 2).sum(axis=0).mean()
        c = sum(s * e) / src_var
        r *= c

    t = dst_mean - r @ src_mean

    return r, t



def align_atlas(reference_centers,
        reference_scales=(0.325, 0.325, 20),
        atlas_box_size=(1000, 1000, 300),
        atlas_box_scales=(10, 10, 20),
        atlas_raw_scale=10):
    """
    Finally, we could put all the functions together to assemble a simple function to use.
    Just feed it with the reference structure centers,
    and it would print out the transformation matrix to be typed into neuroglancer to align the structures.
    :param reference_centers: centers you got from neuroglancer of the structures
    :param reference_scales: resolution of x and y and section thickness
    :param atlas_box_size: generic size of the atlas you are creating
    :param atlas_box_scales: scale in micrometers of x,y,z
    :param atlas_raw_scale: scale in micrometers of atlas
    :return: rotation matrix: r, and translation vector: t
    """

    atlas_centers = get_atlas_centers(atlas_box_size, atlas_box_scales, atlas_raw_scale)

    structures = sorted(reference_centers.keys())

    src_point_set = np.array([atlas_centers[s] for s in structures]).T
    src_point_set = np.diag(atlas_box_scales) @ src_point_set

    dst_point_set = np.array([reference_centers[s] for s in structures]).T
    dst_point_set = np.diag(reference_scales) @ dst_point_set

    r, t = align_point_sets(src_point_set, dst_point_set)

    print('Please type the following numbers into neuroglancer to align the atlas structures.')
    print()
    print('Rotation:')
    print(r)
    print()
    print('Translation:')
    print(t / np.array([reference_scales]).T)

    return r, t



if __name__ == '__main__':
    # Replace this data with your real data you got from the centers of mass of
    # at least 3 structures from neuroglancer. The data below is our data and will most
    # likely work with your stack!
    reference_centers = {
        '12N': [46488, 18778, 242],
        '5N_L': [38990, 20019, 172],
        '5N_R': [39184, 19027, 315],
        '7N_L': [42425, 23190, 166],
        '7N_R': [42286, 22901, 291]
    }
    r, t = align_atlas(reference_centers)
