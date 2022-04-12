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
from abakit.lib.FileLocationManager import FileLocationManager
from lib.MetaUtilities import MetaUtilities
from lib.PrepCreater import PrepCreater
from lib.NgPrecomputedMaker import NgPrecomputedMaker
from lib.NgDownsampler import NgDownsampler
from lib.ProgressLookup import ProgressLookup
from lib.TiffExtractor import TiffExtractor
from timeit import default_timer as timer
from abakit.lib.SqlController import SqlController
from lib.logger import get_logger
from lib.ParallelManager import ParallelManager
from lib.Normalizer import Normalizer
from lib.MaskManager import MaskManager
from lib.ImageCleaner import ImageCleaner
from lib.HistogramMaker import HistogramMaker
from lib.ElastixManager import ElastixManager

class Pipeline(MetaUtilities,TiffExtractor,PrepCreater,ParallelManager,Normalizer,MaskManager,\
    ImageCleaner,HistogramMaker,ElastixManager,NgPrecomputedMaker,NgDownsampler):
    '''
    A class that sets the methods and attributes for the Active Brain Atlas
    image processing pipeline
    '''
    def __init__(self, animal, channel=1, downsample=True,DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root',debug=False):
        '''
        Set i[ the pipeline. Only required parameter is animal
        :param animal: string, usually something like DKXX
        :param channel: integer defaults to 1, user enters 2 or 3 otherwise
        :param downsample: boolean, default to true for creating the smaller images
        '''
        self.animal = animal
        self.channel = channel
        self.ch_dir = f'CH{self.channel}'
        self.downsample = downsample
        self.debug = debug
        self.fileLocationManager =  FileLocationManager(animal,DATA_PATH = DATA_PATH)
        self.sqlController = SqlController(animal)
        self.hostname = self.get_hostname()
        self.load_parallel_settings()
        self.progress_lookup = ProgressLookup()
        self.logger = get_logger(animal)

    @staticmethod
    def check_programs():
        '''
        Make sure the necessary tools are installed on the machine.
        And the java heap size is big enough 10GB seems to work
        If it doesn't work, check the workernoshell.err.log
        for more info in the base directory of this program
        '''
        start = timer()
        os.environ["_JAVA_OPTIONS"] = "-Xmx10g"
        os.environ["export CV_IO_MAX_IMAGE_PIXELS"] = '21474836480'
        
        error = ""
        if not os.path.exists('/usr/local/share/bftools/showinf'):
            error += "showinf in bftools is not installed"
        if not os.path.exists('/usr/local/share/bftools/bfconvert'):
            error += "\nbfconvert in bftools is not installed"
        if not os.path.exists('/usr/bin/identify'):
            error += "\nImagemagick is not installed"
        if not which("java"):
            error += "\njava is not installed"
            
        if len(error) > 0:
            print(error)
            sys.exit()
        end = timer()
        print(f'Check programs took {end - start} seconds')    
    
    def run_program_and_time(self,function,function_name):
        print(function_name)
        time = timer()
        function()
        print(f'{function_name} took {timer()-time} seconds') 

    def prepare_image_for_quality_control(self):
        self.check_programs()
        self.run_program_and_time(self.extract_slide_meta_data_and_insert_to_database,'Creating meta')
        self.run_program_and_time(self.extract_tifs_from_czi,'Extracting Tiffs')
        if self.channel == 1 and self.downsample:
            self.run_program_and_time(self.create_web_friendly_image,'create web friendly image')

    def apply_qc_and_prepare_image_masks(self):
        self.run_program_and_time(self.make_full_resolution,'Making full resolution copies')
        self.run_program_and_time(self.make_low_resolution,'Making downsampled copies')
        self.set_task_preps()
        if self.channel == 1 and self.downsample:
            self.create_normalization()
            self.run_program_and_time(self.create_normalization,'Creating normalization')
        if self.channel == 1:
            self.create_mask()
            self.run_program_and_time(self.make_low_resolution,'Creating masks')
        
    def clean_images_and_create_histogram(self):
        if self.channel == 1 and self.downsample:
            self.run_program_and_time(self.apply_user_mask_edits,'Applying masks')
        self.run_program_and_time(self.create_cleaned_images,'Creating cleaned image')  
        if self.downsample:
            self.run_program_and_time(self.make_histogram,'Making histogram')  
            self.run_program_and_time(self.make_combined_histogram,'Making combined histogram')  
    
    def align_images_within_stack(self):
        start = timer()
        if self.channel == 1 and self.downsample:
            self.run_program_and_time(self.create_elastix,'Creating elastics transform')  
        transforms = self.parse_elastix()
        if self.downsample:
            self.align_downsampled_images(transforms)
        else:
            self.align_full_size_image(transforms)
        end = timer()
        print(f'Creating elastix and alignment took {end - start} seconds')   
        
    def create_neuroglancer_cloud_volume(self):
        start = timer()
        self.create_neuroglancer()
        self.create_downsamples()
        end = timer()
        print(f'Last step: creating neuroglancer images took {end - start} seconds')    