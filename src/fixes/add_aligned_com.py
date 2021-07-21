"""
THis script is the interface between the pipeline / database and the alignment software
Ed, please comple and move to pipeline/src
"""

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
DIR = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(DIR)
from model.structure import Structure
from model.layer_data import LayerData
from model.scan_run import ScanRun
from sql_setup import session
CORRECTED = 2

"""
    The provided r, t is the affine transformation from brain to atlas such that:
        t_phys = atlas_scale @ t
        atlas_coord_phys = r @ brain_coord_phys + t_phys

    The corresponding reverse transformation is:
        brain_coord_phys = r_inv @ atlas_coord_phys - r_inv @ t_phys
"""

def atlas_to_brain_transformXXX(
    atlas_coord, r, t,
    brain_scale=(1,1,1),
    atlas_scale=(1, 1, 1)):
    brain_scale = np.diag(brain_scale)
    atlas_scale = np.diag(atlas_scale)
    # Bring atlas coordinates to physical space
    atlas_coord = np.array(atlas_coord).reshape(3, 1) # Convert to a column vector
    atlas_coord_phys = atlas_scale @ atlas_coord    
    # Apply affine transformation in physical space
    t_phys = atlas_scale @ t
    r_inv = np.linalg.inv(r)
    brain_coord_phys = r_inv @ atlas_coord_phys - r_inv @ t_phys
    # Bring brain coordinates back to brain space
    brain_coord = np.linalg.inv(brain_scale) @ brain_coord_phys
    return brain_coord.T[0] # Convert back to a row vector


def atlas_to_brain_transform(atlas_coord, r, t):
    # Bring atlas coordinates to physical space
    atlas_coord = np.array(atlas_coord).reshape(3, 1) # Convert to a column vector
    # Apply affine transformation in physical space
    r_inv = np.linalg.inv(r)
    #####brain_coord_phys = r_inv @ atlas_coord - r_inv @ t
    brain_coord_phys = r_inv @ atlas_coord - (r_inv @  t)
    # Bring brain coordinates back to brain space
    #brain_coord = np.linalg.inv(brain_scale) @ brain_coord_phys
    return brain_coord_phys.T[0] # Convert back to a row vector


def brain_to_atlas_transform(
    brain_coord, r, t,
    brain_scale=(1, 1, 1),
    atlas_scale=(1, 1, 1)
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
    #####brain_scale = np.diag(brain_scale)
    #####atlas_scale = np.diag(atlas_scale)

    # Transform brain coordinates to physical space
    brain_coord = np.array(brain_coord).reshape(3, 1) # Convert to a column vector
    #####brain_coord_phys = brain_scale @ brain_coord
    
    # Apply affine transformation in physical space
    # t_phys = atlas_scale @ t
    # The following is wrong but it is what the rest of the code assumes
    # We need to fix it in the future
    # this gets flip flopped to above line
    #####t_phys = brain_scale @ t
    #####atlas_coord_phys = r @ brain_coord_phys + t_phys
    atlas_coord = r @ brain_coord + t

    # Bring atlas coordinates back to atlas space
    #atlas_coord = np.linalg.inv(atlas_scale) @ atlas_coord_phys

    #####return atlas_coord_phys.T[0] # Convert back to a row vector
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
            .filter(LayerData.input_type_id == input_type_id)\
            .all()
    row_dict = {}
    for row in rows:
        structure = row.structure.abbreviation
        row_dict[structure] = [row.x, row.y, row.section]
    return row_dict


def add_layer(animal, structure, x, y, section, person_id, layer='COM'):
    com = LayerData(
        prep_id=animal, structure=structure, x=x, y=y, section=section, layer=layer,
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

        print(animal, abbrev, x,y,section)
        add_layer(animal, structure, x, y, section, person_id)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--jsonfile', help='Enter json file', required=False)
    parser.add_argument('--pointbrain', help='Enter point animal', required=True)
    parser.add_argument('--imagebrain', help='Enter image animal', required=True)
    

    args = parser.parse_args()
    jsonfile = args.jsonfile
    pointbrain = args.pointbrain
    imagebrain = args.imagebrain

    r0, t0 = get_transformation_matrix(pointbrain, 'corrected')
    r1, t1 = get_transformation_matrix(imagebrain, 'corrected')
    # get some COM data from DK55
    data = get_centers(pointbrain, CORRECTED)
    for abbrev, coord in data.items():
        x0, y0 , section0 = coord
        #x1, y1, section1 = brain_to_atlas_transform(coord, r0, t0, (1,1,1), (1,1,1))


        x2,y2,section2 = atlas_to_brain_transform((x1,y1,section1), r1, t1)
        structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
        print(structure.abbreviation, end="\t")
        print( round(x0), round(y0),round(section0), end="\t\t")
        print( round(x1), round(y1),round(section1), end="\t")
        print( round(x2), round(y2),round(section2))

        
        #add_layer(imagebrain, structure, x2, y2, section2, 1, 'CCCCCC')
    # transform to atlas space        

