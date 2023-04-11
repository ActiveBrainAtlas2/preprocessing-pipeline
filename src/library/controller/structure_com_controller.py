import pandas as pd

from library.controller.main_controller import Controller
from library.database_model.annotation_points import AnnotationSession, AnnotationType, StructureCOM
from library.database_model.brain_region import BrainRegion



class StructureCOMController(Controller):
    """The class that queries and addes entry to the StructureCOM table
    """

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self, *args, **kwargs)

    def get_annotation_dict(self, prep_id, annotator_id, source):
        """This method replaces get_centers_dict and get_layer_data_row.

        :param prep_id: string name of animal
        :param label: formerly layer, the string name of the layer
        """

        row_dict = {}
        """
        try:
            animal = Animal.objects.get(pk=prep_id)
        except Animal.DoesNotExist:
            logger.error(f'Error, {prep_id} does not exist in DB. Method: get_annotation_dict is returning an empty dictionary.')
            return row_dict
        base = AnnotationBase()
        base.set_animal_from_id(prep_id)
        base.set_annotator_from_id(annotator_id)
        """

        sessions = self.get_available_sessions(prep_id, annotator_id)

        sids = [session.id for session in sessions]
        # ses.query(FooBar).join(Bar).join(Foo).filter(Foo.name == "blah")
        
        rows = self.session.query(StructureCOM)\
            .filter(StructureCOM.FK_session_id.in_(sids))\
            .join(AnnotationSession)\
                .filter(AnnotationSession.FK_prep_id==prep_id)\
                .filter(AnnotationSession.FK_annotator_id==annotator_id)\
            .   all()
        brain_region_dict = {}
        brain_regions = self.session.query(BrainRegion).filter(BrainRegion.active==True).all()
        for brain_region in brain_regions:
            brain_region_dict[brain_region.id] = brain_region.abbreviation

        for row in rows:
            brain_region_id = row.session.brain_region.id
            abbreviation = brain_region_dict[brain_region_id]
            row_dict[abbreviation] = [row.x, row.y, row.z]
        return row_dict


        
    
    def get_available_sessions(self, prep_id, annotator_id):
        annotation_session = self.session.query(AnnotationSession).filter(AnnotationSession.active==True)\
            .filter(AnnotationSession.annotation_type==AnnotationType.STRUCTURE_COM)\
            .filter(AnnotationSession.FK_prep_id==prep_id)\
            .filter(AnnotationSession.FK_annotator_id==annotator_id)\
            .order_by(AnnotationSession.created).all()
        return annotation_session
