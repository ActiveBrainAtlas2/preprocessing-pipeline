import os
from lib.ParallelManager import ParallelManager

class TiffExtractor(ParallelManager):
    def extract_tifs_from_czi(self):
        """
        This method will:
            1. Fetch the sections from the database
            2. Yank the tif out of the czi file according to the index and channel with the bioformats tool.
            3. Then updates the database with updated meta information
        Args:
            animal: the prep id of the animal
            channel: the channel of the stack to process
            compression: default is LZW compression

        Returns:
            nothing
        """

        INPUT = self.fileLocationManager.czi
        OUTPUT = self.fileLocationManager.tif
        os.makedirs(OUTPUT, exist_ok=True)
        sections = self.sqlController.get_distinct_section_filenames(self.animal, self.channel)
        commands = []
        for section in sections:
            input_path = os.path.join(INPUT, section.czi_file)
            output_path = os.path.join(OUTPUT, section.file_name)
            if not os.path.exists(input_path):
                continue
            if os.path.exists(output_path):
                continue
            cmd = ['/usr/local/share/bftools/bfconvert', '-bigtiff', '-separate', '-series', str(section.scene_index),
                    '-compression', 'LZW', '-channel', str(section.channel_index),  '-nooverwrite', input_path, output_path]
            commands.append(cmd)
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_shell(commands,workers)
        self.update_database()
    
    def update_database(self):
        self.sqlController.set_task(self.animal, self.progress_lookup.QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN)
        self.sqlController.set_task(self.animal, self.progress_lookup.CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1)

    def create_web_friendly_image(self):
        INPUT = self.fileLocationManager.tif
        OUTPUT = self.fileLocationManager.thumbnail_web
        os.makedirs(OUTPUT, exist_ok=True)
        file_keys = []
        files = os.listdir(INPUT)
        for file in files:
            filepath = os.path.join(INPUT, file)
            if not file.endswith('_C1.tif'):
                continue
            png_path = os.path.join(OUTPUT, file.replace('tif', 'png'))
            if os.path.exists(png_path):
                continue
            file_key = ['convert', filepath, '-resize', '3.125%', '-depth', '8', '-normalize', '-auto-level', png_path]
            file_keys.append(file_key)
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_shell(file_keys,workers)