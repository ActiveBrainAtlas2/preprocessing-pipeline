from lib.sqlcontroller import SqlController
import numpy as np
import pickle

animal = 'DK55'
controller = SqlController(animal)

test_counts,train_sections = pickle.load(open('categories_round2.pkl','rb'))
cells = train_sections['computer missed, human detected']

for celli in cells:
    coord = celli[1]
    coord = np.array([coord['x'],coord['y'],coord['section']])*np.array([0.325,0.325,20])
    controller.add_layer_data_row(animal,34,1,coord,52,'computer missed, human detected')
