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
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama

def get_common_structure(brains):
    sqlController = SqlController('MD594') # just to declare var
    common_structures = set()
    for brain in brains:
        common_structures = common_structures | set(sqlController.get_annotation_points_entry(brain).keys())
    common_structures = list(sorted(common_structures))
    return common_structures


def get_transformation(animal):
    sqlController = SqlController(animal) # just to declare var
    pointdata = sqlController.get_annotation_points_entry(animal)
    atlas_centers = sqlController.get_annotation_points_entry('Atlas', FK_input_id=1, person_id=16)
    common_structures = get_common_structure(['Atlas', animal])
    point_structures = sorted(pointdata.keys())
    
    dst_point_set = np.array([atlas_centers[s] for s in point_structures if s in common_structures and s in atlas_centers]).T
    point_set = np.array([pointdata[s] for s in point_structures if s in common_structures and s in atlas_centers]).T
    
    R, t = umeyama(point_set, dst_point_set)
    return R, t 





def create_segmentation(animal, transform=False):
    fileLocationManager = FileLocationManager(animal)
    OUTPATH = os.path.join(fileLocationManager.thumbnail_web, 'structures')
    os.makedirs(OUTPATH, exist_ok=True)
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
    
    
    # get all distinct structures in DB
    abbreviations = sqlController.get_distinct_labels(animal)
    # We loop through every structure from the CSV data in the DB for a brain
    # If we want to transform the data to atlas coordinates, use transform=True
    if transform:
        atlas_centers = sqlController.get_annotation_points_entry('Atlas', FK_input_id=1, person_id=16)
        R, t = get_transformation(animal)
        abbreviations = [a for a in abbreviations if a in atlas_centers.keys()]
        
    print(f'Working with {len(abbreviations)} structures')
    
    for abbreviation in abbreviations:
        rows = sqlController.get_annotations_by_structure(animal, 1, abbreviation, POLYGON_ID)
        polygons = defaultdict(list)
        
        for row in rows:
            x, y , z = row.x, row.y, row.z
            if transform:
                x, y, z = brain_to_atlas_transform((x, y, z), R, t)

            xy = (x/scale_xy, y/scale_xy)
            z = int(np.round(z/z_scale))
            polygons[z].append(xy)
        #### loop through all the sections and write to a template, then add that template to the volume
        structure_volume = np.zeros((aligned_shape[1], aligned_shape[0], num_sections), dtype=np.uint8)
        
        # Get the min and max for x,y, and z for each structure
        # They need to be scaled and downsampled. If you didn't downsample, the array would be far too large
        minx, maxx, miny, maxy, minz, maxz = sqlController.get_structure_min_max(animal, abbreviation, POLYGON_ID)
        # [[y for y in x] for x in l]
        # minx2 =  [[[point for point in points] for points in polygon] for polygon in polygons.values()] 
        minx2 = [ [ point for point in points for points in polygon] for polygon in polygons.values()]
        #print(*[c for a in polygons.values() for b in a for c in b], sep='\n')
        #minx2 = [c for a in polygons.values() for b in a for c in b]
        #minx2 = [c for a in polygons.values() for b in a for c in b]
        #miny2 = min([[y for y in x] for x in polygons.values()])
        #minz2 = min([[y for y in x] for x in polygons.values()])
        print('x', minx, minx2, len(minx2))
        #print('y', miny,miny2)
        #print('z', minz,minz2)
        
        sys.exit()
        
        minx = int(round((minx/scale_xy)*SCALING_FACTOR))
        maxx = int(round((maxx/scale_xy)*SCALING_FACTOR))
        miny = int(round((miny/scale_xy)*SCALING_FACTOR))
        maxy = int(round((maxy/scale_xy)*SCALING_FACTOR))
        minz = int(round(minz/z_scale))
        maxz = int(round(maxz/z_scale))
        
        midz = maxz - (maxz - minz)//2
        
        for section, points in polygons.items():
            template = np.zeros((aligned_shape[1], aligned_shape[0]), dtype=np.uint8)
            points = np.array(points)
            points = np.round(points*SCALING_FACTOR)
            points = points.astype(np.int32)
            cv2.fillPoly(template, pts = [points], color = 1)
            if section == midz:
                img = np.zeros((aligned_shape[1], aligned_shape[0]), dtype=np.uint8)
                cv2.fillPoly(img, pts = [points], color = 255)
                outfile = os.path.join(OUTPATH, f'{abbreviation}.png')
                cv2.imwrite(outfile, img)
        
            structure_volume[:, :, section] += template
            
                
        arr = structure_volume[miny:maxy, minx:maxx, minz:maxz]
        saveme = np.ndarray.dumps(arr)
        brain_region = sqlController.get_structure(abbreviation)
        brain_shape = BrainShape(prep_id = animal, FK_structure_id = brain_region.id, 
                                 dimensions=str(arr.shape), 
                                 xoffset = (minx*scale_xy)/SCALING_FACTOR,
                                 yoffset = (miny*scale_xy)/SCALING_FACTOR,
                                 zoffset = minz*z_scale,
                                 transformed=transform,
                                 numpy_data = saveme)
        sqlController.add_row(brain_shape)
        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--transform', help='Enter true or false', required=False, default='false')
    

    args = parser.parse_args()
    animal = args.animal
    transform = bool({'true': True, 'false': False}[str(args.transform).lower()])
    create_segmentation(animal, transform)
