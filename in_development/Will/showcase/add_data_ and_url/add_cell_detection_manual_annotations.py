from lib.SqlController import SqlController
from lib.UrlGenerator import UrlGenerator
import json
import numpy as np
url = 377
animal = 'DK55'
generator = UrlGenerator()
controller = SqlController(animal)
generator.load_database_url(url)
positive = generator.get_points_from_annotation_layer('Positive')*np.array([0.325,0.325,20])
negative = generator.get_points_from_annotation_layer('Negative')*np.array([0.325,0.325,20])

for pointi in positive:
    controller.add_layer_data_row(animal,34,1,pointi,52,'positive_round1')

for pointi in negative:
    controller.add_layer_data_row(animal,34,1,pointi,52,'negative_round1')

print()