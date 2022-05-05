import os
import sys
import argparse

import numpy as np
from pystackreg import StackReg
from pystackreg.util import to_uint16
from skimage import io

def create_stack(animal, debug):

    #load reference and "moved" image
    INPUT = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps/CH1/thumbnail_cleaned/'
    ALIGNED_PATH = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps/CH1/thumbnail_stack_aligned/'
    os.makedirs(ALIGNED_PATH, exist_ok=True)
    try:
        files = sorted(os.listdir(INPUT))
    except Exception as e:
        print(f'Error reading {animal} files')
        sys.exit()
    

    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath, img_num=0)
    height = midfile.shape[0]
    width = midfile.shape[1]

    if debug:
        files = files[0:6]

    f = len(files)
    img0 = np.zeros([f, height, width], dtype=np.uint16)

    for i, f in enumerate(files):
        inpath = os.path.join(INPUT, f)
        infile = io.imread(inpath)
        img0[i, :, :] = infile

    print(f'Working on a stack with shape: {img0.shape} and dtype: {img0.dtype}')

    sr = StackReg(StackReg.RIGID_BODY)
    reg = sr.register_transform_stack(img0 - img0.min())
    """
    # register each frame to the previous (already registered) one
    # this is what the original StackReg ImageJ plugin uses
    out_previous = sr.register_transform_stack(img0, reference='previous')
    print('register each frame to the previous (already registered) one')
    print(out_previous.dtype, out_previous.shape)

    # register to first image
    out_first = sr.register_transform_stack(img0, reference='first')
    print('register to first image')
    print(out_first.dtype, out_first.shape)


    # register to mean of first 10 images
    out_first10 = sr.register_transform_stack(img0, reference='first', n_frames=10)
    print('register to mean of first 10 images')
    print(out_first10.dtype, out_first10.shape)
    # calculate a moving average of 10 images, then register the moving average to the mean of
    # the first 10 images and transform the original image (not the moving average)
    out_moving10 = sr.register_transform_stack(img0, reference='mean', n_frames=5, moving_average = 5)
    print('calculate a moving average of 10 images')
    print(out_moving10.dtype, out_moving10.shape)
    """

    # register to mean image
    out_mean = sr.register_transform_stack(img0, reference='mean')
    print('register to mean image')
    print(out_mean.dtype, out_mean.shape)


    for i in range(0, out_mean.shape[0]):
        outpath = os.path.join(ALIGNED_PATH, f'{str(i).zfill(3)}.tif')
        img = out_mean[i,:,:]
        reg_int = to_uint16(img)
        io.imsave(outpath, reg_int)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--debug', help='Enter debug True|False', required=False, default='true')

    args = parser.parse_args()
    animal = args.animal
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_stack(animal, debug)

