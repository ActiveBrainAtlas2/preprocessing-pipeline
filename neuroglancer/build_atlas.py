import sys
from collections import defaultdict
import json



PATH = '/home/eddyod/programming/pipeline_utility'
sys.path.append(PATH)
from utilities.imported_atlas_utilities import load_original_volume_all_known_structures_v3, get_centroid_3d, \
    load_alignment_results_v3, transform_points, average_location, convert_to_left_name, convert_to_right_name, \
    paired_structures, load_original_volume_v2

INPUT_KEY_LOC = 'structure_key_minimal.json'
NUM_STRUCTS = 49
with open(INPUT_KEY_LOC, 'r') as f:
    structures = json.load(f)

structures = list(structures.values())
structures = structures[0:1]
print(structures)
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


nominal_centroids_wrt_canonicalAtlasSpace_um, \
instance_centroids_wrt_canonicalAtlasSpace_um, \
canonical_center_wrt_fixed_um, \
canonical_normal, \
transform_matrix_to_canonicalAtlasSpace_um = \
average_location(structure_centroids_all_brains_um_grouped_by_structure_wrt_fixed)

for name_u in ['SNR']:
    # for name_u in all_known_structures:
    # Load instance volumes.

    instance_volumes = []
    instance_source = []

    if name_u in paired_structures:
        left_name = convert_to_left_name(name_u)
        right_name = convert_to_right_name(name_u)
    else:
        left_name = name_u
        right_name = name_u

    for brain_name in [fixed_brain_name] + moving_brain_names:

        brain_spec = {'name': brain_name, 'vol_type': 'annotationAsScore', 'resolution': resolution}
        print('Brain', brain_spec)

        try:
            right_instance_vol, _ = load_original_volume_v2(stack_spec=brain_spec,
                                                                        structure=right_name,
                                                                        return_origin_instead_of_bbox=True,
                                                                        crop_to_minimal=True)
            instance_volumes.append(right_instance_vol)  # if right, do not mirror
            instance_source.append((brain_name, 'R'))
        except Exception as e:
            continue

        try:
            left_instance_vol, _ = load_original_volume_v2(stack_spec=brain_spec,
                                                                       structure=left_name,
                                                                       return_origin_instead_of_bbox=True,
                                                                       crop_to_minimal=True)
            instance_volumes.append(left_instance_vol[..., ::-1])  # if left, mirror
            instance_source.append((brain_name, 'L'))
        except:
            continue


    template_instance_volume = instance_volumes[0]
    template_instance_centroid_wrt_templateOrigin = get_centroid_3d(template_instance_volume).astype(np.int16)
    template_instance_wrt_templateCentroid = (template_instance_volume, - template_instance_centroid_wrt_templateOrigin)

    aligned_moving_instance_wrt_templateCentroid_all_instances = []
