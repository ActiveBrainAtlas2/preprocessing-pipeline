from abakit.lib.SqlController import SqlController
from abakit.registration.algorithm import align_point_dictionary
import numpy as np

animal = 'DK55'
controller = SqlController(animal)
atlas_centers = controller.get_atlas_centers()
reference_centers = controller.get_com_dict(prep_id=animal)
R, t = align_point_dictionary(atlas_centers, reference_centers)
t = t.T / np.array([0.325,0.325,20]) # production version
print('R')
print(R)
print('t')
print(t)