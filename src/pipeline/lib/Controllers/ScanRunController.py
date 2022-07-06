from abakit.lib.Controllers.Controller import Controller
from abakit.model.scan_run import ScanRun
from abakit.model.slide import SlideCziTif
from abakit.model.slide import Slide
from sqlalchemy import func

class ScanRunController(Controller):
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
        
    def scan_run_exists(self,animal):
        return self.row_exists(dict(prep_id = animal),ScanRun)
    
    def get_scan_run(self,animal):
        search_dictionary = dict(prep_id = animal)
        return self.get_row(search_dictionary,ScanRun)
    
    def update_scanrun(self, id):
        width = self.session.query(func.max(SlideCziTif.width)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        height = self.session.query(func.max(SlideCziTif.height)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        SAFEMAX = 10000
        LITTLE_BIT_MORE = 500
        # just to be safe, we don't want to update numbers that aren't realistic
        if height > SAFEMAX and width > SAFEMAX:
            height = round(height, -3)
            width = round(width, -3)
            height += LITTLE_BIT_MORE
            width += LITTLE_BIT_MORE
            # width and height get flipped
            try:
                self.session.query(ScanRun).filter(ScanRun.id == id).update(
                    {'width': height, 'height': width})
                self.session.commit()
            except Exception as e:
                print(f'No merge for  {e}')
                self.session.rollback()