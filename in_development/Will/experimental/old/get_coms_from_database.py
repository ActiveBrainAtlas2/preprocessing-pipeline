import sys
import numpy as np
from abakit.lib.Controllers.SqlController import SqlController
controller = SqlController('DK52')

def get_prep_list_for_rough_alignment_test():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']

def get_prep_list():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55','DK52']

def image_to_physical(com):
    com_physical = np.array(com)*np.array([0.325,0.325,20])
    return com_physical
def convert_com_dict_units(com_dict,conversion_function):
    com_dict_converted = {}
    for landmark,com in com_dict.items():
        com_dict_converted[landmark] = conversion_function(com)
    return com_dict_converted

def get_atlas_com():
    return controller.get_atlas_centers()

def get_prepi_com(prepi):
    com = controller.get_com_dict(prepi,input_type_id=1,person_id=2,active=False)
    prepi_com = convert_com_dict_units(com,image_to_physical) 
    return prepi_com

def get_corrected_prepi_com(prepi):
    return controller.get_com_dict(prepi,input_type_id=2,person_id=2,active=True)

def get_corrected_dk52_com():
    return get_corrected_prepi_com('DK52')

def get_dk52_com():
    return get_prepi_com('DK52')

def get_corrected_prep_coms():
    prep_list = get_prep_list_for_rough_alignment_test()
    corrected_prep_coms = []
    for prepi in prep_list:
        corrected_com = combined_og_and_corrected_beth_annotation(get_prepi_com(prepi),get_corrected_prepi_com(prepi))
        corrected_prep_coms.append(convert_com_dict_units(corrected_com,image_to_physical))
    return corrected_prep_coms
    
def get_prep_coms():
    prep_list = get_prep_list_for_rough_alignment_test()
    prep_coms = [convert_com_dict_units(get_prepi_com(prepi),image_to_physical) for prepi in prep_list]
    return prep_coms

def combined_og_and_corrected_beth_annotation(og,corrected):
    og_landmarks = list(og.keys())
    corrected_landmarks = list(corrected.keys())
    for landmarki in og_landmarks:
        if landmarki not in corrected_landmarks:
            corrected[landmarki] = og[landmarki]
    return corrected
