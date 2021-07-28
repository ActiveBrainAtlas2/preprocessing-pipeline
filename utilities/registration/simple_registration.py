from os.path import expanduser
from tqdm import tqdm
HOME = expanduser("~")
import os, sys
import cv2


animal = 'DK63'
DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps'
INPUT = os.path.join(DIR, 'CH1', 'thumbnail_cleaned')
ELASTIX = os.path.join(DIR, 'elastix')
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.registration.utilities_registration import register_simple

files = sorted(os.listdir(INPUT))
img = cv2.imread(os.path.join(INPUT, files[0]), -1)
midx = img.shape[1] / 2
midy = img.shape[0] / 2

for f in tqdm(range(len(files) - 1)):
    fixed_index = str(f).zfill(3)
    moving_index = str(f+1).zfill(3)
    outdir = os.path.join(ELASTIX, f'{moving_index}_to_{fixed_index}')
    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, 'TransformParameters.0.txt')
    
    if os.path.exists(outfile):
        continue
    
    R, xshift, yshift = register_simple(INPUT, fixed_index, moving_index)

    f = open(outfile, "a")
    f.write(f"(TransformParameters {R} {xshift} {yshift})\n")
    f.write(f"(CenterOfRotationPoint {midx} {midy})\n")
    f.write("(Spacing 1.0 1.0)\n")
    f.close()
