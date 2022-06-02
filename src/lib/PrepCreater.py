import os
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from concurrent.futures.process import ProcessPoolExecutor
from shutil import copyfile
from abakit.lib.SqlController import SqlController
from abakit.lib.utilities_process import test_dir, create_downsample
from lib.pipeline_utilities import get_image_size

class PrepCreater:

    def set_task_preps(self):
        self.sqlController = SqlController(self.animal)
        if self.channel == 1:
            self.sqlController.update_scanrun(self.sqlController.scan_run.id)
        progress_id = self.sqlController.get_progress_id(True, self.channel, 'TIF')
        self.sqlController.set_task(self.animal, progress_id)
        progress_id = self.sqlController.get_progress_id(False, self.channel, 'TIF')
        self.sqlController.set_task(self.animal, progress_id)


    def apply_QC_to_full_resolution_images(self):
        """
        Applies the inclusion and replacement results defined by the user on the Django admin portal for the Quality Controll step
        to the full resolution images.  The result is stored in the animal_folder/preps/full directory
        """
        INPUT = self.fileLocationManager.tif
        OUTPUT = self.fileLocationManager.get_full(self.channel)
        os.makedirs(OUTPUT, exist_ok=True)
        input_paths = []
        output_paths = []
        sections = self.sqlController.get_sections(self.animal, self.channel)
        for section_number, section in enumerate(sections):
            input_path = os.path.join(INPUT, section.file_name)
            output_path = os.path.join(OUTPUT, str(section_number).zfill(3) + '.tif')
            if not os.path.exists(input_path):
                continue
            if os.path.exists(output_path):
                continue
            input_paths.append(input_path)
            output_paths.append(output_path)
            width, height = get_image_size(input_path)
            self.sqlController.update_tif(section.id, width, height)
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_executor([input_paths,output_paths],workers,copyfile)


    def make_low_resolution(self):
        """
        Making low resolution version of the full resolution images with QC applied.  These images are used to
        create image masks and within stack alignments
        """
        file_keys = []
        INPUT = self.fileLocationManager.get_full(self.channel)
        OUTPUT = self.fileLocationManager.get_thumbnail(self.channel)
        os.makedirs(OUTPUT, exist_ok=True)
        test_dir(self.animal, INPUT, downsample=False, same_size=False)
        files = sorted(os.listdir(INPUT))
        for file in files:
            infile = os.path.join(INPUT, file)
            outpath = os.path.join(OUTPUT, file)
            if os.path.exists(outpath):
                continue
            file_keys.append([infile, outpath])
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_executor([file_keys],workers,create_downsample)