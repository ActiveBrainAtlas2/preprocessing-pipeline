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
import shutil
from timeit import default_timer as timer
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_affine import get_transformation_matrix, DATA_PATH

start = timer()


def create_points(animal, layer, create):

    fileLocationManager = FileLocationManager(animal)
    sql_controller = SqlController(animal)
    sqlController = SqlController(animal)
    resolution = sqlController.scan_run.resolution
    URL_ID = 182 # DK52 this needs to be turned into a variable or looked up somehow

    df = sql_controller.get_point_dataframe(URL_ID)
    df = df.loc[df['Layer'] == layer]
    print(df.head())

    R = np.eye(3)
    t = np.zeros(3)

    R = np.array([[1.03699589, -0.04262374, 0.01931515],
           [0.04338848, 1.03626601, -0.04266775],
           [-0.01752994, 0.04343171, 1.03699408]]),
    t = np.array([[-301.07168962],
           [-254.70219464],
           [-266.32054886]])


    coordinates = []

    # shuffle the DataFrame rows
    df = df.sample(frac=1)

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

        coordinates.append((xt, yt, zt))


    width = sql_controller.scan_run.width
    height = sql_controller.scan_run.height
    sections = sqlController.get_section_count(animal)



    if create:
        layer = str(layer).replace(' ','_')
        OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, layer)
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        info = os.path.join(DATA_PATH, 'atlas_data', 'points', 'info')
        outfile = os.path.join(OUTPUT_DIR, 'info')
        with open(info, 'r+') as rf:
            data = json.load(rf)
            data['upper_bound'] = [width, height, sections]  # <--- add `id` value.
            rf.seek(0)  # <--- should reset file position to the beginning.
        with open(outfile, 'w') as wf:
            json.dump(data, wf, indent=4)

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
            outfile.close()


    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True,)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    parser.add_argument('--layer', help='layer', required=False, default='PM nucleus')
    args = parser.parse_args()
    animal = args.animal
    layer = args.layer
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_points(animal, layer, create)

