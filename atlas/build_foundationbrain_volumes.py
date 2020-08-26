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
from utilities.contour_utilities import get_contours_from_annotations, add_structure_to_neuroglancer, \
    create_full_volume, get_structure_colors
from utilities.imported_atlas_utilities import get_all_structures
xy_ng_resolution_um = 5
color_radius = 3
animal = 'MD589'
# MD585: x_um = 35617,           y_um = 26086
# MD585: x_pixels_.46res = x_um*0.46,  y_pixels_.46res = y_um*0.46
# MD585: x_pixels_newres = x_pixels_.46res*(0.46/newres), y_pixels_newres = y_pixels_.46res*(0.46/newres)
# microns/resolution
width = 43700
height = 32400
INPUT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}/preps/CH1/thumbnail'.format(animal)
zdim = len(os.listdir(INPUT))
#y_voxels = 1 + int(height * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
#x_voxels = 1 + int(width * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
#full_brain_volume_annotated = np.zeros((zdim, y_voxels, x_voxels), dtype=np.uint8)
width = 35617 # original value
height = 26086 # original value
y_voxels = 1+int( height*0.46*(.46/xy_ng_resolution_um) + 0.5)
x_voxels = 1+int( width*0.46*(.46/xy_ng_resolution_um) + 0.5)
full_brain_volume_annotated = np.zeros((268,y_voxels,x_voxels), dtype=np.uint8)
full_brain_volume_annotated = np.zeros((268,3000,5000), dtype=np.uint8)
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
#print(all_structures)
#structure_color = {'SC': 18, 'IC': 11, 'SNR': 20}
#structure_color = {'SC': 18, 'IC': 11, 'SNR': 20}
structures = [s.upper() for s in all_structures]
colors = get_structure_colors()
viewer = neuroglancer.Viewer()
structures = ['SC', 'IC', 'Sp5O_L', 'Sp5O_R']
for structure in structures:
    try:
        color = colors[structure.upper()]
    except:
        sided = '{}_R'.format(structure)
        color = colors[sided]

    print(structure, color, end="\t")
    contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations, densify=4)
    if first_sec == 0 or last_sec == 0:
        continue

    threshold = 1
    solid_volume = True
    no_offset_big_volume = True
    #for section in sorted(contour_annotations):
    #    print(section)
    #sys.exit()

    structure_volume, xyz_offsets = create_full_volume(contour_annotations, structure, first_sec, last_sec, \
        color_radius, xy_ng_resolution_um, threshold, color)


    z_len, y_len, x_len = np.shape(structure_volume)
    print('volume shape', structure_volume.shape, end="\t")
    print('z range:', xyz_offsets[2], z_len, end="\t")
    print('y range:', xyz_offsets[1], y_len, end="\t")
    print('x range:', xyz_offsets[0], x_len, end="\t")
    #     full_brain_volume_annotated[0:z_len, 0:y_len, 0:x_len] = str_volume.copy()
    for z in range(xyz_offsets[2], z_len):
        for y in range(xyz_offsets[1], y_len):
            for x in range(xyz_offsets[0], x_len):
                structure_val = structure_volume[z, y, x]
                if structure_val == 0:
                    continue
                else:
                    try:
                        full_brain_volume_annotated[z, y, x] = structure_val
                    except Exception as e:
                        print(e)

OUTPUT = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes', animal)
outfile = os.path.join(OUTPUT, 'full_brain_volume_annotated.npy')
print('full_brain_volume_annotated at', OUTPUT)
np.save(outfile, np.ascontiguousarray(full_brain_volume_annotated))
