from lib.Controllers.Controller import Controller
from abakit.model.transformation import Transformation

class TransformationController(Controller):

    def __init__(self):
        super().__init__()
    
    def add_transformation_row(self,source,destination,transformation_type,transformation):
        data = Transformation(source = source, destination = destination,transformation_type = transformation_type, transformation = transformation )
        self.add_row(data)

    def has_transformation(self,source,destination):
        return bool(self.session.query(Transformation).filter(Transformation.source == source, Transformation.destination == destination).first())