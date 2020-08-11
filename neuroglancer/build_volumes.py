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
VOL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/atlasV7/score_volumes'
#full_brain_volume_annotated = np.zeros((268,3000,5000), dtype=np.uint8)

xy_ng_resolution_um = 5
width = 35617 # original value
height = 26086 # original value
y_voxels = 1+int( height*0.46*(.46/xy_ng_resolution_um) + 0.5)
x_voxels = 1+int( width*0.46*(.46/xy_ng_resolution_um) + 0.5)
width = 5000
height = 3000
full_brain_volume_annotated = np.zeros((268,height,width), dtype=np.uint8)

print('full brain volume shape:', full_brain_volume_annotated.shape)

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
structures = ['SC','IC', 'Sp5O_R']
#structures = ['SC']
midx = full_brain_volume_annotated.shape[2] // 2
midy = full_brain_volume_annotated.shape[1] // 2
for structure in structures:
    try:
        color = colors[structure.upper()]
    except:
        sided = '{}_R'.format(structure.upper())
        color = colors[sided]
    volume_filename = os.path.join(VOL_DIR, '{}.npy'.format(structure))
    volume_input = np.load(volume_filename)

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
    print("origin", midx, midy)

    z_start = 30
    y_start = int(midy + y)
    x_start = int(midx + x)

    #y_start = 1 + int(h * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
    #x_start = 1 + int(w * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
    print(structure, color, first_section, last_section, round(x), round(y), round(z), 'shape:', structure_volume.shape)

    z_len, y_len, x_len = np.shape(structure_volume)
    print(structure, 'z', z_start, z_len+z_start)
    print(structure, 'y', y_start, y_len+y_start)
    print(structure, 'x', x_start, x_len+x_start)

    y_len += y_start
    x_len += x_start
    for z in range(z_start, z_len):
        for y in range(y_start, y_len):
            for x in range(x_start, x_len):
                yy = y - y_start
                xx = x - x_start
                structure_val = structure_volume[z, yy, xx]
                if structure_val == 0:
                    continue
                else:
                    try:
                        full_brain_volume_annotated[z, y, x] = structure_val
                        #print('location:', x,y,z)
                    except Exception as e:
                        print(e)



OUTPUT = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes', 'atlasV8')
outfile = os.path.join(OUTPUT, 'volume_test.npy')
print('\nfull_brain_volume_annotated at', outfile)
np.save(outfile, np.ascontiguousarray(full_brain_volume_annotated.astype(np.uint8)))

