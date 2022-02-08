import os


DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
ROOT_DIR = os.path.join(DATA_PATH, 'pipeline_data')


class FileLocationManager(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, stack):
        """ setup the directory, file locations
            Args:
                stack: the animal brain name, AKA prep_id
        """
        self.root = ROOT_DIR
        self.prep = os.path.join(ROOT_DIR, stack, 'preps')

        self.czi = os.path.join(ROOT_DIR, stack, 'czi')
        self.tif = os.path.join(ROOT_DIR, stack, 'tif')
        self.jp2 = os.path.join(ROOT_DIR, stack, 'jp2')
        self.thumbnail = os.path.join(self.prep, 'CH1', 'thumbnail')
        self.histogram = os.path.join(ROOT_DIR, stack, 'histogram')
        self.thumbnail_web = os.path.join(ROOT_DIR, stack, 'www')
        self.neuroglancer_data = os.path.join(ROOT_DIR, stack, 'neuroglancer_data')

        self.brain_info = os.path.join(ROOT_DIR, stack, 'brains_info')
        self.operation_configs = os.path.join(self.brain_info, 'operation_configs')
        self.mxnet_models = os.path.join(self.brain_info, 'mxnet_models')
        self.atlas_volume = os.path.join(self.brain_info, 'CSHL_volumes', 'atlasV7', 'score_volumes')
        self.classifiers = os.path.join(self.brain_info, 'classifiers')
        self.custom_transform = os.path.join(self.brain_info, 'custom_transform')
        self.mouseatlas_tmp = os.path.join(self.brain_info, 'mouseatlas_tmp')

        self.elastix_dir = os.path.join(self.prep, 'elastix')
        self.full_masked = os.path.join(self.prep, 'full_masked')
        self.full_aligned = os.path.join(self.prep, 'full_aligned')
        self.thumbnail_mask = os.path.join(self.prep, 'masks', 'thumbnail_masked')
        self.rotated_and_padded_thumbnail_mask = os.path.join(self.prep, 'masks', 'thumbnail_rotated_and_padded')
        self.aligned_rotated_and_padded_thumbnail_mask = os.path.join(self.prep, 'masks', 'thumbnail_aligned_rotated_and_padded')
        self.shell = os.path.join(ROOT_DIR, stack,'shell')

    # def get_elastix(self,channel = 1):
    #     return os.path.join(self.prep,f'CH{channel}','elastix')
    
    # def get_full_masked(self,channel = 1):
    #     return os.path.join(self.prep,f'CH{channel}','full_masked')
    
    def get_full_aligned(self,channel = 1):
        return os.path.join(self.prep,f'CH{channel}','full_aligned')
    
    def get_thumbnail_aligned(self,channel = 1):
        return os.path.join(self.prep, f'CH{channel}', 'thumbnail_aligned')
        
    # def get_thumbnail_masked(self,channel = 1):
    #     return os.path.join(self.prep,f'CH{channel}', 'masks', 'thumbnail_masked')
        

