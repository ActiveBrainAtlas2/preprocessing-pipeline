from controller.main_controller import Controller
from database_model.slide import SlideCziTif

class SlideCZIToTifController(Controller):

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        

        Controller.__init__(self,*args,**kwargs)

    def get_tif(self, ID):
        """Get one tif object (row)
        
        :param id: integer primary key
        :return: one tif
        """

        return self.session.query(SlideCziTif).get(ID)

    def update_tif(self, id, width, height):
        """Update a TIFF object (row)
        
        :param id: primary key
        :param width: int of width of TIFF  
        :param height: int of height of TIFF  
        """
        
        try:
            self.session.query(SlideCziTif).filter(
                SlideCziTif.id == id).update({'width': width, 'height': height})
            self.session.commit()
        except Exception as e:
            print(f'No merge for  {e}')
            self.session.rollback()
