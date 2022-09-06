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


def run_pipeline(
    animal, channel, downsample, data_path, host, schema, tg, padding_margin, clean, debug
):

    pipeline = Pipeline(
        animal, channel, downsample, data_path, host, schema, tg, padding_margin, clean, debug
    )

    print(
        "RUNNING PREPROCESSING-PIPELINE WITH THE FOLLOWING SETTINGS:",
        "prep_id: " + animal,
        "channel: " + str(channel),
        "downsample: " + str(downsample),
        "host: " + host,
        "schema: " + schema,
        "tg: " + str(tg),
        "padding_margin: " + str(padding_margin),
        "debug: " + str(debug),
        sep="\n",
    )

    print("Step 0")
    
    pipeline.prepare_image_for_quality_control()

    if step > 0:
        print("Step 1")
        pipeline.apply_qc_and_prepare_image_masks()
    
    if step > 1:
        print("Step 2")
        # if cleanup == "True":
        #     pipeline.qc_cleanup()
        pipeline.clean_images_and_create_histogram()
    
    if step > 2:
        print("Step 3")
        # if cleanup == "True":
        #     pipeline.align_cleanup()
        pipeline.align_images_within_stack()
    
    if step > 3:
        print("Step 4")
        # if cleanup == "True":
        #     pipeline.ng_cleanup(downsample, channel)
        pipeline.create_neuroglancer_cloud_volume()


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
