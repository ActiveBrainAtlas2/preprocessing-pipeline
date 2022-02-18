"""
This is a rewritten script from Yuncong
Takes the volume and origin data from here:
/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes/MDXXX/10.0um_annotationAsScoreVolume/
for each brain and then aligns it into a new averaged set of arrays, origins
and messhes (stl files) here:
/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasVXXX/

"""
import os
import sys
from collections import defaultdict
import numpy as np
from tqdm import tqdm
import pickle
from pathlib import Path

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

surface_level = 0.9
from lib.SqlController import SqlController
from lib.FileLocationManager import DATA_PATH
from lib.utilities_atlas import load_original_volume_all_known_structures_v3, get_centroid_3d, \
    load_alignment_results_v3, transform_points, average_location, \
    load_original_volume_v2, \
    convert_transform_forms, volume_to_polydata, singular_structures, \
    average_shape, mirror_volume_v2, \
    save_mesh_stl, transform_volume_v4, \
    load_mean_shape
from lib.atlas_aligner import Aligner

fixed_brain_name = 'MD589'
sqlController = SqlController(fixed_brain_name)
structures = sqlController.get_structures_list()
structures = ['SC']

moving_brain_names = ['MD585', 'MD594']
resolution = '10.0um'
resolution_um = 10.0
structure_centroids_all_brains_um_wrt_fixed = []
fixed_brain_spec = {'name': fixed_brain_name, 'vol_type': 'annotationAsScore', 'resolution': resolution}

fixed_brain = load_original_volume_all_known_structures_v3(stack_spec=fixed_brain_spec, structures=structures, 
                                                           in_bbox_wrt='wholebrain')
fixed_brain_structure_centroids = get_centroid_3d(fixed_brain)
fixed_brain_structure_centroids_um = {s: c * resolution_um for s, c in fixed_brain_structure_centroids.items()}
structure_centroids_all_brains_um_wrt_fixed.append(fixed_brain_structure_centroids_um)
atlas_name = 'atlasV8'
ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)

# Compute intance centroids
for brain_m in moving_brain_names:
    moving_brain_spec = {'name': brain_m, 'vol_type': 'annotationAsScore', 'resolution': resolution}
    print('Brain', moving_brain_spec)
    moving_brain = load_original_volume_all_known_structures_v3(stack_spec=moving_brain_spec, structures=structures, in_bbox_wrt='wholebrain')
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
        {s: c * resolution_um for s, c in
        list(transformed_moving_brain_structure_centroids_input_resol_wrt_fixed.items())}

    structure_centroids_all_brains_um_wrt_fixed.append(transformed_moving_brain_structure_centroids_um_wrt_fixed)

structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed = defaultdict(list)
for sc in structure_centroids_all_brains_um_wrt_fixed:
    for k, c in sc.items():
        structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed[k].append(c)
structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed.default_factory = None

nominal_centroids, \
instance_centroids_wrt_canonicalAtlasSpace_um, \
canonical_center_wrt_fixed_um, \
canonical_normal, \
transform_matrix_to_canonicalAtlasSpace_um = \
average_location(structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed)

filepath = os.path.join(ATLAS_PATH, '1um_meanPositions.pkl')
with open(filepath, 'wb') as f:
    pickle.dump(nominal_centroids, f)
    
# Note that all shapes have voxel resolution matching input resolution (10.0 micron).
for structure in structures:
    # for structure in all_known_structures:
    # Load instance volumes.
    instance_volumes = []
    instance_source = []

    for brain_name in [fixed_brain_name] + moving_brain_names:
        brain_spec = {'name': brain_name, 'vol_type': 'annotationAsScore', 'resolution': resolution}
       
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
                          {0: (moving_instance_volume, np.array((0,0,0)))},
                          labelIndexMap_m2f={0:0},
                         verbose=False)
        aligner.set_centroid(centroid_m='structure_centroid', centroid_f='structure_centroid')
        aligner.compute_gradient(smooth_first=True)
        lr = 1.
        ### max_iter_num was originally 100 and 1000
        iters = 100
        _, _ = aligner.optimize(tf_type='rigid',
                                history_len=100,
                                max_iter_num=100 if structure in ['SC', 'IC'] else 100,
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
    filename = f'{structure}.npy'
    filepath =  os.path.join(ATLAS_PATH, 'structure', filename)
    np.save(filepath, np.ascontiguousarray(mean_shape_wrt_templateCentroid[0]))

    filename = f'{structure}.txt'
    filepath = os.path.join(ATLAS_PATH, 'origin', filename)
    np.savetxt(filepath, mean_shape_wrt_templateCentroid[1])
    
 #####   Combine standard shapes with standard centroid locations
atlas_resolution = '10.0um'
atlas_resolution_um = 10.0
filepath = os.path.join(ATLAS_PATH, '1um_meanPositions.pkl')
nominal_centroids = pickle.load( open(filepath, "rb" ) )
nominal_centroids_10um = {s: c / atlas_resolution_um for s, c in nominal_centroids.items()}
mean_shapes = {name_u: load_mean_shape(atlas_name=atlas_name, structure=name_u, resolution=atlas_resolution) 
                    for name_u in structures}

print()
print('mirror and add centroid')
for structure in structures:

    if '_L' in structure:
        mean_shape = mirror_volume_v2(volume=mean_shapes[structure], 
                                      centroid_wrt_origin=-mean_shapes[structure][1],
                                      new_centroid=nominal_centroids_10um[structure])
    else:
        mean_shape = (mean_shapes[structure][0], mean_shapes[structure][1] + nominal_centroids_10um[structure])
    print(structure, mean_shapes[structure][1], nominal_centroids_10um[structure])
    
    volume = mean_shape[0]
    #volume = np.rot90(volume, axes=(0, 1))
    #volume = np.flip(volume, axis=0)

    #volume[volume >= threshold] = color
    #volume = volume.astype(np.uint8)

    #volume[volume >= threshold] = 100
    #volume[volume < threshold] = 0
    #volume = volume.astype(np.uint8)
    #volume = np.swapaxes(volume, 0, 2)
    #volume = np.rot90(volume, axes=(1, 2))
    #volume = np.flip(volume, axis=1)

    origin = mean_shape[1]
    # save origin, this is also the important one
    filename = f'{structure}.txt'
    filepath = os.path.join(ATLAS_PATH, 'origin', filename)
    np.savetxt(filepath, origin)
    # Save volume with stated level. This is the important one
    filename = f'{structure}.npy'
    filepath = os.path.join(ATLAS_PATH, 'structure', filename)
    np.save(filepath, volume)
    # mesh
    aligned_volume = (mean_shape[0] >= 0.8, origin)
    aligned_structure = volume_to_polydata(volume=aligned_volume,
                           num_simplify_iter=3, smooth=False,
                           return_vertex_face_list=False)
    filepath = os.path.join(ATLAS_PATH, 'mesh', f'{structure}.stl')
    save_mesh_stl(aligned_structure, filepath)
 
  

