import os, psutil
import numpy as np
from concurrent.futures.process import ProcessPoolExecutor
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from pathlib import Path
import operator

from utilities.utilities_mask import clean_and_rotate_image
from lib.pipeline_utilities import get_max_image_size, convert_size
from utilities.utilities_process import test_dir
from model.slide import SlideCziTif
from model.slide import Slide
from model.slide import Section

class ImageCleaner:
    def create_cleaned_images(self):
        """
        This method applies the image masks that has been edited by the user to extract the tissue image from the surrounding
        debris
        """
        if self.channel == 1:
            self.sqlController.set_task(
                self.animal, self.progress_lookup.CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK
            )
        if self.downsample:
            self.create_cleaned_images_thumbnail()
        else:
            self.create_cleaned_images_full_resolution()

    def create_cleaned_images_thumbnail(self):
        """Clean the image using the masks for the downsampled version"""
        CLEANED = self.fileLocationManager.get_thumbnail_cleaned(self.channel)
        INPUT = self.fileLocationManager.get_thumbnail(self.channel)
        MASKS = self.fileLocationManager.thumbnail_masked
        self.logevent(f"INPUT FOLDER: {INPUT}")
        starting_files = os.listdir(INPUT)
        self.logevent(f"FILE COUNT: {len(starting_files)}")
        self.logevent(f"MASK FOLDER: {MASKS}")
        starting_files = os.listdir(INPUT)
        self.logevent(f"FILE COUNT: {len(starting_files)}")
        self.logevent(f"OUTPUT FOLDER: {CLEANED}")
        os.makedirs(CLEANED, exist_ok=True)
        self.parallel_create_cleaned(INPUT, CLEANED, MASKS)

    def create_cleaned_images_full_resolution(self):
        """Clean the image using the masks for the full resolution image"""
        CLEANED = self.fileLocationManager.get_full_cleaned(self.channel)
        os.makedirs(CLEANED, exist_ok=True)
        INPUT = self.fileLocationManager.get_full(self.channel)
        MASKS = self.fileLocationManager.full_masked
        self.logevent(f"INPUT FOLDER: {INPUT}")
        starting_files = os.listdir(INPUT)
        self.logevent(f"FILE COUNT: {len(starting_files)}")
        self.logevent(f"MASK FOLDER: {MASKS}")
        starting_files = os.listdir(INPUT)
        self.logevent(f"FILE COUNT: {len(starting_files)}")
        self.logevent(f"OUTPUT FOLDER: {CLEANED}")
        self.parallel_create_cleaned(INPUT, CLEANED, MASKS)

    def get_section_rotation(self, section: Section):
        sections = self.sqlController.session.query(SlideCziTif).filter(
            SlideCziTif.FK_slide_id == section.FK_slide_id
        )
        indices = np.sort(np.unique([i.scene_index for i in sections]))
        scene = np.where(indices == section.scene_index)[0][0] + 1
        slide = self.sqlController.session.query(Slide).get(section.FK_slide_id)
        return getattr(slide, f"scene_rotation_{scene}")

    def parallel_create_cleaned(self, INPUT, CLEANED, MASKS):
        """Clean the images (downsampled or full size) in parallel"""
        max_width, max_height = get_max_image_size(INPUT)
        print(
            f" max_width {max_width}, max_height {max_height}, padding_margin {self.padding_margin}", end=" "
        )
        rotation = self.sqlController.scan_run.rotation
        flip = self.sqlController.scan_run.flip
        test_dir(
            self.animal, INPUT, self.section_count, self.downsample, same_size=False
        )

        files = os.listdir(INPUT)
        dict_target_filesizes = {}  # dict for symlink <-> target file size
        for filename in files:
            symlink = os.path.join(INPUT, filename)
            target_file = Path(symlink).resolve()  # taget of symbolic link
            file_size = os.path.getsize(target_file)
            dict_target_filesizes[filename] = file_size

        files_ordered_by_filesize_desc = dict(
            sorted(
                dict_target_filesizes.items(), key=operator.itemgetter(1), reverse=True
            )
        )

        progress_id = self.sqlController.get_progress_id(
            self.downsample, self.channel, "CLEAN"
        )
        self.sqlController.set_task(self.animal, progress_id)
        file_keys = []
        for i, file in enumerate(files_ordered_by_filesize_desc.keys()):
            infile = os.path.join(INPUT, file)
            if i == 0:  # largest file
                single_file_size = os.path.getsize(infile)

            outpath = os.path.join(CLEANED, file)  # regular-birdstore
            if os.path.exists(outpath):
                continue
            maskfile = os.path.join(MASKS, file)
            file_keys.append(
                [
                    infile,
                    outpath,
                    maskfile,
                    rotation,
                    flip,
                    int(max_width * self.padding_margin),
                    int(max_height * self.padding_margin),
                    self.channel,
                ]
            )
        ram_coefficient = 10

        mem_avail = psutil.virtual_memory().available
        batch_size = mem_avail // (single_file_size * ram_coefficient)
        print(
            f"MEM AVAILABLE: {convert_size(mem_avail)}; [LARGEST] SINGLE FILE SIZE: {convert_size(single_file_size)}; BATCH SIZE: {round(batch_size,0)}", end=" "
        )
        self.logevent(
            f"MEM AVAILABLE: {convert_size(mem_avail)}; [LARGEST] SINGLE FILE SIZE: {convert_size(single_file_size)}; BATCH SIZE: {round(batch_size,0)}"
        )
        
        workers = self.get_nworkers()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            executor.map(clean_and_rotate_image, sorted(file_keys))


