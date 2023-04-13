import datetime
from sqlalchemy.orm.exc import NoResultFound

from library.controller.main_controller import Controller
from library.database_model.brain_region import BrainRegion
from library.database_model.annotation_points import StructureCOM
from library.database_model.annotation_points import AnnotationSession, AnnotationType



class AnnotationSessionController(Controller):
    """The class that queries and addes entry to the annotation_session table
    """

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self, *args, **kwargs)
        
    
    def get_existing_session(self):
        """retruns a list of available session objects that is currently active in the database

        Returns:
            list: list of volume sessions
        """ 
        active_sessions = self.session.query(AnnotationSession) \
                .filter(AnnotationSession.annotation_type==AnnotationType.STRUCTURE_COM)\
                .filter(AnnotationSession.active==True).all()
        return active_sessions
    
    def get_brain_region(self, abbreviation):
        brain_region = self.session.query(BrainRegion) \
                .filter(BrainRegion.abbreviation==abbreviation)\
                .filter(BrainRegion.active==True).one_or_none()
        return brain_region
    

    def get_annotation_session(self, prep_id, brain_region_id, annotator_id):
        annotation_session = self.session.query(AnnotationSession).filter(AnnotationSession.active==True)\
            .filter(AnnotationSession.annotation_type==AnnotationType.STRUCTURE_COM)\
            .filter(AnnotationSession.FK_prep_id==prep_id)\
            .filter(AnnotationSession.FK_structure_id==brain_region_id)\
            .filter(AnnotationSession.FK_annotator_id==annotator_id)\
            .order_by(AnnotationSession.created.desc()).first()

        if annotation_session is None:
            annotation_session = AnnotationSession(
                FK_prep_id=prep_id,
                FK_annotator_id=annotator_id,
                FK_structure_id=brain_region_id,
                annotation_type=AnnotationType.STRUCTURE_COM,
                active=True,
                created=datetime.datetime.now())

            self.session.add(annotation_session)
            self.session.commit()
            self.session.refresh(annotation_session)
            
        return annotation_session

    def upsert_structure_com(self, entry):
        """Method to do update/insert. It first checks if there is already an entry. If not,
        it does insert otherwise it updates.
        """
        FK_session_id = entry['FK_session_id']
        structure_com = self.session.query(StructureCOM).filter(StructureCOM.FK_session_id==FK_session_id).first()
        if structure_com is None:
            data = StructureCOM(
                source=entry['source'],
                FK_session_id = FK_session_id,
                x = entry['x'],
                y = entry['y'],
                z = entry['z']
            )
            self.add_row(data)
        else:
            self.session.query(StructureCOM)\
                .filter(StructureCOM.FK_session_id == FK_session_id).update(entry)
            self.session.commit()


