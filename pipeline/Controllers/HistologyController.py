from model.histology import Histology
from Controllers.Controller import Controller
class HistologyController(Controller):
    def get_histology(self,animal):
        return self.get_row(search_dictionary=dict(prep_id = animal),model = Histology)