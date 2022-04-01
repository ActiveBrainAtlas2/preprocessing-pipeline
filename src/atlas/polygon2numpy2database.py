import argparse
import os, sys
import numpy as np
from collections import defaultdict
import cv2
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from lib.utilities_process import SCALING_FACTOR
from model.brain_shape import BrainShape
POLYGON_ID = 54


def create_segmentation(animal, debug=False):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    # vars
    sections = sqlController.get_sections(animal, 1)
    if len(sections) < 10:
        sections = os.listdir( os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned'))
        
    num_sections = len(sections)
    if num_sections < 10:
        print('no sections')
        sys.exit()
    
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    scale_xy = sqlController.scan_run.resolution
    z_scale = sqlController.scan_run.zresolution

    width = int(width * SCALING_FACTOR)
    height = int(height * SCALING_FACTOR)
    aligned_shape = np.array((width, height))
    if debug:
        print('aligned shape', aligned_shape)
    
    # get all distinct structures in DB
    abbreviations = sqlController.get_distinct_labels(animal)
    if debug:
        print(f'Working with {len(abbreviations)} structures')
    # We loop through every structure from the CSV data in the DB for a brain
    for abbreviation in tqdm(abbreviations):
        rows = sqlController.get_annotations_by_structure(animal, 1, abbreviation, POLYGON_ID)
        polygons = defaultdict(list)
        
        for row in rows:
            xy = (row.x/scale_xy, row.y/scale_xy)
            z = int(np.round(row.z/z_scale))
            polygons[z].append(xy)
            
        #### loop through all the sections and write to a template, then add that template to the volume
        structure_volume = np.zeros((aligned_shape[1], aligned_shape[0], num_sections), dtype=np.uint8)
        
        # Get the min and max for x,y, and z for each structure
        # They need to be scaled and downsampled. If you didn't downsample, the array would be far too large
        minx, maxx, miny, maxy, minz, maxz = sqlController.get_structure_min_max(animal, abbreviation, POLYGON_ID)
        minx = int(round((minx/scale_xy)*SCALING_FACTOR))
        maxx = int(round((maxx/scale_xy)*SCALING_FACTOR))
        miny = int(round((miny/scale_xy)*SCALING_FACTOR))
        maxy = int(round((maxy/scale_xy)*SCALING_FACTOR))
        minz = int(round(minz/z_scale))
        maxz = int(round(maxz/z_scale))
        
        for section, points in polygons.items():
            template = np.zeros((aligned_shape[1], aligned_shape[0]), dtype=np.uint8)
            points = np.array(points)
            points = np.round(points*SCALING_FACTOR)
            points = points.astype(np.int32)
            cv2.fillPoly(template, pts = [points], color = 1)
        
            structure_volume[:, :, section] += template
                
                
        saveme = np.ndarray.dumps(structure_volume[miny:maxy, minx:maxx, minz:maxz])
        brain_region = sqlController.get_structure(abbreviation)
        brain_shape = BrainShape(prep_id = animal, FK_structure_id = brain_region.id, numpy_data = saveme)
        sqlController.add_row(brain_shape)
        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--debug', help='Enter true or false', required=False, default='false')
    

    args = parser.parse_args()
    animal = args.animal
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_segmentation(animal, debug)
