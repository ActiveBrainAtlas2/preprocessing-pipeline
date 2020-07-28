import os,sys
from collections import defaultdict
import json
import numpy as np
import pickle
HOME = os.path.expanduser("~")

PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.imported_atlas_utilities import load_original_volume_all_known_structures_v3, get_centroid_3d, \
    load_alignment_results_v3, transform_points, average_location, \
    convert_to_original_name, name_unsided_to_color, paired_structures, \
    convert_to_left_name, convert_to_right_name, load_original_volume_v2, save_alignment_results_v3, \
    convert_transform_forms, transform_volume_v4, volume_to_polydata, singular_structures, get_surround_volume, \
    MESH_DIR, average_shape, convert_to_surround_name, \
    save_mesh_stl
from utilities.aligner_v3 import Aligner


INPUT_KEY_LOC = os.path.join(PATH, 'neuroglancer', 'structure_key_minimal.json')
NUM_STRUCTS = 49
with open(INPUT_KEY_LOC, 'r') as f:
    structures = json.load(f)
structures = list(structures.values())
structures = structures[0:4]
structures  = ['12N']

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
    print('Brain', moving_brain_spec)
    moving_brain = load_original_volume_all_known_structures_v3(stack_spec=moving_brain_spec, structures=structures)
    alignment_spec = dict(stack_m=moving_brain_spec, stack_f=fixed_brain_spec, warp_setting=109)
    moving_brain_structure_centroids_input_resol = get_centroid_3d(moving_brain)
    # Load registration.
    # Alignment results fp: os.path.join(reg_root_dir, alignment_spec['stack_m']['name'], warp_basename, warp_basename + '_' + what + '.' + ext)
    transform_parameters_moving_brain_to_fixed_brain = load_alignment_results_v3(alignment_spec=alignment_spec, what='parameters')
    # Transform moving brains into alignment with the fixed brain.
    transformed_moving_brain_structure_centroids_input_resol_wrt_fixed = \
        dict(zip(moving_brain_structure_centroids_input_resol.keys(),
                 transform_points(pts=moving_brain_structure_centroids_input_resol.values(),
                                  transform=transform_parameters_moving_brain_to_fixed_brain)))

    transformed_moving_brain_structure_centroids_um_wrt_fixed = \
        {s: c * resolution_um for s, c in
         transformed_moving_brain_structure_centroids_input_resol_wrt_fixed.items()}

    structure_centroids_all_brains_um_wrt_fixed.append(transformed_moving_brain_structure_centroids_um_wrt_fixed)

structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed = defaultdict(list)
for sc in structure_centroids_all_brains_um_wrt_fixed:
    for k, c in sc.items():
        structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed[k].append(c)
structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed.default_factory = None

# compute standard centroids

nominal_centroids_wrt_canonicalAtlasSpace_um, \
instance_centroids_wrt_canonicalAtlasSpace_um, \
canonical_center_wrt_fixed_um, \
canonical_normal, \
transform_matrix_to_canonicalAtlasSpace_um = \
average_location(structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed)


colors = {name_s: np.array(name_unsided_to_color[convert_to_original_name(name_s)])/255.
                                        for name_s in instance_centroids_wrt_canonicalAtlasSpace_um.keys()}


filepath = os.path.join(MESH_DIR, 'atlasV7', '1um_meanPositions.pkl')
with open(filepath, 'wb') as f:
    pickle.dump(nominal_centroids_wrt_canonicalAtlasSpace_um, f)

filepath = os.path.join(MESH_DIR, 'atlasV7', 'canonicalCentroid_wrt_fixedWholebrain.txt')
np.savetxt(filepath, canonical_center_wrt_fixed_um)

# Note that all shapes have voxel resolution matching input resolution (10.0 micron).
for structure in ['12N']:
    # for structure in all_known_structures:
    # Load instance volumes.
    instance_volumes = []
    instance_source = []

    if structure in paired_structures:
        left_name = convert_to_left_name(structure)
        right_name = convert_to_right_name(structure)
    else:
        left_name = structure
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
        print('Registering {} instance {} to instance 0'.format(structure, i))
        # Compute transform.
        moving_instance_volume = instance_volumes[i]
        aligner = Aligner({0: template_instance_wrt_templateCentroid},
                          {0: (moving_instance_volume, np.array((0,0,0)))},
                          labelIndexMap_m2f={0:0},
                         verbose=False)
        aligner.set_centroid(centroid_m='structure_centroid', centroid_f='structure_centroid')
        aligner.compute_gradient(smooth_first=True)
        lr = 1.
        ### max_iter_num was originally 100 and 1000
        print('Entering aligner optimzer')
        _, _ = aligner.optimize(tf_type='rigid',
                                history_len=100,
                                max_iter_num=2 if structure in ['SC', 'IC'] else 3,
                                grad_computation_sample_number=None,
                                full_lr=np.array([lr, lr, lr, 0.1, 0.1, 0.1]),
                                terminate_thresh_trans=.01)



        reg_root_dir=os.path.join(MESH_DIR, atlas_name, 'mean_shapes', 'instance_registration')
        save_alignment_results_v3(aligner=aligner,
                              select_best='max_value',
                              alignment_spec=dict(warp_setting=108,
                                                  stack_f=dict(name='%s_instance0' % structure, vol_type='annotationAsScore'),
                                                  stack_m=dict(name='%s_instance%d' % (structure, i),
                                                               vol_type='annotationAsScore')),
                              reg_root_dir=reg_root_dir)

        # Transform instances.
        T = convert_transform_forms(aligner=aligner, out_form=(3, 4), select_best='max_value')
        aligned_moving_instance_volume, aligned_moving_instance_origin_wrt_templateCentroid = \
            transform_volume_v4(volume=(moving_instance_volume, (0, 0, 0)), transform=T,
                                return_origin_instead_of_bbox=True)
        aligned_moving_instance_wrt_templateCentroid = (
        aligned_moving_instance_volume, aligned_moving_instance_origin_wrt_templateCentroid)
        aligned_moving_instance_wrt_templateCentroid_all_instances.append(aligned_moving_instance_wrt_templateCentroid)

    # Generate meshes for each instance.
    instance_mesh_wrt_templateCentroid_all_instances = [
        volume_to_polydata(v, origin=o, num_simplify_iter=3, smooth=True)
        for v, o in
        [template_instance_wrt_templateCentroid] + aligned_moving_instance_wrt_templateCentroid_all_instances]

    # Save meshes.
    for i, mesh_data in enumerate(instance_mesh_wrt_templateCentroid_all_instances):
        meshfile = '{}_{}_{}.stl'.format(resolution, structure, str(i))
        meshpath = os.path.join(MESH_DIR, atlas_name, 'aligned_instance_meshes', meshfile)
        print('Save stl at {}'.format( meshpath))
        save_mesh_stl(mesh_data, meshpath)

    filename = '{}_sources.pkl'.format(structure)
    filepath = os.path.join(MESH_DIR, atlas_name, 'instance_sources', filename)
    with open(filepath, 'wb') as f:
        pickle.dump(instance_source, f)

    # Compute average shape.

    if structure == 'IC' or structure == 'SC':
        # IC and SC boundaries are particularly jagged, so do a larger value smoothing.
        sigma = 5.
    else:
        sigma = 2.

    mean_shape_wrt_templateCentroid = \
        average_shape(volume_origin_list=[template_instance_wrt_templateCentroid] + \
                                         aligned_moving_instance_wrt_templateCentroid_all_instances,
                      force_symmetric=(structure in singular_structures),
                      sigma=sigma,
                      )

    for surface_level in np.arange(0.1, 1.1, .1):
        print("level =", surface_level, ', volume =',
              np.count_nonzero(mean_shape_wrt_templateCentroid[0] > surface_level) * resolution_um ** 3 / 1e9, "mm^3")

    # Generate meshes for mean shape.
    mean_shape_isosurface_polydata_all_levels = {surface_level:
                                                     volume_to_polydata(
                                                         mean_shape_wrt_templateCentroid[0] >= surface_level,
                                                         origin=mean_shape_wrt_templateCentroid[1],
                                                         num_simplify_iter=3, smooth=True,
                                                         return_mesh=False)
        for surface_level in np.arange(0.1, 1.1, .1)}

    # Identify the surrouding area as additional structure.

    wall_level = .5
    surround_distance_um = 200.

    # changed to v2 to v3 Jul/27/2020 renamed without the _vX
    # volume, distance=5, wall_level=0, prob=False, return_origin_instead_of_bbox=True, padding=5
    # def get_surround_volume(volume, origin, distance=5, wall_level=0, prob=False, return_origin_instead_of_bbox=True,
    #                        padding=5):
    surround_wrt_stdShapeCentroid = \
        get_surround_volume(volume=mean_shape_wrt_templateCentroid[0],
                               origin=mean_shape_wrt_templateCentroid[1],
                               distance=surround_distance_um / resolution_um,
                               wall_level=wall_level,
                               prob=True,
                               return_origin_instead_of_bbox=True,
                               padding=5)

    # Generate meshes for surrouding area.
    surround_isosurface_polydata_all_levels = {surface_level:
             volume_to_polydata(surround_wrt_stdShapeCentroid[0] >= surface_level,
                                origin=surround_wrt_stdShapeCentroid[1],
                                num_simplify_iter=3, smooth=True,
                                return_mesh=False)
         for surface_level in np.arange(0.1, 1.1, .1)}

    # Save mean shape.
    filename = '{}_{}_volume.npy'.format(resolution, structure)
    filepath =  os.path.join(MESH_DIR, atlas_name, 'mean_shapes', filename)
    print('Saving numpy array at', filepath)
    np.save(filepath, np.ascontiguousarray(mean_shape_wrt_templateCentroid[0]))

    filename = '{}_{}_origin_wrt_meanShapeCentroid.txt'.format(resolution, structure)
    filepath = os.path.join(MESH_DIR, atlas_name, 'mean_shapes', filename)
    print('Saving numpy text at', filepath)
    np.savetxt(filepath, mean_shape_wrt_templateCentroid[1])


    for level in np.arange(0.1, 1.1, .1):
        filename = '{}_{}_mesh_level_{}.stl'.format(resolution, structure, str(level))
        filepath = os.path.join(MESH_DIR, atlas_name, 'mean_shapes', filename)
        print('Saving mesh at', filepath)
        save_mesh_stl(mean_shape_isosurface_polydata_all_levels[level], filepath)

    surround_name = convert_to_surround_name(structure, margin=str(int(surround_distance_um)) + 'um')
    filename = '{}_{}_volume.npy'.format(resolution, surround_name)
    filepath = os.path.join(MESH_DIR, atlas_name, 'mean_shapes', filename)
    print('Saving numpy array at', filepath)
    np.save(filepath, np.ascontiguousarray(surround_wrt_stdShapeCentroid[0]))


    filename = '{}_{}_origin_wrt_meanShapeCentroid.txt'.format(resolution, surround_name)
    filepath = os.path.join(MESH_DIR, atlas_name, 'mean_shapes', filename)
    print('Saving numpy text at', filepath)
    np.savetxt(filepath, surround_wrt_stdShapeCentroid[1])

    for level in np.arange(0.1, 1.1, .1):
        filename = '{}_{}_{}.stl'.format(resolution, surround_name, str(level))
        filepath = os.path.join(MESH_DIR, atlas_name, 'mean_shapes', filename)
        print('Saving mesh at', filepath)
        save_mesh_stl(surround_isosurface_polydata_all_levels[level], filepath)
