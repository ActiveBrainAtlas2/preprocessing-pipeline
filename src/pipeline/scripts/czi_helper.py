import numpy as np
from aicspylibczi import CziFile
from aicsimageio import AICSImage
import os


animal = 'DK37'

czi_file_path = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/czi'

czi_files = os.listdir(czi_file_path)
widths = []
heights = []
for czi_file in czi_files:
    if czi_file.endswith('czi'):
        infile = os.path.join(czi_file_path, czi_file)
        czi_aics = AICSImage(infile)
        total_scenes = czi_aics.scenes

        channels = czi_aics.dims.C
        print(f"CZI FILE={czi_file} with {len(total_scenes)} scenes and {channels} channels")
        for idx, scene in enumerate(total_scenes):
            czi_aics.set_scene(scene)
            dimensions = (czi_aics.dims.X, czi_aics.dims.Y)
            x = czi_aics.physical_pixel_sizes.X 
            y = czi_aics.physical_pixel_sizes.Y 

            print("\tScene index:", idx, end="\t")
            print("\tDimension (x,y):", dimensions)
            widths.append(dimensions[0])
            heights.append(dimensions[1])

# Most of the scenes need to be rotated.
# The original scenes have the rostral at the top and caudal at the bottom
# so we flip the width and height below
print(f'Max width={int(max(heights))}')
print(f'Max height={int(max(widths))}')


