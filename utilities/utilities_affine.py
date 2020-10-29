import os, sys
import numpy as np
from pathlib import Path

from scipy import ndimage

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager

def rigid_transform_3D(A, B):
    assert A.shape == B.shape

    num_rows, num_cols = A.shape
    if num_rows != 3:
        raise Exception(f"matrix A is not 3xN, it is {num_rows}x{num_cols}")

    num_rows, num_cols = B.shape
    if num_rows != 3:
        raise Exception(f"matrix B is not 3xN, it is {num_rows}x{num_cols}")

    # find mean column wise
    centroid_A = np.mean(A, axis=1)
    centroid_B = np.mean(B, axis=1)

    # ensure centroids are 3x1
    centroid_A = centroid_A.reshape(-1, 1)
    centroid_B = centroid_B.reshape(-1, 1)

    # subtract mean
    Am = A - centroid_A
    Bm = B - centroid_B

    H = Am @ np.transpose(Bm)

    # sanity check
    # if linalg.matrix_rank(H) < 3:
    #    raise ValueError("rank of H = {}, expecting 3".format(linalg.matrix_rank(H)))

    # find rotation
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    # special reflection case
    if np.linalg.det(R) < 0:
        print("det(R) < R, reflection detected!, correcting for it ...")
        Vt[2, :] *= -1
        R = Vt.T @ U.T

    t = -R @ centroid_A + centroid_B

    return R, t

def umeyama(P, Q):
    assert P.shape == Q.shape
    n, dim = P.shape
    centeredP = P - P.mean(axis=0)
    centeredQ = Q - Q.mean(axis=0)
    C = np.dot(np.transpose(centeredP), centeredQ) / n
    V, S, W = np.linalg.svd(C)
    d = (np.linalg.det(V) * np.linalg.det(W)) < 0.0

    if d:
        S[-1] = -S[-1]
        V[:, -1] = -V[:, -1]

    R = np.dot(V, W)
    varP = np.var(P, axis=0).sum()
    c = 1/varP * np.sum(S) # scale factor
    t = Q.mean(axis=0) - P.mean(axis=0).dot(c*R)

    return c, R, t


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


def estimate_structure_centers(atlas_data, animal):
    sql_controller = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    thumbnail_dir = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_aligned')

    # Compute box center
    print(f'resolution: {sql_controller.scan_run.resolution}')
    print(f'width: {sql_controller.scan_run.width}')
    print(f'height: {sql_controller.scan_run.height}')
    box_w = sql_controller.scan_run.width * sql_controller.scan_run.resolution / 10  # 10 mum scale
    box_h = sql_controller.scan_run.height * sql_controller.scan_run.resolution / 10  # 10 mum scale
    box_z = len(os.listdir(thumbnail_dir))  # 20 mum scale
    box_center = np.array([box_w, box_h, box_z]) / 2
    print(f'box center: {box_center}')

    # From the neuroglancer righ panel, I would expect the following:
    # box_center = np.array([1000, 1000, 300]) / 2

    # Estimate structure volume center of mass
    atlas_com = {}
    for name, (origin, volume) in atlas_data.items():
        sx, sy, sz = volume.shape
        grid_com = np.array([sx, sy, (sz + 0) / 2]) / 1  # Why (sz + 1) instead of sz? And why / 2?
        # I'm considering an alternative way to compute com like the following:
        #grid_com = np.array(ndimage.measurements.center_of_mass(volume))
        #grid_com[2] /= 2
        atlas_com[name] = (box_center + origin + grid_com, volume)
    return atlas_com


def load_atlas_data():
    atlas_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV7')
    origin_dir = atlas_dir / 'origin'
    volume_dir = atlas_dir / 'structure'

    atlas_data = {}

    for origin_file, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        assert origin_file.stem == volume_file.stem
        name = origin_file.stem

        origin = np.loadtxt(origin_file)

        volume = np.load(volume_file)
        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)

        atlas_data[name] = (origin, volume)

    return atlas_data
