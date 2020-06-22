import os
import time
import datajoint as dj

from model.atlas_schema import schema, RawSection
from utilities.file_location import FileLocationManager
from Litao.old.make_mask import make_mask_file
from Litao.old.clean_mask import apply_mask_file


@schema
class MakeMaskInitiated(dj.Manual):
    definition = """
    id              : int auto_increment
    raw_section_id  : int
    ----------------
    thumbnail       : tinyint
    """


@schema
class MakeMaskFinished(dj.Computed):
    definition = """
    -> MakeMaskInitiated
    ---
    duration : float
    """

    def make(self, key):
        # Read raw section info
        raw_section_id = key['raw_section_id']
        raw_section = (RawSection & f'id="{raw_section_id}"').fetch(as_dict=True)[0]
        animal = raw_section['prep_id']
        channel = raw_section['channel']
        file_name = str(raw_section['section_number']).zfill(3) + '.tif'

        # Read parameters for this operation
        thumbnail = bool((MakeMaskInitiated & key).fetch1('thumbnail'))

        if channel != 1:
            return

        file_location_manager = FileLocationManager(animal)
        input_dir = os.path.join(file_location_manager.prep, 'CH1', 'thumbnail')
        masked_dir = os.path.join(file_location_manager.prep, 'masked')
        cleaned_dir = os.path.join(file_location_manager.prep, 'CH1', 'cleaned')

        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(masked_dir, file_name)
        cleaned_path = os.path.join(cleaned_dir, file_name)

        start = time.time()
        success = make_mask_file(input_path, masked_path, cleaned_path)
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))


@schema
class CleanMaskInitiated(dj.Manual):
    definition = """
    id              : int auto_increment
    raw_section_id  : int
    ----------------
    thumbnail       : tinyint
    stain           : enum('NTB')
    rotation        : int
    flip            : enum('flip', 'flop')
    """


@schema
class CleanMaskFinished(dj.Computed):
    definition = """
    -> CleanMaskInitiated
    ---
    duration: float
    """

    def make(self, key):
        # Read raw section info
        raw_section_id = key['raw_section_id']
        raw_section = (RawSection & f'id="{raw_section_id}"').fetch(as_dict=True)[0]
        animal = raw_section['prep_id']
        channel = raw_section['channel']
        file_name = str(raw_section['section_number']).zfill(3) + '.tif'

        # Read parameters for this operation
        thumbnail = bool((CleanMaskInitiated & key).fetch1('thumbnail'))
        stain = str((CleanMaskInitiated & key).fetch1('stain'))
        rotation = int((CleanMaskInitiated & key).fetch1('rotation'))
        flip = str((CleanMaskInitiated & key).fetch1('flip'))

        file_location_manager = FileLocationManager(animal)
        if channel > 1:
            input_dir = os.path.join(file_location_manager.prep, 'CH' + str(channel), 'thumbnail')
        else:
            input_dir = os.path.join(file_location_manager.prep, 'CH' + str(channel), 'cleaned')
        masked_dir = os.path.join(file_location_manager.prep, 'masked')
        cleaned_dir = os.path.join(file_location_manager.prep, 'CH' + str(channel), 'cleaned')

        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(masked_dir, file_name)
        cleaned_path = os.path.join(cleaned_dir, file_name)

        start = time.time()
        success = apply_mask_file(input_path, masked_path, cleaned_path, stain, rotation, flip)
        end = time.time()

        if success:
            self.insert1(dict(key, duration=end - start))


def make_mask_operation(animal, thumbnail):
    raw_section_ids = (RawSection & f'prep_id = "{animal}"' & f'channel = 1').fetch('id')
    thumbnail = int(thumbnail)

    for raw_section_id in raw_section_ids:
        MakeMaskInitiated.insert1({'raw_section_id': raw_section_id, 'thumbnail': thumbnail})

    MakeMaskFinished.populate(display_progress=True)


def clean_mask_operation(animal, thumbnail, stain, rotation, flip):
    raw_section_ids = (RawSection & f'prep_id = "{animal}"' & f'channel = 1').fetch('id')
    thumbnail = int(thumbnail)
    rotation = int(rotation)
    flip = str(flip)
    stain = str(stain)

    for raw_section_id in raw_section_ids[:10]:
        CleanMaskInitiated.insert1({'raw_section_id': raw_section_id, 'thumbnail': thumbnail,
                                    'stain': stain, 'rotation': rotation, 'flip': flip})

    CleanMaskFinished.populate(display_progress=True)


#make_mask_operation('DK43', True)
clean_mask_operation('DK43', True, 'NTB', 0, 'flip')
