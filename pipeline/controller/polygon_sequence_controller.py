import pandas as pd

from controller.main_controller import Controller
from model.annotation_points import PolygonSequence
from model.annotation_points import AnnotationSession,AnnotationType



class PolygonSequenceController(Controller):
    '''The class that queries and addes entry to the PolygonSequence table'''
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
        
    def get_available_volumes(self):
        active_sessions = self.get_available_volumes_sessions()
        information = [[i.FK_prep_id,i.user.first_name,i.brain_region.abbreviation] for i in active_sessions]
        return information
    
    def get_volume(self,prep_id, annotator_id, structure_id):
        """Returns the points in a brain region volume

        Args:
            prep_id (str): Animal ID
            annotator_id (int): Annotator ID
            structure_id (int): Structure ID

        Returns:
            dictionary: points in a volume grouped by polygon.
        """        
        #Polygons must be ordered by section(z), then point ordering
        print(prep_id, annotator_id, structure_id, self.schema, self.host)
        session = self.session.query(AnnotationSession)\
            .filter(AnnotationSession.FK_prep_id==prep_id)\
            .filter(AnnotationSession.FK_annotator_id==annotator_id)\
            .filter(AnnotationSession.FK_structure_id==structure_id)\
            .filter(AnnotationSession.active==1).first()
        volume_points = self.session.query(PolygonSequence)\
            .filter(PolygonSequence.FK_session_id==session.id)\
                .order_by(PolygonSequence.z)\
                .order_by(PolygonSequence.point_order)\
                    .all()
        volume = {}
        volume['coordinate']=[[i.x,i.y,i.z] for i in volume_points]
        volume['point_ordering']=[i.point_order for i in volume_points]
        volume['polygon_ordering']=[i.polygon_index for i in volume_points]
        volume = pd.DataFrame(volume)
        return volume
    
    def get_available_volumes_sessions(self):
        """retruns a list of available session objects that is currently active in the database

        Returns:
            list: list of volume sessions
        """        
        active_sessions = self.session.query(AnnotationSession).\
            filter(AnnotationSession.annotation_type==AnnotationType.POLYGON_SEQUENCE)\
            .filter(AnnotationSession.active==1).all()
        return active_sessions