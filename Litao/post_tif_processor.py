import os
import sys
import time

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
    def __init__(self, prep_id, session, thumbnail):
        """ setup the attributes for the SlidesProcessor class

        Args:
            animal: object of animal to process
            session: sqlalchemy session to run queries
        """
        try:
            animal = session.query(AlcAnimal).filter(AlcAnimal.prep_id == prep_id).one()
        except (NoResultFound):
            print('No results found for prep_id: {}.'.format(prep_id))
            sys.exit()

        self.animal = animal
        self.session = session
        self.thumbnail = thumbnail
        self.file_location_manager = FileLocationManager(animal.prep_id)

    def make_mask_dir(self):
        input_dir = self.file_location_manager.get_prep_channel_dir(1, self.thumbnail)
        for file_name in tqdm(sorted(os.listdir(input_dir))):
            input_path = os.path.join(input_dir, file_name)
            masked_path = os.path.join(self.file_location_manager.masked, file_name)
            cleaned_path = os.path.join(self.file_location_manager.get_prep_channel_dir(1, self.thumbnail, 'cleaned'),
                                        file_name)

            PostTIFProcessor.make_mask_file(input_path, masked_path, cleaned_path)

    def make_mask_datajoint(self):
        global dj_make_mask_params
        dj_make_mask_params['thumbnail'] = self.thumbnail

        restrictions = [RawSection & f'prep_id="{self.animal}" and active=1 and channel=1']
        MakeMaskOperation.populate(restrictions=restrictions, display_progress=True)

    def apply_mask_dir(self, channel, stain, flip, rotation):
        input_dir = self.file_location_manager.get_prep_channel_dir(channel, self.thumbnail)
        for file_name in tqdm(sorted(os.listdir(input_dir))):
            input_path = os.path.join(input_dir, file_name)
            masked_path = os.path.join(self.file_location_manager.masked, file_name)
            cleaned_path = os.path.join(self.file_location_manager.get_prep_channel_dir(channel, self.thumbnail,
                                                                                        'cleaned'), file_name)

            PostTIFProcessor.apply_mask_file(input_path, masked_path, cleaned_path, stain, rotation, flip)

    def apply_mask_datajoint(self, stain, rotation, flip):
        global dj_apply_mask_params
        dj_apply_mask_params['thumbnail'] = self.thumbnail
        dj_apply_mask_params['stain'] = stain
        dj_apply_mask_params['rotation'] = rotation
        dj_apply_mask_params['flip'] = flip

        restrictions = [RawSection & f'prep_id="{self.animal}" and active=1']
        ApplyMaskOperation.populate(restrictions=restrictions, display_progress=True)

    @staticmethod
    def make_mask_file(input_path, masked_path, cleaned_path):
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


dj_make_mask_params = {
    'thumbnail': True,
}
dj_apply_mask_params = {
    'thumbnail': True,
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
        input_dir = file_location_manager.get_prep_channel_dir(1, dj_make_mask_params['thumbnail'])
        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(file_location_manager.masked, file_name)
        cleaned_path = os.path.join(file_location_manager.get_prep_channel_dir(1, dj_make_mask_params['thumbnail'],
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
        input_dir = file_location_manager.get_prep_channel_dir(raw_section_row.channel, dj_make_mask_params['thumbnail'])
        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(file_location_manager.masked, file_name)
        cleaned_path = os.path.join(file_location_manager.get_prep_channel_dir(raw_section_row.channel,
                                                                               dj_make_mask_params['thumbnail'],
                                                                               'cleaned'), file_name)

        start = time.time()
        success = PostTIFProcessor.apply_mask_file(input_path, masked_path, cleaned_path, dj_apply_mask_params['stain'],
                                                   dj_apply_mask_params['rotation'], dj_apply_mask_params['flip'])
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))
