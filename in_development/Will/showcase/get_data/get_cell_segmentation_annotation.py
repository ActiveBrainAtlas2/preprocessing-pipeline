from abakit.lib.SqlController import SqlController
import numpy as np
from datetime import datetime
animal = 'DK55'
save_path = '/home/zhw272/Desktop/'
controller = SqlController(animal)

positive = controller.get_layer_data({'prep_id':animal,'input_type_id':1,'person_id':2,'layer':'positive'})
negative = controller.get_layer_data({'prep_id':animal,'input_type_id':1,'person_id':2,'layer':'negative'})
positive_coord = controller.get_coordinates_from_query_result(positive)
negative_coord = controller.get_coordinates_from_query_result(negative)
time_stamp = datetime.today().strftime('%Y-%m-%d')
np.savetxt(save_path+f'{animal}_positive_{time_stamp}.csv',positive_coord,delimiter=',')
np.savetxt(save_path+f'{animal}_negative_{time_stamp}.csv',negative_coord,delimiter=',')
print('done')
