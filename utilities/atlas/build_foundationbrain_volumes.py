# Add all annotated brains to the viewer
from timeit import  default_timer as timer
import os, sys

import numpy as np
from scipy import ndimage
import pandas as pd
import ast


HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.atlas.utilities_contour import get_contours_from_annotations, create_full_volume
from utilities.sqlcontroller import SqlController
from utilities.file_location import DATA_PATH

xy_ng_resolution_um = 10
color_radius = 3
animal = 'MD589'
sqlController = SqlController(animal)

csvfile = os.path.join(DATA_PATH, 'atlas_data/foundation_brain_annotations',  f'{animal}_annotation.csv')
#csvfile = os.path.join(DATA_PATH, 'atlas_data', f'{animal}_corrected_vertices.csv')
hand_annotations = pd.read_csv(csvfile)

hand_annotations['vertices'] = hand_annotations['vertices'] \
    .apply(lambda x: x.replace(' ', ',')) \
    .apply(lambda x: x.replace('\n', ',')) \
    .apply(lambda x: x.replace(',]', ']')) \
    .apply(lambda x: x.replace(',,', ',')) \
    .apply(lambda x: x.replace(',,', ',')) \
    .apply(lambda x: x.replace(',,', ',')).apply(lambda x: x.replace(',,', ','))

hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))

structures = sqlController.get_structures_dict()
#
#structures_arr = hand_annotations.name.unique()
#structures = structures_arr.tolist()
x_length = 1000
y_length = 1000
z_length = 300
for structure, values in structures.items():
    if structure not in ['SC', '10N_L', '10N_R']:
        continue
    try:
        color = values[1]
    except:
        color = 999

    contour_annotations, first_sec, last_sec = get_contours_from_annotations(animal, structure, hand_annotations, densify=4)
    if first_sec == 0 or last_sec == 0:
        continue

    threshold = 1
    solid_volume = True
    no_offset_big_volume = True

    volume, xyz_offsets = create_full_volume(contour_annotations, structure, first_sec, last_sec, \
        color_radius, xy_ng_resolution_um, threshold, color)


    #x, y, z = xyz_offsets
    volume = np.swapaxes(volume, 0 ,2)
    #volume = np.rot90(volume, axes=(0, 1))
    #volume = np.flip(volume, axis=0)
    x, y, z = (np.array(xyz_offsets) + ndimage.measurements.center_of_mass(volume))

    print(structure, volume.shape, x,y,z)
    continue
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
