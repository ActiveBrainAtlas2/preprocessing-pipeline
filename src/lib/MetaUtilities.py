import os, sys, time
from datetime import datetime
from tqdm import tqdm
import re
from abakit.lib.utilities_bioformats import get_czi_metadata, get_fullres_series_indices
from abakit.model.slide import Slide
from abakit.model.slide import SlideCziTif


class MetaUtilities:
    def extract_slide_meta_data_and_insert_to_database(self):
        """
        Scans the czi dir to extract the meta information for each tif file
        """
        self.check_czi_file_exists()
        self.scan_id = self.get_user_entered_scan_id()
        czi_files = self.get_czi_files()
        if not self.all_slide_meta_data_exists_in_database(czi_files):
            for _, czi_file in enumerate(tqdm(czi_files)):
                if self.is_czi_file(czi_file):
                    if not self.slide_meta_data_exists(czi_file):
                        self.add_slide_information_to_database(czi_file)
                        self.add_to_slide_czi_tiff_table(czi_file)
            self.update_database()

    def get_czi_files(self):
        """Get the list of czi files in the directory"""
        try:
            czi_files = sorted(os.listdir(self.fileLocationManager.czi))
        except OSError as e:
            print(e)
            sys.exit()
        return czi_files

    def add_slide_information_to_database(self, czi_file):
        """Add the meta information about image slides that are extracted from the czi file and add them to the database"""
        self.slide = Slide()
        self.slide.scan_run_id = self.scan_id
        self.slide.slide_physical_id = int(re.findall(r"\d+", czi_file)[1])
        self.slide.rescan_number = "1"
        self.slide.slide_status = "Good"
        self.slide.processed = False
        self.slide.file_size = os.path.getsize(
            os.path.join(self.fileLocationManager.czi, czi_file)
        )
        self.slide.file_name = czi_file
        self.slide.created = datetime.fromtimestamp(
            os.path.getmtime(os.path.join(self.fileLocationManager.czi, czi_file))
        )
        czi_file_path = os.path.join(self.fileLocationManager.czi, czi_file)
        self.metadata = get_czi_metadata(czi_file_path)
        self.series = get_fullres_series_indices(self.metadata)
        self.slide.scenes = len(self.series)
        self.sqlController.session.add(self.slide)
        self.sqlController.session.flush()
        self.sqlController.session.commit()

    def add_to_slide_czi_tiff_table(self, czi_file):
        """Add entry to the table that prepares the user Quality Control interface"""
        for j, series_index in enumerate(self.series):
            scene_number = j + 1
            channels = range(self.metadata[series_index]["channels"])
            channel_counter = 0
            width = self.metadata[series_index]["width"]
            height = self.metadata[series_index]["height"]
            for channel in channels:
                tif = SlideCziTif()
                tif.slide_id = self.slide.id
                tif.scene_number = scene_number
                tif.file_size = 0
                tif.active = 1
                tif.width = width
                tif.height = height
                tif.scene_index = series_index
                channel_counter += 1
                newtif = "{}_S{}_C{}.tif".format(
                    czi_file, scene_number, channel_counter
                )
                newtif = newtif.replace(".czi", "").replace("__", "_")
                tif.file_name = newtif
                tif.channel = channel_counter
                tif.processing_duration = 0
                tif.created = time.strftime("%Y-%m-%d %H:%M:%S")
                self.sqlController.session.add(tif)
        self.sqlController.session.commit()

    def get_user_entered_scan_id(self):
        """Get id in the "scan run" table for the current microspy scan that was entered by the user in the preparation phase"""
        return self.sqlController.scan_run.id

    def is_czi_file(self, czi_file):
        """Check if a file has the .czi extension"""
        extension = os.path.splitext(czi_file)[1]
        return extension.endswith("czi")

    def all_slide_meta_data_exists_in_database(self, czi_files):
        """Check if the number of czi files in the directory matches the number of entries in the database table 'Slide'"""
        nslides = self.sqlController.session.query(Slide).filter(Slide.scan_run_id == self.scan_id).count()
        return nslides == len(czi_files)

    def slide_meta_data_exists(self, czi_file_name):
        """Checks if a specific CZI file has been logged in the database"""
        return bool(
            self.sqlController.session.query(Slide)
            .filter(Slide.scan_run_id == self.scan_id)
            .filter(Slide.file_name == czi_file_name)
            .first()
        )

    def check_czi_file_exists(self):
        """Check that the CZI files are placed in the correct location"""
        INPUT = self.fileLocationManager.czi
        if not os.path.exists(INPUT):
            print(f"{INPUT} does not exist, we are exiting.")
            sys.exit()
        files = os.listdir(INPUT)
        nfiles = len(files)
        if nfiles < 1:
            print("There are no CZI files to work with, we are exiting.")
            sys.exit()
        print(f"create meta is working with {nfiles} files.")
        self.logevent(f"create meta is working with {nfiles} files (.czi).")

    def update_database(self):
        """Updates the "file log" table in the database that tracks the progress of the pipeline"""
        SLIDES_ARE_SCANNED = self.sqlController.get_progress_id(downsample=0,channel=0,action='SCAN')
        CZI_FILES_ARE_PLACED_ON_BIRDSTORE = self.sqlController.get_progress_id(downsample=0,channel=0,action='BIRDSTORE')
        CZI_FILES_ARE_SCANNED_TO_GET_METADATA = self.sqlController.get_progress_id(downsample=0,channel=0,action='META')
        self.sqlController.set_task(self.animal, SLIDES_ARE_SCANNED)
        self.sqlController.set_task(self.animal, CZI_FILES_ARE_PLACED_ON_BIRDSTORE)
        self.sqlController.set_task(self.animal, CZI_FILES_ARE_SCANNED_TO_GET_METADATA)
