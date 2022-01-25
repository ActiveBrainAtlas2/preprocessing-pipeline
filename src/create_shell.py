"""
Creates a shell from  aligned masks
"""
import argparse
import os
import sys
import numpy as np
import shutil
from skimage import io, measure
import cv2
import json
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
from tqdm import tqdm


from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from lib.utilities_process import test_dir, SCALING_FACTOR


def mask_to_shell(mask):
    '''
    Takes in a binary mask file, gets the contours
    and returns an outline of the brain.
    :param mask: the binary tif file: mask
    '''
    sub_contours = measure.find_contours(mask, 1)

    sub_shells = []
    for sub_contour in sub_contours:
        sub_contour.T[[0, 1]] = sub_contour.T[[1, 0]]
        pts = sub_contour.astype(np.int32).reshape((-1, 1, 2))
        sub_shell = np.zeros(mask.shape, dtype='uint8')
        sub_shell = cv2.polylines(sub_shell, [pts], True, 1, 5, lineType=cv2.LINE_AA)
        sub_shells.append(sub_shell)
    shell = np.array(sub_shells).sum(axis=0)
    del sub_shells
    return shell

class NumpyToNeuroglancer():
    '''
    This should be replaced with the class from lib/utilities_cvat_neuroglancer.py
    '''

    def __init__(self, volume, scales, offset=[0, 0, 0], layer_type='segmentation'):
        self.volume = volume
        self.scales = scales
        self.offset = offset
        self.layer_type = layer_type
        self.precomputed_vol = None

    def init_precomputed(self, path):
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[3] if len(self.volume.shape) > 3 else 1,
            layer_type = self.layer_type,
            data_type = str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',                    # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset,          # x,y,z offset in voxels from the origin
            chunk_size = [64, 64, 64],           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=False)
        self.precomputed_vol.commit_info()
        self.precomputed_vol[:, :, :] = self.volume[:, :, :]

    def add_segment_properties(self, ids):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        self.precomputed_vol.info['segment_properties'] = 'names'
        self.precomputed_vol.commit_info()

        segment_properties_path = os.path.join(self.precomputed_vol.layer_cloudpath.replace('file://', ''), 'names')
        os.makedirs(segment_properties_path, exist_ok=True)

        info = {
            "@type": "neuroglancer_segment_properties",
            "inline": {
                "ids": [str(value) for value in ids.tolist()],
                "properties": [{
                    "id": "label",
                    "type": "label",
                    "values": [str(value) for value in ids.tolist()]
                }]
            }
        }
                
        with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
            json.dump(info, file, indent=2)

    def add_downsampled_volumes(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        tq = LocalTaskQueue(parallel=4)
        tasks = tc.create_downsampling_tasks(self.precomputed_vol.layer_cloudpath, compress=True)
        tq.insert(tasks)
        tq.execute()

    def add_segmentation_mesh(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        tq = LocalTaskQueue(parallel=4)
        tasks = tc.create_meshing_tasks(self.precomputed_vol.layer_cloudpath, mip=0, compress=True) # The first phase of creating mesh
        tq.insert(tasks)
        tq.execute()

        # It should be able to incoporated to above tasks, but it will give a weird bug. Don't know the reason
        tasks = tc.create_mesh_manifest_tasks(self.precomputed_vol.layer_cloudpath) # The second phase of creating mesh
        tq.insert(tasks)
        tq.execute()



def create_shell(animal, DEBUG=False):
    '''
    Gets some info from the database used to create the numpy volume from
    the masks. It then turns that numpy volume into a neuroglancer precomputed
    mesh
    :param animal:
    :param DEBUG:
    '''
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'masks', 'rotated_aligned_masked')
    error = test_dir(animal, INPUT, downsample=True, same_size=True)
    if len(error) > 0:
        print(error)
        sys.exit()

    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'shell')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    len_files = len(files)
    midpoint = len_files // 2
    if DEBUG:
        limit = 50
        start = midpoint - limit
        end = midpoint + limit
        files = files[start:end]
    volume = []
    for file in tqdm(files):
        tif = io.imread(os.path.join(INPUT, file))
        tif = mask_to_shell(tif)
        volume.append(tif)
    volume = np.array(volume).astype('uint8')
    volume = np.swapaxes(volume, 0, 2)
    ids = np.unique(volume)

    resolution = sqlController.scan_run.resolution
    resolution = int(resolution * 1000 / SCALING_FACTOR)
    ng = NumpyToNeuroglancer(volume, [resolution, resolution, 20000], offset=[0,0,0])
    ng.init_precomputed(OUTPUT_DIR)
    ng.add_segment_properties(ids)
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_shell(animal)

