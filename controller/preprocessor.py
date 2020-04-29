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

from sqlalchemy.orm.exc import NoResultFound
import os, sys, subprocess, time
from datetime import datetime
from matplotlib import pyplot as plt
from skimage import io
from skimage.util import img_as_uint
import numpy as np
import re

from model.section import RawSection
from .bioformats_utilities import get_czi_metadata, get_fullres_series_indices
from model.animal import Animal
from model.histology import Histology as AlcHistology
from model.scan_run import ScanRun as AlcScanRun
from model.slide import Slide as AlcSlide
from model.slide_czi_to_tif import SlideCziTif as AlcSlideCziTif
from model.task import Task
from sql_setup import dj, database
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
schema = dj.schema(database)


class SlideProcessor(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, prep_id, session):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
                session: sql session to run queries
        """
        try:
            animal = session.query(Animal).filter(Animal.prep_id == prep_id).one()
        except (NoResultFound):
            print('No results found for prep_id: {}.'.format(prep_id))
            sys.exit()

        self.animal = animal
        self.session = session
        self.scan_ids = [scan.id for scan in self.animal.scan_runs]
        self.fileLocationManager = FileLocationManager(animal.prep_id)

    def process_czi_dir(self):
        """
        After the CZI files are placed on birdstore, they need to be scanned to get the metadata for
        the tif files. Set the progress status here.
        """
        lookup_ids = [1,2,3]
        scan_id = max(self.scan_ids)
        self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).delete(synchronize_session=False)
        self.session.query(Task).filter(Task.lookup_id.in_(lookup_ids))\
            .filter(Task.prep_id == self.animal.prep_id)\
            .delete(synchronize_session=False)
        for i in lookup_ids:
            task = Task(self.animal.prep_id, i, True)
            self.session.add(task)

        self.session.commit()

        try:
            czi_files = sorted(os.listdir(self.fileLocationManager.czi))
        except OSError as e:
            print(e)
            sys.exit()

        section_number = 1
        for i, czi_file in enumerate(czi_files):
            extension = os.path.splitext(czi_file)[1]
            if extension.endswith('czi'):
                slide = AlcSlide()
                slide.scan_run_id = scan_id
                slide.slide_physical_id = int(re.findall(r'\d+', czi_file)[1])
                slide.rescan_number = "1"
                slide.slide_status = 'Good'
                slide.processed = False
                slide.file_size = os.path.getsize(os.path.join(self.fileLocationManager.czi, czi_file))
                slide.file_name = czi_file
                slide.created = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.fileLocationManager.czi, czi_file)))

                # Get metadata from the czi file
                czi_file_path = os.path.join(self.fileLocationManager.czi, czi_file)
                metadata_dict = get_czi_metadata(czi_file_path)
                #print(metadata_dict)
                series = get_fullres_series_indices(metadata_dict)
                slide.scenes = len(series)
                self.session.add(slide)
                self.session.flush()


                for j, series_index in enumerate(series):
                    scene_number = j + 1
                    channels = range(metadata_dict[series_index]['channels'])
                    channel_counter = 0
                    width = metadata_dict[series_index]['width']
                    height = metadata_dict[series_index]['height']
                    for channel in channels:
                        channel_counter += 1
                        newtif = '{}_S{}_C{}.tif'.format(czi_file, scene_number, channel_counter)
                        newtif = newtif.replace('.czi','')
                        tif = AlcSlideCziTif()
                        tif.slide_id = slide.id
                        tif.section_number = section_number
                        tif.scene_number = scene_number
                        tif.channel = channel_counter
                        tif.file_name = newtif
                        tif.file_size = 0
                        tif.active = 1
                        tif.width = width
                        tif.height = height
                        tif.channel_index = channel
                        tif.scene_index = series_index
                        tif.processing_duration = 0
                        tif.created = time.strftime('%Y-%m-%d %H:%M:%S')
                        print(newtif)
                        self.session.add(tif)
                    section_number += 1
        # lookup_id=3 is for the scanning CZI
        task =   self.session.query(Task).filter(Task.lookup_id == 3)\
        .filter(Task.prep_id == self.animal.prep_id).one()
        task.end_date = datetime.now()
        self.session.merge(task)

        self.session.commit()


    def update_tif_data(self):
        try:
            os.listdir(self.fileLocationManager.tif)
        except OSError as e:
            print(e)
            sys.exit()

        slides = self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).filter(AlcSlide.slide_status=='Good').all()
        slide_ids = [slide.id for slide in slides]
        tifs = self.session.query(AlcSlideCziTif).filter(AlcSlideCziTif.slide_id.in_(slide_ids)).filter(AlcSlideCziTif.active==1).all()
        for tif in tifs:
            if os.path.exists(os.path.join(self.fileLocationManager.tif, tif.file_name)):
                tif.file_size = os.path.getsize(os.path.join(self.fileLocationManager.tif, tif.file_name))
                self.session.merge(tif)
        self.session.commit()


    def compare_tif(self):
        INPUT = self.fileLocationManager.tif

        slides = self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids))
        slide_ids = [slide.id for slide in slides]
        tifs = self.session.query(AlcSlideCziTif).filter(AlcSlideCziTif.slide_id.in_(slide_ids)).filter(active=1)
        for tif in tifs:
            input_tif = os.path.join(INPUT, tif.file_name)
            img = io.imread(input_tif)
            print(img.shape)
            print(tif.width, tif.height)
            if img.shape[3] != tif.height or img.shape[4] != tif.width:
                print(f'The information about {tif.file_name} is inconsistent')

    def test_tables(self):
        try:
            animal = self.session.query(Animal).filter(Animal.prep_id == self.animal.prep_id).one()
        except (NoResultFound):
            print('No results found for prep_id: {}.'.format(animal.prep_id))

        try:
            self.session.query(AlcHistology).filter(AlcHistology.prep_id == animal.prep_id).all()
        except (NoResultFound):
            print('No histology results found for prep_id: {}.'.format(animal.prep_id))

        try:
            self.session.query(AlcScanRun).filter(AlcScanRun.prep_id == animal.prep_id).all()
        except (NoResultFound):
            print('No scan run results found for prep_id: {}.'.format(animal.prep_id))

        try:
            self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).all()
        except (NoResultFound):
            print('No slides found for prep_id: {}.'.format(animal.prep_id))

        try:
            slides = self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).all()
            slides_ids = [slide.id for slide in slides]
            tifs = self.session.query(AlcSlideCziTif).filter(AlcSlideCziTif.slide_id.in_(slides_ids))
            print('Found {} tifs'.format(tifs.count()))
        except (NoResultFound):
            print('No tifs found for prep_id: {}.'.format(animal.prep_id))


    # End of table definitions

    def make_thumbnail(self, file_id, file_name, testing=False):
        """
        This will create a tif in the preps dir that are used throughout the pipeline
        """
        result = 0
        rsection = self.session.query(RawSection).filter(RawSection.id == file_id).one()
        source = os.path.join(self.fileLocationManager.tif, file_name)
        prep_destination = os.path.join(self.fileLocationManager.thumbnail_prep, rsection.destination_file)
        # Create thumbnails
        # if source exists
        if testing:
            command = ['touch', prep_destination]
            subprocess.run(command)
            return 1
        if os.path.exists(source):
            # if the prep thumbnail exists
            if  not os.path.exists(prep_destination):
                command = ['convert', source, '-resize', '3.125%', '-auto-level',
                           '-normalize', '-compress', 'lzw', prep_destination]
                subprocess.run(command)
        else:
            print('No source file', source)

        return result

    def make_web_thumbnail(self, file_id, file_name, testing=False):
        """
        This will create a png in the web thumbnail dir
        """
        result = 0
        rsection = self.session.query(RawSection).filter(RawSection.id == file_id).one()
        prep_destination = os.path.join(self.fileLocationManager.thumbnail_prep, rsection.destination_file)
        # Create thumbnails if prep thumbnail exists
        if os.path.exists(prep_destination):
            base = os.path.splitext(rsection.destination_file)[0]
            output_png = os.path.join(self.fileLocationManager.thumbnail_web, base + '.png')
            #  test for the web thumbnail
            if testing:
                command = ['touch', output_png]
                subprocess.run(command)
                return 1
            if os.path.exists(output_png):
                return 1
            command = ['convert', prep_destination, output_png]
            subprocess.run(command)

        return result

    def make_histogram(self, file_id, file_name, testing=False):
        source = os.path.join(self.fileLocationManager.tif, file_name)
        HIS_FOLDER = self.fileLocationManager.histogram
        base = os.path.splitext(file_name)[0]
        output_png = os.path.join(HIS_FOLDER, base + '.png')
        if os.path.exists(output_png):
            return 1
        if testing:
            command = ['touch', output_png]
            subprocess.run(command)
            return 1

        rsection = self.session.query(RawSection).filter(RawSection.id == file_id).one()
        try:
            img = io.imread(source)
        except:
            return 0

        colors = {1: 'b', 2: 'r', 3: 'g'}
        fig = plt.figure()
        plt.rcParams['figure.figsize'] = [10, 6]
        if img.shape[0] * img.shape[1] > 1000000000:
            scale = 1 / float(2)
            img = img[::int(1. / scale), ::int(1. / scale)]
        try:
            flat = img.flatten()
        except:
            return 0
        del img
        fmax = flat.max()
        plt.hist(flat, fmax, [0, fmax], color=colors[rsection.channel])
        plt.style.use('ggplot')
        plt.yscale('log')
        plt.grid(axis='y', alpha=0.75)
        plt.xlabel('Value')
        plt.ylabel('Frequency')
        plt.title('{} @16bit'.format(file_name))
        fig.savefig(output_png, bbox_inches='tight')
        plt.close()
        del flat
        return 1


def everything_cv(img, rotation):
    scale = 1 / float(32)
    two_16 = 2 ** 16
    img = np.rot90(img, rotation)
    img = np.fliplr(img)
    try:
        img = img[::int(1. / scale), ::int(1. / scale)]
        #img[:, ::2, ::2]
    except:
        print('Cannot resize')
        return 0
    flat = img.flatten()
    hist, bins = np.histogram(flat, two_16)
    cdf = hist.cumsum()  # cumulative distribution function
    cdf = two_16 * cdf / cdf[-1]  # normalize
    # use linear interpolation of cdf to find new pixel values
    img_norm = np.interp(flat, bins[:-1], cdf)
    img_norm = np.reshape(img_norm, img.shape)
    #img_norm = two_16 - img_norm
    return img_norm.astype('uint16')

def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)


def make_tif(session, prep_id, tif_id, file_id, testing=False):
    slide_processor = SlideProcessor(prep_id, session)
    CZI_FOLDER = slide_processor.fileLocationManager.czi
    TIF_FOLDER = slide_processor.fileLocationManager.tif
    start = time.time()
    tif = session.query(AlcSlideCziTif).filter(AlcSlideCziTif.id==tif_id).one()
    slide = session.query(AlcSlide).filter(AlcSlide.id==tif.slide_id).one()
    czi_file = os.path.join(CZI_FOLDER, slide.file_name)
    rsection = session.query(RawSection).filter(RawSection.id==file_id).one()
    tif_file = os.path.join(TIF_FOLDER, rsection.destination_file)
    if not os.path.exists(czi_file) and not testing:
        return 0
    if os.path.exists(tif_file):
        return 1

    if testing:
        command = ['touch', tif_file]
    else:
        command = ['/usr/local/share/bftools/bfconvert', '-bigtiff', '-compression', 'LZW', '-separate',
                                  '-series', str(tif.scene_index), '-channel', str(tif.channel_index), '-nooverwrite', czi_file, tif_file]
    subprocess.run(command)

    end = time.time()
    if os.path.exists(tif_file):
        tif.file_size = os.path.getsize(tif_file)

    tif.processing_duration = end - start
    session.merge(tif)
    session.commit()

    return 1


def lognorm(img, limit):
    lxf = np.log(img + 0.005)
    lxf = np.where(lxf < 0, 0, lxf)
    xmin = min(lxf.flatten())
    xmax = max(lxf.flatten())
    return -lxf * limit / (xmax - xmin) + xmax * limit / (xmax - xmin)  # log of data and stretch 0 to 255


def linnorm(img, limit):
    flat = img.flatten()
    hist, bins = np.histogram(flat, limit + 1)
    cdf = hist.cumsum()  # cumulative distribution function
    cdf = limit * cdf / cdf[-1]  # normalize
    # use linear interpolation of cdf to find new pixel values
    img_norm = np.interp(flat, bins[:-1], cdf)
    img_norm = np.reshape(img_norm, img.shape)
    img_norm = limit - img_norm
    return img_norm

