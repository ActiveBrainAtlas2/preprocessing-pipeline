import numpy as np
import os
from tqdm import tqdm
import cv2
from skimage import io


from abakit.lib.utilities_mask import pad_image, equalized, remove_strip

BASEINPUT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/CHATM2/preps'

"""
INPUT = os.path.join(BASEINPUT, 'CH0/thumbnail')
files = sorted(os.listdir(INPUT))
os.makedirs(os.path.join(BASEINPUT, 'CH1/thumbnail'), exist_ok=True)
os.makedirs(os.path.join(BASEINPUT, 'CH2/thumbnail'), exist_ok=True)
os.makedirs(os.path.join(BASEINPUT, 'CH3/thumbnail'), exist_ok=True)

os.makedirs(os.path.join(BASEINPUT, 'CH1/thumbnail_cleaned'), exist_ok=True)
os.makedirs(os.path.join(BASEINPUT, 'CH2/thumbnail_cleaned'), exist_ok=True)
os.makedirs(os.path.join(BASEINPUT, 'CH3/thumbnail_cleaned'), exist_ok=True)

for file in tqdm(files):
    infile = os.path.join(INPUT, file)
    img = cv2.imread(infile)
    ch1_img = img[:,:,0]
    ch2_img = img[:,:,1]
    ch3_img = img[:,:,2]
    ch1_outpath = os.path.join(BASEINPUT, 'CH1/thumbnail', file)
    ch2_outpath = os.path.join(BASEINPUT, 'CH2/thumbnail', file)
    ch3_outpath = os.path.join(BASEINPUT, 'CH3/thumbnail', file)
    cv2.imwrite(ch1_outpath, ch1_img.astype(np.uint8))
    cv2.imwrite(ch2_outpath, ch2_img.astype(np.uint8))
    cv2.imwrite(ch3_outpath, ch3_img.astype(np.uint8))
"""
max_width = 2000
max_height = 1000

for channel in [2]:
    INPUT = os.path.join(BASEINPUT, f'CH{channel}/thumbnail')
    files = sorted(os.listdir(INPUT))

    for file in tqdm(files):
        infile = os.path.join(INPUT, file)
        img = io.imread(infile)
        img, _ = remove_strip(img)
        mask = compute_mask(img, m=0.2, M=0.9, cc=False, opening=2, exclude_zeros=True)
        mask = mask.astype(int)
        mask[mask==0] = 0
        mask[mask==1] = 255
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask.astype(np.uint8), kernel, iterations=2)
        mask = mask.astype(np.uint8)
        fixed = cv2.bitwise_and(img, img, mask=mask)
        fixed = equalized(fixed)
        BASEOUTPUT = os.path.join(BASEINPUT, f'CH{channel}/thumbnail_cleaned')
        outpath = os.path.join(BASEOUTPUT, file)
        os.makedirs(BASEOUTPUT, exist_ok=True)
        fixed = np.rot90(fixed, 3, axes=(1,0))
        fixed = np.flip(fixed, axis=1)
        fixed = pad_image(fixed, file, max_width, max_height, 0)

        cv2.imwrite(outpath, fixed.astype(np.uint16))
