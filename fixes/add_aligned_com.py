from sqlalchemy import func
from tqdm import tqdm

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
from utilities.model.center_of_mass import CenterOfMass
from utilities.model.scan_run import ScanRun
from sql_setup import session

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


def get_transformation_matrix(animal):
    try:
        url = f'https://activebrainatlas.ucsd.edu/activebrainatlas/rotation/{animal}/manual/2'
        response = requests.get(url)
        response.raise_for_status()
        # access JSOn content
        transformation_matrix = response.json()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    return transformation_matrix


animals = ['DK39', 'DK41', 'DK43', 'DK52', 'DK54', 'DK55','MD589']

person_id = 1
beth = 2
for animal in tqdm(animals):
    transformation = get_transformation_matrix(animal)
    r = np.array(transformation['rotation'])
    t = np.array(transformation['translation'])
    person_id = 1 # me
    scan_run = session.query(ScanRun).filter(ScanRun.prep_id == animal).one()
    rows = session.query(CenterOfMass).filter(
        CenterOfMass.active.is_(True))\
            .filter(CenterOfMass.prep_id == animal)\
            .filter(CenterOfMass.person_id == beth)\
            .filter(CenterOfMass.input_type == 'manual')\
            .all()
    row_dict = {}
    for row in rows:
        structure = row.structure.abbreviation
        row_dict[structure] = [row.x, row.y, row.section]

    for abbrev,v in row_dict.items():
        x = v[0]
        y = v[1]
        section = v[2]
        structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
        brain_coords = np.asarray([x, y, section])
        brain_scale = [scan_run.resolution, scan_run.resolution, 20]
        transformed = brain_to_atlas_transform(brain_coords, r, t, brain_scale=brain_scale)
        x = transformed[0]
        y = transformed[1]
        section = transformed[2]
        com = CenterOfMass(
            prep_id=animal, structure=structure, x=x, y=y, section=section,
            created=datetime.utcnow(), active=True, person_id=person_id, input_type='aligned'
        )
        try:
            session.add(com)
            session.commit()
        except Exception as e:
            print(f'No merge for {abbrev} {e}')
            session.rollback()

