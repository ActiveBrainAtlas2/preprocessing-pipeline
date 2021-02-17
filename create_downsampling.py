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
from utilities.utilities_cvat_neuroglancer import get_cpus

def create_downsamples(animal, channel, downsample):
    fileLocationManager = FileLocationManager(animal)
    channel_outdir = 'C{}T'.format(channel)
    mips = 5
    chunk = 64
    zchunk = chunk

    if downsample == 'full':
        channel_outdir = 'C{}'.format(channel)
        mips = 8
        chunk = 128
        zchunk = 64

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')

    if not os.path.exists(OUTPUT_DIR):
        print(f'DIR {OUTPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{OUTPUT_DIR}"
    cv = CloudVolume(cloudpath, 0)
    workers = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    tasks = tc.create_downsampling_tasks(cv.layer_cloudpath, num_mips=mips, mip=2, compress=True, chunk_size=[chunk,chunk,zchunk])
    tq.insert(tasks)
    tq.execute()

    print("Done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--downsample', help='Enter full or thumbnail', required=False, default='thumbnail')
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    downsample = args.downsample
    create_downsamples(animal, channel, downsample)

