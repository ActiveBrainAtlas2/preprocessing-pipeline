"""
This is the base sql class. It is mostly used per animal, so the init function
needs an animal passed to the constructor
It also needs for the animal, histology and scan run tables to be
filled out for each animal to use
"""
import sys
from lib.Controllers.ElasticsController import ElasticsController
from lib.Controllers.LayerDataController import LayerDataController
from lib.Controllers.StructuresController import StructuresController
from lib.Controllers.TransformationController import TransformationController

from abakit.lib.sql_setup import  pooledsession
from abakit.model.file_log import FileLog
from abakit.model.task import Task, ProgressLookup
from abakit.model.slide_czi_to_tif import SlideCziTif
from abakit.model.slide import Slide
from abakit.model.section import Section
from abakit.model.scan_run import ScanRun
from abakit.model.histology import Histology
from abakit.model.animal import Animal
from collections import OrderedDict
from datetime import datetime
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound


class SqlController(ElasticsController,LayerDataController,StructuresController,TransformationController):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, animal):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
        """
        ElasticsController.__init__(self)
        if self.animal_exists(animal):
            self.animal = self.session.query(Animal).filter(
                Animal.prep_id == animal).one()
        else:
            print(f'No animal/brain with the name {animal} was found in the database.')
            sys.exit()
        try:
            self.histology = self.session.query(Histology).filter(
                Histology.prep_id == animal).one()
        except NoResultFound:
            print(f'No histology for {animal}')
        try:
            self.scan_run = self.session.query(ScanRun).filter(
                ScanRun.prep_id == animal).order_by(ScanRun.id.desc()).one()
        except NoResultFound:
            print(f'No scan run for {animal}')
        self.slides = None
        self.tifs = None
        self.valid_sections = OrderedDict()
    
    def scan_run_exists(self,animal):
        return bool(self.session.query(ScanRun).filter(ScanRun.prep_id == animal).order_by(ScanRun.id.desc()).first())

    def animal_exists(self,animal):
        return bool(self.session.query(Animal).filter(Animal.prep_id == animal).first())
    
    def get_scan_run(self,animal):
        return self.session.query(ScanRun).filter(
                ScanRun.prep_id == animal).order_by(ScanRun.id.desc()).one()

    def get_animal_list(self):
        results = self.session.query(Animal).all()
        animals = []
        for resulti in results:
            animals.append(resulti.prep_id)
        return animals

    def get_section(self, ID):
        """
        The sections table is a view and it is already filtered by active and file_status = 'good'
        This qeury returns a single section by id.
        Args:
            id: integer primary key

        Returns: one section
        """
        return self.session.query(Section).filter(Section.id == ID).one()

    def get_slide(self, ID):
        """
        Args:
            id: integer primary key

        Returns: one slide
        """
        return self.session.query(Slide).filter(Slide.id == ID).one()

    def get_tif(self, ID):
        """
        Args:
            id: integer primary key

        Returns: one tif
        """
        return self.session.query(SlideCziTif).filter(SlideCziTif.id == ID).one()

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
        we need to get the tifs without duplicates. The duplicates will then get replicated
        with the get_sections method. The order doesn't matter here.
        Args:
            animal: the animal to query
            channel: 1 or 2 or 3.

        Returns: list of sections with distinct file names

        """
        sections = self.session.query(Section.czi_file, Section.file_name, Section.scene_index,  Section.channel_index).distinct()\
            .filter(Section.prep_id == animal).filter(
            Section.channel == channel).all()

        return sections

    def get_slide_czi_to_tifs(self, channel):
        slides = self.session.query(Slide).filter(Slide.scan_run_id == self.scan_run.id)\
            .filter(Slide.slide_status == 'Good').all()
        slide_czi_to_tifs = self.session.query(SlideCziTif).filter(SlideCziTif.channel == channel)\
            .filter(SlideCziTif.slide_id.in_([slide.id for slide in slides]))\
            .filter(SlideCziTif.active == 1).all()

        return slide_czi_to_tifs

    def update_scanrun(self, id):
        width = self.session.query(func.max(SlideCziTif.width)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        height = self.session.query(func.max(SlideCziTif.height)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        SAFEMAX = 10000
        LITTLE_BIT_MORE = 500
        # just to be safe, we don't want to update numbers that aren't realistic
        if height > SAFEMAX and width > SAFEMAX:
            height = round(height, -3)
            width = round(width, -3)
            height += LITTLE_BIT_MORE
            width += LITTLE_BIT_MORE
            # width and height get flipped
            try:
                self.session.query(ScanRun).filter(ScanRun.id == id).update(
                    {'width': height, 'height': width})
                self.session.commit()
            except Exception as e:
                print(f'No merge for  {e}')
                self.session.rollback()

    def update_tif(self, id, width, height):
        try:
            self.session.query(SlideCziTif).filter(
                SlideCziTif.id == id).update({'width': width, 'height': height})
            self.session.commit()
        except Exception as e:
            print(f'No merge for  {e}')
            self.session.rollback()

    def get_sections_numbers(self, animal):
        sections = self.session.query(Section).filter(
            Section.prep_id == animal).filter(Section.channel == 1).all()

        section_numbers = []
        for i, r in enumerate(sections):
            section_numbers.append(i)

        return section_numbers

    def get_sections_dict(self, animal):
        sections = self.session.query(Section).filter(
            Section.prep_id == animal).filter(Section.channel == 1).all()

        sections_dict = {}
        for i, r in enumerate(sections):
            sections_dict[i] = str(i).zfill(3) + 'tif'

        return sections_dict

    def get_coordinates_from_query_result(self,query_result):
        coord = []
        resolution = self.scan_run.resolution
        for resulti in query_result:
            coord.append([resulti.x/resolution,resulti.y/resolution,int(resulti.section/20)])
        return(np.array(coord))

    def get_section_count(self, animal):
        try:
            count = self.session.query(Section).filter(
                Section.prep_id == animal).filter(Section.channel == 1).count()
        except:
            count = 666
        return count

    def get_current_task(self, animal):
        step = None
        try:
            lookup_id = self.session.query(func.max(Task.lookup_id)).filter(Task.prep_id == animal) \
                .filter(Task.completed.is_(True)).scalar()
        except NoResultFound as nrf:
            print('No results for {} error: {}'.format(animal, nrf))
            return step

        try:
            lookup = self.session.query(ProgressLookup).filter(
                ProgressLookup.id == lookup_id).one()
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
    
    def structure_abbreviation_to_id(self,abbreviation):
        try:
            structure = self.get_structure(str(abbreviation).strip())
        except NoResultFound as nrf:
            print(f'No structure found for {abbreviation} {nrf}')
            return
        return structure.id

    def get_progress_id(self, downsample, channel, action):

        try:
            lookup = self.session.query(ProgressLookup) \
                .filter(ProgressLookup.downsample == downsample) \
                .filter(ProgressLookup.channel == channel) \
                .filter(ProgressLookup.action == action).one()
        except NoResultFound as nrf:
            print(
                f'Bad lookup code for {downsample} {channel} {action} error: {nrf}')
            return 0

        return lookup.id

    def convert_coordinate_pixel_to_microns(self,coordinates):
        resolution = self.scan_run.resolution
        self.session.close()
        x,y,z = coordinates
        x*=resolution
        y*=resolution
        z*=20
        return x,y,z

def file_processed(animal, progress_id, filename):
    """
    Args:
        animal: prep_id
        progress_id: ID from progress_lookup table
        filename: filename you are working on
    Returns:
        boolean if file exists or not
    """
    try:
        file_log = pooledsession.query(FileLog) \
            .filter(FileLog.prep_id == animal) \
            .filter(FileLog.progress_id == progress_id) \
            .filter(FileLog.filename == filename).one()
    except NoResultFound as nrf:
        return False
    finally:
        pooledsession.close()

    return True

def set_file_completed(animal, progress_id, filename):
    """
    Args:
        animal: prep_id
        progress_id: ID from progress_lookup table
        filename: filename you are working on
    Returns:
        nothing, just merges
    """

    file_log = FileLog(prep_id=animal, progress_id=progress_id, filename=filename,
                       created=datetime.utcnow(), active=True)

    try:
        pooledsession.add(file_log)
        pooledsession.commit()
    except Exception as e:
        print(f'No merge for {animal} {filename} {e}')
        pooledsession.rollback()
    finally:
        pooledsession.close()


    

