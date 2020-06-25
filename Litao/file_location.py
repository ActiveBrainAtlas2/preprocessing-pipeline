import os

ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
CSHL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes'


class FileLocationManager(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, stack):
        """ setup the directory, file locations
            Args:
                stack: the animal brain name, AKA prep_id
        """
        self.root = ROOT_DIR
        self.cshl = CSHL_DIR

        self.czi = os.path.join(ROOT_DIR, stack, 'czi')
        self.tif = os.path.join(ROOT_DIR, stack, 'tif')
        self.histogram = os.path.join(ROOT_DIR, stack, 'histogram')
        self.thumbnail = os.path.join(ROOT_DIR, stack, 'thumbnail')
        self.thumbnail_web = os.path.join(ROOT_DIR, stack, 'www')

        self.brain_info = os.path.join(ROOT_DIR, stack, 'brains_info')
        self.operation_configs = os.path.join(self.brain_info, 'operation_configs')
        self.mxnet_models = os.path.join(self.brain_info, 'mxnet_models')
        self.atlas_volume = os.path.join(self.brain_info, 'CSHL_volumes', 'atlasV7', 'score_volumes')
        self.classifiers = os.path.join(self.brain_info, 'classifiers')
        self.custom_transform = os.path.join(self.brain_info, 'custom_transform')
        self.mouseatlas_tmp = os.path.join(self.brain_info, 'mouseatlas_tmp')

        self.prep = os.path.join(ROOT_DIR, stack, 'preps')
        self.elastix_dir = os.path.join(self.prep, 'elastix')
        self.masked = os.path.join(self.prep, 'masked')

        '''
        self.thumbnail_prep = os.path.join(self.prep, 'thumbnail')
        self.oriented = os.path.join(ROOT_DIR, stack, PREPS, 'oriented')
        self.aligned = os.path.join(ROOT_DIR, stack, PREPS, 'aligned')
        self.prealigned = os.path.join(ROOT_DIR, stack, PREPS, 'prealigned')
        self.padded = os.path.join(ROOT_DIR, stack, PREPS, 'padded')
        self.custom_output = os.path.join(ROOT_DIR, stack, PREPS, 'custom_output')
        self.cleaned = os.path.join(ROOT_DIR, stack, PREPS, 'cleaned')
        self.normalized = os.path.join(ROOT_DIR, stack, PREPS, 'normalized')
        '''

    def get_prep_channel_dir(self, channel, full, tail=None):
        channel_path = os.path.join(self.prep, f'CH{channel}')
        if full:
            path = os.path.join(channel_path, 'full')
        else:
            path = os.path.join(channel_path, 'thumbnail')

        if tail is not None:
            path = os.path.join(path, tail)

        return path
