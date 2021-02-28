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

def create_mesh(animal, mip, mse):
    fileLocationManager = FileLocationManager(animal)
    channel_outdir = 'color_mesh'
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, channel_outdir)
    if not os.path.exists(OUTPUT_DIR):
        print(f'DIR {OUTPUT_DIR} does not exist, exiting.')
        sys.exit()

    cloudpath = f"file://{OUTPUT_DIR}"
    cv = CloudVolume(cloudpath, mip)
    workers, _ = get_cpus()
    tq = LocalTaskQueue(parallel=workers)
    mesh = True
    if mesh:
        mesh_dir = f'mesh_mip_{mip}_err_{mse}'
        cv.info['mesh'] = mesh_dir
        cv.commit_info()
        tasks = tc.create_meshing_tasks(cv.layer_cloudpath, mip=mip, mesh_dir=mesh_dir, max_simplification_error=mse)
        tq.insert(tasks)
        tq.execute()
        tasks = tc.create_mesh_manifest_tasks(cv.layer_cloudpath, mesh_dir=mesh_dir)
        tq.insert(tasks)
        tq.execute()
    else:
        tasks = tc.create_skeletonizing_tasks(cv.layer_cloudpath,mip)
        #tq.insert(tasks)
        #tq.execute()


    print("Done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--mip', help='Enter the mip', required=False, default=0)
    parser.add_argument('--mse', help='Enter the mse', required=False, default=40)
    args = parser.parse_args()
    animal = args.animal
    mip = int(args.mip)
    mse = int(args.mse)
    create_mesh(animal, mip, mse)

