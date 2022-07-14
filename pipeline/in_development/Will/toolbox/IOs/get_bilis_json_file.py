import json
import numpy as np
from notebooks.Bili.old.script.toolbox.airlab import load_al_affine_transform

def get_transformed_prepi_com(prepi):
    coms_dict = get_transformed_com_dict(prepi)
    coms = np.array(list(coms_dict.values()))
    return coms

def get_transformed_com_dict(prepi):
    data_path = '/home/zhw272/programming/pipeline_utility/notebooks/Bili/old/data/rough-alignment/'
    file_name = 'coms-rough.json'
    path_to_json_file = data_path+prepi+'/'+file_name
    with open(path_to_json_file) as f:
        coms_dict = json.load(f)
    for key,value in coms_dict.items():
        coms_dict[key] = np.array(value)*np.array([0.325,0.325,20])
    return coms_dict

def get_kui_dk52_dict_com():
    json_file_path = '/home/zhw272/programming/pipeline_utility/notebooks/Bili/data/DK52_coms_kui_detected.json'
    with open(json_file_path) as f:
        coms_dict = json.load(f)
    return coms_dict

def get_kui_dk52_com_dict_physical():
    """get_kui_dk52_com_dict_physical [loads Kui's annotation for DK52 
    the com coordinate is in the physical scale of (1um,1um,1um)]

    :return: [description]
    :rtype: [type]
    """
    json_file_path = '/home/zhw272/programming/pipeline_utility/notebooks/Bili/data/DK52_coms_kui_detected.json'
    with open(json_file_path) as f:
        coms_dict = json.load(f)
    for key,value in coms_dict.items():
        coms_dict[key] = np.array(value)*np.array([0.325,0.325,20])
    return coms_dict

def get_tranformation(prepi):
    """get_tranformation [loads image to image affine transformation calculated by Bili using airlab]

    :param prepi: [brain id]
    :type prepi: [str]
    :return: [transformation]
    :rtype: [airlab transformation]
    """
    data_path = '/home/zhw272/programming/pipeline_utility/notebooks/Bili/old/data/rough-alignment/'
    file_name = 'transform-affine-al.json'
    path_to_json_file = data_path+prepi+'/'+file_name
    affine_transformetion = load_al_affine_transform(path_to_json_file)
    return affine_transformetion