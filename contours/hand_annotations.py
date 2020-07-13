import os, sys
import pandas as pd
import neuroglancer
import numpy as np
import ast

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.contour_utilities import get_contours_from_annotations, add_structure_to_neuroglancer

stack = 'MD589'
target_str = '3N'
neuroglancer.set_server_bind_address('0.0.0.0')
viewer = neuroglancer.Viewer()
print(viewer)



#filepath = os.path.join('/home/eddyod/MouseBrainSlicer_data/MD589', 'Annotation.npy')
csvfile = os.path.join(os.getcwd(), 'MD589_annotation_contours.csv')
hand_annotations = pd.read_csv(csvfile)
#v1 = hand_annotations.iloc[:,16].values
#hand_annotations = hand_annotations.replace(r' ',',', regex=True)
#hand_annotations['vertices'] = hand_annotations['vertices'].apply(ast.literal_eval)
#hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: list(x))
#column_values = hand_annotations[["side"]].values.ravel()
#unique_values = pd. unique(column_values)
#unique_values = hand_annotations.groupby(['name', 'side']).size()
#print(unique_values)
#print(type(v1[0]))


#annotation = np.load(filepath, allow_pickle = True, encoding='latin1')
#contours = pd.DataFrame(annotation)
#hand_annotations = contours.rename(columns={0:"name", 1:"section", 2:"vertices"})
unique_values = hand_annotations.groupby(['name']).size()
print(hand_annotations.head(10))
#sys.exit()
str_contours_annotation, first_sec, last_sec = get_contours_from_annotations(stack, target_str, hand_annotations, densify=0)
color = 2
ng_structure_volume = add_structure_to_neuroglancer( viewer, str_contours_annotation, target_str, stack, first_sec, last_sec, \
                                                    color_radius=2, xy_ng_resolution_um=5, threshold=1, color=color, \
                                                    solid_volume=False, no_offset_big_volume=True, save_results=False, \
                                                    return_with_offsets=False, add_to_ng=True, human_annotation=True )

print('ng_structure_volume shape', ng_structure_volume.shape)
print('ng_structure_volume max', np.amax(ng_structure_volume))
