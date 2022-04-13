import numpy as np
from abakit.model.layer_data import LayerData
import json
import pandas as pd
from lib.Controllers.Controller import Controller

class LayerDataController(Controller):

    def __init__(self):
        super().__init__()

    def get_values_from_column(self, query_result):
        query_result = query_result.all()
        query_result = [entryi[0] for entryi in query_result]
        return query_result

    def get_layer_data(self,search_dictionary):
        query_start = self.session.query(LayerData)
        for key, value in search_dictionary.items():
            query_start = eval(f'query_start.filter(LayerData.{key}=="{value}")')
        return query_start.all()
    
    def add_layer_data(self, abbreviation, animal, layer, x, y, section, 
                       person_id, input_type_id):
        """
        Look up the structure id from the structure.
        Args:
            structure: abbreviation with the _L or _R ending
            animal: prep_id
            x=float of x coordinate
            y=float of y coordinate
            section = int of z/section coordinate
        Returns:
            nothing, just merges
        try:
            structure = self.session.query(Structure) \
                .filter(Structure.abbreviation == func.binary(abbreviation)).one()
        except NoResultFound:
            print(f'No structure for {abbreviation}')
        """

        structure_id = self.structure_abbreviation_to_id(abbreviation)
        coordinates = (x,y,section)
        self.add_layer_data_row(animal,person_id,input_type_id,coordinates,structure_id,layer)

    def get_layer_data_entry(self, prep_id, input_type_id=1, person_id=2,active = True,layer = 'COM'):
        rows = self.session.query(LayerData)\
            .filter(LayerData.active.is_(active))\
            .filter(LayerData.prep_id == prep_id)\
            .filter(LayerData.input_type_id == input_type_id)\
            .filter(LayerData.person_id == person_id)\
            .filter(LayerData.layer == layer)\
            .all()
        row_dict = {}
        for row in rows:
            structure = row.structure.abbreviation
            row_dict[structure] = [row.x, row.y, row.section]
        return row_dict


    def add_layer_data_row(self,animal,person_id,input_type_id,coordinates,structure_id,layer):
        x,y,z = coordinates
        data = LayerData(prep_id = animal, person_id = person_id, input_type_id = input_type_id, x=x, y=y, \
            section=z,structure_id=structure_id,layer=layer)
        self.add_row(data)
    
    def add_com(self, prep_id, abbreviation, coordinates, person_id=2 , input_type_id = 1):
        structure_id = self.structure_abbreviation_to_id(abbreviation)
        if self.layer_data_row_exists(animal=prep_id,person_id = person_id,input_type_id = input_type_id,\
            structure_id = structure_id,layer = 'COM'):
            self.delete_layer_data_row(animal=prep_id,person_id = person_id,input_type_id = input_type_id,\
                structure_id = structure_id,layer = 'COM')
        self.add_layer_data_row(animal = prep_id,person_id = person_id,input_type_id = input_type_id,\
            coordinates = coordinates,structure_id = structure_id,layer = 'COM')
    
    def layer_data_row_exists(self,animal, person_id, input_type_id, structure_id, layer):
        row_exists = bool(self.session.query(LayerData).filter(
            LayerData.prep_id == animal, 
            LayerData.person_id == person_id, 
            LayerData.input_type_id == input_type_id, 
            LayerData.structure_id == structure_id,
            LayerData.layer == layer).first())
        return row_exists
 
    def delete_layer_data_row(self,animal,person_id,input_type_id,structure_id,layer):
        self.session.query(LayerData)\
            .filter(LayerData.active.is_(True))\
            .filter(LayerData.prep_id == animal)\
            .filter(LayerData.input_type_id == input_type_id)\
            .filter(LayerData.person_id == person_id)\
            .filter(LayerData.structure_id == structure_id)\
            .filter(LayerData.layer == layer).delete()
        self.session.commit()
    
    def get_com_dict(self, prep_id, input_type_id=1, person_id=2,active = True):
        return self.get_layer_data_entry( prep_id = prep_id, input_type_id=input_type_id,\
             person_id=person_id,active = active,layer = 'COM')

    def get_atlas_centers(self):
        PERSON_ID_LAUREN = 16
        INPUT_TYPE_MANUAL = 1
        return self.get_com_dict('Atlas',INPUT_TYPE_MANUAL,PERSON_ID_LAUREN)
    
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
            layers = json_txt['layers']
            for l in layers:
                if 'annotations' in l:
                    name = l['name']
                    annotation = l['annotations']
                    d = [row['point'] for row in annotation]
                    df = pd.DataFrame(d, columns=['X', 'Y', 'Section'])
                    df['X'] = df['X'].astype(int)
                    df['Y'] = df['Y'].astype(int)
                    df['Section'] = df['Section'].astype(int)
                    df['Layer'] = name
                    df = df[['Layer', 'X', 'Y', 'Section']]
                    dfs.append(df)
            if len(dfs) == 0:
                result = None
            elif len(dfs) == 1:
                result = dfs[0]
            else:
                result = pd.concat(dfs)

        return result
    
    def get_annotated_animals(self):
        results = self.session.query(LayerData)\
            .filter(LayerData.active.is_(True))\
            .filter(LayerData.input_type_id == 1)\
            .filter(LayerData.person_id == 2)\
            .filter(LayerData.layer == 'COM').all()
        return np.unique([ri.prep_id for ri in results])