"""
This takes the image stack that has section to section alignment
and creates the neuroglancer precomputed volume. It works on thumbnails by default and
works by channel
"""
import argparse
import os, sys
import json
import shutil
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
import numpy as np

from skimage import io
from neuroglancer_scripts.scripts import (generate_scales_info,
                                          slices_to_precomputed,
                                          compute_scales)

from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_cpus, get_segment_ids


def create_mesh(animal):
    """
    Takes the directory with aligned images and creates a new directory available
    to the internet. Uses resolution from database and 20000 as width of section
    in nanometers.
    :param folder_to_convert_from: list of aligned and cleaned images
    :param folder_to_convert_to: neuroglancer folder available to the web
    :param resolution: either full or thumbnail
    :return: nothing
    """
    fileLocationManager = FileLocationManager(animal)
    scale = 3
    resolution = 1000 * scale
    voxel_resolution = [resolution, resolution, resolution]
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

    # make a folder under the "precomputed" dir and execute conversion routine
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/small')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    img = io.imread(midfilepath)


    # read 1 image to get the shape
    # write info_fullres.json
    info_fullres = info_fullres_template.copy()
    info_fullres['scales'][0]['size'] = [img.shape[1], img.shape[0], len(files)]
    info_fullres['scales'][0]['resolution'] = voxel_resolution
    info_fullres['num_channels'] = img.shape[2] if len(img.shape) > 2 else 1
    info_fullres['data_type'] = str(img.dtype)
    with open(os.path.join(OUTPUT_DIR, 'info_fullres.json'), 'w') as outfile:
        json.dump(info_fullres, outfile)
    del img
    # --- neuroglancer-scripts routine ---
    #  generate_scales_info - make info.json
    generate_scales_info.main(['', os.path.join(OUTPUT_DIR, 'info_fullres.json'),
                               OUTPUT_DIR])
    # slices_to_precomputed - build the precomputed for the fullress
    slices_to_precomputed.main(['', INPUT, OUTPUT_DIR, '--flat', '--no-gzip'])
    # compute_scales - build the precomputed for other scales
    compute_scales.main(['', OUTPUT_DIR, '--flat', '--no-gzip'])

    info = os.path.join(OUTPUT_DIR, 'info')

    print('Done computing scales')
    layer_cloudpath = f"file:///net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/neuroglancer_data/mesh"
    with open(info, 'r+') as rf:
        data = json.load(rf)
        data['segment_properties'] = 'names'
        data['type'] = 'segmentation'
        rf.seek(0)  # <--- should reset file position to the beginning.
    with open(info, 'w') as wf:
        json.dump(data, wf, indent=4)

    fake_volume = np.zeros(3) + 255
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
    tasks = tc.create_meshing_tasks(layer_cloudpath, mip=0,compress=False)  # The first phase of creating mesh
    tq.insert(tasks)
    tq.execute()
    tasks = tc.create_mesh_manifest_tasks(layer_cloudpath)  # The second phase of creating mesh
    tq.insert(tasks)
    tq.execute()
1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_mesh(animal)
