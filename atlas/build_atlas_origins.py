import json
import os, sys
import numpy as np
import pickle

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
atlas_name = 'atlasV7'
surface_level = 0.9
DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
OUTPUT = os.path.join(ATLAS_PATH, 'mesh')

from utilities.imported_atlas_utilities import volume_to_polydata, save_mesh_stl, convert_to_surround_name, \
    get_structure_mean_positions_filepath, all_known_structures_unsided_including_surround_200um, load_mean_shape, \
    convert_volume_forms, convert_to_left_name, convert_to_right_name, mirror_volume_v2, save_original_volume

structure_file = os.path.join(PATH, 'neuroglancer', 'structure_key_minimal.json')
NUM_STRUCTS = 49
with open(structure_file, 'r') as f:
    structures = json.load(f)
structures = list(structures.values())
atlas_resolution = '10.0um'
atlas_resolution_um = 10.0
atlas_spec = dict(name=atlas_name, vol_type='score', resolution=atlas_resolution)
filepath = os.path.join(DATA_PATH, 'CSHL_volumes', atlas_name, '1um_meanPositions.pkl')

all_known_structures = all_known_structures_unsided_including_surround_200um()
centroids_wrt_canonicalAtlasSpace_um = pickle.load(open(filepath, "rb"))
centroids_wrt_canonicalAtlasSpace_10um = {s: c / atlas_resolution_um for s, c in
                                          centroids_wrt_canonicalAtlasSpace_um.items()}
mean_shapes_10um_wrt_stdShapeCentroid = {
    structure: load_mean_shape(atlas_name=atlas_name, structure=structure, resolution=atlas_resolution)
    for structure in structures}

# structures = singular_structures

INPUT = os.path.join(DATA_PATH, 'CSHL_meshes', atlas_name, 'mean_shapes')

for structure in structures:

    if str(structure).endswith('_L'):
        #print('left structure', structure)

        left_mean_shape_wrt_canonicalAtlasSpace_10um = mirror_volume_v2(
            volume=mean_shapes_10um_wrt_stdShapeCentroid[structure],
            centroid_wrt_origin=-mean_shapes_10um_wrt_stdShapeCentroid[structure][1],
            new_centroid=centroids_wrt_canonicalAtlasSpace_10um[structure])

        #save_original_volume(volume=left_mean_shape_wrt_canonicalAtlasSpace_10um,
        #                     stack_spec=atlas_spec,
        #                     structure=structure, wrt='canonicalAtlasSpace')
        left_volume = mean_shapes_10um_wrt_stdShapeCentroid[structure][0]
        left_origin = mean_shapes_10um_wrt_stdShapeCentroid[structure][1]
        new_centroid = centroids_wrt_canonicalAtlasSpace_10um[structure]
        left_mean_shape = mirror_volume_v2(volume=left_volume, centroid_wrt_origin=-left_origin, new_centroid=new_centroid)

    elif str(structure).endswith('_R'):
        #print('right structure', structure)

        right_mean_shape_wrt_canonicalAtlasSpace_10um = (mean_shapes_10um_wrt_stdShapeCentroid[structure][0],
                                                         mean_shapes_10um_wrt_stdShapeCentroid[structure][1] +
                                                         centroids_wrt_canonicalAtlasSpace_10um[structure])

        #save_original_volume(volume=right_mean_shape_wrt_canonicalAtlasSpace_10um,
        #                     stack_spec=atlas_spec,
        #                     structure=structure, wrt='canonicalAtlasSpace')
    else:
        structure_filepath = os.path.join(INPUT, f'10.0um_{structure}_volume.npy')
        structure_volume = np.load(structure_filepath)
        origin_filepath = os.path.join(INPUT, f'10.0um_{structure}_origin_wrt_meanShapeCentroid.txt')
        structure_origin = np.loadtxt(origin_filepath)
        mean_shape = (mean_shapes_10um_wrt_stdShapeCentroid[structure][0],
                                                   mean_shapes_10um_wrt_stdShapeCentroid[structure][1] +
                                                   centroids_wrt_canonicalAtlasSpace_10um[structure])
        #             mean_shape_wrt_canonicalAtlasSpace_all_structures_10um[name] = mean_shape_wrt_canonicalAtlasSpace_10um
        #save_original_volume(volume=mean_shape, stack_spec=atlas_spec, structure=structure,
        #                     wrt='canonicalAtlasSpace')
        print('Structure is singular', structure, end="\t")
        print('origin',mean_shape[1])
