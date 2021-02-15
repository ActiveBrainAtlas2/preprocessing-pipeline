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

    if downsample == 'full':
        channel_outdir = 'C{}'.format(channel)

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'{channel_outdir}')

    if not os.path.exists(OUTPUT_DIR):
        print(f'DIR {OUTPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{OUTPUT_DIR}"
    workers = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    tasks = tc.create_downsampling_tasks(cloudpath, chunk_size=[256,256,128], compress=True)
    tq.insert(tasks)
    tq.execute()

    print("Done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_downsamples(animal)

