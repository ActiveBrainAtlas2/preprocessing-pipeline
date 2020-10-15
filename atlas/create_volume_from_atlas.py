import argparse
import os
import sys
import numpy as np
from timeit import default_timer as timer
import collections
from pymicro.view.vol_utils import compute_affine_transform
import cv2
from pprint import pprint

start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties

def Affine_Fit( from_pts, to_pts ):
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
    if len(q) != len(p) or len(q)<1:
        print("from_pts and to_pts must be of same size.")
        return False

    dim = len(q[0]) # num of dimensions
    if len(q) < dim:
        print("Too few points => under-determined system.")
        return False

    # Make an empty (dim) x (dim+1) matrix and fill it
    c = [[0.0 for a in range(dim)] for i in range(dim+1)]
    for j in range(dim):
        for k in range(dim+1):
            for i in range(len(q)):
                qt = list(q[i]) + [1]
                c[k][j] += qt[k] * p[i][j]

    # Make an empty (dim+1) x (dim+1) matrix and fill it
    Q = [[0.0 for a in range(dim)] + [0] for i in range(dim+1)]
    for qi in q:
        qt = list(qi) + [1]
        for i in range(dim+1):
            for j in range(dim+1):
                Q[i][j] += qt[i] * qt[j]

    # Ultra simple linear system solver. Replace this if you need speed.
    def gauss_jordan(m, eps = 1.0/(10**10)):
      """Puts given matrix (2D array) into the Reduced Row Echelon Form.
         Returns True if successful, False if 'm' is singular.
         NOTE: make sure all the matrix items support fractions! Int matrix will NOT work!
         Written by Jarno Elonen in April 2005, released into Public Domain"""
      (h, w) = (len(m), len(m[0]))
      for y in range(0,h):
        maxrow = y
        for y2 in range(y+1, h):    # Find max pivot
          if abs(m[y2][y]) > abs(m[maxrow][y]):
            maxrow = y2
        (m[y], m[maxrow]) = (m[maxrow], m[y])
        if abs(m[y][y]) <= eps:     # Singular?
          return False
        for y2 in range(y+1, h):    # Eliminate column y
          c = m[y2][y] / m[y][y]
          for x in range(y, w):
            m[y2][x] -= m[y][x] * c
      for y in range(h-1, 0-1, -1): # Backsubstitute
        c  = m[y][y]
        for y2 in range(0,y):
          for x in range(w-1, y-1, -1):
            m[y2][x] -=  m[y][x] * m[y2][y] / c
        m[y][y] /= c
        for x in range(h, w):       # Normalize row y
          m[y][x] /= c
      return True

    # Augement Q with c and solve Q * a' = c by Gauss-Jordan
    M = [ Q[i] + c[i] for i in range(dim+1)]
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
                str = "x%df = " % j
                for i in range(dim):
                    str +="x%d * %f + " % (i, M[i][j+dim+1])
                str += "%f" % M[dim][j+dim+1]
                res += str + "\n"
            return res

        def Transform(self, pt):
            res = [0.0 for a in range(dim)]
            for j in range(dim):
                for i in range(dim):
                    res[j] += pt[i] * M[i][j+dim+1]
                res[j] += M[dim][j+dim+1]
            return res
    return Transformation()

def solve_affineXXX(rbar, rfit):
    x = np.transpose(np.matrix(rbar))
    y = np.transpose(np.matrix(rfit))
    # add ones on the bottom of x and y
    x = np.vstack((x,[1,1,1]))
    y = np.vstack((y,[1,1,1]))
    # solve for A2
    A2 = y * x.I
    # return function that takes input x and transforms it
    # don't need to return the 4th row as it is
    return lambda x: (A2*np.vstack((np.matrix(x).reshape(3,1),1)))[0:3,:]


def solve_affine(rbar, rfit):
    x = np.transpose(np.matrix(rbar))
    y = np.transpose(np.matrix(rfit))
    # add ones on the bottom of x and y
    rows = rbar.shape[0]
    bottom = [1 for x in range(rows)]
    x = np.vstack((x,bottom))
    y = np.vstack((y,bottom))
    # solve for A2
    A2 = y * x.I
    # return function that takes input x and transforms it
    # don't need to return the 4th row as it is
    return lambda x: (A2*np.vstack((np.matrix(x).reshape(3,1),1)))[0:rows,:]


def create_atlas(animal):

    fileLocationManager = FileLocationManager(animal)
    atlas_name = 'atlasV7'
    DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
    ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
    THUMBNAIL_DIR = os.path.join(ROOT_DIR, animal, 'preps', 'CH1', 'thumbnail')
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
    ORIGIN_PATH = os.path.join(ATLAS_PATH, 'origin')
    VOLUME_PATH = os.path.join(ATLAS_PATH, 'structure')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'atlas')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    SCALE = 32
    origin_files = sorted(os.listdir(ORIGIN_PATH))
    volume_files = sorted(os.listdir(VOLUME_PATH))

    structure_volume_origin = {}
    for volume_filename, origin_filename in zip(volume_files, origin_files):
        structure = os.path.splitext(volume_filename)[0]
        if structure not in origin_filename:
            print(structure, origin_filename)
            break

        color = get_structure_number(structure.replace('_L', '').replace('_R', ''))

        origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
        volume = np.load(os.path.join(VOLUME_PATH, volume_filename))

        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)
        volume[volume > 0.8] = color
        volume = volume.astype(np.uint8)

        structure_volume_origin[structure] = (volume, origin)
    #print(structure_volume_origin.keys())


    #x_length = 1000
    #y_length = 1000
    #z_length = 300
    sqlController = SqlController(animal)
    resolution = sqlController.scan_run.resolution
    aligned_shape = np.array((sqlController.scan_run.width, sqlController.scan_run.height))
    z_length = len(os.listdir(THUMBNAIL_DIR))

    downsampled_aligned_shape = np.round(aligned_shape / SCALE).astype(int)

    x_length = downsampled_aligned_shape[1] + 0
    y_length = downsampled_aligned_shape[0] + 0

    atlasV7_volume = np.zeros((x_length, y_length, z_length), dtype=np.uint32)

    min_structures = {'SC': [21868, 5119, 220],
                      'DC_L': [24103, 11618, 134],
                      'DC_R': [19870, 11287, 330],
                      'LC_L': [24746, 11178, 180],
                      'LC_R': [24013, 11621, 268],
                      '5N_L': [23105, 12133, 160],
                      '5N_R': [20205, 13373, 298],
                      '7n_L': [20611, 17991, 177],
                      '7n_R': [24218, 13615, 284]}

    mean_structures = {'SC': [24226, 6401, 220],
                       'DC_L': [24482, 11985, 134],
                       'DC_R': [20424, 11736, 330],
                       'LC_L': [25290, 11750, 180],
                       'LC_R': [24894, 12079, 268],
                       '5N_L': [23790, 13025, 160],
                       '5N_R': [20805, 14163, 298],
                       '7n_L': [20988, 18405, 177],
                       '7n_R': [24554, 13911, 284]}

    animal_origin = {}
    for structure, origin in mean_structures.items():
        animal_origin[structure] = [mean_structures[structure][1]/SCALE,
                                        mean_structures[structure][0]/SCALE,
                                        mean_structures[structure][2]]

    atlas_origin = {}
    atlas_all_origins = {}


    # 1st loop to fill dictionarys with data
    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        x, y, z = origin
        x_start = x + x_length / 2
        y_start = y + y_length / 2
        z_start = z / 2 + z_length / 2
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) / 2
        midx = (x_end + x_start) / 2
        midy = (y_end + y_start) / 2
        midz = (z_end + z_start) / 2
        #print(structure,'centroid', midx,midy,midz)

        if structure in animal_origin.keys():
            atlas_origin[structure] = [round(midx,2), round(midy,2), int(round(midz))]

        atlas_all_origins[structure] = [midx, midy, midz]
    pprint(atlas_origin)
    atlas_origin_array = np.array(list(atlas_origin.values()), dtype=np.float32)
    animal_origin_array = np.array(list(animal_origin.values()), dtype=np.float32)

    #animal_origin = {'SC': [200.03125, 757.0625, 220], 'DC_L': [374.53125, 765.0625, 134], 'DC_R': [366.75, 638.25, 330]}
    #atlas_origin =  {'SC': [377.0, 454.0, 226], 'DC_L': [580.0, 651.0, 131], 'DC_R': [580.0, 651.0, 318]}
    Y = np.array(list(atlas_origin.values()), dtype=np.float32)
    X = np.array(list(animal_origin.values()), dtype=np.float32)
    transformFn = solve_affine(X, Y)


    animal_centroid = np.mean(X, axis=0)
    atlas_centroid = np.mean(Y, axis=0)
    print('volume centriods', animal_centroid, atlas_centroid)
    print('X', X.shape)
    print(X)
    print('Y', Y.shape)
    print(Y)


    trn = Affine_Fit(X, Y)
    print("Transformation is:")
    print(trn.To_Str())

    # basic least squares
    n = X.shape[0]
    pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
    unpad = lambda x: x[:, :-1]
    Xp = pad(X)
    Yp = pad(Y)
    # Solve the least squares problem X * A = Y
    # to find our transformation matrix A
    A, residuals, rank, s = np.linalg.lstsq(Xp, Yp, rcond=None)
    transform = lambda x: unpad(np.dot(pad(x), A))
    A[np.abs(A) < 1e-10] = 0
    print(A)



    translation, transformation = compute_affine_transform(X, Y)
    #invt = np.linalg.inv(transformation)
    #offset = -np.dot(invt, translation)
    print(transformation)


    # 2nd loop
    atlas_minmax = []
    trans_minmax = []
    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        x, y, z = origin
        x_start = int(x) + x_length // 2
        y_start = int(y) + y_length // 2
        z_start = int(z) // 2 + z_length // 2
        print(str(structure).ljust(8), 'original starts: x', x_start, 'y', y_start, 'z', z_start, end="\t")
        #x_start, y_start, z_start = atlas_all_origins[structure]
        #print('mids', xmid, ymid, zmid, end="\n")
        #original_array = np.array([x,y,z])
        # do transformation
        #x_start = int(xf2) + x_length // 2
        #y_start = int(yf2) + y_length // 2
        #z_start = int(zf2) // 2 + z_length // 2

        original_array = np.array([x_start, y_start, z_start])
        #xf2, yf2, zf2 = animal_centroid + np.dot(transformation, original_array  - atlas_centroid)
        #original_array = np.vstack((original_array, [1,1,1]))
        #results  = transform(original_array)[0:1]
        #xf2 = results[0,0]
        #yf2 = results[0,1]
        #zf2 = results[0,2]

        #xf2,yf2,zf2, _ = transformFn(original_array)
        xf2, yf2, zf2 = trn.Transform(original_array)

        #transformed_array = np.array([xf2, yf2, zf2])


        x_start = int(round(xf2))
        y_start = int(round(yf2))
        z_start = int(round(zf2))
        #x_start = int(round(xf2[0,0]))
        #y_start = int(round(yf2[0,0]))
        #z_start = int(round(zf2[0,0]))
        atlas_minmax.append(x_start)
        trans_minmax.append(xf2)
        print('2. trans x', x_start, 'y', y_start, 'z', z_start, end="\n")
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) // 2

        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        try:
            atlasV7_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume
        except:
            print('could not add', structure, x_start,y_start, z_start)

    print('min,max x for atlas', np.min(atlas_minmax),np.max(atlas_minmax))
    print('min,max x for trans', np.min(trans_minmax),np.max(trans_minmax))
    #origin_centroid + np.dot(transformation, atlasV7_volume - fitted_centroid)
    planar_resolution = sqlController.scan_run.resolution
    #resolution = int(planar_resolution * 1000 * SCALE)
    #resolution = 0.46 * 1000 * SCALE
    resolution = 10000
    print(resolution)
    if True:
        #def __init__(self, volume, scales, offset=[0, 0, 0], layer_type='segmentation'):

        ng = NumpyToNeuroglancer(atlasV7_volume, [resolution, resolution, 20000], offset=[770,20,0])
        ng.init_precomputed(OUTPUT_DIR)
        ng.add_segment_properties(get_segment_properties())
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()


    end = timer()
    print(f'Finito! Program took {end - start} seconds')

    #outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.npy')
    #with open(outpath, 'wb') as file:
    #    np.save(file, atlasV7_volume)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_atlas(animal)

