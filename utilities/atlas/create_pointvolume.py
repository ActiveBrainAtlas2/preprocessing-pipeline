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
import shutil

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)

from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager, DATA_PATH

def create_points(animal, layer, url_id, create):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    # Get src points data
    df = sqlController.get_point_dataframe(url_id)
    df = df[df['Layer'] == layer]
    if create:
        records = df[['X', 'Y', 'Section']].to_records(index=False)
        coordinates = list(records)

        width = sqlController.scan_run.width
        height = sqlController.scan_run.height
        sections = sqlController.get_section_count(animal)


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
    else:
        print(df['Layer'].unique())
        print(df.head(25))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--id', help='URL ID', required=True)
    parser.add_argument('--layer', help='layer', required=False, default='PM nucleus')
    parser.add_argument('--create', help='create volume', required=False, default='false')

    args = parser.parse_args()
    animal = args.animal
    layer = args.layer
    url_id = int(args.id)
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_points(animal, layer, url_id, create)

