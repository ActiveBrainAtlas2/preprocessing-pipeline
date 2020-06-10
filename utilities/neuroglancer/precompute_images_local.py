import argparse
import os
import json
from skimage import io
from neuroglancer_scripts.scripts import (generate_scales_info,
                                          slices_to_precomputed,
                                          compute_scales)

from os.path import expanduser
HOME = expanduser("~")


def convert_to_precomputed(folder_to_convert_from, folder_to_convert_to):

    # ---------------- Conversion to precomputed format ----------------
    voxel_resolution=[460, 460, 20000]
    voxel_offset=[0, 0, 0]

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
    if not os.path.isdir(folder_to_convert_from):
        raise NotADirectoryError
    # make a corresponding folder in the "precomputed_dir"
    if not os.path.exists(folder_to_convert_to):
        os.makedirs(folder_to_convert_to)
    # read 1 image to get the shape
    imgs = os.listdir(folder_to_convert_from)
    img = io.imread(os.path.join(folder_to_convert_from, imgs[0]))
    # write info_fullres.json
    info_fullres = info_fullres_template.copy()
    info_fullres['scales'][0]['size'] = [img.shape[1], img.shape[0], len(imgs)]
    info_fullres['scales'][0]['resolution'] = voxel_resolution
    info_fullres['num_channels'] = img.shape[2] if len(img.shape) > 2 else 1
    info_fullres['data_type'] = str(img.dtype)
    with open(os.path.join(folder_to_convert_to, 'info_fullres.json'), 'w') as outfile:
        json.dump(info_fullres, outfile)

    # --- neuroglancer-scripts routine ---
    #  generate_scales_info - make info.json
    generate_scales_info.main(['', os.path.join(folder_to_convert_to, 'info_fullres.json'),
                               folder_to_convert_to])
    # slices_to_precomputed - build the precomputed for the fullress
    slices_to_precomputed.main(
        ['', folder_to_convert_from, folder_to_convert_to, '--flat', '--no-gzip'])
    # compute_scales - build the precomputed for other scales
    compute_scales.main(['', folder_to_convert_to, '--flat', '--no-gzip'])



def run_neuroglancer(animal, channel, resolution):
    channel_dir = 'CH{}'.format(channel)
    channel_outdir = 'C{}'.format(channel)
    if 'thumb' in resolution.lower():
        channel_outdir = 'C{}T'.format(channel)
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}'.format(animal)
    INPUT = os.path.join(DIR, 'preps', channel_dir, 'aligned')
    NEUROGLANCER =  os.path.join(DIR, 'neuroglancer_data', '{}'.format(channel_outdir))
    print(INPUT)
    print(NEUROGLANCER)
    convert_to_precomputed(INPUT, NEUROGLANCER)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--resolution', help='Enter full or thumbnail', required=True)
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    resolution = args.resolution
    run_neuroglancer(animal, channel, resolution)

