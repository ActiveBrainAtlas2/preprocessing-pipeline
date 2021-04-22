"""
Creates a 3D Mesh
"""
import argparse
import os
import sys
import json
from concurrent.futures.process import ProcessPoolExecutor
from skimage import io
from timeit import default_timer as timer
import numpy as np
from taskqueue.taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
import shutil

from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_cpus, get_hostname

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def create_mesh(animal, limit, mse):
    #chunks = calculate_chunks('full', -1)
    chunks = [64,64,1]
    resolution = 25 
    scales = (resolution, resolution, resolution)
    fileLocationManager = FileLocationManager(animal)
    INPUT = "/net/birdstore/Vessel/WholeBrain/ML_2018_08_15/visualization/Neuroglancer_cc"
    OUTPUT1_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_input')
    OUTPUT2_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    PROGRESS_DIR = os.path.join(fileLocationManager.prep, 'progress', 'mesh_input')
    if 'ultraman' in get_hostname():
        INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full_aligned')
        if os.path.exists(OUTPUT1_DIR):
            shutil.rmtree(OUTPUT1_DIR)
        if os.path.exists(OUTPUT2_DIR):
            shutil.rmtree(OUTPUT2_DIR)
        if os.path.exists(PROGRESS_DIR):
            shutil.rmtree(PROGRESS_DIR)

    files = sorted(os.listdir(INPUT))

    os.makedirs(OUTPUT1_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)

    len_files = len(files)
    midpoint = len_files // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
    data_type = midfile.dtype
    """
    ids = [  8,  16,  24,  32,  40,  48,  56,  64,  72,  80,  88,  96,
       104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 200,
       208, 216, 224, 232, 240, 248, 255]
    """
    image = np.load('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures/allen/allen.npy')
    ids = np.unique(image)
    ids = [(number, f'{number}: {number}') for number in ids]


    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]
    height, width = midfile.shape
    startx = 0
    endx = midfile.shape[1]
    starty = 0
    endy = midfile.shape[0]
    height = endy - starty
    width = endx - startx
    starting_points = [starty,endy, startx,endx]
    volume_size = (width, height, len(files)) # neuroglancer is width, height
    print('volume size', volume_size)
    ng = NumpyToNeuroglancer(animal, None, scales, layer_type='segmentation', data_type=data_type, chunk_size=chunks)
    ng.init_precomputed(OUTPUT1_DIR, volume_size, starting_points=starting_points, progress_id=1)

    file_keys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        file_keys.append([i, infile])
        #ng.process_image([i, infile])
    #sys.exit()

    start = timer()
    workers, cpus = get_cpus()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_image, sorted(file_keys), chunksize=workers)
        executor.shutdown(wait=True)

    ng.precomputed_vol.cache.flush()

    end = timer()
    print(f'Create volume method took {end - start} seconds')



    ##### rechunk
    cloudpath1 = f"file://{OUTPUT1_DIR}"
    cv1 = CloudVolume(cloudpath1, 0)
    _, workers = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    cloudpath2 = f'file://{OUTPUT2_DIR}'


    tasks = tc.create_transfer_tasks(cloudpath1, dest_layer_path=cloudpath2, 
        chunk_size=[64,64,64], mip=0, skip_downsamples=True)

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
            "ids": [str(number) for number, label in ids],
            "properties": [{
                "id": "label",
                "type": "label",
                "values": [str(label) for number, label in ids]
            }]
        }
    }
    with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
        json.dump(info, file, indent=2)


    ##### first mesh task, create meshing tasks
    workers, _ = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    mesh_dir = f'mesh_mip_0_err_{mse}'
    cv2.info['mesh'] = mesh_dir
    cv2.commit_info()
    tasks = tc.create_meshing_tasks(cv2.layer_cloudpath, mip=0, mesh_dir=mesh_dir, max_simplification_error=mse)
    tq.insert(tasks)
    tq.execute()
    ##### 2nd mesh task, create manifest
    tasks = tc.create_mesh_manifest_tasks(cv2.layer_cloudpath, mesh_dir=mesh_dir)
    tq.insert(tasks)
    tq.execute()


    
    print("Done!")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--mse', help='Enter the MSE', required=False, default=40)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    mse = int(args.mse)
    create_mesh(animal, limit, mse)

