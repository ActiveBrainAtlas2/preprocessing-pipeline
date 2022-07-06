"""
DUANE VERSION FOR TESTING - 9-JUN-2022
ALL DEFAULT CONSTANTS FOR PIPELINE IN settings.py (git ignore)


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
1. "QC Step" - After create meta - the user needs to check the database and verify the images 
are in the correct order and the images look good. (prepare_image_for_quality_control)*Marissa has tally form for all slides
1b. (automated mask creation: apply_qc_and_prepare_image_masks)
2. After the first create mask method - the user needs to check the colored masks
and possible dilate or crop them. 
3. After the alignment process - the user needs to verify the alignment looks good. 
increasing the step size will make the pipeline move forward in the process.
see: src/python/create_pipeline.py -h
for more information.

Note: Setting debug=True will force single core

"""
import settings
from lib.pipeline import Pipeline


def run_pipeline(animal, channel, downsample, step, DATA_PATH):
    pipeline = Pipeline(animal, channel, downsample, DATA_PATH=DATA_PATH, host=settings.host, schema=settings.schema, debug=False)
    

    pipeline.prepare_image_for_quality_control()

    if step >= 1:
        pipeline.apply_qc_and_prepare_image_masks()
    if step >= 2:
        pipeline.clean_images_and_create_histogram()
    if step >= 3:
        pipeline.align_images_within_stack()
    if step >= 4:
        pipeline.create_neuroglancer_cloud_volume()


if __name__ == "__main__":
    animal = "DK77"
    channel = 1
    downsample = False
    step = 4
    DATA_PATH = "/net/birdstore/Active_Atlas_Data/data_root/"
    run_pipeline(animal, channel, downsample, step, DATA_PATH)
