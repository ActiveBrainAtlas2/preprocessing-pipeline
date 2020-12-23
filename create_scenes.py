"""
This file does the following operations:
    1. Queries the sections view to get active tifs to be created.
    2. Runs the bfconvert bioformats command to yank the tif out of the czi and place
    it in the correct directory with the correct name
    3. If you  extracting jp2 files, you need to set this bash variable before running the program:
    export BF_MAX_MEM=12096M and set the njobs to 1
"""
import os
import argparse
from multiprocessing.pool import Pool
from utilities.file_location import FileLocationManager
from utilities.utilities_process import workernoshell


def make_scenes(animal, njobs):
    """
    Args:
        animal: the prep id of the animal
        njobs: number of jobs for parallel computing

    Returns:
        nothing
    """

    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.czi
    OUTPUT = fileLocationManager.thumbnail_web
    czis = os.listdir(INPUT)

    commands = []
    for czi in czis:
        input_path = os.path.join(INPUT, czi)
        for i in range(0,21):
            slide_number = czi.replace(animal, '').replace('_slide','').replace('.czi','')[0:3]
            scene_index = str(i).zfill(3)
            tif = f'slide_{slide_number}_index_{scene_index}.tif'
            tif_path = os.path.join(OUTPUT, tif)
            png = tif.replace('tif', 'png')
            png_path = os.path.join(OUTPUT, png)
            if os.path.exists(tif_path):
                continue
            if os.path.exists(png_path):
                continue

            cmd = ['/usr/local/share/bftools/bfconvert', '-bigtiff', '-separate', '-series', str(i),
                   '-channel', str(0),  '-nooverwrite', input_path, tif_path]
            commands.append(cmd)

    with Pool(njobs) as p:
        p.map(workernoshell, commands)

    ### do the png after all the tifs have been done
    convert_commands = []
    INPUT = fileLocationManager.thumbnail_web
    tifs = os.listdir(INPUT)
    for tif in tifs:
        tif_path = os.path.join(OUTPUT, tif)
        if not tif.endswith('tif'):
            continue

        png = tif.replace('tif', 'png')
        png_path = os.path.join(OUTPUT, png)
        if os.path.exists(png_path):
            continue

        # convert tif to png
        cmd = ['convert', tif_path, '-resize', '3.125%', '-normalize', '-rotate', '90', png_path]
        convert_commands. append(cmd)


    with Pool(njobs) as p:
        p.map(workernoshell, convert_commands)

    # clean up
    tifs = os.listdir(OUTPUT)
    for tif in tifs:
        tif_path = os.path.join(OUTPUT, tif)
        if tif.endswith('tif'):
            os.remove(tif_path)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--njobs', help='How many processes to spawn', default=4, required=False)

    args = parser.parse_args()
    animal = args.animal
    njobs = int(args.njobs)

    make_scenes(animal, njobs)
