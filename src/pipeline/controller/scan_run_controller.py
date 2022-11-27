from sqlalchemy import func

from controller.main_controller import Controller
from database_model.scan_run import ScanRun
from database_model.slide import SlideCziTif
from database_model.slide import Slide

class ScanRunController(Controller):
    """Controller for the scan_run table"""

    def __init__(self, *args, **kwargs):
        """initiates the controller class
        """
        Controller.__init__(self, *args, **kwargs)

    def scan_run_exists(self, animal):
        """Check to see if there is a row for this animal in the
        scan run table

        :param animal: the animal (AKA primary key)
        :return boolean: whether the scan run exists for this animal
        """

        return self.row_exists(dict(prep_id=animal), ScanRun)

    def get_scan_run(self, animal):
        """Check to see if there is a row for this animal in the
        scan run table

        :param animal: the animal (AKA primary key)
        :return scan run object: one object (row)
        """

        search_dictionary = dict(prep_id=animal)
        return self.get_row(search_dictionary, ScanRun)

    def update_scanrun(self, id):
        """Update the scan run table with safe and good values for the width and height

        :param id: integer primary key of scan run table
        """
        
        width = self.session.query(func.max(SlideCziTif.width)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        height = self.session.query(func.max(SlideCziTif.height)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        print(f'\tFirst height={height} and width={width}')
        SAFEMAX = 10000
        LITTLE_BIT_MORE = 500
        # just to be safe, we don't want to update numbers that aren't realistic
        if height > SAFEMAX and width > SAFEMAX:
            height = round(height, -3)
            width = round(width, -3)
            height += LITTLE_BIT_MORE
            width += LITTLE_BIT_MORE
            print(f'\tAfter modifications, height={height} and width={width}')
            # width and height get flipped
            try:
                self.session.query(ScanRun).filter(ScanRun.id == id).update(
                    {'width': height, 'height': width})
                self.session.commit()
            except Exception as e:
                print(f'No merge for  {e}')
                self.session.rollback()