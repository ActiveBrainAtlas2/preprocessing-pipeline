from controller.main_controller import Controller
from database_model.slide import Slide

class SlideController(Controller):

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """ 

        Controller.__init__(self,*args,**kwargs)

    def get_slide(self, ID):
        """Get one slide object (row)
        
        :param id: integer primary key
        :return: one slide
        """

        return self.session.query(Slide).filter(Slide.id == ID).one()
    
    def get_slides_from_scan_run_id(self, scan_run_id):
        """Gets all slides for a given scan run
        
        :param scan_run_id: ID that will designate all slides for an animal
        :return list: of slides for an animal
        """
        
        return self.session.query(Slide).filter(Slide.scan_run_id == scan_run_id).all()
        