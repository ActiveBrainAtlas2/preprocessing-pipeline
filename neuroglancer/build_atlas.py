import sys
import os

import numpy as np
import bloscpack as bp
import json



PATH = '/home/eddyod/programming/pipeline_utility'
sys.path.append(PATH)
from utilities.imported_atlas_utilities import load_original_volume_all_known_structures_v3, get_centroid_3d

INPUT_KEY_LOC = 'structure_key_minimal.json'
NUM_STRUCTS = 49
with open(INPUT_KEY_LOC, 'r') as f:
    structures = json.load(f)

structures = list(structures.values())
structures = structures[0:2]
atlas_name = 'atlasV7'
fixed_brain_name = 'MD589'
moving_brain_names = ['MD585', 'MD594']
resolution = '10.0um'
resolution_um = 10.0
structure_centroids_all_brains_um_wrt_fixed = []
fixed_brain_spec = {'name': fixed_brain_name, 'vol_type': 'annotationAsScore', 'resolution': resolution}

fixed_brain = load_original_volume_all_known_structures_v3(stack_spec=fixed_brain_spec, structures=structures)


fixed_brain_structure_centroids = get_centroid_3d(fixed_brain)
print('fixed_brain_structure_centroids', fixed_brain_structure_centroids)
fixed_brain_structure_centroids_um = {s: c * resolution_um for s, c in fixed_brain_structure_centroids.items()}
print('fixed_brain_structure_centroids_um', fixed_brain_structure_centroids_um)
structure_centroids_all_brains_um_wrt_fixed.append(fixed_brain_structure_centroids_um)

for brain_m in moving_brain_names:
    moving_brain_spec = {'name': brain_m, 'vol_type': 'annotationAsScore', 'resolution': resolution}

    moving_brain = load_original_volume_all_known_structures_v3(stack_spec=moving_brain_spec, structures=structures)

    alignment_spec = dict(stack_m=moving_brain_spec, stack_f=fixed_brain_spec, warp_setting=109)

    moving_brain_structure_centroids_input_resol = get_centroid_3d(moving_brain)

    # Load registration.

    # Alignment results fp: os.path.join(reg_root_dir, alignment_spec['stack_m']['name'], warp_basename, warp_basename + '_' + what + '.' + ext)
    transform_parameters_moving_brain_to_fixed_brain = load_alignment_results_v3(
        alignment_spec=alignment_spec, what='parameters')

    # Transform moving brains into alignment with the fixed brain.

    transformed_moving_brain_structure_centroids_input_resol_wrt_fixed = \
        dict(zip(moving_brain_structure_centroids_input_resol.keys(),
                 transform_points(pts=moving_brain_structure_centroids_input_resol.values(),
                                  transform=transform_parameters_moving_brain_to_fixed_brain)))

    transformed_moving_brain_structure_centroids_um_wrt_fixed = \
        {s: c * resolution_um for s, c in
         transformed_moving_brain_structure_centroids_input_resol_wrt_fixed.iteritems()}

    structure_centroids_all_brains_um_wrt_fixed.append(transformed_moving_brain_structure_centroids_um_wrt_fixed)
