"""
Creates a 3D Mesh
"""
import argparse
import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from cloudvolume import CloudVolume
import shutil
import numpy as np
from pathlib import Path
import pandas as pd


PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from library.image_manipulation.filelocation_manager import FileLocationManager

# from library.controller.sql_controller import SqlController
from library.image_manipulation.neuroglancer_manager import NumpyToNeuroglancer
from library.utilities.utilities_process import get_hostname, read_image

def get_labels_from_csv(csvfile):
    df = pd.read_csv(csvfile)
    print(df.head(2))
    return pd.Series(df.acronym.values + ": " + df.name.values,index=df.id).to_dict()


def create_mesh(atlas):
    HOME = os.path.expanduser("~")    
    chunks = (64, 64, 64)
    INPUT = os.path.join(HOME, ".brainglobe/allen_mouse_25um_v1.2")
    volume_file = os.path.join(INPUT, 'annotation.tiff')
    csvfile = os.path.join(INPUT, 'structures.csv')
    if not os.path.exists(volume_file):
        print(f'Volume does not exist at {volume_file}')
        return
    scales = (25000, 25000, 25000)
    infile = os.path.join(INPUT, volume_file)
    volume = read_image(infile)    
    print(f'Volume: {infile} dtype={volume.dtype}, shape={volume.shape}')
    print(f'Initial chunks at {chunks} and chunks for downsampling={chunks} and scales with {scales}')
    segment_properties = get_labels_from_csv(csvfile)
    for k,v in segment_properties.items():
        if k == 661:
            print(k,v)
    outpath = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures"
    MESH_DIR = os.path.join(outpath, atlas)
    PROGRESS_DIR = os.path.join(outpath, 'progress', atlas)
    if 'godzilla' in get_hostname() or 'mothra' in get_hostname():
        outpath = "/home/httpd/html/data"
        print(f'Cleaning {MESH_DIR}')
        if os.path.exists(MESH_DIR):
            shutil.rmtree(MESH_DIR)

    os.makedirs(MESH_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    
    
    ng = NumpyToNeuroglancer(atlas, volume, scales, layer_type='segmentation', 
        data_type=volume.dtype, chunk_size=chunks)

    ng.init_volume(MESH_DIR)
    cloudpath2 = f'file://{MESH_DIR}'
    ##### add segment properties
    print('Adding segment properties')
    cv2 = CloudVolume(cloudpath2, 0)
    ng.add_segment_properties(cv2, segment_properties)
    ##### first mesh task, create meshing tasks
    print(f'Creating meshing tasks on volume from {cloudpath2}')
    ##### first mesh task, create meshing tasks
    ng.add_segmentation_mesh(cv2.layer_cloudpath, mip=0)
    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on atlas')
    parser.add_argument('--atlas', help='Enter the atlas', required=True)
    args = parser.parse_args()
    atlas = args.atlas

    create_mesh(atlas)

