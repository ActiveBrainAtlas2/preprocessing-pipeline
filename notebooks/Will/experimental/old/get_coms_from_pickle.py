from bdb import Breakpoint
import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
import os
import pickle

save_dict = pickle.load(open(os.path.join(sys.path[0], 'com_save_7-1-2021.p'),'rb'))
#dict_keys(['atlas_com', 'beth_coms', 'beth_corrected_coms', 'bili_aligned_coms', 'bili_aligned_corrected_coms', 'kui_airlab_coms'])
for key,value in save_dict.items():
    exec("%s = value" % (key))

def get_prep_list_for_rough_alignment_test():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']

def get_prep_list():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55','DK52']

def atlas_to_physical(com):
    com_physical = (np.array(com)*10/np.array([10,10,20])+np.array([500,500,150]))*np.array([10,10,20])
    return com_physical

def image_to_physical(com):
    com_physical = np.array(com)*np.array([0.325,0.325,20])
    return com_physical

def neuroglancer_atlas_to_physical(com):
    com_physical = np.array(com)*np.array([10,10,20])
    return com_physical

def conversion_identity(com):
    return com

def convert_com_dict_units(com_dict,conversion_function):
    com_dict_converted = {}
    for landmark,com in com_dict.items():
        com_dict_converted[landmark] = conversion_function(com)
    return com_dict_converted

def get_atlas_com():
    atlas_com_phys = convert_com_dict_units(atlas_com,atlas_to_physical)
    return atlas_com_phys

def get_prepi_com(prepi):
    prepi_com = convert_com_dict_units(beth_coms[prepi],image_to_physical) 
    return prepi_com

def get_corrected_prepi_com(prepi):
    com = combined_og_and_corrected_beth_annotation(beth_coms[prepi],beth_corrected_coms[prepi])
    prepi_com = convert_com_dict_units(com,image_to_physical) 
    return prepi_com

def get_corrected_dk52_com():
    return get_corrected_prepi_com('DK52')

def get_dk52_com():
    return get_prepi_com('DK52')

def get_corrected_prep_coms():
    prep_list = get_prep_list_for_rough_alignment_test()
    corrected_prep_coms = []
    for prepi in prep_list:
        corrected_com = combined_og_and_corrected_beth_annotation(beth_coms[prepi],beth_corrected_coms[prepi])
        corrected_prep_coms.append(convert_com_dict_units(corrected_com,image_to_physical))
    return corrected_prep_coms
    
def get_prep_coms():
    prep_coms = [convert_com_dict_units(com_dict,image_to_physical) for name,com_dict in beth_coms.items()]
    return prep_coms

def combined_og_and_corrected_beth_annotation(og,corrected):
    og_landmarks = list(og.keys())
    corrected_landmarks = list(corrected.keys())
    for landmarki in og_landmarks:
        if landmarki not in corrected_landmarks:
            corrected[landmarki] = og[landmarki]
    return corrected
