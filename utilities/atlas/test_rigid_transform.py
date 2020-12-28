import numpy as np
from create_volume_from_atlas import rigid_transform_3D
from collections import OrderedDict
# Test with random data

# Random rotation and translation
#R = np.random.rand(3,3)
#t = np.random.rand(3,1)

R = np.array([[ 0.10232369, -0.90355305, -0.41607901],
 [ 0.98482251,  0.03306588,  0.17038567],
 [-0.14019447, -0.42719846,  0.89322281]])

t = np.array([[1709.39118827],
 [ 319.24478843],
 [ 549.87179821]])


# make R a proper rotation matrix, force orthonormal
U, S, Vt = np.linalg.svd(R)
R = U@Vt

# remove reflection
if np.linalg.det(R) < 0:
   Vt[2,:] *= -1
   R = U@Vt

# number of points
n = 9
A = np.random.rand(3, n)
print('shape of A', A.shape)
##### actual data for both sets of points
resolution = 0.452
# the atlas uses a 10um scale
SCALE = (10 / resolution)

MD589_centers = {'5N_L': [23790, 13025, 160],
                 '5N_R': [20805, 14163, 298],
                 '7n_L': [20988, 18405, 177],
                 '7n_R': [24554, 13911, 284],
                 'DC_L': [24482, 11985, 134],
                 'DC_R': [20424, 11736, 330],
                 'LC_L': [25290, 11750, 180],
                 'LC_R': [24894, 12079, 268],
                 'SC': [24226, 6401, 220]}
MD589_centers = OrderedDict(MD589_centers)
MD589_list = []
for value in MD589_centers.values():
    MD589_list.append((value[1] / SCALE, value[0] / SCALE, value[2]))
A = np.array(MD589_list).T

print('A')
print(A)
B = R@A + t
print('R@A + t')
print(B)

# Recover R and t
ret_R, ret_t = rigid_transform_3D(A, B)

# Compare the recovered R and t with the original
B2 = (ret_R@A) + ret_t

# Find the root mean squared error
err = B2 - B
err = err * err
err = np.sum(err)
rmse = np.sqrt(err/n)

print("Points A")
print(A)
print("")

print("Points B")
print(B)
print("")

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

A = np.array([600,400,200])
print('A')
at = np.reshape(A, (3,1))
print('at shape',at.shape)
print(at)
B = R@at + t
print('R@A + t')
print(B)
