from datetime import datetime

from database_model.elastix_transformation import ElastixTransformation
from controller.main_controller import Controller

class ElastixController(Controller):
    """Controller class for the elastix table

    Args:
        Controller (Class): Parent class of sqalchemy session
    """

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)

    def check_elastix_row(self, animal, section, iteration=0):
        """checks that a given elastix row exists in the database

        :param animal: (str): Animal ID
        :section (int): Section Number
        :iteration (int): Iteration, which pass are we working on.
        :return boolean: if the row in question exists
        """

        row_exists = bool(self.session.query(ElastixTransformation).filter(
            ElastixTransformation.prep_id == animal,
            ElastixTransformation.iteration == iteration,
            ElastixTransformation.section == section).first())
        return row_exists

    def check_elastix_metric_row(self, animal, section, iteration=0):
        """checks that a given elastix row exists in the database

        :param animal (str): Animal ID
        :iteration (int): Iteration, which pass are we working on.
        :param section (int): Section Number

        :return bool: if the row in question exists
        """

        row_exists = bool(self.session.query(ElastixTransformation).filter(
            ElastixTransformation.prep_id == animal,
            ElastixTransformation.section == section,
            ElastixTransformation.iteration == iteration,
            ElastixTransformation.metric != 0).first())
        return row_exists
    
    def add_elastix_row(self, animal, section, rotation, xshift, yshift, iteration=0):
        """adding a row in the elastix table

        :param animal: (str) Animal ID
        :param section: (str) Section Number
        :param rotation: float
        :param xshift: float
        :param yshift: float
        :iteration (int): Iteration, which pass are we working on.
        """

        data = ElastixTransformation(
            prep_id=animal, section=section, rotation=rotation, xshift=xshift, yshift=yshift, iteration=iteration,
            created=datetime.utcnow(), active=True)
        self.add_row(data)


    def update_elastix_row(self, animal, section, updates):
        """Update a row
        
        :param animal: (str) Animal ID
        :param section: (str) Section Number
        :param updates: dictionary of column:values to update
        """
        self.session.query(ElastixTransformation)\
            .filter(ElastixTransformation.prep_id == animal)\
            .filter(ElastixTransformation.iteration == 1)\
            .filter(ElastixTransformation.section == section).update(updates)
        self.session.commit()
