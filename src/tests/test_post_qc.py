import argparse
from create_clean import masker
from create_alignment import parse_elastix,run_offsets
from create_neuroglancer_image import create_neuroglancer
from create_downsampling import create_downsamples
from create_masks import create_mask

if __name__ == '__main__':
    suffix = False
    animal = 'DK61'
    channel = 2
    downsample = True
    debug = False
    scale  =45000
    masks = False
    create_csv = False
    allen = False
    njobs = 1
    create_mask(animal, downsample, njobs)
    # masker(animal, channel, downsample, scale, debug)
    # transforms = parse_elastix(animal)
    # run_offsets(animal, transforms, channel, downsample, masks, create_csv, allen,njobs)
    # create_neuroglancer(animal, channel, downsample, debug,16)
    # create_downsamples(animal, channel, suffix, downsample)
