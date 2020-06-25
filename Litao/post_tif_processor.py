import os
import sys
import time
from shutil import copyfile

import datajoint as dj
import cv2
from skimage import io
from sqlalchemy.orm.exc import NoResultFound
from tqdm import tqdm

from Litao.database_schema import AlcAnimal, AlcRawSection
from Litao.file_location import FileLocationManager
from Litao.utilities_mask import make_mask, apply_mask
from Litao.database_setup import schema, session, RawSection


class PostTIFProcessor(object):
    """ Create a class for processing the pipeline after the TIF files are generated.
    The TIF files for the specified prep_id are assumed to be generated and uploaded to the correct folder on birdstore.
    All the output files will be properly stored in the animal's preps folder.
    """

    def __init__(self, prep_id, full):
        """ setup the attributes for the PostCZIProcessor class

        Args:
            prep_id: the prep_id of animal to process
            full: indicate whether to process full TIF image or thumbnails
        """

        try:
            animal = session.query(AlcAnimal).filter(AlcAnimal.prep_id == prep_id).one()
        except (NoResultFound):
            print('No results found for prep_id: {}.'.format(prep_id))
            sys.exit()

        self.animal = animal
        self.full = full
        self.file_location_manager = FileLocationManager(animal.prep_id)

    def preprocess_prep_dir(self):
        """ Copy the files that will be processed to the different channel folders in preps.
        """

        raw_section_rows = session.query(AlcRawSection).filter(AlcRawSection.prep_id == self.animal.prep_id) \
            .filter(AlcRawSection.active == 1).filter(AlcRawSection.file_status == 'good')

        for raw_section_row in raw_section_rows:
            if self.full:
                src_folder = self.file_location_manager.tif
            else:
                src_folder = self.file_location_manager.thumbnail
            src_file = os.path.join(src_folder, raw_section_row.destination_file)
            dst_file = os.path.join(self.file_location_manager.get_prep_channel_dir(raw_section_row.channel, self.full),
                                    str(raw_section_row.section_number).zfill(3) + '.tif')

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            copyfile(src_file, dst_file)

    def make_mask_dir(self):
        input_dir = self.file_location_manager.get_prep_channel_dir(1, self.full)
        for file_name in tqdm(sorted(os.listdir(input_dir))):
            input_path = os.path.join(input_dir, file_name)
            masked_path = os.path.join(self.file_location_manager.masked, file_name)
            cleaned_path = os.path.join(self.file_location_manager.get_prep_channel_dir(1, self.full, 'cleaned'),
                                        file_name)

            PostTIFProcessor.make_mask_file(input_path, masked_path, cleaned_path)

    def apply_mask_dir(self, channel, stain, flip, rotation):
        input_dir = self.file_location_manager.get_prep_channel_dir(channel, self.full)
        for file_name in tqdm(sorted(os.listdir(input_dir))):
            input_path = os.path.join(input_dir, file_name)
            masked_path = os.path.join(self.file_location_manager.masked, file_name)
            cleaned_path = os.path.join(self.file_location_manager.get_prep_channel_dir(channel, self.full,
                                                                                        'cleaned'), file_name)

            PostTIFProcessor.apply_mask_file(input_path, masked_path, cleaned_path, stain, rotation, flip)

    @staticmethod
    def make_mask_file(input_path, masked_path, cleaned_path):
        """ Make masks from the channel 1 TIF files and also clean them.

        Args:
            input_path: the input TIF file
            masked_path: the output mask file
            cleaned_path: the output cleaned TIF file

        Returns:
            bool: Indicator True for success, False otherwise.
        """

        try:
            img = io.imread(input_path)
        except:
            print('Could not open', input_path)
            return False

        closing, scaled = make_mask(img)

        try:
            os.makedirs(os.path.dirname(masked_path), exist_ok=True)
            cv2.imwrite(masked_path, closing.astype('uint8'))
        except:
            print('Could not write', masked_path)
            return False

        try:
            os.makedirs(os.path.dirname(cleaned_path), exist_ok=True)
            cv2.imwrite(cleaned_path, scaled.astype('uint16'))
        except:
            print('Could not write', cleaned_path)
            return False

        return True

    @staticmethod
    def apply_mask_file(input_path, masked_path, cleaned_path, stain, rotation, flip):
        """ Apply masks generated from the channel 1 TIF files to other channels

        Args:
            input_path: the input TIF file
            masked_path: the input mask file
            cleaned_path: the output cleaned TIF file
            stain: the stain of the animal
            rotation: whether to rotate the TIF file
            flip: whether to flip or flop the TIF file

        Returns:
            bool: Indicator True for success, False otherwise.
        """

        try:
            img = io.imread(input_path)
        except:
            print('Could not open', input_path)
            return False

        try:
            mask = io.imread(masked_path)
        except:
            print('Could not open', input_path)
            return False

        fixed = apply_mask(img, mask, stain, rotation, flip)

        try:
            os.makedirs(os.path.dirname(cleaned_path), exist_ok=True)
            cv2.imwrite(cleaned_path, fixed.astype('uint16'))
        except:
            print('Could not write', cleaned_path)
            return False

        return True

    def make_mask_datajoint(self, debug=False):
        """ The wrapper function to invoke datajoint's autopopulate method for "make_mask" operation.
        To speed up, you can run this method on different machines at the same time.

        Args:
            debug: whether to print the debug message
        """

        global dj_make_mask_params
        dj_make_mask_params['full'] = self.full

        restrictions = [RawSection & f'prep_id="{self.animal.prep_id}" and active=1 and channel=1']
        MakeMaskOperation.populate(restrictions, display_progress=debug)

    def apply_mask_datajoint(self, stain, rotation, flip, debug=False):
        """ The wrapper function to invoke datajoint's autopopulate method for "apply_mask" operation.
        To speed up, you can run this method on different machines at the same time.

        Args:
            stain: the parameter passed into operation. Refer to that function for details.
            rotation: the parameter passed into operation. Refer to that function for details.
            flip: the parameter passed into operation. Refer to that function for details.
            debug: whether to print the debug message
        """

        global dj_apply_mask_params
        dj_apply_mask_params['full'] = self.full
        dj_apply_mask_params['stain'] = stain
        dj_apply_mask_params['rotation'] = rotation
        dj_apply_mask_params['flip'] = flip

        restrictions = [RawSection & f'prep_id="{self.animal.prep_id}" and active=1']
        ApplyMaskOperation.populate(restrictions, display_progress=debug)


"""
Below are the definitions of datajoint tables required for the operations in the PostTifProcessor.

Because of the stupidity of datajoint's not allowing pass parameters to the make function, the parameters have to be 
global variables. Thus, the parameters for each operation are in a dictionary that will be fulfilled in the datajoint 
wrapper functions. 
"""

dj_make_mask_params = {
    'full': True,
}
dj_apply_mask_params = {
    'full': True,
    'rotation': 0,
    'flip': 'flip',
    'stain': 'NTB',
}


@schema
class MakeMaskOperation(dj.Computed):
    definition = """
    -> RawSection
    ---
    duration : float
    """

    def make(self, key):
        raw_section_row = session.query(AlcRawSection).filter(AlcRawSection.id == key['id']).one()

        if raw_section_row.channel != 1:
            return

        file_name = str(raw_section_row.section_number).zfill(3) + '.tif'
        file_location_manager = FileLocationManager(raw_section_row.prep_id)
        input_dir = file_location_manager.get_prep_channel_dir(1, dj_make_mask_params['full'])
        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(file_location_manager.masked, file_name)
        cleaned_path = os.path.join(file_location_manager.get_prep_channel_dir(1, dj_make_mask_params['full'],
                                                                               'cleaned'), file_name)

        start = time.time()
        success = PostTIFProcessor.make_mask_file(input_path, masked_path, cleaned_path)
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))


@schema
class ApplyMaskOperation(dj.Computed):
    definition = """
    -> RawSection
    ---
    duration : float
    """

    def make(self, key):
        raw_section_row = session.query(AlcRawSection).filter(AlcRawSection.id == key['id']).one()

        file_name = str(raw_section_row.section_number).zfill(3) + '.tif'
        file_location_manager = FileLocationManager(raw_section_row.prep_id)
        input_dir = file_location_manager.get_prep_channel_dir(raw_section_row.channel, dj_make_mask_params['full'])
        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(file_location_manager.masked, file_name)
        cleaned_path = os.path.join(file_location_manager.get_prep_channel_dir(raw_section_row.channel,
                                                                               dj_make_mask_params['full'],
                                                                               'cleaned'), file_name)

        start = time.time()
        success = PostTIFProcessor.apply_mask_file(input_path, masked_path, cleaned_path, dj_apply_mask_params['stain'],
                                                   dj_apply_mask_params['rotation'], dj_apply_mask_params['flip'])
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))
