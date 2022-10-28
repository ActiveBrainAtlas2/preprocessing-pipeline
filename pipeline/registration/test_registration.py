import os
import sys
import numpy as np
from skimage import io
from scipy.ndimage import zoom

from rigid_transform_3D import rigid_transform_3D

# Test with random data

# Random rotation and translation
R = np.random.rand(3, 3)
t = np.random.rand(3,1)

# make R a proper rotation matrix, force orthonormal
U, S, Vt = np.linalg.svd(R)
R = U@Vt

# remove reflection
if np.linalg.det(R) < 0:
   Vt[2,:] *= -1
   R = U@Vt

# number of points
n = 5


animal = 'DK55'
ROOT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
#boundary_path = os.path.join(ROOT, animal, 'preps/CH1/brainreg_allen', 'boundaries.tiff')
#downsampled_path = os.path.join(ROOT, animal, 'preps/CH1/brainreg_allen', 'downsampled.tiff')
#A = io.imread(boundary_path)
#B = io.imread(downsampled_path)
#A = np.random.rand(3, n, 1)
#A = np.zeros(3,n)
A = np.array(
    [[1,2,3,4,5],
    [1,2,3,4,5],
    [1,2,3,4,5]]
    ).astype(np.uint8)
B = np.array(
   [[2,3,4,5,6],
    [2,3,4,5,78],
    [2,3,4,5,6]]
    ).astype(np.uint8)
print("info on Points A")
print(A.dtype, A.shape, A.ndim)
An = zoom(A, (1.5, 1.5))
print(An.dtype, An.shape, An.ndim)
print(An)
sys.exit()
#B = R@A + t

# Recover R and t
ret_R, ret_t = rigid_transform_3D(A, B)

# Compare the recovered R and t with the original
B2 = (ret_R@A) + ret_t

# Find the root mean squared error
err = B2 - B
err = err * err
err = np.sum(err)
rmse = np.sqrt(err/n)


print("Ground truth rotation")
print(R)

print("Recovered rotation")
print(ret_R)
print("")

print("Ground truth translation")
print(t)

print("Recovered translation")
print(ret_t)
print("")

print("RMSE:", rmse)

if rmse < 1e-5:
    print("Everything looks good!")
else:
    print("Hmm something doesn't look right ...")