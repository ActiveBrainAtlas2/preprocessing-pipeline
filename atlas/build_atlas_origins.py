import json
import os, sys
from collections import defaultdict

import numpy as np
import pickle

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
atlas_name = 'atlasV8'
surface_level = 0.9
DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
OUTPUT = os.path.join(ATLAS_PATH, 'mesh')


centroid_filepath = os.path.join(ATLAS_PATH, '1um_meanPositions.pkl')

from utilities.imported_atlas_utilities import volume_to_polydata, save_mesh_stl, mirror_volume_v2, average_location

structure_file = os.path.join(PATH, 'neuroglancer', 'structure_key_minimal.json')
with open(structure_file, 'r') as f:
    structures = json.load(f)
structures = list(structures.values())
atlas_resolution_um = 10.0



centroids = pickle.load(open(centroid_filepath, "rb"))
#centroids = {s: c / atlas_resolution_um for s, c in centroids_data.items()}


for structure in structures:

    structure_filepath = os.path.join(ATLAS_PATH, 'structure', f'{structure}.npy')
    structure_volume = np.load(structure_filepath)
    origin_filepath = os.path.join(ATLAS_PATH, 'origin', f'{structure}.txt')
    structure_origin = np.loadtxt(origin_filepath)

    if str(structure).endswith('_L'):

        mean_shape = mirror_volume_v2(volume=structure_volume,
                                           centroid_wrt_origin=-structure_origin,
                                           new_centroid=centroids[structure])
    else:
        mean_shape = (structure_volume, structure_origin + centroids[structure])

    print(structure,'origin:'.ljust(20), mean_shape[1])


    volume = (mean_shape[0] >= surface_level, mean_shape[1])
    aligned_structure = volume_to_polydata(volume=volume,
                           num_simplify_iter=3, smooth=True,
                           return_vertex_face_list=False)
    filepath = os.path.join(OUTPUT, '{}.stl'.format(structure))
    save_mesh_stl(aligned_structure, filepath)

