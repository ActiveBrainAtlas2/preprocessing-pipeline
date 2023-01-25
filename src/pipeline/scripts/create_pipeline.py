"""
This program will create everything.
The only required argument is the animal and step. By default it will work on channel=1
and downsample = True. Run them in this sequence:

- python src/pipeline/scripts/create_pipeline.py --animal DKXX --step 0|1|2|3|4|5
- python src/pipeline/scripts/create_pipeline.py --animal DKXX channel 2|3 --step 0|1|2|3|4|5
- python src/pipeline/scripts/create_pipeline.py --animal DKXX channel 1 downsample false --step 0|1|2|3|4|5
- python src/pipeline/scripts/create_pipeline.py --animal DKXX channel 2|3 downsample false --step 0|1|2|3|4|5

Explanation for the steps:

- Step 0 - extracts the metadata from the CZI and inserts into the database. \
    Also creates web friendly PNG files for viewing in the portal. Extracts the TIFF \
    files at the standard downsampling factor
- Step 1 - This is after the database portal QC. The normalized images are created and the masks \
    are also created. The user peforms QC on the masks and makes sure they are good.
- Step 2 - Final masks are created and then the images are cleaned from the masks.
- Step 3 - Histograms are created of all channel 1 sections
- Step 4 - Alignment with Elastix is run on the cleaned images
- Step 5 - Neuroglancer precomputed data is created from the aligned and cleaned images.

**Changes from previous pipeline version**

- Use opencv cv2.imwrite instead of tiff.imwrite. This saves lots of space and works fine
- More of the code was moved from pipeline.py to this file to make it obvious what is being run
- I removed the greater than sign in the steps and replaced it with == to run specific methods only.
- Fine tuned the scaled method in the cleaning process. This will save lots of RAM!!!!
- Replaced the run_commands_with_executor with run_commands_concurrently. Much simpler!
- Removed the insert and select from ng.process_image and replaced with a touch file in \
the PROGRESS_DIR, this will remove those 'mysql connection has gone away' errors.
- Changed the session to a scoped session and extended the connection timeout to 24 hours.

**Timing results**

- The processes that take the longest and need the most monitoring are, cleaning, aligning \
and creating the neuroglancer images. The number of workers must be set correctly \
otherwise the workstations will crash if the number of workers is too high. If the number \
of workers is too low, the processes take too long.
- Cleaning full resolution of 480 images on channel 1 on ratto took 5.5 hours
- Aligning full resolution of 480 images on channel 1 on ratto took 6.8 hours
- Running entire neuroglancer process on 480 images on channel 1 on ratto took 11.3 hours

**Human intervention is required at several points in the process**

- After create meta - the user needs to check the database and verify the images \
are in the correct order and the images look good.
- After the first create mask method - the user needs to check the colored masks \
and possible dilate or crop them.
- After the alignment process - the user needs to verify the alignment looks good. \
increasing the step size will make the pipeline move forward in the process.
"""
import argparse
from pathlib import Path
import sys
PIPELINE_ROOT = Path('./src/pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

try:
    from settings import data_path, host, schema
except ImportError:
    print('Missing settings using defaults')
    data_path = "/net/birdstore/Active_Atlas_Data/data_root"
    host = "db.dk.ucsd.edu"
    schema = "active_atlas_production"


from image_manipulation.pipeline_process import Pipeline


def run_pipeline(animal, channel, downsample, data_path, tg, debug):
    """Takes params and runs the pipeline

    :param animal: The animal we are working on.
    :param channel: The channel, integer 1, 2, or 3. Defaults to 1
    :param downsample: True for downsample, False for full resolution. Defaults to True
    :param data_path: A string pointing to the birdstore location.
    :param tg: A boolean to determine if the mask gets extended for the trigeminal ganglia.
    :param debug: A boolean to determine if we should run in debug mode: Defaults to false.
    """

    pipeline = Pipeline(animal, channel, downsample, data_path, tg, debug)

    print("RUNNING PREPROCESSING-PIPELINE WITH THE FOLLOWING SETTINGS:")
    print("\tprep_id:".ljust(20), f"{animal}".ljust(20))
    print("\tstep:".ljust(20), f"{step}".ljust(20))
    print("\tchannel:".ljust(20), f"{str(channel)}".ljust(20))
    print("\tdownsample:".ljust(20), f"{str(downsample)}".ljust(20))
    print("\thost:".ljust(20), f"{host}".ljust(20))
    print("\tschema:".ljust(20), f"{schema}".ljust(20))
    print("\ttg:".ljust(20), f"{str(tg)}".ljust(20))
    print("\tdebug:".ljust(20), f"{str(debug)}".ljust(20))
    print()

    if step == 0:
        print(f"Step {step}: prepare images for quality control.")
        pipeline.run_program_and_time(pipeline.extract_slide_meta_data_and_insert_to_database, pipeline.TASK_CREATING_META)
        pipeline.run_program_and_time(pipeline.create_web_friendly_image, pipeline.TASK_CREATING_WEB_IMAGES)
        pipeline.run_program_and_time(pipeline.extract_tiffs_from_czi, pipeline.TASK_EXTRACTING_TIFFS)

    if step == 1:
        print(f"Step {step}: apply QC and prepare image masks")
        pipeline.set_task_preps_update_scanrun()
        pipeline.run_program_and_time(pipeline.apply_QC, pipeline.TASK_APPLYING_QC)
        pipeline.run_program_and_time(pipeline.create_normalized_image, pipeline.TASK_APPLYING_NORMALIZATION)
        pipeline.run_program_and_time(pipeline.create_mask, pipeline.TASK_CREATING_MASKS)
    
    if step == 2:
        print(f"Step {step}: clean images")
        pipeline.run_program_and_time(pipeline.apply_user_mask_edits, pipeline.TASK_APPLYING_MASKS)
        pipeline.run_program_and_time(pipeline.create_cleaned_images, pipeline.TASK_CREATING_CLEANED_IMAGES)
    
    if step == 3:
        print(f"Step {step}: create histograms")
        pipeline.run_program_and_time(pipeline.make_histogram, pipeline.TASK_CREATING_HISTOGRAMS)
        pipeline.run_program_and_time(pipeline.make_combined_histogram, pipeline.TASK_CREATING_COMBINED_HISTOGRAM)

    if step == 4:
        print(f"Step {step}: align images within stack")

        for i in [0, 1]:
            print(f'Starting iteration {i}')
            pipeline.iteration = i
            pipeline.run_program_and_time(pipeline.create_within_stack_transformations, pipeline.TASK_CREATING_ELASTIX_TRANSFORM)
            transformations = pipeline.get_transformations()
            pipeline.align_downsampled_images(transformations)
            pipeline.align_full_size_image(transformations)
            pipeline.run_program_and_time(pipeline.call_alignment_metrics, pipeline.TASK_CREATING_ELASTIX_METRICS)

        pipeline.run_program_and_time(pipeline.create_web_friendly_sections, pipeline.TASK_CREATING_SECTION_PNG)
    
    if step == 5:
        print(f"Step {step}: create neuroglancer data")
        pipeline.run_program_and_time(pipeline.create_neuroglancer, pipeline.TASK_NEUROGLANCER_SINGLE)
        pipeline.run_program_and_time(pipeline.create_downsamples, pipeline.TASK_NEUROGLANCER_PYRAMID)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Work on Animal")
    parser.add_argument("--animal", help="Enter the animal", required=True)
    parser.add_argument("--channel", help="Enter channel", required=False, default=1)
    parser.add_argument("--downsample", help="Enter true or false", required=False, default="true")
    parser.add_argument("--step", help="steps", required=False, default=0)
    parser.add_argument("--debug", help="Enter true or false", required=False, default="false")
    parser.add_argument("--tg", help="Extend the mask to expose the entire underside of the brain", required=False, default=False)

    args = parser.parse_args()

    animal = args.animal
    channel = int(args.channel)
    downsample = bool({"true": True, "false": False}[str(args.downsample).lower()])
    step = int(args.step)
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    tg = bool({"true": True, "false": False}[str(args.tg).lower()])

    run_pipeline(animal, channel, downsample, data_path, tg, debug)
