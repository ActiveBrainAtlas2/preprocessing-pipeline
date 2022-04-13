from abakit.lib.SqlController import SqlController
import os
import pandas as pd
import numpy as np
data2 = '/scratch/programming/preprocessing-pipeline/in_development/yoav/marked_cell_detector/data2/'
df = pd.read_csv(data2+'/DK55_premotor_manual_2021-12-09.csv')
df_cells = df.to_numpy()
controller = SqlController('DK55')
cells = controller.get_layer_data( dict(prep_id = 'DK55', input_type_id=1,\
             person_id=3,active = 1,layer = 'Premotor'))

truth = [i in cells for i in df_cells]
np.all(truth)