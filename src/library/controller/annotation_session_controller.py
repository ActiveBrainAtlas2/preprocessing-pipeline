import datetime
from sqlalchemy.orm.exc import NoResultFound

from library.controller.main_controller import Controller
from library.database_model.brain_region import BrainRegion
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
                .filter(AnnotationSession.active==1).all()
        return active_sessions
    
    def get_brain_region(self, abbreviation):
        brain_region = self.session.query(BrainRegion) \
                .filter(BrainRegion.abbreviation==abbreviation)\
                .filter(BrainRegion.active==1).one_or_none()
        return brain_region
    

    def get_annotation_session(self, prep_id, brain_region_id, annotator_id):
        annotation_session = self.session.query(AnnotationSession).filter(AnnotationSession.active==True)\
            .filter(AnnotationSession.annotation_type==AnnotationType.STRUCTURE_COM)\
            .filter(AnnotationSession.FK_prep_id==prep_id)\
            .filter(AnnotationSession.FK_brain_region_id==brain_region_id)\
            .filter(AnnotationSession.FK_user_id==annotator_id)\
            .order_by(AnnotationSession.created.desc()).first()

        if annotation_session is None:
            annotation_session = AnnotationSession(
                FK_prep_id=prep_id,
                FK_user_id=annotator_id,
                FK_brain_region_id=brain_region_id,
                annotation_type=AnnotationType.STRUCTURE_COM,
                active=True,
                created=datetime.datetime.now())
            """
            FK_prep_id = Column(String, nullable=False)
            FK_user_id = Column(Integer, ForeignKey('auth_user.id'), nullable=True)
            FK_brain_region_id = Column(Integer, ForeignKey('brain_region.id'),nullable=True)
            annotation_type = Column(Enum(AnnotationType))    
            brain_region = relationship('BrainRegion', lazy=True, primaryjoin="AnnotationSession.FK_brain_region_id == BrainRegion.id")
            annotator = relationship('User', lazy=True)
            active =  Column(Integer,default=1)
            created =  Column(DateTime)
            """

            self.session.add(annotation_session)
            self.session.commit()
            self.session.refresh(annotation_session)
            
        return annotation_session


