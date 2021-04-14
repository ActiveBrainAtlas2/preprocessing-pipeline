from multiprocessing.pool import Pool
import os, sys, time
from datetime import datetime
import re
from celery import Celery, current_task, group
from pathlib import Path
from subprocess import Popen, run, check_output

from celery.app import shared_task
PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workernoshell
from sql_setup import QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1
#from utilities.logger import get_logger
SCALING_FACTOR = 0.03125

from decimal import Decimal
PROGRESS_STATE = 'PROGRESS'

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)

from sql_setup import session
from utilities.model.slide import Slide
from utilities.model.slide_czi_to_tif import SlideCziTif
from utilities.utilities_bioformats import get_czi_metadata, get_fullres_series_indices

app = Celery('pipeline')
app.config_from_object('utilities.celeryconfig')


"""
Start of import of methods to set up celery queue
"""

@app.task(bind=True)
def make_meta(self, animal, remove):
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
    file_count = len(czi_files)
    for i, czi_file in enumerate(czi_files):
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
            current_task.update_state(state=PROGRESS_STATE, meta={'current':i, 'total':file_count})
            

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

"""
from create_tifs.py
"""

@app.task(bind=True)
def make_tifs(self, animal, channel, njobs):
    """
    This method will:
        1. Fetch the sections from the database
        2. Yank the tif out of the czi file according to the index and channel with the bioformats tool.
        3. Then updates the database with updated meta information
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
        njobs: number of jobs for parallel computing
        compression: default is no compression so we can create jp2 files for CSHL. The files get
        compressed using LZW when running create_preps.py

    Returns:
        nothing
    """

    #logger = get_logger(animal)
    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = fileLocationManager.czi
    OUTPUT = fileLocationManager.tif
    os.makedirs(OUTPUT, exist_ok=True)
    sections = sqlController.get_distinct_section_filenames(animal, channel)

    sqlController.set_task(animal, QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN)
    sqlController.set_task(animal, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1)
    nproc = 2
    commands = []
    for section in sections:
        input_path = os.path.join(INPUT, section.czi_file)
        output_path = os.path.join(OUTPUT, section.file_name)

        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue

        cmd = ['/usr/local/share/bftools/bfconvert', '-bigtiff', '-separate', '-series', str(section.scene_index),
                '-channel', str(section.channel_index),  '-nooverwrite', input_path, output_path]

        """
        cmd = [section.scene_index, section.channel_index, input_path, output_path]
        commands.extend([bfconvert.subtask(
            (section.scene_index, section.channel_index, input_path, output_path))
                for i in range(nproc)])

    result = group(commands).apply_async()
        """
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workernoshell, commands)



@shared_task
def bfconvert(scene_index, channel_index, input_path, output_path):
    cmd = ['/usr/local/share/bftools/bfconvert', '-bigtiff', '-separate', '-series', str(scene_index),
            '-channel', str(channel_index),  '-nooverwrite', input_path, output_path]
    proc = Popen(cmd, shell=False, stderr=None, stdout=None)
    proc.wait()
    #run(cmd)



@app.task
def make_scenes(self, animal, njobs):
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.tif
    OUTPUT = os.path.join(fileLocationManager.thumbnail_web, 'scene')
    os.makedirs(OUTPUT, exist_ok=True)

    commands = []
    tifs = os.listdir(INPUT)
    for tif in tifs:
        tif_path = os.path.join(INPUT, tif)
        if not tif.endswith('_C1.tif'):
            continue

        png = tif.replace('tif', 'png')
        png_path = os.path.join(OUTPUT, png)
        if os.path.exists(png_path):
            continue

        # convert tif to png
        cmd = ['convert', tif_path, '-resize', '3.125%', '-normalize', png_path]
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workernoshell, commands)




def set_progress(self, current, total, description=""):
    percent = 0
    if total > 0:
        percent = (Decimal(current) / Decimal(total)) * Decimal(100)
        percent = float(round(percent, 2))
    state = PROGRESS_STATE
    meta = {
        'pending': False,
        'current': current,
        'total': total,
        'percent': percent,
        'description': description
    }
    self.update_state(
        state=state,
        meta=meta
    )
    return state, meta
