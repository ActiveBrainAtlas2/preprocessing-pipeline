"""
Creates a shell from  aligned thumbnails
"""
import os
import argparse
from skimage import io
from concurrent.futures.process import ProcessPoolExecutor

from lib.FileLocationManager import FileLocationManager
from controller.sql_controller import SqlController
from utilities.utilities_process import get_cpus, SCALING_FACTOR
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, calculate_chunks



def get_scales(animal,downsample):
    sqlController = SqlController(animal)
    db_resolution = sqlController.scan_run.resolution
    resolution = int(db_resolution * 1000 / SCALING_FACTOR)
    if not downsample:
        resolution = int(db_resolution * 1000)
    scales = (resolution, resolution, 20000)
    return scales


def get_file_information(INPUT, progress_dir):
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
        file_keys.append([i,filepath, None, progress_dir])
    return midfile,file_keys,volume_size,num_channels



def create_neuroglancer(animal, channel, downsample, debug=False):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = f'CH{channel}'
    channel_outdir = f'C{channel}T_rechunkme'
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'boundary')
    scales = get_scales(animal,downsample)
    workers, _ = get_cpus()
    chunks = calculate_chunks(downsample, -1)
    sqlController.session.close()
    if not downsample:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
        channel_outdir = f'C{channel}_rechunkme'
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')
    PROGRESS_DIR = fileLocationManager.get_neuroglancer_progress(downsample, 1)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    midfile,file_keys,volume_size,num_channels = get_file_information(INPUT, PROGRESS_DIR)
    ng = NumpyToNeuroglancer(animal, None, scales, 'image', midfile.dtype, num_channels=num_channels, chunk_size=chunks)
    ng.init_precomputed(OUTPUT_DIR, volume_size)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        if num_channels == 1:
            executor.map(ng.process_image, sorted(file_keys))
        else:
            executor.map(ng.process_3channel, sorted(file_keys))
    ng.precomputed_vol.cache.flush()





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=False, default=1)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--debug', help='Enter debug True|False', required=False, default='false')

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_neuroglancer(animal, channel, downsample, debug)

