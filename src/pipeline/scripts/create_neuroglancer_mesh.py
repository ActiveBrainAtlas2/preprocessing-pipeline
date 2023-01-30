"""
Creates a 3D Mesh
"""
import argparse
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
from skimage.transform import resize

PIPELINE_ROOT = Path('./src/pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from image_manipulation.filelocation_manager import FileLocationManager

from controller.sql_controller import SqlController
from image_manipulation.neuroglancer_manager import NumpyToNeuroglancer, calculate_chunks
from utilities.utilities_process import get_cpus, get_hostname
DEBUG = True

def create_mesh(animal, limit, scaling_factor):
    chunks = (128, 128, 1)
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    xy = sqlController.scan_run.resolution * 1000
    z = sqlController.scan_run.zresolution * 1000
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full')
    OUTPUT1_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_input')
    OUTPUT2_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_scaled')

    xy *=  scaling_factor
    z *= scaling_factor

    scales = (int(xy), int(xy), int(z))
    if 'godzilla' in get_hostname():
        print('Cleaning output dirs:')
        print(OUTPUT1_DIR)
        print(OUTPUT2_DIR)
        if os.path.exists(OUTPUT1_DIR):
            shutil.rmtree(OUTPUT1_DIR)
        if os.path.exists(OUTPUT2_DIR):
            shutil.rmtree(OUTPUT2_DIR)

    files = sorted(os.listdir(INPUT))

    os.makedirs(OUTPUT1_DIR, exist_ok=True)
    os.makedirs(OUTPUT2_DIR, exist_ok=True)

    len_files = len(files)
    midpoint = len_files // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
    midfile = midfile.astype(np.uint8)
    midfile[midfile > 0] = 255

    data_type = np.uint8
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
    for i,f in enumerate(files):
        if i % scaling_factor == 0:
            infile = os.path.join(INPUT, f)            
            file_keys.append([index, infile])
            img = process_image([index, infile, (volume_size[1], volume_size[0])])
            try:
                ng.precomputed_vol[:, :, index] = img
            except:
                print(f'Index={index}, could not set {f} to precomputed with shape {img.shape} and dtype {img.dtype}')
            index += 1
        
    
    # sys.exit()
    #ng.precomputed_vol.cache.flush()

    ##### rechunk
    cloudpath1 = f"file://{OUTPUT1_DIR}"
    # cv1 = CloudVolume(cloudpath1, 0)
    _, workers = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    cloudpath2 = f'file://{OUTPUT2_DIR}'
    chunks = (128, 128, 64)
    tasks = tc.create_transfer_tasks(cloudpath1, dest_layer_path=cloudpath2, 
        chunk_size=chunks, mip=0, skip_downsamples=True)

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
    workers, _ = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    mesh_dir = 'mesh_mip_0_err_40'
    cv2.info['mesh'] = mesh_dir
    cv2.commit_info()
    tasks = tc.create_meshing_tasks(cv2.layer_cloudpath, mip=0, mesh_dir=mesh_dir, max_simplification_error=40)
    tq.insert(tasks)
    tq.execute()
    ##### 2nd mesh task, create manifest
    tasks = tc.create_mesh_manifest_tasks(cv2.layer_cloudpath, mesh_dir=mesh_dir)
    tq.insert(tasks)
    tq.execute()
    
    print("Done!")




def process_image(file_key):
    """This reads the image and starts the precomputed data

    :param file_key: file_key: tuple
    """

    index, infile, orientation = file_key
    basefile = os.path.basename(infile)

    try:
        img = io.imread(infile, img_num=0)
    except IOError as ioe:
        print(f'could not open {infile} {ioe}')
        return
    
    try:
        img = img * 255
        img = resize(img.astype(np.uint8), orientation, anti_aliasing=True)
        img = img.astype(np.uint8)
        img[img==1] = 255

    except:
        print(f'could not resize {basefile} with shape={img.shape} to new shape={orientation}')
        return
    

    if DEBUG:
        values, counts = np.unique(img, return_counts=True)
        print(f'img index={index}, shape={img.shape} dtype={img.dtype} values={values} counts={counts}', end="\t")
    
    try:
        img = img.reshape(1, img.shape[0], img.shape[1]).T
    except:
        print(f'could not reshape {infile}')
        return
    
    if DEBUG:
        print(f'after reshaping img shape={img.shape} dtype={img.dtype}')

    return img


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

