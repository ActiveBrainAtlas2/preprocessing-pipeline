
import os, sys

import cv2
from skimage import img_as_ubyte, io
from skimage.color import rgb2gray
import numpy as np
import argparse

HOME = os.path.expanduser("~")
sys.path.append(os.path.join(HOME, 'programming/pipeline_utility'))
from utilities.alignment_utility import convert_resolution_string_to_um
from utilities.imported_atlas_utilities import load_cropbox_v2, images_to_volume_v2, get_original_volume_filepath_v2, \
    get_original_volume_origin_filepath_v3

from utilities.file_location import FileLocationManager

images = {}

def create_volume(animal):


    output_resolution = '10.0um'
    tb_resol = 'thumbnail'

    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_aligned')
    files = sorted(os.listdir(INPUT))
    MASK  = os.path.join(fileLocationManager.prep, 'thumbnail_masked_aligned')
    #     for sec in metadata_cache['valid_sections_all'][stack]:
    section = 1
    for infile in files:

        img_rgb = os.path.join(INPUT, infile)
        img = cv2.imread(img_rgb, cv2.IMREAD_GRAYSCALE)
        #maskfile = os.path.join(MASK, infile)
        #mask = io.imread(maskfile)

        #img[~mask] = 0
        images[section] = img
        section += 1

    # Specify isotropic resolution of the output volume.
    voxel_size_um = convert_resolution_string_to_um(animal, output_resolution)
    input_image_resolution_um = convert_resolution_string_to_um(animal, tb_resol)
    volume_outVolResol, volume_origin_wrt_wholebrainWithMargin_outVolResol = images_to_volume_v2(images=images,
                                                spacing_um=20.,
                                                in_resol_um=input_image_resolution_um,
                                                out_resol_um=voxel_size_um)

    prep5_origin_wrt_prep1_tbResol = load_cropbox_v2(stack=animal, only_2d=True, prep_id='alignedWithMargin')
    loaded_cropbox_resol = 'thumbnail'
    prep5_origin_wrt_prep1_outVolResol = prep5_origin_wrt_prep1_tbResol * \
    convert_resolution_string_to_um(stack=animal, resolution=loaded_cropbox_resol) / voxel_size_um
    wholebrainWithMargin_origin_wrt_wholebrain_outVolResol = np.r_[np.round(prep5_origin_wrt_prep1_outVolResol).astype(np.int)[[0,2]], 0]
    volume_origin_wrt_wholebrain_outVolResol = volume_origin_wrt_wholebrainWithMargin_outVolResol + wholebrainWithMargin_origin_wrt_wholebrain_outVolResol

    OUTPUT = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes', animal)
    outfile = os.path.join(OUTPUT, 'volume_outVolResol.npy')
    print('Saving data volume_outVolResol at', OUTPUT)
    np.save(outfile, np.ascontiguousarray(volume_outVolResol))

    outfile = os.path.join(OUTPUT, 'volume_origin_wrt_wholebrain_outVolResol.npy')
    print('Saving data volume_outVolResol at', outfile)
    np.save(outfile, volume_origin_wrt_wholebrain_outVolResol)
    print('volume_origin_wrt_wholebrain_outVolResol', volume_origin_wrt_wholebrain_outVolResol)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_volume(animal)
