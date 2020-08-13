# Add all annotated brains to the viewer
from timeit import  default_timer as timer
import os, sys
import numpy as np


HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)
from utilities.contour_utilities import get_structure_colors
VOL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/atlasV7/10.0um_annotationAsScoreVolume'
MD589_VOLUME_PATH = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/MD589/MD589_full_filled.npy'
MD589 = np.load(MD589_VOLUME_PATH)
xy_ng_resolution_um = 5

height, width, zdim = MD589.shape

#full_brain_volume_annotated = np.zeros((zdim,height,width), dtype=np.uint8)
full_brain_volume_annotated = np.zeros((MD589.shape), dtype=np.uint8)
files = os.listdir(VOL_DIR)
numpy_files = [f for f in files if f.endswith('.npy') and 'surround' not in f]
print('full brain volume shape:', full_brain_volume_annotated.shape)
midx = width // 2
midy = height // 2
midz = zdim // 2
print("origin", midx, midy, midz)
colors = get_structure_colors()

for n in numpy_files:
    structure = os.path.splitext(n)[0]
    try:
        color = colors[structure.upper()]
    except:
        sided = '{}_R'.format(structure.upper())
        color = colors[sided]


    volume_filename = os.path.join(VOL_DIR, '{}.npy'.format(structure))
    volume_input = np.load(volume_filename)
    volume_input = np.swapaxes(volume_input, 0, 2)

    volume_nonzero_indices = volume_input > 0
    volume_input[volume_nonzero_indices] = color
    structure_volume = volume_input.astype(np.uint8)

    origin_filename = os.path.join(VOL_DIR, '{}_origin_wrt_canonicalAtlasSpace.txt'.format(structure))
    origin_wrt = np.loadtxt(origin_filename)
    x,y,z = origin_wrt


    z_start = 30
    y_start = int(y) + midy
    x_start = int(x) + midx
    x_end = x_start + structure_volume.shape[2]
    y_end = y_start + structure_volume.shape[1]
    z_end = z_start + structure_volume.shape[0]

    try:
        full_brain_volume_annotated[z_start:z_end, y_start:y_end,x_start:x_end] = structure_volume
        print('Fit',str(structure).ljust(8), str(color).rjust(2), end="\t")
        print('shape', str(structure_volume.shape).rjust(18), end=", ")
        print('x range', str(x_start).rjust(4), str(x_end).rjust(4), end=", ")
        print('y range', str(y_start).rjust(4), str(y_end).rjust(4), end=", ")
        print('z range', str(z_start).rjust(4), str(z_end).rjust(4))
    except:
        print('Error',str(structure).ljust(8), str(color).rjust(2), end="\t")
        print('shape', str(structure_volume.shape).rjust(18), end=", ")
        print('x range', str(x_start).rjust(4), str(x_end).rjust(4), end=", ")
        print('y range', str(y_start).rjust(4), str(y_end).rjust(4), end=", ")
        print('z range', str(z_start).rjust(4), str(z_end).rjust(4))

OUTPUT = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes', 'atlasV8')
outfile = os.path.join(OUTPUT, 'volume_test.npy')
if np.amax(full_brain_volume_annotated) > 1:
    print('\nfull_brain_volume_annotated at', outfile)
    np.save(outfile, full_brain_volume_annotated.astype(np.uint8))
else:
    print('\nfinished testing\n')
