import os


ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
CZI = 'czi'
TIF = 'tif'
HISTOGRAM = 'histogram'
ORIENTED = 'oriented'
PREPS = 'preps'
THUMBNAIL = 'thumbnail'
BRAIN_INFO = 'brain_info'
CUSTOM_TRANSFORM = 'custom_transform'
ALIGNEDTO = 'aligned_to'


class FileLocationManager(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, stack):
        """ setup the directory, file locations
            Args:
                stack: the animal brain name, AKA prep_id
        """
        self.root = ROOT_DIR
        self.czi = os.path.join(ROOT_DIR, stack, CZI)
        self.tif = os.path.join(ROOT_DIR, stack, TIF)
        self.thumbnail_web = os.path.join(ROOT_DIR, stack, THUMBNAIL)
        self.thumbnail_prep = os.path.join(ROOT_DIR, stack, PREPS, THUMBNAIL)
        self.brain_info = os.path.join(ROOT_DIR, stack, BRAIN_INFO)
        self.oriented = os.path.join(ROOT_DIR, stack, PREPS, ORIENTED)
        self.histogram = os.path.join(ROOT_DIR, stack, HISTOGRAM)
        self.custom_transform = os.path.join(self.brain_info, CUSTOM_TRANSFORM)
        self.aligned_to = os.path.join(ROOT_DIR, stack, PREPS, ALIGNEDTO)