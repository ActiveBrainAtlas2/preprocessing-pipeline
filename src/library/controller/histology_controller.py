from library.controller.main_controller import Controller
from library.database_model.histology import Histology

class HistologyController(Controller):
    """Controller class for the histology table
    """

    def get_histology(self, animal):
        """Gets one single object of histology

        :param animal: string of the animal primary key
        """
        
        return self.get_row(search_dictionary=dict(prep_id = animal),model = Histology)