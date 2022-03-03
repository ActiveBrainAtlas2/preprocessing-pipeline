import os, sys, time
from datetime import datetime
from tqdm import tqdm
import re
from lib.file_location import FileLocationManager
from lib.sqlcontroller import SqlController
from lib.utilities_bioformats import get_czi_metadata, get_fullres_series_indices
from model.scan_run import ScanRun
from model.slide import Slide
from model.slide_czi_to_tif import SlideCziTif
from lib.sql_setup import session, SLIDES_ARE_SCANNED, CZI_FILES_ARE_PLACED_ON_BIRDSTORE, CZI_FILES_ARE_SCANNED_TO_GET_METADATA


def make_meta(animal):
    """
    Scans the czi dir to extract the meta information for each tif file
    Args:
        animal: the animal as primary key

    Returns: nothing
    """
    sqlController = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    scan_id = sqlController.scan_run.id
    slide_count = session.query(Slide).filter(Slide.scan_run_id == scan_id).count()
    session.query(ScanRun).filter(ScanRun.id == scan_id).update({'number_of_slides': slide_count})
    session.commit()

    try:
        czi_files = sorted(os.listdir(fileLocationManager.czi))
    except OSError as e:
        print(e)
        sys.exit()

    if slide_count == len(czi_files):
        return
    else:
        print('Slides in DB and #slides on filesystem differ, redoing slide DB update.')
        session.query(Slide).filter(Slide.scan_run_id == scan_id).delete(synchronize_session=False)
        session.commit()

    section_number = 1
    for i, czi_file in enumerate(tqdm(czi_files)):
        extension = os.path.splitext(czi_file)[1]
        slide_id = int(re.findall(r'\d+', czi_file)[1])
        if extension.endswith('czi') and not sqlController.slide_exists(scan_id, slide_id):
            slide = Slide()
            slide.scan_run_id = scan_id
            slide.slide_physical_id = slide_id
            slide.rescan_number = "1"
            slide.slide_status = 'Good'
            slide.processed = False
            slide.file_size = os.path.getsize(os.path.join(fileLocationManager.czi, czi_file))
            slide.file_name = czi_file
            slide.created = datetime.fromtimestamp(os.path.getmtime(os.path.join(fileLocationManager.czi, czi_file)))
            # Get metadata from the czi file
            czi_file_path = os.path.join(fileLocationManager.czi, czi_file)
            metadata_dict = get_czi_metadata(czi_file_path)
            # print(metadata_dict)
            series = get_fullres_series_indices(metadata_dict)
            # print('series', series)
            slide.scenes = len(series)
            session.add(slide)
            session.flush()

            for j, series_index in enumerate(series):
                scene_number = j + 1
                channels = range(metadata_dict[series_index]['channels'])
                # print('channels range and dict', channels,metadata_dict[series_index]['channels'])
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
                    newtif = newtif.replace('.czi', '').replace('__', '_')
                    tif.file_name = newtif
                    tif.channel = channel_counter
                    tif.processing_duration = 0
                    tif.created = time.strftime('%Y-%m-%d %H:%M:%S')
                    session.add(tif)
                section_number += 1
        session.commit()
    sqlController = SqlController(animal)
    sqlController.set_task(animal, SLIDES_ARE_SCANNED)
    sqlController.set_task(animal, CZI_FILES_ARE_PLACED_ON_BIRDSTORE)
    sqlController.set_task(animal, CZI_FILES_ARE_SCANNED_TO_GET_METADATA)
