
from sqlalchemy.orm.exc import NoResultFound
import os
from model.animal import Animal
from model.histology import Histology
from model.scan_run import ScanRun
from model.slide import Slide
from model.slide_czi_to_tif import SlideCziTif
from sql_setup import dj, database, session


DATA_ROOT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
TIF = 'tif'
HIS = 'histogram'
ROTATED = 'rotated'
PREPS = 'preps'
THUMBNAIL = 'thumbnail'
schema = dj.schema(database)


class SqlController(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
                session: sql session to run queries
        """
        self.session = session
        self.stack_metadata = {}
        #result = session.query(Animal).join(Histology, Histology.prep_id == Animal.prep_id, isouter=True).order_by(Animal.prep_id).all()
        #result = session.query.join(Animal.histology).order_by(Animal.prep_id).all()
        for a, h in session.query(Animal, Histology).filter(Animal.prep_id == Histology.prep_id).all():
            self.stack_metadata[a.prep_id] = {'stain': h.counterstain,
                                 'cutting_plane': h.orientation,
                                 'resolution': 0,
                                 'section_thickness': h.section_thickness}

        print(self.stack_metadata)