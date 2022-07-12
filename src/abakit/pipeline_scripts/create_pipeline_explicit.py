"""
DUANE VERSION FOR TESTING - 1-JUN-2022
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
from lib.pipeline import Pipeline

def run_pipeline(animal, channel, downsample, step, DATA_PATH):
    pipeline = Pipeline(animal, channel, downsample, DATA_PATH=DATA_PATH, debug=True)
    if step >= 0:
        pipeline.extract_slide_meta_data_and_insert_to_database()
        pipeline.create_web_friendly_image()
        pipeline.extract_tifs_from_czi()
    if step >= 1:
        pipeline.apply_QC()
        pipeline.set_task_preps()
        pipeline.create_normalized_image()
        pipeline.create_mask()
    if step >= 2:
        pipeline.apply_user_mask_edits()
        pipeline.create_cleaned_images()
        pipeline.make_histogram()
        pipeline.make_combined_histogram()
    if step >= 3:
        pipeline.create_within_stack_transformations()
        transformations = pipeline.get_transformations()
        pipeline.align_downsampled_images(transformations)
        pipeline.align_full_size_image(transformations)
    if step >= 4:
        pipeline.create_neuroglancer()
        pipeline.create_downsamples()


if __name__ == "__main__":
    animal = "DK73"
    channel = 1
    downsample = True
    step = 4
    DATA_PATH = "/net/birdstore/Active_Atlas_Data/data_root/"
    run_pipeline(animal, channel, downsample, step, DATA_PATH)

