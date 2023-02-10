"""
Creates a 3D Mesh
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import os
import sys
import json
from skimage import io
from taskqueue.taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
import shutil
import numpy as np
from tqdm import tqdm
from pathlib import Path

PIPELINE_ROOT = Path('./src/pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from image_manipulation.filelocation_manager import FileLocationManager

from controller.sql_controller import SqlController
from image_manipulation.neuroglancer_manager import NumpyToNeuroglancer, calculate_factors
from utilities.utilities_process import get_cpus, get_hostname
DEBUG = True
DTYPE = np.uint8

def create_mesh(animal, limit, scaling_factor):
    chunk = 128
    chunks = (chunk, chunk, 1)
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    xy = sqlController.scan_run.resolution * 1000
    z = sqlController.scan_run.zresolution * 1000
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full')
    OUTPUT1_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_input')
    OUTPUT2_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'mesh_{scaling_factor}')
    PROGRESS_DIR = fileLocationManager.get_neuroglancer_progress(False, 1)
    
    xy *=  scaling_factor
    z *= scaling_factor

    scales = (int(xy), int(xy), int(z))
    if 'godzilla' in get_hostname():
        print('Cleaning output dirs:')
        print(OUTPUT1_DIR)
        print(OUTPUT2_DIR)
        print(PROGRESS_DIR)
        if os.path.exists(OUTPUT1_DIR):
            shutil.rmtree(OUTPUT1_DIR)
        if os.path.exists(OUTPUT2_DIR):
            shutil.rmtree(OUTPUT2_DIR)
        if os.path.exists(PROGRESS_DIR):
            shutil.rmtree(PROGRESS_DIR)

    files = sorted(os.listdir(INPUT))

    os.makedirs(OUTPUT1_DIR, exist_ok=True)
    os.makedirs(OUTPUT2_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)

    len_files = len(files)
    midpoint = len_files // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
    midfile = midfile.astype(np.uint8)
    midfile[midfile > 0] = 255

    data_type = DTYPE
    if limit > 0:
        _start = midpoint - limit
        _end = midpoint + limit
        files = files[_start:_end]
    ids = np.unique(midfile)
    
    height, width = midfile.shape
    volume_size = (width//scaling_factor, height//scaling_factor, len(files) // scaling_factor) # neuroglancer is width, height
    print('volume size', volume_size)
    print('scales', scales)
    print('chunks', chunks)
    print(f'ids {ids}')
    print('midfile data type', data_type)
    ng = NumpyToNeuroglancer(animal, None, scales, layer_type='segmentation', 
        data_type=data_type, chunk_size=chunks)

    ng.init_precomputed(OUTPUT1_DIR, volume_size)

    file_keys = []

    # index, infile, orientation, progress_dir = file_key
    index = 0
    for i in range(0, len(files), scaling_factor):
        infile = os.path.join(INPUT, files[i])            
        file_keys.append([index, infile, (volume_size[1], volume_size[0]), PROGRESS_DIR])
        
        """
        img = process_image([index, infile, (volume_size[1], volume_size[0])])
        try:
            ng.precomputed_vol[:, :, index] = img
        except:
            print(f'Fatal error: Index={index}, could not set {infile} to precomputed with shape {img.shape} and dtype {img.dtype}')
            sys.exit()
        """
        index += 1

    _, workers = get_cpus()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_image_mesh, sorted(file_keys), chunksize=1)
        executor.shutdown(wait=True)

    
    chunks = (chunk, chunk, 64)
    # This calls the igneous create_transfer_tasks
    ng.add_rechunking(OUTPUT2_DIR, chunks=chunks, mip=0, skip_downsamples=True)

    ##### multiple mips
    mips = [0, 1]

    tq = LocalTaskQueue(parallel=workers)
    cloudpath2 = f'file://{OUTPUT2_DIR}'
    for mip in mips:
        cv = CloudVolume(cloudpath2, mip)
        factors = calculate_factors(True, mip)
        tasks = tc.create_downsampling_tasks(cv.layer_cloudpath, mip=mip, num_mips=1, factor=factors, compress=True,  chunk_size=chunks)
        tq.insert(tasks)
        tq.execute()



    ##### add segment properties
    cv2 = CloudVolume(cloudpath2, 0)
    cv2.info['segment_properties'] = 'names'
    cv2.commit_info()

    segment_properties_path = os.path.join(cloudpath2.replace('file://', ''), 'names')
    os.makedirs(segment_properties_path, exist_ok=True)

    info = {
        "@type": "neuroglancer_segment_properties",
        "inline": {
            "ids": [str(value) for value in ids.tolist()],
            "properties": [{
                "id": "label",
                "type": "label",
                "values": [str(value) for value in ids.tolist()]
            }]
        }
    }
    with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
        json.dump(info, file, indent=2)

    ##### first mesh task, create meshing tasks

    ng.add_segmentation_mesh(cv2.layer_cloudpath, mip=0)
 
    ##### skeleton
    """For some reason, this is hanging and not completing when the scaling factor is small
    tasks = tc.create_skeletonizing_tasks(cv2.layer_cloudpath, mip=0)
    tq.insert(tasks)
    tasks = tc.create_unsharded_skeleton_merge_tasks(cv2.layer_cloudpath)
    tq.insert(tasks)
    tq.execute()
    """

    
    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--scaling_factor', help='Enter an integer that will be the denominator', required=False, default=1)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    scaling_factor = int(args.scaling_factor)
    
    create_mesh(animal, limit, scaling_factor)

