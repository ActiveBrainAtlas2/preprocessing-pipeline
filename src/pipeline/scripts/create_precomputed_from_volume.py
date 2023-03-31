"""
Creates a 3D Mesh
"""
import argparse
import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import shutil
from pathlib import Path
from cloudvolume import CloudVolume
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.image_manipulation.filelocation_manager import FileLocationManager
from library.image_manipulation.neuroglancer_manager import NumpyToNeuroglancer, calculate_chunks, calculate_factors
from library.utilities.utilities_process import get_hostname, read_image

def create_precomputed(animal, volume_file):
    chunk = 64
    chunks = (chunk, chunk, 1)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'registered')
    outpath = os.path.basename(volume_file)
    outpath = outpath.split('.')[0]
    IMAGE_INPUT = os.path.join(fileLocationManager.neuroglancer_data, f'input_{outpath}')
    scales = (20000, 20000, 20000)
    if 'godzilla' in get_hostname():
        print(f'Cleaning {IMAGE_INPUT}')
        if os.path.exists(IMAGE_INPUT):
            shutil.rmtree(IMAGE_INPUT)


    os.makedirs(IMAGE_INPUT, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = read_image(midfilepath)
    height = midfile.shape[0]
    width = midfile.shape[1]
    num_channels = midfile.shape[2] if len(midfile.shape) > 2 else 1
    volume_size = (width, height, len(files))
    print(f'\nCreating volume with shape={volume_size} and dtype={midfile.dtype}')

    ng = NumpyToNeuroglancer(
        animal,
        None,
        scales,
        "image",
        midfile.dtype,
        num_channels=num_channels,
        chunk_size=chunks,
    )



    ng.init_precomputed(IMAGE_INPUT, volume_size)
    
    for index, f in enumerate(files):
        infile = os.path.join(INPUT, f)
        img = read_image(infile)
        try:
            img = img.reshape(num_channels, img.shape[0], img.shape[1]).T
        except:
            print(f'could not reshape {infile}')
            sys.exit()
        try:
            ng.precomputed_vol[:, :, index] = img
        except Exception as e:
            print(f'{index} could not set {os.path.basename(infile)} shape={img.shape} dtype={img.dtype} to precomputed')
            print(f'{str(e)}')
            sys.exit()

    ng.precomputed_vol.cache.flush()

    # now create downsamples
    OUTPUT = os.path.join(fileLocationManager.neuroglancer_data, outpath)

    outpath = f"file://{OUTPUT}"
    if not os.path.exists(IMAGE_INPUT):
        print(f"DIR {IMAGE_INPUT} does not exist, exiting.")
        sys.exit()
    cloudpath = f"file://{IMAGE_INPUT}"
    workers = 4
    tq = LocalTaskQueue(parallel=workers)
    tasks = tc.create_transfer_tasks(
        cloudpath,
        dest_layer_path=outpath,
        chunk_size=[chunk, chunk, chunk],
        mip=0,
        skip_downsamples=True,
    )
    tq.insert(tasks)
    tq.execute()
    
    mips = [0,1,2]
    for mip in mips:
        cv = CloudVolume(outpath, mip)
        chunks = calculate_chunks(True, mip)
        factors = calculate_factors(True, mip)
        tasks = tc.create_downsampling_tasks(
            cv.layer_cloudpath,
            mip=mip,
            num_mips=1,
            factor=factors,
            preserve_chunk_size=False,
            compress=True,
            chunk_size=chunks,
        )
        tq.insert(tasks)
        tq.execute()



    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--volume', help='Enter the name of the volume file', required=False, default='downsampled_standard.tiff')
    args = parser.parse_args()
    animal = args.animal
    volume = args.volume
    
    create_precomputed(animal, volume)

