import os
import sys
import neuroglancer

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.contour_utilities import image_contour_generator, add_structure_to_neuroglancer

stack = 'MD589'
detector_id = 19
structure = '3N_R'
str_contour, first_sec, last_sec = image_contour_generator(stack, detector_id, structure, use_local_alignment=True,
                                                           image_prep=2, threshold=0.2)
print(str_contour, first_sec, last_sec)

neuroglancer.set_server_bind_address('0.0.0.0')
viewer = neuroglancer.Viewer()
viewer  # port 41989, IP 132.239.73.85

# Sets 'Image' layer to be prep2 images from S3 of <stack>
with viewer.txn() as s:
    s.layers['image'] = neuroglancer.ImageLayer(
        source='precomputed://https://mousebrainatlas-datajoint-jp2k.s3.amazonaws.com/precomputed/' + stack + '_fullres')
    s.layout = 'xy'  # '3d'/'4panel'/'xy'
print(viewer)

ng_structure_volume_normal = add_structure_to_neuroglancer(viewer, str_contour, structure, stack, first_sec, last_sec, \
                                                           color_radius=5, xy_ng_resolution_um=10, threshold=0.2,
                                                           color=5, \
                                                           solid_volume=False, no_offset_big_volume=False,
                                                           save_results=False, \
                                                           return_with_offsets=False, add_to_ng=True,
                                                           human_annotation=False)
