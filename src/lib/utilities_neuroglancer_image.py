import os
import sys
from concurrent.futures.process import ProcessPoolExecutor

from skimage import io
from timeit import default_timer as timer


HOME = os.path.expanduser("~")
#PATH = os.path.join(HOME, 'programming/pipeline_utility')
#sys.path.append(PATH)
from lib.file_location import FileLocationManager
from lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer, calculate_chunks
from lib.sqlcontroller import SqlController
from sql_setup import RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES
from lib.utilities_process import get_cpus, SCALING_FACTOR, test_dir

def create_neuroglancer(animal, channel, downsample, workers,debug=False):
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    channel_dir = f'CH{channel}'
    channel_outdir = f'C{channel}T_rechunkme'
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    db_resolution = sqlController.scan_run.resolution
    resolution = int(db_resolution * 1000 / SCALING_FACTOR)
    workers, _ = get_cpus()
    chunks = calculate_chunks(downsample, -1)
    progress_id = sqlController.get_progress_id(downsample, channel, 'NEUROGLANCER')
    sqlController.session.close()
    if not downsample:
        INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'full_aligned')
        channel_outdir = f'C{channel}_rechunkme'
        sqlController.set_task(animal, progress_id)

        if 'thion' in sqlController.histology.counterstain:
            sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES)
            sqlController.set_task(animal, RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES)

        resolution = int(db_resolution * 1000)

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')

    error = test_dir(animal, INPUT, downsample, same_size=True)
    if len(error) > 0 and not debug:
        print(error)
        sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = io.imread(midfilepath, img_num=0)
    height = midfile.shape[0]
    width = midfile.shape[1]
    num_channels = midfile.shape[2] if len(midfile.shape) > 2 else 1
    file_keys = []
    scales = (resolution, resolution, 20000)
    volume_size = (width, height, len(files))
    print('Volume shape:', volume_size)

    ng = NumpyToNeuroglancer(animal, None, scales, 'image', midfile.dtype, num_channels=num_channels, chunk_size=chunks)
    ng.init_precomputed(OUTPUT_DIR, volume_size, progress_id=progress_id)

    for i, f in enumerate(files):
        filepath = os.path.join(INPUT, f)
        file_keys.append([i,filepath])
        #ng.process_3channel([i, filepath])
    #sys.exit()

    start = timer()
    print(f'Working on {len(file_keys)} files with {workers} cpus')
    with ProcessPoolExecutor(max_workers=workers) as executor:
        if num_channels == 1:
            executor.map(ng.process_image, sorted(file_keys))
        else:
            executor.map(ng.process_3channel, sorted(file_keys))


    end = timer()
    print(f'Create volume method took {end - start} seconds')
    ng.precomputed_vol.cache.flush()