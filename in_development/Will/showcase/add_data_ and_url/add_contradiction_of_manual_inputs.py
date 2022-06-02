import pandas as pd
from abakit.lib.Controllers.SqlController import SqlController
import inspect
import numpy as np
def varName(var):
    lcls = inspect.stack()[2][0].f_locals
    for name in lcls:
        if id(var) == id(lcls[name]):
            return name
    return None

def add_points(np_array):
    animal = 'DK55'
    controller = SqlController(animal)
    Detected = 1
    Zhongkai = 34
    Point = 52
    label = varName((np_array))
    print('adding '+label+' points')
    for pointi in np_array:
        structure_id = Point
        coordinates = pointi * np.array([0.325,0.325,20])
        controller.add_layer_data_row(animal,Zhongkai,Detected,coordinates,\
            structure_id,layer=label)


path = '/home/zhw272/Downloads/contradictions.csv'
df = pd.read_csv(path)

manual_train = df[df.name == 'manual_train'].to_numpy()[:,1:4]
manual_negative = df[df.name == 'manual_negative'].to_numpy()[:,1:4]
computer_unsure = df[df.name == 'computer_unsure'].to_numpy()[:,1:4]

add_points(manual_train)
add_points(manual_negative)
add_points(computer_unsure)

animal = 'DK55'
controller = SqlController(animal)
Zhongkai = 34
Detected = 2
Point = 52

print('adding sure points')
for pointi in range(npoints_sure):
    structure_id = Point
    coordinates = cols_sure[pointi]*0.325,rows_sure[pointi]*0.325,sections_sure[pointi]*20
    controller.add_layer_data_row(animal,Zhongkai,Added,coordinates,structure_id,layer='detected_soma')


df.head()
print()