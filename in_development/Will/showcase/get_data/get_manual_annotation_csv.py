from lib.sqlcontroller import SqlController
import numpy as np
from datetime import datetime
animal = 'DK55'
save_path = '/home/zhw272/Desktop/'
controller = SqlController(animal)

def create_manual_csv():
    search_dictionary = {'prep_id':animal,'input_type_id':1,'person_id':3,'layer':'Premotor'}
    premotor = controller.get_layer_data(search_dictionary)
    time_stamp = datetime.today().strftime('%Y-%m-%d')
    premotor = controller.get_coordinates_from_query_result(premotor)
    np.savetxt(save_path+f'{animal}_premotor_{time_stamp}.csv',premotor,delimiter=',')

def get_manual_csv_per_section():
    nsection = controller.get_sections_numbers(animal)
    for sectioni in nsection:
        search_dictionary = {'prep_id':animal,'input_type_id':1,'person_id':3,'layer':'Premotor','section':int(sectioni*20)}
        premotor = controller.get_layer_data(search_dictionary)
        time_stamp = datetime.today().strftime('%Y-%m-%d')
        premotor = controller.get_coordinates_from_query_result(premotor)
        np.savetxt(save_path+f'{animal}_premotor_{sectioni}_{time_stamp}.csv',premotor,delimiter=',')

def create_detected_csv():
    layer = 'detected_soma'
    search_dictionary = {'prep_id':animal,'input_type_id':6,'person_id':34,'layer':'detected_soma'}
    premotor = controller.get_layer_data(search_dictionary)
    time_stamp = datetime.today().strftime('%Y-%m-%d')
    premotor = controller.get_coordinates_from_query_result(premotor)
    np.savetxt(save_path+f'{animal}_premotor_sure_detection_{time_stamp}.csv',premotor,delimiter=',')
    search_dictionary = {'prep_id':animal,'input_type_id':7,'person_id':34,'layer':'detected_soma'}
    premotor = controller.get_layer_data(search_dictionary)
    time_stamp = datetime.today().strftime('%Y-%m-%d')
    premotor = controller.get_coordinates_from_query_result(premotor)
    np.savetxt(save_path+f'{animal}_premotor_unsure_detection_{time_stamp}.csv',premotor,delimiter=',')

def create_manual_positive_csv():
    search_dictionary = {'prep_id':animal,'input_type_id':1,'person_id':34,'layer':'positive_round1'}
    premotor = controller.get_layer_data(search_dictionary)
    time_stamp = datetime.today().strftime('%Y-%m-%d')
    premotor = controller.get_coordinates_from_query_result(premotor)
    np.savetxt(save_path+f'{animal}_premotor_manual_positive_round1_{time_stamp}.csv',premotor,delimiter=',')

def create_manual_negative_csv():
    search_dictionary = {'prep_id':animal,'input_type_id':1,'person_id':34,'layer':'negative_round1'}
    premotor = controller.get_layer_data(search_dictionary)
    time_stamp = datetime.today().strftime('%Y-%m-%d')
    premotor = controller.get_coordinates_from_query_result(premotor)
    np.savetxt(save_path+f'{animal}_premotor_manual_negative_round1_{time_stamp}.csv',premotor,delimiter=',')

print('done')

if __name__ == '__main__':
    create_detected_csv()
    create_manual_positive_csv()
    create_manual_negative_csv()