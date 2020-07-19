"""
This is the base sql class. It is mostly used per animal, so the init function
needs an animal passed to the constructor
It also needs for the animal, histology and scan run tables to be
filled out for each animal to use
"""
import logging
import traceback
import transaction
###from logger import Log


from collections import OrderedDict

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from model.animal import Animal
from model.histology import Histology
from model.scan_run import ScanRun
from model.section import Section
from model.slide import Slide
from model.slide_czi_to_tif import SlideCziTif
from model.task import Task, ProgressLookup
from sql_setup import session


class SqlController(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, animal):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
                session: sql session to run queries
        """
        self.session = session
        self.stack_metadata = {}
        self.all_stacks = []
        self.animal = session.query(Animal).filter(Animal.prep_id == animal).one()
        self.histology = session.query(Histology).filter(Histology.prep_id == animal).one()
        self.scan_run = session.query(ScanRun).filter(ScanRun.prep_id == animal).order_by(ScanRun.id.desc()).one()
        self.slides = None
        self.tifs = None
        self.valid_sections = OrderedDict()
        # fill up the metadata_cache variable

    def get_sections(self, animal, channel):
        """
        The sections table is a view and it is already filtered by active and file_status = 'good'
        The ordering is important. This needs to come from the histology table.
        Args:
            animal: the animal to query
            channel: 1 or 2 or 3.

        Returns: list of sections in order

        """
        orderby = self.histology.side_sectioned_first

        if orderby == 'DESC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.desc())\
                .order_by(Section.scene_number.desc()).all()
        else:
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.asc())\
                .order_by(Section.scene_number.asc()).all()

        return sections

    def get_distinct_section_filenames(self, animal, channel):
        """
        Very similar to the get_sections query but this will return a list of
        distinct file names. Since some of the scenes get duplicated in the QA process,
        we need to get the without duplicates. The duplicates will then get replicated
        with the get_sections method. The order doesn't matter.
        Args:
            animal: the animal to query
            channel: 1 or 2 or 3.

        Returns: list of sections in order with distinct file namnes

        """
        sections = self.session.query(Section.czi_file, Section.file_name, Section.scene_index, Section.channel_index).distinct()\
            .filter(Section.prep_id == animal).filter(
            Section.channel == channel) \

        return sections

    def get_slide_czi_to_tifs(self, channel):
        slides = self.session.query(Slide).filter(Slide.scan_run_id == self.scan_run.id)\
            .filter(Slide.slide_status == 'Good').all()
        slide_czi_to_tifs = self.session.query(SlideCziTif).filter(SlideCziTif.channel == channel)\
            .filter(SlideCziTif.slide_id.in_([slide.id for slide in slides]))\
            .filter(SlideCziTif.active == 1).all()

        return slide_czi_to_tifs

    def update_row(self, row):
        self.session.merge(row)
        self.session.commit()

    def get_sections_numbers(self, animal):
        sections = self.session.query(Section).filter(Section.prep_id == animal).filter(Section.channel == 1).all()

        section_numbers = []
        for i, r in enumerate(sections):
            section_numbers.append(i)

        return section_numbers

    def get_current_task(self, animal):
        step = None
        try:
            lookup_id = self.session.query(func.max(Task.lookup_id)).filter(Task.prep_id == animal) \
                .filter(Task.completed.is_(True)).scalar()
        except NoResultFound as nrf:
            print('No results for {} error: {}'.format(animal, nrf))
            return step

        try:
            lookup = self.session.query(ProgressLookup).filter(ProgressLookup.id == lookup_id).one()
        except NoResultFound as nrf:
            print('Bad lookup code for {} error: {}'.format(lookup_id, nrf))
            return step

        return lookup.description

    def set_task(self, animal, lookup_id):
        """
        Look up the lookup up from the step. Check if the animal already exists,
        if not, insert, otherwise, update
        Args:
            animal: string of the animal you are working on
            lookup_id: current lookup ID
        Returns:
            nothing, just merges
        """
        try:
            lookup = self.session.query(ProgressLookup) \
                .filter(ProgressLookup.id == lookup_id) \
                .limit(1).one()
        except NoResultFound:
            print('No lookup for {} so we will enter one.'.format(lookup_id))
        try:
            task = self.session.query(Task).filter(Task.lookup_id == lookup.id) \
                .filter(Task.prep_id == animal).one()
        except NoResultFound:
            print('No step for {}, so creating new task.'.format(lookup_id))
            task = Task(animal, lookup.id, True)

        try:
            self.session.merge(task)
            self.session.commit()
        except:
            print('Bad lookup code for {}'.format(lookup.id))
            self.session.rollback()

"""
    class SQLAlchemyHandler(logging.Handler):
        # A very basic logger that commits a LogRecord to the SQL Db
        def emit(self, record):
            trace = None
            exc = record.__dict__['exc_info']
            if exc:
                trace = traceback.format_exc()
            log = Log(
                logger=record.__dict__['name'],
                level=record.__dict__['levelname'],
                trace=trace,
                msg=record.__dict__['msg'],)
            self.session.add(log)
            transaction.commit()
"""
