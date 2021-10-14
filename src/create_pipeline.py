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
from timeit import default_timer as timer
from lib.pipeline import Pipeline
from lib.logger import get_logger

if __name__ == '__main__':
    steps = """
    start=0, 
    prep, normalized and masks=1, 
    mask, clean and histograms=2, 
    elastix and alignment=3, 
    neuroglancer=4
    """
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=False, default=1)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--step', help=steps, required=False, default=0)

    args = parser.parse_args()
    animal = args.animal
    channel = int(args.channel)
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    step = int(args.step)
    logger = get_logger(animal)
    
    pipeline = Pipeline(animal, channel, downsample)
    start = timer()
    pipeline.check_programs()
    end = timer()
    print(f'Check programs took {end - start} seconds')    
    logger.info(f'Check programs took {end - start} seconds')
    start = timer()
    pipeline.create_meta()
    end = timer()
    print(f'Create meta took {end - start} seconds')    
    logger.info(f'Ceate meta took {end - start} seconds')
    start = timer()
    pipeline.create_tifs()
    end = timer()
    print(f'Create tifs took {end - start} seconds')    
    logger.info(f'Create tifs took {end - start} seconds')
    if step > 0:
        start = timer()
        pipeline.create_preps()
        pipeline.create_normalized()
        pipeline.create_masks()
        end = timer()
        print(f'Creating normalized and masks took {end - start} seconds')    
        logger.info(f'Create preps, normalized and masks took {end - start} seconds')
    if step > 1:
        start = timer()
        pipeline.create_masks_final()
        print(f'Finished create_masks final')    
        pipeline.create_clean()
        print(f'Finished clean')    
        pipeline.create_histograms(single=True)
        print(f'Finished histogram single')    
        pipeline.create_histograms(single=False)
        print(f'Finished histograms combined')    
        end = timer()
        print(f'Creating masks, cleaning and histograms took {end - start} seconds')    
        logger.info(f'Creating masks, cleaning and histograms took {end - start} seconds')
    if step > 2:
        start = timer()
        pipeline.create_elastix()
        pipeline.create_alignment()
        end = timer()
        print(f'Creating elastix and alignment took {end - start} seconds')    
        logger.info(f'Create elastix and alignment took {end - start} seconds')
    if step > 3:
        start = timer()
        pipeline.create_neuroglancer_image()
        pipeline.create_downsampling()
        end = timer()
        print(f'Last step: creating neuroglancer images took {end - start} seconds')    
        logger.info(f'Last step: creating neuroglancer took {end - start} seconds')

    
