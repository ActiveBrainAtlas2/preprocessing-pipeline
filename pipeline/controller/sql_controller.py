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
from controller.elastix_controller import ElastixController
from controller.structure_controller import StructuresController
from controller.structure_com_controller import StructureComController
from controller.marked_cell_controller import MarkedCellController
from controller.transformation_controller import TransformationController
from controller.animal_controller import AnimalController
from controller.url_controller import UrlController
from controller.scan_run_controller import ScanRunController
from controller.sections_controller import SectionsController
from controller.slide_controller import SlideController
from controller.slide_tif_controller import SlideCZIToTifController
from controller.tasks_controller import TasksController
from controller.histology_controller import HistologyController
from model.scan_run import ScanRun
from model.histology import Histology
from model.annotation_points import StructureComView
try:
    from settings import data_path, host, password, user, schema
except ImportError as fe:
    print('You must have a settings file in the pipeline directory.', fe)
    raise

class SqlController(ElastixController,StructuresController,TransformationController,
    UrlController,AnimalController,ScanRunController,SectionsController,TasksController,
    SlideController,SlideCZIToTifController,HistologyController,StructureComController,MarkedCellController):
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

    def get_slides_from_animal(self,prep_id):
        scan_run_id = self.get_scan_run(prep_id).id
        return self.get_slides_from_scan_run_id(scan_run_id)

    def get_all_manual_COM(self):
        coms = self.session.query(StructureComView)\
            .filter(StructureComView.source == 'MANUAL').all()
        coms = np.array(coms)
        animals = np.array([i.FK_prep_id for i in coms])
        unique_animals = np.unique(animals)
        all_coms = {}
        for i in unique_animals:
            animal_com = coms[animals==i]
            names = [self.structure_id_to_abbreviation(i.FK_structure_id) for i in animal_com]
            coords = [np.floor([i.x,i.y,i.z]).astype(int) for i in animal_com]
            all_coms[i] = dict(zip(names,coords))
        return all_coms