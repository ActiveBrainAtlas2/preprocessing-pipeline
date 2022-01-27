from lib.sqlcontroller import SqlController
import pandas as pd
import numpy as np
animal = 'DK55'
round2_cell_detection_result = pd.read_csv('/data/cell_segmentation/detections_DK55_round2.csv')
cells = round2_cell_detection_result[round2_cell_detection_result.predictions==2][['col','row','section']]
controller = SqlController(animal)


for _,celli in cells.iterrows():
    coord = np.array([celli.col,celli.row,celli.section])*np.array([0.325,0.325,20])
    controller.add_layer_data_row(animal,34,1,coord,52,'detected_soma_round2')
