from abakit.model.elastix_transformation import ElastixTransformation
from datetime import datetime
from lib.Controllers.Controller import Controller

class ElasticsController(Controller):

    def __init__(self):
        super().__init__()

    def check_elastix_row(self, animal, section):
        row_exists = bool(self.session.query(ElastixTransformation).filter(
            ElastixTransformation.prep_id == animal,
            ElastixTransformation.section == section).first())
        return row_exists
        
    def add_elastix_row(self, animal, section, rotation, xshift, yshift):
        data = ElastixTransformation(
            prep_id=animal, section=section, rotation=rotation, xshift=xshift, yshift=yshift,
            created=datetime.utcnow(), active=True)
        self.add_row(data)

    def clear_elastix(self, animal):
        self.session.query(ElastixTransformation).filter(ElastixTransformation.prep_id == animal)\
            .delete()