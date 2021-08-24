import pandas as pd
import ast
import numpy as np

dir = '/net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations/MD585_annotation.csv'
hand_annotations = pd.read_csv(dir)

hand_annotations['vertices'] = hand_annotations['vertices'] \
        .apply(lambda x: x.replace(' ', ',')) \
        .apply(lambda x: x.replace('\n', ',')) \
        .apply(lambda x: x.replace(',]', ']')) \
        .apply(lambda x: x.replace(',,', ',')) \
        .apply(lambda x: x.replace(',,', ',')) \
        .apply(lambda x: x.replace(',,', ',')).apply(lambda x: x.replace(',,', ','))

hand_annotations['vertices'] = hand_annotations['vertices'].apply(lambda x: ast.literal_eval(x))

annotation = hand_annotations[np.logical_and(hand_annotations.name == 'SC',hand_annotations.creator == 'yuncong')]

num_annotations = len(annotation)
all_annotation = []
for annotationi in range(num_annotations):
    section = annotation.iloc[annotationi].section
    rowi = annotation.iloc[annotationi].vertices
    for i in range(len(rowi)):
        rowi[i].append(section)
    all_annotation+=rowi
all_annotation = np.array(all_annotation)

import plotly.graph_objects as go
fig = go.Figure(data=[go.Scatter3d(x=all_annotation[:,0], y=all_annotation[:,1], z=all_annotation[:,2],
                                   mode='markers',marker=dict(size=1))])
margin=go.layout.Margin(
        l=50,
        r=50,
        b=100,
        t=100,
        pad = 4)
fig.show()