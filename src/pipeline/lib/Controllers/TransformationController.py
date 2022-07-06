from abakit.lib.Controllers.Controller import Controller
from abakit.model.transformation import Transformation
from abakit.model.transformation_type import TransformationType
import pickle
class TransformationController(Controller):

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
    
    def add_transformation_row(self,source,destination,transformation_type,transformation):
        """adding a row to the transformation table

        Args:
            source (str): Animal ID of The stack/atlas coordinates where we are transforming from
            destination (str): Animal ID of The stack/atlas coordinates where we are transforming to
            transformation_type (str): type of transformation
            transformation (Transformation): Sqalchemy transformation entry
        """        
        data = Transformation(source = source, destination = destination,transformation_type = transformation_type, transformation = transformation )
        self.add_row(data)

    def has_transformation(self,source,destination):
        """Check if a transformation entry exists in the database

        Args:
            source (str): Animal ID of the stack/atlas coordiantes where we are transforming from
            destination (str): Animal ID of the stack/atlas coordinates where we are transforming to

        Returns:
            bool: if a transformation row exists
        """        
        return bool(self.session.query(Transformation).filter(Transformation.source == source, Transformation.destination == destination).first())
    
    def get_transformation_row(self,source,destination,transformation_type):
        """get a row from the transformation table

        Args:
            source (str): Animal ID of the stack/atlas coordiantes where we are transforming from
            destination (str): Animal ID of the stack/atlas coordinates where we are transforming to
            transformation_type (str): Type of transformation, must match entries in the transformation type table

        Returns:
            Sqalchemy orm: transformation row orm from Sqlalchemy
        """        
        type_id = self.get_row(dict(transformation_type=transformation_type),TransformationType).id
        search_dictionary = dict(source = source,destination=destination,transformation_type = type_id)
        return self.get_row(search_dictionary,Transformation)
    
    def get_transformation(self,source,destination,transformation_type):
        """getting a row from the transformation table

        Args:
            source (str): Animal ID of the stack/atlas coordiantes where we are transforming from
            destination (str): Animal ID of the stack/atlas coordinates where we are transforming to
            transformation_type (str): Type of transformation, must match entries in the transformation type table

        Returns:
            Transformation: Aba kit Transformation type with functions for transforming points ready to use
        """        
        transformation = self.get_transformation_row(source,destination,transformation_type)
        return pickle.loads(transformation.transformation)