"""
Creates a 3D Mesh
"""
import argparse
import os
import sys
from concurrent.futures.process import ProcessPoolExecutor
from skimage import io
from timeit import default_timer as timer
import numpy as np
from taskqueue.taskqueue import LocalTaskQueue
import igneous.task_creation as tc

from tqdm import tqdm

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_cpus, get_segment_ids

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def create_mesh(animal, limit):
    scale = 1
    chunk = 256
    zchunk = 64
    data_type = np.uint8
    resolution = 1000 * scale
    scales = (resolution, resolution, resolution)
    fileLocationManager = FileLocationManager(animal)
    #INPUT = os.path.join(fileLocationManager.prep, 'CH2/full_aligned')
    INPUT = "/net/birdstore/Vessel/WholeBrain/ML_2018_08_15/visualization/Neuroglancer_cc"
    files = sorted(os.listdir(INPUT))
    channel_outdir = 'color_mesh'
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, channel_outdir)
    PROGRESS_DIR = os.path.join(fileLocationManager.prep, 'progress', f'{channel_outdir}')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)

    len_files = len(files)
    midpoint = len_files // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath)
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]
        #files = files[len_files-limit:len_files]
        zchunk = limit
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
    ng = NumpyToNeuroglancer(None, scales, layer_type='segmentation', data_type=data_type, chunk_size=[chunk, chunk, 1])
    ng.init_precomputed(OUTPUT_DIR, volume_size, starting_points=starting_points, progress_dir=PROGRESS_DIR)

    file_keys = []
    for i,f in enumerate(tqdm(files)):
        infile = os.path.join(INPUT, f)
        file_keys.append([i, infile])

    start = timer()
    workers, cpus = get_cpus()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(ng.process_mesh, sorted(file_keys), chunksize=workers)
        executor.shutdown(wait=True)

    ng.precomputed_vol.cache.flush()


    end = timer()
    print(f'Create volume method took {end - start} seconds')

    ids = get_segment_ids(midfile)
    del midfile
    ng.add_segment_properties(ids)

    start = timer()
    tq = LocalTaskQueue(parallel=cpus)
    tasks = tc.create_downsampling_tasks(ng.precomputed_vol.layer_cloudpath, 
                                            num_mips=2, chunk_size=[chunk, 
                                            chunk, zchunk], factor=[2,2,2], 
                                            compress=True)
    tq.insert(tasks)
    tq.execute()
    end = timer()
    print(f'Downsampling took {end - start} seconds')


    print('Finished')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    create_mesh(animal, limit)

