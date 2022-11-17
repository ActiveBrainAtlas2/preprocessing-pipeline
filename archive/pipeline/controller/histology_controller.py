from controller.main_controller import Controller
from database_model.histology import Histology

class HistologyController(Controller):
    def get_histology(self,animal):
        return self.get_row(search_dictionary=dict(prep_id = animal),model = Histology)