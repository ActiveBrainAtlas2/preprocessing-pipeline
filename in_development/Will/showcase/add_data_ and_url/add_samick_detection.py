from pipeline.lib.SqlController import SqlController
import pandas as pd
import numpy as np
animal = 'DK39'
controller = SqlController(animal)
file = '/data/samik_detection/DK39/jsonG/DK39_CH3_premotor.csv'
premotor = pd.read_csv(file,header=None).to_numpy()
premotor = premotor[:,[1,2,0]]
premotor = premotor * np.array([0.325,0.325,20])
for pointi in premotor:
    controller.add_layer_data_row(animal,34,1,pointi,52,'samick_cell_detection')
print('done')