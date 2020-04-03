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
            self.valid_sections[r.id] = {'section_number': r.section_number,
                                                     'channel': r.channel,
                                                     'source': r.source_file,
                                                     'destination': r.destination_file,
                                                     'quality': r.file_status}

        #print(self.valid_sections)
        return self.valid_sections

    def move_section(self, stack, section_number, change):
        min_id = session.query(func.min(RawSection.section_number)).filter(RawSection.prep_id == stack)\
            .filter(RawSection.active == 1).scalar()
        max_id = session.query(func.max(RawSection.section_number)).filter(RawSection.prep_id == stack)\
            .filter(RawSection.active == 1).scalar()
        set_to = section_number
        """
         for both operations, you need to set the next/previous section to a dummy number,
         There is a unique constraint on prep_id, section_number, channel
        
         if we are moving a section to the left, set the preceding section number to the current section
         and the current section to the preceding. Two updates.
         Likewise, if we are moving it to right, set the next section number to the current section
         and the current section the to next. Two updates. 
         Only do either of these updates if there is an allowable active section number to move
         them to.
        """
        DUMMY_SECTION_NUMBER = 9999
        if change == -1:
            if section_number > min_id:
                set_to += change
                preceding_section = section_number - 1
                self.change_section_number(stack, preceding_section, DUMMY_SECTION_NUMBER)
                self.change_section_number(stack, section_number, set_to)
                self.change_section_number(stack, DUMMY_SECTION_NUMBER, section_number)
        else:
            if section_number < max_id:
                set_to += change
                next_section = section_number + 1
                self.change_section_number(stack, next_section, DUMMY_SECTION_NUMBER)
                self.change_section_number(stack, section_number, set_to)
                self.change_section_number(stack, DUMMY_SECTION_NUMBER, section_number)


    def change_section_number(self, stack, section_number, set_to):
        try:
            raw_sections = self.session.query(RawSection)\
                .filter(RawSection.prep_id == stack)\
                .filter(RawSection.section_number == section_number).all()
        except NoResultFound as nrf:
            print('No section for id {} error: {}'.format(id, nrf))
            return
        for section in raw_sections:
            section.section_number = set_to
            self.session.merge(section)

        self.session.commit()


    def inactivate_section(self, prep_id, section_number):
        try:
            raw_sections = self.session.query(RawSection)\
                .filter(RawSection.prep_id == prep_id)\
                .filter(RawSection.section_number == section_number).all()
        except NoResultFound as nrf:
            print('No section for id {} error: {}'.format(id, nrf))
            return
        for section in raw_sections:
            section.active = 0
            self.session.merge(section)
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
