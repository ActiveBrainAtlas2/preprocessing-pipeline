from controller.main_controller import Controller
from database_model.cell_type import CellType

class CellTypeController(Controller):
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
        
    def get_cell_type_id_to_name(self):
        cell_types = self.query_table({},CellType)
        ids = [i.id for i in cell_types]
        names = [i.cell_type for i in cell_types]
        return dict(zip(ids,names))