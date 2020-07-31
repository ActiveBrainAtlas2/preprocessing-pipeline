# Add all annotated brains to the viewer
import numpy as np

from contour_utilities import get_contours_from_annotations, add_structure_to_neuroglancer
from utilities.imported_atlas_utilities import all_structures_total
from utilities.contour_utilities import stru
xy_ng_resolution_um = 5
color_radius = 3
stack = 'MD585'
# MD585: x_um = 35617,           y_um = 26086
# MD585: x_pixels_.46res = x_um*0.46,  y_pixels_.46res = y_um*0.46
# MD585: x_pixels_newres = x_pixels_.46res*(0.46/newres), y_pixels_newres = y_pixels_.46res*(0.46/newres)
# microns/resolution
y_voxels = 1 + int(26086 * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
x_voxels = 1 + int(35617 * 0.46 * (.46 / xy_ng_resolution_um) + 0.5)
full_brain_volume_annotated = np.zeros((268, y_voxels, x_voxels), dtype=np.uint8)

for target_str in all_structures_total:
    # for target_str in['VCA_L','7n_R','7n_L']:
    print(target_str)
    str_contours_annotation, first_sec, last_sec = get_contours_from_annotations(stack, target_str, densify=4)

    try:
        color = structure_to_color[target_str]
    except Exception as e:
        print(e)
        color = 4

    str_volume, xyz_str_offsets = add_structure_to_neuroglancer( \
        viewer, str_contours_annotation, target_str, stack, first_sec, last_sec, \
        color_radius=color_radius, xy_ng_resolution_um=xy_ng_resolution_um, threshold=1, color=color, \
        solid_volume=False, no_offset_big_volume=True, save_results=True, \
        return_with_offsets=True, add_to_ng=False, human_annotation=True)

    z_len, y_len, x_len = np.shape(str_volume)
    #     full_brain_volume_annotated[0:z_len, 0:y_len, 0:x_len] = str_volume.copy()
    for z in range(xyz_str_offsets[2], z_len):
        for y in range(xyz_str_offsets[1], y_len):
            for x in range(xyz_str_offsets[0], x_len):
                structure_val = str_volume[z, y, x]
                if structure_val == 0:
                    continue
                else:
                    try:
                        full_brain_volume_annotated[z, y, x] = structure_val
                    except Exception as e:
                        print(e)
