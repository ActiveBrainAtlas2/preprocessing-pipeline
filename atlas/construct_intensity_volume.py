
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
    volume_images, origin_images = images_to_volume_v2(images=images,
                                                spacing_um=20.,
                                                in_resol_um=input_image_resolution_um,
                                                out_resol_um=voxel_size_um)

    prep5_origin = load_cropbox_v2(stack=animal, only_2d=True, prep_id='alignedWithMargin')
    loaded_cropbox_resol = 'thumbnail'
    prep5_origin_wrt_prep1 = prep5_origin * convert_resolution_string_to_um(stack=animal, resolution=loaded_cropbox_resol) / voxel_size_um
    wholebrainWithMargin_origin = np.r_[np.round(prep5_origin_wrt_prep1).astype(np.int)[[0,2]], 0]
    origin_brain = origin_images + wholebrainWithMargin_origin

    OUTPUT = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes', animal)
    print('Shape of volume images', volume_images.shape)

    outfile = os.path.join(OUTPUT, 'volume_images.npy')
    print('Saving', OUTPUT)
    np.save(outfile, np.ascontiguousarray(volume_images))

    outfile = os.path.join(OUTPUT, 'origin_brain.npy')
    print('Saving', outfile)
    np.save(outfile, origin_brain)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_volume(animal)
