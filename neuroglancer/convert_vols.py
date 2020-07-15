"""
This script takes as input a segmentation map represented as a numpy array and converts into a
precomputed volume to be shown on neuroglancer.
"""

import numpy as np
import os
import json
import nibabel as nib
from neuroglancer_scripts.scripts import (generate_scales_info,
                                          slices_to_precomputed,
                                          compute_scales, volume_to_precomputed)
animal = 'atlas'
VOL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/vol_fill'

NI_OUT = os.path.join(VOL_DIR, animal, 'filled.nii')
ATLAS_FILE = os.path.join(VOL_DIR, 'compressed_atlas.npy')
OUTPUT = os.path.join(VOL_DIR, animal, 'annotations')


if not os.path.isdir(OUTPUT):
    os.mkdir(OUTPUT)

vol_m = np.load(ATLAS_FILE)
volume_file = vol_m.astype(np.uint8)
del vol_m

#volume_file = np.swapaxes(volume_file,1,0)
"""
volume_img = nib.Nifti1Image(volume_file, affine=np.array(\
      [[ 0.005,  0.,  0.,  0.],\
       [ 0.,   0.005,  0.,  0.],\
       [ 0.,  0.,  0.02,  0.],\
       [ 0.,  0.,  0.,  1.]]))
"""
volume_img = nib.Nifti1Image(volume_file, affine=np.array(\
      [[ 1,  0.,  0.,  0.],\
       [ 0.,   1,  0.,  0.],\
       [ 0.,  0.,  1,  0.],\
       [ 0.,  0.,  0.,  1.]]))
nib.save(volume_img, NI_OUT)

volume_to_precomputed.main(['', NI_OUT, OUTPUT, '--generate-info', '--no-gzip'])
with open(os.path.join(os.path.join(OUTPUT, 'info_fullres.json')), 'r') as info_file:
    info = json.load(info_file)

info["type"] = "segmentation"
info["segment_properties"] = "names"

with open(os.path.join(os.path.join(OUTPUT, 'info_fullres.json')), 'w') as info_file:
    json.dump(info, info_file)

generate_scales_info.main(['', os.path.join(OUTPUT, 'info_fullres.json'), '--encoding', 'compressed_segmentation',
                           OUTPUT, '--max-scales', '10', '--target-chunk-size', '128'])

volume_to_precomputed.main(['', NI_OUT, OUTPUT, '--flat', '--no-gzip'])
compute_scales.main(['', OUTPUT, '--downscaling-method', "majority", "--flat", "--no-gzip"])
