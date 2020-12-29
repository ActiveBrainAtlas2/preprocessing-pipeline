"""
This takes the coordinates and packs them into a binary file,
see https://github.com/google/neuroglancer/issues/227
Create a dir on birdstore called points
put the info file under points/info
create the binary file and put in points/spatial0/0_0_0
"""
import argparse
import json
import os
import struct
import sys
import numpy as np
from timeit import default_timer as timer
from _collections import OrderedDict
import shutil
from pprint import pprint
import pandas as pd
start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties
from utilities.utilities_affine import align_point_sets, DK52_centers, DATA_PATH


def create_points(animal, create):

    fileLocationManager = FileLocationManager(animal)
    sql_controller = SqlController(animal)
    atlas_name = 'atlasV7'
    DF_DIR = '/net/birdstore/Active_Atlas_Data/data_root/atlas_data'
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'points')
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
    if os.path.exists(OUTPUT_DIR) and create:
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sqlController = SqlController(animal)
    resolution = sqlController.scan_run.resolution
    surface_threshold = 0.8
    SCALE = (10 / resolution)
    resolution = int(resolution * 1000 * SCALE)

    csvfile = os.path.join(DF_DIR, f'{animal}.points.csv')
    df = pd.read_csv(csvfile, dtype={'Layer': 'str', 'X': np.uint16, 'Y': np.uint16, 'Section': np.uint16})
    df = df.loc[df['Layer'] == 'PM nucleus']
    print(df.head())

    rotationpath = os.path.join(ATLAS_PATH, f'atlas2{animal}.rotation.npy')
    r_auto = np.load(rotationpath)
    translatepath = os.path.join(ATLAS_PATH, f'atlas2{animal}.translation.npy')
    t_auto = np.load(translatepath)

    R = np.array([[0.99539957,  0.36001948,  0.01398446],
                  [-0.35951649,  0.99520404, - 0.03076857],
                 [-0.02361111,0.02418234,1.05805842]])
    t = np.array([[19186.25529129],
                  [9825.28539829],
                  [78.18301303]])


    coordinates = []
    for index, row in df.iterrows():
        x = row['X']
        y = row['Y']
        z = row['Section']
        source_point = np.array([x,y,z]) # get adjusted x,y,z from above loop
        results = (R @ source_point + t.T).reshape(1,3) # transform to fit
        xt = int(round(results[0][0])) # new x
        yt = int(round(results[0][1])) # new y
        zt = int(round(results[0][2])) # z
        print(x,y,z,"\t", xt, yt, zt)

        coordinates.append((xt, yt, z))


    width = sql_controller.scan_run.width
    height = sql_controller.scan_run.height
    sections = sqlController.get_section_count(animal)

    info = os.path.join(DATA_PATH, 'atlas_data', 'points', 'info')
    with open(info, 'r+') as f:
        data = json.load(f)
        data['upper_bound'] = [width, height, sections]  # <--- add `id` value.
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)


    if create:

        spatial_dir = os.path.join(OUTPUT_DIR, 'spatial0')
        os.makedirs(spatial_dir)

        with open(os.path.join(spatial_dir, '0_0_0'), 'wb') as outfile:
            total_count = len(coordinates)  # coordinates is a list of tuples (x,y,z)
            buf = struct.pack('<Q', total_count)
            for (x, y, z) in coordinates:
                pt_buf = struct.pack('<3f', x, y, z)
                buf += pt_buf
            # write the ids at the end of the buffer as increasing integers
            id_buf = struct.pack('<%sQ' % len(coordinates), *range(len(coordinates)))
            buf += id_buf
            outfile.write(buf)

    print('Resolution at', resolution)

    if create:
        pass

    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True,)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_points(animal, create)

