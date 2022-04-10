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
import yaml
import socket
import multiprocessing

class Pipeline:
    '''
    A class that sets the methods and attributes for the Active Brain Atlas
    image processing pipeline
    '''
    def __init__(self, animal, channel=1, downsample=True, debug=False):
        '''
        Set i[ the pipeline. Only required parameter is animal
        :param animal: string, usually something like DKXX
        :param channel: integer defaults to 1, user enters 2 or 3 otherwise
        :param downsample: boolean, default to true for creating the smaller images
        '''
        self.animal = animal
        self.channel = channel
        self.downsample = downsample
        self.debug = debug
        self.fileLocationManager =  FileLocationManager(animal)
        self.hostname = self.get_hostname()
        self.load_parallel_settings()
        
    def load_parallel_settings(self):
        '''
        There was a LOT of effort in getting the numbers below. Unless you have
        done lots of testing with full and downsampled images, don't change them!
        Feel free to add another host/workstation.
        '''
        usecpus = 4
        cpus = {}
        cpus['mothra'] = 1
        cpus['muralis'] = 12
        cpus['basalis'] = 6
        cpus['ratto'] = 6
        host = self.hostname
        if host in cpus.keys():
            usecpus = cpus[host]
            
        self.parallel_settings = usecpus
            
    def get_hostname(self):
        hostname = socket.gethostname()
        hostname = hostname.split(".")[0]
        return hostname

    def get_nworkers(self, downsample=True):
        '''
        get the number of cpus/processes to spawn. There is only one number
        per machine. The downsampled get processed so quickly, that there is
        no real reason to set a higher number for the downsampled.
        :param downsample: boolean, True for downsampled images
        '''
        nworkers = self.parallel_settings
        print(f'working with workers {nworkers}')
        return nworkers

    def create_meta(self):
        """
        The CZI file need to be present. Test to make sure the dir exists
        and there are some files there.
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
        print(f'create meta is working with {nfiles} files.')
        make_meta(self.animal)

                
    def create_tifs(self):
        '''
        This method creates the tifs from the czi files. The files are used for the create_preps method
        It also creates the scenes under data/DKXX/www/scenes
        '''
        make_tifs(self.animal, self.channel,self.get_nworkers())
        if self.channel == 1 and self.downsample:
            make_scenes(self.animal)


    def create_preps(self):
        """
        Creates the tifs. These need to be checked in the DB before
        proceeding to the create_preps step
        """
        make_full_resolution(self.animal, self.channel,self.get_nworkers())
        make_low_resolution(self.animal, self.channel, self.debug,self.get_nworkers())
        set_task_preps(self.animal, self.channel)

    
    def create_normalized(self):
        '''
        This method creates the histogram equalized channel 1 downampled files.
        These are used by the user to easily see the images.
        '''
        if self.channel == 1 and self.downsample:
            create_normalization(self.animal, self.channel)

    
    def create_masks(self):
        """
        After running this step, the masks need to manually checked and if 
        needed, edited with GIMP, see the Process.md file for instructions.
        This creates the masks in preps/masks/thumbnail_colored
        If downsample is False and we are creating full scale masks,
        the masks are created in preps/masks/full_masked
        """
        if self.channel == 1:
            create_mask(self.animal, self.downsample)

    
    def create_masks_final(self):
        '''
        This is the 2nd step in the masking process. It is performed
        after the user verifies and possibly edits the colored masks
        Creates the black/white masks in preps/masks/thumbnail_masked
        Only run on the downsampled images
        '''
        if self.channel == 1 and self.downsample:
            create_final(self.animal)
    
    def create_histograms(self, single):
        '''
        Creates histograms for each image (single=True)
        Also creates a combined histogram with data from all downsampled
        images (single=False)
        :param single: boolean, single=True means a histogram is created for
        every single image. Otherwise, single=False means all the images are
        combined and the data is aggregated into one histogram.
        '''
        if self.downsample:
            if single:
                make_histogram(self.animal, self.channel)
            else:
                make_combined(self.animal, self.channel)

    
    def create_clean(self):
        '''
        Uses the data from preps/masks/thumbnail_masked to mask 
        for the downsampled and preps/masks/full_masked for the full resolution
        images. Resulting images are in preps/CHX/thumbnail_cleaned
        and preps/CHX/full_cleaned
        '''
        masker(self.animal, self.channel, self.downsample, self.debug)

    
    def create_elastix(self):
        '''
        This runs the elastix section-section alignment process.
        The resulting transformation rotation, xshift and yshift is
        stored in the elastix_transformation table.
        This method is only run when channel=1 and downsample=True
        '''
        if self.channel == 1 and self.downsample:
            create_elastix(self.animal)

    
    def create_aligned(self):
        '''
        This gets run on all downsampled and full res and all 3 channels. It
        fetches the data from the elastix_transformation table and then uses
        PIL to rotate, shift the image.
        '''
        transforms = parse_elastix(self.animal)
        masks = False 
        create_csv = False
        allen = False
        run_offsets(self.animal, transforms, self.channel, self.downsample, masks, create_csv, allen)

    
    def create_web(self):
        '''
        Creates png files from the thumbnail_cleaned dir and puts them in the www/
        directory.
        '''
        make_web_thumbnails(self.animal)
    
    def create_neuroglancer_image(self):
        '''
        This the first step in the neuroglancer process. Data is created
        in the DKXX/neuroglancer_data/CX_rechunkme directory
        '''
        create_neuroglancer(self.animal, self.channel, self.downsample, self.debug)

    
    def create_downsampling(self):
        '''
        This the second step in the neuroglancer process. Data is pulled
        from the previous step in the DKXX/neuroglancer_data/CX_rechunkme dir
        and it then creates the appropriate chunks and pyramids in the 
        DKXX/neuroglancer_data/CX directory
        '''
        create_downsamples(self.animal, self.channel, self.downsample)
        
    @staticmethod
    def check_programs():
        '''
        Make sure the necessary tools are installed on the machine.
        And the java heap size is big enough 10GB seems to work
        If it doesn't work, check the workernoshell.err.log
        for more info in the base directory of this program
        '''
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

        
