# Add all annotated brains to the viewer
from timeit import  default_timer as timer
import os, sys

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
#viewer = neuroglancer.Viewer()
structures = ['SC', 'IC', 'Sp5O_L', 'Sp5O_R']
x_length = 1000
y_length = 1000
z_length = 300
full_brain_volume_annotated = np.zeros((x_length, y_length, z_length), dtype=np.uint32)
for structure in structures:
    try:
        color = colors[structure.upper()]
    except:
        sided = '{}_R'.format(structure)
        color = colors[sided]

    contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations, densify=4)
    if first_sec == 0 or last_sec == 0:
        continue

    threshold = 1
    solid_volume = True
    no_offset_big_volume = True

    volume, xyz_offsets = create_full_volume(contour_annotations, structure, first_sec, last_sec, \
        color_radius, xy_ng_resolution_um, threshold, color)

    x, y, z = xyz_offsets
    x_start = int(x) + x_length // 2
    y_start = int(y) + y_length // 2
    z_start = int(z) // 2 + z_length // 2
    x_end = x_start + volume.shape[0]
    y_end = y_start + volume.shape[1]
    z_end = z_start + (volume.shape[2] + 1) // 2

    print(structure, 'X range', x_start, x_end, end="\t")
    print('Y range', y_start, y_end, end="\t")
    print('Z range', z_start, z_end, end="\t")

    z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
    volume = volume[:, :, z_indices]
    print('Shape:', volume.shape)
    continue
    full_brain_volume_annotated[x_start:x_end, y_start:y_end,z_start:z_end] += volume
