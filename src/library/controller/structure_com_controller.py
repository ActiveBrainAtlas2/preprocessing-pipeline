import pandas as pd

from library.controller.main_controller import Controller
from library.database_model.annotation_points import StructureCOM
from library.database_model.annotation_points import AnnotationSession,AnnotationType



class StructureCOMController(Controller):
    """The class that queries and addes entry to the StructureCOM table
    """

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self, *args, **kwargs)
        
    
    def get_available_volumes_sessions(self):
        """retruns a list of available session objects that is currently active in the database

        Returns:
            list: list of volume sessions
        """        
        active_sessions = self.session.query(AnnotationSession).\
            filter(AnnotationSession.annotation_type==AnnotationType.STRUCTURE_COM)\
            .filter(AnnotationSession.active==1).all()
        return active_sessions