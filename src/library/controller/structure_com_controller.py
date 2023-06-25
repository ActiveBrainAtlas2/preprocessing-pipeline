import numpy as np

from library.controller.sql_controller import SqlController
from library.database_model.annotation_points import AnnotationSession, AnnotationType, StructureCOM
from library.database_model.brain_region import BrainRegion



class StructureCOMController(SqlController):
    """The class that queries and addes entry to the StructureCOM table
    """

    def get_annotation_dict(self, prep_id, annotator_id):
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
        
        rows = self.session.query(StructureCOM)\
            .filter(StructureCOM.FK_session_id.in_(sids))\
            .join(AnnotationSession)\
                .filter(AnnotationSession.FK_prep_id==prep_id)\
                .filter(AnnotationSession.FK_user_id==annotator_id)\
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

    def get_COM(self, prep_id, annotator_id=2):
        """returns the Center Of Mass of structures for a Animal ID and annotator combination

        Args:
            prep_id (str): Animal ID
            annotator_id (int): Annotator Id

        Returns:
            dict: dictionary of x,y,z coordinates indexed by structure name
        """

        sessions = self.get_available_sessions(prep_id, annotator_id)
        coms = []
        for session in sessions:
            com = self.session.query(StructureCOM)\
                .filter(StructureCOM.FK_session_id == session.id).first()
            coms.append(com)
        coordinate = [[i.x, i.y, i.z] for i in coms if i is not None]
        structure = [
            i.session.brain_region.abbreviation for i in coms if i is not None]
        return dict(zip(structure, coordinate))

    def get_all_manual_COM(self):
        import sys
        coms = self.session.query(StructureCOM)\
            .filter(StructureCOM.source == 'MANUAL').all()
        coms = np.array(coms)
        animals = np.array([i.session.FK_prep_id for i in coms])
        unique_animals = np.unique(animals)
        #animals = [com.session.FK_prep_id for com in coms]
        #animals = np.unique(animals)
        #coms = np.array(coms)
        all_coms = {}
        for animal in unique_animals:
            animal_com = coms[animals==animal]
            print(animal, animal_com.shape)
            names = [self.structure_id_to_abbreviation(i.FK_structure_id) for i in animal_com]
            coords = [np.floor([i.x,i.y,i.z]).astype(int) for i in animal_com]
            #print(animal, names, coords)
            all_coms[animal] = dict(zip(names,coords))
        return all_coms        
    
    def get_available_sessions(self, prep_id, annotator_id):
        sessions = self.session.query(AnnotationSession)\
            .filter(AnnotationSession.active==True)\
            .filter(AnnotationSession.annotation_type==AnnotationType.STRUCTURE_COM)\
            .filter(AnnotationSession.FK_prep_id==prep_id)\
            .filter(AnnotationSession.FK_user_id==annotator_id)\
            .order_by(AnnotationSession.created).all()
        return sessions
