"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
import numpy as np

from taskqueue import LocalTaskQueue
import igneous.task_creation as tc


HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_cpus

def create_mesh(animal, mip):
    fileLocationManager = FileLocationManager(animal)
    channel_outdir = 'mesh'
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, channel_outdir)
    if not os.path.exists(OUTPUT_DIR):
        print(f'DIR {OUTPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{OUTPUT_DIR}"
    workers = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    tasks = tc.create_meshing_tasks(cloudpath, mip=mip)
    tq.insert(tasks)
    tq.execute()
    tasks = tc.create_mesh_manifest_tasks(cloudpath)
    tq.insert(tasks)
    tq.execute()
    print("Done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--mip', help='Enter the mip', required=True)
    args = parser.parse_args()
    animal = args.animal
    mip = int(args.mip)
    create_mesh(animal, mip)

