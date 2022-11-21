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

    def check_elastix_row(self, animal, section):
        """checks that a given elastix row exists in the database

        :param animal: (str): Animal ID
        :section (int): Section Number
        :return boolean: if the row in question exists
        """

        row_exists = bool(self.session.query(ElastixTransformation).filter(
            ElastixTransformation.prep_id == animal,
            ElastixTransformation.section == section).first())
        return row_exists

    def check_elastix_metric_row(self, animal, section):
        """checks that a given elastix row exists in the database

        :param animal (str): Animal ID
        :param section (int): Section Number

        :return bool: if the row in question exists
        """

        row_exists = bool(self.session.query(ElastixTransformation).filter(
            ElastixTransformation.prep_id == animal,
            ElastixTransformation.section == section,
            ElastixTransformation.metric != 0).first())
        return row_exists
    
    def delete_elastix_row(self, animal, section):
        """Deletes a given elastix row in the database

        :param animal: (str) Animal ID
        :param section: (str) Section Number
        """

        search_dictionary = {'prep_id':animal,'section':section}
        self.delete_row(search_dictionary, ElastixTransformation)
    
    def add_elastix_row(self, animal, section, rotation, xshift, yshift):
        """adding a row in the elastix table

        :param animal: (str) Animal ID
        :param section: (str) Section Number
        :param rotation: float
        :param xshift: float
        :param yshift: float
        """

        data = ElastixTransformation(
            prep_id=animal, section=section, rotation=rotation, xshift=xshift, yshift=yshift,
            created=datetime.utcnow(), active=True)
        self.add_row(data)

    def clear_elastix(self, animal):
        """delete an elastix row

        :param animal (str): Animal ID
        """    
        self.session.query(ElastixTransformation).filter(ElastixTransformation.prep_id == animal)\
            .delete()


    def update_elastix_row(self, animal, section, updates):
        """Update a row
        
        :param animal: (str) Animal ID
        :param section: (str) Section Number
        :param updates: dictionary of column:values to update
        """
        self.session.query(ElastixTransformation)\
            .filter(ElastixTransformation.prep_id == animal)\
            .filter(ElastixTransformation.section == section).update(updates)
        self.session.commit()
