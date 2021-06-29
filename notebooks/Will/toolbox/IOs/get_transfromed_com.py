import json
import numpy as np

def get_transformed_prepi_com(prepi):
    coms_dict = get_transformed_com_dict(prepi)
    coms = np.array(list(coms_dict.values()))
    return coms

def get_transformed_com_dict(prepi):
    data_path = '/home/zhw272/programming/pipeline_utility/notebooks/Bili/old/data/rough-alignment/'
    com_string = 'coms-rough.json'
    path_to_json_file = data_path+prepi+'/'+com_string
    with open(path_to_json_file) as f:
        coms_dict = json.load(f)
    return coms_dict