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
import os, sys, time
from datetime import datetime
from skimage import io
import re
from tqdm import tqdm
from pathlib import Path

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities.utilities_bioformats import get_czi_metadata, get_fullres_series_indices
from utilities.model.animal import Animal
from utilities.model.histology import Histology as AlcHistology
from utilities.model.scan_run import ScanRun as AlcScanRun
from utilities.model.slide import Slide as AlcSlide
from utilities.model.slide_czi_to_tif import SlideCziTif as AlcSlideCziTif
from sql_setup import database
from utilities.file_location import FileLocationManager
#schema = dj.schema(database)


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
                        tif = AlcSlideCziTif()
                        tif.slide_id = slide.id
                        tif.scene_number = scene_number
                        tif.file_size = 0
                        tif.active = 1
                        tif.width = width
                        tif.height = height
                        tif.scene_index = series_index
                        channel_counter += 1
                        newtif = '{}_S{}_C{}.tif'.format(czi_file, scene_number, channel_counter)
                        newtif = newtif.replace('.czi', '').replace('__','_')
                        tif.file_name = newtif
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
