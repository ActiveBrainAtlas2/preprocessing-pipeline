import os
import glob
import cv2
import numpy as np
from skimage import io
from utilities.utilities_mask import equalized
from pipeline.utilities.shell_tools import get_image_size


class Normalizer:
    def create_normalized_image(self):
        """Normalize the downsampled images with QC applied"""
        if self.channel == 1 and self.downsample:
            INPUT = self.fileLocationManager.thumbnail
            OUTPUT = self.fileLocationManager.get_normalized(self.channel)
            self.logevent(f"INPUT FOLDER: {INPUT}")
            files = sorted(os.listdir(INPUT))
            self.logevent(f"CURRENT FILE COUNT: {len(files)}")
            self.logevent(f"OUTPUT FOLDER: {OUTPUT}")
            os.makedirs(OUTPUT, exist_ok=True)

            # INPUT = self.fileLocationManager.thumbnail_web
            # sections = self.sqlController.get_sections(self.animal, self.channel)
            # input_paths = []
            # output_paths = []
            # for section_number, section in enumerate(sections):

            #     input_path = os.path.join(
            #         INPUT, os.path.splitext(section.file_name)[0] + ".png"
            #     )  # DB has input filename stored with .tif extension
            #     output_path = os.path.join(
            #         OUTPUT, str(section_number).zfill(3) + ".png"
            #     )
            #     if not os.path.exists(input_path):
            #         continue
            #     if os.path.exists(output_path):
            #         continue
            #     input_paths.append(
            #         os.path.relpath(input_path, os.path.dirname(output_path))
            #     )
            #     output_paths.append(output_path)
            #     width, height = get_image_size(input_path)
            #     if self.downsample:
            #         self.sqlController.update_tif(section.id, width, height)
            # for file_key in zip(input_paths, output_paths):
            #     os.symlink(*file_key)

            ####################### LEGACY BELOW USING .tif FILES

            for file in files:
                infile = os.path.join(INPUT, file)
                outpath = os.path.join(OUTPUT, file)
                if os.path.exists(outpath):
                    continue
                img = io.imread(infile)
                if img.dtype == np.uint16:
                    img = (img / 256).astype(np.uint8)
                fixed = equalized(img)
                cv2.imwrite(outpath, fixed.astype(np.uint8))
