from library.database_model.histology import Histology

class HistologyController():
    """Controller class for the histology table
    """
    def __init__(self, session):
        """initiates the controller class
        """
        self.session = session

    def get_histology(self, animal):
        """Gets one single object of histology

        :param animal: string of the animal primary key
        """
        
        return self.get_row(search_dictionary=dict(prep_id = animal), model = Histology)