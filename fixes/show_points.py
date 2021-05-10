import os, sys
import pandas as pd
from subprocess import Popen
import argparse
import numpy as np
from scipy.spatial.distance import pdist, squareform

HOME = os.path.expanduser("~")

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)

from utilities.utilities_process import get_image_size
from utilities.file_location import FileLocationManager

def create_points(animal, section, layer, debug=False):

    fileLocationManager = FileLocationManager(animal)

    INPUT = os.path.join(fileLocationManager.prep, 'CH3', 'full_aligned')
    
    dfpath = os.path.join(fileLocationManager.brain_info, 'CH3.points.csv')
    if not os.path.exists(dfpath):
        print(dfpath, 'does not exist')
        return
    df = pd.read_csv(dfpath)
    df.drop(["Description"], inplace=True, axis=1)
    counts = df[['Layer', 'X', 'Section']].groupby(['Layer','Section']).agg(['count'])
    if debug:
        print(counts.to_string())

    df = df[(df["Layer"] == layer)]
    sections = df['Section'].unique()
    for section in sections:
        df = df[(df["Layer"] == layer) & (df["Section"] == section)]
        if debug:
            print('section', section)
            print(df.head())
        pts = df[['X','Y']].values / 1
        means = np.mean(pts, axis=0)
        mean_x = means[0]
        mean_y = means[1]
        D = pdist(pts)
        D = squareform(D);
        max_distance, [I_row, I_col] = np.nanmax(D), np.unravel_index( np.argmax(D), D.shape )

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
        
        sizex = int(max_distance + 500)
        sizey = sizex
        offsetx = int(mean_x - max_distance/2)
        offsety = int(mean_y - max_distance/2)

        #cmd = f'convert {outpath} -gravity West -chop {chop}x0 {outpath}' 
        cmd = f'convert {outpath} -crop {sizex}x{sizey}+{offsetx}+{offsety} -normalize -auto-level {outpath}' 
        if debug:
            print(cmd)
        else:
            proc = Popen(cmd, shell=True)
            proc.wait()

        pngfile = str(section).zfill(3) + '.png'
        pngpath = os.path.join(fileLocationManager.thumbnail_web, 'points', layer)
        os.makedirs(pngpath, exist_ok=True)
        png = os.path.join(pngpath, pngfile)
        cmd = f'convert {outpath} -resize 12% {png}' 
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
