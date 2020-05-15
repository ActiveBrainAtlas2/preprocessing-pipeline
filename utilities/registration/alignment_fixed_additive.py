import numpy as np
#from skimage import io
import cv2 as cv
from os.path import expanduser
HOME = expanduser("~")
import os
import SimpleITK as sitk
from tqdm import tqdm

DIR = '/data2/edward/DK39'
ALIGNED = os.path.join(DIR, 'aligned')
RESIZED = os.path.join(DIR, 'resized')
INPUT = RESIZED
OUTPUT = ALIGNED

files = sorted(os.listdir(INPUT))
#files = files[2:-1]

#'fixed_fp': prev_fp,
#'moving_fp': curr_fp


def simple_resample(fixed_image, moving_image):
    return sitk.Elastix(fixed_image, moving_image)


movingFile = files[0]
movingPath = os.path.join(INPUT, movingFile)
fixedPath = movingPath
fixed_image = sitk.ReadImage(fixedPath, sitk.sitkFloat32)
moving_image = sitk.ReadImage(movingPath, sitk.sitkFloat32)
fixed_image = simple_resample(fixed_image, moving_image)

for file in tqdm(files):
    movingFile = file
    movingPath = os.path.join(INPUT, movingFile)
    moving_image = sitk.ReadImage(movingPath, sitk.sitkFloat32)
    fixed_image = simple_resample(fixed_image, moving_image)
    img = sitk.GetArrayFromImage(fixed_image)
    outfile = os.path.join(OUTPUT, file)
    flat = img.flatten()
    fmax = int(flat.max())
    fmin = int(flat.min())
    flat = flat + abs(fmin)
    img = np.reshape(flat, img.shape)
    img[img <= 0] = 0
    #io.imsave(outfile, img.astype('uint16'), check_contrast=False)
    cv.imwrite(outfile, img.astype('uint16'))
    img = None
print('done')
