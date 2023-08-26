"""
Creates a 3D Mesh
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from taskqueue.taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
import shutil
import numpy as np
#np.seterr(all=None, divide=None, over=None, under=None, invalid=None)
np.seterr(all="ignore")
from pathlib import Path

import faulthandler
import signal
faulthandler.register(signal.SIGUSR1.value)
"""
use:
kill -s SIGUSR1 <pid> 
This will give you a stacktrace of the running process and you can see where it hangs.
"""

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.controller.sql_controller import SqlController
from library.image_manipulation.filelocation_manager import FileLocationManager
from library.image_manipulation.neuroglancer_manager import NumpyToNeuroglancer, MESHDTYPE
from library.utilities.utilities_process import get_cpus, get_hostname

def create_mesh(animal, limit, scaling_factor, skeleton, debug):
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    xy = sqlController.scan_run.resolution * 1000
    z = sqlController.scan_run.zresolution * 1000
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'full')
    MESH_INPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'mesh_input_{scaling_factor}')
    MESH_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'mesh_{scaling_factor}')
    PROGRESS_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'progress', f'mesh_{scaling_factor}')
    
    xy *=  scaling_factor
    z *= scaling_factor

    scales = (int(xy), int(xy), int(z))
    if 'godzilla' in get_hostname():
        print(f'Cleaning {MESH_DIR}')
        if os.path.exists(MESH_DIR):
            shutil.rmtree(MESH_DIR)

    files = sorted(os.listdir(INPUT))

    os.makedirs(MESH_INPUT_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)

    len_files = len(files)
    midpoint = len_files // 2
    infile = os.path.join(INPUT, files[midpoint])
    midim = Image.open(infile)
    midfile = np.array(midim)
    del midim
    midfile = midfile.astype(MESHDTYPE)
    ids, counts = np.unique(midfile, return_counts=True)
    ids = ids.tolist()

    if scaling_factor >= 10:    
        chunk = 64
    else:
        chunk = 128

    chunkZ = chunk
    if limit > 0:
        _start = midpoint - limit
        _end = midpoint + limit
        files = files[_start:_end]
        len_files = len(files)
        chunkZ //= 2

    chunks = (chunk, chunk, 1)
    height, width = midfile.shape
    volume_size = (width//scaling_factor, height//scaling_factor, len_files // scaling_factor) # neuroglancer is width, height
    print(f'\nMidfile: {infile} dtype={midfile.dtype}, shape={midfile.shape}, ids={ids}, counts={counts}')
    print(f'Scaling factor={scaling_factor}, volume size={volume_size} with dtype={MESHDTYPE}, scales={scales}')
    print(f'Initial chunks at {chunks} and chunks for downsampling=({chunk},{chunk},{chunkZ})\n')
    ng = NumpyToNeuroglancer(animal, None, scales, layer_type='segmentation', 
        data_type=MESHDTYPE, chunk_size=chunks)

    ng.init_precomputed(MESH_INPUT_DIR, volume_size)
    
    file_keys = []
    index = 0
    for i in range(0, len_files, scaling_factor):
        if index == len_files // scaling_factor:
            print(f'breaking at index={index}')
            break
        infile = os.path.join(INPUT, files[i])            
        file_keys.append([index, infile, (volume_size[1], volume_size[0]), PROGRESS_DIR, scaling_factor])
        index += 1

    _, cpus = get_cpus()
    print(f'Working on {len(file_keys)} files with {cpus} cpus')
    with ProcessPoolExecutor(max_workers=cpus) as executor:
        executor.map(ng.process_image_mesh, sorted(file_keys), chunksize=1)
        executor.shutdown(wait=True)
    
    
    chunks = (chunk, chunk, chunkZ)
    ###### start cloudvolume tasks #####
    # This calls the igneous create_transfer_tasks
    # the input dir is now read and the rechunks are created in the final dir
    _, cpus = get_cpus()
    tq = LocalTaskQueue(parallel=cpus)
    if not os.path.exists(MESH_DIR):
        os.makedirs(MESH_DIR, exist_ok=True)
        layer_path = f'file://{MESH_DIR}'
        #ng.add_rechunking(layer_path, chunks=chunks, mip=0, skip_downsamples=True)
        #ng.add_rechunking(layer_path)
        tasks = tc.create_transfer_tasks(ng.precomputed_vol.layer_cloudpath, dest_layer_path=layer_path, mip=0, skip_downsamples=True)
        #tasks = tc.create_image_shard_transfer_tasks(ng.precomputed_vol.layer_cloudpath, layer_path)
        tq.insert(tasks)
        tq.execute()
    
    ##### add segment properties
    cloudpath = CloudVolume(layer_path, 0)
    segment_properties = {str(id): str(id) for id in ids}
    ng.add_segment_properties(cloudpath, segment_properties)
    ##### first mesh task, create meshing tasks
    #####ng.add_segmentation_mesh(cloudpath.layer_cloudpath, mip=0)
    
    print('Creating sharded mesh')
    tasks = tc.create_meshing_tasks(layer_path, mip=0, compress=True, sharded=True) # The first phase of creating mesh
    tq.insert(tasks)
    tq.execute()
          
    print(f'Creating sharded multires task with {cpus} CPUs')
    # tasks = tc.create_sharded_multires_mesh_tasks(layer_path, num_lod=2, max_labels_per_shard=1, min_shards=2)
    #tasks = tc.create_unsharded_multires_mesh_tasks(layer_path, num_lod=1) 1=106MB, chunks at 64,64,64
    #tasks = tc.create_unsharded_multires_mesh_tasks(layer_path, num_lod=0) 1=66MB, chunks at 64,64,64, also same with skip downsamples dir=188M
    #tasks = tc.create_unsharded_multires_mesh_tasks(layer_path, num_lod=1, magnitude=4) 106M and dir=229M
    #tasks = tc.create_unsharded_multires_mesh_tasks(layer_path, num_lod=1, magnitude=5) 106M and dir=229M
    
    # for apache to serve shards, this command: curl -I --head --header "Range: bytes=50-60" https://activebrainatlas.ucsd.edu/index.html 
    # must return HTTP/1.1 206 Partial Content
    # 
    tasks = tc.create_sharded_multires_mesh_tasks(layer_path, num_lod=1)
    tq.insert(tasks)    
    tq.execute()
    
    print(f'Creating meshing manifest tasks with {cpus} CPUs')
    tasks = tc.create_mesh_manifest_tasks(layer_path) # The second phase of creating mesh
    tq.insert(tasks)
    tq.execute()

    ##### skeleton
    if skeleton:
        print('Creating skeletons')
        tasks = tc.create_skeletonizing_tasks(layer_path, mip=0)
        tq = LocalTaskQueue(parallel=cpus)
        tq.insert(tasks)
        tasks = tc.create_unsharded_skeleton_merge_tasks(layer_path)
        tq.insert(tasks)
        tq.execute()
    

    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--scaling_factor', help='Enter an integer that will be the denominator', required=False, default=1)
    parser.add_argument("--skeleton", help="Create skeletons", required=False, default=False)
    parser.add_argument("--debug", help="debug", required=False, default=False)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    scaling_factor = int(args.scaling_factor)
    skeleton = bool({"true": True, "false": False}[str(args.skeleton).lower()])
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    
    create_mesh(animal, limit, scaling_factor, skeleton, debug)

