"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
from cloudvolume import CloudVolume

from taskqueue import LocalTaskQueue
import igneous.task_creation as tc


HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import calculate_chunks, calculate_factors, get_cpus

def create_downsamples(animal, channel, mips, downsample):
    fileLocationManager = FileLocationManager(animal)
    channel_outdir = f'C{channel}'
    first_chunk = [128,128,64]

    if downsample == 'thumbnail':
        channel_outdir += 'T'
        first_chunk = [64,64,64]

    outpath = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')
    outpath = f'file://{outpath}'

    channel_outdir += "_rechunkme"
    INPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')

    if not os.path.exists(INPUT_DIR):
        print(f'DIR {INPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{INPUT_DIR}"
    workers, _ = get_cpus()
    tq = LocalTaskQueue(parallel=workers)

    tasks = tc.create_transfer_tasks(cloudpath, dest_layer_path=outpath, 
        chunk_size=first_chunk, mip=0, skip_downsamples=False, preserve_chunk_size=False)
    tq.insert(tasks)
    tq.execute()

    sys.exit()



    loop = False

    if loop:
        for mip in range(0, mips):
            cv = CloudVolume(cloudpath, mip)
            chunks = calculate_chunks(downsample, mip)
            factors = calculate_factors(downsample, mip)
            tasks = tc.create_downsampling_tasks(cv.layer_cloudpath, mip=mip, num_mips=1, factor=factors, preserve_chunk_size=False,
                compress=True, chunk_size=chunks)
            tq.insert(tasks)
            tq.execute()
    else:
        cv = CloudVolume(cloudpath, mips)
        chunks = calculate_chunks(downsample, mips)
        factors = calculate_factors(downsample, mips)
        tasks = tc.create_downsampling_tasks(cv.layer_cloudpath, mip=mips, num_mips=1, factor=factors, preserve_chunk_size=False,
            compress=True, chunk_size=chunks)
        tq.insert(tasks)
        tq.execute()

    
    print("Done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--mips', help='Enter mips', required=True)
    parser.add_argument('--downsample', help='Enter full or thumbnail', required=False, default='thumbnail')
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    mips = int(args.mips)
    downsample = args.downsample
    create_downsamples(animal, channel, mips, downsample)

