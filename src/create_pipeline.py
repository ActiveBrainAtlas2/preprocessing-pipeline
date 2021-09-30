"""
This program will create all three downsampled channels first.
After they are done, the full resolution images can be completed.
Human intervention is required at several points in the process:
1. After create meta
1. After the first create mask method
1. After the alignemnt process
1. After the final neuroglancer downsampling
"""
import argparse
from lib.pipeline import Pipeline

if __name__ == '__main__':
    steps = "start=1, prep=2, mask=3, final mask=4, align=5"
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=False, default=1)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--step', help=steps, required=False, default=0)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    step = int(args.step)
    
    pipeline = Pipeline(animal, channel, downsample)
    print('check programs')
    pipeline.check_programs()
    print('create meta')
    pipeline.create_meta()
    print('create tifs')
    pipeline.create_tifs()
    if step > 0:
        print('create preps')
        pipeline.create_preps()
    if step > 1:
        print('create normalized')
        pipeline.create_normalized()
        print('create masks')
        pipeline.create_masks()
    if step > 2:
        print('create masks final')
        pipeline.create_masks_final()
        print('create clean')
        pipeline.create_clean()
        print('create histogram true')
        pipeline.create_histograms(single=True)
        print('create histogram false')
        pipeline.create_histograms(single=False)
    if step > 3:
        print('create elastix')
        pipeline.create_elastix()
    if step > 4:
        print('create alignment')
        pipeline.create_alignment()
        print('create neuroglancer image')
        pipeline.create_neuroglancer_image()
        print('create downsampling')
        pipeline.create_downsampling()
    
    
