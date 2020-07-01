import os
import sys
import neuroglancer
import json
import numpy as np

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.contour_utilities import image_contour_generator, add_structure_to_neuroglancer

stack = 'MD589'
detector_id = 19
"""
structure = '3N_R'
str_contour, first_sec, last_sec = image_contour_generator(stack, detector_id, structure, use_local_alignment=True,
                                                           image_prep=2, threshold=0.2)
print(str_contour, first_sec, last_sec)


ng_structure_volume_normal = add_structure_to_neuroglancer(viewer, str_contour, structure, stack, first_sec, last_sec, \
                                                           color_radius=5, xy_ng_resolution_um=10, threshold=0.2,
                                                           color=5, \
                                                           solid_volume=False, no_offset_big_volume=False,
                                                           save_results=False, \
                                                           return_with_offsets=False, add_to_ng=True,
                                                           human_annotation=False)
"""
neuroglancer.set_server_bind_address('0.0.0.0')
viewer = neuroglancer.Viewer()

# Sets 'Image' layer to be prep2 images from S3 of <stack>
with viewer.txn() as s:
    s.layers['image'] = neuroglancer.ImageLayer(
        source='precomputed://https://mousebrainatlas-datajoint-jp2k.s3.amazonaws.com/precomputed/' + stack + '_fullres')
    s.layout = 'xy'  # '3d'/'4panel'/'xy'
print(viewer)

# CREATE ENTIRE BRAIN VOLUME
xy_ng_resolution_um = 5

with open('/home/eddyod/programming/pipeline_utility/contours/json_cache/struct_reverse.json', 'r') as json_file:
    all_structures_total = json.load(json_file)

with open('/home/eddyod/programming/pipeline_utility/contours/json_cache/struct_reverse_2.json', 'r') as json_file:
    structure_to_color = json.load(json_file)

# MD585: x_um = 35617,           y_um = 26086
# MD585: x_pixels_.46res = x_um*0.46,  y_pixels_.46res = y_um*0.46
# MD585: x_pixels_newres = x_pixels_.46res*(0.46/newres), y_pixels_newres = y_pixels_.46res*(0.46/newres)
# microns/resolution
y_voxels = int(26086 * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
x_voxels = int(35617 * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
full_brain_volumes = np.zeros((268, y_voxels, x_voxels), dtype=np.uint8)

for structure in all_structures_total:
    str_contour, first_sec, last_sec = image_contour_generator(stack, detector_id, structure, use_local_alignment=True,
                                                               image_prep=2, threshold=0.5)

    try:
        color = structure_to_color[structure]
    except:
        color = 2
    print(structure, first_sec, last_sec)
    continue
    str_volume, xyz_offsets = add_structure_to_neuroglancer(viewer, str_contour, structure, stack, first_sec, last_sec,
                                                            color_radius=5, xy_ng_resolution_um=xy_ng_resolution_um,
                                                            threshold=0.5, color=color,
                                                            solid_volume=False, no_offset_big_volume=True,
                                                            save_results=False, return_with_offsets=True,
                                                            add_to_ng=False, human_annotation=False)

    z_len, y_len, x_len = np.shape(str_volume)
    full_brain_volumes[0:z_len, 0:y_len, 0:x_len] += str_volume
