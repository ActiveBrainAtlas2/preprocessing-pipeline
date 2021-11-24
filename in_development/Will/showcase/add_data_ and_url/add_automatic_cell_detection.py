import pandas as pd
import numpy as np
from lib.sqlcontroller import SqlController
csv_path = '/data/cell_segmentation/DK55.Predicted.csv'
data = pd.read_csv(csv_path)
predictions = np.array(data['predictions'].to_list())
sections = np.array(data['section'].to_list()).astype(int)
rows = np.array(data['row'].to_list()).astype(int)
cols  = np.array(data['col'].to_list()).astype(int)
npoints = len(predictions)
animal = 'DK55'
controller = SqlController(animal)

sure = predictions == 2
unsure = predictions == 0

sections_sure = sections[sure]
rows_sure = rows[sure]
cols_sure = cols[sure]
sections_unsure = sections[unsure]
rows_unsure = rows[unsure]
cols_unsure = cols[unsure]
npoints_sure = sum(sure)
npoints_unsure = sum(unsure)

Zhongkai = 34
Sure = 6
Unsure = 7
Point = 52
print('adding sure points')
for pointi in range(npoints_sure):
    structure_id = Point
    coordinates = cols_sure[pointi]*0.325,rows_sure[pointi]*0.325,sections_sure[pointi]*20
    controller.add_layer_data_row(animal,Zhongkai,Sure,coordinates,structure_id,layer='detected_soma')

print('adding unsure points')
for pointi in range(npoints_unsure):
    structure_id = Point
    coordinates = cols_unsure[pointi]*0.325,rows_unsure[pointi]*0.325,sections_unsure[pointi]*20
    controller.add_layer_data_row(animal,Zhongkai,Unsure,coordinates,structure_id,layer='detected_soma')

print('done')