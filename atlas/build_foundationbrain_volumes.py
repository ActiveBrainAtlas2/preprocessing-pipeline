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
from utilities.imported_atlas_utilities import get_all_structures, get_structures

xy_ng_resolution_um = 5
color_radius = 3
animal = 'MD589'


CSV_PATH = '/net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations'
csvfile = os.path.join(CSV_PATH, f'{animal}_annotation.csv')
hand_annotations = pd.read_csv(csvfile)
hand_annotations['vertices'] = hand_annotations['vertices'] \
    .apply(lambda x: x.replace(' ', ','))\
    .apply(lambda x: x.replace('\n',','))\
    .apply(lambda x: x.replace(',]',']'))\
    .apply(lambda x: x.replace(',,', ','))\
    .apply(lambda x: x.replace(',,', ','))\
    .apply(lambda x: x.replace(',,', ',')).apply(lambda x: x.replace(',,', ','))

hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))
structures = get_structures()
#
structures_arr = hand_annotations.name.unique()
annotation_structures = structures_arr.tolist()
structures = [a for a in annotation_structures if a in structures]
colors = get_structure_colors()

x_length = 1000
y_length = 1000
z_length = 300
full_brain_volume_annotated = np.zeros((x_length, y_length, z_length), dtype=np.uint32)


for structure in structures:
    try:
        color = colors[structure.upper()]
    except:
        sided = '{}_R'.format(structure)
        try:
            color = colors[sided]
        except:
            color = 100

    print(structure, color, end="\t")
    contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations,
                                                                             densify=4)
    if first_sec == 0 or last_sec == 0:
        print('No sections found')
        continue
    else:
        print('Section start, end:', first_sec, last_sec, end="\t")

    threshold = 1
    volume, xyz_offsets = create_full_volume(contour_annotations, structure, first_sec, last_sec, \
                                                       color_radius, xy_ng_resolution_um, threshold, color)

    x_start, y_start, z_start = xyz_offsets
    x_end = x_start + structure_volume.shape[2]
    y_end = y_start + structure_volume.shape[1]
    z_end = z_start + structure_volume.shape[0]
    print('X range', x_start, x_end, end="\t")
    print('Y range', y_start, y_end, end="\t")
    print('Z range', z_start, z_end)
