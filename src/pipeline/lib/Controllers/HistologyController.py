from abakit.model.histology import Histology
from abakit.lib.Controllers.Controller import Controller
class HistologyController(Controller):
    def get_histology(self,animal):
        return self.get_row(search_dictionary=dict(prep_id = animal),model = Histology)