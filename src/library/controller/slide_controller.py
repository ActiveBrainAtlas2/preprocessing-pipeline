from library.controller.main_controller import Controller
from library.database_model.slide import Slide

class SlideController(Controller):

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """ 

        Controller.__init__(self,*args,**kwargs)
        