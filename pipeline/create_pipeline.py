"""
This program will create everything.
The only required argument is the animal. By default it will work on channel=1
and downsample = True. Run them in this sequence:
    python src/create_py --animal DKXX
    python src/create_py --animal DKXX --channel 2
    python src/create_py --animal DKXX --channel 3
    python src/create_py --animal DKXX --channel 1 --downsample false
    python src/create_py --animal DKXX --channel 2 --downsample false
    python src/create_py --animal DKXX --channel 3 --downsample false

Human intervention is required at several points in the process:
1. After create meta - the user needs to check the database and verify the images 
are in the correct order and the images look good.
1. After the first create mask method - the user needs to check the colored masks
and possible dilate or crop them.
1. After the alignment process - the user needs to verify the alignment looks good. 
increasing the step size will make the pipeline move forward in the process.
see: src/python/create_py -h
for more information.
"""
import argparse
from settings import host as HOST, schema as SCHEMA, DATA_PATH
from lib.pipeline import Pipeline


def run_pipeline(animal, channel, downsample, data_path, host, schema, tg, padding_margin, clean, debug):

    pipeline = Pipeline(animal, channel, downsample, data_path, host, schema, tg, padding_margin, clean, debug)

    print("RUNNING PREPROCESSING-PIPELINE WITH THE FOLLOWING SETTINGS:")
    print(f"\tprep_id:".ljust(20), f"{animal}".ljust(20))
    print(f"\tchannel:".ljust(20), f"{str(channel)}".ljust(20))
    print(f"\tdownsample:".ljust(20), f"{str(downsample)}".ljust(20))
    print(f"\thost:".ljust(20), f"{host}".ljust(20))
    print(f"\tschema:".ljust(20), f"{schema}".ljust(20))
    print(f"\ttg:".ljust(20), f"{str(tg)}".ljust(20))
    print(f"\tpadding_margin:".ljust(20), f"{str(padding_margin)}".ljust(20))
    print(f"\tdebug:".ljust(20), f"{str(debug)}".ljust(20))


    print()

    if step == 0:
        print(f"Step {step}: prepare images for quality control.")
        pipeline.run_program_and_time(pipeline.extract_slide_meta_data_and_insert_to_database, "Creating meta")
        pipeline.run_program_and_time(pipeline.create_web_friendly_image, "create web friendly image")
        pipeline.run_program_and_time(pipeline.extract_tifs_from_czi, "Extracting Tiffs")

    if step == 1:
        print(f"Step {step}: apply QC and prepare image masks")
        pipeline.set_task_preps()
        pipeline.run_program_and_time(pipeline.apply_QC, "Applying QC")
        pipeline.run_program_and_time(pipeline.create_normalized_image, "Creating normalization")
        pipeline.run_program_and_time(pipeline.create_mask, "Creating masks")
    
    if step == 2:
        print(f"Step {step}: clean images")
        pipeline.run_program_and_time(pipeline.apply_user_mask_edits, "Applying masks")
        pipeline.run_program_and_time(pipeline.create_cleaned_images, "Creating cleaned image")
    
    if step == 3:
        print(f"Step {step}: create histograms")
        pipeline.run_program_and_time(pipeline.make_histogram, "Making histogram")
        pipeline.run_program_and_time(pipeline.make_combined_histogram, "Making combined histogram")

    if step == 4:
        print(f"Step {step}: align images within stack")
        pipeline.run_program_and_time(pipeline.create_within_stack_transformations, "Creating elastix transform")
        transformations = pipeline.get_transformations()
        pipeline.align_downsampled_images(transformations)
        pipeline.align_full_size_image(transformations)
    
    if step == 5:
        print(f"Step {step}: create neuroglancer data")
        pipeline.run_program_and_time(pipeline.create_neuroglancer, "Neuroglancer1 single")
        pipeline.run_program_and_time(pipeline.create_downsamples, "Neuroglancer2 pyramid")


if __name__ == "__main__":
    steps = """
    start=0, prep, normalized and masks=1, mask, clean and histograms=2, 
     elastix and alignment=3, neuroglancer=4
     """
    parser = argparse.ArgumentParser(description="Work on Animal")
    parser.add_argument("--animal", help="Enter the animal", required=True)
    parser.add_argument("--channel", help="Enter channel", required=False, default=1)
    parser.add_argument(
        "--downsample", help="Enter true or false", required=False, default="true"
    )
    parser.add_argument("--step", help="steps", required=False, default=0)
    parser.add_argument(
        "--pad", help="padding factor", type=float, required=False, default=1
    )
    parser.add_argument(
        "--debug", help="Enter true or false", required=False, default="false"
    )
    parser.add_argument(
        "--clean",
        help="Remove prev DB entries and files",
        required=False,
        default=False,
    )
    parser.add_argument(
        "--tg",
        help="Extend the mask to expose the entire underside of the brain",
        required=False,
        default=False,
    )

    args = parser.parse_args()

    animal = args.animal
    channel = int(args.channel)
    downsample = bool({"true": True, "false": False}[str(args.downsample).lower()])
    step = int(args.step)
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])
    tg = bool({"true": True, "false": False}[str(args.tg).lower()])

    run_pipeline(
        animal,
        channel,
        downsample,
        DATA_PATH,
        HOST,
        SCHEMA,
        tg,
        args.pad,
        args.clean,
        debug,
    )
