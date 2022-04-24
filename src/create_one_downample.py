"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from cloudvolume import CloudVolume
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from lib.file_location import FileLocationManager
from lib.utilities_process import get_cpus



def create_downsample(animal, channel, mip, transfer):
    fileLocationManager = FileLocationManager(animal)
    channel_outdir = f'C{channel}'
    first_chunk = [64,64,64]
 
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')
    outpath = f'file://{OUTPUT_DIR}'

    channel_outdir += "_rechunkme"
    INPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')

    if not os.path.exists(INPUT_DIR):
        print(f'DIR {INPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{INPUT_DIR}"
    _, workers = get_cpus()
    tq = LocalTaskQueue(parallel=workers)

    if transfer:
        tasks = tc.create_transfer_tasks(cloudpath, dest_layer_path=outpath, 
            chunk_size=first_chunk, mip=0, skip_downsamples=True)
        tq.insert(tasks)
        tq.execute()

    cv = CloudVolume(outpath, mip)
    chunks = [64,64,64]
    factors = [2,2,1]
    tasks = tc.create_downsampling_tasks(cv.layer_cloudpath, mip=mip, num_mips=1, factor=factors,
        compress=True, chunk_size=chunks)
    tq.insert(tasks)
    tq.execute()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--mip', help='Enter mip', required=True)
    parser.add_argument('--transfer', help='Enter bool transfer', required=True)
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    mip = int(args.mip)
    transfer = bool({'true': True, 'false': False}[str(args.transfer).lower()])
    create_downsample(animal, channel, mip, transfer)

