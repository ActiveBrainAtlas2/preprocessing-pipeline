import os, sys
import pandas as pd
import neuroglancer
import numpy as np
import ast

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.contour_utilities import get_contours_from_annotations, add_structure_to_neuroglancer

stack = 'MD589'
target_str = '3N_R'
neuroglancer.set_server_bind_address('0.0.0.0')
viewer = neuroglancer.Viewer()
print(viewer)



filepath = os.path.join(os.getcwd(), 'MD589_annotation_contours.csv')

hand_annotations = pd.read_csv(filepath)
v1 = hand_annotations.iloc[:,16].values
hand_annotations = hand_annotations.replace(r' ',',', regex=True)
hand_annotations['vertices'] = hand_annotations['vertices'].apply(ast.literal_eval)
#hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: list(x))
print(hand_annotations.dtypes)

print(type(v1[0]))

str_contours_annotation, first_sec, last_sec = get_contours_from_annotations(stack, target_str, hand_annotations, densify=0)
print('type fo str contors', type(str_contours_annotation))
#print(str_contours_annotation, first_sec, last_sec)
color = 2
ng_structure_volume = add_structure_to_neuroglancer( viewer, str_contours_annotation, target_str, stack, first_sec, last_sec, \
                                                    color_radius=2, xy_ng_resolution_um=5, threshold=1, color=color, \
                                                    solid_volume=False, no_offset_big_volume=True, save_results=False, \
                                                    return_with_offsets=False, add_to_ng=True, human_annotation=True )

