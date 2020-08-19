import os, sys
import json
import numpy as np
HOME = os.path.expanduser("~")

PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.imported_atlas_utilities import load_original_volume_all_known_structures_v3, get_centroid_3d, \
    load_alignment_results_v3, transform_points, average_location, \
    convert_to_original_name, name_unsided_to_color, paired_structures, \
    convert_to_left_name, convert_to_right_name, load_original_volume_v2, save_alignment_results_v3, \
    convert_transform_forms, transform_volume_v4, volume_to_polydata, singular_structures, \
    average_shape, convert_to_surround_name, \
    save_mesh_stl, get_surround_volume_v2, MESH_DIR


structure_path = os.path.join(PATH, 'neuroglancer', 'structure_key_minimal.json')
with open(structure_path, 'r') as f:
    structures = json.load(f)
structures = list(structures.values())
atlas_name = 'atlasV8'
atlas_resolution = '10.0um'
atlas_spec = dict(name=atlas_name, vol_type='score', resolution=atlas_resolution)
mesh_path = os.path.join(MESH_DIR, atlas_name, 'aligned_stls')
os.makedirs(mesh_path, exist_ok=True)

for name_s in structures:
    aligned_structure = load_original_volume_v2(stack_spec=atlas_spec, structure=name_s, bbox_wrt='canonicalAtlasSpace')

    surface_level = 0.9
    aligned_mesh = volume_to_polydata(volume=(aligned_structure[0] >= surface_level, aligned_structure[1]),
                 num_simplify_iter=3, smooth=True,
                 return_vertex_face_list=False)
    filepath = os.path.join(mesh_path, '{}.stl'.format(name_s))
    save_mesh_stl(aligned_mesh, filepath)
