"""
This program will create everything.
The only required argument is the animal. By default it will work on channel=1
and downsample = True. Run them in this sequence:
    python src/create_pipeline.py --animal DKXX
    python src/create_pipeline.py --animal DKXX --channel 2
    python src/create_pipeline.py --animal DKXX --channel 3
    python src/create_pipeline.py --animal DKXX --channel 1 --downsample false
    python src/create_pipeline.py --animal DKXX --channel 2 --downsample false
    python src/create_pipeline.py --animal DKXX --channel 3 --downsample false

Human intervention is required at several points in the process:
1. After create meta - the user needs to check the database and verify the images 
are in the correct order and the images look good.
1. After the first create mask method - the user needs to check the colored masks
and possible dilate or crop them.
1. After the alignment process - the user needs to verify the alignment looks good. 
increasing the step size will make the pipeline move forward in the process.
see: src/python/create_pipeline.py -h
for more information.
"""
import argparse
import settings
from lib.pipeline import Pipeline




def run_pipeline(animal, channel, downsample, data_path, host, schema, debug):

    pipeline = Pipeline(animal, channel, downsample, data_path, host, schema, debug)
    
    pipeline.prepare_image_for_quality_control()

    if step > 0:
        pipeline.apply_qc_and_prepare_image_masks()
    if step > 1:
        pipeline.clean_images_and_create_histogram()
    if step > 2:
        pipeline.align_images_within_stack()
    if step > 3:
        pipeline.create_neuroglancer_cloud_volume()



if __name__ == '__main__':
    steps = """
    start=0, prep, normalized and masks=1, mask, clean and histograms=2, 
     elastix and alignment=3, neuroglancer=4
     """
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=False, default=1)
    parser.add_argument('--downsample', help='Enter true or false', required=False, default='true')
    parser.add_argument('--step', help=steps, required=False, default=0)
    parser.add_argument('--debug', help='Enter true or false', required=False, default='false')
    parser.add_argument('--host', help='Enter the DB host', required=True, default=settings.host)
    parser.add_argument('--schema', help='Enter the DB schema', required=True, default=settings.schema)

    args = parser.parse_args()

    animal = args.animal
    channel = int(args.channel)
    downsample = bool({'true': True, 'false': False}[str(args.downsample).lower()])
    step = int(args.step)
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    host = args.host
    schema = args.schema

    DATA_PATH = "/net/birdstore/Active_Atlas_Data/data_root/"
    run_pipeline(animal, channel, downsample, DATA_PATH, host, schema, debug)
