from pipeline.Controllers.SqlController import SqlController
import numpy as np
from datetime import datetime
animal = 'DK55'
save_path = '/home/zhw272/Desktop/'
controller = SqlController(animal)
nsection = controller.get_sections_numbers()
for sectioni in range(nsection):
    search_dictionary = {'prep_id':animal,'input_type_id':1,'person_id':2,'layer':'Premotor','section':sectioni}
    premotor = controller.get_layer_data_flex(search_dictionary)
    time_stamp = datetime.today().strftime('%Y-%m-%d')
    premotor = controller.get_coordinates_from_query_result(premotor)
    np.savetxt(save_path+f'{animal}_premotor_{sectioni}_{time_stamp}.csv',premotor,delimiter=',')
print('done')
