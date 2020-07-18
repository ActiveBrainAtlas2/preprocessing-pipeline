"""
This file does the following operations:
    1. Queries the sections view to get active tifs to be created.
    2. Runs the bfconvert bioformats command to yank the tif out of the czi and place
    it in the correct directory with the correct name
"""
import argparse
import os
from multiprocessing.pool import Pool

from tqdm import tqdm

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController
from utilities.utilities_process import workershell
from sql_setup import QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1


def update_tif_data(self):
    try:
        os.listdir(self.fileLocationManager.tif)
    except OSError as e:
        print(e)
        sys.exit()

    slides = self.session.query(AlcSlide).filter(AlcSlide.scan_run_id.in_(self.scan_ids)).filter(
        AlcSlide.slide_status == 'Good').all()
    slide_ids = [slide.id for slide in slides]
    tifs = self.session.query(AlcSlideCziTif).filter(AlcSlideCziTif.slide_id.in_(slide_ids)).filter(
        AlcSlideCziTif.active == 1).all()
    for tif in tifs:
        if os.path.exists(os.path.join(self.fileLocationManager.tif, tif.file_name)):
            tif.file_size = os.path.getsize(os.path.join(self.fileLocationManager.tif, tif.file_name))
            self.session.merge(tif)
    self.session.commit()


def make_tifs(animal, channel, njobs):
    """
    Args:
        animal: the prep id of the animal
        channel: the channel of the stack to process
        njobs: number of jobs for parallel computing

    Returns:
        nothing
    """

    fileLocationManager = FileLocationManager(animal)
    sqlController = SqlController(animal)
    INPUT = fileLocationManager.czi
    OUTPUT = fileLocationManager.tif
    tifs = sqlController.get_distinct_section_filenames(animal, channel)

    sqlController.set_task(animal, QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN)
    sqlController.set_task(animal, CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1)

    commands = []
    for tif in tqdm(tifs):
        input_path = os.path.join(INPUT, tif.czi_file)
        output_path = os.path.join(OUTPUT, tif.file_name)
        if not os.path.exists(input_path):
            continue

        if os.path.exists(output_path):
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = '/usr/local/share/bftools/bfconvert -bigtiff -compression LZW -separate -series {} -channel {} -nooverwrite {} {}'.format(
            tif.scene_index, tif.channel_index, input_path, output_path)
        commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workershell, commands)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)
    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)
    channel = int(args.channel)
    make_tifs(animal, channel, njobs)

