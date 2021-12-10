import os
import sys
from concurrent.futures.process import ProcessPoolExecutor
from skimage import io
from lib.file_location import FileLocationManager
from lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer, calculate_chunks
from lib.sqlcontroller import SqlController
from lib.sql_setup import RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES
from lib.utilities_process import get_cpus, SCALING_FACTOR, test_dir

def get_scales(animal,downsample):
    sqlController = SqlController(animal)
    db_resolution = sqlController.scan_run.resolution
    resolution = int(db_resolution * 1000 / SCALING_FACTOR)
    if not downsample:
        resolution = int(db_resolution * 1000)
    scales = (resolution, resolution, 20000)
    return scales

def get_file_information(INPUT):
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath, img_num=0)
    height = midfile.shape[0]
    width = midfile.shape[1]
    num_channels = midfile.shape[2] if len(midfile.shape) > 2 else 1
    file_keys = []
    volume_size = (width, height, len(files))
    for i, f in enumerate(files):
        filepath = os.path.join(INPUT, f)
        file_keys.append([i,filepath])
    return midfile,file_keys,volume_size,num_channels

def create_neuroglancer(animal, channel, downsample, debug=False):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = f'CH{channel}'
    channel_outdir = f'C{channel}T_rechunkme'
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    scales = get_scales(animal,downsample)
    workers, _ = get_cpus()
    chunks = calculate_chunks(downsample, -1)
    progress_id = sqlController.get_progress_id(downsample, channel, 'NEUROGLANCER')
    sqlController.session.close()
    if not downsample:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
        channel_outdir = f'C{channel}_rechunkme'
        sqlController.set_task(animal, progress_id)
        if sqlController.histology.counterstain != None:
            if 'thion' in sqlController.histology.counterstain:
                sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES)
                sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES)
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    error = test_dir(animal, INPUT, downsample, same_size=True)
    if len(error) > 0 and not debug:
        print(error)
        sys.exit()
    midfile,file_keys,volume_size,num_channels = get_file_information(INPUT)
    ng = NumpyToNeuroglancer(animal, None, scales, 'image', midfile.dtype, num_channels=num_channels, chunk_size=chunks)
    ng.init_precomputed(OUTPUT_DIR, volume_size, progress_id=progress_id)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        if num_channels == 1:
            executor.map(ng.process_image, sorted(file_keys))
        else:
            executor.map(ng.process_3channel, sorted(file_keys))
    ng.precomputed_vol.cache.flush()

def create_neuroglancer_lite(downsample,INPUT,OUTPUT_DIR):
    scales = get_scales('DK39',downsample)
    midfile,file_keys,volume_size,num_channels = get_file_information(INPUT)
    chunks = calculate_chunks(downsample, -1)
    ng = NumpyToNeuroglancer('Atlas', None, scales, 'image', midfile.dtype, num_channels=num_channels, chunk_size=chunks)
    ng.init_precomputed(OUTPUT_DIR, volume_size, progress_id=None)
    with ProcessPoolExecutor(max_workers=10) as executor:
        executor.map(ng.process_image, sorted(file_keys))