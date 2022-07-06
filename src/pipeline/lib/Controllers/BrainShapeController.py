from abakit.lib.Controllers.Controller import Controller
class BrainShapeController(Controller):
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
        
    def insert_shapes(self):
        ...
    
    def get_shapes(self):
        ...
    
    def get_available_shapes(self):
        ...
    ...