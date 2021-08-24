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
from abakit.registration.algorithm import brain_to_atlas_transform, atlas_to_brain_transform, umeyama

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(DIR)
from model.structure import Structure
from model.layer_data import LayerData
from model.scan_run import ScanRun
from sql_setup import session


MANUAL = 1
CORRECTED = 2
DETECTED = 3

"""
    The provided r, t is the affine transformation from brain to atlas such that:
        t_phys = atlas_scale @ t
        atlas_coord_phys = r @ brain_coord_phys + t_phys

    The corresponding reverse transformation is:
        brain_coord_phys = r_inv @ atlas_coord_phys - r_inv @ t_phys
"""



def get_centers(animal, input_type_id, person_id=2, layer='COM'):
    if input_type_id == 3:
        person_id = 23
    rows = session.query(LayerData).filter(
        LayerData.active.is_(True))\
            .filter(LayerData.prep_id == animal)\
            .filter(LayerData.person_id == person_id)\
            .filter(LayerData.layer == layer)\
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
        created=datetime.utcnow(), active=True, person_id=person_id, input_type_id=MANUAL
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
        common_structures = common_structures | set(get_centers(brain, input_type_id=MANUAL).keys())
    common_structures = list(sorted(common_structures))
    return common_structures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--pointbrain', help='Enter point animal', required=True)
    parser.add_argument('--imagebrain', help='Enter image animal', required=True)
    parser.add_argument('--inputlayer', help='Enter input layer name', required=False, default='COM')
    parser.add_argument('--input_type_id', help='Enter input type id', required=False, default=1)
    parser.add_argument('--outputlayer', help='Enter output layer name', required=False)
    

    args = parser.parse_args()
    pointbrain = args.pointbrain
    imagebrain = args.imagebrain
    inputlayer = args.inputlayer
    outputlayer = args.outputlayer
    input_type_id = int(args.input_type_id)


    pointdata = get_centers(pointbrain, input_type_id, layer=inputlayer)
    atlas_centers = get_centers('atlas', input_type_id=1, person_id=16)
    common_structures = get_common_structure([pointbrain, imagebrain])

    point_structures = sorted(pointdata.keys())
    dst_point_set = np.array([atlas_centers[s] for s in point_structures if s in common_structures]).T
    point_set = np.array([pointdata[s] for s in point_structures if s in common_structures]).T

    if len(common_structures) < 3 or dst_point_set.size == 0 or point_set.size == 0:
        print(f'len common structures {len(common_structures)}')
        print(f'Size of dst_point_set {dst_point_set.size} point_set {point_set.size}')
        print('No point data to work with.')
        sys.exit()

    r0, t0 = umeyama(point_set, dst_point_set)


    imagedata = get_centers(imagebrain, input_type_id)
    image_structures = sorted(imagedata.keys())
    image_set = np.array([imagedata[s] for s in image_structures if s in common_structures]).T
    dst_point_set = np.array([atlas_centers[s] for s in image_structures if s in common_structures]).T
    if dst_point_set.size == 0 or image_set.size == 0:
        print(f'No image data to work with. size of dst,image {dst_point_set.size} {image_set.size}')
        sys.exit()
    r1, t1 = umeyama(image_set, dst_point_set)

    # get some COM data from DK55
    for abbrev, coord in pointdata.items():
        x0, y0 , section0 = coord
        x1, y1, section1 = brain_to_atlas_transform(coord, r0, t0)
        x2,y2,section2 = atlas_to_brain_transform((x1,y1,section1), r1, t1)
        structure = session.query(Structure).filter(Structure.abbreviation == func.binary(abbrev)).one()
        print(structure.abbreviation, end="\t")
        print( round(x0), round(y0),round(section0), end="\t\t")
        print( round(x1), round(y1),round(section1), end="\t\t")
        print( round(x2), round(y2),round(section2))

        if outputlayer is not None:
            add_layer(pointbrain, structure, x2, y2, section2, 1, outputlayer)
    # transform to atlas space        

