import json
import os, sys
from collections import defaultdict

import numpy as np
import pickle
from tqdm import tqdm


HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
atlas_name = 'atlasV8'
surface_level = 0.9
DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)

from utilities.imported_atlas_utilities import volume_to_polydata, save_mesh_stl, \
    load_original_volume_v2, get_centroid_3d, convert_transform_forms, transform_volume_v4, average_shape, \
    singular_structures, load_original_volume_all_known_structures_v3, \
    load_alignment_results_v3, transform_points, average_location, mirror_volume_v2
from utilities.aligner_v3 import Aligner

structure_file = os.path.join(PATH, 'neuroglancer', 'structure_key_minimal.json')
with open(structure_file, 'r') as f:
    structures = json.load(f)
structures = list(structures.values())
resolution = '10.0um'
atlas_resolution_um = 10.0
fixed_brain_name = 'MD589'
moving_brain_names = ['MD585', 'MD594']
fixed_brain_spec = {'name': fixed_brain_name, 'vol_type': 'annotationAsScore', 'resolution': resolution}
structure_centroids_all_brains_um_wrt_fixed = []

for brain_m in moving_brain_names:
    moving_brain_spec = {'name': brain_m, 'vol_type': 'annotationAsScore', 'resolution': resolution}
    print('Brain', moving_brain_spec)
    moving_brain = load_original_volume_all_known_structures_v3(stack_spec=moving_brain_spec,
                                                                structures=structures, in_bbox_wrt='wholebrain')
    alignment_spec = dict(stack_m=moving_brain_spec, stack_f=fixed_brain_spec, warp_setting=109)
    moving_brain_structure_centroids_input_resol = get_centroid_3d(moving_brain)
    # Load registration.
    # Alignment results fp: os.path.join(reg_root_dir, alignment_spec['stack_m']['name'], warp_basename, warp_basename + '_' + what + '.' + ext)
    transform_parameters_moving_brain_to_fixed_brain = load_alignment_results_v3(alignment_spec=alignment_spec, what='parameters')
    # Transform moving brains into alignment with the fixed brain.
    transformed_moving_brain_structure_centroids_input_resol_wrt_fixed = \
    dict(list(zip(list(moving_brain_structure_centroids_input_resol.keys()),
                  transform_points(pts=list(moving_brain_structure_centroids_input_resol.values()),
                                   transform=transform_parameters_moving_brain_to_fixed_brain))))

    transformed_moving_brain_structure_centroids_um_wrt_fixed = \
        {s: c * atlas_resolution_um for s, c in
        list(transformed_moving_brain_structure_centroids_input_resol_wrt_fixed.items())}

    structure_centroids_all_brains_um_wrt_fixed.append(transformed_moving_brain_structure_centroids_um_wrt_fixed)


structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed = defaultdict(list)
for sc in structure_centroids_all_brains_um_wrt_fixed:
    for k, c in sc.items():
        structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed[k].append(c)
structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed.default_factory = None
centroids, \
instance_centroids_wrt_canonicalAtlasSpace_um, \
canonical_center_wrt_fixed_um, \
canonical_normal, \
transform_matrix_to_canonicalAtlasSpace_um = \
average_location(structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed)

# save centroid origins. divide by atlas resolution first
centroid_filepath = os.path.join(ATLAS_PATH, '1um_meanPositions.pkl')
centroids = {k: (v / atlas_resolution_um) for k,v in centroids.items()}
with open(centroid_filepath, 'wb') as f:
    pickle.dump(centroids, f)

# Note that all shapes have voxel resolution matching input resolution (10.0 micron).
for structure in tqdm(structures):
    # for structure in all_known_structures:
    # Load instance volumes.
    instance_volumes = []
    instance_source = []
    left_name = structure
    right_name = structure

    if str(structure).endswith('_L'):
        left_name = structure

    if str(structure).endswith('_R'):
        right_name = structure

    for brain_name in [fixed_brain_name] + moving_brain_names:
        brain_spec = {'name': brain_name, 'vol_type': 'annotationAsScore', 'resolution': resolution}
        right_instance_vol, _ = load_original_volume_v2(stack_spec=brain_spec,
                                                        structure=right_name,
                                                        return_origin_instead_of_bbox=True,
                                                        crop_to_minimal=True)
        instance_volumes.append(right_instance_vol)  # if right, do not mirror
        instance_source.append((brain_name, 'R'))

        left_instance_vol, _ = load_original_volume_v2(stack_spec=brain_spec,
                                                       structure=left_name,
                                                       return_origin_instead_of_bbox=True,
                                                       crop_to_minimal=True)
        instance_volumes.append(left_instance_vol[..., ::-1])  # if left, mirror
        instance_source.append((brain_name, 'L'))

    # Use the first instance as registration target.
    # Register every other instance to the first instance.
    template_instance_volume = instance_volumes[0]
    template_instance_centroid_wrt_templateOrigin = get_centroid_3d(template_instance_volume).astype(np.int16)
    template_instance_wrt_templateCentroid = (template_instance_volume, - template_instance_centroid_wrt_templateOrigin)
    aligned_moving_instance_wrt_templateCentroid_all_instances = []

    for i in range(1, len(instance_volumes)):
        # Compute transform.
        moving_instance_volume = instance_volumes[i]
        aligner = Aligner({0: template_instance_wrt_templateCentroid},
                          {0: (moving_instance_volume, np.array((0, 0, 0)))},
                          labelIndexMap_m2f={0: 0},
                          verbose=False)
        aligner.set_centroid(centroid_m='structure_centroid', centroid_f='structure_centroid')
        aligner.compute_gradient(smooth_first=True)
        lr = 1.
        ### max_iter_num was originally 100 and 1000
        _, _ = aligner.optimize(tf_type='rigid',
                                history_len=100,
                                max_iter_num=10 if structure in ['SC', 'IC'] else 100,
                                grad_computation_sample_number=None,
                                full_lr=np.array([lr, lr, lr, 0.1, 0.1, 0.1]),
                                terminate_thresh_trans=.01)

        # Transform instances.
        T = convert_transform_forms(aligner=aligner, out_form=(3, 4), select_best='max_value')
        aligned_moving_instance_volume, aligned_moving_instance_origin_wrt_templateCentroid = \
            transform_volume_v4(volume=(moving_instance_volume, (0, 0, 0)), transform=T,
                                return_origin_instead_of_bbox=True)
        aligned_moving_instance_wrt_templateCentroid = (
            aligned_moving_instance_volume, aligned_moving_instance_origin_wrt_templateCentroid)
        aligned_moving_instance_wrt_templateCentroid_all_instances.append(aligned_moving_instance_wrt_templateCentroid)

    # Generate meshes for each instance.
    volume_origin_list = [template_instance_wrt_templateCentroid] + aligned_moving_instance_wrt_templateCentroid_all_instances
    instance_mesh_wrt_templateCentroid_all_instances = [volume_to_polydata(volume, num_simplify_iter=3, smooth=True)
                                                        for volume, o in volume_origin_list]


    # Compute average shape.

    if structure == 'IC' or structure == 'SC':
        # IC and SC boundaries are particularly jagged, so do a larger value smoothing.
        sigma = 5.
    else:
        sigma = 2.

    mean_shape_wrt_templateCentroid = \
        average_shape(volume_origin_list=volume_origin_list, force_symmetric=(structure in singular_structures),
                      sigma=sigma,
                      )


    # Save mean shape. This is the important one
    filename = '{}.npy'.format(structure)
    filepath = os.path.join(ATLAS_PATH, 'structure', filename)
    np.save(filepath, np.ascontiguousarray(mean_shape_wrt_templateCentroid[0]))

    # save origin, this is also the important one
    filename = '{}.txt'.format(structure)
    filepath = os.path.join(ATLAS_PATH, 'origin', filename)
    np.savetxt(filepath, mean_shape_wrt_templateCentroid[1])


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
                           num_simplify_iter=3, smooth=False,
                           return_vertex_face_list=False)
    filepath = os.path.join(ATLAS_PATH, 'mesh', '{}.stl'.format(structure))
    save_mesh_stl(aligned_structure, filepath)

