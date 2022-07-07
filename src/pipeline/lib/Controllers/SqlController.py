"""
This is the base sql class. It is mostly used per animal, so the init function
needs an animal passed to the constructor
It also needs for the animal, histology and scan run tables to be
filled out for each animal to use
"""
import sys
from abakit.lib.Controllers.Controller import Controller
from abakit.lib.Controllers.ElasticsController import ElasticsController
from abakit.lib.Controllers.StructuresController import StructuresController
from abakit.lib.Controllers.StructureComController import StructureComController
from abakit.lib.Controllers.TransformationController import TransformationController
from abakit.lib.Controllers.AnimalController import AnimalController
from abakit.lib.Controllers.UrlController import UrlController
from abakit.lib.Controllers.ScanRunController import ScanRunController
from abakit.lib.Controllers.SectionsController import SectionsController
from abakit.lib.Controllers.SlideController import SlideController
from abakit.lib.Controllers.SlideCZIToTifController import SlideCZIToTifController
from abakit.lib.Controllers.TasksController import TasksController,file_processed, set_file_completed
from abakit.lib.Controllers.HistologyController import HistologyController
from abakit.model.scan_run import ScanRun
from abakit.model.histology import Histology
from collections import OrderedDict
from sqlalchemy.orm.exc import NoResultFound
from abakit.settings import host,schema
import numpy as np

class SqlController(ElasticsController,StructuresController,TransformationController,
    UrlController,AnimalController,ScanRunController,SectionsController,TasksController,
    SlideController,SlideCZIToTifController,HistologyController,StructureComController):
    """ This is the old sql_controller class.  This is a huge class and we are in the process of breaking it up into smaller
        components.  Each parent class of SqlController would correspond to one table in the database, and include all the 
        methods to interact with that table
    """

    def __init__(self, animal='DK39', host=host, schema=schema):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
        """
        Controller.__init__(self,host=host, schema=schema)
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

    def convert_coordinate_pixel_to_microns(self,coordinates):
        resolution = self.scan_run.resolution
        x,y,z = coordinates
        x*=resolution
        y*=resolution
        z*=20
        return x,y,z

    def get_resolution(self,animal):
        scan_run = self.get_scan_run(animal)
        histology = self.get_histology(animal)
        if histology.orientation == 'coronal':
            return np.array([scan_run.zresolution,scan_run.resolution,scan_run.resolution])
        elif histology.orientation == 'horizontal':
            return np.array([scan_run.resolution,scan_run.zresolution,scan_run.resolution])
        elif histology.orientation == 'sagittal':
            return np.array([scan_run.resolution,scan_run.resolution,scan_run.zresolution])


    

