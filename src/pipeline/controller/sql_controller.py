"""
This is the base sql class. It is mostly used per animal, so the init function
needs an animal passed to the constructor
It also needs for the animal, histology and scan run tables to be
filled out for each animal to use
"""

import sys
import numpy as np
from collections import OrderedDict
from sqlalchemy.orm.exc import NoResultFound

from controller.main_controller import Controller
from controller.animal_controller import AnimalController
from controller.elastix_controller import ElastixController
from controller.histology_controller import HistologyController
from controller.scan_run_controller import ScanRunController
from controller.sections_controller import SectionsController
from controller.slide_controller import SlideController
from controller.slide_tif_controller import SlideCZIToTifController
from controller.tasks_controller import TasksController
from database_model.scan_run import ScanRun
from database_model.histology import Histology

try:
    from settings import host, password, user, schema
except ImportError as fe:
    print('You must have a settings file in the pipeline directory.', fe)
    raise


class SqlController(AnimalController, ElastixController, HistologyController,
                     ScanRunController, SectionsController,
                    SlideController, SlideCZIToTifController, TasksController):
    """ This is the base class for all things SQL.  
    Each parent class of SqlController would correspond to one table in the database, and include all the 
    methods to interact with that table
    """

    def __init__(self, animal):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
        """
        Controller.__init__(self, host=host, password=password, schema=schema, user=user)
        if self.animal_exists(animal):
            self.animal = self.get_animal(animal)
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

    def get_resolution(self, animal):
        """Returns the resolution for an animal
        
        :param animal: string primary key
        :return numpy array: of the resolutions
        """
        
        scan_run = self.get_scan_run(animal)
        histology = self.get_histology(animal)
        if histology.orientation == 'coronal':
            return np.array([scan_run.zresolution, scan_run.resolution, scan_run.resolution])
        elif histology.orientation == 'horizontal':
            return np.array([scan_run.resolution, scan_run.zresolution, scan_run.resolution])
        elif histology.orientation == 'sagittal':
            return np.array([scan_run.resolution, scan_run.resolution, scan_run.zresolution])
