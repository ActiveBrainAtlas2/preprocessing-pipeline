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
from itertools import zip_longest
import os, sys, subprocess, time
from datetime import datetime
from matplotlib import pyplot as plt
from skimage import io
from skimage.util import img_as_uint
import numpy as np
import re
from .bioformats_utilities import get_czi_metadata, get_fullres_series_indices
from model.animal import Animal
from model.histology import Histology as AlcHistology
from model.scan_run import ScanRun as AlcScanRun
from model.slide import Slide as AlcSlide
from model.section import RawSection as AlcRawSection
from model.slide_czi_to_tif import SlideCziTif as AlcSlideCziTif
from model.task import Task
from sql_setup import dj, database
from utilities.file_location import FileLocationManager

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
        no_czi = len(czi_files)
        no_scenes = 4
        total_sections = no_czi * no_scenes
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
                self.session.add(slide)
                self.session.flush()

                # Get metadata from the czi file
                czi_file_path = os.path.join(self.fileLocationManager.czi, czi_file)
                metadata_dict = get_czi_metadata(czi_file_path)
                #print(metadata_dict)
                series = get_fullres_series_indices(metadata_dict)
                for j, series_index in enumerate(series):
                    channels = range(metadata_dict[series_index]['channels'])
                    channel_counter = 0
                    width = metadata_dict[series_index]['width']
                    height = metadata_dict[series_index]['height']
                    for channel in channels:
                        channel_counter += 1
                        newtif = '{}_S{}_C{}.tif'.format(czi_file, series_index, channel_counter)
                        newtif = newtif.replace('.czi','')
                        tif = AlcSlideCziTif()
                        tif.slide_id = slide.id
                        tif.section_number = section_number
                        tif.scene_number = j
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
                        print('{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(newtif, tif.section_number, tif.slide_id, tif.scene_index, tif.channel, width, height))
                        self.session.add(tif)
                    section_number += 1
        # lookup_id=3 is for the scanning CZI
        task =   self.session.query(Task).filter(Task.lookup_id == 3)\
        .filter(Task.prep_id == self.animal.prep_id).one()
        task.end_date = datetime.now()
        self.session.merge(task)

        self.session.commit()




    def create_sections(self):
        """
        """
        prep_id = self.animal.prep_id
        self.session.query(AlcRawSection).filter(AlcRawSection.prep_id == prep_id).delete(synchronize_session=False)
        slides = self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).all()
        slide_ids = [slide.id for slide in slides]
        no_slides = len(slide_ids)
        no_scenes = 4
        total_sections = no_slides * no_scenes
        section_list = [i for i in range(1,total_sections + 1)]
        tifs = self.session.query(AlcSlideCziTif).filter(AlcSlideCziTif.slide_id.in_(slide_ids)).filter(AlcSlideCziTif.channel_index==0).all()
        for tif, section_number in zip_longest(tifs, section_list):
            if tif is not None:
                name = '{}_{}'.format(tif.file_name, section_number)
            else:
                name = '{}_{}'.format(prep_id, section_number)
            print(name, section_number)
            section = AlcRawSection()
            section.source_file = '{}'.format(name)
            section.prep_id = prep_id
            section.section_number = int(section_number)
            section.active = True
            section.created = datetime.now()
            self.session.add(section)
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

    def make_thumbnail(self, file_name):
        """
        This will create a png in the web thumbnail dir, and another one
        in the preps dir that are used throughout the pipeline
        """
        result = 0

        source = os.path.join(self.fileLocationManager.tif, file_name)
        web_destination = os.path.join(self.fileLocationManager.thumbnail_web, file_name)
        prep_destination = os.path.join(self.fileLocationManager.thumbnail_prep, file_name)
        if os.path.exists(source):
            # Create thumbnails
            command = ['convert', source, '-resize 3.125%', '-auto-level',
                       '-normalize', ',-compress lzw', prep_destination]
            #print('prep:', " ".join(command))
            #subprocess.run(command)
            base = os.path.splitext(file_name)[0]
            output_png = os.path.join(web_destination, base + '.png')
            command = ['convert', prep_destination, output_png]
            #print('web:', " ".join(command))
            #subprocess.run(command)
            result = 1
        else:
            print('File {} does not exist'.format(source))

        return result



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

def make_histogram(session, prep_id, file_id):
    tif = session.query(AlcSlideCziTif).filter(AlcSlideCziTif.id==file_id).one()
    HIS_FOLDER = os.path.join(DATA_ROOT, prep_id, HIS)
    TIF_FOLDER = os.path.join(DATA_ROOT, prep_id, TIF)
    input_tif = os.path.join(TIF_FOLDER, tif.file_name)
    base = os.path.splitext(tif.file_name)[0]
    output_png = os.path.join(HIS_FOLDER, base + '.png')
    try:
        img = io.imread(input_tif)
    except:
        return 0

    colors = {1:'b', 2:'r', 3:'g'}
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
    plt.hist(flat, fmax, [0, fmax], color=colors[tif.channel])
    plt.style.use('ggplot')
    plt.yscale('log')
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('{} @16bit'.format(tif.file_name))
    fig.savefig(output_png, bbox_inches='tight')
    plt.close()
    del flat
    return 1


def make_tif(session, prep_id, file_id):
    CZI_FOLDER = os.path.join(DATA_ROOT, prep_id, CZI)
    TIF_FOLDER = os.path.join(DATA_ROOT, prep_id, TIF)
    start = time.time()
    tif = session.query(AlcSlideCziTif).filter(AlcSlideCziTif.id==file_id).one()
    slide = session.query(AlcSlide).filter(AlcSlide.id==tif.slide_id).one()
    czi_file = os.path.join(CZI_FOLDER, slide.file_name)

    tif_file = os.path.join(TIF_FOLDER, tif.file_name)
    command = ['/usr/local/share/bftools/bfconvert', '-bigtiff', '-compression', 'LZW', '-separate',
                              '-series', str(tif.scene_index), '-channel', str(tif.channel_index), '-nooverwrite', czi_file, tif_file]
    #cli = " ".join(command)
    #command = ['touch', tif_file]
    subprocess.run(command)
    #print(cli)

    end = time.time()
    if os.path.exists(tif_file):
        tif.file_size = os.path.getsize(tif_file)

    tif.processing_duration = end - start
    session.merge(tif)
    session.commit()

    #session.commit()
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

