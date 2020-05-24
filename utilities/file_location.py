import os


ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
PREPS = 'preps'
THUMBNAIL = 'thumbnail'
BRAIN_INFO = 'brains_info'

class FileLocationManager(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, stack):
        """ setup the directory, file locations
            Args:
                stack: the animal brain name, AKA prep_id
        """
        self.root = ROOT_DIR
        self.CSHL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes'
        self.operation_configs = os.path.join(ROOT_DIR, stack, BRAIN_INFO, 'operation_configs')
        self.mxnet_models = os.path.join(ROOT_DIR, stack, BRAIN_INFO, 'mxnet_models')
        self.atlas_volume = os.path.join(ROOT_DIR, stack, BRAIN_INFO, 'CSHL_volumes', 'atlasV7', 'score_volumes')
        self.classifiers = os.path.join(ROOT_DIR, stack, BRAIN_INFO, 'classifiers')

        self.czi = os.path.join(ROOT_DIR, stack, 'czi')
        self.tif= os.path.join(ROOT_DIR, stack, 'tif')
        self.thumbnail_web = os.path.join(ROOT_DIR, stack, THUMBNAIL)
        self.thumbnail_prep = os.path.join(ROOT_DIR, stack, PREPS, THUMBNAIL)
        self.brain_info = os.path.join(ROOT_DIR, stack, BRAIN_INFO)
        self.oriented = os.path.join(ROOT_DIR, stack, PREPS, 'oriented')
        self.histogram = os.path.join(ROOT_DIR, stack, 'histogram')
        self.custom_transform = os.path.join(self.brain_info, 'custom_transform')
        self.aligned = os.path.join(ROOT_DIR, stack, PREPS, 'aligned')
        self.prealigned = os.path.join(ROOT_DIR, stack, PREPS, 'prealigned')
        self.padded = os.path.join(ROOT_DIR, stack, PREPS, 'padded')
        self.elastix_dir = os.path.join(ROOT_DIR, stack, PREPS, 'elastix')
        self.custom_output = os.path.join(ROOT_DIR, stack, PREPS, 'custom_output')
        self.mouseatlas_tmp = os.path.join(self.brain_info, 'mouseatlas_tmp')
        self.masked = os.path.join(ROOT_DIR, stack, PREPS, 'masked')
