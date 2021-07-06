"""
This is the first script run in the pipeline process.
It goes through the czi directory and gets the biggest
4 files with the bioformats tool: showinf. It then
populates the database with this meta information. The user
then validates the data with the ActiveAtlasAdmin database portal
"""
import argparse
import os, sys, time
from datetime import datetime
from tqdm import tqdm
import re

from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_bioformats import get_czi_metadata, get_fullres_series_indices
from model.slide import Slide
from model.slide_czi_to_tif import SlideCziTif
from sql_setup import session, SLIDES_ARE_SCANNED, CZI_FILES_ARE_PLACED_ON_BIRDSTORE, CZI_FILES_ARE_SCANNED_TO_GET_METADATA


def make_meta(animal, remove):
    """
    Scans the czi dir to extract the meta information for each tif file
    Args:
        animal: the animal as primary key

    Returns: nothing
    """
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    scan_id = sqlController.scan_run.id
    slides = session.query(Slide).filter(Slide.scan_run_id == scan_id).count()

    if slides > 0 and not remove:
        print(f'There are {slides} existing slides. You must manually delete the slides first.')
        print('Rerun this script as create_meta.py --animal DKXX --remove true')
        sys.exit()

    session.query(Slide).filter(Slide.scan_run_id == scan_id).delete(synchronize_session=False)
    session.commit()

    try:
        czi_files = sorted(os.listdir(fileLocationManager.czi))
    except OSError as e:
        print(e)
        sys.exit()

    section_number = 1
    for i, czi_file in enumerate(tqdm(czi_files)):
        extension = os.path.splitext(czi_file)[1]
        if extension.endswith('czi'):
            slide = Slide()
            slide.scan_run_id = scan_id
            slide.slide_physical_id = int(re.findall(r'\d+', czi_file)[1])
            slide.rescan_number = "1"
            slide.slide_status = 'Good'
            slide.processed = False
            slide.file_size = os.path.getsize(os.path.join(fileLocationManager.czi, czi_file))
            slide.file_name = czi_file
            slide.created = datetime.fromtimestamp(os.path.getmtime(os.path.join(fileLocationManager.czi, czi_file)))

            # Get metadata from the czi file
            czi_file_path = os.path.join(fileLocationManager.czi, czi_file)
            metadata_dict = get_czi_metadata(czi_file_path)
            #print(metadata_dict)
            series = get_fullres_series_indices(metadata_dict)
            #print('series', series)
            slide.scenes = len(series)
            session.add(slide)
            session.flush()

            for j, series_index in enumerate(series):
                scene_number = j + 1
                channels = range(metadata_dict[series_index]['channels'])
                #print('channels range and dict', channels,metadata_dict[series_index]['channels'])
                channel_counter = 0
                width = metadata_dict[series_index]['width']
                height = metadata_dict[series_index]['height']
                for channel in channels:
                    tif = SlideCziTif()
                    tif.slide_id = slide.id
                    tif.scene_number = scene_number
                    tif.file_size = 0
                    tif.active = 1
                    tif.width = width
                    tif.height = height
                    tif.scene_index = series_index
                    channel_counter += 1
                    newtif = '{}_S{}_C{}.tif'.format(czi_file, scene_number, channel_counter)
                    newtif = newtif.replace('.czi', '').replace('__','_')
                    tif.file_name = newtif
                    tif.channel = channel_counter
                    tif.processing_duration = 0
                    tif.created = time.strftime('%Y-%m-%d %H:%M:%S')
                    session.add(tif)
                section_number += 1
        session.commit()






if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--remove', help='Enter true or false', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    remove = bool({'true': True, 'false': False}
                      [str(args.remove).lower()])
    make_meta(animal, remove)
    sqlController = SqlController(animal)
    sqlController.set_task(animal, SLIDES_ARE_SCANNED)
    sqlController.set_task(animal, CZI_FILES_ARE_PLACED_ON_BIRDSTORE)
    sqlController.set_task(animal, CZI_FILES_ARE_SCANNED_TO_GET_METADATA)
