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
import requests
from timeit import default_timer as timer
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_affine import get_transformation_matrix, DATA_PATH, align_point_sets

start = timer()

def get_transform(animal):
    res = requests.get(f'https://activebrainatlas.ucsd.edu/activebrainatlas/alignatlas?animal={animal}')
    r = np.array(res.json()['rotation'])
    t = np.array(res.json()['translation'])
    return r, t


def transform_point_dataframe(
        src_url_id=182,
        src_animal='DK52',
        src_scale=(0.325, 0.325, 20),
        dst_animal='DK39',
        dst_scale=(0.325, 0.325, 20),
        layer='premotor'
):
    """Transform coordinates from one animal brain to another.

    The transformation is from src coordinates to dst coordinates.
    """
    src_scale = np.array(src_scale)
    dst_scale = np.array(dst_scale)

    # Get transformations from atlas to each animal
    r_src, t_src = get_transform(src_animal)
    r_dst, t_dst = get_transform(dst_animal)

    # Get transformation from src to dst
    r = r_dst @ np.linalg.inv(r_src)
    t_phys = np.diag(dst_scale) @ t_dst - np.diag(src_scale) @ t_src

    # Get src points data
    sqlController = SqlController(src_animal)
    df_src = sqlController.get_point_dataframe(src_url_id)
    df_src = df_src[df_src['Layer'] == layer]

    # Transform points from src to dst
    x_src = df_src[['X', 'Y', 'Section']].to_numpy().T
    x_src_phys = np.diag(src_scale) @ x_src
    x_dst_phys = r @ x_src_phys + t_phys
    x_dst = np.diag(1 / dst_scale) @ x_dst_phys
    return x_dst

def create_points(src_animal, dst_animal, layer, create):
    debug = True
    fileLocationManager = FileLocationManager(src_animal)
    sqlController = SqlController(src_animal)
    resolution = sqlController.scan_run.resolution
    src_url_id = 182 # DK52 this needs to be turned into a variable or looked up somehow
    # Get src points data
    df_src = sqlController.get_point_dataframe(src_url_id)
    df_src = df_src[df_src['Layer'] == layer]
    src_scale = np.array([resolution, resolution, 20])
    ## now get dst animal resolution
    sqlController = SqlController(dst_animal)
    resolution = sqlController.scan_run.resolution
    dst_scale = np.array([resolution, resolution, 20])
    if debug:
        print(df_src['Layer'].unique())
    df_drc = df_src.loc[df_src['Layer'] == layer]
    if debug:
        print(df_src.head())

        # Get transformations from atlas to each animal
    r_src, t_src = get_transform(src_animal)
    r_dst, t_dst = get_transform(dst_animal)

    # Get transformation from src to dst
    r = r_dst @ np.linalg.inv(r_src)
    t_phys = np.diag(dst_scale) @ t_dst - np.diag(src_scale) @ t_src


    # Transform points from src to dst
    x_src = df_src[['X', 'Y', 'Section']].to_numpy().T
    x_src_phys = np.diag(src_scale) @ x_src
    x_dst_phys = r @ x_src_phys + t_phys
    #x_dst = np.diag(1 / dst_scale) @ x_dst_phys

    x_dst = transform_point_dataframe()

    print('shape of x_dst', x_dst.shape)

    print(x_dst.T[0])
    results = x_dst.T[0]
    print(results[0], results[1], results[2])
    coordinates = []

    i = 0
    for index, row in df_src.iterrows():
        x = row['X']
        y = row['Y']
        z = row['Section']
        source_point = np.array([x,y,z]) # get adjusted x,y,z from above loop
        results = x_dst.T[i]
        xt = int(round(results[0])) # new x
        yt = int(round(results[1])) # new y
        zt = int(round(results[2])) # z
        print(x,y,z,"\t", xt, yt, zt)

        coordinates.append((xt, yt, zt))
        i += 1


    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    sections = sqlController.get_section_count(dst_animal)


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
        total_count = len(coordinates)  # coordinates is a list of tuples (x,y,z)

        with open(os.path.join(spatial_dir, '0_0_0'), 'wb') as outfile:
            buf = struct.pack('<Q', total_count)
            pt_buf = b''.join(struct.pack('<3f', x, y, z) for (x, y, z) in coordinates)
            buf += pt_buf
            id_buf = struct.pack('<%sQ' % len(coordinates), *range(len(coordinates)))
            buf += id_buf
            outfile.write(buf)


    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--src_animal', help='Enter the animal to align from', required=True)
    parser.add_argument('--dst_animal', help='Enter the animal to align to', required=True)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    parser.add_argument('--layer', help='layer', required=False, default='PM nucleus')
    args = parser.parse_args()
    src_animal = args.src_animal
    dst_animal = args.dst_animal
    layer = args.layer
    create = bool({'true': True, 'false': False}[args.create.lower()])
    #create_points(src_animal, dst_animal, layer, create)
    create_points(src_animal, dst_animal, layer, create)

