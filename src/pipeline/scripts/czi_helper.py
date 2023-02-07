import numpy as np
from aicspylibczi import CziFile
from aicsimageio import AICSImage
import os
import argparse



def run_main(animal):

    czi_file_path = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/czi'
    czi_files = sorted(os.listdir(czi_file_path))
    widths = []
    heights = []
    for i, czi_file in enumerate(czi_files):
        if czi_file.endswith('czi'):
            infile = os.path.join(czi_file_path, czi_file)
            czi_aics = AICSImage(infile)
            total_scenes = czi_aics.scenes

            channels = czi_aics.dims.C
            print(f"{i+1} {czi_file} has {len(total_scenes)} scenes and {channels} channels")
            if debug:
                for idx, scene in enumerate(total_scenes):
                    czi_aics.set_scene(scene)
                    dimensions = (czi_aics.dims.X, czi_aics.dims.Y)
                    print("\tScene index:", idx, end="\t")
                    print("\tDimension (x,y):", dimensions)
                    widths.append(dimensions[0])
                    heights.append(dimensions[1])

    if debug:
        # Most of the scenes need to be rotated.
        # The original scenes have the rostral at the top and caudal at the bottom
        # so we flip the width and height below
        print(f'Max width={int(max(heights))} after rotating.')
        print(f'Max height={int(max(widths))} after rotating.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Work on Animal")
    parser.add_argument("--animal", help="Enter the animal", required=True)
    parser.add_argument("--debug", help="Enter true or false", required=False, default="false")

    args = parser.parse_args()

    animal = args.animal
    debug = bool({"true": True, "false": False}[str(args.debug).lower()])

    run_main(animal, debug)



