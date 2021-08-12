"""
This gets the CSV data of the 3 foundation brains' annotations.
These annotations were done by Lauren, Beth, Yuncong and Harvey
(i'm not positive about this)
The annotations are full scale vertices.
"""
import argparse
import json
import os
import sys
import cv2
import numpy as np
from tqdm import tqdm
from scipy.ndimage.measurements import center_of_mass
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
from lib.file_location import DATA_PATH
from lib.utilities_atlas import ATLAS
from lib.sqlcontroller import SqlController

DOWNSAMPLE_FACTOR = 1

def save_volume_origin(atlas_name, animal, structure, volume, xyz_offsets):
    x, y, z = xyz_offsets
    origin = [x, y, z]
    #volume = np.swapaxes(volume, 0, 2)
    #volume = np.rot90(volume, axes=(0, 1))
    #volume = np.flip(volume, axis=0)
    OUTPUT_DIR = os.path.join(DATA_PATH, 'atlas_data', atlas_name, animal)
    volume_filepath = os.path.join(OUTPUT_DIR, 'structure', f'{structure}.npy')
    os.makedirs(os.path.join(OUTPUT_DIR, 'structure'), exist_ok=True)
    np.save(volume_filepath, volume)
    origin_filepath = os.path.join(OUTPUT_DIR, 'origin', f'{structure}.txt')
    os.makedirs(os.path.join(OUTPUT_DIR, 'origin'), exist_ok=True)
    np.savetxt(origin_filepath, origin)


def create_volumes(animal):
    sqlController = SqlController(animal)
    CSVPATH = os.path.join(DATA_PATH, 'atlas_data', ATLAS, animal)
    jsonpath = os.path.join(CSVPATH,  'aligned_structure_sections.json')
    with open(jsonpath) as f:
        aligned_dict = json.load(f)
    structures = list(aligned_dict.keys())                      
    for structure in tqdm(structures):
        onestructure = aligned_dict[structure]
        mins = []
        maxs = []

        for index, points in onestructure.items():
            arr_tmp = np.array(points)
            min_tmp = np.min(arr_tmp, axis=0)
            max_tmp = np.max(arr_tmp, axis=0)
            mins.append(min_tmp)
            maxs.append(max_tmp)
            
        min_xy = np.min(mins, axis=0)
        min_x = min_xy[0]
        min_y = min_xy[1]
        max_xy = np.max(maxs, axis=0)
        max_x = max_xy[0]
        max_y = max_xy[1]
        xlength = max_x - min_x
        ylength = max_y - min_y
        sections = [int(i) for i in onestructure.keys()]
        zlength = (max(sections) - min(sections))        
        padding = 1.1
        PADDED_SIZE = (int(ylength*padding), int(xlength*padding))
        volume = []
        for section, points in sorted(onestructure.items()):
            vertices = np.array(points) - np.array((min_x, min_y))
            volume_slice = np.zeros(PADDED_SIZE, dtype=np.uint8)
            points = (vertices).astype(np.int32)
            color = 10
            volume_slice = cv2.polylines(volume_slice, [points], isClosed=True, color=color, thickness=1)
            volume.append(volume_slice)

        volume = np.array(volume)
        com = center_of_mass(volume)
        midx = (max_x - min_x) / 2
        midy = (max_y - min_y) / 2
        midz = (zlength) / 2
        
        to_um = 0.452 * 32
        #xyz_offsets = (mid_x+min_x, mid_y+min_y, mid_z+min(sections))
        x,y,z = ((min_x+com[0])*to_um, (min_y+com[1])*to_um, (min(sections) + com[2])*20)
        #x,y,z = ((min_x+midx)*to_um, (min_y+midy)*to_um, (min(sections) + midz)*20)
        sqlController.add_layer_data(abbreviation=structure, animal=animal, 
                                     layer='COM', x=x, y=y, section=z, 
                                     person_id=1, input_type_id=1)
        #print(animal, structure, xyz_offsets)
        # print(animal, structure, min_y*32, max_y*32)
        save_volume_origin(ATLAS, animal, structure, volume, (x,y,z))

                      
                      

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=False)
    args = parser.parse_args()
    animal = args.animal
    if animal is None:
        animals = ['MD585', 'MD589', 'MD594']
    else:
        animals = [animal]

    for animal in animals:
        create_volumes(animal)
