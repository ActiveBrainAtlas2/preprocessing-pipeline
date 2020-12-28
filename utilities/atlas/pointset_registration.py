from math import pi, cos, sin
import numpy as np
import random
from _collections import OrderedDict
from matplotlib import pyplot as plt, colors as mcol
from pymicro.view.vol_utils import compute_affine_transform
from pprint import pprint
import pandas as pd
import plotly.express as px
colors = 'brgmkbrgmkbrgmkbrgmk'
my_gray = (0.8, 0.8, 0.8)
random.seed(13)
resolution = 0.452
# the atlas uses a 10um scale
SCALE = (10 / resolution)
w = 43700 // SCALE
h = 32400 // SCALE
z_length = 447

##### actual data for both sets of points
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
MD589 = np.array(MD589_list)

atlas_centers = {'5N_L': [686.53, 990.08, 155.38],
                 '5N_R': [686.53, 990.08, 292.62],
                 '7n_L': [725.04, 1034.44, 172.21],
                 '7n_R': [725.04, 1034.44, 275.79],
                 'DC_L': [806.29, 955.16, 130.35],
                 'DC_R': [806.29, 955.16, 317.65],
                 'LC_L': [731.55, 934.49, 182.33],
                 'LC_R': [731.55, 934.49, 265.67],
                 'SC': [602.87, 757.7, 225.5],
                 }

atlas_centers = OrderedDict(atlas_centers)
ATLAS = np.array(list(atlas_centers.values()), dtype=np.float32)

MD589 = np.array([[376.87494712731785,453.2021838243744,225.5],
                  [580.2902956709964,650.6552322784685,130.34657230772547],
                  [580.2902956709964,650.6552322784685,317.65342769227453]])
ATLAS = np.array([[200.03125, 757.0625 , 220.0],
                  [366.75   , 638.25   , 330.],
                  [367.1875 , 790.3125 , 180. ]])


n = ATLAS.shape[0]
ref_points = np.empty((n, 3))
for i in range(n):
    ref_points[i, 0] = MD589[i, 0]
    ref_points[i, 1] = MD589[i, 1]
    ref_points[i, 2] = MD589[i, 2]
    print(ref_points[i])
    #plt.plot(ref_points[i, 0], ref_points[i, 1], 'o', color=colors[i], markersize=10, markeredgecolor='none',
    #         label='reference points' if i == 0 else '')
#plt.grid()
#plt.axis([200, w, 200, h])
#plt.xlabel('X coordinate')
#plt.ylabel('Y coordinate')
#plt.legend(numpoints=1)
#plt.savefig('pointset_registration_1.png', format='png')


# transform the points
tsr_points = np.empty_like(ref_points)
for i in range(n):
    tsr_points[i, 0] = ATLAS[i, 0]
    tsr_points[i, 1] = ATLAS[i, 1]
    tsr_points[i, 2] = ATLAS[i, 2]
    # tsr_points[i] = T[:2] + np.dot(np.dot(S[:2, :2], R[:2, :2]), ref_points[i])
    print(tsr_points[i])
    #plt.plot(tsr_points[i, 0], tsr_points[i, 1], 's', color=colors[i], markersize=10, markeredgecolor='none',
    #         label='transformed points' if i == 0 else '')
# overwrite reference points in light gray
#plt.plot(ref_points[:, 0], ref_points[:, 1], 'o', color=my_gray, markersize=10, markeredgecolor='none',
#         label='reference points' if i == 0 else '')
# draw dashed lines between reference and transformed points
#for i in range(n):
#    plt.plot([ref_points[i, 0], tsr_points[i, 0]], [ref_points[i, 1], tsr_points[i, 1]], '--', color=colors[i])
#plt.legend(numpoints=1)
#plt.savefig('pointset_registration_2.png', format='png')

# compute the affine transform from the point set
translation, transformation = compute_affine_transform(ref_points, tsr_points)
invt = np.linalg.inv(transformation)
offset = -np.dot(invt, translation)
ref_centroid = np.mean(ref_points, axis=0)
tsr_centroid = np.mean(tsr_points, axis=0)
new_points = np.empty_like(ref_points)
for i in range(n):
    new_points[i] = ref_centroid + np.dot(transformation, tsr_points[i] - tsr_centroid)
    print('point %d will move to (%3.1f, %3.1f, %3.1f) to be compared with (%3.1f, %3.1f, %3.1f)' % (
        i, new_points[i, 0], new_points[i, 1], new_points[i, 2], ref_points[i, 0], ref_points[i, 1], ref_points[i, 2]))
    #plt.plot(new_points[i, 0], new_points[i, 1], 'x', color=colors[i], markersize=12,
    #         label='new points' if i == 0 else '')
#plt.legend(numpoints=1)
#plt.savefig('pointset_registration_3.png', format='png')
#plt.show()
df = pd.DataFrame(new_points, columns=['x', 'y','section'])
fig = px.scatter_3d(df, x='x', y='y', z='section',
              color='section')
fig.show()
