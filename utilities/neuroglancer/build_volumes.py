# Add all annotated brains to the viewer
from timeit import  default_timer as timer
import os, sys
import numpy as np


HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)
from utilities.contour_utilities import get_structure_colors
#VOL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/atlasV7/10.0um_annotationAsScoreVolume'
VOL_DIR = '/net/birdstore/Active_Atlas_Data/copied_from_S3/mousebrainatlas-data/CSHL_volumes/atlasV7/atlasV7_10.0um_scoreVolume/score_volumes'

xy_ng_resolution_um = 5

x_length = 2000
y_length = 1500
z_length = 1500
full_brain_volume_annotated = np.zeros((z_length, y_length, x_length), dtype=np.uint8)


files = os.listdir(VOL_DIR)
numpy_files = [f for f in files if f.endswith('.npy') and 'surround' not in f]
print('full brain volume shape:', full_brain_volume_annotated.shape)
colors = get_structure_colors()

for n in numpy_files:
    prefix = os.path.splitext(n)[0]
    structure = prefix.split('_', 3)[3]

    try:
        color = colors[structure.upper()]
    except:
        sided = '{}_R'.format(structure.upper())
        color = colors[sided]

    #if structure not in ['SC', 'Sp5C_R', 'Sp5C_L']:
    #    continue

    threshold = 0.90
    volume_filename = os.path.join(VOL_DIR, n)
    volume_input = np.load(volume_filename)
    volume_input = np.swapaxes(volume_input, 0, 2)
    volume_input = np.swapaxes(volume_input, 1, 2)
    volume_nonzero_indices = volume_input >= threshold
    volume_nonone_indices = volume_input < threshold
    volume_input[volume_nonzero_indices] = color
    volume_input[volume_nonone_indices] = 0
    structure_volume = volume_input.astype(np.uint8)

    origin_filename = os.path.join(VOL_DIR, '{}_origin_wrt_canonicalAtlasSpace.txt'.format(prefix))
    origin_wrt = np.loadtxt(origin_filename)
    x, y, z = origin_wrt

    x, y, z = origin_wrt
    x_start = int(x) + x_length // 2
    y_start = int(y) + y_length // 2
    z_start = int(z) + z_length // 2

    x_end = x_start + structure_volume.shape[2]
    y_end = y_start + structure_volume.shape[1]
    z_end = z_start + structure_volume.shape[0]

    try:
        full_brain_volume_annotated[z_start:z_end, y_start:y_end,x_start:x_end] = structure_volume
        print('Fit', str(structure).ljust(8), str(color).rjust(2), end="\t")
        print('shape', str(structure_volume.shape).rjust(18), end=", ")
        print('x range', str(x_start).rjust(4), str(x_end).rjust(4), end=", ")
        print('y range', str(y_start).rjust(4), str(y_end).rjust(4), end=", ")
        print('z range', str(z_start).rjust(4), str(z_end).rjust(4))
    except:
        print('Error', str(structure).ljust(8), str(color).rjust(2), end="\t")
        print('shape', str(structure_volume.shape).rjust(18), end=", ")
        print('x range', str(x_start).rjust(4), str(x_end).rjust(4), end=", ")
        print('y range', str(y_start).rjust(4), str(y_end).rjust(4), end=", ")
        print('z range', str(z_start).rjust(4), str(z_end).rjust(4))

full_brain_volume_annotated = np.swapaxes(full_brain_volume_annotated, 0, 2)
OUTPUT = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes', 'atlasV8')
outfile = os.path.join(OUTPUT, 'volume_test.npy')
if np.amax(full_brain_volume_annotated) > 1:
    print('\nfull_brain_volume_annotated at', outfile)
    np.save(outfile, full_brain_volume_annotated.astype(np.uint8))
else:
    print('\nfinished testing\n')
