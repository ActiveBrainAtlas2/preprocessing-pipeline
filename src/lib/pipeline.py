"""
This class is used to run the entire preprocessing pipeline - 
from CZI files to a pyramid of tiles that can be viewed in neuroglancer.

Args are animal, channel, and downsample. With animal being
the only required argument.
All imports are listed by the order in which they are used in the pipeline.
"""

import os
import sys
from shutil import which
import glob

# from abakit.lib.FileLocationManager import FileLocationManager
from lib.FileLocationManager import FileLocationManager
from lib.MetaUtilities import MetaUtilities
from lib.PrepCreater import PrepCreater
from lib.NgPrecomputedMaker import NgPrecomputedMaker
from lib.NgDownsampler import NgDownsampler
from lib.ProgressLookup import ProgressLookup
from lib.TiffExtractor import TiffExtractor
from timeit import default_timer as timer
from abakit.lib.Controllers.SqlController import SqlController
from lib.FileLogger import FileLogger
from lib.logger import get_logger
from lib.ParallelManager import ParallelManager
from lib.Normalizer import Normalizer
from lib.MaskManager import MaskManager
from lib.ImageCleaner import ImageCleaner
from lib.HistogramMaker import HistogramMaker
from lib.ElastixManager import ElastixManager


class Pipeline(
    MetaUtilities,
    TiffExtractor,
    PrepCreater,
    ParallelManager,
    Normalizer,
    MaskManager,
    ImageCleaner,
    HistogramMaker,
    ElastixManager,
    NgPrecomputedMaker,
    NgDownsampler,
    FileLogger,
):
    """
    This is the main class that handles the preprocessing pipeline responsible for converting Zeiss microscopy images (.czi) into neuroglancer
    viewable formats.  The Zeiss module can be swapped out to make the pipeline compatible with other microscopy setups
    """

    def __init__(
        self,
        animal,
        channel=1,
        downsample=True,
        DATA_PATH="/net/birdstore/Active_Atlas_Data/data_root",
        debug=False,
        host="db.dk.ucsd.edu",
        schema="active_atlas_production",
    ):
        """Setting up the pipeline and the processing configurations
           The pipeline performst the following steps:
           1. extracting the images from the microscopy formats (eg czi) to tiff format
           2. Prepare thumbnails of images for quality control
           3. clean the images
           4. align the images
           5. convert to Seung lab neuroglancer cloudvolume format

           step 3 and 4 are first performed on downsampled images, and the image masks(for step 3) and the within stack alignments(for step 4) are
           upsampled for use in the full resolution images

        Args:
            animal (str): Animal Id
            channel (int, optional): channel number.  This tells the program which channel to work on and which channel to extract from the czis. Defaults to 1.
            downsample (bool, optional): Determine if we are working on the full resolution or downsampled version. Defaults to True.
            DATA_PATH (str, optional): path to where the images and intermediate steps are stored. Defaults to '/net/birdstore/Active_Atlas_Data/data_root'.
            debug (bool, optional): determine if we are in debug mode.  This is used for development purposes. Defaults to False. (forces processing on single core)
        """
        self.animal = animal
        self.channel = channel
        self.ch_dir = f"CH{self.channel}"
        self.downsample = downsample
        self.debug = debug
        self.fileLocationManager = FileLocationManager(animal, DATA_PATH=DATA_PATH)
        self.sqlController = SqlController(animal, host, schema)
        self.hostname = self.get_hostname()
        self.load_parallel_settings()
        self.progress_lookup = ProgressLookup()
        # self.logger = get_logger(animal,self.sqlController.session)
        self.check_programs()

    @staticmethod
    def check_programs():
        """
        Make sure the necessary tools are installed on the machine and configures the memory of involving tools to work with
        big images.
        Some tools we use are based on java so we adjust the java heap size limit to 10 GB.  This is big enough for our purpose but should
        be increased accordingly if your images are bigger
        If the check failed, check the workernoshell.err.log in your project directory for more information
        """
        start = timer()
        os.environ["_JAVA_OPTIONS"] = "-Xmx10g"
        os.environ["export CV_IO_MAX_IMAGE_PIXELS"] = "21474836480"

        error = ""
        if not os.path.exists("/usr/local/share/bftools/showinf"):
            error += "showinf in bftools is not installed"
        if not os.path.exists("/usr/local/share/bftools/bfconvert"):
            error += "\nbfconvert in bftools is not installed"
        if not os.path.exists("/usr/bin/identify"):
            error += "\nImagemagick is not installed"
        if not which("java"):
            error += "\njava is not installed"

        if len(error) > 0:
            print(error)
            sys.exit()
        end = timer()
        print(f"Check programs took {end - start} seconds")

    def run_program_and_time(self, function, function_name):
        """utility to run a specific function and time it

        Args:
            function (function): funtion to run
            function_name (str): name of the function used to report timing result
        """
        print(function_name)
        time = timer()

        self.logevent("START " + str(function_name))
        if function_name == "Extracting Tiffs":
            starting_files = glob.glob(
                os.path.join(self.fileLocationManager.tif, "*.tif")
            )
            self.logevent(f"OUTPUT FOLDER: {self.fileLocationManager.tif}")
            self.logevent(f"CURRENT FILE COUNT: {len(starting_files)}")
        elif function_name == "create web friendly image":
            self.logevent(f"OUTPUT FOLDER: {self.fileLocationManager.thumbnail_web}")
        else:
            pass

        function()  # RUN FUNCTION
        message = f"{function_name} took {timer()-time} seconds"
        print(message)
        # self.logger.info(message)

        sep = "*" * 40 + "\n"
        if function_name == "Extracting Tiffs":
            ending_files = glob.glob(
                os.path.join(self.fileLocationManager.tif, "*.tif")
            )
            self.logevent(f"CURRENT (FINAL) FILE COUNT: {len(ending_files)}")

            if ending_files != starting_files:
                endtime = timer()
                self.logevent(f"AGGREGATE: {function_name} took {endtime-time} seconds")
                print(type(ending_files), ending_files)
                unitary_calc = (endtime - time) / len(ending_files)
                self.logevent(
                    f"TIME PER FILE CREATION (seconds): {str(unitary_calc)}\n{sep}"
                )
            else:
                self.logevent(f"NOTHING TO PROCESS - ALL TIFF FILES EXTRACTED\n{sep}")
                self.logevent(f"CALCULATE FILE CHECKSUMS\n{sep}")
                # self.create_filechecksums()

        else:
            self.logevent(f"{function_name} took {timer()-time} seconds\n{sep}")

    def prepare_image_for_quality_control(self):
        """This is the first step of the pipeline.  The images are extracted from the CZI files,
        logged in the database, and downsampled to a web friendly size.  These preparations makes
        it possible to preview the images on the django database admin portal, allowing the user to
        perform quality control on the images.  The user can determine to mark slides or sections
        on a slide as insufficient in quality, and replace them with adjuscent slide or sections

        1) extract meta info
        2) extract tiffs from czi
        3) create png files (downsampled)
        """
        self.run_program_and_time(
            self.extract_slide_meta_data_and_insert_to_database, "Creating meta"
        )

        self.run_program_and_time(self.extract_tifs_from_czi, "Extracting Tiffs")
        if self.channel == 1 and self.downsample:
            self.run_program_and_time(
                self.create_web_friendly_image, "create web friendly image"
            )

    def apply_qc_and_prepare_image_masks(self):
        """This function performs 2 steps:
        1. Applies the QC result that the user provides on the Django database admin portal and prepares a copy
        of the tiff files that reflects the image/slide exclusion and replacement decisions made by user.
        Following steps in the pipeline then use this copy as the input
        2. Use a CNN based machine learning algorism to create masks around the tissue.
           These masks will be used to crop out the tissue from the surrounding debres.
        """
        self.run_program_and_time(
            self.apply_QC_to_full_resolution_images, "Making full resolution copies"
        )
        self.run_program_and_time(self.make_low_resolution, "Making downsampled copies")
        self.set_task_preps()
        if self.channel == 1 and self.downsample:
            self.run_program_and_time(
                self.create_normalized_image, "Creating normalization"
            )
        if self.channel == 1:
            self.run_program_and_time(self.create_mask, "Creating masks")

    def clean_images_and_create_histogram(self):
        """This function performs the following steps:
        1. apply the Edits of images masks made by user
        2. create the cleaned images using the image masks
        3. making a histogram of pixel intensity for view in the Django admin portal
        """
        if self.channel == 1 and self.downsample:
            self.run_program_and_time(self.apply_user_mask_edits, "Applying masks")
        self.run_program_and_time(self.create_cleaned_images, "Creating cleaned image")
        if self.downsample:
            self.run_program_and_time(self.make_histogram, "Making histogram")
            self.run_program_and_time(
                self.make_combined_histogram, "Making combined histogram"
            )

    def align_images_within_stack(self):
        """This function calculates the rigid transformation used to align the images within stack and applies them to the image"""
        start = timer()
        if self.channel == 1 and self.downsample:
            self.run_program_and_time(
                self.create_within_stack_transformations, "Creating elastics transform"
            )
        transformations = self.get_transformations()
        if self.downsample:
            self.align_downsampled_images(transformations)
        else:
            self.align_full_size_image(transformations)
        end = timer()
        print(f"Creating elastix and alignment took {end - start} seconds")

    def create_neuroglancer_cloud_volume(self):
        """This function creates the Seung lab neuroglancer cloud volume folders that is required to view the images in neuroglancer"""
        start = timer()
        self.create_neuroglancer()
        self.create_downsamples()
        end = timer()
        print(f"Last step: creating neuroglancer images took {end - start} seconds")
