from abakit.lib.Controllers.AnnotationSessionController import AnnotationSessionController
from abakit.model.annotation_points import CellSources,MarkedCell
from abakit.model.cell_type import CellType
from abakit.lib.Controllers.Controller import Controller
import numpy as np

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
        session = self.get_annotation_session(search_dictionary)
        self.get_cells_from_sessioni(session.id)
        

    def print_cell_types(self):
        cell_types = self.query_table({},CellType)
        for i in cell_types:
            print(i.id,i.cell_type)