"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""

import argparse
from sqlalchemy import func
from tqdm import tqdm
import numpy as np
import os
import sys
import ast
import pandas as pd
from datetime import datetime

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(DIR)
from model.structure import Structure
from model.layer_data import LayerData
from sql_setup import session



def add_layer(animal, abbreviation, x, y, section, person_id, layer='COM'):
    structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbreviation)).one()
    com = LayerData(
        prep_id=animal, structure=structure, x=x, y=y, section=section, layer=layer,
        created=datetime.utcnow(), active=True, person_id=person_id, input_type_id=3
    )
    try:
        session.add(com)
        session.commit()
    except Exception as e:
        print(f'No merge {e}')
        session.rollback()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter animal', required=True)
    parser.add_argument('--filepath', help='Enter file path', required=True)
    

    args = parser.parse_args()
    animal = args.animal
    filepath = args.filepath
    
    df = pd.read_csv(filepath)
    df['Coordinate 1'] = df['Coordinate 1'].apply(lambda x: ast.literal_eval(x))
    print(df.head())
    person_id = 23
    for index, row in df.iterrows():
        coords = row['Coordinate 1']
        x = int(coords[0]) * 0.325
        y = int(coords[1]) * 0.325
        section = int(coords[2]) * 20
        abbreviation = row['Description']
        abbreviation = abbreviation.strip()
        add_layer(animal, abbreviation, x, y, section, person_id, layer='COM')
    
    
 