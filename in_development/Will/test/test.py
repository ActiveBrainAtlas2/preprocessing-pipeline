import pandas as pd
from lib.sqlcontroller import SqlController
import numpy as np

file = '/net/birdstore/Active_Atlas_Data/cell_segmentation/DK55/detections_DK55.2.csv'
detection = pd.read_csv(file)
controller = SqlController('DK55')

search_param = dict(prep_id='DK55',layer='detected_soma',input_type_id=6)
sure_detection = controller.get_coordinates_from_query_result(controller.get_layer_data(search_param))

search_param = dict(prep_id='DK55',layer='detected_soma',input_type_id=7)
unsure_detection = controller.get_coordinates_from_query_result(controller.get_layer_data(search_param))

sure = detection[detection.predictions==2]
unsure = detection[detection.predictions==0]

df_sure = np.array([sure['col'],sure['row'],sure['section']]).T
np.all(np.round(sure_detection).astype(int)==df_sure)

df_unsure = np.array([unsure['col'],unsure['row'],unsure['section']]).T
np.all(np.round(unsure_detection).astype(int)==df_unsure)
print('done')