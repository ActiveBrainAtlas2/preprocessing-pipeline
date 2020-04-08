from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
import os
from _collections import OrderedDict
from model.animal import Animal
from model.histology import Histology
from model.scan_run import ScanRun
from model.section import RawSection
from model.slide import Slide
from model.slide_czi_to_tif import SlideCziTif
from model.task import Task, ProgressLookup
from sql_setup import dj, database, session
from utilities.metadata import ROOT_DIR

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
        self.valid_sections = OrderedDict()
        # fill up the metadata_cache variable

    def generate_stack_metadata(self):
        """
        There must be an entry in both the animal and histology and task tables
        The task table is necessary as that is filled when the CZI dir is scanned.
        If there are no czi and tif files, there is no point in running the pipeline on that stack
        Returns:
            a dictionary of stack information

        """
        for a, h in session.query(Animal, Histology).filter(Animal.prep_id == Histology.prep_id).all():
            resolution = session.query(func.max(ScanRun.resolution)).filter(ScanRun.prep_id == a.prep_id).scalar()

            tif_dir = os.path.join(ROOT_DIR, a.prep_id, 'tif')
            if (os.path.exists(tif_dir) and len(os.listdir(tif_dir)) > 0):
                self.all_stacks.append(a.prep_id)
                self.stack_metadata[a.prep_id] = {'stain': h.counterstain,
                                                  'cutting_plane': h.orientation,
                                                  'resolution': resolution,
                                                  'section_thickness': h.section_thickness}
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
         For both operations, you need to set the next/previous section to a dummy number,
         as there is a unique constraint on prep_id, section_number, channel.
        
         If we are moving a section to the left, set the preceding section number to the current section
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
            raw_section = self.session.query(RawSection).filter(RawSection.id == key).one()
            raw_section.file_status = value['quality']
            session.merge(raw_section)
        session.commit()

    #################### Get and set progress ############

    def get_current_step_from_progress_ini(self, stack):
        step = "1-2_setup_images"
        try:
            lookup_id = self.session.query(func.max(Task.lookup_id)).filter(Task.prep_id == stack) \
                .filter(Task.completed.is_(True)).scalar()
        except NoResultFound as nrf:
            print('No results for {} error: {}'.format(stack, nrf))
            return step

        try:
            lookup = self.session.query(ProgressLookup).filter(ProgressLookup.id == lookup_id).one()
        except NoResultFound as nrf:
            print('Bad lookup code for {} error: {}'.format(lookup_id, nrf))
            return step

        return lookup.original_step

    def set_step_completed_in_progress_ini(self, stack, step):
        """
        Look up the lookup up from the step. Check if the stack already exists,
        if not, insert, otherwise, update
        Args:
            stack: string of the stack you are working on
            step: current step

        Returns:
            nothing, just merges
        """
        try:
            lookup = self.session.query(ProgressLookup)\
                .filter(ProgressLookup.original_step == step)\
                .order_by(ProgressLookup.original_step.desc())\
                .limit(1).one()
        except NoResultFound:
            print('No lookup for {}'.format(step))
        try:
            task = self.session.query(Task).filter(Task.lookup_id == lookup.id)\
                .filter(Task.prep_id == stack).one()
        except NoResultFound:
            print('No step for {}'.format(step))
            task = Task(stack, lookup.id, True)

        try:
            self.session.merge(task)
            self.session.commit()
        except:
            print('Bad lookup code for {}'.format(lookup.id))
            self.session.rollback()
        #progress_dict = DataManager.get_brain_info_progress(stack)
        #progress_dict[step] = True
        #progress_ini_to_save = {}
        #progress_ini_to_save['DEFAULT'] = progress_dict
        #fp = os.path.join(ROOT_DIR, stack, 'brains_info', 'progress.ini')
        #save_dict_as_ini(progress_ini_to_save, fp)

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
