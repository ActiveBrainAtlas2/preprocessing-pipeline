"""
This takes the image stack that has section to section alignment
and creates the neuroglancer precomputed volume. It works on thumbnails by default and
works by channel
"""
import argparse
import os, sys
import json
import shutil
import cv2
import numpy as np

from skimage import io
from timeit import default_timer as timer
from neuroglancer_scripts.scripts import (generate_scales_info,
                                          slices_to_precomputed,
                                          compute_scales)

from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_cpus, get_segment_ids
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc

def setup_input_dir(source_dir, output_dir):

    if os.path.exists(output_dir):
        print(f'Directory: {output_dir} exists.')
        shutil.rmtree(output_dir)

    scale = 10
    os.makedirs(output_dir, exist_ok=True)
    files = sorted(os.listdir(source_dir))
    files = [f for i,f in enumerate(files) if i % scale == 0]
    for f in files:
        source = os.path.join(source_dir, f)
        img = io.imread(source)
        img = (img * 255).astype('uint8')
        outpath = os.path.join(output_dir, f)
        cv2.imwrite(outpath, img)




def create_mesh():
    animal = 'X'
    fileLocationManager = FileLocationManager(animal)
    channel_dir = 'CH1'
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh_v1')
    scale = 3
    resolution = 1000*scale
    voxel_resolution = [resolution, resolution, resolution]
    print(voxel_resolution)
    voxel_offset = [0, 0, 0]

    info_fullres_template = {
        "type": "image",
        "num_channels": None,
        "scales": [{
            "chunk_sizes": [],
            "encoding": "raw",
            "key": "full",
            "resolution": [None, None, None],
            "size": [None, None, None],
            "voxel_offset": voxel_offset}],
        "data_type": None}

    files = os.listdir(INPUT)
    img = io.imread(os.path.join(INPUT, files[0]))
    if os.path.exists(OUTPUT_DIR):
        print(f'Directory: {OUTPUT_DIR} exists.')
        sys.exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # write info_fullres.json
    info_fullres = info_fullres_template.copy()
    info_fullres['scales'][0]['size'] = [img.shape[1], img.shape[0], len(files)]
    info_fullres['scales'][0]['resolution'] = voxel_resolution
    info_fullres['num_channels'] = img.shape[2] if len(img.shape) > 2 else 1
    info_fullres['data_type'] = str(img.dtype)
    info_fullres['type'] = 'segmentation'
    with open(os.path.join(OUTPUT_DIR, 'info_fullres.json'), 'w') as outfile:
        json.dump(info_fullres, outfile)

    # --- neuroglancer-scripts routine ---
    #  generate_scales_info - make info.json
    jsonpath = os.path.join(OUTPUT_DIR, 'info_fullres.json')
    generate_scales_info.main(['',  jsonpath, OUTPUT_DIR])
    # slices_to_precomputed - build the precomputed for the fullress
    slices_to_precomputed.main(['', INPUT, OUTPUT_DIR, '--flat'])
    # compute_scales - build the precomputed for other scales
    compute_scales.main(['', OUTPUT_DIR, '--flat'])
    layer_cloudpath = f"file:///net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/neuroglancer_data/mesh"
    fake_volume = np.zeros((1,1), dtype=np.uint8) + 255
    segment_properties = get_segment_ids(fake_volume)
    segment_properties_path = os.path.join(layer_cloudpath.replace('file://', ''), 'names')
    os.makedirs(segment_properties_path, exist_ok=True)

    info = {
        "@type": "neuroglancer_segment_properties",
        "inline": {
            "ids": [str(number) for number, label in segment_properties],
            "properties": [{
                "id": "label",
                "type": "label",
                "values": [str(label) for number, label in segment_properties]
            }]
        }
    }
    with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
        json.dump(info, file, indent=2)

    cpus = get_cpus()
    tq = LocalTaskQueue(parallel=cpus)
    tasks = tc.create_meshing_tasks(layer_cloudpath, mip=0,compress=True)  # The first phase of creating mesh
    tq.insert(tasks)
    tq.execute()
    tasks = tc.create_mesh_manifest_tasks(layer_cloudpath)  # The second phase of creating mesh
    tq.insert(tasks)
    tq.execute()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Work on Animal')
    source = ''
    dest = ''
    create_mesh()
