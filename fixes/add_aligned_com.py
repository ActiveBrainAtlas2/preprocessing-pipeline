import argparse
from sqlalchemy import func
from tqdm import tqdm
import json
from pprint import pprint
import numpy as np
import os
import sys
from datetime import datetime
import requests
from requests.exceptions import HTTPError


HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)
from utilities.model.structure import Structure
from utilities.model.layer_data import LayerData
from utilities.model.scan_run import ScanRun
from sql_setup import session
CORRECTED = 2

def brain_to_atlas_transform(
    brain_coord, r, t,
    brain_scale=(0.325, 0.325, 20),
    atlas_scale=(10, 10, 20)
):
    """
    Takes an x,y,z brain coordinates, and a rotation matrix and transform vector.
    Returns the point in atlas coordinates.
    
    The recorded r, t is the transformation from brain to atlas such that:
        t_phys = atlas_scale @ t
        atlas_coord_phys = r @ brain_coord_phys + t_phys
        
    Currently we erraneously have:
        t_phys = brain_scale @ t
    This should be fixed in the future.
    """
    brain_scale = np.diag(brain_scale)
    atlas_scale = np.diag(atlas_scale)

    # Transform brain coordinates to physical space
    brain_coord = np.array(brain_coord).reshape(3, 1) # Convert to a column vector
    brain_coord_phys = brain_scale @ brain_coord
    
    # Apply affine transformation in physical space
    # t_phys = atlas_scale @ t
    # The following is wrong but it is what the rest of the code assumes
    # We need to fix it in the future
    # this gets flip flopped to above line
    t_phys = brain_scale @ t
    atlas_coord_phys = r @ brain_coord_phys + t_phys

    # Bring atlas coordinates back to atlas space
    atlas_coord = np.linalg.inv(atlas_scale) @ atlas_coord_phys

    return atlas_coord.T[0] # Convert back to a row vector


def get_transformation_matrix(animal, input_type):
    try:
        url = f'https://activebrainatlas.ucsd.edu/activebrainatlas/rotation/{animal}/{input_type}/2'
        response = requests.get(url)
        response.raise_for_status()
        # access JSOn content
        transformation_matrix = response.json()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    r = np.array(transformation_matrix['rotation'])
    t = np.array(transformation_matrix['translation'])
    return r,t



def get_centers(animal, input_type_id):

    beth = 2
    rows = session.query(LayerData).filter(
        LayerData.active.is_(True))\
            .filter(LayerData.prep_id == animal)\
            .filter(LayerData.person_id == beth)\
            .filter(LayerData.layer == 'COM')\
            .filter(LayerData).input_type_id == input_type_id)\
            .all()
    row_dict = {}
    for row in rows:
        structure = row.structure.abbreviation
        row_dict[structure] = [row.x, row.y, row.section]
    return row_dict


def add_center_of_mass(animal, structure, x, y, section, person_id):
    com = LayerData(
        prep_id=animal, structure=structure, x=x, y=y, section=section,
        created=datetime.utcnow(), active=True, person_id=person_id, input_type_id=CORRECTED
    )
    try:
        session.add(com)
        session.commit()
    except Exception as e:
        print(f'No merge {e}')
        session.rollback()



def transform_and_add_dict(animal, person_id, row_dict, r=None, t=None):

    for abbrev,v in row_dict.items():
        x = v[0]
        y = v[1]
        section = v[2]
        structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
        if r is not None:
            scan_run = session.query(ScanRun).filter(ScanRun.prep_id == animal).one()
            brain_coords = np.asarray([x, y, section])
            brain_scale = [scan_run.resolution, scan_run.resolution, 20]
            transformed = brain_to_atlas_transform(brain_coords, r, t, brain_scale=brain_scale)
            x = transformed[0]
            y = transformed[1]
            section = transformed[2]

        add_center_of_mass(animal, structure, x, y, section, person_id)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--jsonfile', help='Enter json file', required=False)
    parser.add_argument('--transform', help='Enter true or false', required=True)

    args = parser.parse_args()
    animal = args.animal
    jsonfile = args.jsonfile
    person_id = 28 # bili
    transform = bool({'true': True, 'false': False}[str(args.transform).lower()])
    animals = ['DK39', 'DK41', 'DK43', 'DK52', 'DK54', 'DK55','MD589']

    if jsonfile is not None:
        with open(jsonfile) as f:
            row_dict = json.load(f)
    else:
        row_dict = get_centers(animal, CORRECTED)

    r = None
    t = None

    if transform:
        r, t = get_transformation_matrix(animal, 'corrected')
    
    transform_and_add_dict(animal, person_id, row_dict, r, t)

