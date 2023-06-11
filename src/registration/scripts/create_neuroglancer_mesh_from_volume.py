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

def get_labels_from_csv(csvfile, ids):
    df = pd.read_csv(csvfile)
    print(df.head())
    labels = {}
    for id in ids:
        row = df.loc[df['id'] == id]
        acronym = row.iat[0, 1]
        description = row.iat[0,4]
        labels[id] = f"{acronym}: {description}" 
    return labels


def create_mesh():
    HOME = os.path.expanduser("~")    
    chunks = (64, 64, 64)
    INPUT = os.path.join(HOME, ".brainglobe/allen_mouse_25um_v1.2")
    volume_file = os.path.join(INPUT, 'annotation.tiff')
    csvfile = os.path.join(INPUT, 'structures.csv')
    outpath = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures"
    MESH_DIR = os.path.join(outpath, 'allen')
    PROGRESS_DIR = os.path.join(outpath, 'progress', 'allen')
    scales = (25000, 25000, 25000)
    if 'godzilla' in get_hostname():
        print(f'Cleaning {MESH_DIR}')
        if os.path.exists(MESH_DIR):
            shutil.rmtree(MESH_DIR)

    os.makedirs(MESH_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)

    infile = os.path.join(INPUT, volume_file)
    volume = read_image(infile)
    
    ids, counts = np.unique(volume, return_counts=True)

    data_type = volume.dtype
    
    print()
    print(f'Volume: {infile} dtype={data_type}, shape={volume.shape}')
    print(f'Initial chunks at {chunks} and chunks for downsampling={chunks} and scales with {scales}')
    #print(f'counts={counts}')
    segment_properties = get_labels_from_csv(csvfile, ids)
    print(segment_properties)
    return
    
    
    ng = NumpyToNeuroglancer(animal, volume, scales, layer_type='segmentation', 
        data_type=data_type, chunk_size=chunks)

    ng.init_volume(MESH_DIR)
    
    # This calls the igneous create_transfer_tasks
    #ng.add_rechunking(MESH_DIR, chunks=chunks, mip=0, skip_downsamples=True)

    #tq = LocalTaskQueue(parallel=4)
    cloudpath2 = f'file://{MESH_DIR}'
    #ng.add_downsampled_volumes(chunk_size = chunks, num_mips = 1)

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
    
    create_mesh()

