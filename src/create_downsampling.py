"""
Creates a shell from  aligned thumbnails
"""
import argparse
from lib.utilities_downsampling import create_downsamples

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--suffix', help='Enter suffix to add to the output dir', required=False)
    parser.add_argument('--njobs', help='number of core to use for parallel processing muralus can handle 100 ratto can handle 4', required=False, default=4)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    workers = int(args.njobs)
    suffix = args.suffix
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    create_downsamples(animal, channel, suffix, downsample,workers)

