"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""

import argparse
from sqlalchemy import func
import json
import os
import sys
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(DIR)
from model.urlModel import UrlModel
from lib.sqlcontroller import SqlController


def create_task(animal, filepath, debug):
    layer = 'detected_soma'
    df = pd.read_csv(filepath)
    if debug:
        print(df.head(25))
        # sys.exit()
    person_id = 26 # change this!
    SURE = 6
    UNSURE = 7
    sqlController = SqlController(animal)
    resolution = sqlController.scan_run.resolution
    for index, row in df.iterrows():
        x = int(row['col']) * resolution
        y = int(row['row']) * resolution
        section = int(row['section']) * 20
        abbreviation = 'point'
        abbreviation = abbreviation.strip()
        if row['label'] == 1:
            input_type = SURE
        else:
            input_type = UNSURE

        if debug:
            print('Add layer', animal, abbreviation, x, y, section, person_id, layer,input_type)
        else:
            if row['label'] == 1:
                sqlController.add_layer_data(abbreviation,animal, layer,x, y, section, person_id, input_type)
            else:
                sqlController.add_layer_data(abbreviation, animal, layer, x, y, section, person_id, input_type)


def parse_layer(animal, id):
    """
    Get the id from https://activebrainatlas.ucsd.edu/activebrainatlas/admin/neuroglancer/urlmodel/
    When you hover over the animal link, you can see the ID in the url, or just click on it.
    """
    sqlController = SqlController(animal)
    try:
        data = sqlController.get_urlModel(id)
    except NoResultFound as nrf:
        print('No results for {} error: {}'.format(animal, nrf))
        return
 
    json_txt = json.loads(data.url)
    layers = json_txt['layers']
    data = []
    for layer in layers:
        if 'annotations' in layer:
            name = layer['name']
            annotation = layer['annotations']
            # d = [row['point'] for row in annotation if 'point' in row]
            d = {row['description']:row['point'] for row in annotation if 'point' in row and 'description' in row}
            for row in annotation:
                if 'point' in row and 'description' in row:
                    description = str(row['description']).strip()
                    x,y,z = row['point']
                    data.append([description, x, y, int(round(z))])
            
            df = pd.DataFrame(data, columns=['description','x','y','section'])
            print(df.head())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter animal', required=True)
    parser.add_argument('--filepath', help='Enter file path', required=True)
    parser.add_argument('--id', help='Enter primary key of URL JSON', required=False, default=0)
    parser.add_argument('--debug', help='Enter true or false', required=False, default='true')
    args = parser.parse_args()
    animal = args.animal
    filepath = args.filepath
    id = int(args.id) 
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    
    create_task(animal, filepath, debug)
    #parse_layer(animal, id)
    
   
    
 