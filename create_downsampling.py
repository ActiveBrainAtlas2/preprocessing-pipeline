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

    if downsample == 'thumbnail':
        channel_outdir += 'T'

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')

    if not os.path.exists(OUTPUT_DIR):
        print(f'DIR {OUTPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{OUTPUT_DIR}"
    workers, _ = get_cpus()
    tq = LocalTaskQueue(parallel=workers)

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

