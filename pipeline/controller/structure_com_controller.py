from controller.annotation_session_controller import AnnotationSessionController
from database_model.annotation_points import AnnotationSession, StructureCOM

class StructureComController(AnnotationSessionController):
    '''The class that queries and addes entry to the StructureCom table'''
    
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        AnnotationSessionController.__init__(self,*args,**kwargs)

    def get_COM(self,prep_id,annotator_id=2):
        """returns the Center Of Mass of structures for a Animal ID and annotator combination

        Args:
            prep_id (str): Animal ID
            annotator_id (int): Annotator Id

        Returns:
            dict: dictionary of x,y,z coordinates indexed by structure name
        """    
        sessions = self.session.query(AnnotationSession).filter(AnnotationSession.FK_prep_id==prep_id)\
                                                        .filter(AnnotationSession.FK_annotator_id==annotator_id)\
                                                        .filter(AnnotationSession.active==1).all()
        coms = []
        for sessioni in sessions:                                                    
            com = self.session.query(StructureCOM)\
                .filter(StructureCOM.FK_session_id==sessioni.id).first()   
            coms.append(com)
        coordinate = [[i.x,i.y,i.z] for i in coms if i is not None]
        structure = [i.session.brain_region.abbreviation for i in coms if i is not None]
        return dict(zip(structure,coordinate))
    
    def get_atlas_centers(self):
        return self.get_COM('Atlas',annotator_id=16)
    
    def insert_com(self, coordinate, annotator_id, prep_id, structure_id, source):
        session_id = self.add_structure_com_session(prep_id, annotator_id, structure_id)
        cell = StructureCOM(x=coordinate[0], y=coordinate[1], 
        z=coordinate[2], source=source, FK_session_id=session_id)
        self.add_row(cell)
