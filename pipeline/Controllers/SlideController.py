from Controllers.Controller import Controller
from model.slide import Slide
class SlideController(Controller):

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)

    def get_slide(self, ID):
        """
        Args:
            id: integer primary key

        Returns: one slide
        """
        return self.session.query(Slide).filter(Slide.id == ID).one()
    
    def get_slides_from_scan_run_id(self,scan_run_id):
        return self.session.query(Slide).filter(Slide.scan_run_id == scan_run_id).all()
        