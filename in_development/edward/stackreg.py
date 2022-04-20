import os
import sys
import numpy as np
from pystackreg import StackReg
from pystackreg.util import to_uint16
from skimage import io

#load reference and "moved" image
DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK73/preps/CH1/thumbnail_cleaned/'
ALIGNED_PATH = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK73/preps/CH1/thumbnail_aligned/'

files = sorted(os.listdir(DATA_PATH))
w = 1796
h = 2703
#files = files[0:10]
f = len(files)
img0 = np.zeros([f, w, h], dtype=np.uint16)

for i, f in enumerate(files):
    inpath = os.path.join(DATA_PATH, f)
    infile = io.imread(inpath)
    img0[i, :, :] = infile

print(img0.shape, img0.dtype)

#img0 = io.imread(stack) # 3 dimensions : frames x width x height

sr = StackReg(StackReg.RIGID_BODY)
reg = sr.register_transform_stack(img0 - img0.min())
# register each frame to the previous (already registered) one
# this is what the original StackReg ImageJ plugin uses
out_previous = sr.register_transform_stack(img0, reference='previous')
print('register each frame to the previous (already registered) one')
print(out_previous.dtype, out_previous.shape)

# register to first image
out_first = sr.register_transform_stack(img0, reference='first')
print('register to first image')
print(out_first.dtype, out_first.shape)

# register to mean image
out_mean = sr.register_transform_stack(img0, reference='mean')
print('register to mean image')
print(out_mean.dtype, out_mean.shape)

# register to mean of first 10 images
out_first10 = sr.register_transform_stack(img0, reference='first', n_frames=10)
print('register to mean of first 10 images')
print(out_first10.dtype, out_first10.shape)

# calculate a moving average of 10 images, then register the moving average to the mean of
# the first 10 images and transform the original image (not the moving average)
out_moving10 = sr.register_transform_stack(img0, reference='first', n_frames=10, moving_average = 10)
print('calculate a moving average of 10 images')
print(out_moving10.dtype, out_moving10.shape)

for i in range(0, out_moving10.shape[0]):
    outpath = os.path.join(ALIGNED_PATH, f'{str(i).zfill(3)}.tif')
    img = out_moving10[i,:,:]
    reg_int = to_uint16(img)
    io.imsave(outpath, reg_int)
