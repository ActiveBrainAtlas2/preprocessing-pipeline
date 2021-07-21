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
from pprint import pprint
import numpy as np
import os
import sys
from datetime import datetime


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


def atlas_to_brain_transform(atlas_coord, r, t):
    """
    Takes an x,y,z brain coordinates, and a rotation matrix and translation vector.
    Returns the point in atlas coordinates in micrometers.
    params:
        atlas_coord: tuple of x,y,z coordinates of the atlas in micrometers
        r: float of the rotation matrix
        t: vector of the translation matrix
    """
    # Bring atlas coordinates to physical space
    atlas_coord = np.array(atlas_coord).reshape(3, 1) # Convert to a column vector
    # Apply affine transformation in physical space
    r_inv = np.linalg.inv(r)
    #####brain_coord_phys = r_inv @ atlas_coord - r_inv @ t
    brain_coord_phys = r_inv @ atlas_coord - (r_inv @  t)
    # Bring brain coordinates back to brain space
    #brain_coord = np.linalg.inv(brain_scale) @ brain_coord_phys
    return brain_coord_phys.T[0] # Convert back to a row vector


def brain_to_atlas_transform(brain_coord, r, t):
    """
    Takes an x,y,z brain coordinates, and a rotation matrix and translation vector.
    params:
        atlas_coord: tuple of x,y,z coordinates of the atlas in micrometers
        r: float of the rotation matrix
        t: vector of the translation matrix
    Returns the point in atlas coordinates in micrometers.
    """
    # Transform brain coordinates to physical space
    brain_coord = np.array(brain_coord).reshape(3, 1) # Convert to a column vector
    atlas_coord = r @ brain_coord + t
    #####return atlas_coord_phys.T[0] # Convert back to a row vector
    return atlas_coord.T[0] # Convert back to a row vector


def get_centers(animal, input_type_id, person_id=2):
    beth = 2
    rows = session.query(LayerData).filter(
        LayerData.active.is_(True))\
            .filter(LayerData.prep_id == animal)\
            .filter(LayerData.person_id == person_id)\
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

def get_common_structure(brains):
    common_structures = set()
    for brain in brains:
        common_structures = common_structures | set(get_centers(brain, input_type_id=CORRECTED).keys())
    common_structures = list(sorted(common_structures))
    return common_structures


def align_point_sets(src, dst, with_scaling=True):
    """
    Analytically computes a transformation that minimizes the squared error between source and destination.
    ------------------------------------------------------
    src is the dictionary of the brain we want to align
    dst is the dictionary of the atlas structures
    Defaults to scaling true, which means the transformation is rigid and a uniform scale.
    returns the linear transformation r, and the translation vector t
    """
    assert src.shape == dst.shape
    assert len(src.shape) == 2
    m, n = src.shape  # dimension, number of points

    src_mean = np.mean(src, axis=1).reshape(-1, 1)
    dst_mean = np.mean(dst, axis=1).reshape(-1, 1)

    src_demean = src - src_mean
    dst_demean = dst - dst_mean

    u, s, vh = np.linalg.svd(dst_demean @ src_demean.T / n)

    # deal with reflection
    e = np.ones(m)
    if np.linalg.det(u) * np.linalg.det(vh) < 0:
        print('reflection detected')
        e[-1] = -1

    r = u @ np.diag(e) @ vh

    if with_scaling:
        src_var = (src_demean ** 2).sum(axis=0).mean()
        c = sum(s * e) / src_var
        r *= c

    t = dst_mean - r @ src_mean
    return r, t


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--pointbrain', help='Enter point animal', required=True)
    parser.add_argument('--imagebrain', help='Enter image animal', required=True)
    parser.add_argument('--layer', help='Enter layer name', required=False)
    

    args = parser.parse_args()
    pointbrain = args.pointbrain
    imagebrain = args.imagebrain
    layer = args.layer


    pointdata = get_centers(pointbrain, CORRECTED)
    atlas_centers = get_centers('atlas', input_type_id=1, person_id=16)
    common_structures = get_common_structure([pointbrain, imagebrain])

    point_structures = sorted(pointdata.keys())
    dst_point_set = np.array([atlas_centers[s] for s in point_structures if s in common_structures]).T
    point_set = np.array([pointdata[s] for s in point_structures if s in common_structures]).T
    r0, t0 = align_point_sets(point_set, dst_point_set)


    imagedata = get_centers(imagebrain, CORRECTED)
    image_structures = sorted(imagedata.keys())
    image_set = np.array([imagedata[s] for s in image_structures if s in common_structures]).T
    dst_point_set = np.array([atlas_centers[s] for s in image_structures if s in common_structures]).T
    r1, t1 = align_point_sets(image_set, dst_point_set)

    # get some COM data from DK55
    for abbrev, coord in pointdata.items():
        x0, y0 , section0 = coord
        x1, y1, section1 = brain_to_atlas_transform(coord, r0, t0)
        x2,y2,section2 = atlas_to_brain_transform((x1,y1,section1), r1, t1)
        structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
        print(structure.abbreviation, end="\t")
        print( round(x0), round(y0),round(section0), end="\t\t")
        print( round(x1), round(y1),round(section1), end="\t")
        print( round(x2), round(y2),round(section2))

        if layer is not None:
            add_layer(pointbrain, structure, x2, y2, section2, 1, layer)
    # transform to atlas space        

