import argparse
import os, sys
import numpy as np
import json
from cloudvolume import CloudVolume
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
import shutil
from tqdm import tqdm
import pickle

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility/src')
sys.path.append(PATH)
from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from lib.utilities_process import SCALING_FACTOR
POLYGON_ID = 54


def create_segmentation(animal, transform=False):
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
        
    if transform:
        outdir = 'transformed'
    else:
        outdir = 'structures'
    
    width = sqlController.scan_run.width
    height = sqlController.scan_run.height
    scale_xy = sqlController.scan_run.resolution
    z_scale = sqlController.scan_run.zresolution
    scales = np.array([int(scale_xy*32*1000), int(scale_xy*32*1000), int(z_scale*1000)])
    print('Scaling to downsampled Neuroglancer with scales', scales)

    width = int(width * SCALING_FACTOR)
    height = int(height * SCALING_FACTOR)
    aligned_shape = np.array((width, height))
    
    volume = np.zeros((aligned_shape[1], aligned_shape[0], num_sections), dtype=np.uint8)
    print('Creating a 3D numpy volume with shape', volume.shape)
    
    # get all distinct structures in DB
    abbreviations = sqlController.get_distinct_labels(animal)
    print(f'Working with {len(abbreviations)} structures')
    structure_dict = sqlController.get_structures_dict()
    segment_properties = {}
    # We loop through every structure in the DB for a brain
    for abbreviation in tqdm(abbreviations):
        try:
            structure_info = structure_dict[abbreviation]
            color = structure_info[1]
            desc = structure_info[0]
            FK_structure_id = structure_info[2]
            brain_shape = sqlController.get_brain_shape(animal, FK_structure_id, transform)
            abbrev = abbreviation.replace('_L','').replace('_R','')
            k = f'{abbrev}: {desc}'
            segment_properties[k] = color
        except KeyError:
            print('key error for', abbreviation)
            continue
        
        arr = pickle.loads(brain_shape.numpy_data)
        arr = arr * color
        row_start = int(round((brain_shape.yoffset/scale_xy)*SCALING_FACTOR))
        col_start = int(round((brain_shape.xoffset/scale_xy)*SCALING_FACTOR))
        z_start = int(round(brain_shape.zoffset/z_scale))
        
        row_end = row_start + arr.shape[0]
        col_end = col_start + arr.shape[1]
        z_end = z_start + arr.shape[2]
        
        volume[row_start:row_end, col_start:col_end, z_start:z_end] = arr
        
    # take the 3D numpy volume and use CloudVolume to convert to precomputed
    offset = (0, 0, 0) # this is just the upper left of the neuroglancer viewer
    layer_type = 'segmentation'
    chunks = [64, 64, 64]
    num_channels = 1
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, outdir)
    
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
            "ids": [str(v) for k, v in segment_properties.items()],
            "properties": [{
                "id": "label",
                "type": "label",
                "values":  [str(k) for k, v in segment_properties.items()]
            }]
        }
    }
    with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
        json.dump(info, file, indent=2)

    #### 1st create mesh
    mse = 40 # default value 
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
    parser.add_argument('--transform', help='Enter true or false', required=False, default='false')
    

    args = parser.parse_args()
    animal = args.animal
    transform = bool({'true': True, 'false': False}[str(args.transform).lower()])
    create_segmentation(animal, transform)
