import numpy as np
import pandas as pd

from controller.annotation_session_controller import AnnotationSessionController
from controller.main_controller import Controller
from database_model.annotation_points import CellSources, MarkedCell, MarkedCellView
from database_model.cell_type import CellType

class MarkedCellController(AnnotationSessionController):
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)

    def insert_marked_cells(self,coordinates,annotator_id,prep_id,cell_type_id, type:CellSources):
        session_id = self.add_marked_cell_session(prep_id=prep_id,annotator_id=annotator_id)
        for point in coordinates:
            cell = MarkedCell(x = point[0],y=point[1],z=point[2],source = type,FK_session_id=session_id,FK_cell_type_id=cell_type_id)
            self.add_row(cell)
    
    def get_cells_from_sessioni(self,session_id):
        cells = self.query_table(search_dictionary=dict(FK_session_id = session_id),model = MarkedCell)
        return np.array([[i.x,i.y,i.z] for i in cells])
    
    def get_marked_cells(self,search_dictionary):
        return self.query_table(search_dictionary,MarkedCellView)

    def print_cell_types(self):
        cell_types = self.query_table({},CellType)
        for i in cell_types:
            print(i.id,i.cell_type)

user_look_up = {38:'Marissa',41:'Julian'}

def get_DataFrame_from_query_result(results,category,factor):
    values = []
    for i in results:
        source = i.source.value
        if '-' in source:
            source = source.split('-')[1]    
        x,y,z = np.array([i.x,i.y,i.z]).astype(float)/factor
        values.append([x,y,z,f'{category}_{user_look_up[i.FK_annotator_id]}_{source}'])
    # values = [[eval(f'j.{i}')  for j in results ] for i in attr_names]
    df = pd.DataFrame(dict(zip(['x','y','section','name'],np.array(values).T)))
    df["x"] = pd.to_numeric(df["x"])
    df["y"] = pd.to_numeric(df["y"])
    df["section"] = pd.to_numeric(df["section"])
    return df