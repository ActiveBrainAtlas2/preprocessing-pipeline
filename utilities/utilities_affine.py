import numpy as np
from superpose3d import Superpose3D


def affine_fit(from_pts, to_pts):
    """Fit an affine transformation to given point sets.
      More precisely: solve (least squares fit) matrix 'A'and 't' from
      'p ~= A*q+t', given vectors 'p' and 'q'.
      Works with arbitrary dimensional vectors (2d, 3d, 4d...).

      Written by Jarno Elonen <elonen@iki.fi> in 2007.
      Placed in Public Domain.

      Based on paper "Fitting affine and orthogonal transformations
      between two sets of points, by Helmuth Späth (2003)."""

    q = from_pts
    p = to_pts
    if len(q) != len(p) or len(q) < 1:
        print("from_pts and to_pts must be of same size.")
        return False

    dim = len(q[0])  # num of dimensions
    if len(q) < dim:
        print("Too few points => under-determined system.")
        return False

    # Make an empty (dim) x (dim+1) matrix and fill it
    c = [[0.0 for a in range(dim)] for i in range(dim + 1)]
    for j in range(dim):
        for k in range(dim + 1):
            for i in range(len(q)):
                qt = list(q[i]) + [1]
                c[k][j] += qt[k] * p[i][j]

    # Make an empty (dim+1) x (dim+1) matrix and fill it
    Q = [[0.0 for a in range(dim)] + [0] for i in range(dim + 1)]
    for qi in q:
        qt = list(qi) + [1]
        for i in range(dim + 1):
            for j in range(dim + 1):
                Q[i][j] += qt[i] * qt[j]

    # Ultra simple linear system solver. Replace this if you need speed.
    def gauss_jordan(m, eps=1.0 / (10 ** 10)):
        """Puts given matrix (2D array) into the Reduced Row Echelon Form.
           Returns True if successful, False if 'm' is singular.
           NOTE: make sure all the matrix items support fractions! Int matrix will NOT work!
           Written by Jarno Elonen in April 2005, released into Public Domain"""
        (h, w) = (len(m), len(m[0]))
        for y in range(0, h):
            maxrow = y
            for y2 in range(y + 1, h):  # Find max pivot
                if abs(m[y2][y]) > abs(m[maxrow][y]):
                    maxrow = y2
            (m[y], m[maxrow]) = (m[maxrow], m[y])
            if abs(m[y][y]) <= eps:  # Singular?
                return False
            for y2 in range(y + 1, h):  # Eliminate column y
                c = m[y2][y] / m[y][y]
                for x in range(y, w):
                    m[y2][x] -= m[y][x] * c
        for y in range(h - 1, 0 - 1, -1):  # Backsubstitute
            c = m[y][y]
            for y2 in range(0, y):
                for x in range(w - 1, y - 1, -1):
                    m[y2][x] -= m[y][x] * m[y2][y] / c
            m[y][y] /= c
            for x in range(h, w):  # Normalize row y
                m[y][x] /= c
        return True

    # Augement Q with c and solve Q * a' = c by Gauss-Jordan
    M = [Q[i] + c[i] for i in range(dim + 1)]
    if not gauss_jordan(M):
        print("Error: singular matrix. Points are probably coplanar.")
        return False

    # Make a result object
    class Transformation:
        """Result object that represents the transformation
           from affine fitter."""

        def To_Str(self):
            res = ""
            for j in range(dim):
                str = "x%d' = " % j
                for i in range(dim):
                    str += "x%d * %f + " % (i, M[i][j + dim + 1])
                str += "%f" % M[dim][j + dim + 1]
                res += str + "\n"
            return res

        def Transform(self, pt):
            res = [0.0 for a in range(dim)]
            for j in range(dim):
                for i in range(dim):
                    res[j] += pt[i] * M[i][j + dim + 1]
                res[j] += M[dim][j + dim + 1]
            return res

    return Transformation()


def ralign(from_points, to_points):
    assert len(from_points.shape) == 2, \
        "from_points must be a m x n array"
    assert from_points.shape == to_points.shape, \
        "from_points and to_points must have the same shape"

    N, m = from_points.shape

    mean_from = from_points.mean(axis=0)
    mean_to = to_points.mean(axis=0)

    delta_from = from_points - mean_from  # N x m
    delta_to = to_points - mean_to  # N x m

    sigma_from = (delta_from * delta_from).sum(axis=1).mean()
    sigma_to = (delta_to * delta_to).sum(axis=1).mean()

    cov_matrix = delta_to.T.dot(delta_from) / N

    U, d, V_t = np.linalg.svd(cov_matrix, full_matrices=True)
    cov_rank = np.linalg.matrix_rank(cov_matrix)
    S = np.eye(m)

    if cov_rank >= m - 1 and np.linalg.det(cov_matrix) < 0:
        S[m - 1, m - 1] = -1
    elif cov_rank < m - 1:
        raise ValueError("colinearility detected in covariance matrix:\n{}".format(cov_matrix))

    R = U.dot(S).dot(V_t)
    c = (d * S.diagonal()).sum() / sigma_from
    t = mean_to - c * R.dot(mean_from)

    return c*R, t


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

def superalign(A, B):
    RMSD, R, t, c = Superpose3D(A, B)
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
