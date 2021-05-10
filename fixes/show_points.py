import os, sys
import pandas as pd
from subprocess import Popen
import argparse

HOME = os.path.expanduser("~")

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)

from utilities.utilities_process import get_image_size
from utilities.file_location import FileLocationManager

def create_points(animal, section, layer, debug=False):

    fileLocationManager = FileLocationManager(animal)

    INPUT = os.path.join(fileLocationManager.prep, 'CH3', 'full_aligned')
    dfpath = os.path.join(HOME, f'programming/brains/{animal}', f'{animal}.CH3.Premotor.csv')
    if not os.path.exists(dfpath):
        print(dfpath, 'does not exist')
        return
    df = pd.read_csv(dfpath)
    df.drop(["Description"], inplace=True, axis=1)
    counts = df[['Layer', 'X', 'Section']].groupby(['Layer','Section']).agg(['count'])
    if debug:
        print(counts.to_string())
    df = df[(df["Layer"] == layer) & (df["Section"] == section)]
    if debug:
        print(df.head())
    pts = df[['X','Y']].values / 1
    points = pts.tolist()

    file = f'{section}.tif' 
    infile = os.path.join(INPUT, file)

    if not os.path.exists(infile):
        print(infile, 'does not exist')
        return

    OUTPUT = f'{HOME}/programming/brains/{animal}/CH3'
    os.makedirs(OUTPUT, exist_ok=True)
    outpath =  os.path.join(OUTPUT, f'{section}.points.tif')

    if os.path.exists(outpath):
        print(outpath, 'exists')
        return

    cmd = f'convert {infile} -fill transparent -stroke yellow'  
    for point in points:
        endcircle = point[0] + (20*5)
        cmd += f' -draw "circle {point[0]},{point[1]},{endcircle},{point[1]}" '

    cmd += f' {outpath}'
    if debug:
        print(cmd)
    else:
        proc = Popen(cmd, shell=True)
        proc.wait()
    
    width, height = get_image_size(infile)
    chop = width//2

    cmd = f'convert {outpath} -gravity West -chop {chop}x0 {outpath}' 
    if debug:
        print(cmd)
    else:
        proc = Popen(cmd, shell=True)
        proc.wait()

    outfile = str(section).zfill(3) + '.png'
    outpath = os.path.join(fileLocationManager.thumbnail_web, 'points')
    os.makedirs(outpath, exist_ok=True)
    png = os.path.join(outpath, outfile)
    cmd = f'convert {outpath} -resize 5% -normalize -auto-level {png}' 
    if debug:
        print(cmd)
    else:
        proc = Popen(cmd, shell=True)
        proc.wait()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--section', help='Enter section', required=True)
    parser.add_argument('--layer', help='Enter layer', required=True)
    parser.add_argument('--debug', help='Enter true or false', required=False, default='true')
    
 
    args = parser.parse_args()
    animal = args.animal
    section = int(args.section)
    layer = args.layer
    debug = bool({'true': True, 'false': False}[str(args.debug).lower()])
    create_points(animal, section, layer, debug)
