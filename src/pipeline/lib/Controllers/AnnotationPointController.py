import numpy as np
from abakit.model.annotation_points import AnnotationPoint
import json
import pandas as pd
from abakit.lib.Controllers.Controller import Controller


class AnnotationPointController(Controller):
    """This class is about to be depricated as the annotation points table are to be split into the PolygonSequence,
       StructureCom and MarkedCells table
    """
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)

    def get_annotation_points_orm(self, search_dictionary):
        """The main function for querying the annoataion points table

        Args:
            search_dictionary (dict): column name and value pair for the search

        Returns:
            list: list of sqlalchemy ORM objects
        """
        return self.query_table(search_dictionary, AnnotationPoint)

    def add_annotation_points(self, abbreviation, animal, label, x, y, section,
                              FK_owner_id, FK_input_id):
        """adding a row to annotation points table

        Args:
            abbreviation (string): structure name short hand
            animal (string): animal name
            label (string): label name
            x (float): x coordinate
            y (float): y coordinate
            section (int): z section number
            FK_owner_id (int): id of annotator 
            FK_input_id (int): id of input type
        """
        FK_structure_id = self.structure_abbreviation_to_id(abbreviation)
        coordinates = (x, y, section)
        self.add_annotation_points(
            animal, FK_owner_id, FK_input_id, coordinates, FK_structure_id, label)

    def get_annotation_points(self, prep_id, FK_input_id=1, FK_owner_id=2, active=1, label='COM'):
        """function to obtain coordinates of annotation points

        Args:
            prep_id (str): Animal ID
            FK_input_id (int, optional): int for input type. Defaults to 1.
            FK_owner_id (int, optional): annotation id. Defaults to 2.
            active (bool, optional): search of active or inactive annotations. Defaults to True.
            label (str, optional): label name. Defaults to 'COM'.

        Returns:
            _type_: _description_
        """
        search_dictionary = dict(prep_id=prep_id,
                                 FK_input_id=FK_input_id,
                                 FK_owner_id=FK_owner_id,
                                 label=label,
                                 active=1)
        rows = self.get_annotation_points_orm(search_dictionary)
        search_result = {}
        for row in rows:
            structure = row.brain_region.abbreviation
            search_result[structure] = [row.x, row.y, row.z]
        return search_result

    def add_annotation_points(self, animal, FK_owner_id, FK_input_id, coordinates, FK_structure_id, label):
        """adding a row to the annotation points table

        Args:
            animal (str): Animal ID
            FK_owner_id (int): Annotator ID
            FK_input_id (int): Input Type ID
            coordinates (list): list of x,y,z coordinates
            FK_structure_id (int): Structure ID
            label (str): label name
        """
        x, y, z = coordinates
        data = AnnotationPoint(prep_id=animal, FK_owner_id=FK_owner_id, FK_input_id=FK_input_id, x=x, y=y,
                               section=z, FK_structure_id=FK_structure_id, label=label)
        self.add_row(data)

    def add_com(self, prep_id, abbreviation, coordinates, FK_owner_id=2, FK_input_id=1):
        """Adding a Com Entry

        Args:
            prep_id (str): Animal ID
            abbreviation (str): structure abbreviation
            coordinates (list): list of x,y,z coordinates
            FK_owner_id (int, optional): Annotator ID. Defaults to 2.
            FK_input_id (int, optional): Input Type ID. Defaults to 1.
        """
        FK_structure_id = self.structure_abbreviation_to_id(abbreviation)
        if self.label_data_row_exists(animal=prep_id, FK_owner_id=FK_owner_id, FK_input_id=FK_input_id,
                                      FK_structure_id=FK_structure_id, label='COM'):
            self.delete_label_data_row(animal=prep_id, FK_owner_id=FK_owner_id, FK_input_id=FK_input_id,
                                       FK_structure_id=FK_structure_id, label='COM')
        self.add_annotation_points(animal=prep_id, FK_owner_id=FK_owner_id, FK_input_id=FK_input_id,
                                   coordinates=coordinates, FK_structure_id=FK_structure_id, label='COM')

    def label_data_row_exists(self, animal, FK_owner_id, FK_input_id, FK_structure_id, label):
        row_exists = bool(self.session.query(AnnotationPoint).filter(
            AnnotationPoint.prep_id == animal,
            AnnotationPoint.FK_owner_id == FK_owner_id,
            AnnotationPoint.FK_input_id == FK_input_id,
            AnnotationPoint.FK_structure_id == FK_structure_id,
            AnnotationPoint.label == label).first())
        return row_exists

    def delete_label_data_row(self, animal, FK_owner_id, FK_input_id, FK_structure_id, label):
        self.session.query(AnnotationPoint)\
            .filter(AnnotationPoint.active.is_(True))\
            .filter(AnnotationPoint.prep_id == animal)\
            .filter(AnnotationPoint.FK_input_id == FK_input_id)\
            .filter(AnnotationPoint.FK_owner_id == FK_owner_id)\
            .filter(AnnotationPoint.FK_structure_id == FK_structure_id)\
            .filter(AnnotationPoint.label == label).delete()
        self.session.commit()

    def get_com_dict(self, prep_id, FK_input_id=1, FK_owner_id=2, active=1):
        return self.get_annotation_points(prep_id=prep_id, FK_input_id=FK_input_id,
                                          FK_owner_id=FK_owner_id, active=active, label='COM')

    def get_atlas_centers(self):
        FK_owner_id_LAUREN = 16
        INPUT_TYPE_MANUAL = 1
        return self.get_com_dict('Atlas', INPUT_TYPE_MANUAL, FK_owner_id_LAUREN)

    def get_point_dataframe(self, id):
        """
        :param id: primary key from the url. Look at:
         https://activebrainatlas.ucsd.edu/activebrainatlas/admin/neuroglancer/points/164/change/
         for example use 164 for the primary key
         to get the ID
        :return: a pandas dataframe
        """

        try:
            urlModel = self.session.query(
                UrlModel).filter(UrlModel.id == id).one()
        except NoResultFound as nrf:
            print('Bad ID for {} error: {}'.format(id, nrf))
            return

        result = None
        dfs = []
        if urlModel.url is not None:
            json_txt = json.loads(urlModel.url)
            labels = json_txt['labels']
            for l in labels:
                if 'annotations' in l:
                    name = l['name']
                    annotation = l['annotations']
                    d = [row['point'] for row in annotation]
                    df = pd.DataFrame(d, columns=['X', 'Y', 'Section'])
                    df['X'] = df['X'].astype(int)
                    df['Y'] = df['Y'].astype(int)
                    df['Section'] = df['Section'].astype(int)
                    df['label'] = name
                    df = df[['label', 'X', 'Y', 'Section']]
                    dfs.append(df)
            if len(dfs) == 0:
                result = None
            elif len(dfs) == 1:
                result = dfs[0]
            else:
                result = pd.concat(dfs)

        return result

    def get_annotated_animals(self):
        results = self.session.query(AnnotationPoint)\
            .filter(AnnotationPoint.active.is_(True))\
            .filter(AnnotationPoint.FK_input_id == 1)\
            .filter(AnnotationPoint.FK_owner_id == 2)\
            .filter(AnnotationPoint.label == 'COM').all()
        return np.unique([ri.prep_id for ri in results])
