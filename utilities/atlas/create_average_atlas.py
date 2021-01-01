"""
Takes the volume and origin data from here:
/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/MDXXX/10.0um_annotationAsScoreVolume/
for each brain and then aligns it into a new averaged set of arrays, origins and messhes (stl files) here:
/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasVXXX/

"""

import os, sys
from collections import defaultdict
import numpy as np
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)

atlas_name = 'atlasV8'
surface_level = 0.9
from utilities.sqlcontroller import SqlController
from utilities.file_location import DATA_PATH
from utilities.atlas.imported_atlas_utilities import volume_to_polydata, save_mesh_stl, \
    load_original_volume_v2, get_centroid_3d, convert_transform_forms, transform_volume_v4, average_shape, \
    load_alignment_results_v3, transform_points, average_location, mirror_volume_v2, load_all_structures_and_origins, \
    load_mean_shape
from utilities.atlas.atlas_aligner import Aligner

ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
fixed_brain_name = 'MD589'
sqlController = SqlController(fixed_brain_name)
structures = sqlController.get_structures_list()
structures.remove('R')
singular_structures = [s for s in structures if '_L' not in s and '_R' not in s]

atlas_resolution = '10.0um'
atlas_resolution_um = 10.0
moving_brain_names = ['MD585', 'MD594']
fixed_brain_spec = {'name': fixed_brain_name, 'vol_type': 'annotationAsScore', 'resolution': atlas_resolution}

moving_brains_structure_centroids = []

# This loops through the 2 moving brains, loads all the hand annotation structures and origins
for animal in tqdm(moving_brain_names):
    animal_spec = {'name': animal, 'vol_type': 'annotationAsScore', 'resolution': atlas_resolution}
    moving_brain = load_all_structures_and_origins(stack_spec=animal_spec,
                                                                structures=structures, in_bbox_wrt='wholebrain')

    alignment_spec = dict(stack_m=animal_spec, stack_f=fixed_brain_spec, warp_setting=109)
    structure_centroids = get_centroid_3d(moving_brain)
    # Load registration.
    # Alignment results fp: os.path.join(reg_root_dir, alignment_spec['stack_m']['name'], warp_basename, warp_basename + '_' + what + '.' + ext)
    moving_brain_to_fixed_brain_transforms = load_alignment_results_v3(alignment_spec=alignment_spec, what='parameters')
    # Transform moving brains into alignment with the fixed brain.

    moving_brain_structure_centroids_aligned_wrt_fixed = \
    dict(list(zip(list(structure_centroids.keys()),
                  transform_points(pts=list(structure_centroids.values()),
                                   transform=moving_brain_to_fixed_brain_transforms))))

    moving_brain_structure_centroids_um_wrt_fixed = \
        {s: c * atlas_resolution_um for s, c in
        list(moving_brain_structure_centroids_aligned_wrt_fixed.items())}

    moving_brains_structure_centroids.append(moving_brain_structure_centroids_um_wrt_fixed)


average_structure_centroids = defaultdict(list)
for animal in moving_brains_structure_centroids:
    for structure, centroid in animal.items():
        average_structure_centroids[structure].append(centroid)

average_structure_centroids.default_factory = None

nominal_centroids, \
centroids_wrt_canonicalAtlasSpace, \
canonical_center_wrt_fixed, \
canonical_normal, \
transform_matrix_to_canonicalAtlasSpace_um = average_location(average_structure_centroids)



for structure in tqdm(structures):
    # for structure in all_known_structures:
    # Load instance volumes.
    instance_volumes = []
    instance_source = []

    for brain_name in [fixed_brain_name] + moving_brain_names:
        brain_spec = {'name': brain_name, 'vol_type': 'annotationAsScore', 'resolution': atlas_resolution}

        if '_L' in structure:
            left_instance_vol, _ = load_original_volume_v2(stack_spec=brain_spec,
                                                           structure=structure,
                                                           return_origin_instead_of_bbox=True,
                                                           crop_to_minimal=True)
            instance_volumes.append(left_instance_vol[..., ::-1])  # if left, mirror
            instance_source.append((brain_name, 'L'))

        else:
            right_instance_vol, _ = load_original_volume_v2(stack_spec=brain_spec,
                                                            structure=structure,
                                                            return_origin_instead_of_bbox=True,
                                                            crop_to_minimal=True)
            instance_volumes.append(right_instance_vol)  # if right, do not mirror
            instance_source.append((brain_name, 'R'))

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
                                max_iter_num=100 if structure in ['SC', 'IC'] else 500,
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
    volume_origin_list = [
                             template_instance_wrt_templateCentroid] + aligned_moving_instance_wrt_templateCentroid_all_instances
    instance_mesh_wrt_templateCentroid_all_instances = [volume_to_polydata(volume, num_simplify_iter=3, smooth=True)
                                                        for volume, o in volume_origin_list]

    if structure == 'IC' or structure == 'SC':
        # IC and SC boundaries are particularly jagged, so do a larger value smoothing.
        sigma = 5.
    else:
        sigma = 2.

    mean_shape_wrt_templateCentroid = \
        average_shape(volume_origin_list=volume_origin_list, force_symmetric=(structure in singular_structures),
                      sigma=sigma,
                      )

    wall_level = .5
    surround_distance_um = 200.

    # Save mean shape.
    volume_filename = f'{structure}.npy'
    volume_filepath = os.path.join(ATLAS_PATH, 'structure', volume_filename)
    np.save(volume_filepath, np.ascontiguousarray(mean_shape_wrt_templateCentroid[0]))

    origin_filename = f'{structure}.txt'
    origin_filepath = os.path.join(ATLAS_PATH, 'origin', origin_filename)
    np.savetxt(origin_filepath, mean_shape_wrt_templateCentroid[1])

##### Combine standard shapes with standard centroid locations
nominal_centroids_10um = {s: c / atlas_resolution_um for s, c in nominal_centroids.items()}

for structure in tqdm(structures):

    origin_filename = f'{structure}.txt'
    origin_filepath = os.path.join(ATLAS_PATH, 'origin', origin_filename)
    origin = np.loadtxt(origin_filepath)

    volume_filename = f'{structure}.npy'
    volume_filepath = os.path.join(ATLAS_PATH, 'structure', volume_filename)
    volume = np.load(volume_filepath)

    if '_L' in structure:
        aligned_tuple = mirror_volume_v2(volume=volume, centroid_wrt_origin=-origin, new_centroid=nominal_centroids_10um[structure])
    else:
        aligned_tuple = (volume, origin + nominal_centroids_10um[structure])

    aligned_volume = aligned_tuple[0]
    aligned_origin = aligned_tuple[1]

    # write over origin
    np.savetxt(origin_filepath, aligned_origin)

    # write over numpy volume
    np.save(volume_filepath, aligned_volume)

    # mesh
    surface_level_aligned_volume = (aligned_volume >= surface_level, aligned_origin)
    aligned_mesh = volume_to_polydata(volume=surface_level_aligned_volume,
                                           num_simplify_iter=3, smooth=False,
                                           return_vertex_face_list=False)
    mesh_filepath = os.path.join(ATLAS_PATH, 'mesh', f'{structure}.stl')
    save_mesh_stl(aligned_mesh, mesh_filepath)
