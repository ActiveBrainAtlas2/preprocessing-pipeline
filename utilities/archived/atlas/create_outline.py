"""
Creates a shell from  aligned thumbnails
"""
import argparse
import os
import sys
import numpy as np
from timeit import default_timer as timer
import shutil
from skimage import io
import tinybrain
from cloudvolume import CloudVolume
from tqdm import tqdm


HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import mask_to_shell

def create_shell(animal):
    start = timer()
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_aligned')
    OUTPUT = os.path.join(fileLocationManager.neuroglancer_data, 'shell')
    if os.path.exists(OUTPUT):
        shutil.rmtree(OUTPUT)
    os.makedirs(OUTPUT, exist_ok=True)

    files = sorted(os.listdir(INPUT))

    volume = []
    for file in tqdm(files):
        tif = io.imread(os.path.join(INPUT, file))
        tif = mask_to_shell(tif)
        volume.append(tif)
    volume = np.array(volume).astype('uint8')
    volume = np.swapaxes(volume, 0, 2)

    """
    factor = (2, 2, 1)
    volumes = tinybrain.downsample_segmentation(volume, factor=factor, num_mips=2, sparse=False)
    volumes.insert(0, volume)
    planar_resolution = sqlController.scan_run.resolution
    resolution = int(planar_resolution * 1000 / 0.03125)

    info = CloudVolume.create_new_info(
        num_channels=1,
        layer_type='segmentation',
        data_type='uint8',  # Channel images might be 'uint8'
        encoding='raw',  # raw, jpeg, compressed_segmentation, fpzip, kempressed
        resolution=[resolution, resolution, 20000],  # Voxel scaling, units are in nanometers
        voxel_offset=[0, 0, 0],  # x,y,z offset in voxels from the origin
        chunk_size=[512, 512, 16],  # units are voxels
        volume_size=volume.shape,  # e.g. a cubic millimeter dataset
    )

    path = 'file://' + OUTPUT

    vol = CloudVolume(path, info=info, compress=False, progress=False)

    for mip, volume in enumerate(volumes):
        vol.add_scale(np.array(factor) ** mip)
        vol.commit_info()
        vol = CloudVolume(path, mip=mip, compress=False, progress=False)
        vol[:, :, :] = volume[:, :, :]

    vol.commit_info()
    """
    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_shell(animal)

