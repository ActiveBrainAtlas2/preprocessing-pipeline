import argparse
import os, sys
import numpy as np
from collections import defaultdict
import cv2
import json
from cloudvolume import CloudVolume
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
import shutil
from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager


def create_segmentation(animal, label, debug=False):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    from lib.utilities_process import SCALING_FACTOR
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
    scales = np.array([int(scale_xy*32*1000), int(scale_xy*32*1000), int(z_scale*1000)])
    print('scales', scales)

    width = int(width * SCALING_FACTOR)
    height = int(height * SCALING_FACTOR)
    aligned_shape = np.array((width, height))
    
    # get all distinct structures in layer
    volume = np.zeros((aligned_shape[1], aligned_shape[0], num_sections), dtype=np.uint8)
    structures = sqlController.get_distinct_structures(label)
    structure_dict = sqlController.get_structures_dict()

    print(f'Working with {len(structures)} structures')
    ## loop thru all the structures and get all points
    #structures = [21, 33] ## IC and SC for testing, they are big and obvious
    segment_properties = {}
    for FK_structure_id in structures:
        abbreviation = sqlController.get_structure_from_id(FK_structure_id)
        try:
            structure_info = structure_dict[abbreviation]
            color = structure_info[1]
            segment_properties[abbreviation] = color
        except KeyError:
            continue
        rows = sqlController.get_annotations_by_structure(animal, 1, label, FK_structure_id)
        polygons = defaultdict(list)
        
  
        for row in rows:
            xy = (row.x/scale_xy, row.y/scale_xy)
            z = int(np.round(row.z/z_scale))
            polygons[z].append(xy)
            
        #### loop through all the sections and write to a template, then add that template to the volume
        for section, points in tqdm(polygons.items()):
            template = np.zeros((aligned_shape[1], aligned_shape[0]), dtype=np.uint8)
            points = np.array(points)
            points = np.round(points*SCALING_FACTOR)
            points = points.astype(np.int32)
            # cv2.polylines(template, [points], True, color, 8, lineType=cv2.LINE_AA)
            cv2.fillPoly(template, pts = [points], color = color)
        
            volume[:, :, section - 1] += template
            
    offset = (0, 0, 0)
    layer_type = 'segmentation'
    chunks = [64, 64, 64]
    num_channels = 1
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, label)
    
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # swap axes for neuroglancer viewing
    volume = np.swapaxes(volume, 0, 1)
    
        #### initialize the Cloudvolume
    cloudpath = f'file://{OUTPUT_DIR}'
    info = CloudVolume.create_new_info(
        num_channels = num_channels,
        layer_type = layer_type,
        data_type = str(volume.dtype), # Channel images might be 'uint8'
        encoding = 'raw', # raw, jpeg, compressed_segmentation, fpzip, kempressed
        resolution = scales, # Voxel scaling, units are in nanometers
        voxel_offset = offset, # x,y,z offset in voxels from the origin
        chunk_size = chunks, # units are voxels
        volume_size = volume.shape, # e.g. a cubic millimeter dataset
    )
    vol = CloudVolume(cloudpath, mip=0, info=info, compress=True)
    vol.commit_info()
    vol[:, :, :] = volume[:, :, :]
    #### create json for neuroglancer info files
    cv = CloudVolume(cloudpath, 0)
    cv.info['segment_properties'] = 'names'
    cv.commit_info()
    
    segment_properties_path = os.path.join(cloudpath.replace('file://', ''), 'names')
    os.makedirs(segment_properties_path, exist_ok=True)
    
    info = {
        "@type": "neuroglancer_segment_properties",
        "inline": {
            "ids": [str(number) for number, label in segment_properties.items()],
            "properties": [{
                "id": "label",
                "type": "label",
                "values":  [str(label) for number, label in segment_properties.items()]
            }]
        }
    }
    with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
        json.dump(info, file, indent=2)

    #### 1st create mesh
    mse = 40
    tq = LocalTaskQueue(parallel=1)
    mesh_dir = f'mesh_mip_0_err_{mse}'
    cv.info['mesh'] = mesh_dir
    cv.commit_info()
    tasks = tc.create_meshing_tasks(cv.layer_cloudpath, mip=0, mesh_dir=mesh_dir, max_simplification_error=mse)
    tq.insert(tasks)
    tq.execute()
    
    ##### 2nd mesh task, create manifest
    tasks = tc.create_mesh_manifest_tasks(cv.layer_cloudpath, mesh_dir=mesh_dir)
    tq.insert(tasks)
    tq.execute()
    
        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--label', help='Enter the layer label', required=True)
    parser.add_argument('--debug', help='Enter true or false', required=False, default='false')
    

    args = parser.parse_args()
    animal = args.animal
    label = args.label
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_segmentation(animal, label, debug)
