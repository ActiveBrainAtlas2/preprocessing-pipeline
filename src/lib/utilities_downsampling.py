import os
import sys
from cloudvolume import CloudVolume
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from lib.file_location import FileLocationManager
from lib.utilities_cvat_neuroglancer import calculate_chunks, calculate_factors
from lib.utilities_process import get_cpus

def create_downsamples(animal, channel, downsample):
    fileLocationManager = FileLocationManager(animal)
    channel_outdir = f'C{channel}'
    first_chunk = calculate_chunks(downsample, 0)
    mips = [0,1,2,3,4,5,6,7]

    if downsample:
        channel_outdir += 'T'
        mips = [0]
 

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')
    if os.path.exists(OUTPUT_DIR):
        print(f'DIR {OUTPUT_DIR} already exists and not performing any downsampling.')
        return
    
    outpath = f'file://{OUTPUT_DIR}'

    channel_outdir += "_rechunkme"
    INPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')

    if not os.path.exists(INPUT_DIR):
        print(f'DIR {INPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{INPUT_DIR}"
    _, workers = get_cpus()
    tq = LocalTaskQueue(parallel=workers)

    tasks = tc.create_transfer_tasks(cloudpath, dest_layer_path=outpath, 
        chunk_size=first_chunk, mip=0, skip_downsamples=True)
    tq.insert(tasks)
    tq.execute()

    #mips = 7 shows good results in neuroglancer
    for mip in mips:
        cv = CloudVolume(outpath, mip)
        chunks = calculate_chunks(downsample, mip)
        factors = calculate_factors(downsample, mip)
        tasks = tc.create_downsampling_tasks(cv.layer_cloudpath, mip=mip, num_mips=1, factor=factors, preserve_chunk_size=False,
            compress=True, chunk_size=chunks)
        tq.insert(tasks)
        tq.execute()
