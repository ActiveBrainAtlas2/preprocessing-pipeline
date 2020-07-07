"""
Working with OpenCV
It is possible that you may need to use an image created using skimage with OpenCV or vice versa.
OpenCV image data can be accessed (without copying) in NumPy (and, thus, in scikit-image).
OpenCV uses BGR (instead of scikit-image’s RGB) for color images, and its dtype is
uint8 by default (See Image data types and what they mean). BGR stands for Blue Green Red.
Here is ID, values for the progress lookup table:
|  1 | Slides are scanned                     | prepipeline |
|  2 | CZI files are placed on birdstore      | prepipeline |
|  3 | CZI files are scanned to get metadata  | prepipeline |
|  4 | QC is one on slides in admin area      | prepipeline |
|  5 | CZI files are converted into TIF files | prepipeline |
|  6 | Thumbnails and histograms are created  | prepipeline |
|  7 | Section list is created and exported   | prepipeline |
"""

import os
import sys
import subprocess
import time
import re

import datajoint as dj
from datetime import datetime
from matplotlib import pyplot as plt
from skimage import io
from sqlalchemy.orm.exc import NoResultFound

from Litao.database_schema import AlcSlide, AlcSlideCziTif, AlcRawSection, AlcAnimal, AlcRawSection as RawSection
from Litao.file_location import FileLocationManager
from Litao.utilities_bioformats import get_czi_metadata, get_fullres_series_indices
from Litao.database_setup import schema, session


class PostCZIProcessor(object):
    """ Create a class for processing the pipeline after the CZI files are generated.
    The CZI files for the specified prep_id are assumed to be generated and uploaded to the correct folder on birdstore.
    """

    def __init__(self, prep_id):
        """ setup the attributes for the PostCZIProcessor class

        Args:
            prep_id: the prep_id of animal to process
        """

        try:
            animal = session.query(AlcAnimal).filter(AlcAnimal.prep_id == prep_id).one()
        except (NoResultFound):
            print('No results found for prep_id: {}.'.format(prep_id))
            sys.exit()

        self.animal = animal
        self.file_location_manager = FileLocationManager(self.animal.prep_id)
        self.scan_ids = [scan.id for scan in self.animal.scan_runs]

    def process_czi_dir(self):
        """ Read metadata from actual CZI files and populate Task, Slide and SlideCziToTif tables.
        After the CZI files are placed on birdstore, they need to be scanned to get the metadata for
        the tif files. Set the progress status here.
        """

        scan_id = max(self.scan_ids)
        '''
        lookup_ids = [1, 2, 3]
        session.query(Task).filter(Task.lookup_id.in_(lookup_ids)) \
            .filter(Task.prep_id == self.animal.prep_id) \
            .delete(synchronize_session=False)
        for i in lookup_ids:
            task = Task(self.animal.prep_id, i, True)
            session.add(task)

        session.commit()
        '''

        # Read CZI files from the folder
        try:
            czi_files = sorted(os.listdir(self.file_location_manager.czi))
        except OSError as e:
            print(e)
            sys.exit()

        # Delete existing rows in Slide table with same scan_id, if any
        session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).delete(synchronize_session=False)

        # For each CZI file, add a row to Slide table and add its TIF files to SlideCziTif table
        section_number = 1
        for i, czi_file in enumerate(czi_files):
            extension = os.path.splitext(czi_file)[1]
            if extension.endswith('czi'):
                # Get metadata from the czi file
                czi_file_path = os.path.join(self.file_location_manager.czi, czi_file)
                metadata_dict = get_czi_metadata(czi_file_path)
                series = get_fullres_series_indices(metadata_dict)

                # Insert Slide row
                slide = AlcSlide()
                slide.scan_run_id = scan_id
                slide.slide_physical_id = int(re.findall(r'\d+', czi_file)[1])
                slide.rescan_number = "1"
                slide.slide_status = 'Good'
                slide.processed = False
                slide.file_size = os.path.getsize(os.path.join(self.file_location_manager.czi, czi_file))
                slide.file_name = czi_file
                slide.created = datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(self.file_location_manager.czi, czi_file)))
                slide.scenes = len(series)

                session.add(slide)
                session.flush()

                for j, series_index in enumerate(series):
                    scene_number = j + 1
                    channels = range(metadata_dict[series_index]['channels'])
                    channel_counter = 0
                    width = metadata_dict[series_index]['width']
                    height = metadata_dict[series_index]['height']
                    for channel in channels:
                        channel_counter += 1
                        #new_tif = '{}_S{}_C{}.tif'.format(czi_file, scene_number, channel_counter)
                        #new_tif = new_tif.replace('.czi', '')
                        #print(new_tif)

                        tif = AlcSlideCziTif()
                        tif.slide_id = slide.id
                        tif.section_number = section_number
                        tif.scene_number = scene_number
                        tif.channel = channel_counter
                        #tif.file_name = new_tif
                        #tif.file_size = 0
                        tif.active = 1
                        #tif.width = width
                        #tif.height = height
                        tif.channel_index = channel
                        tif.scene_index = series_index
                        tif.processing_duration = 0
                        tif.created = time.strftime('%Y-%m-%d %H:%M:%S')
                        session.add(tif)
                    section_number += 1

        '''
        # lookup_id=3 is for the scanning CZI
        task = session.query(Task).filter(Task.lookup_id == 3) \
            .filter(Task.prep_id == self.animal.prep_id).one()
        task.end_date = datetime.now()
        session.merge(task)
        '''

        session.commit()

    @staticmethod
    def make_tif_file(czi_file, tif_file, scene_index, channel_index):
        """Convert CZI files to TIF files.
        Use bfconvert program to convert each CZI file to multiple TIF files.

        Args:
            czi_file: the path to the czi file
            tif_file: the path to the full resolution TIF file that will be generated
            scene_index: scene_index in the slide_czi_to_tif table
            channel_index: channel_index in the slide_czi_to_tif table

        Returns:
            bool: Indicator True for success, False otherwise.

        """
        if os.path.exists(tif_file):
            return True

        if os.path.exists(czi_file):
            os.makedirs(os.path.dirname(tif_file), exist_ok=True)

            command = ['/usr/local/share/bftools/bfconvert', '-bigtiff', '-compression', 'LZW', '-separate',
                       '-series', str(scene_index), '-channel', str(channel_index),
                       '-nooverwrite', czi_file, tif_file]
            completed_process = subprocess.run(command, capture_output=True)
        else:
            print('No source file', tif_file)
            return False

        if completed_process.returncode != 0:
            print(completed_process.stderr.decode('ascii'))
            return False

        return True

    @staticmethod
    def make_histogram_file(tif_file, histogram_file, channel):
        """Make histogram image from each full resolution tif file.

        Args:
            tif_file: the path to the full resolution TIF file
            histogram_file: the path to the histogram file that will be generated
            channel: the channel of the TIF file

        Returns:
            bool: Indicator True for success, False otherwise.

        """
        if os.path.exists(histogram_file):
            return True

        if os.path.exists(tif_file):
            try:
                img = io.imread(tif_file)
            except:
                return False

            if img.shape[0] * img.shape[1] > 1000000000:
                scale = 1 / float(2)
                img = img[::int(1. / scale), ::int(1. / scale)]

            try:
                flat = img.flatten()
            except:
                return False

            COLORS = {1: 'b', 2: 'r', 3: 'g'}
            fig = plt.figure()
            plt.rcParams['figure.figsize'] = [10, 6]
            plt.hist(flat, flat.max(), [0, flat.max()], color=COLORS[channel])
            plt.style.use('ggplot')
            plt.yscale('log')
            plt.grid(axis='y', alpha=0.75)
            plt.xlabel('Value')
            plt.ylabel('Frequency')
            plt.title(f'{os.path.basename(tif_file)} @16bit')
            plt.close()

            os.makedirs(os.path.dirname(histogram_file), exist_ok=True)
            fig.savefig(histogram_file, bbox_inches='tight')
        else:
            print('No source file', tif_file)
            return False

        return True

    @staticmethod
    def make_thumbnail_file(tif_file, thumbnail_file):
        """Create the thumbnail file from each full resolution TIF file

        Args:
            tif_file: the path to the full resolution TIF file
            thumbnail_file: the path to the thumbnail file that will be generated

        Returns:
            bool: Indicator True for success, False otherwise.

        """
        if os.path.exists(thumbnail_file):
            return True

        if os.path.exists(tif_file):
            os.makedirs(os.path.dirname(thumbnail_file), exist_ok=True)

            command = ['convert', tif_file, '-resize', '3.125%', '-auto-level',
                       '-normalize', '-compress', 'lzw', thumbnail_file]
            completed_process = subprocess.run(command, capture_output=True)
        else:
            print('No source file', tif_file)
            return False

        if completed_process.returncode != 0:
            print(completed_process.stderr.decode('ascii'))
            return False

        return True

    @staticmethod
    def make_thumbnail_web_file(thumbnail_file, png_file):
        """Create the png thumbnail file from each TIF thumbnail file

        Args:
            thumbnail_file: the path to the thumbnail file
            png_file: the path to the web thumbnail file that will be genearted

        Returns:
            bool: Indicator True for success, False otherwise.

        """
        if os.path.exists(png_file):
            return True

        if os.path.exists(thumbnail_file):
            os.makedirs(os.path.dirname(png_file), exist_ok=True)

            command = ['convert', thumbnail_file, png_file]
            completed_process = subprocess.run(command, capture_output=True)
        else:
            print('No source file', thumbnail_file)
            return False

        if completed_process.returncode != 0:
            print(completed_process.stderr.decode('ascii'))
            return False

        return True

    def make_tif_datajoint(self, debug=False):
        """ The wrapper function to invoke datajoint's autopopulate method for "make_tif" operation.
        To speed up, you can run this method on different machines at the same time.

        Args:
            debug: whether to print the debug message
        """

        global dj_make_tif_params

        restrictions = [RawSection & f'prep_id="{self.animal.prep_id}" and active=1']
        MakeTifOperation.populate(restrictions, display_progress=debug)

    def make_histogram_datajoint(self, debug=False):
        """ The wrapper function to invoke datajoint's autopopulate method for "make_histogram" operation.
        To speed up, you can run this method on different machines at the same time.

        Args:
            debug: whether to print the debug message
        """

        global dj_make_histogram_params

        restrictions = [RawSection & f'prep_id="{self.animal.prep_id}" and active=1']
        MakeHistogramOperation.populate(restrictions, display_progress=debug)

    def make_thumbnail_datajoint(self, debug=False):
        """ The wrapper function to invoke datajoint's autopopulate method for "make_thumbnail" operation.
        To speed up, you can run this method on different machines at the same time.

        Args:
            debug: whether to print the debug message
        """

        global dj_make_thumbnail_params

        restrictions = [RawSection & f'prep_id="{self.animal.prep_id}" and active=1']
        MakeThumbnailOperation.populate(restrictions, display_progress=debug)

    def make_thumbnail_web_datajoint(self, debug=False):
        """ The wrapper function to invoke datajoint's autopopulate method for "make_mask_web" operation.
        To speed up, you can run this method on different machines at the same time.

        Args:
            debug: whether to print the debug message
        """

        global dj_make_thumbnail_web_params

        restrictions = [RawSection & f'prep_id="{self.animal.prep_id}" and active=1']
        MakeThumbnailWebOperation.populate(restrictions, display_progress=debug)


"""
Below are the definitions of datajoint tables required for the operations in the PostCziProcessor.

Because of the stupidity of datajoint's not allowing pass parameters to the make function, the parameters have to be 
global variables. Thus, the parameters for each operation are in a dictionary that will be fulfilled in the datajoint 
wrapper functions. 
"""

dj_make_tif_params = {
}
dj_make_histogram_params = {
}
dj_make_thumbnail_params = {
}
dj_make_thumbnail_web_params = {
}


@schema
class MakeTifOperation(dj.Computed):
    definition = """
    -> RawSection
    ---
    duration : float
    """

    def make(self, key):
        raw_section_row = session.query(AlcRawSection).filter(AlcRawSection.id == key['id']).one()
        slide_czi_tif_row = session.query(AlcSlideCziTif).filter(AlcSlideCziTif.id == raw_section_row.tif_id).one()
        slide_row = session.query(AlcSlide).filter(AlcSlide.id == slide_czi_tif_row.slide_id).one()

        file_location_manager = FileLocationManager(raw_section_row.prep_id)
        czi_file = os.path.join(file_location_manager.czi, slide_row.file_name)
        tif_file = os.path.join(file_location_manager.tif, raw_section_row.destination_file)
        scene_index = slide_czi_tif_row.scene_index
        channel_index = slide_czi_tif_row.channel_index

        start = time.time()
        success = PostCZIProcessor.make_tif_file(czi_file, tif_file, scene_index, channel_index)
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))


@schema
class MakeHistogramOperation(dj.Computed):
    definition = """
    -> RawSection
    ---
    duration : float
    """

    def make(self, key):
        raw_section_row = session.query(AlcRawSection).filter(AlcRawSection.id == key['id']).one()

        file_location_manager = FileLocationManager(raw_section_row.prep_id)
        tif_file = os.path.join(file_location_manager.tif, raw_section_row.destination_file)
        histogram_file = os.path.join(file_location_manager.histogram,
                                      os.path.splitext(raw_section_row.destination_file)[0] + '.png')

        start = time.time()
        success = PostCZIProcessor.make_histogram_file(tif_file, histogram_file, raw_section_row.channel)
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))


@schema
class MakeThumbnailOperation(dj.Computed):
    definition = """
    -> RawSection
    ---
    duration : float
    """

    def make(self, key):
        raw_section_row = session.query(AlcRawSection).filter(AlcRawSection.id == key['id']).one()

        file_location_manager = FileLocationManager(raw_section_row.prep_id)
        tif_file = os.path.join(file_location_manager.tif, raw_section_row.destination_file)
        thumbnail_file = os.path.join(file_location_manager.thumbnail,
                                      os.path.splitext(raw_section_row.destination_file)[0] + '.tif')

        start = time.time()
        success = PostCZIProcessor.make_thumbnail_file(tif_file, thumbnail_file)
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))


@schema
class MakeThumbnailWebOperation(dj.Computed):
    definition = """
    -> RawSection
    ---
    duration : float
    """

    def make(self, key):
        raw_section_row = session.query(AlcRawSection).filter(AlcRawSection.id == key['id']).one()

        file_location_manager = FileLocationManager(raw_section_row.prep_id)
        thumbnail_file = os.path.join(file_location_manager.tif, raw_section_row.destination_file)
        png_file = os.path.join(file_location_manager.thumbnail_web,
                                os.path.splitext(raw_section_row.destination_file)[0] + '.png')

        start = time.time()
        success = PostCZIProcessor.make_thumbnail_web_file(thumbnail_file, png_file)
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))
