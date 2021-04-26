import numpy as np
import os, sys
from tqdm import tqdm
import cv2


BASEINPUT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/CHATM2/preps'
INPUT = os.path.join(BASEINPUT, 'CH0/thumbnail')
files = sorted(os.listdir(INPUT))

for f in tqdm(files):
    infile = os.path.join(INPUT, f)
    img = cv2.imread(infile)
    ch1_img = img[:,:,0]
    ch2_img = img[:,:,1]
    ch3_img = img[:,:,2]
    ch1_outpath = os.path.join(BASEINPUT, 'CH1/thumbnail', f)
    ch2_outpath = os.path.join(BASEINPUT, 'CH2/thumbnail', f)
    ch3_outpath = os.path.join(BASEINPUT, 'CH3/thumbnail', f)
    cv2.imwrite(ch1_outpath, ch1_img.astype(np.uint8))
    cv2.imwrite(ch2_outpath, ch2_img.astype(np.uint8))
    cv2.imwrite(ch3_outpath, ch3_img.astype(np.uint8))
