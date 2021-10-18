"""
This class can be used to run an entire pipeline.
Args are animal, channel, and downsample. With animal being
the only required argument.
All imports are listed by the order in which they are used in the pipeline.
"""

import os
import sys
from shutil import which



from lib.file_location import FileLocationManager
from lib.utilities_meta import make_meta
from lib.utilities_preps import make_full_resolution, make_low_resolution, set_task_preps
from lib.utilities_process import make_tifs, make_scenes
from lib.utilities_normalized import create_normalization
from lib.utilities_create_masks import create_final,create_mask
from lib.utilities_histogram import make_combined,make_histogram
from lib.utilities_clean import masker
from lib.utilities_elastics import create_elastix
from lib.utilities_create_alignment import parse_elastix, run_offsets
from lib.utilities_web import make_web_thumbnails
from lib.utilities_neuroglancer_image import create_neuroglancer
from lib.utilities_downsampling import create_downsamples





class Pipeline:
    def __init__(self, animal, channel=1, downsample=True):
        self.animal = animal
        self.channel = channel
        self.downsample = downsample
        self.debug = False
        self.fileLocationManager =  FileLocationManager(animal)

        
    def create_meta(self):
        """
        The CZI file need to be present
        """
        INPUT = self.fileLocationManager.czi
        if not os.path.exists(INPUT):
            print(f'{INPUT} does not exist, we are exiting.')
            sys.exit()
        files = os.listdir(INPUT)
        nfiles = len(files)
        if nfiles < 1:
            print('There are no CZI files to work with, we are exiting.')
            sys.exit()
        print(f'Working with {nfiles} files.')
        make_meta(self.animal)

                
    def create_tifs(self):
        make_tifs(self.animal, self.channel)
        print('channel', self.channel, type(channel))
        print('downsamle', self.downsample, type(downsample))
        if self.channel == 1 and self.downsample:
            make_scenes(self.animal)


    def create_preps(self):
        """
        Creates the tifs. These need to be checked in the DB before
        proceeding to the create_preps step
        """
        make_full_resolution(self.animal, self.channel)
        make_low_resolution(self.animal, self.channel, self.debug)
        set_task_preps(self.animal, self.channel)

    
    def create_normalized(self):
        if self.channel == 1 and bool(self.downsample):
            create_normalization(self.animal, self.channel)

    
    def create_masks(self):
        """
        After running this step, the masks need to manually checked and if 
        needed, edited with GIMP, see the Process.md file for instructions.
        """
        if self.channel == 1 and bool(self.downsample):
            create_mask(self.animal, self.downsample)

    
    def create_masks_final(self):
        if self.channel == 1 and bool(self.downsample):
            create_final(self.animal)
    
    def create_histograms(self, single):
        if self.channel == 1 and bool(self.downsample):
            if single:
                make_histogram(self.animal, self.channel)
            else:
                make_combined(self.animal, self.channel)

    
    def create_clean(self):
        masker(self.animal, self.channel, self.downsample, self.debug)

    
    def create_elastix(self):
        if self.channel == 1 and bool(self.downsample):
            create_elastix(self.animal)

    
    def create_alignment(self):
        transforms = parse_elastix(self.animal)
        masks = False 
        create_csv = False
        allen = False
        run_offsets(self.animal, transforms, self.channel, self.downsample, masks, create_csv, allen)

    
    def create_web(self):
        make_web_thumbnails(self.animal)

    
    def create_neuroglancer_image(self):
        create_neuroglancer(self.animal, self.channel, self.downsample, self.debug)

    
    def create_downsampling(self):
        create_downsamples(self.animal, self.channel, self.downsample)
        
    @staticmethod
    def check_programs():
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

        
