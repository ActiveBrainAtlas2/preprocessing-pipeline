import argparse
from lib.utilities_create_masks import ,create_mask


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--final', help='Enter true or false', required=False, default='false')

    args = parser.parse_args()
    animal = args.animal
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    final = bool({'true': True, 'false': False}[str(args.final).lower()])

    if final:
         (animal)
    else:
         create_mask(animal, downsample)
       



