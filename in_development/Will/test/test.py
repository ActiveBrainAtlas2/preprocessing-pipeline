#%%
import sys
import os
sys.path.append('/scratch/programming/preprocessing-pipeline/src')
from skimage import io
from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
import matplotlib.pyplot as plt
import numpy as np
import cv2
from skimage import measure
from lib.utilities_mask import place_image,rotate_image
import scipy.ndimage
from scipy.signal import savgol_filter
from scipy import fftpack
#%%
animal = 'DK55'
sqlController = SqlController(animal)
fileLocationManager = FileLocationManager(animal)
input = fileLocationManager.get_thumbnail_aligned()
files = os.listdir(input)
filei = '217.tif'
img = io.imread(os.path.join(input,filei))
img = np.flip(img)
img = np.flip(img, axis=1)
mask = img>np.average(img)
_,masks,stats,_=cv2.connectedComponentsWithStats(np.int8(mask))
seg_sizes = stats[:,-1]
second_largest = np.argsort(seg_sizes)[-2]
mask = masks==second_largest
print()
sub_contours = measure.find_contours(mask, 0)
sub_contour = sub_contours[0]
sub_contour.T[[0, 1]] = sub_contour.T[[1, 0]]
pts = sub_contour.astype(np.int32).reshape((-1, 2))
if len(pts)>99:
    pts = savgol_filter((pts[:,0],pts[:,1]), 99, 1).T.astype(np.int32)
sub_shell = np.zeros(mask.shape, dtype='uint8')
sub_shell = cv2.polylines(sub_shell, [pts], True, 1, 5, lineType=cv2.LINE_AA)
plt.imshow(sub_shell)
# %%
plt.imshow(img)

# %%
plt.scatter(pts[:,0],pts[:,1])
# %%
pts = sub_contour.astype(np.int32).reshape((-1, 2))
pts = smooth_data_fft(pts,1)
# %%
def smooth_data_fft(arr, span):  # the scaling of "span" is open to suggestions
    w = fftpack.rfft(arr)
    spectrum = w ** 2
    cutoff_idx = spectrum < (spectrum.max() * (1 - np.exp(-span / 2000)))
    w[cutoff_idx] = 0
    return fftpack.irfft(w)
# %%
pts = savgol_filter((pts[:,0],pts[:,1]), 99, 0).astype(np.int32).T
# %%
