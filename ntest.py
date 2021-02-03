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

from skimage import io
from timeit import default_timer as timer
from neuroglancer_scripts.scripts import (generate_scales_info,
                                          slices_to_precomputed,
                                          compute_scales)

from utilities.file_location import FileLocationManager


def setup_input_dir(source_dir, output_dir):

    if os.path.exists(output_dir):
        print(f'Directory: {output_dir} exists.')
        shutil.rmtree(output_dir)

    scale = 3
    os.makedirs(output_dir, exist_ok=True)
    files = sorted(os.listdir(source_dir))
    files = [f for i,f in enumerate(files) if i % scale == 0]
    for f in files:
        source = os.path.join(source_dir, f)
        img = io.imread(source)
        img = (img * 1).astype('uint8')
        outpath = os.path.join(output_dir, f)
        cv2.imwrite(outpath, img)




def convert_to_precomputed(INPUT, OUTPUT_DIR):
    """
    Takes the directory with aligned images and creates a new directory available
    to the internet. Uses resolution from database and 20000 as width of section
    in nanometers.
    :param INPUT: list of aligned and cleaned images
    :param OUTPUT_DIR: neuroglancer folder available to the web
    :param resolution: either full or thumbnail
    :return: nothing
    """
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
        shutil.rmtree(OUTPUT_DIR)
        #sys.exit()

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
    slices_to_precomputed.main(
        ['', INPUT, OUTPUT_DIR, '--flat', '--no-gzip'])
    # compute_scales - build the precomputed for other scales
    compute_scales.main(['', OUTPUT_DIR, '--flat', '--no-gzip'])

def run_neuroglancer(animal, channel):
    fileLocationManager = FileLocationManager(animal)
    channel_dir = 'CH{}'.format(channel)
    source_dir = os.path.join(fileLocationManager.prep, channel_dir, 'downsampled_33')
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail_aligned')
    setup_input_dir(source_dir, INPUT)
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    convert_to_precomputed(INPUT, OUTPUT_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=False, default=1)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    run_neuroglancer(animal, channel)
