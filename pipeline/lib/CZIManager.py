import os
import sys
from PIL import Image
from aicspylibczi import CziFile
from aicsimageio import AICSImage, imread
from tifffile import imsave
from utilities.utilities_mask import equalized
from lib.FileLogger import FileLogger


class CZIManager(FileLogger):
    def __init__(self, czi_file):
        self.czi_file = czi_file
        self.file = CziFile(czi_file)

    def extract_metadata_from_czi_file(self, czi_file, czi_file_path):
        czi_aics = AICSImage(czi_file_path)
        total_scenes = czi_aics.scenes

        czi_meta_dict = {}
        scenes = {}
        for idx, scene in enumerate(total_scenes):
            czi_aics.set_scene(scene)
            dimensions = (czi_aics.dims.X, czi_aics.dims.Y)
            channels = czi_aics.dims.C

            print("CZI FILE:", czi_file)
            print("CURRENT SCENE:", czi_aics.current_scene)
            print("DIMENSIONS (x,y):", dimensions)
            print("CHANNELS:", channels)

            scenes[idx] = {
                "scene_name": czi_aics.current_scene,
                "channels": channels,
                "dimensions": dimensions,
            }

        czi_meta_dict[czi_file] = scenes
        return czi_meta_dict

    def get_scene(self, scene_index, channel, scale=1):
        region = self.get_scene_dimension(scene_index)
        return self.file.read_mosaic(region=region, scale_factor=scale, C=channel-1)[0]


def extract_tiff_from_czi(czi_file, file_name, scenei, channel=1, scale=1):
    czi = CZIManager(czi_file)
    try:
        data = czi.get_scene(scale=scale, scene_index=scenei, channel=channel)
        imsave(file_name, data)
    except Exception as e:
        print(
            f"ERROR READING SCENE - [extract_tiff_from_czi] IN FILE {czi_file} ... SKIPPING"
        )
        czi.logevent(
            f"ERROR READING SCENE - [extract_tiff_from_czi] FROM FILE {czi_file} -> {file_name}; SCENE: {scenei}; CHANNEL: {channel} ... SKIPPING - ERR: {e}"
        )


def extract_png_from_czi(file_key, normalize=True):
    """SINGLE CHANNEL ONLY"""

    index, infile, outfile, scene_index, scale = file_key

    czi = CZIManager(infile)
    try:
        data = czi.get_scene(scene_index=scene_index, channel=1, scale=scale)
        if normalize:
            data = equalized(data)
        im = Image.fromarray(data)
        im.save(outfile)
    except Exception as e:
        print(
            f"ERROR READING SCENE - [extract_png_from_czi] IN FILE {infile} ... SKIPPING"
        )
        czi.logevent(
            f"ERROR READING SCENE - [extract_png_from_czi] IN FILE {infile} ... SKIPPING - ERR: {e}"
        )
