import pickle
from lib.SqlController import SqlController
import numpy as np
path = '/home/zhw272/Downloads/AtlasCOMsStack.pkl'
file = open(path,'rb')
coms = pickle.load(file)
animal = 'DK55'
com = coms[animal]
controller = SqlController(animal)
for structure, coordinate in com.items():
    print(structure,coordinate)
    x,y,section = coordinate
    controller.add_layer_data( abbreviation = structure, animal = animal, 
                        layer = 'affine_transformed_COM', x = x, y = y, section = section, 
                       person_id = 2, input_type_id = 3)
print()