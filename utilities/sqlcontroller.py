from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
import os
from model.animal import Animal
from model.histology import Histology
from model.scan_run import ScanRun
from model.section import RawSection
from model.slide import Slide
from model.slide_czi_to_tif import SlideCziTif
from sql_setup import dj, database, session


DATA_ROOT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
TIF = 'tif'
HIS = 'histogram'
ROTATED = 'rotated'
PREPS = 'preps'
THUMBNAIL = 'thumbnail'
schema = dj.schema(database)


class SqlController(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
                session: sql session to run queries
        """
        self.session = session
        self.stack_metadata = {}
        self.all_stacks = []
        self.animal = None
        self.histology = None
        self.scan_run = None
        self.slides = None
        self.tifs = None
        self.valid_sections = {}
        # fill up the metadata_cache variable

    def generate_stack_metadata(self):
        # fill up the metadata_cache variable
        for a, h in session.query(Animal, Histology).filter(Animal.prep_id == Histology.prep_id).all():
            self.stack_metadata[a.prep_id] = {'stain': h.counterstain,
                                              'cutting_plane': h.orientation,
                                              'resolution': 0,
                                              'section_thickness': h.section_thickness}
            self.all_stacks.append(a.prep_id)
        return self.stack_metadata

    def get_animal_info(self, stack):
        self.animal = self.session.query(Animal).filter(Animal.prep_id == stack).one()
        self.histology = self.session.query(Histology).filter(Histology.prep_id == stack).one()
        #scan_run = self.session.query(ScanRun, func.max(ScanRun.id).label('resolution')).filter(ScanRun.prep_id == stack).group_by(ScanRun.prep_id).one()
        self.scan_run = self.session.query(ScanRun).filter(ScanRun.prep_id == stack).order_by(ScanRun.id.desc()).one()

    def get_valid_sections(self, stack):
        self.raw_sections = self.session.query(RawSection).filter(RawSection.prep_id == stack)\
            .filter(RawSection.active == 1)\
            .order_by(RawSection.section_number).order_by(RawSection.source_file).all()

        for r in self.raw_sections:
            self.valid_sections[r.section_number] = {'source': r.source_file,
                                                     'destination': r.destination_file,
                                                     'quality': r.file_status}

        #print(self.valid_sections)
        return self.valid_sections

    def inactivate_section(self, section_number):
        try:
            raw_section = self.session.query(RawSection).filter(RawSection.section_number == section_number).one()
        except NoResultFound as nrf:
            print('No section for id {} error: {}'.format(id, nrf))
            return
        raw_section.active = 0
        print('raw section id ', raw_section.id)
        self.session.merge(raw_section)
        self.session.commit()

    def save_valid_sections(self, valid_sections):
        for key, value in valid_sections.items():
            print(key, value)

    #################### Resolution conversions ############

    def convert_resolution_string_to_um(self, resolution, stack):
        return self.convert_resolution_string_to_voxel_size(resolution, stack=stack)

    def convert_resolution_string_to_voxel_size(self, resolution, stack):
        """
        Args:
            resolution (str):
        Returns:
            voxel/pixel size in microns.
        """

        assert stack is not None, 'Stack argument cannot be None.'
        scan_run = self.session.query(ScanRun, func.max(ScanRun.resolution).label('resolution')).filter(ScanRun.prep_id == stack).group_by(ScanRun.prep_id).one()
        planar_resolution = scan_run.resolution
        print('planar resolution from query', planar_resolution)

        if resolution in ['down32', 'thumbnail']:
            assert stack is not None
            return planar_resolution * 32.
        elif resolution == 'lossless' or resolution == 'down1' or resolution == 'raw':
            return planar_resolution
        elif resolution.startswith('down'):
            return planar_resolution * int(resolution[4:])
        elif resolution == 'um':
            return 1.
        elif resolution.endswith('um'):
            return float(resolution[:-2])
        else:
            print(resolution)
            raise Exception("Unknown resolution string %s" % resolution)
