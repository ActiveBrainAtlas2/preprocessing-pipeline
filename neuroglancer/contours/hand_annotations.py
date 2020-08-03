import os, sys
import pandas as pd
import neuroglancer
import numpy as np
import ast
DIR = '/home/eddyod/programming/pipeline_utility'
sys.path.append(DIR)
from utilities.contour_utilities import get_contours_from_annotations, add_structure_to_neuroglancer

animal = 'MD589'
target_structure = '3N'


#filepath = os.path.join('/home/eddyod/MouseBrainSlicer_data/MD589', 'Annotation.npy')
#csvfile = os.path.join(os.getcwd(), 'MD589_annotation_contours.csv')
#csvfile = os.path.join(os.getcwd(), 'junk.csv')
#hand_annotations = pd.read_csv(csvfile)
#cols = ['section','name', 'side', 'vertices']
#hand_annotations = hand_annotations[cols]
"""
hand_annotations['vertices'] = hand_annotations['vertices'] \
    .apply(lambda x: x.replace(' ', ','))\
    .apply(lambda x: x.replace('\n',','))\
    .apply(lambda x: x.replace(',]',']'))\
    .apply(lambda x: x.replace(',,', ','))\
    .apply(lambda x: x.replace(',,', ','))\
    .apply(lambda x: x.replace(',,', ',')).apply(lambda x: x.replace(',,', ','))
hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))

hand_annotations.to_csv('hand_annotations.csv')
"""
csvfile = os.path.join(DIR, 'contours', 'hand_annotations.csv')
hand_annotations = pd.read_csv(csvfile)
hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))

#annotation = np.load(filepath, allow_pickle = True, encoding='latin1')
#contours = pd.DataFrame(annotation)
#hand_annotations = contours.rename(columns={0:"name", 1:"section", 2:"vertices"})
#unique_values = hand_annotations.groupby(['name']).size()
print(hand_annotations.head() )
#sys.exit()
str_contours_annotation, first_sec, last_sec = get_contours_from_annotations(animal, target_structure, hand_annotations, densify=0)
color = 2
neuroglancer.set_server_bind_address('0.0.0.0')
viewer = neuroglancer.Viewer()
print(viewer)

ng_structure_volume = add_structure_to_neuroglancer( viewer, str_contours_annotation, target_structure, animal, first_sec, last_sec, \
                                                    color_radius=2, xy_ng_resolution_um=5, threshold=1, color=color, \
                                                    solid_volume=False, no_offset_big_volume=True, save_results=False, \
                                                    return_with_offsets=False, add_to_ng=True, human_annotation=True )

print('ng_structure_volume shape', ng_structure_volume.shape)
print('ng_structure_volume max', np.amax(ng_structure_volume))
