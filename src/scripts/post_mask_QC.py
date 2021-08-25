import argparse
from create_clean import masker
from create_alignment import parse_elastix,run_offsets
from create_neuroglancer_image import create_neuroglancer
from create_downsampling import create_downsamples

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Work on Animal')
    # parser.add_argument('--animal', help='Enter the animal', required=True)
    # parser.add_argument('--channel', help='Enter channel', required=True)
    # parser.add_argument('--suffix', help='Enter suffix to add to the output dir', required=False)
    # parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    # parser.add_argument('--debug', help='Enter debug True|False', required=False, default='false')
    # parser.add_argument('--masks', help='Enter True for running masks', required=False, default=False)
    # parser.add_argument('--csv', help='Enter true or false', required=False, default='false')
    # parser.add_argument('--scale', help='Enter scaling', required=False, default=45000)
    # parser.add_argument('--allen', help='Enter true or false', required=False, default='false')

    # args = parser.parse_args()
    # animal = args.animal
    # channel = args.channel
    # downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    # create_csv = bool({'true': True, 'false': False}[str(args.csv).lower()])
    # allen = bool({'true': True, 'false': False}[str(args.allen).lower()])
    # masks = args.masks
    # suffix = args.suffix
    # debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    # scale = int(args.scale)
    suffix = False
    animal = 'DK63'
    channel = 2
    downsample = False
    debug = False
    scale  =45000
    masks = False
    create_csv = False
    allen = False
    njobs = 1
    # masker(animal, channel, downsample, scale, debug)
    transforms = parse_elastix(animal)
    run_offsets(animal, transforms, channel, downsample, masks, create_csv, allen,njobs)
    # create_neuroglancer(animal, channel, downsample, debug,16)
    # create_downsamples(animal, channel, suffix, downsample)
