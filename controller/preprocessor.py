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
import numpy as np
import re
import matplotlib
import matplotlib.figure
import os
import cv2
import pandas as pd
from tqdm import tqdm

from model.section import Section
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
        scan_id = max(self.scan_ids)
        self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).delete(synchronize_session=False)
        self.session.commit()

        try:
            czi_files = sorted(os.listdir(self.fileLocationManager.czi))
        except OSError as e:
            print(e)
            sys.exit()

        section_number = 1
        for i, czi_file in enumerate(tqdm(czi_files)):
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
                #print('series', series)
                slide.scenes = len(series)
                self.session.add(slide)
                self.session.flush()

                for j, series_index in enumerate(series):
                    scene_number = j + 1
                    channels = range(metadata_dict[series_index]['channels'])
                    #print('channels range and dict', channels,metadata_dict[series_index]['channels'])
                    channel_counter = 0
                    width = metadata_dict[series_index]['width']
                    height = metadata_dict[series_index]['height']
                    for channel in channels:

                        newtif = '{}_S{}_C{}.tif'.format(czi_file, scene_number, channel_counter)
                        newtif = newtif.replace('.czi', '').replace('__','_')
                        tif = AlcSlideCziTif()
                        tif.slide_id = slide.id
                        tif.scene_number = scene_number
                        tif.file_name = newtif
                        tif.file_size = 0
                        tif.active = 1
                        tif.width = width
                        tif.height = height
                        tif.scene_index = series_index
                        tif.channel_index = channel_counter
                        channel_counter += 1
                        tif.channel = channel_counter
                        tif.processing_duration = 0
                        tif.created = time.strftime('%Y-%m-%d %H:%M:%S')
                        self.session.add(tif)
                    section_number += 1
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
        rsection = self.session.query(Section).filter(Section.id == file_id).one()
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
        rsection = self.session.query(Section).filter(Section.id == file_id).one()
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

        rsection = self.session.query(Section).filter(Section.id == file_id).one()
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
    section = session.query(Section).filter(Section.id==file_id).one()
    tif_file = os.path.join(TIF_FOLDER, section.file_name)
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

def place_image(img, max_width, max_height):
    zmidr = max_height // 2
    zmidc = max_width // 2
    startr = zmidr - (img.shape[0] // 2)
    endr = startr + img.shape[0]
    startc = zmidc - (img.shape[1] // 2)
    endc = startc + img.shape[1]
    new_img = np.zeros([max_height, max_width])
    try:
        new_img[startr:endr, startc:endc] = img
    except:
        print('could not create new img')

    return new_img.astype('uint16')


def find_main_blob(stats, image):
    height, width = image.shape
    df = pd.DataFrame(stats)
    df.columns = ['Left', 'Top', 'Width', 'Height', 'Area']
    df['blob_label'] = df.index
    df = df.sort_values(by='Area', ascending=False)

    for row in df.iterrows():
        Left = row[1]['Left']
        Top = row[1]['Top']
        Width = row[1]['Width']
        Height = row[1]['Height']
        corners = int(Left == 0) + int(Top == 0) + int(Width == width) + int(Height == height)
        if corners <= 2:
            return row


def scale_and_mask(src, mask, epsilon=0.01):
    vals = np.array(sorted(src[mask > 10]))
    ind = int(len(vals) * (1 - epsilon))
    _max = vals[ind]
    # print('thr=%d, index=%d'%(vals[ind],index))
    _range = 2 ** 16 - 1
    scaled = src * (45000. / _max)
    scaled[scaled > _range] = _range
    scaled = scaled * (mask > 10)
    return scaled, _max


def find_threshold(src):
    fig = matplotlib.figure.Figure()
    ax = matplotlib.axes.Axes(fig, (0, 0, 0, 0))
    n, bins, patches = ax.hist(src.flatten(), 360);
    del ax, fig
    min_point = np.argmin(n[:5])
    min_point = int(max(2, min_point))
    thresh = (min_point * 64000 / 360)
    return min_point, thresh


def make_mask(session, prep_id, file_id, max_width, max_height):
    slide_processor = SlideProcessor(prep_id, session)

    DIR = '/data2/edward/DK39'
    ##### TESTING #####
    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps'
    #####INPUT = slide_processor.fileLocationManager.tif
    INPUT = '/data2/edward/DK39/CH1'
    CLEANED = os.path.join(DIR, 'cleaned')
    MASKED = os.path.join(DIR, 'masked')

    OUTPUT = CLEANED
    rsection = session.query(Section).filter(Section.id==file_id).one()
    #infile = rsection.destination_file
    infile = '{}.tif'.format(str(rsection.section_number).zfill(3))
    inpath = os.path.join(INPUT, infile)
    outfile = '{}.tif'.format(str(rsection.section_number).zfill(3))
    outpath = os.path.join(OUTPUT, outfile)
    maskpath = os.path.join(MASKED, outfile)

    if os.path.exists(outpath) and os.path.exists(maskpath):
        return 1

    try:
        img = io.imread(inpath)
    except:
        print('Could not open', inpath)
        return 0
    img = get_last_2d(img)
    min_value, threshold = find_threshold(img)
    ###### Threshold it so it becomes binary
    # threshold = 272
    ret, threshed = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    threshed = np.uint8(threshed)
    ###### Find connected elements
    # You need to choose 4 or 8 for connectivity type
    connectivity = 4
    output = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_32S)
    # Get the results
    # The first cell is the number of labels
    num_labels = output[0]
    # The second cell is the label matrix
    labels = output[1]
    # The third cell is the stat matrix
    stats = output[2]
    # The fourth cell is the centroid matrix
    centroids = output[3]
    # Find the blob that corresponds to the section.
    row = find_main_blob(stats, img)
    blob_label = row[1]['blob_label']
    # extract the blob
    blob = np.uint8(labels == blob_label) * 255
    # Perform morphological closing
    kernel10 = np.ones((10, 10), np.uint8)
    closing = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)
    del blob
    # scale and mask
    scaled, _max = scale_and_mask(img, closing)
    #####closing = place_image(closing, max_width, max_height)
    cv2.imwrite(maskpath, closing.astype('uint8'))
    del closing
    ##### TESTING #####
    return 1

    try:
        img = place_image(scaled, max_width, max_height)
    except:
        print('Could not place image', infile, img.shape)
        return 0

    del scaled


    tilesize = 16
    clahe = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(tilesize, tilesize))
    img = clahe.apply(img)

    outpath = os.path.join(OUTPUT, outpath)
    cv2.imwrite(outpath, img.astype('uint16'))


    return 1


def clean_with_mask(session, prep_id, file_id, max_width, max_height):
    slide_processor = SlideProcessor(prep_id, session)

    DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps'
    #####INPUT = slide_processor.fileLocationManager.tif
    MASKED = os.path.join(DIR, 'masked')
    return 1
