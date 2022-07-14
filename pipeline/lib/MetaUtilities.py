import os, sys, time, re, psutil
from datetime import datetime
from tqdm import tqdm
import re
from model.slide import Slide, SlideCziTif
from lib.CZIManager import CZIManager
from pathlib import Path
import operator
from lib.pipeline_utilities import convert_size
from concurrent.futures.process import ProcessPoolExecutor
from Controllers.SqlController import SqlController


class MetaUtilities:
    def extract_slide_meta_data_and_insert_to_database(self):
        """
        REVISED FOR PARALLEL PROCESSING
        Scans the czi dir to extract the meta information for each tif file
        """
        INPUT = self.fileLocationManager.czi
        czi_files = self.check_czi_file_exists()
        self.scan_id = self.get_user_entered_scan_id()
        if not self.all_slide_meta_data_exists_in_database(czi_files):
            if self.debug:
                print("debugging with single core")
                
                for _, czi_file in enumerate(tqdm(czi_files)):
                    if self.is_czi_file(czi_file):
                        if not self.slide_meta_data_exists(czi_file):
                            self.load_metadata(czi_file)
                            self.add_slide_information_to_database(czi_file)
                            self.add_to_slide_czi_tiff_table(czi_file)

                self.update_database()
            else:
                # PARALLEL PROCESSING
                dict_target_filesizes = {}  # dict for symlink <-> target file size
                for filename in czi_files:
                    symlink = os.path.join(INPUT, filename)
                    target_file = Path(symlink).resolve()  # taget of symbolic link
                    file_size = os.path.getsize(target_file)
                    dict_target_filesizes[filename] = file_size

                files_ordered_by_filesize_desc = dict(
                    sorted(
                        dict_target_filesizes.items(),
                        key=operator.itemgetter(1),
                        reverse=True,
                    )
                )
                file_keys = []
                for i, file in enumerate(files_ordered_by_filesize_desc.keys()):
                    infile = os.path.join(INPUT, file)
                    if i == 0:  # largest file
                        single_file_size = os.path.getsize(infile)

                    file_keys.append(
                        [
                            infile,
                            self.scan_id,
                            self.channel,
                            self.animal,
                            self.dbhost,
                            self.dbschema,
                        ]
                    )
                    
                ram_coefficient = 2

                mem_avail = psutil.virtual_memory().available
                batch_size = mem_avail // (single_file_size * ram_coefficient)

                print(
                    f"MEM AVAILABLE: {convert_size(mem_avail)}; [LARGEST] SINGLE FILE SIZE: {convert_size(single_file_size)}; BATCH SIZE: {round(batch_size,0)}"
                )
                self.logevent(
                    f"MEM AVAILABLE: {convert_size(mem_avail)}; [LARGEST] SINGLE FILE SIZE: {convert_size(single_file_size)}; BATCH SIZE: {round(batch_size,0)}"
                )
                n_processing_elements = len(file_keys)
                workers = self.get_nworkers()

                self.run_commands_in_parallel_with_executor(
                    [file_keys],
                    workers,
                    parallel_extract_slide_meta_data_and_insert_to_database,
                    batch_size,
                )
                self.update_database()  # may/will need revisions for parallel


    def get_user_entered_scan_id(self):
        """Get id in the "scan run" table for the current microspy scan that was entered by the user in the preparation phase"""
        return self.sqlController.scan_run.id

    def is_czi_file(self, czi_file):
        """Check if a file has the .czi extension"""
        extension = os.path.splitext(czi_file)[1]
        return extension.endswith("czi")

    def all_slide_meta_data_exists_in_database(self, czi_files):
        """Check if the number of czi files in the directory matches the number of entries in the database table 'Slide'"""
        nslides = (
            self.sqlController.session.query(Slide)
            .filter(Slide.scan_run_id == self.scan_id)
            .count()
        )
        print(
            f"SLIDES IN DB: {nslides}"
        )
        self.logevent(
            f"SLIDES IN DB: {nslides}"
        )
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
        try:
            files = os.listdir(INPUT)
            nfiles = len(files)
            if nfiles < 1:
                print("There are no CZI files to work with, we are exiting.")
                sys.exit()
            self.logevent(f"INPUT FOLDER: {INPUT}")
            self.logevent(f"FILE COUNT: {nfiles}")
            print(f"INPUT FOLDER: {INPUT}")
            print(f"FILE COUNT: {nfiles}")
        except OSError as e:
            print(e)
            sys.exit()

        return files

    def update_database(self):
        """Updates the "file log" table in the database that tracks the progress of the pipeline"""
        SLIDES_ARE_SCANNED = self.sqlController.get_progress_id(
            downsample=0, channel=0, action="SCAN"
        )
        CZI_FILES_ARE_PLACED_ON_BIRDSTORE = self.sqlController.get_progress_id(
            downsample=0, channel=0, action="BIRDSTORE"
        )
        CZI_FILES_ARE_SCANNED_TO_GET_METADATA = self.sqlController.get_progress_id(
            downsample=0, channel=0, action="META"
        )
        self.sqlController.set_task(self.animal, SLIDES_ARE_SCANNED)
        self.sqlController.set_task(self.animal, CZI_FILES_ARE_PLACED_ON_BIRDSTORE)
        self.sqlController.set_task(self.animal, CZI_FILES_ARE_SCANNED_TO_GET_METADATA)


def parallel_extract_slide_meta_data_and_insert_to_database(file_key):
    # function that gets submitted for parallel processing
    def load_metadata(czi_org_path):
        czi_file = os.path.basename(os.path.normpath(czi_org_path))
        czi = CZIManager(czi_org_path)
        czi.metadata = czi.extract_metadata_from_czi_file(czi_file, czi_org_path)
        return czi.metadata

    def add_slide_information_to_database(
        czi_org_path, scan_id, czi_metadata, animal, dbhost, dbschema
    ):
        """Add the meta information about image slides that are extracted from the czi file and add them to the database"""
        slide = Slide()
        slide.scan_run_id = scan_id
        slide.slide_physical_id = int(re.findall(r"slide\d+", czi_org_path)[0][5:])
        slide.rescan_number = "1"
        slide.slide_status = "Good"
        slide.processed = False
        slide.file_size = os.path.getsize(czi_org_path)
        slide.file_name = os.path.basename(os.path.normpath(czi_org_path))
        slide.created = datetime.fromtimestamp(
            Path(os.path.normpath(czi_org_path)).stat().st_mtime
        )
        slide.scenes = len(czi_metadata)
        print(
            f"ADD SLIDE INFO TO DB: {slide.file_name} -> PHYSICAL SLIDE ID: {slide.slide_physical_id}"
        )

        sqlController = SqlController(animal, dbhost, dbschema)

        sqlController.session.add(slide)
        sqlController.session.flush()
        sqlController.session.commit()

        """Add entry to the table that prepares the user Quality Control interface"""
        for series_index in range(slide.scenes):
            scene_number = series_index + 1
            channels = range(czi_metadata[slide.file_name][series_index]["channels"])
            channel_counter = 0

            width, height = czi_metadata[slide.file_name][series_index]["dimensions"]
            
            for channel in channels:
                tif = SlideCziTif()
                tif.FK_slide_id = slide.id
                tif.scene_number = scene_number
                tif.file_size = 0
                tif.active = 1
                tif.width = width
                tif.height = height
                tif.scene_index = series_index
                channel_counter += 1
                newtif = "{}_S{}_C{}.tif".format(
                    czi_org_path, scene_number, channel_counter
                )
                newtif = newtif.replace(".czi", "").replace("__", "_")
                tif.file_name = newtif
                tif.channel = channel_counter
                tif.processing_duration = 0
                tif.created = time.strftime("%Y-%m-%d %H:%M:%S")
                sqlController.session.add(tif)
            print(f"TOTAL CHANNELS: {channel_counter}")
        sqlController.session.commit()

    infile, scan_id, channel, animal, host, schema = file_key
    czi_metadata = load_metadata(infile)
    add_slide_information_to_database(
        infile, scan_id, czi_metadata, animal, host, schema
    )
    return
