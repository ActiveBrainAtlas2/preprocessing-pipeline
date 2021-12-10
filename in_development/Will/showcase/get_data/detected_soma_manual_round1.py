from lib.sqlcontroller import SqlController
import numpy as np
from datetime import datetime
animal = 'DK55'
save_path = '/home/zhw272/Desktop/'
controller = SqlController(animal)

def get_detected_cells():
    layer = 'detected_soma'
    search_dictionary = {'prep_id':animal,'input_type_id':6,'person_id':34,'layer':'detected_soma'}
    premotor = controller.get_layer_data(search_dictionary)
    sure = controller.get_coordinates_from_query_result(premotor)
    search_dictionary = {'prep_id':animal,'input_type_id':7,'person_id':34,'layer':'detected_soma'}
    premotor = controller.get_layer_data(search_dictionary)
    unsure = controller.get_coordinates_from_query_result(premotor)
    return sure,unsure

def get_manual_positive():
    search_dictionary = {'prep_id':animal,'input_type_id':1,'person_id':34,'layer':'positive_round1'}
    premotor = controller.get_layer_data(search_dictionary)
    premotor = controller.get_coordinates_from_query_result(premotor)
    return premotor

def get_manual_negative():
    search_dictionary = {'prep_id':animal,'input_type_id':1,'person_id':34,'layer':'negative_round1'}
    premotor = controller.get_layer_data(search_dictionary)
    premotor = controller.get_coordinates_from_query_result(premotor)
    return premotor

def get_min_distance(points_a,points_b):
    min_distance = []
    for point_a in points_a:
        distance = []
        for point_b in points_b:
            distance.append(np.sum(np.power((point_a-point_b)*np.array([0.325,0.325,20]),2)))
        min_distance.append(np.min(distance)) 
    min_distance = np.array(min_distance)
    return min_distance

def get_second_min_distance(points_a,points_b):
    min_distance = []
    for point_a in points_a:
        distance = []
        for point_b in points_b:
            distance.append(np.sum(np.power((point_a-point_b)*np.array([0.325,0.325,20]),2)))
        min_distance.append(np.sort(distance)[1]) 
    min_distance = np.array(min_distance)
    return min_distance

sure,unsure = get_detected_cells()
positive = get_manual_positive()
negative = get_manual_negative()

matching = [np.all(pointi == positive[0]) for pointi in unsure]
np.any(matching)
sum(matching)


false_positives = get_min_distance(positive,unsure)
duplicates = get_second_min_distance(positive,positive)
negative_duplicates = get_second_min_distance(negative,negative)

n_duplicates = sum(duplicates == 0)
n_duplicates_negative = sum(negative_duplicates == 0)
n_false_positive = np.sum(false_positives==0)

n_duplicates = np.sum(duplicates==0)
np.sum(min_distance<100)
len(unsure)
len(positive)
len(positive)-n_false_positive-n_duplicates


print('done')
