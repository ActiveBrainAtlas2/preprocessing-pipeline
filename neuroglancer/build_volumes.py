# Add all annotated brains to the viewer
from timeit import  default_timer as timer
import os, sys

import neuroglancer
import numpy as np
import pandas as pd
import ast


HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)
from utilities.contour_utilities import min_max_sections, add_structure_to_neuroglancer, \
    create_full_volume, get_structure_colors, get_contours_from_annotations
from utilities.imported_atlas_utilities import get_all_structures
VOL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/atlasV7/10.0um_annotationAsScoreVolume'
#full_brain_volume_annotated = np.zeros((268,3000,5000), dtype=np.uint8)

xy_ng_resolution_um = 5
width = 35617 # original value
height = 26086 # original value
y_voxels = 1+int( height*0.46*(.46/xy_ng_resolution_um) + 0.5)
x_voxels = 1+int( width*0.46*(.46/xy_ng_resolution_um) + 0.5)
width = 1429
height = 1099
zdim = 288
#full_brain_volume_annotated = np.zeros((zdim,height,width), dtype=np.uint8)
full_brain_volume_annotated = np.zeros((zdim, height, width), dtype=np.uint8)

print('full brain volume shape:', full_brain_volume_annotated.shape)
midx = width // 2
midy = height // 2
midz = zdim // 2
print("origin", midx, midy, midz)

#neuroglancer.set_server_bind_address(bind_port='33645')
#viewer = neuroglancer.Viewer()
csvfile = os.path.join(DIR, 'neuroglancer', 'contours', 'hand_annotations.csv')
hand_annotations = pd.read_csv(csvfile)
hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))
all_structures = get_all_structures()
#
structures_arr = hand_annotations.name.unique()
structures = structures_arr.tolist()
#print(structures)
#structure_color = {'SC': 18, 'IC': 11, 'SNR': 20}
#structure_color = {'SC': 18, 'IC': 11, 'SNR': 20}
structures = [s.upper() for s in all_structures]
colors = get_structure_colors()
viewer = neuroglancer.Viewer()
structures = ['SC','IC']
structures = ['Sp5C_R', 'Sp5O_R', 'Sp5I_R']
#structures = ['SC','Sp5C_R', 'IC']

for structure in structures:
    try:
        color = colors[structure.upper()]
    except:
        sided = '{}_R'.format(structure.upper())
        color = colors[sided]
    volume_filename = os.path.join(VOL_DIR, '{}.npy'.format(structure))
    volume_input = np.load(volume_filename)
    #volume_input = np.swapaxes(volume_input, 0, 2)

    volume_nonzero_indices = volume_input > 0
    volume_input[volume_nonzero_indices] = color
    structure_volume = volume_input.astype(np.uint8)

    origin_filename = os.path.join(VOL_DIR, '{}_origin_wrt_canonicalAtlasSpace.txt'.format(structure))
    origin_wrt = np.loadtxt(origin_filename)
    x,y,z = origin_wrt
    first_section, last_section = min_max_sections(structure, hand_annotations)

    threshold = 1
    solid_volume = True
    no_offset_big_volume = True
    color_radius = 3

    #contour_annotations, first_sec, last_sec = get_contours_from_annotations('MD589', structure, hand_annotations, densify=4)
    #structure_volume, xyz_offsets = create_full_volume(contour_annotations, structure, first_sec, last_sec, \
    #    color_radius, xy_ng_resolution_um, threshold, color)

    """
    SC z 36 219
    SC y 410 1167
    SC x 1466 2486
    IC z 30 222
    IC y 415 1270
    IC x 1507 2602
    """

    z_start = 30
    ext = 150
    y_start = int(y) + midy
    x_start = int(x) + midx

    #y_start = 1 + int(y_start * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
    #x_start = 1 + int(x_start * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
    print(str(structure).ljust(8), color, end=",")
    print('x', str(round(x)).rjust(7), end=", ")
    print('y', str(round(y)).rjust(7), end=", ")
    print('z', str(round(z)).rjust(7), end=", ")
    print('shape', structure_volume.shape, end=", ")

    z_len, y_len, x_len = np.shape(structure_volume)
    x_end = x_start + x_len
    y_end = y_start + y_len
    z_end = z_start + z_len
    print('x range', str(x_start).rjust(4), str(x_end).rjust(4), end=", ")
    print('y range', str(y_start).rjust(4), str(y_end).rjust(4), end=", ")
    print('z range', str(z_start).rjust(4), str(z_end).rjust(4))
    y_len += y_start
    x_len += x_start

    full_brain_volume_annotated[x_start:x_start + structure_volume.shape[2],
    y_start:y_start + structure_volume.shape[1], z_start:z_start + structure_volume.shape[0]] = structure_volume


OUTPUT = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes', 'atlasV8')
outfile = os.path.join(OUTPUT, 'volume_test.npy')
if np.amax(full_brain_volume_annotated) > 1:
    print('\nfull_brain_volume_annotated at', outfile)
    np.save(outfile, full_brain_volume_annotated.astype(np.uint8))
else:
    print('\nfinished testing\n')
